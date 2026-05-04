#!/usr/bin/env python3
"""
Exercise 3 – Gesture classifier: training + TFLite conversion
Dataset: RTIMULib recordings from HW02 (classes A, B, C + garbage)
Model:   1-D CNN operating on fixed-length windows of IMU time-series

Data format (from HW02 logger_recording.cpp):
    timestamp_ms, label, accel_x, accel_y, accel_z,
                         gyro_x,  gyro_y,  gyro_z,
                         mag_x,   mag_y,   mag_z
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import tensorflow as tf
from data_sync import sync_from_pi

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a 1-D CNN on HW02 gesture data and export to TFLite."
    )
    parser.add_argument(
        "--data-dir",
        default="recordings",
        help=(
            "Folder containing the raw CSV recordings from HW02. "
            "Class is inferred from the filename suffix, e.g. '..._A.csv'."
        ),
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Where .tflite and .keras files are written.",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=50,
        help=(
            "Number of timesteps per training sample. "
            "Recordings have variable length; we extract one or more "
            "non-overlapping windows of this size from each file."
        ),
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
            "(e.g. the 1372-row outlier in the HW02 dataset)."
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

# Sensor columns to use - we drop timestamp_ms (col 0) and label (col 1)
SENSOR_COLS = [2, 3, 4, 5, 6, 7, 8, 9, 10]  # accel xyz, gyro xyz, mag xyz
N_AXES = len(SENSOR_COLS)  # 9


def load_recordings(data_dir: Path, window_size: int, max_file_rows: int,
                    ) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Load all CSV files from data_dir.

    Filename convention (from HW02):  YYYY-MM-DD_HH-MM-SS_<LABEL>.csv
    The last character before '.csv' is the class label (A / B / C / -).

    Because recordings have variable lengths we use a sliding-window
    approach: each file contributes floor(n_rows / window_size) non-
    overlapping windows.  This naturally augments longer recordings.
    """
    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    # label_char -> list of windows
    label_to_windows: dict[str, list[np.ndarray]] = {}

    skipped_long  = 0
    skipped_short = 0

    for csv_path in csv_files:
        # Extract label from filename: last character before ".csv"
        label_char = csv_path.stem[-1].upper()

        try:
            raw = np.loadtxt(
                csv_path,
                delimiter=",",
                skiprows=1,
                usecols=SENSOR_COLS,
                dtype=np.float32,
            )
        except Exception as exc:
            print(f"  WARNING: not able toread {csv_path.name}: {exc}")
            continue

        if raw.ndim == 1:
            raw = raw[np.newaxis, :]  # single-row edge case

        n_rows = raw.shape[0]

        # Skip suspiciously long files (likely idle/accidental recordings)
        if n_rows > max_file_rows:
            print(f"  SKIP (too long, {n_rows} rows): {csv_path.name}")
            skipped_long += 1
            continue

        # Skip files too short for even one window
        if n_rows < window_size:
            print(f"  SKIP (too short, {n_rows} rows < window {window_size}): {csv_path.name}")
            skipped_short += 1
            continue

        # Extract non-overlapping windows
        n_windows = n_rows // window_size
        for i in range(n_windows):
            window = raw[i * window_size : (i + 1) * window_size]
            label_to_windows.setdefault(label_char, []).append(window)

    if not label_to_windows:
        raise ValueError("No usable samples found after filtering.")

    class_names = sorted(label_to_windows.keys())
    print(f"\nClasses: {class_names}")
    for c in class_names:
        print(f"  '{c}': {len(label_to_windows[c])} windows")
    if skipped_long:
        print(f"  (skipped {skipped_long} file(s) exceeding --max-file-rows)")
    if skipped_short:
        print(f"  (skipped {skipped_short} file(s) shorter than --window-size)")

    if len(class_names) < 4:
        print(
            "\n  NOTE: fewer than 4 classes found. "
            "Add garbage recordings (files ending in '_-.csv') to train a 4-class model."
        )

    all_windows: list[np.ndarray] = []
    all_labels:  list[int]        = []
    for label_idx, c in enumerate(class_names):
        for w in label_to_windows[c]:
            all_windows.append(w)
            all_labels.append(label_idx)

    X = np.stack(all_windows, axis=0)       # (n_samples, window_size, 9)
    y = np.array(all_labels, dtype=np.int32)
    return X, y, class_names


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

