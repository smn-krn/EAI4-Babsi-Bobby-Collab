#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Infer exported models on Raspberry Pi.

Supports:
    - model_fp32.h5
    - model_pruned_stripped.h5
    - model_fp16.tflite

Example:
    python3 infer_models_on_pi.py \
      --data test_data.npz \
      --scalers scalers.npz \
      --models model_fp32.h5 model_pruned_stripped.h5 model_fp16.tflite \
      --outdir pi_results \
      --num-threads 2
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import Optional

import numpy as np

# TensorFlow is required for .h5 inference.
try:
    import tensorflow as tf
    HAVE_TF = True
    TFLITE_INTERPRETER = tf.lite.Interpreter
except Exception:
    tf = None
    HAVE_TF = False
    TFLITE_INTERPRETER = None

# Fallback for pure TFLite deployments on Raspberry Pi.
if TFLITE_INTERPRETER is None:
    try:
        from tflite_runtime.interpreter import Interpreter as TFLITE_INTERPRETER
    except Exception:
        TFLITE_INTERPRETER = None


def load_scalers(path: str) -> dict[str, np.ndarray | int]:
    d = np.load(path)
    return {
        "x_mean": d["x_mean"].astype(np.float32),
        "x_scale": d["x_scale"].astype(np.float32),
        "y_mean": d["y_mean"].astype(np.float32),
        "y_scale": d["y_scale"].astype(np.float32),
        "seq_len": int(d["seq_len"]),
        "n_sensors": int(d["n_sensors"]),
    }


def load_dataset(path: str) -> tuple[np.ndarray, Optional[np.ndarray], int, int]:
    d = np.load(path)
    X = d["X"].astype(np.float32)
    y = d["y"].astype(np.float32) if "y" in d.files else None
    seq_len = int(d["seq_len"]) if "seq_len" in d.files else X.shape[1]
    n_sensors = int(d["n_sensors"]) if "n_sensors" in d.files else X.shape[2]
    return X, y, seq_len, n_sensors


def scale_X(X: np.ndarray, x_mean: np.ndarray, x_scale: np.ndarray) -> np.ndarray:
    n, slen, nch = X.shape
    X_scaled = ((X.reshape(-1, nch) - x_mean) / x_scale).reshape(n, slen, nch)
    return X_scaled.astype(np.float32)


def inverse_y(y_scaled: np.ndarray, y_mean: np.ndarray, y_scale: np.ndarray) -> np.ndarray:
    y_mean_scalar = float(np.asarray(y_mean).reshape(-1)[0])
    y_scale_scalar = float(np.asarray(y_scale).reshape(-1)[0])
    return np.asarray(y_scaled).reshape(-1) * y_scale_scalar + y_mean_scalar


def compute_metrics(preds: np.ndarray, y_true: Optional[np.ndarray]) -> dict[str, float | int]:
    result: dict[str, float | int] = {"n_samples": int(len(preds))}
    if y_true is None:
        return result

    err = preds - y_true
    mae = float(np.mean(np.abs(err)))
    mse = float(np.mean(np.square(err)))
    rmse = float(np.sqrt(mse))
    result.update({"mae": mae, "mse": mse, "rmse": rmse})
    return result


def infer_keras(model_path: str, X_scaled: np.ndarray, batch_size: int) -> np.ndarray:
    if not HAVE_TF:
        raise RuntimeError(
            f"TensorFlow is not available, so .h5 model loading is not possible: {model_path}"
        )
    model = tf.keras.models.load_model(model_path, compile=False)
    preds_scaled = model.predict(X_scaled, batch_size=batch_size, verbose=0).reshape(-1)
    return preds_scaled.astype(np.float32)


def infer_tflite(model_path: str, X_scaled: np.ndarray, num_threads: int) -> np.ndarray:
    if TFLITE_INTERPRETER is None:
        raise RuntimeError("Neither TensorFlow Lite nor tflite-runtime is available.")

    interpreter = TFLITE_INTERPRETER(model_path=model_path, num_threads=num_threads)
    interpreter.allocate_tensors()

    inp = interpreter.get_input_details()[0]
    outp = interpreter.get_output_details()[0]

    preds_scaled = np.empty((len(X_scaled),), dtype=np.float32)
    for i in range(len(X_scaled)):
        x = X_scaled[i:i + 1].astype(inp["dtype"])
        interpreter.set_tensor(inp["index"], x)
        interpreter.invoke()
        y_hat = interpreter.get_tensor(outp["index"])
        preds_scaled[i] = np.asarray(y_hat).reshape(-1)[0]

    return preds_scaled


