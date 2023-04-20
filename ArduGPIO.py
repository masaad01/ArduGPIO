import asyncio
import threading

import time
import atexit

from telemetrix_aio import telemetrix_aio

from ArduGPIOTypes import *
from ArduPin import Pin

    
    
# variables for the telemetrix loop
__board: telemetrix_aio.TelemetrixAIO = None
__loop: asyncio.AbstractEventLoop = None
__loop_tasks: list[asyncio.Task] = []

__loop_thread: threading.Thread = None
__loop_condition = threading.Condition()

# variables for the state of the pins

__mode = None
__active_pins: list[Pin] = []



def __telemetrix_loop():
    """_summary_: This function is run in a separate thread to run the asyncio event loop.
    It is responsible for the asynchronous communication with the Telemetrix board.
    It is run in a separate thread so that the main thread can be used to run
     the RPi.GPIO functions.
    """
    global __loop
    global __loop_condition
    global __board
    with __loop_condition:
        __loop = asyncio.new_event_loop()
        asyncio.set_event_loop(__loop)
        __board = telemetrix_aio.TelemetrixAIO()
        __loop_condition.notify()
    __loop.run_forever()

def __start_loop():
    """_summary_: This function starts the telemetrix loop in a separate thread.
    """
    global __loop
    global __loop_thread
    global __loop_condition
    if __loop_thread is None:
        __loop_thread = threading.Thread(target=__telemetrix_loop, daemon=True)
        __loop_thread.start()
        with __loop_condition:
            while __loop is None:
                __loop_condition.wait()
        __loop.create_task(__board.disable_all_reporting())

def __shutdown():
    """_summary_: This function is called when the program is terminated.
    It calls the shutdown function to stop the telemetrix loop gracefully, and then exits the program.
    """
    print("Telemetrix Shutting down.")
    
    tasks = asyncio.all_tasks(__loop)
    for task in tasks:
        task.cancel()
    
    if __loop is not None:
        __loop.stop()
        while __loop.is_running():
            time.sleep(0.1)
    if __board is not None:
        __loop.run_until_complete(__board.shutdown())
        __loop_thread.join()
        __loop.close()

# Define ArduGPIO pin setup functions

async def __setup_pin_analog_in(pin: Pin):
    """_summary_: This function is called to set up an analog input pin.
    It is run in a separate task in the telemetrix asyncio event loop.
    
    Args:
        pin: The pin to set up; must be instance of Pin class.
    """
    global __board
    sleep_time = 0.001 # what does changing this do?
    await __board.set_pin_mode_analog_input(pin.channel, pin.update_threshold, pin.update)
    await __board.enable_analog_reporting(pin.channel)
    # keep the task alive until cancelled
    try:
        while True:
            await asyncio.sleep(sleep_time)
    except asyncio.CancelledError or Exception:
        pass

async def __setup_pin_digital_in(pin: Pin):
    """_summary_: This function is called to set up a digital input pin.

    Args:
        pin (Pin): The pin to set up; must be instance of Pin class.

    Raises:
        NotImplementedError: Pull down resistors are not supported by arduino
        ValueError: Invalid pull up/down value
    """
    global __board
    sleep_time = 0.001 # what does changing this do?
    
    if pin.pull_up_down == PUD_OFF:
        await __board.set_pin_mode_digital_input(pin.channel, pin.update)
        await __board.enable_digital_reporting(pin.channel)
    elif pin.pull_up_down == PUD_UP:
        await __board.set_pin_mode_digital_input_pullup(pin.channel, pin.update)
        await __board.enable_digital_reporting(pin.channel)
    elif pin.pull_up_down == PUD_DOWN:
        raise NotImplementedError("Pull down resistors are not supported")
    else:
        raise ValueError("Invalid pull up/down value")
    
    try:
        while True:
            await asyncio.sleep(sleep_time)
    except asyncio.CancelledError or Exception:
        pass

async def __setup_pin_analog_out(pin: Pin):
    """_summary_: This function is called to set up an analog output pin.

    Args:
        pin (Pin): The pin to set up; must be instance of Pin class.
    """
    global __board
    await __board.set_pin_mode_analog_output(pin.channel)
    
async def __setup_pin_digital_out(pin: Pin):
    """_summary_: This function is called to set up a digital output pin.
    
    Args:
        pin (Pin): The pin to set up; must be instance of Pin class.
    """
    global __board
    if pin.pull_up_down == PUD_OFF:
        await __board.set_pin_mode_digital_output(pin.channel)
    else :
        raise NotImplementedError("Pull up/down resistors are not supported for digital outputs")

# Define pin getter functions

def active_pins() -> tuple[int]:
    """_summary_: This function returns a tuple of the channels of all active pins.

    Returns:
        tuple[int]: A tuple of the channels of all active pins.
    """
    global __active_pins
    return tuple(pin.channel for pin in __active_pins)


