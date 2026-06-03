// main.cpp

#include <chrono>
#include <exception>
#include <iostream>
#include <string>
#include <vector>
#include <iomanip>
#include <map>
#include <cmath>
#include "RTIMULib.h"
#include <thread>

#include "TfliteGestureClassifier.h"
#include <fstream>
#include <sstream>

namespace
{

    const std::vector<std::string> kClassNames = {
        "-",
        "A",
        "B",
        "C"}; // class 0 is the garbage class, and classes 1-3 are the actual gestures

    constexpr const char *kModelPath = "baseline.tflite"; // default model path, can be overridden with --model command line argument in the terminal
    constexpr const char *kCsvPath = "0001.csv";          // default CSV file for testing, can be overridden with --csv command line argument in the terminal

    constexpr int kDefaultWarmupRuns = 20;      // number of warmup runs to perform before benchmarking - helps to ensure that any one-time setup costs (like memory allocation, JIT compilation, etc.) are not included in the benchmark timing, again can be overridden with --warmup command line argument in the terminal
    constexpr int kDefaultBenchmarkRuns = 1000; // number of runs to perform for benchmarking, can be overridden with --runs command line argument in the terminal

    // chooses program mode_> gesture inference or benchmark
    enum class ProgramMode
    {
        kGestureInference,
        kBenchmark,
    };

    // struct to hold all program options, with default values that can be overridden by command line arguments
    struct ProgramOptions
    {
        std::string model_path = kModelPath;               // default model path
        std::string csv_path = kCsvPath;                   // default CSV path for testing
        ProgramMode mode = ProgramMode::kGestureInference; // default to gesture inference mode
        int warmup_runs = kDefaultWarmupRuns;
        int benchmark_runs = kDefaultBenchmarkRuns;
        bool stream_mode = false; // whether to run in streaming mode, false -> run in gesture inference mode using CSV input, true -> run in streaming mode using live IMU data for inference
    };

    // prints command line usage information: e.g. how to specify the model path, CSV path, number of warmup runs, number of benchmark runs, and how to enable streaming mode
    void PrintUsage(const char *program_name)
    {
        std::cerr
            << "Usage:\n"
            << "  "
            << program_name
            << " --model baseline.tflite --csv test_gesture.csv\n";
    }

    // parses a positive integer option value and verifies that the value is positive
    bool ParsePositiveInt(const std::string &text, int *value)
    {
        try
        {
            const int parsed = std::stoi(text); // converts input text to an integer using std::stoi-> throws exception if the input is not a valid integer

            if (parsed <= 0)
            {
                return false;
            }

            *value = parsed; // stores the parsed integer value in the provided pointer if it is valid and positive
            return true;
        }
        catch (const std::exception &)
        { // catches any exceptions thrown by std::stoi (e.g., invalid input, out of range) and returns false to indicate that the parsing failed
            return false;
        }
    }

    // parses command line arguments and populates the ProgramOptions struct with the specified options, including model path, CSV path, number of warmup runs, number of benchmark runs, and whether to enable streaming mode
    bool ParseArgs(int argc, char **argv, ProgramOptions *options)
    {
        for (int index = 1; index < argc; ++index)
        {
            const std::string arg = argv[index];

            if (arg == "--help" || arg == "-h")
            {
                PrintUsage(argv[0]);
                return false;
            }

            if (arg == "--model" && index + 1 < argc)
            {
                options->model_path = argv[++index];
                continue;
            }

            if (arg == "--csv" && index + 1 < argc)
            {
                options->csv_path = argv[++index];
                continue;
            }

            if (arg == "--runs" && index + 1 < argc)
            {
                if (!ParsePositiveInt(argv[++index], &options->benchmark_runs))
                {
                    std::cerr << "Invalid --runs value.\n";
                    return false;
                }

                continue;
            }

            if (arg == "--warmup" && index + 1 < argc)
            {
                if (!ParsePositiveInt(argv[++index], &options->warmup_runs))
                {
                    std::cerr << "Invalid --warmup value.\n";
                    return false;
                }

                continue;
            }

            // supports positional argument for model path (for backward compatibility with our previous assignments)
            if (!arg.empty() && arg[0] != '-')
            {
                // if argument does not start with a dash, treat it as the model path
                // allows us to specify model path without using the --model flag, e.g. "./program baseline.tflite" instead of "./program --model baseline.tflite")
                options->model_path = arg;
                continue;
            }

            if (arg == "--benchmark")
            {
                // if --benchmark flag is present-> program mode set to benchmark mode
                options->mode = ProgramMode::kBenchmark;
                continue;
            }

            else if (arg == "--stream")
            {
                // if --stream flag is present-> enable streaming mode, which uses live IMU data for inference instead of CSV input
                options->stream_mode = true;
                continue;
            }

            std::cerr << "Unknown or incomplete argument: " << arg << "\n";
            PrintUsage(argv[0]);
            return false;
        }

        return true;
    }

