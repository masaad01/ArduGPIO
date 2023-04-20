from asyncio import Task
import time
from typing import Iterable, Callable

from ArduGPIOTypes import *

class Pin:
    __old_value: int = None
    __old_timestamp: float = None
    __value: int = None
    __timestamp: float = None
    __async_task: Task = None
    
    def __init__(self, type, channel: int, direction, update_threshold: int = 5, callback: Callable[[any], any] = None, pull_up_down = PUD_OFF, value: int = None):
        self.__type = type
        self.__channel = channel
        self.__direction = direction
        
        if direction == IN and value is not None:
            raise ValueError("Cannot set value value for input pin")
        elif direction == OUT:
            if value is None:
                value = 0
            self.__value = value
        
        self.__pull_up_down = pull_up_down
        self.__callback = callback
        self.__update_threshold = update_threshold
    
    async def update(self, data: list[int, int, int, int]):
        #[pin_type, pin_number, pin_value, raw_time_stamp]
        self.__old_value = self.__value
        self.__old_timestamp = self.__timestamp
        self.__value = data[2]
        self.__timestamp = data[3]
        if self.__callback is not None:
            self.__callback(self)
    
    def set_async_task(self, task: Task):
        if self.__direction == IN:
            self.__async_task = task
        else:
            raise ValueError("Cannot set async task for output pin; this is needed for input pins receiving data from the Arduino")
    
    def cancel_async_task(self):
        if self.__async_task is not None:
            if not (self.__async_task.done() or self.__async_task.cancelled()):
                self.__async_task.cancel()
    
    # define getters
    @property
    def type(self):
        return self.__type
    
    @property
    def channel(self) -> int:
        return self.__channel
    
    @property
    def direction(self):
        return self.__direction
    
    @property
    def value(self) -> int:
        return self.__value
    
    @property
    def timestamp(self) -> int:
        return self.__timestamp
    
    @property
    def rate_of_change(self) -> float:
        if self.__old_value is None or self.__old_timestamp is None:
            return 0
        return (self.__value - self.__old_value) / (self.__timestamp - self.__old_timestamp)
    
    @property
    def update_threshold(self) -> int:
        return self.__update_threshold
    
    @property
    def pull_up_down(self):
        return self.__pull_up_down

    @property
    def callback(self) -> Callable[[any], any]:
        return self.__callback
    
    # define setters
    @callback.setter
    def callback(self, callback: Callable[[any], any]):
        self.__callback = callback
    
    @value.setter
    def value(self, value: int) -> None:
        if self.__direction == IN:
            raise ValueError("Cannot set value of input pin")
        
        if self.__type == ANALOG:
            if value > 255 or value < 0:
                raise ValueError("Value for analog output (PWM) must be between 0 and 255")
        elif self.__type == DIGITAL:
            if value not in [0, 1, LOW, HIGH]:
                raise ValueError("Value for digital output must be 0 or 1 (or LOW or HIGH))")
        
        # if no errors, set value
        self.__old_value = self.__value
        self.__old_timestamp = self.__timestamp
        self.__value = value
        self.__timestamp = time.time()

    def __dir__(self) -> Iterable[str]:
        return ["type", "channel", "direction", "value", "timestamp", "rate_of_change", "update_threshold", "pull_up_down"]
    def __str__(self):
        return f"Pin(channel={self.__channel}, direction={self.__direction}, value={self.__value}, timestamp={self.__timestamp}, rate_of_change={self.rate_of_change})"
