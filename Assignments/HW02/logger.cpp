#include "RTIMULib.h"

#include <iostream>
#include <fstream>
#include <chrono>
#include <memory>
#include <thread>

int const retNotFound = -1;
int const retInitFailed = -2;

int main() {
   auto settings = std::make_unique<RTIMUSettings>("RTIMULib");
   auto imu = std::unique_ptr<RTIMU>(RTIMU::createIMU(settings.get()));

   if (!imu || imu->IMUType() == RTIMU_TYPE_NULL) {
      std::cerr << "No IMU / Sense Hat found. \n";
      return retNotFound;
   }

   if (!imu->IMUInit()) {
      std::cerr << "IMUINit failed \n";
      return retInitFailed;
   }

   imu->setAccelEnable(true);
   imu->setGyroEnable(true);
   imu->setCompassEnable(true);

   std::cout << "IMU is being read. Cancel with Ctrl+C" << std::endl;

   std::ofstream file("data.csv", std::ios::trunc);
   if (!file.is_open()) {
      std::cerr << "failed to open the file. \n";
      return -3;
   }

   file << "timestamp_ms,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,mag_x,mag_y,mag_z\n";

   while (true) {
       using namespace std::literals::chrono_literals;
       auto const poll_intervall = 50ms;

       std::this_thread::sleep_for(poll_intervall);

       while (imu->IMURead()) {
         const auto& data = imu->getIMUData();
         file << data.timestamp / 1000 << ",";

         if (data.accelValid && data.gyroValid && data.compassValid) {
            file << data.accel.x() << ",";
            file << data.accel.y() << ",";
            file << data.accel.z() << ",";

            file << data.gyro.x() << ",";
            file << data.gyro.y() << ",";
            file << data.gyro.z() << ",";

            file << data.compass.x() << ",";
            file << data.compass.y() << ",";
            file << data.compass.z() << "\n";

            file.flush(); // ensures that the data is written to the file
         } else
         {
            std::cerr << "Warning: Missing IMU Data\n";
         }

       }

   }
   return 0;
}