def normalize(X_train: np.ndarray, X_val: np.ndarray, X_test: np.ndarray,
              ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Z-score normalization per sensor axis.
    Statistics are computed ONLY on the training split to avoid data leakage.
    mean/std shape: (1, 1, 9) - broadcasts over samples and timesteps.
    """
    mean = X_train.mean(axis=(0, 1), keepdims=True)
    std  = X_train.std( axis=(0, 1), keepdims=True) + 1e-8

    X_train = (X_train - mean) / std
    X_val   = (X_val   - mean) / std
    X_test  = (X_test  - mean) / std
    return X_train, X_val, X_test


def augment(X: np.ndarray, y: np.ndarray, rng: np.random.Generator,
            ) -> tuple[np.ndarray, np.ndarray]:
    """
    Label-preserving augmentations to increase effective dataset size:
      • Gaussian noise  – simulates IMU measurement noise
      • Time reversal   – gesture backwards is still the same class
      • Axis scaling    – small random gain per sensor axis (±10%)
    Applied only to the training set - never to val or test.
    """
    aug_X = [X]
    aug_y = [y]

    # Gaussian noise
    aug_X.append(X + rng.normal(0, 0.02, size=X.shape).astype(np.float32))
    aug_y.append(y)

    # Time reversal
    aug_X.append(X[:, ::-1, :])
    aug_y.append(y)

    # Random axis scaling
    scale = rng.uniform(0.9, 1.1, size=(X.shape[0], 1, X.shape[2])).astype(np.float32)
    aug_X.append(X * scale)
    aug_y.append(y)

    return np.concatenate(aug_X, axis=0), np.concatenate(aug_y, axis=0)


def split_data(X: np.ndarray, y: np.ndarray,
               val_frac: float, test_frac: float,
               seed: int) -> tuple[np.ndarray, ...]:
    """
    Stratified train / val / test split (class-by-class).
    Ensures every class is proportionally represented in all subsets.
    Test set is carved first so it is never influenced by training choices.
    """
    rng = np.random.default_rng(seed)
    n_classes = int(y.max()) + 1

    train_idx, val_idx, test_idx = [], [], []

    for c in range(n_classes):
        idx = np.where(y == c)[0].copy()
        rng.shuffle(idx)

        n_test = max(1, int(len(idx) * test_frac))
        n_val  = max(1, int(len(idx) * val_frac))

        test_idx .extend(idx[:n_test])
        val_idx  .extend(idx[n_test : n_test + n_val])
        train_idx.extend(idx[n_test + n_val :])

    def gather(indices: list[int]) -> tuple[np.ndarray, np.ndarray]:
        i = np.array(indices)
        return X[i], y[i]

    X_train, y_train = gather(train_idx)
    X_val,   y_val   = gather(val_idx)
    X_test,  y_test  = gather(test_idx)

    print(f"Split: train={len(y_train)}  val={len(y_val)}  test={len(y_test)}")
    return X_train, y_train, X_val, y_val, X_test, y_test


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def make_model(window_size: int, n_axes: int, n_classes: int,
               filters: int = 32, dense_units: int = 64,
               ) -> tf.keras.Model:
    """
    1-D CNN for IMU gesture classification.

    Why Conv1D?
        Our input is a time-series of shape (window_size, n_axes).
        Conv1D slides a small kernel along the TIME axis and learns
        local temporal patterns — e.g. a sharp acceleration spike from
        a wrist flick.  Conv2D would be wrong here because our data has
        no 2-D spatial structure.

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
            tf.keras.layers.Input(shape=(window_size, n_axes), name="imu_input"),

            tf.keras.layers.Conv1D(filters,     kernel_size=3, padding="same", activation="relu", name="conv1"),
            tf.keras.layers.MaxPooling1D(pool_size=2, name="pool1"),

            tf.keras.layers.Conv1D(filters * 2, kernel_size=3, padding="same", activation="relu", name="conv2"),
            tf.keras.layers.MaxPooling1D(pool_size=2, name="pool2"),

            tf.keras.layers.Conv1D(filters * 2, kernel_size=3, padding="same", activation="relu", name="conv3"),

            tf.keras.layers.GlobalAveragePooling1D(name="gap"),

            tf.keras.layers.Dense(dense_units, activation="relu", name="dense1"),
            tf.keras.layers.Dropout(0.4, name="dropout"),
            tf.keras.layers.Dense(n_classes, activation="softmax", name="output"),
        ],
        name="gesture_1d_cnn",
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
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
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=7, verbose=1
        ),
    ]

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=2,
        shuffle=True,
    )


