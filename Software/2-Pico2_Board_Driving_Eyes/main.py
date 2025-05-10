import uasyncio as asyncio
import random
import math
import gc9a01
import tft_config
from machine import Pin, UART, PWM
from micropython_rotary_encoder import RotaryEncoderRP2, RotaryEncoderEvent
from uasyncio import Lock
import time  # Needed for seeding RNG (optional)

color_scheme_changed = False
eyes_mode_changed = False

dollar_bitmap = [
    "00100",
    "01111",
    "10000",
    "10000",
    "01110",
    "00001",
    "00001",
    "11110",
    "00100"
]

heart_bitmap = [
    "001110011100",
    "011111111110",
    "111111111111",
    "111111111111",
    "111111111111",
    "111111111111",
    "011111111110",
    "001111111100",
    "000111111000",
    "000011110000",
    "000001100000"
]

bat_bitmap = [
    "1,1,0,0,0,0,0,0,0,0,0,1,1",
    "0,1,1,0,0,1,0,1,0,0,1,1,0",
    "0,0,1,1,0,1,1,1,0,1,1,0,0",
    "0,0,0,1,1,1,1,1,1,1,0,0,0",
    "0,0,0,1,1,1,1,1,1,1,0,0,0",
    "0,0,0,0,1,1,1,1,1,0,0,0,0",
    "0,0,0,0,0,0,1,0,0,0,0,0,0",
]

def draw_dollar_sign(tft, cx, cy, scale, color):
    # Draw a 5x9 dollar sign bitmap centered at (cx, cy)
    for row_index, row in enumerate(dollar_bitmap):
        for col_index, pixel in enumerate(row):
            if pixel == "1":
                for dy in range(scale):
                    for dx in range(scale):
                        x = cx + (col_index - 2) * scale + dx
                        y = cy + (row_index - 4) * scale + dy
                        tft.pixel(x, y, color)

def draw_heart(tft, cx, cy, scale, color):
    width = len(heart_bitmap[0])
    height = len(heart_bitmap)
    offset_x = (width * scale) // 2
    offset_y = (height * scale) // 2

    for y, row in enumerate(heart_bitmap):
        for x, bit in enumerate(row):
            if bit == "1":
                tft.fill_rect(
                    cx - offset_x + x * scale,
                    cy - offset_y + y * scale,
                    scale,
                    scale,
                    color
                )

