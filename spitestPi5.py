import spidev
import gpiod
import time
import sys

# Open the GPIO chip
chip = gpiod.Chip('gpiochip0')

# Define GPIO lines
FPAA_RESET_B = chip.get_line(26)  # Output, drive high to enable FPAA
FPAA_CFGFLG_B = chip.get_line(23)  # Input, configuration status flag
FPAA_ACTIVATE = chip.get_line(24)  # Input, pulled low by FPAA until configuration has been loaded
FPAA_ERR_B = chip.get_line(25)  # Input, driven low if configuration error detected
FPAA_ACLK_REF = chip.get_line(4)  # Output (set up as GPCLK0 if used)
FPAA_LCL_ACLK_EN = chip.get_line(14)  # Output, enables oscillator on Pi.Ka board
FPAA_ACLK_SEL0 = chip.get_line(5)  # Output, LSB of ACLK source selector
FPAA_ACLK_SEL1 = chip.get_line(6)  # Output, MSB of ACLK source selector
#FPAA_CE0 = chip.get_line(8)  # Output, active low chip select common to all FPAAs

# Request lines
FPAA_RESET_B.request(consumer='FPAA', type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
FPAA_CFGFLG_B.request(consumer='FPAA', type=gpiod.LINE_REQ_DIR_IN)
FPAA_ACTIVATE.request(consumer='FPAA', type=gpiod.LINE_REQ_DIR_IN)
FPAA_ERR_B.request(consumer='FPAA', type=gpiod.LINE_REQ_DIR_IN)
#FPAA_CE0.request(consumer='FPAA', type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
FPAA_LCL_ACLK_EN.request(consumer='FPAA', type=gpiod.LINE_REQ_DIR_OUT)
FPAA_ACLK_SEL0.request(consumer='FPAA', type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
FPAA_ACLK_SEL1.request(consumer='FPAA', type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

# SPI setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.mode = 0b00
spi.no_cs = False  # Control CE0 as GPIO to prevent toggling between SPI transfers
spi.lsbfirst = False
spi.bits_per_word = 8
spi.max_speed_hz = 32000000

# Reset and configure FPAA
FPAA_RESET_B.set_value(0)  # Start with reset low to force reconfiguration
FPAA_LCL_ACLK_EN.set_value(1)  # Enable 16MHz oscillator on Pi.Ka
FPAA_ACLK_SEL0.set_value(0)  # Configure Pi.Ka to use the internal oscillator
FPAA_ACLK_SEL1.set_value(0)  # Configure Pi.Ka to use the internal oscillator
#FPAA_CE0.set_value(0)  # Permanently drive chip select low

time.sleep(0.02)  # Hold reset low for 20ms
FPAA_RESET_B.set_value(1)  # Release reset
time.sleep(0.1)  # Hold reset high for 100ms

# Send one byte of 0s and check ERR_B state
zero_list = [0]
spi.xfer2(zero_list)

if FPAA_ERR_B.get_value() == 0:
    print("ERR_B still low. Check connections and ACLK")

print("Press Enter to continue: ")
waiting = True
while waiting:
    sys.stdin.read(1)
    print("\nContinuing")
    waiting = False

DEBUG = True
def debug_print(printstring):
    if DEBUG:
        print(printstring)

ahf_file_name = "4osc.ahf"
primary_config_list = []  # Create empty list for config bytes

with open(ahf_file_name, "r") as f:
    lines = f.readlines()

for line in lines:
    line = line.strip()  # Strip out newline character
    primary_config_list.append(int(line, base=16))  # Interpret each line as a hex integer

debug_print("file read complete")
debug_print(primary_config_list)

spi.xfer2(primary_config_list)  # xfer2 holds chip select between bytes

# Simple command-line solution for holding the last state until the user decides to exit
print("Press Enter to exit: ")
running = True
while running:
    sys.stdin.read(1)
    print("\nExiting")
    running = False

# Clean up before exiting
spi.close()

# Release the GPIO lines
FPAA_RESET_B.release()
FPAA_CFGFLG_B.release()
FPAA_ACTIVATE.release()
FPAA_ERR_B.release()
#FPAA_CE0.release()
FPAA_LCL_ACLK_EN.release()
FPAA_ACLK_SEL0.release()
FPAA_ACLK_SEL1.release()
