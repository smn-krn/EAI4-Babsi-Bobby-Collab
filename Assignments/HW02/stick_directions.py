from sense_hat import SenseHat

sense = SenseHat()

current_label = "A"
sense.show_letter(current_label, text_colour=[138, 43, 226])

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
            sense.show_letter(current_label,  text_colour=[138, 43, 226])