    // normalizes features in input data by performing per-feature normalization (zero mean and unit variance) across all samples for each feature-> helps to ensure that the input data is on a similar scale, which can improve the performance of the model during inference
    void NormalizeFeatures(
        std::vector<float> *data_input,
        int features_per_row = 9)
    {
        const int rows =
            static_cast<int>(data_input->size()) / features_per_row;

        for (int feature = 0;
             feature < features_per_row;
             ++feature)
        {
            float mean = 0.0f;

            for (int row = 0; row < rows; ++row)
            {
                mean += (*data_input)[row * features_per_row + feature];
            }

            mean /= static_cast<float>(rows);

            float variance = 0.0f;

            for (int row = 0; row < rows; ++row)
            {
                const float value =
                    (*data_input)[row * features_per_row + feature];

                const float diff =
                    value - mean;

                variance += diff * diff;
            }

            variance /= static_cast<float>(rows);

            float stddev =
                std::sqrt(variance);

            if (stddev < 1e-6f)
            {
                stddev = 1.0f;
            }

            for (int row = 0; row < rows; ++row)
            {
                float &value =
                    (*data_input)[row * features_per_row + feature];

                value =
                    (value - mean) / stddev;
            }
        }
    }

    // loads and preprocesses the CSV and stores processed data in the provided data_input vector
    bool LoadCsv(const std::string &path, std::vector<float> *data_input)
    {

        std::ifstream file(path);
        // checks if file was opened successfully, if not, prints an error message and returns false to indicate that loading the CSV failed
        if (!file.is_open())
        {
            std::cerr << "Failed to open CSV file.\n";
            return false;
        }

        std::string line;

        // ignores header line of the csv file
        std::getline(file, line);

        constexpr int kExpectedRows = 150; // expected number of rows in the input CSV, shorter recordings will be zero-padded, longer recordings will be cropped
        constexpr int kFeaturesPerRow = 9; // expected number of features per row (excluding timestamp), should match the models expected input shape

        int row_count = 0;

        while (std::getline(file, line))
        {

            std::stringstream ss(line);
            std::string cell;

            int column = 0;

            // crop extra rows if the CSV has more than the expected number of rows- helps to maintain a consistent input shape for the model during inference
            if (row_count >= kExpectedRows)
            {

                std::cerr
                    << "WARNING: CSV has more than "
                    << kExpectedRows
                    << " rows. Extra rows were cropped.\n";

                break; // due to breaking here, only the first kExpectedRows will be processed and the rest will be ignored
            }

            while (std::getline(ss, cell, ','))
            {

                // skips the first column (timestamp) and processes only the feature columns
                if (column > 0)
                {

                    float value = std::stof(cell); // converts the cell value from string to float using std::stof: necessary because the model expects input data as floats, and the CSV data is read as strings

                    data_input->push_back(value); // stores the converted float value in the data_input vector, which will be used as input for the model during inference
                }

                column++;
            }

            row_count++;
        }

        // short recordings will be zero-padded to ensure that the input data has the correct shape for the model-> important because the model expects a fixed input size
        if (row_count < kExpectedRows)
        {
            // if the CSV has fewer rows than expected, we need to pad the input data with zeros
            // warning message is printed to inform that the CSV has fewer rows than expected and that zero-padding will be applied
            std::cerr
                << "WARNING: CSV has only "
                << row_count
                << " rows. Zero-padding to "
                << kExpectedRows
                << ".\n";

            const int missing_rows =
                kExpectedRows - row_count; // calculate how many rows are missing to reach the expected number of rows

            const int missing_values =
                missing_rows * kFeaturesPerRow; // calculate how many values are missing based on the number of missing rows and features per row

            data_input->resize(
                data_input->size() + missing_values,
                0.0f // actual padding happens here: data_input vector is resized to accommodate the missing values, and the new values are initialized to 0.0f to achieve zero-padding
            );
        }

        // performs feature normalization on the loaded data to ensure that the input data is on a similar scale-> can improve performance of the model during inference
        NormalizeFeatures(data_input);

        return true;
    }

