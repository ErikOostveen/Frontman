"""Generic 240x240 GC9A01

Generic displays connected to a Raspberry Pi Pico.
This module supports configuration of two displays on a shared SPI bus.
Optimized for improved refresh rate by increasing the SPI baudrate.
"""

from machine import Pin, SPI
import gc9a01

# ----------------------------------------------------------------------
# Shared SPI hardware configuration.
SCL_PIN = 14  # Chip pin 20 
SDA_PIN = 15  # Chip pin 19

# ----------------------------------------------------------------------
# Hardware configuration for the first display.
DC_PIN1  = 4   # Chip pin 6 
CS_PIN1  = 5   # Chip pin 7 
RST_PIN1 = 6   # Chip pin 9 

# Hardware configuration for the second display.
# Adjust these pins to available GPIOs on your Pico.
DC_PIN2  = 8  
CS_PIN2  = 9  
RST_PIN2 = 10  

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
# Create the Pin objects for Display 1.
_reset1 = Pin(RST_PIN1, Pin.OUT)
_cs1    = Pin(CS_PIN1, Pin.OUT)
_dc1    = Pin(DC_PIN1, Pin.OUT)

# Create the Pin objects for Display 2.
_reset2 = Pin(RST_PIN2, Pin.OUT)
_cs2    = Pin(CS_PIN2, Pin.OUT)
_dc2    = Pin(DC_PIN2, Pin.OUT)

# ----------------------------------------------------------------------
def config1(rotation=0, buffer_size=0, options=0):
    """
    Configure the first display and return an instance of gc9a01.GC9A01.
    """
    return gc9a01.GC9A01(
        spi,
        240,
        240,
        reset=_reset1,
        cs=_cs1,
        dc=_dc1,
        rotation=rotation,
        options=options,
        buffer_size=buffer_size,
    )

def config2(rotation=0, buffer_size=0, options=0):
    """
    Configure the second display and return an instance of gc9a01.GC9A01.
    """
    return gc9a01.GC9A01(
        spi,
        240,
        240,
        reset=_reset2,
        cs=_cs2,
        dc=_dc2,
        rotation=rotation,
        options=options,
        buffer_size=buffer_size,
    )


# ----- DEFINE 25 COLOR SCHEMES (Sclera always black) -----
# Each scheme defines colors for iris outer, iris inner, pupil, and highlight.
color_schemes = [
    {   # 1. Golden Eagle (default)
        "iris_outer": gc9a01.color565(255, 215, 0),
        "iris_inner": gc9a01.color565(80, 40, 0),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 255, 255),
    },
    {   # 2. Blue
        "iris_outer": gc9a01.color565(0, 0, 255),
        "iris_inner": gc9a01.color565(100, 149, 237),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(173, 216, 230),
    },
    {   # 3. Green
        "iris_outer": gc9a01.color565(0, 255, 0),
        "iris_inner": gc9a01.color565(34, 139, 34),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(144, 238, 144),
    },
    {   # 4. Red
        "iris_outer": gc9a01.color565(255, 0, 0),
        "iris_inner": gc9a01.color565(178, 34, 34),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 160, 122),
    },
    {   # 5. Purple
        "iris_outer": gc9a01.color565(128, 0, 128),
        "iris_inner": gc9a01.color565(147, 112, 219),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(216, 191, 216),
    },
    {   # 6. Cyan
        "iris_outer": gc9a01.color565(0, 255, 255),
        "iris_inner": gc9a01.color565(0, 206, 209),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(224, 255, 255),
    },
    {   # 7. Orange
        "iris_outer": gc9a01.color565(255, 165, 0),
        "iris_inner": gc9a01.color565(255, 140, 0),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 228, 181),
    },
    {   # 8. Pink
        "iris_outer": gc9a01.color565(255, 105, 180),
        "iris_inner": gc9a01.color565(219, 112, 147),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 182, 193),
    },
    {   # 9. Yellow
        "iris_outer": gc9a01.color565(255, 255, 0),
        "iris_inner": gc9a01.color565(238, 232, 170),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 250, 205),
    },
    {   # 10. Magenta
        "iris_outer": gc9a01.color565(255, 0, 255),
        "iris_inner": gc9a01.color565(218, 112, 214),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 192, 203),
    },
    {   # 11. Brown
        "iris_outer": gc9a01.color565(139, 69, 19),
        "iris_inner": gc9a01.color565(160, 82, 45),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(210, 180, 140),
    },
    {   # 12. Grey Scale
        "iris_outer": gc9a01.color565(192, 192, 192),
        "iris_inner": gc9a01.color565(128, 128, 128),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 255, 255),
    },
    {   # 13. Teal
        "iris_outer": gc9a01.color565(0, 128, 128),
        "iris_inner": gc9a01.color565(32, 178, 170),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(175, 238, 238),
    },
    {   # 14. Lavender
        "iris_outer": gc9a01.color565(230, 230, 250),
        "iris_inner": gc9a01.color565(216, 191, 216),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 240, 245),
    },
    {   # 15. Olive
        "iris_outer": gc9a01.color565(128, 128, 0),
        "iris_inner": gc9a01.color565(107, 142, 35),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(189, 183, 107),
    },
    {   # 16. Maroon
        "iris_outer": gc9a01.color565(128, 0, 0),
        "iris_inner": gc9a01.color565(165, 42, 42),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(205, 92, 92),
    },
    {   # 17. Coral
        "iris_outer": gc9a01.color565(255, 127, 80),
        "iris_inner": gc9a01.color565(240, 128, 128),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 160, 122),
    },
    {   # 18. Turquoise
        "iris_outer": gc9a01.color565(64, 224, 208),
        "iris_inner": gc9a01.color565(72, 209, 204),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(175, 238, 238),
    },
    {   # 19. Indigo
        "iris_outer": gc9a01.color565(75, 0, 130),
        "iris_inner": gc9a01.color565(138, 43, 226),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(216, 191, 216),
    },
    {   # 20. Deep Pink
        "iris_outer": gc9a01.color565(255, 20, 147),
        "iris_inner": gc9a01.color565(219, 112, 147),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 182, 193),
    },
    {   # 21. Gold
        "iris_outer": gc9a01.color565(255, 215, 0),
        "iris_inner": gc9a01.color565(218, 165, 32),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 250, 205),
    },
    {   # 22. Crimson
        "iris_outer": gc9a01.color565(220, 20, 60),
        "iris_inner": gc9a01.color565(178, 34, 34),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 192, 203),
    },
    {   # 23. Khaki
        "iris_outer": gc9a01.color565(240, 230, 140),
        "iris_inner": gc9a01.color565(189, 183, 107),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(255, 255, 224),
    },
    {   # 24. Peru
        "iris_outer": gc9a01.color565(205, 133, 63),
        "iris_inner": gc9a01.color565(210, 105, 30),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(244, 164, 96),
    },
    {   # 25. Steel Blue
        "iris_outer": gc9a01.color565(70, 130, 180),
        "iris_inner": gc9a01.color565(100, 149, 237),
        "pupil":      gc9a01.color565(0, 0, 0),
        "highlight":  gc9a01.color565(176, 196, 222),
    },
]
