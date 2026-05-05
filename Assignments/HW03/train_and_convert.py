#!/usr/bin/env python3

"""Exercise 3: Training a CNN model on the collected data and export to TFLite"""

# Standard library imports
import argparse
from pathlib import Path

import numpy as np
import tensorflow as tf
from data_sync import sync_from_pi
import pandas as pd




"""CLI arguments with defaults and help strings"""

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a CNN model on the collected data and export to TFLite"
    )

    # default --data-dir is set to "recordings_clean" which is the local directory containing the CSV files
    parser.add_argument(
        "--data-dir",
        default="recordings_clean",
        help=(
            "This Folder contains the CSV recordings",
        ),
    )

    # default --artifacts-dir is set to "artifacts" where the trained model files will be saved
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Path to where the .tflite and .keras files are writtento",
    )

    # default --window-size is set to 50 timesteps, which means each training sample will consist of 50 consecutive rows from the CSV files
    parser.add_argument(
        "--window-size",
        type=int,
        default=50,
        help=(
            "number of timesteps per training sample "
            "the recordings have variable lengths, so we extract non-overlapping windows of this window size from each file"
        ),
    )

    # default --labels-file is set to "labels.csv" which is a CSV file mapping file IDs to their correct labels ("A", "B", "C" or garbage class)
    parser.add_argument(
        "--labels-file",
        default="/workspaces/EAI4-DockerContainer/labels.csv",
        help="CSV mapping file_id -> label"
    )
    parser.add_argument("--epochs",      type=int,   default=60)
    parser.add_argument("--batch-size",  type=int,   default=16)
    parser.add_argument("--val-split",   type=float, default=0.15) # validation split is 15% of the data
    parser.add_argument("--test-split",  type=float, default=0.15) # test split is 15% as well, leaving 70% for training
    parser.add_argument("--filters",     type=int,   default=32)
    parser.add_argument("--dense-units", type=int,   default=64)
    parser.add_argument(
        "--max-file-rows",
        type=int,
        default=300,
        help=(
            "extremely long CSV files with more than this many data rows are likely idle/accidental recordings and are skipped during loading"
        ),
    )
    parser.add_argument("--seed", type=int, default=42) # set seed as argument for reproducibility

    parser.add_argument(
    "--remote-data",
    default=None,
    help="optional rsync source: kit-18@10.42.0.1:/home/kit-18/Documents/EAI/EAI4-Babsi-Bobby-Collab/Assignments/HW03/recordings_clean/ ./recordings_clean/"
    ) # to sync data from the Pi to the local machine before training

    return parser.parse_args()




"""Data loading"""

# Sensor columns to use 
# dropped timestamp_ms (col 0)
SENSOR_COLS = [1, 2, 3, 4, 5, 6, 7, 8, 9]  # used columns: accel xyz, gyro xyz, mag xyz
N_AXES = len(SENSOR_COLS)  # 9 sensor axes in total


