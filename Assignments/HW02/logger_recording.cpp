// [TASK 7] Log program start with filename and label so the journal shows
   // which recording session this process belongs to
   std::cerr << "[logger_recorder] Started. File: " << filename << " | Label: " << label << "\n";
#include "RTIMULib.h"
#include <iostream>
#include <fstream>
#include <chrono>
#include <memory>
#include <thread>

int const retNotFound = -1;
int const retInitFailed = -2;

int main(int argc, char* argv[]) {

   std::string filename = "data.csv";
   std::string label = "X";

   if (argc >= 2) filename = argv[1];
   if (argc >= 3) label = argv[2];

   auto settings = std::make_unique<RTIMUSettings>("RTIMULib");
   auto imu = std::unique_ptr<RTIMU>(RTIMU::createIMU(settings.get()));

   if (!imu || imu->IMUType() == RTIMU_TYPE_NULL) {
      std::cerr << "No IMU / Sense Hat found.\n";
      return retNotFound;
   }

   if (!imu->IMUInit()) {
      std::cerr << "IMUInit failed\n";
      return retInitFailed;
   }

   imu->setAccelEnable(true);
   imu->setGyroEnable(true);
   imu->setCompassEnable(true);

   std::cout << "IMU is being read. Cancel with Ctrl+C" << std::endl;

   // TASK 7: Log program start
   std::cerr << "[logger_recorder] Started. File: " << filename << " | Label: " << label << "\n";

   std::ofstream file(filename, std::ios::trunc);
   if (!file.is_open()) {
      // TASK 7: Log file open error
      std::cerr << "[logger_recorder] ERROR: Failed to open file: " << filename << "\n";
      return -3;
   }

   // TASK 7: Log successful file open
   std::cerr << "[logger_recorder] File opened successfully: " << filename << "\n";

   file << "timestamp_ms,label,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,mag_x,mag_y,mag_z\n";

   while (true) {
       using namespace std::literals::chrono_literals;
       std::this_thread::sleep_for(50ms);

       while (imu->IMURead()) {
         const auto& data = imu->getIMUData();

         if (data.accelValid && data.gyroValid && data.compassValid) {
            file << data.timestamp / 1000 << "," << label << ",";

            file << data.accel.x() << ",";
            file << data.accel.y() << ",";
            file << data.accel.z() << ",";

            file << data.gyro.x() << ",";
            file << data.gyro.y() << ",";
            file << data.gyro.z() << ",";

            file << data.compass.x() << ",";
            file << data.compass.y() << ",";
            file << data.compass.z() << "\n";

            file.flush();

            // TASK 7: Log write error if stream goes bad
            if (!file) {
               std::cerr << "[logger_recorder] ERROR: Write/flush failed for file: " << filename << "\n";
            }
         }
       }
   }

   return 0;
}
