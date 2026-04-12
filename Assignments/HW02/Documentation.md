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

# Task 5
![alt text](images/image-4.png)

# Task 6
![alt text](images/image-3.png)

# Task 7
![alt text](images/image-2.png)

# Task 8
![alt text](images/image-1.png)