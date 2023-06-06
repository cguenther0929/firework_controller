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


#---------------------------------------------------------------#
# Bit Offsets
#---------------------------------------------------------------#
FOUR_DIG_BIN_NUM_RE = re.compile("[0-1]{4}")
FIVE_DIG_BIN_NUM_RE = re.compile("[0-1]{5}")

#---------------------------------------------------------------
# DEFINE FUNCTIONS
#---------------------------------------------------------------
def _print_fuse_status(message):
    # good_fuses = [0 for x in range (16)]
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
                    # good_fuses[value_index] = 1
                    user_friendy_fuse.append(((4*i)+j+1))
                value_index = value_index + 1
        
        elif(i == 2):
            for j in range (4):
                current_bit = int((int(str(message[7]),16) >> (j)) & 0x01)
                if(current_bit):
                    # good_fuses[value_index] = 1
                    user_friendy_fuse.append(((4*i)+j+1))
                value_index = value_index + 1

        elif(i == 3):
            for j in range (4):
                current_bit = int((int(str(message[6]),16) >> (j)) & 0x01)
                if(current_bit):
                    # good_fuses[int(value_index)] = 1
                    user_friendy_fuse.append(((4*i)+j+1))
                value_index = value_index + 1

    # print("Fuse Values: ", good_fuses)
    print("Valid Channels: ", user_friendy_fuse)


def _ignite_fuse(comm,fuse_number):
    logging.info("---------------------------------------------------")
    logging.info("Igniting fuse" + str(fuse_number) + "...")
    print("---------------------------------------------------")
    print("Igniting fuse", str(fuse_number), "...")
    
    # fuse_value = 0
    # while (fuse_value <= 0 or fuse_value > 16):
    #     fuse_value = int(input("   Enter fuse number to light (1 to 16): "))
    
    bcd_list = _bcd_of_value(fuse_number)

    # print("***DEBUG bcd list: ", bcd_list)

    message_length = len(bcd_list)                      # Message length 

    tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_IGNITE_FUSE,message_length,MESSAGE_EOF])

    for i in range(0,len(bcd_list)):
        tx_array.insert((3+i),bcd_list[i])


    comm.send_message_to_panel(tx_array)
    print("Command sent: ", str(binascii.b2a_hex(tx_array)))
    logging.info("Command sent: " + str(binascii.b2a_hex(tx_array)))

    bintoascii_data_str = comm.read_serial()
    
    logging.info("ACK Response: " + bintoascii_data_str)
    print("ACK Response: ", bintoascii_data_str)



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
        
        for i in range(12,256):
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

    def send_message_to_panel(self, transmit_data_array):  
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

    logging.info("---------------------------------------------")
    logging.info("---------------------------------------------")
    logging.info("------- Firework Controller Log  ------------")
    logging.info("---------------------------------------------")
    logging.info("---------------------------------------------")

    _clear_screen()
    
    #TODO need to correct the baud rate
    #TODO BAUD should be 9600 for XBEE
    comm = SerialComm(serial_baud_rate=57600, serial_timeout_seconds=2)
    
    if(not comm.serial_port_stats):
        logging.info("Failed to open serial port.")
        print("Failed to open serial port.")
        sys.exit(0)

    message_id = 0
    fuse_number = 0


    #---------------------------------------------------------------#
    # Indicate what the valid channels are
    #---------------------------------------------------------------#
    tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_FUSE_STATUS,0x00,MESSAGE_EOF])
    comm.send_message_to_panel(tx_array)
    bintoascii_data_str = comm.read_serial()
    _print_fuse_status(bintoascii_data_str)
    print("------------------------------------------------")


    
    while(fuse_number != 16):

        # print ("\n\nSelect an operation:")
        # print (str(MESSAGE_ID_FUSE_STATUS)        , " -- to request fuse status.")
        # print (str(MESSAGE_ID_IGNITE_FUSE)     , " -- to ignite a fuse.")

        # print (str(99)                          , " -- Exit the application.")

        #---------------------------------------------------------------#
        # After dwell time, request fuse status 
        #---------------------------------------------------------------#
        tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_FUSE_STATUS,0x00,MESSAGE_EOF])
        comm.send_message_to_panel(tx_array)
        bintoascii_data_str = comm.read_serial()
        _print_fuse_status(bintoascii_data_str)
        
        message_id = 0
        fuse_number = 0
        # message_id = int(input("Enter the ID of the message (e.g. 0x01): "))
        while (fuse_number <=0 or fuse_number > 16):
            fuse_number = int(input("What Fuse Number Shall be Lit: "))
        
        _ignite_fuse(comm,fuse_number)

        #---------------------------------------------------------------#
        # Determine the dwell time
        #---------------------------------------------------------------#
        channel_string = "ch_" + str(fuse_number)
        # dwell_time = json_config_string([channel_string][0]["dwell_time_s"])
        dwell_time = json_config_string[channel_string][0]["dwell_time_s"]
        print("Dwell time is: ", dwell_time)
        # time.sleep(dwell_time)
        for i in range (dwell_time,-1,-1):
            sys.stdout.write("\r" + "====> " + str(i) + "  ")
            time.sleep(1)
            sys.stdout.flush()
            
            
            
        
        print("\n----------------------------------------------------")

                    



        #---------------------------------------------------------------#
        # Query the igniter for the fuse status
        #---------------------------------------------------------------#
        # if(message_id == MESSAGE_ID_FUSE_STATUS):  
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting fuse status.")
            
        #     tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_FUSE_STATUS,0x00,MESSAGE_EOF])
            
        #     comm.send_message_to_panel(tx_array)
            
        #     logging.info("Command sent to igniter: " + str(binascii.b2a_hex(tx_array)))
        #     print("Command sent to igniter: ", str(binascii.b2a_hex(tx_array)))

        #     bintoascii_data_str = comm.read_serial()

        #     _print_fuse_status(bintoascii_data_str)

        #     logging.info("Response from igniter: " + bintoascii_data_str)
        #     print("Response from igniter", bintoascii_data_str)
            
        
        #---------------------------------------------------------------#
        # Operation to ignite a fuse
        #---------------------------------------------------------------#
        # elif(message_id == MESSAGE_ID_IGNITE_FUSE):                                        
        #     logging.info("---------------------------------------------------")
        #     logging.info("Igniting fuse")
            
        #     fuse_value = 0
        #     while (fuse_value <= 0 or fuse_value > 16):
        #         fuse_value = int(input("   Enter fuse number to light (1 to 16): "))
            
        #     bcd_list = _bcd_of_value(fuse_value)

        #     print("***DEBUG bcd list: ", bcd_list)

        #     message_length = len(bcd_list)                      # Message length 

        #     tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_IGNITE_FUSE,message_length,MESSAGE_EOF])

        #     for i in range(0,len(bcd_list)):
        #         tx_array.insert((3+i),bcd_list[i])


        #     comm.send_message_to_panel(tx_array)
        #     print("Command sent: ", str(binascii.b2a_hex(tx_array)))
        #     logging.info("Command sent: " + str(binascii.b2a_hex(tx_array)))

        #     bintoascii_data_str = comm.read_serial()
            
        #     logging.info("ACK Response: " + bintoascii_data_str)
        #     print("ACK Response: ", bintoascii_data_str)

        # else:
        #     "Invalid selection."


    #---------------------------------------------------------------
    # CLOSE EVERYTHING DOWN
    #---------------------------------------------------------------
    comm.close_serial_port() #Close the serial port so we don't hose up the system.

    logging.info("---------------------------------------------------")
    logging.info("Application closing.")
    print("\n\n     Application closing.") 