def save_predictions_csv(out_csv: Path, preds: np.ndarray, y_true: Optional[np.ndarray]) -> None:
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if y_true is None:
            writer.writerow(["index", "prediction"])
            for i, pred in enumerate(preds):
                writer.writerow([i, float(pred)])
        else:
            writer.writerow(["index", "prediction", "target", "abs_error", "sq_error"])
            for i, (pred, target) in enumerate(zip(preds, y_true)):
                abs_error = abs(float(pred) - float(target))
                sq_error = (float(pred) - float(target)) ** 2
                writer.writerow([i, float(pred), float(target), abs_error, sq_error])


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run inference for exported TF/TFLite models on Raspberry Pi.")
    ap.add_argument("--data", required=True, help="NPZ file with X and optional y")
    ap.add_argument("--scalers", required=True, help="scalers.npz from the training script")
    ap.add_argument("--models", nargs="+", required=True, help="List of .h5 or .tflite model files")
    ap.add_argument("--outdir", default="pi_inference_results", help="Output directory")
    ap.add_argument("--batch-size", type=int, default=128, help="Batch size for .h5 inference")
    ap.add_argument("--num-threads", type=int, default=1, help="Number of threads for TFLite")
    return ap.parse_args()


def main() -> int:
    args = parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    scalers = load_scalers(args.scalers)
    X_raw, y_true, seq_len, n_sensors = load_dataset(args.data)

    if X_raw.ndim != 3:
        raise ValueError(f"X must be 3D. Received shape: {X_raw.shape}")

    if seq_len != scalers["seq_len"] or n_sensors != scalers["n_sensors"]:
        raise ValueError(
            "Dataset shape does not match scaler/model metadata: "
            f"data(seq_len={seq_len}, n_sensors={n_sensors}) vs "
            f"scalers(seq_len={scalers['seq_len']}, n_sensors={scalers['n_sensors']})"
        )

    X_scaled = scale_X(
        X_raw,
        scalers["x_mean"],
        scalers["x_scale"],
    )

    summary_rows: list[dict[str, object]] = []

    for model_path in args.models:
        model_name = Path(model_path).name
        model_stem = Path(model_path).stem

        print(f"\n=== {model_name} ===")
        t0 = time.perf_counter()

        if model_path.lower().endswith(".tflite"):
            backend = "tflite"
            preds_scaled = infer_tflite(model_path, X_scaled, args.num_threads)
        elif model_path.lower().endswith((".h5", ".keras")):
            backend = "keras"
            preds_scaled = infer_keras(model_path, X_scaled, args.batch_size)
        else:
            print(f"Skipped unsupported file type: {model_path}")
            continue

        dt = time.perf_counter() - t0
        preds = inverse_y(preds_scaled, scalers["y_mean"], scalers["y_scale"])
        metrics = compute_metrics(preds, y_true)
        ms_per_sample = (dt / len(preds)) * 1000.0

        print(f"Backend        : {backend}")
        print(f"Samples        : {len(preds)}")
        print(f"Total time [s] : {dt:.6f}")
        print(f"Per sample [ms]: {ms_per_sample:.6f}")
        if y_true is not None:
            print(f"MAE            : {metrics['mae']:.6f}")
            print(f"MSE            : {metrics['mse']:.6f}")
            print(f"RMSE           : {metrics['rmse']:.6f}")

        pred_csv = outdir / f"{model_stem}_predictions.csv"
        save_predictions_csv(pred_csv, preds, y_true)

        row: dict[str, object] = {
            "model": model_name,
            "backend": backend,
            "n_samples": int(len(preds)),
            "total_time_s": float(dt),
            "ms_per_sample": float(ms_per_sample),
            "predictions_csv": str(pred_csv),
        }
        row.update(metrics)
        summary_rows.append(row)

    summary_csv = outdir / "summary.csv"
    fieldnames = [
        "model",
        "backend",
        "n_samples",
        "mae",
        "mse",
        "rmse",
        "total_time_s",
        "ms_per_sample",
        "predictions_csv",
    ]

    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary_rows:
            writer.writerow(row)

    print(f"\nSummary written to: {summary_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
