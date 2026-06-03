#!/usr/bin/env python3
"""
train_and_convert.py

Exercise 5 – Gesture classifier: training + TFLite conversion
Dataset: RTIMULib recordings from HW03 (classes A, B, C + garbage)
Model:   1-D CNN operating on fixed-length windows of IMU time-series

Data format (from HW03 logger_recording.cpp):
    timestamp_ms, label, accel_x, accel_y, accel_z,
                         gyro_x,  gyro_y,  gyro_z,
                         mag_x,   mag_y,   mag_z

Our data was also augmented in another script (called padding_data.py) to ensure that all recordings 
have a fixed length of 150 rows, which is necessary for training the 1-D CNN model.
If they're shorter => 0s are appended
If they're longer => they're skipped during training.

During inference in main.cpp, shorter files are also padded
while longer files are truncated to 150 rows to ensure consistency with the training data format 
and to prevent memory issues on the Raspberry Pi.
"""

from __future__ import annotations
from importlib.resources import path
from tensorflow import keras

import shutil

from sklearn.metrics import confusion_matrix
import numpy as np

import argparse
from pathlib import Path

from collections import Counter
from sklearn.model_selection import train_test_split

import numpy as np
import tensorflow as tf
from data_sync import sync_from_pi
import pandas as pd
import csv

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a 1-D CNN on HW03 gesture data and export to TFLite."
    )
    parser.add_argument(
        "--data-dir",
        default="recordings_clean",
        help=(
            "Folder containing the raw CSV recordings from HW03. "
        ),
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Where .tflite and .keras files are written.",
    )
    parser.add_argument(
        "--sequence-length",
        type=int,
        default=150, # set to 150 to match the length of the recordings in the dataset, which are all padded/truncated to 150 rows
        help=(
            "Fixed number of timesteps per recording. "
            "All recordings must already be padded/truncated "
            "to this length."
        ),
    )
    parser.add_argument(
        "--labels-file",
        default="/workspaces/EAI4-DockerContainer/labels.csv",
        help="CSV mapping file_id -> label"
    )
    parser.add_argument("--epochs",      type=int,   default=60)
    parser.add_argument("--batch-size",  type=int,   default=16)
    parser.add_argument("--val-split",   type=float, default=0.15)
    parser.add_argument("--test-split",  type=float, default=0.15)
    parser.add_argument("--filters",     type=int,   default=32)
    parser.add_argument("--dense-units", type=int,   default=64)
    parser.add_argument(
        "--max-file-rows",
        type=int,
        default=300,
        help=(
            "Discard CSV files with more than this many data rows. "
            "Protects against accidentally long idle recordings "
            "(e.g. the 1372-row outlier in the HW03 dataset)."
        ),
    )
    parser.add_argument("--seed", type=int, default=42)

    parser.add_argument(
    "--remote-data",
    default=None,
    help="Optional rsync source like pi@IP:/path/to/recordings/"
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

# Sensor columns to use - we drop timestamp_ms (col 0)
SENSOR_COLS = [1, 2, 3, 4, 5, 6, 7, 8, 9]  # accel xyz, gyro xyz, mag xyz
N_AXES = len(SENSOR_COLS)  # 9


def load_recordings(
    data_dir: Path,
    labels_path: Path,
    sequence_length: int,
    max_file_rows: int,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Load all CSV files from data_dir.

    Filename convention (from HW03):  YYYY-MM-DD_HH-MM-SS_<LABEL>.csv
    The last character before '.csv' is the class label (A / B / C / -).

    Because recordings have variable lengths we use a sliding-window
    approach: each file contributes floor(n_rows / sequence_length) non-
    overlapping windows.  This naturally augments longer recordings.
    """
    labels_df = pd.read_csv(labels_path, dtype={"id": str})
    label_map = dict(zip(labels_df["id"].astype(str), labels_df["label"]))
    csv_files = sorted(data_dir.glob("*.csv"))
    print("Sample label_map keys:", list(label_map.keys())[:5]) # Debugging line to check label_map keys
    print("Example file_id:", csv_files[0].stem) # Debugging line to check file_id extraction
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    # List of fixed-length recordings
    samples = []

    skipped_long  = 0 # Count of files skipped for exceeding max_file_rows

    for csv_path in csv_files:
        # Extract label from filename: last character before ".csv"
        file_id = csv_path.stem
        label_char = label_map.get(file_id)

        if label_char is None:
            print(f"  WARNING: no label for {csv_path.name}, skipping")
            continue

        try:
            raw = np.loadtxt(
                csv_path,
                delimiter=",", # CSV format
                skiprows=1, # skip header row
                usecols=SENSOR_COLS, # only load sensor columns
                dtype=np.float32, # load as float32 for efficiency
            )
        except Exception as exc:
            print(f"  WARNING: not able to read {csv_path.name}: {exc}")
            continue

        if raw.ndim == 1:
            raw = raw[np.newaxis, :]  # single-row edge case

        # ------------------------------------------------------------------
        # Per-recording normalization
        # ------------------------------------------------------------------

        mean = raw.mean(axis=0, keepdims=True) # mean per column (axis=0), keepdims for broadcasting
        std = raw.std(axis=0, keepdims=True) # std per column

        std[std < 1e-6] = 1.0 # prevent division by zero for constant columns

        raw = (raw - mean) / std # standardize to zero mean and unit variance

        n_rows = raw.shape[0] # number of rows in the recording (after loading)

        if n_rows > max_file_rows:
            skipped_long += 1
            print(
                f"  SKIP (too long, {n_rows} rows): "
                f"{csv_path.name}"
            )
            # again, make sure to skip file entirely if it's too long, to avoid memory issues
            continue

        # ------------------------------------------------------------------
        # Fixed-size recordings
        # ------------------------------------------------------------------

        if n_rows != sequence_length: # if the recording doesn't have the expected number of rows, skip it

            print(
                f"  SKIP (expected {sequence_length} rows, got {n_rows}): "
                f"{csv_path.name}"
            )

            continue

        samples.append((file_id, label_char, raw)) 
        # append the file_id, label, and raw data as a tuple to the samples list

    class_names = sorted(
        list(set(label for _, label, _ in samples))
    ) # extract unique class labels from the samples and sort them

    if skipped_long:
        print(
            f"  (skipped {skipped_long} file(s) "
            f"exceeding --max-file-rows)"
        )

    if len(class_names) < 4:
        print(
            "\n  NOTE: fewer than 4 classes found. "
            "Add garbage recordings "
            "(files ending in '_-.csv') "
            "to train a 4-class model."
        ) # if there are fewer than 4 classes, print a note about adding garbage recording


    label_to_idx = {
        label: idx
        for idx, label in enumerate(class_names)
    } # create a mapping from class labels to integer indices (e.g. 'A' -> 0, 'B' -> 1, etc.)

    all_sequences = []
    all_labels = []

    for file_id, label, window in samples:
        all_sequences.append(window)
        all_labels.append(label_to_idx[label])
        # append the window (raw data) to all_sequences and the corresponding label index to all_labels

    X = np.stack(all_sequences, axis=0)
    y = np.array(all_labels, dtype=np.int32)
    # stack the list of sequences into a single numpy array X of shape (n_samples, sequence_length, n_axes)
    # convert the list of labels into a numpy array y of shape (n_samples,)

    return X, y, class_names
    # so the final output is the data array X, the label array y, and the list of class names


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

def augment(X: np.ndarray, y: np.ndarray, rng: np.random.Generator,
            ) -> tuple[np.ndarray, np.ndarray]:
    """
    Label-preserving augmentations to increase effective dataset size:
      • Gaussian noise  – simulates IMU measurement noise
      • Time reversal   – gesture backwards is still the same class
      • Axis scaling    – small random gain per sensor axis (±10%)
    Applied only to the training set - never to val or test.
    """
    aug_X = [X] # start with the original data as the first element of the augmented dataset
    aug_y = [y] # start with the original labels as the first element of the augmented labels

    # Gaussian noise
    aug_X.append(X + rng.normal(0, 0.02, size=X.shape).astype(np.float32)) # add Gaussian noise with mean 0 and std 0.02 to the original data, and append it to aug_X
    aug_y.append(y) # labels remain the same for the noisy data

    # Time reversal
    aug_X.append(X[:, ::-1, :]) # reverse the time axis (axis=1) of the original data, and append it to aug_X
    aug_y.append(y) # labels remain the same for the time-reversed data

    # Random axis scaling
    scale = rng.uniform(0.9, 1.1, size=(X.shape[0], 1, X.shape[2])).astype(np.float32) # generate random scaling factors between 0.9 and 1.1 for each sample and each axis, and reshape it to be broadcastable with X
    aug_X.append(X * scale) # scale the original data by the random factors, and append it to aug_X
    aug_y.append(y)

    return np.concatenate(aug_X, axis=0), np.concatenate(aug_y, axis=0) 
    # concatenate all the augmented data and labels along the first axis (n_samples) 
    # to create the final augmented dataset and label array

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def make_model(sequence_length: int, n_axes: int, n_classes: int,
               filters: int = 32, dense_units: int = 64
               ) -> tf.keras.Model:
    """
    1-D CNN for IMU gesture classification.

    Why Conv1D?
        Our input is a time-series of shape (sequence_length, n_axes).
        Conv1D slides a small kernel along the TIME axis and learns
        local temporal patterns — e.g. a sharp acceleration spike from
        a wrist flick.  Conv2D would be wrong here because our data has
        no 2-D spatial structure.

    Why ReLU?
        Simple, efficient, and works well in practice.  Avoids vanishing
        gradients compared to sigmoid/tanh.

    Why GlobalAveragePooling1D instead of Flatten?
        Reduces number of parameters and risk of overfitting.  Makes the
        model more translation-invariant along the time axis.

    Architecture:
        Input (50, 9)
        Conv1D(32, k=3) + ReLU  -> detect short-range patterns
        MaxPool1D(2)             -> halve time resolution
        Conv1D(64, k=3) + ReLU  -> detect longer-range patterns
        MaxPool1D(2)
        Conv1D(64, k=3) + ReLU  -> third level of abstraction
        GlobalAveragePooling1D   -> collapse time axis; fewer params than Flatten
        Dense(64) + ReLU
        Dropout(0.4)             -> regularisation for small dataset
        Dense(n_classes, softmax)

    All layers are fully supported by TFLite on Raspberry Pi.
    """

    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(sequence_length, n_axes), name="imu_input"),

            tf.keras.layers.Conv1D(filters,     kernel_size=3, padding="same", activation="relu", name="conv1"),
            tf.keras.layers.MaxPooling1D(pool_size=2, name="pool1"),
            # first Conv1D layer with 'filters' number of filters, kernel size of 3, 
            # 'same' padding to maintain the input length, ReLU activation, and named "conv1"

            tf.keras.layers.Conv1D(filters * 2, kernel_size=3, padding="same", activation="relu", name="conv2"),
            tf.keras.layers.MaxPooling1D(pool_size=2, name="pool2"),
            # second Conv1D layer with double the number of filters, kernel size of 3, 
            # 'same' padding, ReLU activation, and named "conv2"

            tf.keras.layers.Conv1D(filters * 2, kernel_size=3, padding="same", activation="relu", name="conv3"),
            # third Conv1D layer with the same number of filters as the second layer, kernel size of 3,
            # 'same' padding, ReLU activation, and named "conv3"

            tf.keras.layers.GlobalAveragePooling1D(name="gap"),
            # global average pooling layer to collapse the time dimension, named "gap"

            tf.keras.layers.Dense(dense_units, activation="relu", name="dense1"),
            # fully connected dense layer with 'dense_units' number of units, ReLU activation, and named "dense1"

            tf.keras.layers.Dropout(0.4, name="dropout"),
            # dropout layer with a dropout rate of 0.4 for regularization, named "dropout"

            tf.keras.layers.Dense(n_classes, activation="softmax", name="output"),
            # output dense layer with 'n_classes' number of units, 
            # softmax activation for classification, and named "output"
        ],
        name="gesture_1d_cnn", # name of the entire model
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    # compile the model with the Adam optimizer, sparse categorical crossentropy loss 
    # (since labels are integers), and accuracy as a metric
    return model


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_model(model: tf.keras.Model,
                X_train: np.ndarray, y_train: np.ndarray,
                X_val:   np.ndarray, y_val:   np.ndarray,
                epochs: int, batch_size: int) -> None:
    """
    EarlyStopping: stops training if val_loss does not improve for 15 epochs
                   and automatically restores the best weights.
    ReduceLROnPlateau: halves learning rate after 7 stagnant epochs to help
                       the optimiser escape flat regions.
    """
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=15,
            restore_best_weights=True, verbose=1
        ), # stop training if val_loss doesn't improve for 15 epochs, and restore the best weights
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=7, verbose=1
        ), # reduce learning rate by a factor of 0.5 if val_loss doesn't improve for 7 epochs, 
        # to help escape flat regions
    ]

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs, # maximum number of epochs to train, but may stop early due to EarlyStopping callback
        batch_size=batch_size, # number of samples per gradient update, set to 16 by default
        callbacks=callbacks, # apply the callbacks for early stopping and learning rate reduction during training
        verbose=2, # print one line per epoch with loss and accuracy
        shuffle=True, # shuffle the training data at each epoch to improve generalization
    ) 
    # train the model on the training data with the specified number of epochs and batch size,
    # using the validation data for validation, and applying the callbacks for early stopping and learning rate
    # shuffling the training data at each epoch to improve generalization

# ---------------------------------------------------------------------------
# Prep for saving it in the model_metrics.csv file
# ---------------------------------------------------------------------------
def count_nonzero_weights(model):
    total = 0
    nonzero = 0

    for weight in model.get_weights():
        total += int(weight.size)
        nonzero += int(np.count_nonzero(weight))

    return total, nonzero

# ----------------------------------------------------------------------------
# Pruning
# ----------------------------------------------------------------------------
def compile_for_classification(model):
    """
    After pruning, the model's weights are modified (some set to zero), so we need to recompile the model 
    to ensure that the changes take effect and that the model is ready for classification tasks.
    """
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    ) # compile the model with the Adam optimizer, sparse categorical crossentropy loss, and accuracy metric for classification tasks

def prune_synapses(base_model: keras.Model, prune_ratio: float) -> keras.Model:
    """
    Prune individual synapses (weights) with the smallest absolute values.
    This is a simple unstructured pruning method that zeros out the least important weights based on their magnitude. 
    The prune_ratio determines the percentage of weights to prune (e.g., 0.3 means pruning 30% of the smallest weights). 
    After pruning, the model is recompiled for classification tasks.
    """
    model = keras.models.clone_model(base_model) # create a new model with the same architecture as the base model
    model.set_weights(base_model.get_weights()) # copy the weights from the base model to the new model
    compile_for_classification(model) # compile the model for classification tasks after copying the weights

    kernels = []
    for layer in model.layers:
        weights = layer.get_weights() 
        # get the weights of the current layer, which is a list of numpy arrays 
        # (e.g., [kernel, bias] for Conv1D and Dense layers)
        if len(weights) >= 1:
            kernels.append(np.abs(weights[0]).reshape(-1))
            # if the layer has at least one weight array (the kernel), 
            # take the absolute values of the kernel weights, flatten them into a 1D array, 
            # and append it to the kernels list

    all_kernel_values = np.concatenate(kernels) 
    # concatenate all the kernel values from all layers into a single 1D array

    threshold = np.percentile(all_kernel_values, prune_ratio * 100.0) 
    # calculate the pruning threshold as the value below which a 
    # certain percentage (prune_ratio) of the kernel weights fall

    for layer in model.layers:
        weights = layer.get_weights()
        if len(weights) >= 1:
            kernel = weights[0] # get the kernel weights of the current layer
            kernel[np.abs(kernel) <= threshold] = 0.0 # set weights with absolute value less than or equal to the threshold to zero (prune them)
            weights[0] = kernel # update the kernel weights in the weights list with the pruned kernel
            layer.set_weights(weights) # set the modified weights back to the layer, which now has some weights pruned to zero

    return model 
    # return the pruned model with the same architecture but with some weights set to zero based on the prune_ratio

def keep_count(total: int, prune_ratio: float) -> int:
    """
    Calculate the number of weights to keep after pruning.
    The prune_ratio is clipped to the range [0.0, 0.95] to prevent excessive pruning 
    that could lead to a non-functional model.
    """
    ratio = float(np.clip(prune_ratio, 0.0, 0.95)) 
    # clip the prune_ratio to be between 0.0 and 0.95 to avoid pruning too much of the model, 
    # which could lead to a non-functional model
    # if ratio is outside of the range, it will be set to the nearest boundary (0.0 or 0.95)
    return max(1, min(total, int(round(total * (1.0 - ratio)))))
    # calculate the number of weights to keep after pruning based on the total number of weights and the prune_ratio,
    # ensuring that at least one weight is kept and not more than the total number of weights

def prune_neurons(base_model: keras.Model, prune_ratio: float) -> keras.Model:
    """
    Prune entire neurons (Dense layer units) with the smallest L1-norm (sum of absolute values) 
    of their outgoing weights. This is a structured pruning method that zeros out entire neurons 
    based on the L1-norm of their outgoing weights. The prune_ratio determines the percentage of neurons to prune 
    (e.g., 0.5 means pruning 50% of the neurons in the Dense layer). After pruning, the model is recompiled for classification tasks.
    """

    model = keras.models.clone_model(base_model) # create a new model with the same architecture as the base model
    model.set_weights(base_model.get_weights()) # copy the weights from the base model to the new model

    dense1 = model.get_layer("dense1") 
    # get the Dense layer named "dense1" from the model, which is the layer we want to prune neurons from

    kernel, bias = dense1.get_weights()
    # get the kernel and bias weights of the "dense1" layer, 
    # where kernel is a 2D array of shape (input_units, output_units)

    old_units = kernel.shape[1] 
    # get the number of output units (neurons) in the Dense layer, which is the second dimension of the kernel shape

    remove_count = int(old_units * prune_ratio)
    # calculate the number of neurons to prune based on the old number of units and the prune_ratio

    scores = np.sum(np.abs(kernel), axis=0)
    # calculate the L1-norm (sum of absolute values) of the outgoing weights for each neuron 
    # by summing the absolute values of the kernel weights along the input axis (axis=0), 
    # resulting in a 1D array of scores for each neuron

    remove = np.argsort(scores)[:remove_count]
    # get the indices of the neurons to prune by sorting the scores 
    # and taking the indices of the lowest remove_count scores

    kernel[:, remove] = 0.0 # set the kernel weights of the pruned neurons to zero, effectively removing their contribution to the output
    bias[remove] = 0.0 # set the bias weights of the pruned neurons to zero, ensuring that they do not contribute to the output

    dense1.set_weights([kernel, bias])
    # set the modified kernel and bias weights back to the "dense1" layer, which now has some neurons pruned to zero based on the prune_ratio

    compile_for_classification(model)
    # recompile the model for classification tasks after modifying the weights to ensure that the 
    # changes take effect and that the model is ready for inference

    return model
    # return the pruned model with the same architecture but with some neurons in the "dense1" layer set to zero based on the prune_ratio

def prune_channels(base_model: keras.Model, prune_ratio: float) -> keras.Model:
    """
    Prune entire channels (Conv2D layer filters) with the smallest L1-norm (sum of absolute values) 
    of their outgoing weights. This is a structured pruning method that zeros out entire channels 
    based on the L1-norm of their outgoing weights. The prune_ratio determines the percentage of channels to prune 
    (e.g., 0.5 means pruning 50% of the channels in the Conv2D layer). 
    After pruning, the model is recompiled for classification tasks.
    """

    model = keras.models.clone_model(base_model) # create a new model with the same architecture as the base model
    model.set_weights(base_model.get_weights()) # copy the weights from the base model to the new model

    conv1 = model.get_layer("conv1") 
    # get the Conv1D layer named "conv1" from the model, which is the layer we want to prune channels from

    kernel, bias = conv1.get_weights()
    # get the kernel and bias weights of the "conv1" layer, where kernel 
    # is a 3D array of shape (kernel_size, input_channels, output_channels)

    old_channels = kernel.shape[2] 
    # get the number of output channels (filters) in the Conv2D layer, which is the third dimension of the kernel shape
    
    remove_count = int(old_channels * prune_ratio)
    # calculate the number of channels to prune based on the old number of channels and the prune_ratio

    print("Conv1 channels:", old_channels)
    print("Removing:", remove_count)
    # print the number of channels in the Conv1D layer and the number of channels that will be removed based on the prune_ratio for debugging purposes

    scores = np.sum(np.abs(kernel), axis=(0, 1))
    # calculate the L1-norm (sum of absolute values) of the outgoing weights for each channel 
    # by summing the absolute values of the kernel weights along the kernel_size and input_channels axes (axis=(0, 1)), 
    # resulting in a 1D array of scores for each channel

    remove = np.argsort(scores)[:remove_count]
    # get the indices of the channels to prune by sorting the scores 
    # and taking the indices of the lowest remove_count scores

    kernel[:, :, remove] = 0.0 # set the kernel weights of the pruned channels to zero, effectively removing their contribution to the output
    bias[remove] = 0.0 # set the bias weights of the pruned channels to zero, ensuring that they do not contribute to the output

    conv1.set_weights([kernel, bias])
    # set the modified kernel and bias weights back to the "conv1" layer, 
    # which now has some channels pruned to zero based on the prune_ratio

    compile_for_classification(model) # recompile the model for classification tasks after modifying the weights to ensure that the changes take effect and that the model is ready for inference

    return model
    # return the pruned model with the same architecture but with some 
    # channels in the "conv1" layer set to zero based on the prune_ratio


# Representative data generator calibrates activation ranges for full INT8 TFLite conversion.
def make_representative_dataset(x: np.ndarray, sample_count: int):
    """
    Create a representative dataset for TFLite conversion calibration.
    The representative dataset is used during TFLite conversion to calibrate 
    the activation ranges for quantization, especially when converting to full INT8 precision.
    """
    limit = max(1, min(int(sample_count), len(x))) 
    # determine the number of samples to use for the representative dataset, 
    # ensuring it's at least 1 and not more than the total number of samples in x

    def representative_dataset():
        for index in range(limit):
            yield [x[index : index + 1].astype(np.float32)] 
            # yield one sample at a time from x, 
            # reshaped to have a batch dimension of 1 and 
            # converted to float32, as required by the TFLite converter

    return representative_dataset
    # meaning the function returns a generator function that can be called by the TFLite converter to get representative samples for calibration during quantization

# ---------------------------------------------------------------------------
# TFLite export
# ---------------------------------------------------------------------------

def export_tflite(
    model,
    artifacts_dir,
    tflite_model,
    tflite_mode="fp32",
    representative_data=None
):
    """
    Export the given Keras model to TFLite format.
    The model is first saved in Keras format and then exported to a SavedModel format, 
    which is required for TFLite conversion.
    Returns the path to the exported TFLite model file.
    """

    saved_model_dir = artifacts_dir / f"{tflite_model}_saved_model"
    keras_path = artifacts_dir / f"{tflite_model}.keras"
    tflite_path = artifacts_dir / f"{tflite_model}.tflite"

    model.save(str(keras_path)) # save the Keras model to a .keras file in the artifacts directory (this happens "locally" in the docker container)
    if saved_model_dir.exists():
        shutil.rmtree(saved_model_dir) # remove the existing saved_model_dir if it already exists to avoid conflicts during export
    model.export(str(saved_model_dir)) # export the Keras model to the SavedModel format, which is required for TFLite conversion

    converter = tf.lite.TFLiteConverter.from_saved_model(str(saved_model_dir))
    # create a TFLiteConverter object from the saved model directory, 
    # which will be used to convert the model to TFLite format

    if tflite_mode == "int8":

        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        # set the optimization flag to DEFAULT, which enables quantization during TFLite conversion,

        converter.representative_dataset = \
            make_representative_dataset(
                representative_data,
                sample_count=100
            ) # set the representative dataset for calibration during quantization, 
              # using the make_representative_dataset function to create a generator that 
              # yields samples from the representative_data

        converter.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS_INT8
        ] # specify that the target specification for supported operations is TFLITE_BUILTINS_INT8,

        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        # set the inference input and output types to int8, which is required for full integer quantization

    tflite_bytes = converter.convert()
    # convert the model to TFLite format, which returns the TFLite model as a byte string

    tflite_path.write_bytes(tflite_bytes)
    # write the TFLite model bytes to a .tflite file in the artifacts directory

    print(
        f"\nTFLite model -> {tflite_path} "
        f"({len(tflite_bytes) / 1024:.1f} KB)"
    )

    return tflite_path


def verify_tflite(tflite_path: Path,
                  X_test: np.ndarray, y_test: np.ndarray) -> None:
    """
    Run the TFLite interpreter on test samples to confirm the converted
    model produces correct predictions.
    """
    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    interpreter.allocate_tensors()
    # create a TFLite interpreter for the converted model and allocate tensors for it,
    # which prepares the interpreter for inference

    inp_detail = interpreter.get_input_details()[0]
    out_detail = interpreter.get_output_details()[0]
    # get the input and output details of the TFLite model, 
    # which include information about the expected 
    # input shape, data type, and quantization parameters

    n = min(len(X_test), 30) # limit the number of test samples to verify to 30 for a quick check, or use all samples if there are fewer than 30
    correct = 0
    for i in range(n):
        input_data = X_test[i : i + 1] # get one test sample at a time, reshaped to have a batch dimension of 1

        if inp_detail["dtype"] == np.int8: 
            # if the input data type expected by the TFLite model is int8, we need to quantize the input data accordingly

            scale, zero_point = inp_detail["quantization"]
            # quantize the input data from float32 to int8 using the scale and zero point from the input details

            input_data = (
                input_data / scale + zero_point
            ).astype(np.int8)
            # scale the input data by dividing by the scale, add the zero point to shift it, 
            # and convert it to int8 data type for compatibility with the TFLite model

        else:
            input_data = input_data.astype(np.float32)
            # if the input data type is not int8, we ensure it is 
            # in float32 format for compatibility with the TFLite model

        interpreter.set_tensor(inp_detail["index"], input_data) # set the input tensor of the TFLite interpreter to the prepared input data for the current test sample
        interpreter.invoke() # run inference with the TFLite interpreter on the input data
        output = interpreter.get_tensor(out_detail["index"]) # get the output tensor from the TFLite interpreter after inference, which contains the predicted probabilities for each class

        if out_detail["dtype"] == np.int8:
            # if the output data type of the TFLite model is int8, 
            # we need to dequantize the output data back to float32 for interpretation

            scale, zero_point = out_detail["quantization"]
            # dequantize the output data from int8 to float32 using the scale and zero point from the output details

            output = scale * (output.astype(np.float32) - zero_point)
            # dequantize the output data by first converting it to float32, 
            # subtracting the zero point to shift it back, and then 
            # multiplying by the scale to restore the original range of values

        pred = int(np.argmax(output)) 
        # get the predicted class index by taking the argmax of the 
        # output probabilities, and convert it to an integer
        if pred == int(y_test[i]): 
            # compare the predicted class index with the true class index for the current test sample

            correct += 1

    accuracy = correct / n # calculate the accuracy of the TFLite model on the verified test samples by dividing the number of correct predictions by the total number of samples verified

    print(
        f"TFLite verification: "
        f"{correct}/{n} correct "
        f"({accuracy * 100:.2f}%)"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args() # parse command-line arguments for training and conversion settings

    tf.keras.utils.set_random_seed(args.seed) # set the random seed for TensorFlow to ensure reproducibility of results across runs
    np.random.seed(args.seed) # set the random seed for NumPy to ensure reproducibility of results across runs
    rng = np.random.default_rng(args.seed) # create a random number generator with the specified seed for use in data augmentation and other random operations

    data_dir      = Path("recordings_padded")
    artifacts_dir = Path(args.artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if args.remote_data: 
        # if a remote data directory is specified, synchronize the local data directory with the remote data source 
        # (e.g., Bobby) to ensure that the latest recordings are available for training
        sync_from_pi(args.remote_data, data_dir) # synchronize the local data directory with the remote data source using the sync_from_pi function, which handles the data transfer from the remote location to the local machine

    print("--- Loading data ---")
    X, y, class_names = load_recordings(
        data_dir,
        Path(args.labels_file),
        sequence_length=args.sequence_length,
        max_file_rows=args.max_file_rows
    ) # load the recordings from the specified data directory and labels file,
    # applying the specified sequence length and maximum file rows constraints

    print(f"Total recordings: {X.shape[0]}  shape per sample: {X.shape[1:]}") # print the total number of recordings loaded and the shape of each sample (sequence length and number of axes)
    n_classes = len(class_names) 
    # determine the number of unique classes based on the class names extracted from the loaded recordings

    print("\nClass mapping:")
    for idx, name in enumerate(class_names):
        print(idx, "->", name) 
        # print the mapping of class indices to class names for reference during training and evaluation

    print("\nFiles per class:") 
    # print the number of files for each class based on the labels file, which provides insight 
    #   into the class distribution in the dataset and can help identify any class imbalance issues

    labels_df = pd.read_csv(args.labels_file)

    label_counts = Counter(labels_df["label"]) 
    # count the occurrences of each class label in the labels DataFrame using a Counter, 
    # which creates a dictionary-like object where keys are class labels and values are 
    # the counts of files for each label

    for label in sorted(label_counts.keys()):
        print(f"{label}: {label_counts[label]} files")
        # print the number of files for each class label in sorted order, 
        # which provides a clear overview of the class distribution in the dataset

    print("\n--- Splitting ---")
    X_temp, X_test, y_temp, y_test = train_test_split(
        X,
        y,
        test_size=args.test_split, # split the dataset into a temporary set (X_temp, y_temp) and a test set (X_test, y_test) based on the specified test split ratio
        random_state=args.seed,
        stratify=y # stratify the split based on the labels to ensure that the class distribution is preserved in both the training and test sets
    )

    val_relative = args.val_split / (1.0 - args.test_split) 
    # calculate the relative validation split size based on the original validation split and the test split,
    # to ensure that the validation set is the correct proportion of the remaining data after the test split

    X_train, X_val, y_train, y_val = train_test_split(
        X_temp,
        y_temp,
        test_size=val_relative,
        random_state=args.seed,
        stratify=y_temp # stratify the split based on the labels in the temporary set to ensure that the class distribution is preserved in both the training and validation sets
    )

    print(
        f"Split: train={len(y_train)} "
        f"val={len(y_val)} "
        f"test={len(y_test)}"
    )

    print("\n--- Model ---")
    baseline = make_model(
        sequence_length=args.sequence_length,
        n_axes=N_AXES,
        n_classes=n_classes,
        filters=args.filters, # number of filters in the first Conv1D layer, which is a hyperparameter that can be adjusted to control the model's capacity and performance
        dense_units=args.dense_units
    )
    baseline.summary()
    # create the baseline model using the make_model function with the specified sequence length, 
    # number of axes, number of classes, filters, and dense units, and print the model summary 
    # to show the architecture and number of parameters

    # Augment training set only
    X_train, y_train = augment(X_train, y_train, rng)
    # apply data augmentation to the training set using the augment function, 
    # which increases the effective dataset size by applying label-preserving transformations 
    # to the training samples, while keeping the validation and test sets unchanged for unbiased evaluation

    print("\n--- Training ---")
    train_model(baseline, X_train, y_train, X_val, y_val,
                epochs=args.epochs, batch_size=args.batch_size)
    # train the baseline model using the train_model function with the augmented training data,
    # the validation data, and the specified number of epochs and batch size
    
    print("\n--- Pruning ---")
    synapse = prune_synapses(baseline, 0.6)
    # prune the baseline model by applying synapse pruning with a prune ratio of 0.6, 
    # which zeros out individual weights with the smallest absolute values, and returns the pruned model

    neuron = prune_neurons(baseline, 0.85)
    # prune the baseline model by applying neuron pruning with a prune ratio of 0.82,
    # which zeros out entire neurons (Dense layer units) with the smallest L1-norm

    print("\nChannel pruning: ")
    channel = prune_channels(baseline, 0.155)
    # prune the baseline model by applying channel pruning with a prune ratio of 0.15,
    # which zeros out entire channels (Conv1D layer filters) with the smallest L1-norm

    print("\nCombined pruning: ")
    combined = prune_channels(baseline, 0.155) # Requirement for EX05
    combined = prune_neurons(combined, 0.85)
    # apply channel pruning followed by neuron pruning to the baseline model,
    # which first zeros out entire channels in the Conv1D layer and then zeros out entire

    models = {
        "baseline": baseline,
        "synapse_pruned": synapse,
        "neuron_pruned": neuron,
        "channel_pruned": channel,
        "combined_pruned": combined,
    }

    print("\n--- Model Evaluation ---")
    metrics_rows = []
    evaluation_results = {}

    for name, model in models.items():

        loss, acc = model.evaluate(X_test, y_test, verbose=0)

        evaluation_results[name] = {
            "loss": loss,
            "accuracy": acc
        }

        total, nonzero = count_nonzero_weights(model)

        metrics_rows.append({
            "model": name,
            "method": name,
            "test_accuracy": f"{acc:.6f}",
            "parameter_sparsity": f"{1.0 - (nonzero / total):.6f}",
        })

        print(f"{name:20s} | loss={loss:.4f} | accuracy={acc*100:.2f}%")
        # evaluate the model on the test set to obtain the loss and accuracy,
        # which provides insight into the model's performance on unseen data after training and pruning

    print("\n--- Test set evaluation for Baseline ---")
    test_loss, test_acc = baseline.evaluate(X_test, y_test, verbose=0)
    # evaluate the baseline model on the test set to obtain the loss and accuracy,
    # which provides a baseline performance metric for comparison with the pruned models and the TFLite models
    print(f"Test loss:     {test_loss:.4f}")
    print(f"Test accuracy: {test_acc * 100:.2f} %")

    if test_acc < 0.70:
        print(
            "\nWARNING: accuracy below 70 %. Try:\n"
            "  • Collect more samples (target >= 60 per class)\n"
            "  • Add a garbage class (idle movement recordings)\n"
            "  • --filters 64 --dense-units 128\n"
            "  • Adjust --window-size to match gesture duration\n"
            "  • --epochs 100 (EarlyStopping will stop automatically)"
        )

    # --------------------------------------------------------------------------
    # Confusion matrix before pruning (enables to check if there's maybe class specific issues)
    # --------------------------------------------------------------------------

    # Baseline
    predictions = baseline.predict(X_test)
    y_pred = np.argmax(predictions, axis=1)
    # compute the confusion matrix for the baseline model by comparing the true labels (y_test) 
    # with the predicted labels (y_pred) obtained from the model's predictions on the test set

    cm = confusion_matrix(y_test, y_pred)

    print("\nConfusion Matrix for Baseline: ")
    print(cm)

    # Synapse pruned
    predictions = synapse.predict(X_test)
    y_pred = np.argmax(predictions, axis=1)

    cm = confusion_matrix(y_test, y_pred)
    print("\nConfusion Matrix for Synapse Pruned: ")
    print(cm)

    # Neuron pruned
    predictions = neuron.predict(X_test)
    y_pred = np.argmax(predictions, axis=1)

    cm = confusion_matrix(y_test, y_pred)
    print("\nConfusion Matrix for Neuron Pruned: ")
    print(cm)

    # Channel pruned
    predictions = channel.predict(X_test)
    y_pred = np.argmax(predictions, axis=1)

    cm = confusion_matrix(y_test, y_pred)
    print("\nConfusion Matrix for Channel Pruned: ")
    print(cm)

    # Combined pruned
    predictions = combined.predict(X_test)
    y_pred = np.argmax(predictions, axis=1)

    cm = confusion_matrix(y_test, y_pred)
    print("\nConfusion Matrix for Combined Pruned: ")
    print(cm)

    print("\n--- TFLite export ---")

    ### EXPORT OF BASELINE MODEL WITHOUT QUANTIZATION (FP32)
    export_tflite(baseline, artifacts_dir, "baseline", representative_data=X_train)
    # export the baseline model to TFLite format using the export_tflite function,
    # which saves the model in Keras format, exports it to SavedModel format, and
    # converts it to TFLite format, writing the TFLite model file to the artifacts directory,
    # using the training data as representative data for calibration during quantization if needed

    baseline_path = artifacts_dir / "baseline.tflite"
    print(f"\nFinished! Baseline artifact written to: {baseline_path}")

    ### EXPORT OF SYNAPSE PRUNED MODEL WITHOUT QUANTIZATION (FP32)
    export_tflite(synapse, artifacts_dir, "synapse_pruned", representative_data=X_train)
    # same as above, but for the synapse pruned model

    synapse_path = artifacts_dir / "synapse_pruned.tflite"
    print(f"\nFinished! Synapse pruned artifact written to: {synapse_path}")

    ### EXPORT OF NEURON PRUNED MODEL WITHOUT QUANTIZATION (FP32)
    export_tflite(neuron, artifacts_dir, "neuron_pruned", representative_data=X_train)
    # same as above, but for the neuron pruned model

    neuron_path = artifacts_dir / "neuron_pruned.tflite"
    print(f"\nFinished! Neuron pruned artifact written to: {neuron_path}")

    ### EXPORT OF CHANNEL PRUNED MODEL WITHOUT QUANTIZATION (FP32)
    export_tflite(channel, artifacts_dir, "channel_pruned", representative_data=X_train)
    # same as above, but for the channel pruned model

    channel_path = artifacts_dir / "channel_pruned.tflite"
    print(f"\nFinished! Channel pruned artifact written to: {channel_path}")

    ### EXPORT OF COMBINED PRUNED MODEL WITHOUT QUANTIZATION (FP32)
    export_tflite(
        combined,
        artifacts_dir,
        "combined_pruned",
        representative_data=X_train
    )
    # same as above, but for the combined pruned model

    combined_path = artifacts_dir / "combined_pruned.tflite"
    print(f"\nFinished! Combined pruned artifact written to: {combined_path}")

    ### EXPORT OF BASELINE MODEL WITH FULL INTEGER QUANTIZATION (INT8)
    export_tflite(
        baseline,
        artifacts_dir,
        "baseline_int8",
        tflite_mode="int8",
        representative_data=X_train
    )
    # export the baseline model to TFLite format with full integer quantization (int8) 
    # using the export_tflite function, which saves the model in Keras format, 
    # exports it to SavedModel format, and converts it to TFLite format with int8 quantization, 
    # writing the TFLite model file to the artifacts directory

    int8_path = artifacts_dir / "baseline_int8.tflite"
    print(f"\nFinished! Baseline int8 artifact written to: {int8_path}")
    metrics_rows.append({
        "model": "baseline_int8",
        "method": "int8 quantization",
        "test_accuracy": f"{evaluation_results['baseline']['accuracy']:.6f}",
        "parameter_sparsity": "0.000000",
    })

    ### EXPORT OF COMBINED PRUNED MODEL WITH FULL INTEGER QUANTIZATION (INT8)
    export_tflite(
        combined,
        artifacts_dir,
        "combined_pruned_int8",
        tflite_mode="int8",
        representative_data=X_train
    )
    # export the combined pruned model to TFLite format with full integer quantization (int8)
    # using the export_tflite function, which saves the model in Keras format,
    # exports it to SavedModel format, and converts it to TFLite format with int8 quantization,
    # writing the TFLite model file to the artifacts directory

    combined_int8_path = artifacts_dir / "combined_pruned_int8.tflite"
    print(f"\nFinished! Combined pruned int8 artifact written to: {combined_int8_path}")

    total, nonzero = count_nonzero_weights(combined)

    metrics_rows.append({
        "model": "combined_pruned_int8",
        "method": "combined pruning + int8",
        "test_accuracy": f"{evaluation_results['combined_pruned']['accuracy']:.6f}",
        "parameter_sparsity": f"{1.0 - (nonzero / total):.6f}",
    })

    metrics_path = artifacts_dir / "model_metrics.csv"

    with metrics_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "model",
                "method",
                "test_accuracy",
                "parameter_sparsity",
            ],
        )
        writer.writeheader()
        writer.writerows(metrics_rows)

    print(f"Saved metrics: {metrics_path}")

    return 0

##bash: python train.py --remote-data pi@192.168.1.42:/home/pi/recordings/
# makes it possible for us to not have the data in the docker container but get it form the pi

if __name__ == "__main__":
    raise SystemExit(main())