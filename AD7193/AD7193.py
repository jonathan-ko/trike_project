import board
import busio
from digitalio import DigitalInOut
from adafruit_bus_device.spi_device import SPIDevice
import time

class AD7193:
    # Register Map
    COMMUNICATIONS_REGISTER = 0x00
    STATUS_REGISTER = 0x00
    MODE_REGISTER = 0x01
    CONFIGURATION_REGISTER = 0x02
    DATA_REGISTER = 0x03

    # SPI Settings
    SPI_MODE = 3  # CPOL = 1, CPHA = 1
    SPI_BAUDRATE = 1000000  # 1 MHz (adjustable up to 10 MHz max)
    MAX_SCLK_PERIOD_NS = 100  # Max SCLK period for proper operation

    def __init__(self, spi, cs_pin):
        self.cs = DigitalInOut(cs_pin)
        self.cs.switch_to_output(value=True)  # CS high initially
        self.spi_device = SPIDevice(spi, self.cs, baudrate=self.SPI_BAUDRATE, polarity=1, phase=1)

    def reset(self):
        """Performs a reset on the AD7193."""
        reset_command = bytes([0xFF] * 5)  # 40 consecutive 1 bits
        with self.spi_device as spi:
            spi.write(reset_command)
        time.sleep(0.01)  # Allow time for the device to reset
        print("ADC reset complete.")

    def read_device_id(self):
        """Reads the ID register to verify communication."""
        device_id = int.from_bytes(self.read_register(0x04, 1), 'big')
        print(f"Device ID: {device_id:#04X}")
        return device_id

    def write_register(self, register, value):
        """Writes to a register."""
        command = (register << 3) & 0xF8  # Write operation
        data = bytes([command]) + value
        with self.spi_device as spi:
            spi.write(data)

    def read_register(self, register, length):
        """Reads from a register."""
        command = ((register << 3) | 0x40) & 0xFF  # Read operation
        buffer = bytearray(length)
        with self.spi_device as spi:
            spi.write(bytes([command]))
            spi.readinto(buffer)
        return buffer

    def initialize(self):
        """Initializes the ADC."""
        # Example: Set continuous conversion mode
        mode_value = 0x080060  # Continuous conversion, default settings
        self.write_register(self.MODE_REGISTER, mode_value.to_bytes(3, 'big'))

        # Example: Set gain, unipolar/bipolar, and channel
        config_value = 0x000117  # Gain = 1, bipolar mode, channel 0
        self.write_register(self.CONFIGURATION_REGISTER, config_value.to_bytes(3, 'big'))

    def read_data(self):
        """Reads data from the data register."""
        data = self.read_register(self.DATA_REGISTER, 3)
        # Convert the 3-byte response to an integer
        return int.from_bytes(data, 'big')

    def data_ready(self):
        """Checks if data is ready using the status register."""
        status = self.read_register(self.STATUS_REGISTER, 1)[0]
        return not (status & 0x80)  # RDY bit is 0 when data is ready

    def wait_for_data_ready(self, timeout=1.0):
        """Waits for data to be ready or times out."""
        start = time.monotonic()
        while not self.data_ready():
            if (time.monotonic() - start) > timeout:
                raise TimeoutError("Timeout waiting for data ready")
            time.sleep(0.001)  # Poll every 1 ms

    def get_active_channel(self):
        """Reads the status register to determine the current channel."""
        status = self.read_register(self.STATUS_REGISTER, 1)[0]
        channel = status & 0x0F  # Extract CHD3:CHD0
        return channel

    def get_active_channels(self):
        """Reads the configuration register to determine all active channels."""
        config = int.from_bytes(self.read_register(self.CONFIGURATION_REGISTER, 3), 'big')
        active_channels = []
        for channel in range(8):  # Check CH7 to CH0
            if config & (1 << channel):
                active_channels.append(channel)
        return active_channels

    def get_mode(self):
        """Checks if the ADC is in differential or pseudo-differential mode."""
        config = int.from_bytes(self.read_register(self.CONFIGURATION_REGISTER, 3), 'big')
        return 'Pseudo-Differential' if config & (1 << 12) else 'Differential'

    def configure_adc(self, mode='pseudo-differential', polarity='bipolar', channels=[1, 2, 3, 4], gain=1):
        """
        Configures the AD7193 ADC.

        Parameters:
            mode (str): 'pseudo-differential' or 'differential'.
            polarity (str): 'unipolar' or 'bipolar'.
            channels (list): List of channel numbers to activate (1-8 for pseudo-differential, 1-4 for differential pairs).
            gain (int): Gain setting (1, 8, 16, 32, 64, 128).
        """
        # Validate mode
        if mode not in ['pseudo-differential', 'differential']:
            raise ValueError("Invalid mode. Choose 'pseudo-differential' or 'differential'.")

        # Validate polarity
        if polarity not in ['unipolar', 'bipolar']:
            raise ValueError("Invalid polarity. Choose 'unipolar' or 'bipolar'.")

        # Validate gain
        gain_map = {1: 0b000, 8: 0b011, 16: 0b100, 32: 0b101, 64: 0b110, 128: 0b111}
        if gain not in gain_map:
            raise ValueError("Invalid gain. Choose from 1, 8, 16, 32, 64, 128.")

        # Configure channels
        channel_mask = 0
        if mode == 'pseudo-differential':
            for ch in channels:
                if 1 <= ch <= 8:
                    channel_mask |= (1 << (ch - 1))
                else:
                    raise ValueError("Invalid channel for pseudo-differential. Choose 1-8.")
        elif mode == 'differential':
            for ch in channels:
                if 1 <= ch <= 4:
                    channel_mask |= (1 << (ch - 1))
                else:
                    raise ValueError("Invalid channel for differential. Choose 1-4.")

        # Configure polarity
        unipolar_bit = 0 if polarity == 'bipolar' else 1

        # Build configuration register value
        config_value = (unipolar_bit << 12) | (gain_map[gain] << 8) | channel_mask

        # Write to configuration register
        self.write_register(self.CONFIGURATION_REGISTER, config_value)

