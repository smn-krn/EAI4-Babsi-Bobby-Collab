python3 infer_models_on_pi.py \
  --data test_data.npz \
  --scalers scalers.npz \
  --models model_fp16.tflite \
  --outdir pi_results \
  --num-threads 2
