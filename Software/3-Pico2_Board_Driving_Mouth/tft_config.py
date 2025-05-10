"""Generic 240x240 GC9A01

Generic display connected to a Raspberry Pi Pico.
This module supports configuration of a single display on an SPI bus.
Optimized for improved refresh rate by increasing the SPI baudrate.
"""

from machine import Pin, SPI
import gc9a01

# ----------------------------------------------------------------------
# Shared SPI hardware configuration.
SCL_PIN = 14   # Chip pin 19
SDA_PIN = 15   # Chip pin 20

# ----------------------------------------------------------------------
# Hardware configuration for the display.
DC_PIN  = 4   # Chip pin 6
CS_PIN  = 5   # Chip pin 7
RST_PIN = 6   # Chip pin 9

# ----------------------------------------------------------------------
# Orientation constants.
TFA = 0
BFA = 0
WIDE = 0
TALL = 1

# ----------------------------------------------------------------------
# Create the SPI instance once.
# Increase the baudrate for faster refresh rates.
# In this example we use 40 MHz. Adjust as needed (ensure stability with your display).
spi = SPI(1, baudrate=40_000_000, sck=Pin(SCL_PIN), mosi=Pin(SDA_PIN))

# ----------------------------------------------------------------------
# Create the Pin objects for the display.
_reset = Pin(RST_PIN, Pin.OUT)
_cs    = Pin(CS_PIN, Pin.OUT)
_dc    = Pin(DC_PIN, Pin.OUT)

# ----------------------------------------------------------------------
def config(rotation=0, buffer_size=0, options=0):
    """
    Configure the display and return an instance of gc9a01.GC9A01.
    """
    return gc9a01.GC9A01(
        spi,
        240,
        240,
        reset=_reset,
        cs=_cs,
        dc=_dc,
        rotation=rotation,
        options=options,
        buffer_size=buffer_size,
    )