"""Load CSV recordings, extract fixed-length windows, and map labels"""
def load_recordings(data_dir: Path, labels_path: Path, window_size: int, max_file_rows: int,
                    ) -> tuple[np.ndarray, np.ndarray, list[str]]:

    labels_df = pd.read_csv(labels_path, dtype={"id": str}) # ensure file_id is read as string to match CSV filenames
    label_map = dict(zip(labels_df["id"].astype(str), labels_df["label"])) # mapping from file_id to label character (e.g. "A", "B", "C", or grabage class)
    csv_files = sorted(data_dir.glob("*.csv")) # get list of all CSV files in the data directory

    print("Sample label_map keys:", list(label_map.keys())[:5])
    print("Example file_id:", csv_files[0].stem)

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}") # sanity check to ensure we have data to load

    # label_to_windows is a dictionary that will map each label to list of numpy arrays
    label_to_windows: dict[str, list[np.ndarray]] = {}

    skipped_long  = 0 # count of files skipped for being too long (likely idle/accidental recordings)
    skipped_short = 0 # same for short files that can't even fill one window

    for csv_path in csv_files:
        # Get label from filename: last character before ".csv"
        file_id = csv_path.stem
        label_char = label_map.get(file_id)

        if label_char is None:
            print(f"WARNING: no label for {csv_path.name}, skipping")
            continue

        # load sensor data columns from CSV, skipping header and timestamp column
        try:
            raw = np.loadtxt(
                csv_path,
                delimiter=",",
                skiprows=1,
                usecols=SENSOR_COLS, # only load the sensor columns (accel xyz, gyro xyz, mag xyz)
                dtype=np.float32,
            )
        except Exception as exc:
            print(f"  WARNING: not able toread {csv_path.name}: {exc}")
            continue

        if raw.ndim == 1:
            raw = raw[np.newaxis, :]  # single-row edge case

        n_rows = raw.shape[0] #  number of data rows in the CSV file (after loading only the sensor columns)

        # skip suspiciously long files (likely idle/accidental recordings)
        if n_rows > max_file_rows:
            print(f"  SKIP (too long, {n_rows} rows): {csv_path.name}")
            skipped_long += 1
            continue

        # skip files too short for even one window
        if n_rows < window_size:
            print(f"  SKIP (too short, {n_rows} rows < window {window_size}): {csv_path.name}")
            skipped_short += 1
            continue

        # extract non-overlapping windows
        n_windows = n_rows // window_size
        for i in range(n_windows):
            window = raw[i * window_size : (i + 1) * window_size]
            label_to_windows.setdefault(label_char, []).append(window)

    if not label_to_windows:
        raise ValueError("No usable samples found after filtering")

    # print class distribution and summary of skipped files
    class_names = sorted(label_to_windows.keys())
    print(f"\nClasses: {class_names}")
    for c in class_names:
        print(f"  '{c}': {len(label_to_windows[c])} windows")
    if skipped_long:
        print(f"  (skipped {skipped_long} file(s) exceeding --max-file-rows)")
    if skipped_short:
        print(f"  (skipped {skipped_short} file(s) shorter than --window-size)")

    # warn if fewer than 4 classes found: the model is designed for 4 classes (A, B, C, garbage) and will most likely underperform with fewer
    if len(class_names) < 4:
        print(
            "\n  NOTE: fewer than 4 classes found "
            "add garbage recordings (files ending in '_-.csv') to train a 4-class model"
        )

    # gather all windows and labels into arrays
    all_windows: list[np.ndarray] = []
    all_labels:  list[int]        = []
    for label_idx, c in enumerate(class_names): # assign integer label indices based on sorted class names 
        for w in label_to_windows[c]:
            all_windows.append(w)
            all_labels.append(label_idx)

    X = np.stack(all_windows, axis=0)       # shape (n_samples, window_size, n_axes)
    y = np.array(all_labels, dtype=np.int32) # shape (n_samples,) with integer class indices
    return X, y, class_names



"""Preprocessing"""

