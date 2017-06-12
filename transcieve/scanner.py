import RPi.GPIO as GPIO
import time
from RF24 import *

# Pin Definitions:
ce = 22  # gpio 25
csn = 24  # gpio 8 / spio cs0
sck = 23  # gpio 11 / spio sclk
mosi = 19  # gpio 10 / spio mosi
miso = 21  # gpio 9 / spio miso
irq = 15  # gpio 22

err_led = 12  # gpio
rx_led = 16  # gpio
tx_led = 18  # gpio


# # Pin Setup:
# GPIO.setmode(GPIO.BOARD) # Board pin-numbering scheme
# GPIO.setwarnings(False) # Suppressing too many warnings
# GPIO.setup(err_led, GPIO.OUT) # LED pin set as output
# GPIO.setup(rx_led, GPIO.OUT) # PWM pin set as output
# GPIO.setup(tx_led, GPIO.OUT) # PWM pin set as output
#
# # Initial state for LEDs:
# try:
#     GPIO.output(err_led, GPIO.HIGH)
#     GPIO.output(rx_led, GPIO.HIGH)
#     GPIO.output(tx_led, GPIO.HIGH)
#     time.sleep(5)
#     GPIO.output(err_led, GPIO.LOW)
#     GPIO.output(rx_led, GPIO.LOW)
#     GPIO.output(tx_led, GPIO.LOW)
# except KeyboardInterrupt:
#     GPIO.cleanup() # cleanup all GPIO
#
# GPIO.cleanup()


def scanner():
    my_rf24 = RF24(22, 0)

    min_channels = 0
    max_channels = 127
    num_channels = max_channels - min_channels
    num_samples = 100
    threshold = 10

    # start the radio
    my_rf24.begin()

    # disable error control features
    my_rf24.disableCRC()

    # disable sending out acknowledge messages
    my_rf24.setAutoAck(False)

    # set the data rate, guesses 1MBPS, since this was the only rate with peaks during scans
    # my_rf24.setDataRate(RF24_1MBPS)

    my_rf24.printDetails()

    values = [0]*num_channels
    # check each channel num_samples times
    for i in range(num_samples):
        # switch through the channels
        for j in range(num_channels):
            my_rf24.setChannel(min_channels + j)
            my_rf24.startListening()
            time.sleep(.1)
            my_rf24.stopListening()
            if my_rf24.testCarrier():
                values[j] += 1
                print("Channel {}: {}".format(j, values[j]))

    # output of the results
    for channel in range(num_channels):
        # only print those above the threshold
        if values[channel] > threshold:
            print("{}: {}".format(min_channels + channel, values[channel]))


def promiscuous_receiver():

    my_rf24 = RF24(22, 0)

    # buffer for reading incoming messages
    max_buffer_size = 32
    my_buffer = []
    buffer_size = 16

    # channel to listen to
    channel = 8

    # there are two address modes: 0x55 and 0xAA
    # address_mode = False

    # there are (presently) two print modes: bits and bytes
    # print_mode = 0

    # some flags for the state
    is_running = False
    is_listening = False

    # for a heartbeat to show that the program is still running
    # when there is no transmissions
    has_heartbeat = False
    heartbeat_counter = 0
    timer_threshold = 1000

    has_heartbeat = not has_heartbeat
    is_running = not is_running

    # start the radio
    my_rf24.begin()
    my_rf24.setChannel(channel)
    # disable error control features
    my_rf24.disableCRC()
    # disable sending out acknowledge messages
    my_rf24.setAutoAck(False)
    my_rf24.setDataRate(RF24_250KBPS)
    # my_rf24.setDataRate(RF24_1MBPS)
    my_rf24.setAddressWidth(3)
    # print out the radio settings
    my_rf24.printDetails()

    # def print_bits():
    #     for i in range(buffer_size):
    #         reader_str = ''
    #         for j in range(7):
    #             # TODO: no idea how to translate bitwise
    #             pass
    #             # reader_str += (my_buffer[j:i] & 128)?1:0) + " "

    def print_bytes():
        print("Printing bytes...")
        # initialize output string
        reader_str = ""

        # loop through the buffer
        for i in range(buffer_size):
            # leading spaces to make things look nicer
            if my_buffer[i] < 10:
                reader_str += "  "
            elif my_buffer[i] < 100:
                reader_str += " "
            # add a byte and a delimiter
            reader_str += str(my_buffer[i]) + " "

        # no need for a delimiter at the end of the last byte
        reader_str += str(my_buffer[buffer_size - 1])

        # output of the string
        print(reader_str)

    def toggle_address(address_mode):
        print("Toggling address...")
        if is_listening:
            my_rf24.stopListening()

        if address_mode:
            print("Opening pipes at 0xAA...")
            my_rf24.openReadingPipe(0, 0xAA)
            my_rf24.openReadingPipe(1, 0xAA)
        else:
            print("Opening pipes at 0x55...")
            my_rf24.openReadingPipe(0, 0x55)
            my_rf24.openReadingPipe(1, 0x55)

        # TODO: not sure how to translate below
        address_mode = not address_mode

        if is_listening:
            my_rf24.startListening()

    while is_running:
        if not is_listening:
            my_rf24.openReadingPipe(0, 0xAA)
            my_rf24.openReadingPipe(1, 0xAA)
            print("Starting to listen...")
            my_rf24.startListening()
            is_listening = True

        if has_heartbeat:
            print("Has heartbeat.. continuing...")
            timer = time.time()
            print(my_rf24.available())
            while (not my_rf24.available()) & ((time.time() - timer) < timer_threshold):
                # print('hmm')
                pass

            if heartbeat_counter+1 >= 10:
                print('.')
                heartbeat_counter= 0
            else:
                print('.')

        if my_rf24.available():
            # paySize = my_rf24.getPayloadSize()
            # print(paySize)
            print(my_rf24.read(max_buffer_size))
            print_bytes(my_rf24.read(max_buffer_size))

            # print_bytes()

        else:
            if is_listening:
                my_rf24.stopListening()
                is_listening = False


# promiscuous_receiver()
scanner()
