from sense_hat import SenseHat

#Initialize Sense Hat
sense = SenseHat()

sense.show_message("Hello", scroll_speed=0.05)

while True:
	for event in sense.stick.get_events():
		if event.action == "pressed":
			if event.direction == "up":
				sense.show_message("To the heaven :)")
			else: 
				sense.show_message("Best regards from hell :(")