# Z-score normalization and data augmentation functions
def normalize(X_train: np.ndarray, X_val: np.ndarray, X_test: np.ndarray,
              ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    
    mean = X_train.mean(axis=(0, 1), keepdims=True) # compute mean per sensor axis across all samples and time steps, keepdims to allow broadcasting
    std  = X_train.std( axis=(0, 1), keepdims=True) + 1e-8 # compute std per sensor axis, add small epsilon to avoid division by zero

    X_train = (X_train - mean) / std # standardize training set using training mean and std
    X_val   = (X_val   - mean) / std # same standardization applied to validation set using training mean and std
    X_test  = (X_test  - mean) / std # same for test set

    return X_train, X_val, X_test

# Data augmentation: applied only to training set to increase data diversity and to prevent overfitting
def augment(X: np.ndarray, y: np.ndarray, rng: np.random.Generator,
            ) -> tuple[np.ndarray, np.ndarray]:

    aug_X = [X]
    aug_y = [y]

    # Gaussian noise
    aug_X.append(X + rng.normal(0, 0.02, size=X.shape).astype(np.float32))
    aug_y.append(y)

    # Time reversal
    aug_X.append(X[:, ::-1, :])
    aug_y.append(y)

    # Random axis scaling:  each sensor axis gets multiplied by a random factor between 0.9 and 1.1 to simulate natural variability in gesture execution
    scale = rng.uniform(0.9, 1.1, size=(X.shape[0], 1, X.shape[2])).astype(np.float32)
    aug_X.append(X * scale)
    aug_y.append(y)

    return np.concatenate(aug_X, axis=0), np.concatenate(aug_y, axis=0)


# Data splitting: stratified split to maintain class distribution across train/val/test sets
def split_data(X: np.ndarray, y: np.ndarray,
               val_frac: float, test_frac: float,
               seed: int) -> tuple[np.ndarray, ...]:

    rng = np.random.default_rng(seed)
    n_classes = int(y.max()) + 1

    train_idx, val_idx, test_idx = [], [], []

    # for each class, shuffle the indices and split according to specified fractions, ensuring at least one sample in each set if possible
    for c in range(n_classes):
        idx = np.where(y == c)[0].copy()
        rng.shuffle(idx)

        n_test = max(1, int(len(idx) * test_frac))
        n_val  = max(1, int(len(idx) * val_frac))

        test_idx .extend(idx[:n_test])
        val_idx  .extend(idx[n_test : n_test + n_val])
        train_idx.extend(idx[n_test + n_val :])

    # gather function to index into X and y using the generated indices for each set
    def gather(indices: list[int]) -> tuple[np.ndarray, np.ndarray]:
        i = np.array(indices)
        return X[i], y[i]

    X_train, y_train = gather(train_idx)
    X_val,   y_val   = gather(val_idx)
    X_test,  y_test  = gather(test_idx)

    print(f"Split: train={len(y_train)}  val={len(y_val)}  test={len(y_test)}")
    return X_train, y_train, X_val, y_val, X_test, y_test




"""Model: we chose a 1-D CNN architecture"""

def make_model(window_size: int, n_axes: int, n_classes: int,
               filters: int = 32, dense_units: int = 64,
               ) -> tf.keras.Model:
    
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(
                shape=(window_size, n_axes), name="imu_input"), # input shape matches the window size and number of sensor axes

            tf.keras.layers.Conv1D(filters,     kernel_size=3, padding="same", activation="relu", name="conv1"), # first convolutional layer: specified number of filters and kernel size, ReLU activation for non-linearity
            tf.keras.layers.MaxPooling1D(pool_size=2, name="pool1"), # first pooling layer: reduces time resolution by half, reduces overfitting

            tf.keras.layers.Conv1D(filters * 2, kernel_size=3, padding="same", activation="relu", name="conv2"), # second convolutional layer: doubles number of filters to learn more complex features, same kernel size and activation
            tf.keras.layers.MaxPooling1D(pool_size=2, name="pool2"), # second pooling layer: reduces time resolution by half, reduces overfitting

            tf.keras.layers.Conv1D(filters * 2, kernel_size=3, padding="same", activation="relu", name="conv3"), # third convolutional layer: same as second, but with more filters

            tf.keras.layers.GlobalAveragePooling1D(name="gap"), # global average pooling layer: collapses time axis, reducing the number of parameters

            tf.keras.layers.Dense(dense_units, activation="relu", name="dense1"), # first dense layer: learns complex patterns from the pooled features
            tf.keras.layers.Dropout(0.4, name="dropout"), # dropout layer: prevents overfitting by randomly setting a fraction of input units to 0 at each update during training
            tf.keras.layers.Dense(n_classes, activation="softmax", name="output"), # output layer: maps to number of classes with softmax activation
        ],
        name="gesture_1d_cnn",
    )

    # compile the model with Adam optimizer, sparse categorical crossentropy loss (since labels are integer indices), and accuracy metric for evaluation
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model




"""Training: we use EarlyStopping to prevent overfitting and ReduceLROnPlateau to reduce learning rate when validation loss lands on plateau"""

def train_model(model: tf.keras.Model,
                X_train: np.ndarray, y_train: np.ndarray,
                X_val:   np.ndarray, y_val:   np.ndarray,
                epochs: int, batch_size: int) -> None:


    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=15,
            restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=7, verbose=1
        ),
    ]

    # fit model on training set
    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val), # use validation set for monitoring during training
        epochs=epochs, # maximum number of epochs to train
        batch_size=batch_size, # number of samples per gradient update
        callbacks=callbacks, # callbacks for early stopping and learning rate reduction
        verbose=2, # print training progress per epoch
        shuffle=True, # shuffle training data each epoch to improve generalization
    )




"""TFLite export: model saving and conversion to TFLite format for deployment on Raspberry Pi"""

