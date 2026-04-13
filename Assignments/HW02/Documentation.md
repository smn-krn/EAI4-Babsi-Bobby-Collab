# Task 1
![alt text](images/image.png)

Implemented in C++ because we did the majority of the code already in c++ which made very little change necessary. We renamed the output file to "output.csv" and added a loop that prints every 20th reading via a simple counter variable, because that is the simplest way to do it which is also rather robust.

Command to exectute the code [in the folder where the file is located]: 
```bash
g++ -Wall -std=c++17 -O2 logger.cpp -o logger -I /usr/include/RTIMULib -lRTIMULib -lpthread
```
this creates an executable called "logger" which can be run with 
```bash
./logger
```

to stop press 
```bash
crtl + c
```

# Task 2
![alt text](images/image-7.png)

Creating the file service via 

```bash
sudo nano /etc/systemd/system/logger.service
```

contents of file:
```bash
[Unit]
Description=IMU Logger Service. Runs the logger executable to log IMU data to a csv file. Done for assignment 2.

[Service]
ExecStart=/home/kit-18/Documents/EAI/EAI4-Babsi-Bobby-Collab/Assignments/HW02/logger
WorkingDirectory=/home/kit-18/Documents/EAI/EAI4-Babsi-Bobby-Collab/Assignments/HW02
User=kit-18
Restart=always

[Install]
WantedBy=multi-user.target
```

reload system via 
```bash
sudo systemctl daemon-reload
```

start service via 
```bash
sudo systemctl start logger.service
```

checked whether it works or not via:
```bash
systemctl status logger.service
```

stopping it:
```bash
sudo systemctl stop logger.service
```

output:

```
kit-18@kit-18:~/Documents/EAI/EAI4-Babsi-Bobby-Collab/Assignments/HW02 $ systemctl status logger.service
● logger.service - IMU Logger Service. Runs the logger executable to log IMU data to a csv file. Done for assignment
     Loaded: loaded (/etc/systemd/system/logger.service; disabled; preset: enabled)
     Active: active (running) since Sun 2026-04-12 22:27:21 CEST; 4s ago
 Invocation: a224dbf23e6043ddb39317b8ff77aa40
   Main PID: 3490 (logger)
      Tasks: 1 (limit: 756)
        CPU: 177ms
     CGroup: /system.slice/logger.service
             └─3490 /home/kit-18/Documents/EAI/EAI4-Babsi-Bobby-Collab/Assignments/HW02/logger

Apr 12 22:27:21 kit-18 logger[3490]: Using fusion algorithm RTQF
Apr 12 22:27:21 kit-18 logger[3490]: min/max compass calibration not in use
Apr 12 22:27:21 kit-18 logger[3490]: Ellipsoid compass calibration not in use
Apr 12 22:27:21 kit-18 logger[3490]: Accel calibration not in use
Apr 12 22:27:21 kit-18 logger[3490]: LSM9DS1 init complete
Apr 12 22:27:21 kit-18 logger[3490]: IMU is being read. Cancel with Ctrl+C
Apr 12 22:27:22 kit-18 logger[3490]: t=1776025642652 ms | Acc: (0.00366, -0.012444, 0.953064) | Gyro: (0.00598038, 0.0463634, 0.001603) | Ma>
Apr 12 22:27:23 kit-18 logger[3490]: t=1776025643659 ms | Acc: (0.004148, -0.012932, 0.952088) | Gyro: (0.0040039, 0.0345403, 0.000312979) |>
Apr 12 22:27:24 kit-18 logger[3490]: t=1776025644664 ms | Acc: (0.003904, -0.013176, 0.951356) | Gyro: (0.0046956, 0.0244019, -0.000368268) >
Apr 12 22:27:25 kit-18 logger[3490]: t=1776025645457 ms | Acc: (0.005124, -0.011956, 0.951356) | Gyro: (0.0040274, 0.0179633, 0.00015745) | >
```

view program journal log:
```bash
journalctl -u logger.service
```

# Task 3
![alt text](images/image-6.png)

command to find all running services:
```bash
systemctl list-units --type=service
```

trying to search directly for our service:
```bash
systemctl list-units --type=service | grep -i sense
```
and then also just in case tried:
```bash
systemctl list-units --type=service | grep -i display
```

