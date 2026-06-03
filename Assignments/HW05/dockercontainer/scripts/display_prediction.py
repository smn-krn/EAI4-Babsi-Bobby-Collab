"""Display the predicted gesture on the Sense HAT LED matrix."""

from sense_hat import SenseHat
import sys

sense = SenseHat()

# check if a gesture is provided as a command-line argument
if len(sys.argv) < 2:
    sys.exit(1)

gesture = sys.argv[1] # get the predicted gesture from the command-line argument

colors = {
    "A": [0, 255, 0], # Green for "A"
    "B": [0, 0, 255], # Blue for "B"
    "C": [255, 255, 0], # Yellow for "C"
    "-": [255, 0, 0] # Red for "-" (garbage class)
}

color = colors.get(gesture, [255, 255, 255]) # White for unknown gestures

sense.show_letter(
    gesture,
    text_colour=color
) # display predicted gesture on the LED matrix with the corresponding color