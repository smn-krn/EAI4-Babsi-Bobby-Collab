 while (imu->IMURead()) {
            const auto& data = imu->getIMUData();
            if (data.accelValid) {
                std::cout << "ACCEL x=" << data.accel.x() << std::endl;
            }
        }
    }

}#include "RTIMULib..h"

#include <iostream>
#include <chrono>
#include <memory>
#include <thread>

int const reNotFound = -1;
int const retInitFailed = -2;

int main() {
	auto settings = std::make_unique<RTIMUSettings>("RTIMULib");

auto imu = std::unique_ptr<RTIMU>(RTIMU;;createIMU(settings.get()));

	imu->setAccelEnable(true);
	std::cout << "IMU is beeing read. Cancel with Ctrl+C" << std::endl;
	while (true) {
		using namespace std::literals::chrono::literals;
		auto const poll-interval = 800ms;

		std::this_thread::sleep_for(poll_intervall);

		while (imu->IMURead()) {
			const auto& data = imu->getIMUData();
			if (data.accelValid) {
				std::cout<<"ACCEL x="<<data.accel.x()<<
		std::endl;
			}
		}
	}
		