exact name that was found: **sensehat-host-ip.service**

open service file:
```bash
sudo nano /etc/systemd/system/logger.service
```

edited the file to include the line AFTER and REQUIRES; whereby requires makes sure that if the first thing failed it does not execute the service. AFTER is for order; REQUIRES for dependency. Added a max runtime as well so that it won't be running endlessly and the csv file is getting km long; thereby removed restart=always because then it would just keep going on and on and on.
```bash
[Unit]
Description=IMU Logger Service. Runs the logger executable to log IMU data to a csv file. Done for assignment 2.
After=sensehat-host-ip.service
Requires=sensehat-host-ip.service

[Service]
ExecStart=/home/kit-18/Documents/EAI/EAI4-Babsi-Bobby-Collab/Assignments/HW02/logger
WorkingDirectory=/home/kit-18/Documents/EAI/EAI4-Babsi-Bobby-Collab/Assignments/HW02
User=kit-18
Restart=no
RuntimeMaxSec=10

[Install]
WantedBy=multi-user.target
```

reload system via 
```bash
sudo systemctl daemon-reload
```

restart service via 
```bash
sudo systemctl restart logger.service
```

check logs:
```bash
journalctl -u logger.service
```

```bash
journalctl -u sensehat-host-ip.service
```

or what made it clearler was actually getting the timestamps:
```bash
journalctl -b | grep -E "logger|host"
```

## output (shortend); we see it worked correctly:

```bash
Apr 12 22:40:22 kit-18 systemd[1]: Starting sensehat-host-ip.service - Sense HAT boot display for hostname and Ethernet IP...
Apr 12 22:40:48 kit-18 systemd[1]: sensehat-host-ip.service: Deactivated successfully.
Apr 12 22:40:48 kit-18 systemd[1]: Finished sensehat-host-ip.service - Sense HAT boot display for hostname and Ethernet IP.
Apr 12 22:40:48 kit-18 systemd[1]: sensehat-host-ip.service: Consumed 2.074s CPU time.
Apr 12 22:40:48 kit-18 systemd[1]: Started logger.service - IMU Logger Service. Runs the logger executable to log IMU data to a csv file. Done for assignment 2..
Apr 12 22:40:48 kit-18 logger[4812]: Settings file RTIMULib.ini loaded
Apr 12 22:40:48 kit-18 logger[4812]: Using fusion algorithm RTQF
Apr 12 22:40:48 kit-18 logger[4812]: min/max compass calibration not in use
Apr 12 22:40:48 kit-18 logger[4812]: Ellipsoid compass calibration not in use
Apr 12 22:40:48 kit-18 logger[4812]: Accel calibration not in use
Apr 12 22:40:48 kit-18 logger[4812]: LSM9DS1 init complete
Apr 12 22:40:48 kit-18 logger[4812]: IMU is being read. Cancel with Ctrl+C
Apr 12 22:40:49 kit-18 logger[4812]: t=1776026449329 ms | Acc: (0.003904, -0.011956, 0.954284) | Gyro: (0.000919332, 0.0023967, 0.00164912) | Mag: (-30.8094, 30.5717, 14.9156)
Apr 12 22:40:50 kit-18 logger[4812]: t=1776026450317 ms | Acc: (0.003416, -0.013908, 0.95526) | Gyro: (-0.000161444, 0.000651978, -0.000234083) | Mag: (-31.1709, 30.9983, 15.7577)
Apr 12 22:40:51 kit-18 logger[4812]: t=1776026451262 ms | Acc: (0.004392, -0.01342, 0.955504) | Gyro: (0.00192767, -0.00116718, 0.00025779) | Mag: (-32.0882, 31.368, 17.2943)
Apr 12 22:40:52 kit-18 logger[4812]: t=1776026452281 ms | Acc: (0.003904, -0.0122, 0.954284) | Gyro: (0.000812543, 0.000561193, -0.00181872) | Mag: (-32.211, 31.4716, 17.5098)
Apr 12 22:40:53 kit-18 logger[4812]: t=1776026453073 ms | Acc: (0.004636, -0.012444, 0.953796) | Gyro: (0.0010556, -0.000462525, -0.00144006) | Mag: (-31.251, 30.7645, 15.2509)
Apr 12 22:40:54 kit-18 logger[4812]: t=1776026454020 ms | Acc: (0.003416, -0.012688, 0.954284) | Gyro: (0.00132722, 0.000776634, -0.0020688) | Mag: (-31.1829, 30.6471, 15.6235)
Apr 12 22:40:54 kit-18 logger[4812]: t=1776026454753 ms | Acc: (0.004392, -0.0122, 0.954772) | Gyro: (-0.000992083, 0.00104684, -0.00169812) | Mag: (-32.0667, 30.5847, 14.6915)
```