# ----- Define 25 Color Schemes -----
colorSchemes = {
    1: [gc9a01.color565(0, 0, 255), gc9a01.color565(0, 128, 255),
        gc9a01.color565(0, 255, 255), gc9a01.color565(0, 255, 128),
        gc9a01.color565(255, 255, 0), gc9a01.color565(255, 128, 0),
        gc9a01.color565(255, 0, 0)],
    2: [gc9a01.color565(173,216,230), gc9a01.color565(255,182,193),
        gc9a01.color565(152,251,152), gc9a01.color565(216,191,216),
        gc9a01.color565(255,255,204), gc9a01.color565(255,228,196),
        gc9a01.color565(240,230,140)],
    3: [gc9a01.color565(139,69,19), gc9a01.color565(160,82,45),
        gc9a01.color565(210,180,140), gc9a01.color565(222,184,135),
        gc9a01.color565(188,143,143), gc9a01.color565(128,128,0),
        gc9a01.color565(85,107,47)],
    4: [gc9a01.color565(255,0,255), gc9a01.color565(0,255,255),
        gc9a01.color565(255,255,0), gc9a01.color565(0,255,0),
        gc9a01.color565(0,0,255), gc9a01.color565(255,165,0),
        gc9a01.color565(255,0,0)],
    5: [gc9a01.color565(0,0,0), gc9a01.color565(64,64,64),
        gc9a01.color565(128,128,128), gc9a01.color565(192,192,192),
        gc9a01.color565(224,224,224), gc9a01.color565(240,240,240),
        gc9a01.color565(255,255,255)],
    6: [gc9a01.color565(255,0,127), gc9a01.color565(255,127,0),
        gc9a01.color565(127,255,0), gc9a01.color565(0,255,127),
        gc9a01.color565(0,127,255), gc9a01.color565(127,0,255),
        gc9a01.color565(255,0,0)],
    7: [gc9a01.color565(255,94,77), gc9a01.color565(255,127,80),
        gc9a01.color565(255,160,122), gc9a01.color565(255,182,193),
        gc9a01.color565(255,228,196), gc9a01.color565(255,218,185),
        gc9a01.color565(255,105,180)],
    8: [gc9a01.color565(0,100,0), gc9a01.color565(34,139,34),
        gc9a01.color565(0,128,0), gc9a01.color565(46,139,87),
        gc9a01.color565(60,179,113), gc9a01.color565(32,178,170),
        gc9a01.color565(0,250,154)],
    9: [gc9a01.color565(0,0,139), gc9a01.color565(0,0,205),
        gc9a01.color565(65,105,225), gc9a01.color565(30,144,255),
        gc9a01.color565(135,206,250), gc9a01.color565(176,224,230),
        gc9a01.color565(0,191,255)],
    10: [gc9a01.color565(255,182,193), gc9a01.color565(255,105,180),
         gc9a01.color565(255,20,147), gc9a01.color565(255,99,71),
         gc9a01.color565(255,140,0), gc9a01.color565(255,165,0),
         gc9a01.color565(255,215,0)],
    11: [gc9a01.color565(255,69,0), gc9a01.color565(255,99,71),
         gc9a01.color565(255,140,0), gc9a01.color565(255,165,0),
         gc9a01.color565(255,215,0), gc9a01.color565(255,160,122),
         gc9a01.color565(255,127,80)],
    12: [gc9a01.color565(50,205,50), gc9a01.color565(124,252,0),
         gc9a01.color565(0,255,0), gc9a01.color565(127,255,0),
         gc9a01.color565(173,255,47), gc9a01.color565(152,251,152),
         gc9a01.color565(0,128,0)],
    13: [gc9a01.color565(75,0,130), gc9a01.color565(138,43,226),
         gc9a01.color565(148,0,211), gc9a01.color565(186,85,211),
         gc9a01.color565(216,191,216), gc9a01.color565(221,160,221),
         gc9a01.color565(238,130,238)],
    14: [gc9a01.color565(0,105,148), gc9a01.color565(0,191,255),
         gc9a01.color565(70,130,180), gc9a01.color565(100,149,237),
         gc9a01.color565(135,206,235), gc9a01.color565(176,224,230),
         gc9a01.color565(30,144,255)],
    15: [gc9a01.color565(255,0,0), gc9a01.color565(255,69,0),
         gc9a01.color565(255,140,0), gc9a01.color565(255,165,0),
         gc9a01.color565(255,215,0), gc9a01.color565(255,160,122),
         gc9a01.color565(255,105,180)],
    16: [gc9a01.color565(255,182,193), gc9a01.color565(255,192,203),
         gc9a01.color565(221,160,221), gc9a01.color565(216,191,216),
         gc9a01.color565(240,230,140), gc9a01.color565(255,228,196),
         gc9a01.color565(255,250,205)],
    17: [gc9a01.color565(0,128,128), gc9a01.color565(72,209,204),
         gc9a01.color565(95,158,160), gc9a01.color565(32,178,170),
         gc9a01.color565(0,206,209), gc9a01.color565(64,224,208),
         gc9a01.color565(0,255,255)],
    18: [gc9a01.color565(255,160,122), gc9a01.color565(255,127,80),
         gc9a01.color565(255,99,71), gc9a01.color565(255,69,0),
         gc9a01.color565(255,140,0), gc9a01.color565(255,165,0),
         gc9a01.color565(255,215,0)],
    19: [gc9a01.color565(57,255,20), gc9a01.color565(0,255,255),
         gc9a01.color565(255,20,147), gc9a01.color565(255,105,180),
         gc9a01.color565(138,43,226), gc9a01.color565(0,255,0),
         gc9a01.color565(255,0,255)],
    20: [gc9a01.color565(105,105,105), gc9a01.color565(169,169,169),
         gc9a01.color565(192,192,192), gc9a01.color565(128,128,128),
         gc9a01.color565(112,128,144), gc9a01.color565(119,136,153),
         gc9a01.color565(47,79,79)],
    21: [gc9a01.color565(65,105,225), gc9a01.color565(72,61,139),
         gc9a01.color565(106,90,205), gc9a01.color565(123,104,238),
         gc9a01.color565(0,0,205), gc9a01.color565(25,25,112),
         gc9a01.color565(70,130,180)],
    22: [gc9a01.color565(199,21,133), gc9a01.color565(218,112,214),
         gc9a01.color565(219,112,147), gc9a01.color565(255,20,147),
         gc9a01.color565(255,105,180), gc9a01.color565(255,182,193),
         gc9a01.color565(255,192,203)],
    23: [gc9a01.color565(210,105,30), gc9a01.color565(244,164,96),
         gc9a01.color565(222,184,135), gc9a01.color565(205,133,63),
         gc9a01.color565(160,82,45), gc9a01.color565(139,69,19),
         gc9a01.color565(128,0,0)],
    24: [gc9a01.color565(255,192,203), gc9a01.color565(255,182,193),
         gc9a01.color565(216,191,216), gc9a01.color565(221,160,221),
         gc9a01.color565(238,130,238), gc9a01.color565(230,230,250),
         gc9a01.color565(255,240,245)],
    25: [gc9a01.color565(0,255,0), gc9a01.color565(0,255,255),
         gc9a01.color565(255,0,255), gc9a01.color565(255,255,0),
         gc9a01.color565(255,69,0), gc9a01.color565(255,20,147),
         gc9a01.color565(0,191,255)]
}