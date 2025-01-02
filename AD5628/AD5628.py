import struct
from micropython import const
from adafruit_bus_device.spi_device import SPIDevice
import time



MAX_CHANNELS = 8

# Command Definitions
CMD_WRITE_INPUT_REGISTER = const(0x00)  # Write to Input Register n
CMD_UPDATE_DAC = const(0x01)  # Update DAC Register n
CMD_WRITE_INPUT_UPDATE_ALL = const(0x02)  # Write to Input Register n, update all (software LDAC)
CMD_WRITE_AND_UPDATE_DAC = const(0x03)  # Write to and update DAC Channel n
CMD_POWER_DOWN = const(0x04)  # Power down/power up DAC
CMD_LOAD_CLEAR_CODE = const(0x05)  # Load clear code register
CMD_LOAD_LDAC = const(0x06)  # Load LDAC register
CMD_RESET = const(0x07)  # Reset (power-on reset)
CMD_SETUP_INT_REF_REG = const(0x08)  # Set up internal reference register

# DAC Channel Addresses (A3, A2, A1, A0)
DAC_CHANNEL_A = 0x00  # Channel A
DAC_CHANNEL_B = 0x01  # Channel B
DAC_CHANNEL_C = 0x02  # Channel C
DAC_CHANNEL_D = 0x03  # Channel D
DAC_CHANNEL_E = 0x04  # Channel E
DAC_CHANNEL_F = 0x05  # Channel F
DAC_CHANNEL_G = 0x06  # Channel G
DAC_CHANNEL_H = 0x07  # Channel H
DAC_ALL_CHANNELS = 0x0F  # All DAC channels

# LDAC Modes
LDAC_MODE = {
    'HW': 0x00,  # Hardware control of LDAC
    'SW': 0x01   # Software control of LDAC
}

# Internal Reference Modes
IREF_MODE = {
    'ON': 0x01,  # Internal Reference On
    'OFF': 0x00  # Internal Reference Off
}



try:
    import typing  # pylint: disable=unused-import
    from digitalio import DigitalInOut
    from busio import SPI
except ImportError:
    pass


class AD5628:

    def __init__(
        self, spi: SPI, cs: DigitalInOut  # pylint: disable=invalid-name
    ) -> None:
        self.spi_device = SPIDevice(spi, cs, baudrate=50000000, polarity=0, phase=1)

    def send_data(self, value):
        """Write a 32-bit value to the DAC via SPI."""
        buffer = value.to_bytes(4, 'big')  # Convert to 4-byte big-endian
        with self.spi_device as device:
            device.write(buffer)
            #print(buffer)

    def write_register(self, channel, data):
        """Writes data to a register)."""
        command = (CMD_WRITE_INPUT_REGISTER<< 24) | (channel << 20) | (data & 0xFFFFF)
        self.send_data(command)

    def update_dac(self, channel, data):
        """Writes data to a DAC channel."""
        if channel >= MAX_CHANNELS and channel != DAC_ALL_CHANNELS:
            raise ValueError("Invalid channel")

        # Create a 32-bit register write command
        command = (CMD_UPDATE_DAC << 24) | (channel << 20) | (data << 8)
        self.send_data(command)

    def write_update_dac(self, channel, data):
        """Writes data to a DAC channel."""
        if channel >= MAX_CHANNELS and channel != DAC_ALL_CHANNELS:
            raise ValueError("Invalid channel")

        # Create a 32-bit register write command
        command = (CMD_WRITE_AND_UPDATE_DAC << 24) | (channel << 20) | (data << 8)
        self.send_data(command)

    def tester(self):
        command = (0x03 << 24) | (0x00 << 20) | (0xFFF << 8)
        self.send_data(command)

    def power_down(self):
        """Powers down a specific DAC channel."""
        command = (CMD_POWER_DOWN << 24) 
        self.send_data(command)

    def load_clear_code(self, code):
        """Loads the clear code register."""
        if code not in [0x00, 0x80000, 0xFFFFF]:
            raise ValueError("Invalid clear code, must be 0 (zero), midscale, or fullscale")

        command = (CMD_LOAD_CLEAR_CODE << 24) | (code & 0xFFFFF)
        self.send_data(command)

    def load_ldac(self, channel):
        """Configures the LDAC mode for specific channels."""
        if channel >= MAX_CHANNELS and channel != DAC_ALL_CHANNELS:
            raise ValueError("Invalid channel")

        ldac_value = (0x01 << channel) & 0xFF
        command = (CMD_LOAD_LDAC << 24) | (ldac_value << 8)
        self.send_data(command)

    def update_ldac(self, channel, data):
        """Write to and update DAC Channel n"""
        command = (CMD_WRITE_INPUT_UPDATE_ALL << 24) | (channel << 20) | (data << 8)
        self.send_data(command)

    def reset(self):
        """Resets the DAC to power-on defaults."""
        command = CMD_RESET << 24
        self.send_data(command)

    def internal_ref_mode(self):
        """Sets the internal reference mode."""
        command = (0x08 << 24) | (0x01 << 8)
        self.send_data(command)

