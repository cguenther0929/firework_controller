"""
    The purpose of this module 
    is to drive the firework igniter.
"""
from datetime import datetime
import serial
import time
import timeit
import re
import binascii
import os
import logging
import sys
import json
import argparse

#---------------------------------------------------------------
# Setup Logging
# Logging Levels:
# CRITICAL: 50
# ERROR:    40
# WARNING : 30
# INFO:     20
# DEBUG:    10
# NOTSET:   0
#---------------------------------------------------------------
logging.basicConfig(
    filename = 'data_log_firework_controller.log',
    filemode = 'w',
    level=logging.INFO,
    format=' %(asctime)s -  %(levelname)s - %(message)s'
)
#---------------------------------------------------------------
# Load firework configuration from JSON
#---------------------------------------------------------------
f = open("firework_config.json",'r')
json_config_string = json.loads(f.read())
f.close()

# f = open("firework_config.json",'r')
# json_data = json.load(f)
# f.close()

# TODO the following debug code can be deleted
# print ("Here is the JSON config string: ")
# print (json_config_string)

# print ("Accessing specific member:")
# print (json_config_string["ch_1"][0]["dwell_time_s"])

# sys.exit(0)


#---------------------------------------------------------------
# Message ID Defines
#---------------------------------------------------------------
MESSAGE_SOF                 = 0xFC        #Message ID defines
MESSAGE_EOF                 = 0xF6
MESSAGE_EOF_ASCII           = "f6"

MESSAGE_ID_FUSE_STATUS      = 0x01
MESSAGE_ID_IGNITE_FUSE      = 0x02
MESSAGE_ID_SET_CURRENT      = 0x03
MESSAGE_ID_GET_CURRENT      = 0x04


#---------------------------------------------------------------#
# Bit Offsets
#---------------------------------------------------------------#
FOUR_DIG_BIN_NUM_RE = re.compile("[0-1]{4}")
FIVE_DIG_BIN_NUM_RE = re.compile("[0-1]{5}")

#---------------------------------------------------------------
# DEFINE FUNCTIONS
#---------------------------------------------------------------
def _print_fuse_status(message):
    user_friendy_fuse = []

    value_index = 0

    for i in range (4):
        if(i == 0):
            for j in range (4):
                current_bit = int((int(str(message[9]),16) >> (j)) & 0x01)
                if(current_bit):
                    user_friendy_fuse.append(((4*i)+j+1))
                value_index = value_index + 1

        elif(i == 1):
            for j in range (4):
                current_bit = int((int(str(message[8]),16) >> (j)) & 0x01)
                if(current_bit):
                    user_friendy_fuse.append(((4*i)+j+1))
                value_index = value_index + 1
        
        elif(i == 2):
            for j in range (4):
                current_bit = int((int(str(message[7]),16) >> (j)) & 0x01)
                if(current_bit):
                    user_friendy_fuse.append(((4*i)+j+1))
                value_index = value_index + 1

        elif(i == 3):
            for j in range (4):
                current_bit = int((int(str(message[6]),16) >> (j)) & 0x01)
                if(current_bit):
                    user_friendy_fuse.append(((4*i)+j+1))
                value_index = value_index + 1

    print("Valid Channels: ", user_friendy_fuse)

#---------------------------------------------------------------
# Function for igniting fuse
#---------------------------------------------------------------
def _ignite_fuse(comm,fuse_number):
    logging.info("---------------------------------------------------")
    logging.info("Igniting fuse" + str(fuse_number) + "...")
    print("---------------------------------------------------")
    print("Igniting fuse", str(fuse_number), "...")
    
    bcd_list = _bcd_of_value(fuse_number)

    # print("***DEBUG bcd list: ", bcd_list)

    message_length = len(bcd_list)                      # Message length 

    tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_IGNITE_FUSE,message_length,MESSAGE_EOF])

    for i in range(0,len(bcd_list)):
        tx_array.insert((3+i),bcd_list[i])


    comm.send_message_to_igniter(tx_array)
    print("Command sent: ", str(binascii.b2a_hex(tx_array)))
    logging.info("Command sent: " + str(binascii.b2a_hex(tx_array)))

    bintoascii_data_str = comm.read_serial()
    
    logging.info("ACK Response: " + bintoascii_data_str)
    print("ACK Response: ", bintoascii_data_str)