def get_pin(channel: int) -> Pin:
    """_summary_: This function returns the pin with the given channel.

    Args:
        channel (int): The channel number of the pin to return.

    Raises:
        ValueError: Pin not active; no pin with the given channel was set up.

    Returns:
        Pin: The pin with the given channel number.
    """
    global __active_pins
    for pin in __active_pins:
        if pin.channel == channel:
            return pin
    raise ValueError("Pin not active")

# Define RPi.GPIO compatable functions as empty methods


def setmode(mode):
    """_summary_: This function sets the pin numbering mode.

    Args:
        mode (BOARD or BCM): The pin numbering mode to use (BOARD or BCM).
    """
    global __mode
    __mode = mode


def getmode():
    """_summary_: This function returns the current pin numbering mode.

    Returns:
        (BOARD or BCM): The current pin numbering mode (BOARD or BCM
    """
    global __mode
    return __mode


def setup(channel: int, direction, pull_up_down = PUD_OFF):
    """_summary_: This function sets up a pin for use.

    Args:
        channel (int): The channel number of the pin to set up.
        direction (IN or OUT): The direction of the pin to set up.
        pull_up_down (PUD_OFF, PUD_UP, or PUD_DOWN, optional): The pull up/down resistor mode to use. Defaults to PUD_OFF.

    Raises:
        RuntimeError: Pin numbering mode not set
        RuntimeError: Pin already in use; the pin has already been set up.
        ValueError: Invalid direction value; the direction value is not IN or OUT.
    """
    global __mode
    global __active_pins
    global __loop_tasks
    
    if __mode is None:
        raise RuntimeError("Please set pin numbering mode using GPIO.setmode(GPIO.BOARD) or GPIO.setmode(GPIO.BCM)")
    if channel in active_pins():
        raise RuntimeError("Pin already in use")
    
    pin = Pin(type=DIGITAL, channel=channel, direction=direction, pull_up_down=pull_up_down)
    __active_pins.append(pin)
    
    if direction == IN:
        task = __loop.create_task(__setup_pin_digital_in(pin))
        pin.set_async_task(task)
    elif direction == OUT:
        task = __loop.create_task(__setup_pin_digital_out(pin))
        pin.set_async_task(task)
    else:
        raise ValueError("Invalid direction value")


def input(channel: int):
    """_summary_: This function returns the value of a digital input pin.

    Args:
        channel (int): The channel number of the pin to read.

    Raises:
        ValueError: Pin is not an input; the pin is not set up as an input.

    Returns:
        (0 or 1): The value of the pin.
    """
    pin = get_pin(channel)
    if pin.direction != IN:
        raise ValueError("Pin is not an input")
    return pin.value


def output(channel: int, state):
    """_summary_: This function sets the value of a digital output pin.

    Args:
        channel (int): The channel number of the pin to set.
        state (0 or 1): The value to set the pin to.

    Raises:
        NotImplementedError: Invalid pin type; for analog output pins use PWM.
        ValueError: Invalid pin direction; You cannot set the value of an input pin.
        ValueError: Invalid pin type and/or direction; the pin is not set up as a digital output pin.
    """
    global __loop
    global __loop_tasks
    global __board
    
    pin = get_pin(channel)
    pin.value = state
    if pin.type == DIGITAL and pin.direction == OUT:
        __loop_tasks.append(__loop.create_task(__board.digital_write(pin.channel, pin.value)))
    elif pin.type == ANALOG:
        raise NotImplementedError("Invalid pin type; for analog output pins use PWM")
    elif pin.direction == IN:
        raise ValueError("Invalid pin direction; You cannot set the value of an input pin")
    else:
        raise ValueError("Invalid pin type and/or direction")


def cleanup(channel=None):
    """_summary_: This function cleans up a pin by removing it from the list of active pins.

    Args:
        channel (int, optional): The channel number of the pin to clean up. Defaults to None.
    """
    global __active_pins
    if channel is None:
        __loop.create_task(__board.disable_all_reporting())
        for pin in __active_pins:
            pin.cancel_async_task()
        
        __active_pins = []
    else:
        pin = get_pin(channel)
                
        if pin.direction == IN:
            if pin.type == DIGITAL:
                __loop.create_task(__board.disable_digital_reporting(pin.channel))
            elif pin.type == ANALOG:
                __loop.create_task(__board.disable_analog_reporting(pin.channel))
                
        pin.cancel_async_task()
        __active_pins.remove(pin)


def setwarnings(flag):
    raise NotImplementedError("Mock method: setwarnings")


def gpio_function(channel):
    raise NotImplementedError("Mock method: gpio_function")


def add_event_callback(channel, callback):
    raise NotImplementedError("Mock method: add_event_callback")


def add_event_detect(channel, edge, callback=None, bouncetime=None):
    raise NotImplementedError("Mock method: add_event_detect")


def event_detected(channel):
    raise NotImplementedError("Mock method: event_detected")


def remove_event_detect(channel):
    raise NotImplementedError("Mock method: remove_event_detect")


def wait_for_edge(channel, edge):
    raise NotImplementedError("Mock method: wait_for_edge")


# start the loop thread and register the shutdown function
if __name__ != "__main__":
    __start_loop()
    atexit.register(__shutdown)