    // Exercise 5: Benchmarking and Streaming Inference
    // Benchmarking: RunBenchmark function performs benchmarking of model by running multiple inference runs and measuring the total and average inference time, printing final prediction results
    int RunBenchmark(
        const ProgramOptions &options,
        TfliteGestureClassifier *classifier)
    {

        std::vector<float> data_input;

        if (!LoadCsv(options.csv_path, &data_input))
        {
            return 1;
        }

        constexpr int kExpectedValues = 150 * 9;
        GesturePrediction prediction;

        if (data_input.size() != kExpectedValues)
        {
            std::cerr
                << "Expected "
                << kExpectedValues
                << " values but got "
                << data_input.size()
                << "\n";
            return 1;
        }

        // warmup: runs number of inference runs specified by options.warmup_runs before starting the benchmark timing-> helps to ensure that any one-time setup costs are not included in the benchmark timing
        {
            classifier->Predict(data_input);
        }

        // benchmark: runs the number of inference runs specified by options.benchmark_runs and measures the total time taken for all runs, then calculates and prints the average inference time per run with final prediction results
        using Clock = std::chrono::steady_clock;

        prediction = classifier->Predict(data_input);

        // check if the prediction was successful before time is measured
        // in case the prediction failed-> not proceed with benchmarking and instead error gets reported
        if (!classifier->ok())
        {
            std::cerr << "Inference failed: "
                      << classifier->error_message()
                      << "\n";
            return 1;
        }

        // start benchmark timing after warmup runs and successful prediction
        auto start = Clock::now();

        for (int i = 0; i < options.benchmark_runs; ++i)
        {
            classifier->Predict(data_input);
        }

        // end benchmark timing after all benchmark runs are completed
        auto end = Clock::now();

        // calculate total inference time in microseconds by taking the difference between end and start times and converting to microseconds using std::chrono::duration_cast
        const auto total_us =
            std::chrono::duration_cast<
                std::chrono::microseconds>(
                end - start)
                .count();

        // print total inference time in milliseconds by dividing total microseconds by 1000.0
        << "Total measured inference time in ms: "
        << static_cast<double>(total_us) / 1000.0
        << " ms\n";

        // calculate average inference time per run in microseconds by dividing total microseconds by the number of benchmark runs, then print average inference time in milliseconds
        const double avg_us =
            static_cast<double>(total_us) / options.benchmark_runs;

        std::cout
            << "Average inference time in ms: "
            << avg_us / 1000.0
            << " ms\n";

        std::cout << "Model: "
                  << options.model_path << "\n";

        std::cout << "CSV: "
                  << options.csv_path << "\n";

        std::cout << "\nFINAL PREDICTION\n";

        std::cout << "Predicted gesture class: "
                  << kClassNames[prediction.predicted_class]
                  << " ("
                  << prediction.predicted_class
                  << ")\n";

        std::cout << "Confidence: "
                  << std::fixed
                  << std::setprecision(6)
                  << prediction.confidence
                  << "\n";

        std::cout << "Runs: "
                  << options.benchmark_runs
                  << "\n";

        return 0;
    }

    // RunGestureInference: loads and preprocesses the CSV input data, validates the input size, runs inference using the TfliteGestureClassifier, and prints the final prediction results including predicted gesture class and confidence
    int RunGestureInference(const ProgramOptions &options,
                            TfliteGestureClassifier *classifier)
    {

        std::vector<float> data_input;

        if (!LoadCsv(options.csv_path, &data_input))
        {
            return 1;
        }

        // Expected input shape: model expects a fixed input size of 150 rows and 9 features per row, resulting in a total of 1350 values (150 * 9) for inference

        constexpr int kExpectedRows = 150;
        constexpr int kFeaturesPerRow = 9;

        constexpr int kExpectedValues =
            kExpectedRows * kFeaturesPerRow;

        // validate input size - double check that the CSV loading and preprocessing produced the expected number of values for inference
        if (data_input.size() != kExpectedValues)
        {

            std::cerr
                << "Expected "
                << kExpectedValues
                << " values but got "
                << data_input.size()
                << "\n";

            return 1;
        }

        // Run inference:
        GesturePrediction prediction =
            classifier->Predict(data_input); // run the prediction using the classifier, input data is passed as a vector of floats, which should match the expected input shape of the model
                                             // output is a GesturePrediction struct that contains the predicted class, confidence, and scores for each class

        if (!classifier->ok())
        {

            std::cerr << "Inference failed: "
                      << classifier->error_message()
                      << "\n";

            return 1;
        }

        // final result: print the model path, CSV path, predicted gesture class (both as a string and as an integer), and confidence score with 6 decimal places of precision

        std::cout << "\n";

        std::cout << "Model: "
                  << options.model_path << "\n";

        std::cout << "CSV: "
                  << options.csv_path << "\n";

        std::cout << "\nFINAL PREDICTION\n";

        std::cout << "Predicted gesture class: "
                  << kClassNames[prediction.predicted_class]
                  << " ("
                  << prediction.predicted_class
                  << ")\n";

        std::cout << "Confidence: "
                  << std::fixed
                  << std::setprecision(6)
                  << prediction.confidence
                  << "\n";

        return 0;
    }