def draw_bat(tft, cx, cy, scale, color):
    for row_index, row in enumerate(bat_bitmap):
        bits = row.split(",")
        for col_index, bit in enumerate(bits):
            if bit == "1":
                for dy in range(scale):
                    for dx in range(scale):
                        x = cx + (col_index - len(bits) // 2) * scale + dx
                        y = cy + (row_index - len(bat_bitmap) // 2) * scale + dy
                        tft.pixel(x, y, color)

led_tasks = [None, None, None]  # For pins 11, 12, 13

led_pattern = [(5.0, 100)] * 3  # Default: (fade_time, steps) for R, G, B

draw_lock = Lock()

# Global flag
force_animation = False  # Trigger immediate animation when encoder is rotated

# ----- USER CONFIGURABLE PARAMETERS -----
ANIMATION_STEP_DELAY_MIN = 0.001    # Minimum delay between animation steps (seconds)
ANIMATION_STEP_DELAY_MAX = 0.010    # Maximum delay between animation steps (seconds)
INTER_MOVEMENT_DELAY_MIN   = 0.25    # Minimum delay between movements (seconds)
INTER_MOVEMENT_DELAY_MAX   = 5.00    # Maximum delay between movements (seconds)
BLINK_DELAY                = 0.12    # Blink delay (seconds)

# ----- EYE SETUP (for both displays) -----
cx = 240 // 2
cy = 240 // 2
eye_radius = 60                     # Bigger eyes
base_iris_radius = eye_radius // 2    # 30
iris_offset = (eye_radius * 3) // 4   # 45
clear_margin = 2

# Sclera is always black.
def get_sclera_color():
    if eyesMode == 106:
        return gc9a01.color565(255, 255, 255)  # White
    else:
        return gc9a01.color565(0, 0, 0)  # Black
BLACK = 0

# ----- GLOBAL COLOR SCHEME VARIABLE & ACCESSOR -----
counter = 1    # Global counter selects the color scheme (1 to 25)
encoder_changed = False    # Flag set True when encoder or button events change the display

def get_current_color_scheme():
    return tft_config.color_schemes[counter - 1]

# ----- EYES MODE & OVAL DIMENSIONS -----
# Use eyesMode: 101 = round eyes, 102 = square eyes, 103 = oval eyes, 104 = rhombus., 105 = $, 106 = Heart
eyesMode = 101   # Startup eyesMode = 101 (round eyes)
# For oval eyes (mode 103), adjust these factors for drawing:
OVAL_H_FACTOR = 0.5   # Horizontal radius factor relative to iris_r.
OVAL_V_FACTOR = 1.0   # Vertical radius factor relative to iris_r.

# ----- ENCODER SETUP -----
encoder_pin_clk = Pin(1, Pin.IN, Pin.PULL_UP)
encoder_pin_dt  = Pin(19, Pin.IN, Pin.PULL_UP)
encoder = RotaryEncoderRP2(pin_clk=encoder_pin_clk, pin_dt=encoder_pin_dt)

def dec_counter():
    global counter, encoder_changed, force_animation, color_scheme_changed
    counter = max(1, counter - 1)
    encoder_changed = True
    force_animation = True
    color_scheme_changed = True

def inc_counter():
    global counter, encoder_changed, force_animation, color_scheme_changed
    counter = min(25, counter + 1)
    encoder_changed = True
    force_animation = True
    color_scheme_changed = True

encoder.on(RotaryEncoderEvent.TURN_LEFT, dec_counter)
encoder.on(RotaryEncoderEvent.TURN_LEFT_FAST, dec_counter)
encoder.on(RotaryEncoderEvent.TURN_RIGHT, inc_counter)
encoder.on(RotaryEncoderEvent.TURN_RIGHT_FAST, inc_counter)

# ----- BUTTON SETUP -----
# Button connected to GP2 (with internal pull-up; low when pressed)
button = Pin(2, Pin.IN, Pin.PULL_UP)

async def check_button():
    global eyesMode, encoder_changed, eyes_mode_changed
    last_state = button.value()
    mode_choices = [101, 102, 103, 104, 105, 106, 107]  # Valid expression modes

    while True:
        state = button.value()
        if state == 0 and last_state == 1:
            old_mode = eyesMode
            new_mode = old_mode
            while new_mode == old_mode:
                new_mode = random.choice(mode_choices)

            eyesMode = new_mode
            encoder_changed = True
            eyes_mode_changed = True

            # New random LED pattern
            global led_pattern, led_tasks

            led_pattern = [
                (random.uniform(0.25, 10.0), random.randint(2, 200)) for _ in range(3)
            ]

            # Cancel existing LED tasks
            for task in led_tasks:
                if task:
                    task.cancel()

            # Restart LED fade tasks with new parameters
            led_tasks[0] = asyncio.create_task(led_fade(11, *led_pattern[0]))
            led_tasks[1] = asyncio.create_task(led_fade(12, *led_pattern[1]))
            led_tasks[2] = asyncio.create_task(led_fade(13, *led_pattern[2]))

        last_state = state
        await asyncio.sleep(0.05)

            
        last_state = state
        await asyncio.sleep(0.05)            

# ----- UART SETUP -----
# Configure UART0 with TX on GP16 (Pin 21) at 115200 baud.
uart = UART(0, baudrate=115200, tx=Pin(16))
# We'll track last transmitted values:
last_eyesMode = eyesMode
last_counter = counter

async def uart_transmit():
    global counter, eyesMode
    global color_scheme_changed, eyes_mode_changed

    while True:
        if color_scheme_changed:
            uart.write("C{}\n".format(counter))
            print("C{}\n".format(counter))
            color_scheme_changed = False

        if eyes_mode_changed:
            uart.write("M{}\n".format(eyesMode))
            print("M{}\n".format(eyesMode))
            eyes_mode_changed = False

        await asyncio.sleep(0.05)

# ----- HELPER FUNCTION: fill_ellipse -----
def fill_ellipse(tft, cx, cy, a, b, color):
    for y in range(-b, b + 1):
        try:
            x_extent = int(a * math.sqrt(1 - (y / b) ** 2))
        except ValueError:
            x_extent = 0
        tft.fill_rect(cx - x_extent, cy + y, 2 * x_extent, 1, color)

# ----- DRAWING FUNCTIONS (using dynamic color scheme and eyesMode) -----
def clear_iris_region_with_size(tft, old_x, old_y, old_r):
    global eyesMode
    margin = clear_margin
    x0 = old_x - old_r - margin
    y0 = old_y - old_r - margin
    w = 2 * old_r + 2 * margin
    h = 2 * old_r + 2 * margin

    if eyesMode == 105:
        scale = max(1, old_r // 4)
        half_w = (5 * scale) // 2
        half_h = (9 * scale) // 2
        pad_y = 2
        x0 = old_x - half_w - margin
        y0 = old_y - half_h - margin
        w = 5 * scale + 3 * margin
        h = 9 * scale + 3 * margin + pad_y

    # Use pink background for heart eyes (106)
    if eyesMode == 106:
        bg_color = gc9a01.color565(255, 192, 203)  # Light pink
    else:
        bg_color = gc9a01.color565(0, 0, 0)  # Black sclera fallback

    tft.fill_rect(x0, y0, w, h, bg_color)


def draw_iris(tft, iris_cx, iris_cy, iris_r):
    cs = get_current_color_scheme()
    if eyesMode == 104:
        # Evil eyes: sharp diamond iris + vertical slit pupil
        outer_r = iris_r
        inner_r = int(iris_r * 0.7)
        pupil_w = max(1, iris_r // 6)
        pupil_h = iris_r

        # Draw sharp diamond-like iris (rotated square)
        for offset in range(-outer_r, outer_r + 1):
            width = outer_r - abs(offset)
            tft.fill_rect(iris_cx - width, iris_cy + offset, width * 2, 1, cs["iris_outer"])
        for offset in range(-inner_r, inner_r + 1):
            width = inner_r - abs(offset)
            tft.fill_rect(iris_cx - width, iris_cy + offset, width * 2, 1, cs["iris_inner"])

        # Draw vertical slit pupil (white instead of black)
        WHITE = gc9a01.color565(255, 255, 255)
        tft.fill_rect(iris_cx - pupil_w // 2, iris_cy - pupil_h // 2, pupil_w, pupil_h, BLACK)   
    
    if eyesMode == 101:
        tft.fill_circle(iris_cx, iris_cy, iris_r, cs["iris_outer"])
        inner_r = int(iris_r * 0.8)
        tft.fill_circle(iris_cx, iris_cy, inner_r, cs["iris_inner"])
        pupil_r = iris_r // 2
        tft.fill_circle(iris_cx, iris_cy, pupil_r, cs["pupil"])
        highlight_r = pupil_r // 2
        highlight_x = iris_cx - (pupil_r // 2)
        highlight_y = iris_cy - (pupil_r // 2)
        tft.fill_circle(highlight_x, highlight_y, highlight_r, cs["highlight"])
    elif eyesMode == 102:
        outer_side = 2 * iris_r
        tft.fill_rect(iris_cx - iris_r, iris_cy - iris_r, outer_side, outer_side, cs["iris_outer"])
        inner_side = int(outer_side * 0.8)
        tft.fill_rect(iris_cx - inner_side // 2, iris_cy - inner_side // 2, inner_side, inner_side, cs["iris_inner"])
        pupil_side = outer_side // 2
        tft.fill_rect(iris_cx - pupil_side // 2, iris_cy - pupil_side // 2, pupil_side, pupil_side, cs["pupil"])
        highlight_side = pupil_side // 2
        tft.fill_rect(iris_cx - highlight_side // 2, iris_cy - highlight_side // 2, highlight_side, highlight_side, cs["highlight"])
    elif eyesMode == 103:
        a_outer = int(iris_r * OVAL_H_FACTOR)
        b_outer = int(iris_r * OVAL_V_FACTOR)
        fill_ellipse(tft, iris_cx, iris_cy, a_outer, b_outer, cs["iris_outer"])
        a_inner = int(a_outer * 0.8)
        b_inner = int(b_outer * 0.8)
        fill_ellipse(tft, iris_cx, iris_cy, a_inner, b_inner, cs["iris_inner"])
        a_pupil = a_outer // 2
        b_pupil = b_outer // 2
        fill_ellipse(tft, iris_cx, iris_cy, a_pupil, b_pupil, cs["pupil"])
        a_highlight = a_pupil // 2
        b_highlight = b_pupil // 2
        fill_ellipse(tft, iris_cx - (a_pupil // 2), iris_cy - (b_pupil // 2), a_highlight, b_highlight, cs["highlight"])
    elif eyesMode == 104:
        # Evil eyes: sharp diamond iris + vertical slit pupil
        scale = 1.1  # 20% bigger
        outer_r = int(iris_r * scale)
        inner_r = int(iris_r * 0.7 * scale)
        pupil_w = max(1, int((iris_r // 6) * scale))
        pupil_h = int(iris_r * scale)

        # Draw sharp diamond-like iris (rotated square)
        for offset in range(-outer_r, outer_r + 1):
            width = outer_r - abs(offset)
            tft.fill_rect(iris_cx - width, iris_cy + offset, width * 2, 1, cs["iris_outer"])
        for offset in range(-inner_r, inner_r + 1):
            width = inner_r - abs(offset)
            tft.fill_rect(iris_cx - width, iris_cy + offset, width * 2, 1, cs["iris_inner"])

        # Draw vertical slit pupil (black)
        tft.fill_rect(iris_cx - pupil_w // 2, iris_cy - pupil_h // 2, pupil_w, pupil_h, BLACK)
    elif eyesMode == 105:
        # Dollar sign eyes
        scale = max(1, iris_r // 4)  # Adjust size relative to iris
        draw_dollar_sign(tft, iris_cx, iris_cy, scale, cs["iris_outer"])
    elif eyesMode == 106:
        # Heart eyes
        scale = max(1, iris_r // 6)  # Scale based on iris size
        draw_heart(tft, iris_cx, iris_cy, scale, cs["iris_outer"])
    elif eyesMode == 107:
        # Bat eyes
        scale = max(1, iris_r // 6)  # Adjust as needed
        draw_bat(tft, iris_cx, iris_cy, scale, cs["iris_outer"])
        

def update_iris_with_size(tft, old_x, old_y, new_x, new_y, old_r, new_r):
    global eyesMode

    # Defaults
    adjusted_old_r = old_r
    adjusted_new_r = new_r
    margin = clear_margin

    if eyesMode == 104:
        scale = 1.1
        adjusted_old_r = int(old_r * scale)
        adjusted_new_r = int(new_r * scale)
        margin = int(adjusted_old_r * 0.5)

    elif eyesMode == 105:
        scale_old = max(1, old_r // 4)
        scale_new = max(1, new_r // 4)
        half_w_old = (5 * scale_old) // 2
        half_h_old = (9 * scale_old) // 2
        half_w_new = (5 * scale_new) // 2
        half_h_new = (9 * scale_new) // 2
        adjusted_old_r = max(half_w_old, half_h_old + 2)
        adjusted_new_r = max(half_w_new, half_h_new + 2)
        margin = 2

    # ----- INSERT THIS BLOCK to fix bat trails -----
    if eyesMode == 107:
        scale = max(1, old_r // 6)
        width = 15 * scale  # Updated bitmap width
        height = 7 * scale
        x0 = old_x - width // 2 - margin
        y0 = old_y - height // 2 - margin
        w = width + 2 * margin
        h = height + 2 * margin
        tft.fill_rect(x0, y0, w, h, BLACK)
    # ------------------------------------------------

    if (old_x, old_y, old_r) == (new_x, new_y, new_r):
        return (old_x, old_y, old_r)

    old_left   = old_x - adjusted_old_r - margin
    old_top    = old_y - adjusted_old_r - margin
    old_right  = old_x + adjusted_old_r + margin
    old_bottom = old_y + adjusted_old_r + margin

    new_left   = new_x - adjusted_new_r - margin
    new_top    = new_y - adjusted_new_r - margin
    new_right  = new_x + adjusted_new_r + margin
    new_bottom = new_y + adjusted_new_r + margin

    left   = min(old_left, new_left)
    top    = min(old_top, new_top)
    right  = max(old_right, new_right)
    bottom = max(old_bottom, new_bottom)

    width = right - left
    height = bottom - top

    if eyesMode == 106:
        bg_color = gc9a01.color565(255, 192, 203)
    else:
        bg_color = gc9a01.color565(0, 0, 0)

    tft.fill_rect(left, top, width, height, bg_color)
    draw_iris(tft, new_x, new_y, new_r)
    return (new_x, new_y, new_r)


def draw_sclera(tft):
    if eyesMode == 106:
        # Light pink background for heart eyes
        PINK = gc9a01.color565(255, 192, 203)
        tft.fill(PINK)
    else:
        tft.fill(BLACK)
        tft.fill_circle(cx, cy, eye_radius, get_sclera_color())

# ----- GLOBAL EYE STATE -----
current_state1 = (cx, cy, base_iris_radius)
current_state2 = (cx, cy, base_iris_radius)

# ----- ANIMATION FUNCTIONS -----
async def animate_eyes(tft1, state1, tft2, state2, steps, target1=None, target2=None):
    from uasyncio import Lock
    global draw_lock

    (start_x1, start_y1, start_r1) = state1
    (start_x2, start_y2, start_r2) = state2

    if target1 is None:
        angle1 = random.uniform(0, 2 * math.pi)
        distance1 = random.uniform(0, iris_offset)
        target_r1 = int(base_iris_radius * random.uniform(0.8, 1.2))
        target_x1 = cx + int(distance1 * math.cos(angle1))
        target_y1 = cy + int(distance1 * math.sin(angle1))
    else:
        target_x1, target_y1, target_r1 = target1

    if target2 is None:
        angle2 = random.uniform(0, 2 * math.pi)
        distance2 = random.uniform(0, iris_offset)
        target_r2 = int(base_iris_radius * random.uniform(0.8, 1.2))
        target_x2 = cx + int(distance2 * math.cos(angle2))
        target_y2 = cy + int(distance2 * math.sin(angle2))
    else:
        target_x2, target_y2, target_r2 = target2

    dx1 = (target_x1 - start_x1) / steps
    dy1 = (target_y1 - start_y1) / steps
    dr1 = (target_r1 - start_r1) / steps
    dx2 = (target_x2 - start_x2) / steps
    dy2 = (target_y2 - start_y2) / steps
    dr2 = (target_r2 - start_r2) / steps

    local_state1 = state1
    local_state2 = state2

    async with draw_lock:
        for i in range(steps):
            new_x1 = int(start_x1 + dx1 * (i + 1))
            new_y1 = int(start_y1 + dy1 * (i + 1))
            new_r1 = int(start_r1 + dr1 * (i + 1))
            new_x2 = int(start_x2 + dx2 * (i + 1))
            new_y2 = int(start_y2 + dy2 * (i + 1))
            new_r2 = int(start_r2 + dr2 * (i + 1))

            local_state1 = update_iris_with_size(
                tft1, local_state1[0], local_state1[1],
                new_x1, new_y1, local_state1[2], new_r1
            )
            local_state2 = update_iris_with_size(
                tft2, local_state2[0], local_state2[1],
                new_x2, new_y2, local_state2[2], new_r2
            )
            await asyncio.sleep(random.uniform(ANIMATION_STEP_DELAY_MIN, ANIMATION_STEP_DELAY_MAX))

    return local_state1, local_state2


async def blink_eyes(tft1, state1, tft2, state2, blink_delay=BLINK_DELAY):
    num_blinks = random.choice([1, 2])
    for i in range(num_blinks):
        clear_iris_region_with_size(tft1, state1[0], state1[1], state1[2])
        clear_iris_region_with_size(tft2, state2[0], state2[1], state2[2])
        await asyncio.sleep(blink_delay)
        draw_iris(tft1, state1[0], state1[1], state1[2])
        draw_iris(tft2, state2[0], state2[1], state2[2])
        if i < num_blinks - 1:
            await asyncio.sleep(blink_delay)
    return state1, state2

# ----- LED FADE TASK -----
# Generic LED fade task for a given PWM pin and fade_time (seconds for fade in or fade out).
async def led_fade(pin_number, fade_time=2.0, steps=100):
    try:
        led = PWM(Pin(pin_number))
        led.freq(2000)
        led.duty_u16(0)  # Ensure it's not off forever
        max_duty = 65535
        steps = max(2, steps)
        delay = fade_time / steps

        while True:
            for i in range(steps):
                duty = int((i / (steps - 1)) * max_duty)
                led.duty_u16(duty)
                await asyncio.sleep(delay)
            for i in range(steps):
                duty = int(((steps - 1 - i) / (steps - 1)) * max_duty)
                led.duty_u16(duty)
                await asyncio.sleep(delay)
    except asyncio.CancelledError:
        led.duty_u16(0)  # Turn off gracefully
        return


# ----- MAIN ANIMATION LOOP -----
async def main():
    global tft1, tft2, current_state1, current_state2
    tft1 = tft_config.config1(0)
    tft2 = tft_config.config2(0)
    tft1.init()
    tft2.init()

    draw_sclera(tft1)
    draw_sclera(tft2)

    current_state1 = (cx, cy, base_iris_radius)
    current_state2 = (cx, cy, base_iris_radius)
    draw_iris(tft1, cx, cy, base_iris_radius)
    draw_iris(tft2, cx, cy, base_iris_radius)

    while True:
        steps = random.randint(5, 10)
        common_angle = random.uniform(0, 2 * math.pi)
        common_distance = random.uniform(0, iris_offset)
        if eyesMode == 103:
            common_target_r = int(base_iris_radius * random.uniform(1.0, 1.4))
        else:
            common_target_r = int(base_iris_radius * random.uniform(0.8, 1.2))
        common_target = (cx + int(common_distance * math.cos(common_angle)),
                         cy + int(common_distance * math.sin(common_angle)),
                         common_target_r)

        if random.random() < 0.8:
            target1 = common_target
            target2 = common_target
        else:
            if random.random() < 0.5:
                target1 = None
                target2 = common_target
            else:
                target1 = common_target
                target2 = None

        current_state1, current_state2 = await animate_eyes(tft1, current_state1, tft2, current_state2, steps, target1, target2)
        wait_time = random.uniform(INTER_MOVEMENT_DELAY_MIN, INTER_MOVEMENT_DELAY_MAX)
        if wait_time >= 3:
            await asyncio.sleep(3)
            current_state1, current_state2 = await blink_eyes(tft1, current_state1, tft2, current_state2)
            await asyncio.sleep(wait_time - 3)
        else:
            await asyncio.sleep(wait_time)

# ----- REFRESH TASK -----
async def refresh_display():
    global tft1, tft2, current_state1, current_state2, encoder_changed
    while True:
        if tft1 is not None and tft2 is not None and encoder_changed:
            async with draw_lock:
                tft1.fill(BLACK)
                tft2.fill(BLACK)
                await asyncio.sleep(0.05)
                draw_sclera(tft1)
                draw_iris(tft1, current_state1[0], current_state1[1], current_state1[2])
                draw_sclera(tft2)
                draw_iris(tft2, current_state2[0], current_state2[1], current_state2[2])
                encoder_changed = False
        await asyncio.sleep(0.05)


# ----- COMBINED MAIN -----
async def combined_main():
    global led_pattern
    led_pattern = [
        (random.uniform(0.25, 10.0), random.randint(2, 200)) for _ in range(3)
    ]

    global led_tasks
    led_tasks[0] = asyncio.create_task(led_fade(11, *led_pattern[0]))
    led_tasks[1] = asyncio.create_task(led_fade(12, *led_pattern[1]))
    led_tasks[2] = asyncio.create_task(led_fade(13, *led_pattern[2]))

    # Run everything else that needs to run continuously
    await asyncio.gather(
        encoder.async_tick(),
        main(),
        refresh_display(),
        check_button(),
        uart_transmit()
    )

asyncio.run(combined_main())


