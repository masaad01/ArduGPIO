from time import sleep
import ArduGPIO as GPIO
import time


GPIO.setmode(GPIO.BCM)

GPIO.setup(13, GPIO.OUT)
GPIO.setup(1, GPIO.IN)


for i in range(2):
    print(GPIO.input(1))
    GPIO.output(13, GPIO.HIGH)
    print("ON")
    time.sleep(0.5)
    GPIO.output(13, GPIO.LOW)
    print("OFF")
    time.sleep(0.5)


GPIO.cleanup()

print("DONE")