# Task 4
![alt text](images/image-5.png)

Implemented in python because the sensehat library makes this really convenient.

code:
```python
from sense_hat import SenseHat

sense = SenseHat()

current_label = "A"
sense.show_letter(current_label)

while True:
    for event in sense.stick.get_events():
        if event.action == "pressed":

            if event.direction == "up":
                current_label = "A"
            elif event.direction == "right":
                current_label = "B"
            elif event.direction == "left":
                current_label = "C"
            elif event.direction == "down":
                current_label = "-"  # garbage

            # update display
            sense.show_letter(current_label,  text_colour=[0, 0, 255])
```

run the program via first activating the venv:
```bash
cd ../
source .venv/bin/activate
```

first cd into the folder where the .venv is located and then activate it via the command above. Then cd into the folder where the file is located and run it via:
```bash
python3 EAI4-Babsi-Bobby-Collab/Assignments/HW02/stick_directions.py
```

# Task 5
![alt text](images/image-4.png)

literal implementation of the task; actual implementation is in task 6 because currently it only states "Start recording" but does actually nothing; we choose to combine this already with the next one. Implemented in python because of the ease of the SenseHat library and the fact that we already had the code for task 4 in python which made it easier to just build on top of it. We also added a blinking red dot to indicate that recording is active; this is done via a simple timer and boolean variable to toggle the dot on and off every 0.5 seconds.

```python
from sense_hat import SenseHat
import time

sense = SenseHat()

# labels
label_map = {
    "up": "A",
    "right": "B",
    "left": "C",
    "down": "-"
}

def show_letter_with_dot(letter, show_dot):
    sense.show_letter(letter)
    if show_dot:
        sense.set_pixel(7, 0, 255, 0, 0)  # red dot top-right


# instruction screen
sense.show_message("UP=A RIGHT=B LEFT=C DOWN=-", text_colour=[138, 43, 226])
print("Press the joystick to start/stop recording. The current label will be shown on the LED matrix. UP=A RIGHT=B LEFT=C DOWN=-")

current_label = None
recording = False
recording_direction = None
cooldown = False

# blinking control
blink = False
last_blink = time.time()

while True:

    # blinking logic
    if recording:
        if time.time() - last_blink > 0.5:
            blink = not blink
            last_blink = time.time()

        show_letter_with_dot(current_label, blink)

    for event in sense.stick.get_events():
        if event.action != "pressed":
            continue

        direction = event.direction

        # COOLDOWN
        if cooldown:
            continue

        # IDLE => start recording
        if not recording:
            current_label = label_map.get(direction)

            if current_label is not None:
                recording = True
                recording_direction = direction

                print(f"START recording {current_label}")
                show_letter_with_dot(current_label, True)

        # RECORDING => stop if same direction
        else:
            if direction == recording_direction:
                print(f"STOP recording {current_label}")

                recording = False
                recording_direction = None

                # cooldown
                cooldown = True
                sense.clear(0, 255, 0)
                time.sleep(1.5)

                cooldown = False
                sense.clear()

    time.sleep(0.05)
```

# Task 6
![alt text](images/image-3.png)

Added a new specific logger file, based on the c++ file earlier called logger_recording.cpp. It does not print every 20th reading:

```cpp
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

   std::ofstream file(filename, std::ios::trunc);
   if (!file.is_open()) {
      std::cerr << "Failed to open file.\n";
      return -3;
   }

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
         }
       }
   }

   return 0;
}
```