# ---------------------------------------------------------------------------
# TFLite export
# ---------------------------------------------------------------------------

def export_tflite(model: tf.keras.Model, artifacts_dir: Path) -> Path:
    """
    Export pipeline:
        Keras model -> SavedModel -> TFLite flat buffer

    TFLiteConverter.from_saved_model is used (not from_keras_model) because
    it goes through the full TF graph lowering pipeline that the Pi runtime
    expects.  No quantisation = best accuracy for this dataset size.
    """
    saved_model_dir = artifacts_dir / "saved_model"
    keras_path      = artifacts_dir / "model.keras"
    tflite_path     = artifacts_dir / "model.tflite"

    model.save(str(keras_path))
    model.export(str(saved_model_dir))

    converter    = tf.lite.TFLiteConverter.from_saved_model(str(saved_model_dir))
    tflite_bytes = converter.convert()
    tflite_path.write_bytes(tflite_bytes)

    print(f"\nTFLite model -> {tflite_path}  ({len(tflite_bytes) / 1024:.1f} KB)")
    return tflite_path


def verify_tflite(tflite_path: Path,
                  X_test: np.ndarray, y_test: np.ndarray) -> None:
    """
    Run the TFLite interpreter on test samples to confirm the converted
    model produces correct predictions (exercise requirement g).
    """
    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    interpreter.allocate_tensors()

    inp_detail = interpreter.get_input_details()[0]
    out_detail = interpreter.get_output_details()[0]

    n = min(len(X_test), 30)
    correct = 0
    for i in range(n):
        interpreter.set_tensor(inp_detail["index"], X_test[i : i + 1].astype(np.float32))
        interpreter.invoke()
        pred = int(np.argmax(interpreter.get_tensor(out_detail["index"])))
        if pred == int(y_test[i]):
            correct += 1

    print(f"TFLite verification: {correct}/{n} correct on {n} test samples")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

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
        data_dir, window_size=args.window_size, max_file_rows=args.max_file_rows
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
            "\nWARNING: accuracy below 70 %. Try:\n"
            "  • Collect more samples (target >= 60 per class)\n"
            "  • Add a garbage class (idle movement recordings)\n"
            "  • --filters 64 --dense-units 128\n"
            "  • Adjust --window-size to match gesture duration\n"
            "  • --epochs 100 (EarlyStopping will stop automatically)"
        )

    print("\n--- TFLite export ---")
    tflite_path = export_tflite(model, artifacts_dir)
    verify_tflite(tflite_path, X_test, y_test)

    print(f"\nFinished :-) Artifacts written to: {artifacts_dir}/")
    return 0

##bash: python train.py --remote-data pi@192.168.1.42:/home/pi/recordings/

if __name__ == "__main__":
    raise SystemExit(main())