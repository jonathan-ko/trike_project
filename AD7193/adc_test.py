# Example usage
import board
import busio
import AD7193


spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = board.D7  # Replace with your chip select pin

adc = AD7193.AD7193(spi, cs)
adc.reset()
adc.initialize()


# Configure ADC for pseudo-differential mode, unipolar, channels 1-4, gain of 32
adc.configure_adc(mode='pseudo-differential', polarity='unipolar', channels=[1, 2, 3, 4], gain=32)

print("Current Mode:", adc.get_mode())

all_channels = adc.get_active_channels()
print(f"Enabled Channels: {all_channels}")

try:
    while True:
        adc.wait_for_data_ready()
        current_channel = adc.get_active_channel()
        data = adc.read_data()
        print(f"Channel {current_channel}: Data = {data}")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Stopped.")
