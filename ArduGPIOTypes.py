
# Pin numbering modes
BCM = "bcm"  # Broadcom SOC channel numbering
BOARD = "board"  # Pin numbering according to the board layout

# Pin directions
OUT = "out"  # Output
IN = "in"  # Input

# Pin states
HIGH = 1  # High state (3.3V)
LOW = 0  # Low state (0V)

# Edge detection types
RISING = "rising"  # Detect rising edges
FALLING = "falling"  # Detect falling edges
BOTH = "both"  # Detect both rising and falling edges

# Pin pull-up/down resistor types
PUD_DOWN = "pud_down"  # Pull-down resistor
PUD_OFF = "pud_off"  # No pull-up/down resistor
PUD_UP = "pud_up"  # Pull-up resistor

# Hardware interface types
PWM = "pwm"  # Pulse Width Modulation interface
HARD_PWM = "hard_pwm"  # Hardware Pulse Width Modulation interface
I2C = "i2c"  # I2C interface
SPI = "spi"  # SPI interface
SERIAL = "serial"  # Serial interface
UNKNOWN = "unknown"  # Unknown interface

# Additional interface types
DIGITAL = "digital"  # Digital interface type
ANALOG = "analog"  # Analog interface type
SERVO = "servo"  # Servo interface type

VERSION = "0.0.1"



class BoardPinsScheme:
    DIGITAL_READ: list[int] = []
    DIGITAL_WRITE: list[int] = []
    ANALOG_READ: list[int] = []
    ANALOG_WRITE: list[int] = []
    
    def __init__(self, digital_read: list[int], digital_write: list[int], analog_read: list[int], analog_write: list[int], mode = BCM):
        self.DIGITAL_READ = digital_read
        self.DIGITAL_WRITE = digital_write
        self.ANALOG_READ = analog_read
        self.ANALOG_WRITE = analog_write
        self.mode = mode
        
    def __str__(self):
        return f"BoardPinsScheme(digital_read={self.DIGITAL_READ}, digital_write={self.DIGITAL_WRITE}, analog_read={self.ANALOG_READ}, analog_write={self.ANALOG_WRITE})"
    
    def check_pin(self, pin: int, pin_type, direction):
        if self.mode == BCM:
            pin = self.board_to_bcm(pin)
        if pin_type == DIGITAL:
            if direction == IN:
                if pin not in self.DIGITAL_READ:
                    raise ValueError(f"Pin {pin} is not a valid digital read pin. Valid pins are {self.DIGITAL_READ}")
            elif direction == OUT:
                if pin not in self.DIGITAL_WRITE:
                    raise ValueError(f"Pin {pin} is not a valid digital write pin. Valid pins are {self.DIGITAL_WRITE}")
        elif pin_type == ANALOG:
            if direction == IN:
                if pin not in self.ANALOG_READ:
                    raise ValueError(f"Pin {pin} is not a valid analog read pin. Valid pins are {self.ANALOG_READ}")
            elif direction == OUT:
                if pin not in self.ANALOG_WRITE:
                    raise ValueError(f"Pin {pin} is not a valid analog write pin. Valid pins are {self.ANALOG_WRITE}")
        else:
            raise ValueError(f"Pin {pin} is not a valid pin for type {pin_type}")

    def board_to_bcm(self, pin: int) -> int:
        # for Pi 4 Model B, Pi 3 Model B+, Pi 3 Model B, Pi 3 Model A+, 
        # and Pi 2 Model B, Pi Model B+, Pi Model A+, Pi Zero, Pi Zero W
        pin_dict = {
    3: '2',
    5: '3',
    7: '4',
    8: '14',
    10: '15',
    11: '17',
    12: '18',
    13: '27',
    15: '22',
    16: '23',
    18: '24',
    19: '10',
    21: '9',
    22: '25',
    23: '11',
    24: '8',
    26: '7',
    29: '5',
    31: '6',
    32: '12',
    33: '13',
    35: '19',
    36: '16',
    37: '26',
    38: '20',
    40: '21'
}

        return pin_dict[pin]

ArudinoUnoPins = BoardPinsScheme(
    # digital pins 14 to 19 are the analog pins (A0 to A5). They can be used as digital pins
    digital_read=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19], 
    digital_write=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
    analog_read=[0, 1, 2, 3, 4, 5],
    analog_write=[3, 5, 6, 9, 10, 11]
)