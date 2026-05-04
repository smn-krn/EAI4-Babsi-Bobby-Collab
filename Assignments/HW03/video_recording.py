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

# TASK 7: Log program start
print("[video_recording] Program started.")

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

                # TASK 7: log start of recording with label and filename
                print(f"[video_recording] START recording | Label: {current_label} | File: {filename}")

                script_dir = os.path.dirname(os.path.abspath(__file__))
                logger_path = os.path.join(script_dir, "logger_recorder")

                # TASK 7: Log error if logger_recorder process fails to start
                try:
                    logger_process = subprocess.Popen([logger_path, filename, current_label])
                except Exception as e:
                    print(f"[video_recording] ERROR: Failed to start logger_recorder: {e}")

                show_letter_with_dot(current_label, True)

        # STOP
        else:
            if direction == recording_direction:
                # TASK 7: Log stop of recording with label and filename
                print(f"[video_recording] STOP recording | Label: {current_label} | File: {filename}")

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
