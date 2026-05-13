```bash
kit-07@kit-07:~/demo_dir $ ./pi_demo --model baseline.tflite --csv test_gesture.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.

Model: baseline.tflite
CSV: test_gesture.csv

FINAL PREDICTION
Predicted gesture class: B (2)
Confidence: 0.545568
kit-07@kit-07:~/demo_dir $ ./pi_demo --model baseline.tflite --csv 0001.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.
WARNING: CSV has more than 150 rows. Extra rows were cropped.

Model: baseline.tflite
CSV: 0001.csv

FINAL PREDICTION
Predicted gesture class: B (2)
Confidence: 0.999886
kit-07@kit-07:~/demo_dir $ ./pi_demo --model baseline.tflite --csv 0002.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.

Model: baseline.tflite
CSV: 0002.csv

FINAL PREDICTION
Predicted gesture class: - (0)
Confidence: 0.631845
kit-07@kit-07:~/demo_dir $ ./pi_demo --model baseline.tflite --csv 0003.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.

Model: baseline.tflite
CSV: 0003.csv

FINAL PREDICTION
Predicted gesture class: A (1)
Confidence: 0.711834
kit-07@kit-07:~/demo_dir $ ./pi_demo --model baseline.tflite --csv 0013.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.
WARNING: CSV has only 50 rows. Zero-padding to 150.

Model: baseline.tflite
CSV: 0013.csv

FINAL PREDICTION
Predicted gesture class: C (3)
Confidence: 0.999671
kit-07@kit-07:~/demo_dir $ ./pi_demo --model channel_pruned.tflite --csv test_gesture.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.

Model: channel_pruned.tflite
CSV: test_gesture.csv

FINAL PREDICTION
Predicted gesture class: A (1)
Confidence: 0.994062
kit-07@kit-07:~/demo_dir $ ./pi_demo --model channel_pruned.tflite --csv 0001.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.
WARNING: CSV has more than 150 rows. Extra rows were cropped.

Model: channel_pruned.tflite
CSV: 0001.csv

FINAL PREDICTION
Predicted gesture class: B (2)
Confidence: 0.716986
kit-07@kit-07:~/demo_dir $ ./pi_demo --model channel_pruned.tflite --csv 0002.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.

Model: channel_pruned.tflite
CSV: 0002.csv

FINAL PREDICTION
Predicted gesture class: A (1)
Confidence: 0.837235
kit-07@kit-07:~/demo_dir $ ./pi_demo --model channel_pruned.tflite --csv 0003.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.

Model: channel_pruned.tflite
CSV: 0003.csv

FINAL PREDICTION
Predicted gesture class: A (1)
Confidence: 0.991662
kit-07@kit-07:~/demo_dir $ ./pi_demo --model channel_pruned.tflite --csv 0013.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.
WARNING: CSV has only 50 rows. Zero-padding to 150.

Model: channel_pruned.tflite
CSV: 0013.csv

FINAL PREDICTION
Predicted gesture class: A (1)
Confidence: 0.981981
kit-07@kit-07:~/demo_dir $ ./pi_demo --model neuron_pruned.tflite --csv test_gesture.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.

Model: neuron_pruned.tflite
CSV: test_gesture.csv

FINAL PREDICTION
Predicted gesture class: A (1)
Confidence: 0.823667
kit-07@kit-07:~/demo_dir $ ./pi_demo --model neuron_pruned.tflite --csv 0001.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.
WARNING: CSV has more than 150 rows. Extra rows were cropped.

Model: neuron_pruned.tflite
CSV: 0001.csv

FINAL PREDICTION
Predicted gesture class: B (2)
Confidence: 0.996838
kit-07@kit-07:~/demo_dir $ ./pi_demo --model neuron_pruned.tflite --csv 0002.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.

Model: neuron_pruned.tflite
CSV: 0002.csv

FINAL PREDICTION
Predicted gesture class: C (3)
Confidence: 0.661455
kit-07@kit-07:~/demo_dir $ ./pi_demo --model neuron_pruned.tflite --csv 0003.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.

Model: neuron_pruned.tflite
CSV: 0003.csv

FINAL PREDICTION
Predicted gesture class: A (1)
Confidence: 0.704026
kit-07@kit-07:~/demo_dir $ ./pi_demo --model neuron_pruned.tflite --csv 0013.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.
WARNING: CSV has only 50 rows. Zero-padding to 150.

Model: neuron_pruned.tflite
CSV: 0013.csv

FINAL PREDICTION
Predicted gesture class: C (3)
Confidence: 0.997262
kit-07@kit-07:~/demo_dir $ ./pi_demo --model synapse_pruned.tflite --csv test_gesture.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.

Model: synapse_pruned.tflite
CSV: test_gesture.csv

FINAL PREDICTION
Predicted gesture class: B (2)
Confidence: 0.800973
kit-07@kit-07:~/demo_dir $ ./pi_demo --model synapse_pruned.tflite --csv 0001.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.
WARNING: CSV has more than 150 rows. Extra rows were cropped.

Model: synapse_pruned.tflite
CSV: 0001.csv

FINAL PREDICTION
Predicted gesture class: B (2)
Confidence: 0.999960
kit-07@kit-07:~/demo_dir $ ./pi_demo --model synapse_pruned.tflite --csv 0002.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.

Model: synapse_pruned.tflite
CSV: 0002.csv

FINAL PREDICTION
Predicted gesture class: - (0)
Confidence: 0.546828
kit-07@kit-07:~/demo_dir $ ./pi_demo --model synapse_pruned.tflite --csv 0003.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.

Model: synapse_pruned.tflite
CSV: 0003.csv

FINAL PREDICTION
Predicted gesture class: A (1)
Confidence: 0.700441
kit-07@kit-07:~/demo_dir $ ./pi_demo --model synapse_pruned.tflite --csv 0013.csv
INFO: Initialized TensorFlow Lite runtime.
INFO: Applying 1 TensorFlow Lite delegate(s) lazily.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
VERBOSE: Replacing 13 out of 19 node(s) with delegate (TfLiteXNNPackDelegate) node, yielding 12 partitions for the whole graph.
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
Warning in XNNPACK: unable to enable JIT: not compiled with JIT enabled
INFO: Successfully applied the default TensorFlow Lite delegate indexed at 0.
 *NOTE*: because a delegate has been applied, the precision of computations should be unchanged, but the exact output tensor values may have changed. If such output values are checked in your code, like in your tests etc., please consider increasing error tolerance for the check.
WARNING: CSV has only 50 rows. Zero-padding to 150.

Model: synapse_pruned.tflite
CSV: 0013.csv

FINAL PREDICTION
Predicted gesture class: C (3)
Confidence: 0.997473
```
| Sample             | True Label | Baseline Prediction | Correct | Confidence | Synapse Pruned Prediction | Correct | Confidence | Neuron Pruned Prediction | Correct | Confidence | Channel Pruned Prediction | Correct | Confidence |
|--------------------|------------|---------------------|---------|------------|----------------------------|---------|------------|---------------------------|---------|------------|----------------------------|---------|------------|
| test_gesture.csv   | A          | B                   | ❌      | 0.545568   | B                          | ❌      | 0.800973   | A                         | ✅      | 0.823667   | A                          | ✅      | 0.994062   |
| 0001.csv           | B          | B                   | ✅      | 0.999886   | B                          | ✅      | 0.999960   | B                         | ✅      | 0.996838   | B                          | ✅      | 0.716986   |
| 0002.csv           | C          | -                   | ❌      | 0.631845   | -                          | ❌      | 0.546828   | C                         | ✅      | 0.661455   | A                          | ❌      | 0.837235   |
| 0003.csv           | A          | A                   | ✅      | 0.711834   | A                          | ✅      | 0.700441   | A                         | ✅      | 0.704026   | A                          | ✅      | 0.991662   |
| 0013.csv           | C          | C                   | ✅      | 0.999671   | C                          | ✅      | 0.997473   | C                         | ✅      | 0.997262   | A                          | ❌      | 0.981981   |

| Model              | Correct / 5 | Accuracy |
|-------------------|-------------|----------|
| Baseline          | 3 / 5       | 60%      |
| Synapse Pruned    | 3 / 5       | 60%      |
| Neuron Pruned     | 5 / 5       | 100%     |
| Channel Pruned    | 3 / 5       | 60%      |

# Training accuracy
<img width="392" height="100" alt="grafik" src="https://github.com/user-attachments/assets/110fdd09-2966-40b0-ac55-33f737daffd6" />
