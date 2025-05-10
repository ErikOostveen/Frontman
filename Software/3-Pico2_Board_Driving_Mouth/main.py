import uasyncio as asyncio
import machine
import tft_config
import gc9a01
from machine import UART, Pin
from tft_config import config, colorSchemes
from expressions import *
import random
import math

bitmap_drawn = False
prev_mouthMode = None
last_random_mouth_mode = None

# ----- MSGEQ7 Pin Assignments -----
strobe_pin = machine.Pin(10, machine.Pin.OUT)
reset_pin  = machine.Pin(11, machine.Pin.OUT)
adc_pin    = machine.Pin(26)
adc        = machine.ADC(adc_pin)

# --- Define expressions list ---
expressions = [
    (mouth_anger_bitmap, mouth_anger_palette),
    (mouth_disgust_bitmap, mouth_disgust_palette),
    (mouth_smile_bitmap, mouth_smile_palette),
    (mouth_dracula_bitmap, mouth_dracula_palette),
    (mouth_love_bitmap, mouth_love_palette),
]

def blend_with_black(base_color, ratio):
    r5 = (base_color >> 11) & 0x1F
    g6 = (base_color >> 5) & 0x3F
    b5 = base_color & 0x1F

    r = int(r5 * 8.2258 * ratio)
    g = int(g6 * 4.0476 * ratio)
    b = int(b5 * 8.2258 * ratio)

    return gc9a01.color565(r, g, b)

    return gc9a01.color565(r, g, b)

def draw_ring(cx, cy, inner_r, outer_r, color):
    for y in range(-outer_r, outer_r + 1):
        for x in range(-outer_r, outer_r + 1):
            dist_sq = x * x + y * y
            if inner_r * inner_r <= dist_sq <= outer_r * outer_r:
                tft.pixel(cx + x, cy + y, color)

def draw_ring_segment(cx, cy, inner_r, outer_r, color):
    for y in range(-outer_r, outer_r + 1):
        dist = abs(y)
        if dist < inner_r or dist > outer_r:
            continue
        x_len = int(math.sqrt(outer_r**2 - y**2))
        x_trim = int(math.sqrt(inner_r**2 - y**2)) if dist < inner_r else 0
        tft.hline(cx - x_len, cy + y, 2 * x_len + 1, color)
        if x_trim > 0:
            tft.hline(cx - x_trim, cy + y, 2 * x_trim + 1, BLACK)

def level_to_color(level):
    # Normalize level and return color
    level = max(0, min(level - SILENCE_THRESHOLD, 65535 - SILENCE_THRESHOLD))
    ratio = level / 60000
    # Blend from blue (low) to red (high)
    r = int(255 * ratio)
    g = 0
    b = int(255 * (1 - ratio))
    return gc9a01.color565(r, g, b)

async def update_rings(levels):
    global prev_ring_colors
    center_x = CENTER_X
    center_y = CENTER_Y
    ring_thickness = 5
    radii = [10, 20, 30, 40, 50, 60, 70]

    for i in range(7):
        level = levels[i]
        effective = max(0, level - SILENCE_THRESHOLD)
        ratio = min(1.0, effective / 60000)

        target_color = blend_with_black(current_color_scheme[i], ratio)

        if target_color != prev_ring_colors[i]:
            outer_r = radii[i]
            inner_r = outer_r - ring_thickness
            draw_ring(CENTER_X, CENTER_Y, inner_r, outer_r, target_color)
            prev_ring_colors[i] = target_color
  
def short_delay_us(us):
    for _ in range(us * 5):
        pass

async def init_msgeq7():
    reset_pin.value(0)
    strobe_pin.value(0)
    await asyncio.sleep_ms(1)
    reset_pin.value(1)
    await asyncio.sleep_ms(1)
    reset_pin.value(0)
    strobe_pin.value(1)
    await asyncio.sleep_ms(1)

async def read_msgeq7():
    levels = [0] * 7
    for i in range(7):
        strobe_pin.value(0)
        short_delay_us(100)
        levels[i] = adc.read_u16()
        strobe_pin.value(1)
        short_delay_us(100)
    return levels

# ----- TFT Display Setup -----
tft = tft_config.config(rotation=0)
tft.init()
tft.fill(0)

# ----- Visualization Settings -----
GAIN = 1.3
SILENCE_THRESHOLD = 5000
BLACK = 0
WHITE = gc9a01.color565(255, 255, 255)


TOTAL_WIDTH = 240
TOTAL_HEIGHT = 240
CENTER_X = TOTAL_WIDTH // 2
CENTER_Y = TOTAL_HEIGHT // 2