#---------------------------------------------------------------
# Function to set fuse current
#---------------------------------------------------------------
def _set_fuse_current(comm,fuse_current):
    logging.info("---------------------------------------------------")
    logging.info("Setting fuse current to: " + str(fuse_current) + " mA")
    print("---------------------------------------------------")
    print("Setting fuse current to: ",  str(fuse_current), " mA")
    
    bcd_list = _bcd_of_value(fuse_current)


    message_length = len(bcd_list)                      # Message length 

    tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_SET_CURRENT,message_length,MESSAGE_EOF])

    for i in range(0,len(bcd_list)):
        tx_array.insert((3+i),bcd_list[i])

    comm.send_message_to_igniter(tx_array)
    print("Command sent: ", str(binascii.b2a_hex(tx_array)))
    logging.info("Command sent: " + str(binascii.b2a_hex(tx_array)))

    bintoascii_data_str = comm.read_serial()
    
    logging.info("ACK Response: " + bintoascii_data_str)
    print("ACK Response: ", bintoascii_data_str)

    #---------------------------------------------------------------
    # Confirm setting by querying panel 
    # ---------------------------------------------------------------
    _get_fuse_current(comm)

#---------------------------------------------------------------
# Function to get fuse current
#---------------------------------------------------------------
def _get_fuse_current(comm):
    logging.info("---------------------------------------------------")
    logging.info("Retrieving fuse current value...")
    print("---------------------------------------------------")
    print("Retrieving fuse current value...")
    
    tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_GET_CURRENT,0x00,MESSAGE_EOF])

    comm.send_message_to_igniter(tx_array)
    print("Command sent: ", str(binascii.b2a_hex(tx_array)))
    logging.info("Command sent: " + str(binascii.b2a_hex(tx_array)))

    bintoascii_data_str = comm.read_serial()
    
    logging.info("Igniter response: " + bintoascii_data_str)
    print("Igniter response: ", bintoascii_data_str)

    pow_of_ten = int(bintoascii_data_str[5]) - 1  #Power of ten for BCD value

    if(len(bintoascii_data_str) <= 4):
        print ("Fuse current value not returned...")
    else:                                       
        CurrentVal = ""
        for i in range(6,len(bintoascii_data_str)-2):
            if(i % 2 != 0):
                CurrentVal += bintoascii_data_str[i]
        print ("Fuse current: ", str(float(int(CurrentVal))), " mA")
        logging.info ("Current value: " + str(float(int(CurrentVal))) + " mA")

    logging.info("---------------------------------------------------")
    print("---------------------------------------------------")

def _bcd_of_value(inputValue): 
    x=str(inputValue) 
    bcd_list = [] 
    for char in x: bcd_list.append(int(char))
    return bcd_list
    
def _clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


#---------------------------------------------------------------
# Define Serial Communication Class
#---------------------------------------------------------------
class SerialComm:
    def __init__(self, serial_baud_rate, serial_timeout_seconds):
        self.serial_port_stats = False
        
        for i in range(3,256):
            try:
                self.serial_port_num = i
                self.serial_port_string = "COM" + str(self.serial_port_num)

                self.ser = serial.Serial(self.serial_port_string, serial_baud_rate, timeout=serial_timeout_seconds)                
                
                print ("Found A Serial Port Available At COM%d" %i)
                break
            
            except:
                print ("Nothing On COM%d" %i)

        if (i <= 255):
            self.serial_port_stats = True
        
    def read_serial(self):
        rx_message      = ""
        byte            = 0x00
        byte_ascii      = '\0'
        elapsed_time    = 0
        tic = timeit.default_timer()


        while (byte_ascii != "f6" and elapsed_time < 1.5):
            
            byte = str(binascii.b2a_hex(self.ser.read(1)))
            
            byte_list = byte.split("\'")
            byte_ascii = str(byte_list[1])
            
            rx_message += byte_ascii

            elapsed_time += int(timeit.default_timer() - tic)

        self.ser.flushInput()

        return rx_message  

    def send_message_to_igniter(self, transmit_data_array):  
        self.ser.flushInput()
        self.ser.write(transmit_data_array)

    def close_serial_port(self):
        self.ser.close()
    
