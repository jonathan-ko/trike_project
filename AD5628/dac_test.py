mport board
import busio
import AD5628
import time
import digitalio


spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs=digitalio.DigitalInOut(board.CE0)
cs.direction=digitalio.Direction.OUTPUT
dac = AD5628.AD5628(spi,cs)

dac.reset()
dac.internal_ref_mode()
dac.write_register(0x0F, 0xFFF)

