# %pip install sense_hat
import time, random
from sense_hat import SenseHat

sense = SenseHat()

#defining the colors
snake_color = (0, 255, 0) #green
food_color = (255, 0, 0) #red
clear = (0, 0, 0) #black
sense.show_message("3 2 1 Go!", text_colour=snake_color)

# initial configurations
snake_position = [[2, 2]] #initial position of the snake
moving_direction = [0, 1] #vector that moves the snake to the right
snake_length = 1 #initial length of the snake
food_position = [random.randint(0,7), random.randint(0,7)] #random position for the food #storing food in 2d ccoordinate

# background_color = [clear] * 64 #background color is black #pixels are stored in 1d array
#method to set the direction
#store direction as a vector, to easily add it to the snake's position to move it

def set_directions(direction):
    global moving_direction

    if direction == "up" and moving_direction != [0,1]:
        moving_direction = [0,-1]
    elif direction == "down" and moving_direction != [0,-1]:
        moving_direction = [0,1]
    elif direction == "left" and moving_direction != [1,0]:
        moving_direction = [-1,0]
    elif direction == "right" and moving_direction != [-1,0]:
        moving_direction = [1,0]


# generated with claude sonnet 4.6
# prompt: " generate me an explosion effect starting in the middle, moving outwards to the edges in white and blue ccolors 
# on my rasperry pi sense hat snake game programmed with python"
def explosion_effect(sense, center, score):
    import time

    C1 = (255, 0, 0)      # red
    C2 = (255, 140, 0)    # orange
    C3 = (255, 255, 0)    # yellow
    BLACK = (0, 0, 0)

    colors = [C1, C2, C3]

    # expand outward slowly
    for radius in range(8):
        pixels = [BLACK] * 64

        for x in range(8):
            for y in range(8):
                dist = max(abs(x - center[0]), abs(y - center[1]))

                if dist == radius:
                    pixels[y * 8 + x] = colors[radius % 3]
                elif dist == radius - 1:
                    pixels[y * 8 + x] = colors[(radius + 1) % 3]
                elif dist == radius - 2:
                    pixels[y * 8 + x] = colors[(radius + 2) % 3]

        sense.set_pixels(pixels)
        time.sleep(0.18)   # slow cascade outward

    time.sleep(0.3)
    sense.clear()

    # display score
    message = f"Score: {score}"
    sense.show_message(
        message,
        text_colour=C1,
        scroll_speed=0.05
    )


#game loop
move_delay = 0.5 # as specified in the task 500ms
last_move = time.time()

while True:

    # read joystick immediately
    for move in sense.stick.get_events():
        if move.action == "pressed":
            set_directions(move.direction)

    # only move snake every move_delay seconds
    if time.time() - last_move > move_delay:
        last_move = time.time()

        snake_position.insert(0, [
            snake_position[0][0] + moving_direction[0],
            snake_position[0][1] + moving_direction[1]
        ])

        # Collision with wall
        if snake_position[0][0] < 0 or snake_position[0][0] > 7 or snake_position[0][1] < 0 or snake_position[0][1] > 7:
            head_x = max(0, min(7, snake_position[0][0]))
            head_y = max(0, min(7, snake_position[0][1]))

            explosion_effect(sense, (head_x, head_y), snake_length)
            sense.show_message("Game Over!", text_colour=food_color)
            break

        # Food collision
        if snake_position[0] == food_position:
            while True:
                food_position = [random.randint(0,7), random.randint(0,7)]
                if food_position not in snake_position:
                    break
            snake_length += 1

        # Self collision
        elif snake_position[0] in snake_position[1:]:
            head_x = max(0, min(7, snake_position[0][0]))
            head_y = max(0, min(7, snake_position[0][1]))

            explosion_effect(sense, (head_x, head_y), snake_length)

            sense.show_message("Game Over! :(", text_colour=food_color)
            break

        else:
            snake_position[:] = snake_position[:snake_length]

        # draw frame
        pixels = [clear] * 64

        for pos in snake_position:
            pixels[pos[1] * 8 + pos[0]] = snake_color

        pixels[food_position[1] * 8 + food_position[0]] = food_color
        sense.set_pixels(pixels)

    time.sleep(0.01)