def export_tflite(model: tf.keras.Model, artifacts_dir: Path) -> Path:
    saved_model_dir = artifacts_dir / "saved_model" # directory to save the TensorFlow SavedModel format, required for TFLite conversion
    keras_path      = artifacts_dir / "model.keras" # path to save the Keras model in .keras format, which is a single file containing both architecture and weights
    tflite_path     = artifacts_dir / "model.tflite" # path to save the converted TFLite model

    model.save(str(keras_path))
    model.export(str(saved_model_dir))

    converter    = tf.lite.TFLiteConverter.from_saved_model(str(saved_model_dir)) # create TFLite converter from the saved model directory
    tflite_bytes = converter.convert() # perform the conversion, resulting in a byte string containing the TFLite model
    tflite_path.write_bytes(tflite_bytes)

    print(f"\nTFLite model -> {tflite_path}  ({len(tflite_bytes) / 1024:.1f} KB)")
    return tflite_path


# TFLite sanity check: is run on a few test samples to check if the converted TFLite model produces correct predictions
def verify_tflite(tflite_path: Path,
                  X_test: np.ndarray, y_test: np.ndarray) -> None:

    interpreter = tf.lite.Interpreter(model_path=str(tflite_path)) # load the TFLite model into an interpreter for inference
    interpreter.allocate_tensors() # allocate memory for the model's input and output tensors

    inp_detail = interpreter.get_input_details()[0] # gets details about the input tensor to know how to feed data into the model
    out_detail = interpreter.get_output_details()[0] # same for output tensor to know how to read predictions

    n = min(len(X_test), 30) # test on 30 samples for a quick verification
    correct = 0
    for i in range(n):
        interpreter.set_tensor(inp_detail["index"], X_test[i : i + 1].astype(np.float32)) # set the input tensor with the test sample, adding batch dimension and ensuring correct data type
        interpreter.invoke() # run inference on the TFLite model
        pred = int(np.argmax(interpreter.get_tensor(out_detail["index"]))) # reads output tensor: contains predicted class probabilities, and takes argmax to get predicted class index
        if pred == int(y_test[i]):
            correct += 1

    print(f"TFLite verification: {correct}/{n} correct on {n} test samples")




"""Main: orchestrates the entire process: data loading, preprocessing, model creation, training, evaluation, and TFLite export 
also handles CLI arguments and optional data syncing from the Raspberry Pi"""

def main() -> int:
    args = parse_args()

    tf.keras.utils.set_random_seed(args.seed)
    np.random.seed(args.seed)
    rng = np.random.default_rng(args.seed)

    data_dir      = Path(args.data_dir)
    artifacts_dir = Path(args.artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if args.remote_data:
        sync_from_pi(args.remote_data, data_dir)

    print("--- Loading data ---")
    X, y, class_names = load_recordings(
        data_dir,
        Path(args.labels_file),
        window_size=args.window_size,
        max_file_rows=args.max_file_rows
    )
    print(f"Total windows: {X.shape[0]}  shape per sample: {X.shape[1:]}")
    n_classes = len(class_names)

    print("\n--- Splitting ---")
    X_train, y_train, X_val, y_val, X_test, y_test = split_data(
        X, y, val_frac=args.val_split, test_frac=args.test_split, seed=args.seed
    )

    # Normalise — fit statistics on training set only
    X_train, X_val, X_test = normalize(X_train, X_val, X_test)

    # Augment training set only
    print(f"\nAugmenting training set ({len(y_train)} -> ", end="")
    X_train, y_train = augment(X_train, y_train, rng)
    print(f"{len(y_train)} windows)")

    print("\n--- Model ---")
    model = make_model(
        window_size=args.window_size, n_axes=N_AXES, n_classes=n_classes,
        filters=args.filters, dense_units=args.dense_units,
    )
    model.summary()

    print("\n--- Training ---")
    train_model(model, X_train, y_train, X_val, y_val,
                epochs=args.epochs, batch_size=args.batch_size)

    print("\n--- Test set evaluation ---")
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"Test loss:     {test_loss:.4f}")
    print(f"Test accuracy: {test_acc * 100:.2f} %")

    if test_acc < 0.70:
        print(
            "\nWARNING: accuracy below 70 %")

    print("\n--- TFLite export ---")
    tflite_path = export_tflite(model, artifacts_dir)
    verify_tflite(tflite_path, X_test, y_test)

    print(f"\nFinished :-) Artifacts written to: {artifacts_dir}/")
    return 0


# Entry point: calls main() and exits with its return code
if __name__ == "__main__":
    raise SystemExit(main())