USABLE_WIDTH = int(TOTAL_WIDTH * 0.8)
SPACING = 1
original_bar_width = (USABLE_WIDTH - SPACING * 6) // 7
BAR_WIDTH = int(original_bar_width * 0.75)
USED_WIDTH = BAR_WIDTH * 7 + SPACING * 6
MARGIN_X = (TOTAL_WIDTH - USED_WIDTH) // 2
MARGIN_Y = 2
AVAILABLE_HEIGHT = TOTAL_HEIGHT - 2 * MARGIN_Y
MAX_HALF = int((AVAILABLE_HEIGHT // 2) * 0.8)

# ----- Color Scheme -----
ColScheme = 1
current_color_scheme = colorSchemes[ColScheme]

# ----- Visualization Mode -----
mouthMode = 101
prev_half_bars = [-1] * 7
prev_ring_colors = [None] * 7

def draw_bitmap(bitmap, palette, width, height, mode):
    if mode == 106:
        bg_color = gc9a01.color565(255, 192, 203)  # Light pink
    else:
        bg_color = gc9a01.color565(0, 0, 0)  # Black
    
    tft.fill(bg_color)  
    
    start_x = (TOTAL_WIDTH - width) // 2
    start_y = (TOTAL_HEIGHT - height) // 2
    for row in range(height):
        for col in range(width):
            idx = bitmap[row][col]  # Correct for 2D list
            r, g, b = palette[idx]
            color = gc9a01.color565(r, g, b)
            tft.pixel(start_x + col, start_y + row, color)

# ----- Visualization Functions -----
async def update_bars(levels):
    global prev_half_bars
    for i, level in enumerate(levels):
        effective_level = level - SILENCE_THRESHOLD if level > SILENCE_THRESHOLD else 0
        scale = (effective_level / 60000) if 60000 > 0 else 0
        half_bar = int(scale * MAX_HALF * GAIN)
        half_bar = max(1, min(half_bar, MAX_HALF))

        if half_bar != prev_half_bars[i]:
            x = MARGIN_X + i * (BAR_WIDTH + SPACING)
            tft.fill_rect(x, MARGIN_Y, BAR_WIDTH, AVAILABLE_HEIGHT, BLACK)
            y = CENTER_Y - half_bar
            height = half_bar * 2
            tft.fill_rect(x, y, BAR_WIDTH, height, current_color_scheme[i])
            prev_half_bars[i] = half_bar

# ----- UART SETUP -----
uart = UART(0, baudrate=115200, rx=Pin(17))

def extract_commands(text):
    commands = []
    parts = text.split()
    for part in parts:
        if part.startswith("C") and part[1:].isdigit():
            commands.append(('color', int(part[1:])))
        elif part.startswith("M") and part[1:].isdigit():
            commands.append(('mouth', int(part[1:])))
    return commands

async def uart_receive():
    global ColScheme, current_color_scheme, mouthMode, prev_half_bars, last_random_mouth_mode
    valid_modes = [101, 102, 103, 104, 105, 107]

    while True:
        if uart.any():
            try:
                data = uart.readline()
                if data:
                    text = data.decode().strip()
                    print("Received:", repr(text))
                    commands = extract_commands(text)
                    for cmd, value in commands:
                        if cmd == 'color' and 1 <= value <= 25:
                            ColScheme = value
                            current_color_scheme = colorSchemes[ColScheme]
                            prev_half_bars = [-1] * 7
                            print("UART set ColScheme:", ColScheme)

                        elif cmd == 'mouth':
                            if value == 106:
                                mouthMode = 106  # special case: allow directly
                                print("UART set mouthMode:", mouthMode)
                            elif value in valid_modes:
                                new_mode = random.choice(
                                    [m for m in valid_modes if m != last_random_mouth_mode]
                                )
                                last_random_mouth_mode = new_mode
                                mouthMode = new_mode
                                print("UART randomized mouthMode to:", mouthMode)


            except Exception as e:
                print("UART error:", e)

        await asyncio.sleep(0.1)

# ----- Main Loop -----
async def main():
    global bitmap_drawn, prev_mouthMode
    while True:
        await init_msgeq7()
        levels = await read_msgeq7()

        if mouthMode != prev_mouthMode:
            tft.fill(BLACK)
            bitmap_drawn = False
            prev_mouthMode = mouthMode

        if mouthMode == 101:
            await update_bars(levels)

        elif mouthMode in [102, 103, 104, 105, 106] and not bitmap_drawn:
            index = mouthMode - 102
            if index < len(expressions):
                bitmap, palette = expressions[index]
                draw_bitmap(bitmap, palette, 120, 120, mouthMode)
                bitmap_drawn = True
                
        elif mouthMode == 107:
            await update_rings(levels)

        await asyncio.sleep(0.05)


# ----- Combined Main -----
async def combined_main():
    await asyncio.gather(
        uart_receive(),
        main()
    )

asyncio.run(combined_main())