    // RunStreamingMode: uses live IMU data for inference instead of CSV input, continuously collects IMU data, maintains a sliding window of most recent samples, performs inference at regular intervals, and prints the predicted gesture class and confidence when a stable gesture is detected based on consecutive predictions
    int RunStreamingMode(
        TfliteGestureClassifier *classifier)
    {
        // initialize the IMU using the RTIMULib library, check if the IMU is found and initialized successfully, and enable accelerometer, gyroscope, and compass data collection
        auto settings =
            std::make_unique<RTIMUSettings>("RTIMULib");

        auto imu =
            std::unique_ptr<RTIMU>(
                RTIMU::createIMU(settings.get()));

        if (!imu || imu->IMUType() == RTIMU_TYPE_NULL)
        {
            std::cerr << "No IMU found\n";
            return 1;
        }

        if (!imu->IMUInit())
        {
            std::cerr << "IMU init failed\n";
            return 1;
        }

        imu->setAccelEnable(true);
        imu->setGyroEnable(true);
        imu->setCompassEnable(true);

        // sliding window: maintains a sliding window of the most recent 150 samples with 9 features each (accelerometer, gyroscope, and compass data for x, y, z axes)
        constexpr size_t kWindowSize = 150 * 9;

        std::vector<float> window;
        window.reserve(kWindowSize);

        std::cout << "Streaming mode started\n";

        using Clock = std::chrono::steady_clock;

        auto last_inference = Clock::now();

        constexpr auto kInferenceInterval =
            std::chrono::milliseconds(500);

        int previous_prediction = -1;
        int stable_count = 0;
        int pAppearanceThreshold = 4; // number of consecutive predictions required for a gesture to be considered stable/confirmed and therefore printed as the output
        // helps to reduce false positives by ensuring that a gesture is consistently recognized over multiple inference runs before it is confirmed

        // bool gesture_confirmed = false - to track whether a stable gesture has been confirmed based on consecutive predictions
        bool window_ready_printed = false;

        // main loop: continuously collects IMU data, updates the sliding window, performs inference at regular intervals, and prints predicted gesture class and confidence when a stable gesture is detected based on consecutive predictions
        while (true)
        {

            while (imu->IMURead())
            {

                const auto &data = imu->getIMUData();

                if (!(data.accelValid &&
                      data.gyroValid &&
                      data.compassValid))
                {
                    continue;
                }

                window.push_back(data.accel.x());
                window.push_back(data.accel.y());
                window.push_back(data.accel.z());

                window.push_back(data.gyro.x());
                window.push_back(data.gyro.y());
                window.push_back(data.gyro.z());

                window.push_back(data.compass.x());
                window.push_back(data.compass.y());
                window.push_back(data.compass.z());

                const int samples =
                    static_cast<int>(window.size() / 9); // calculate number of samples based on total number of values in the window divided by the number of features per sample (9 in this case)

                if (!window_ready_printed)
                {
                    std::cout
                        << "\rCollecting samples: "
                        << samples
                        << "/150"
                        << std::flush;
                }

                while (window.size() > kWindowSize)
                {
                    window.erase(
                        window.begin(),
                        window.begin() + 9);
                } // if window has more than the expected number of values (kWindowSize)-> oldest sample is removed (the first 9 values) to maintain a sliding window of the most recent 150 samples

                // inference: when the sliding window is full (contains 150 samples with 9 features each), inference is performed at regular intervals (every 500 milliseconds) using the TfliteGestureClassifier, the predicted gesture class and confidence are printed when a stable gesture is detected based on consecutive predictions
                if (window.size() == kWindowSize)
                {

                    if (!window_ready_printed)
                    {
                        std::cout
                            << "\nWindow full. Starting live inference.\n";

                        window_ready_printed = true;
                    }

                    auto now = Clock::now();

                    if (now - last_inference < kInferenceInterval)
                    {
                        continue;
                    }

                    last_inference = now;

                    std::vector<float> normalized = window;

                    std::cout
                        << "\rNormalizing + inferencing...      "
                        << std::flush;
                    // perform feature normalization on the data in the sliding window before running inference to ensure that the input data is on a similar scale
                    NormalizeFeatures(&normalized);

                    // run inference using the TfliteGestureClassifier with the normalized data from the sliding window, and store the prediction results in a GesturePrediction struct
                    GesturePrediction prediction =
                        classifier->Predict(normalized);

                    if (prediction.predicted_class ==
                        previous_prediction)
                    {
                        stable_count++;
                    }
                    else
                    {
                        previous_prediction =
                            prediction.predicted_class;

                        stable_count = 1;

                        // gesture_confirmed = false; - if the predicted class changes, reset the stable count and set gesture_confirmed to false to indicate that a new gesture is being evaluated for stability
                    }

                    if (stable_count >= pAppearanceThreshold && prediction.confidence >= 0.5f)
                    {
                        // gesture_confirmed = true; - if the same gesture has been predicted for a number of consecutive runs (as defined by pAppearanceThreshold) and the confidence is above a certain threshold (e.g., 0.5), consider gesture to be confirmed and proceed to print the predicted gesture class and confidence

                        static int last_displayed = -1;

                        // to avoid printing the same gesture repeatedly when it is stable, check if the predicted class is different from the last displayed class before printing the results, and only print if it is a new stable gesture
                        if (prediction.predicted_class != last_displayed)
                        {
                            last_displayed = prediction.predicted_class;

                            const std::string cmd =
                                "python3 display_prediction.py " +
                                kClassNames[prediction.predicted_class] +
                                " &";

                            std::system(cmd.c_str());
                        }

                        std::cout
                            << "\nGesture: "
                            << kClassNames[prediction.predicted_class]
                            << " confidence="
                            << std::fixed
                            << std::setprecision(3)
                            << prediction.confidence * 100.0f << " %"
                            << "\n"
                            << "Other gesture confidence: "
                            << "A=" << prediction.scores[1] * 100.0f << " %"
                            << " B=" << prediction.scores[2] * 100.0f << " %"
                            << " C=" << prediction.scores[3] * 100.0f << " %"
                            << " -= " << prediction.scores[0] * 100.0f << " %"
                            << "\n"
                            << std::endl;
                    }
                    else
                    { // if a stable gesture has not been detected yet, print the number of consecutive predictions for the current predicted class to provide feedback on the stability of the prediction and indicate that no stable gesture has been detected yet
                        std::cout
                            << "\rNo stable gesture yet ("
                            << stable_count
                            << "/" << pAppearanceThreshold << ")                    "
                            << std::flush;
                    }
                }
            }

            // sleep for a short duration to avoid busy waiting and reduce CPU usage while continuously reading IMU data and performing inference
            std::this_thread::sleep_for(
                std::chrono::milliseconds(20));
        }

        return 0;
    }

} // namespace

int main(int argc, char **argv)
{
    ProgramOptions options;

    // parse command line arguments to populate ProgramOptions struct with the specified options (like model path, CSV path, number of warmup runs, number of benchmark runs, whether to enable streaming mode)
    // if parsing fails (e.g., due to invalid arguments) print usage information and exit with an error code
    if (!ParseArgs(argc, argv, &options))
    {
        return 1;
    }

    TfliteGestureClassifier classifier(options.model_path);

    if (!classifier.ok())
    {
        std::cerr << "Failed to load model: "
                  << classifier.error_message() << "\n";
        return 1;
    }

    if (options.stream_mode)
    {
        return RunStreamingMode(&classifier);
    }

    // runs program in either gesture inference mode or benchmark mode based on the specified options, and returns the result of the selected mode's execution (0 for success, 1 for failure)
    switch (options.mode)
    {
    case ProgramMode::kGestureInference:
        return RunGestureInference(
            options,
            &classifier);

    case ProgramMode::kBenchmark:
        return RunBenchmark(
            options,
            &classifier);
    }

    return 1;
}