#---------------------------------------------------------------#
#---------------------------------------------------------------#
# MAIN LOOP
#---------------------------------------------------------------#
#---------------------------------------------------------------#
if __name__ == '__main__':

    #---------------------------------------------------------------
    # Parse input arguments 
    #---------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Firework igniter controller")

    parser.add_argument("--setcurrent", "-set", default=False, type=bool, nargs='?',
                   help="Set the fuse current value in mA.")
    
    parser.add_argument("--getcurrent", "-get", default=False, type=bool, nargs='?',
                   help="Request the igniter to report the fuse current setting.")
    
    parser.add_argument('--version', "-v", action='version', version="%(prog)s 1.0.1")  
    
    args = parser.parse_args()

    logging.info("---------------------------------------------")
    logging.info("---------------------------------------------")
    logging.info("------- Firework Controller Log  ------------")
    logging.info("---------------------------------------------")
    logging.info("---------------------------------------------")
    
    _clear_screen()
    print("---------------------------------------------")
    print("---------------------------------------------")
    print("-------- Firework Controller App ------------")
    print("---------------------------------------------")
    print("---------------------------------------------")

    
    comm = SerialComm(serial_baud_rate=9600, serial_timeout_seconds=2)
    
    if(not comm.serial_port_stats):
        logging.info("Failed to open serial port.")
        print("Failed to open serial port.")
        sys.exit(0)

    message_id = 0
    fuse_number = 0

    #---------------------------------------------------------------#
    # Handle input arguments for setting/getting current
    #---------------------------------------------------------------#
    if(args.setcurrent != False):
        logging.info("---------------------------------------------------")
        logging.info("Setting fuse current...")
        print("\n------------------------------------------------")
        print("Setting fuse current...")
        fuse_current_value_ma = 0
        while (fuse_current_value_ma <= 0 or fuse_current_value_ma > 1000):
            fuse_current_value_ma = int(input("Enter fuse current setting in mA (1-1000): "))

        _set_fuse_current(comm,fuse_current_value_ma)
    
    if(args.getcurrent != False):
        fuse_current_value_ma = 0
        _get_fuse_current(comm)


    #---------------------------------------------------------------#
    # Indicate what the valid channels are
    #---------------------------------------------------------------#
    tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_FUSE_STATUS,0x00,MESSAGE_EOF])
    comm.send_message_to_igniter(tx_array)
    time.sleep(.1)
    bintoascii_data_str = comm.read_serial()
    _print_fuse_status(bintoascii_data_str)
    print("------------------------------------------------")

    
    while(fuse_number != 99):

        #---------------------------------------------------------------#
        # After dwell time, request fuse status 
        #---------------------------------------------------------------#
        tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_FUSE_STATUS,0x00,MESSAGE_EOF])
        comm.send_message_to_igniter(tx_array)
        bintoascii_data_str = comm.read_serial()
        _print_fuse_status(bintoascii_data_str)
        
        message_id = 0
        fuse_number = 0
        while (fuse_number <=0 or fuse_number > 16):
            fuse_number = int(input("What Fuse Number Shall be Lit: "))
            if(fuse_number == 99):  # User wishes to exit application
                break

        if(fuse_number == 99):  # User wishes to exit application
            break
        
        _ignite_fuse(comm,fuse_number)

        #---------------------------------------------------------------#
        # Determine the dwell time
        #---------------------------------------------------------------#
        channel_string = "ch_" + str(fuse_number)
        dwell_time = json_config_string[channel_string][0]["dwell_time_s"]
        print("Dwell time is: ", dwell_time)
        for i in range (dwell_time,-1,-1):
            sys.stdout.write("\r" + "====> " + str(i) + "  ")
            time.sleep(1)
            sys.stdout.flush()
            
        print("\n----------------------------------------------------")

    #---------------------------------------------------------------
    # CLOSE EVERYTHING DOWN
    #---------------------------------------------------------------
    comm.close_serial_port() #Close the serial port so we don't hose up the system.

    logging.info("---------------------------------------------------")
    logging.info("Application closing.")
    print("\n\n*******************************")
    print("===> Application closing.")
    time.sleep(2)
    _clear_screen() 