compile using (in the same folder as the file)
```bash
cd EAI4-Babsi-Bobby-Collab/Assignments/HW02/
g++ -std=c++17 -O2 -Wall logger_recording.cpp -o logger_recorder -I /usr/include/RTIMULib -lRTIMULib -lpthread
```

then changed the python file so that it calls the new logger_recording executable and passes the label as an argument; this way we can directly save the data with the correct label without having to do any post processing

```python
from sense_hat import SenseHat
import time
import subprocess
import datetime
import os

sense = SenseHat()

smiley = [
    [0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],
    [0,0,0],[0,0,255],[0,0,255],[0,0,0],[0,0,0],[0,0,255],[0,0,255],[0,0,0],
    [0,0,0],[0,0,255],[0,0,255],[0,0,0],[0,0,0],[0,0,255],[0,0,255],[0,0,0],
    [0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],
    [0,255,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,255,0],
    [0,0,0],[0,255,0],[0,255,0],[0,255,0],[0,255,0],[0,255,0],[0,255,0],[0,0,0],
    [0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],
    [0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]
]

# create folder
script_dir = os.path.dirname(os.path.abspath(__file__))
recording_dir = os.path.join(script_dir, "recordings")

os.makedirs(recording_dir, exist_ok=True)

# labels
label_map = {
    "up": "A",
    "right": "B",
    "left": "C",
    "down": "-"
}

def show_letter_with_dot(letter, show_dot):
    sense.show_letter(letter)
    if show_dot:
        sense.set_pixel(7, 0, 255, 0, 0)

# instruction screen
sense.show_message("UP=A RIGHT=B LEFT=C DOWN=-", text_colour=[138, 43, 226])
print("Press the joystick to start/stop recording. The current label will be shown on the LED matrix. UP=A RIGHT=B LEFT=C DOWN=-")
# flush old joystick events
sense.stick.get_events()
# cooldown (green screen)
cooldown = True
sense.clear(0, 255, 0)
time.sleep(2.5)

cooldown = False
sense.clear()
sense.set_pixels(smiley)

current_label = None
recording = False
recording_direction = None
cooldown = False

logger_process = None

# blinking
blink = False
last_blink = time.time()

while True:

    # blinking red dot while recording
    if recording:
        if time.time() - last_blink > 0.5:
            blink = not blink
            last_blink = time.time()

        show_letter_with_dot(current_label, blink)

    # show smiley when idle
    if not recording and not cooldown:
        sense.set_pixels(smiley)

    for event in sense.stick.get_events():
        if event.action != "pressed":
            continue

        direction = event.direction

        if cooldown:
            continue

        # START
        if not recording:
            current_label = label_map.get(direction)

            if current_label is not None:
                recording = True
                recording_direction = direction

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = os.path.join(recording_dir, f"{timestamp}_{current_label}.csv")

                print(f"START recording {current_label} => {filename}")

                script_dir = os.path.dirname(os.path.abspath(__file__))
                logger_path = os.path.join(script_dir, "logger_recorder")

                logger_process = subprocess.Popen([logger_path, filename, current_label])

                show_letter_with_dot(current_label, True)

        # STOP
        else:
            if direction == recording_direction:
                print(f"STOP recording {current_label}")

                recording = False
                recording_direction = None

                if logger_process:
                    logger_process.terminate()
                    logger_process.wait()
                    logger_process = None

                # cooldown (green screen)
                cooldown = True
                sense.clear(0, 255, 0)
                time.sleep(2.5)

                cooldown = False
                sense.clear()

    time.sleep(0.05)
```

to run the program:
```bash
python3 EAI4-Babsi-Bobby-Collab/Assignments/HW02/video_recording.py
```

# Task 7
![alt text](images/image-2.png)
Based on the files video_recordings.py and logger_recording.cpp I only added the following lines marked by comments stating that the line is done for Task 7.

```cpp
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
```

# Task 8
![alt text](images/image-1.png)
I used the suggested command:
```bash
PS C:\Users\Celina Binder\Documents\FH_Hagenberg> scp kit-18@10.42.0.1:/home/kit-18/Documents/EAI/EAI4-Babsi-Bobby-Collab/Assignments/HW02/recordings/*.csv /EAI
```


