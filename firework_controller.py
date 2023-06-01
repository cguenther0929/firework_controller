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
# def _print_current(bintoascii_data_str):

#     print ("Panel Response: ", bintoascii_data_str)
#     logging.info("Panel Response: " + bintoascii_data_str)

#     pow_of_ten = int(bintoascii_data_str[5]) - 1  #Power of ten for BCD value

#     if(len(bintoascii_data_str) <= 4):
#         print ("Data not returned from panel...")
#     else:                                       
#         CurrentVal = ""
#         for i in range(6,len(bintoascii_data_str)-2):
#             if(i % 2 != 0):
#                 CurrentVal += bintoascii_data_str[i]
#         print ("Current value: ", str(float(int(CurrentVal)/1000.0)), " mA")
#         logging.info ("Current value: " + str(float(int(CurrentVal)/1000.0)) + " mA")
    
# def _read_exciter_current(ID):
    
#     tx_array = bytearray([MESSAGE_SOF,ID,0x00,MESSAGE_EOF])
#     comm.send_message_to_panel(tx_array)
    
#     logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))
    
#     bintoascii_data_str = comm.read_serial()
    
#     _print_current(bintoascii_data_str)

def _print_fuse_status(message):
    good_fuses = [0 for x in range (16)]


    value_index = 0

    for i in range (4):
        if(i == 0):
            for j in range (4):
                current_bit = int((int(str(message[6]),16) >> (3-j)) & 0x01)
                if(current_bit):
                    good_fuses[value_index] = 1
                value_index = value_index + 1

        elif(i == 1):
            for j in range (4):
                current_bit = int((int(str(message[7]),16) >> (3-j)) & 0x01)
                if(current_bit):
                    good_fuses[value_index] = 1
                value_index = value_index + 1
        
        elif(i == 2):
            for j in range (4):
                current_bit = int((int(str(message[8]),16) >> (3-j)) & 0x01)
                if(current_bit):
                    good_fuses[value_index] = 1
                value_index = value_index + 1

        elif(i == 3):
            for j in range (4):
                current_bit = int((int(str(message[9]),16) >> (3-j)) & 0x01)
                if(current_bit):
                    good_fuses[int(value_index)] = 1
                value_index = value_index + 1

    print("Fuse Values: ", good_fuses)



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
    
    #TODO need to correct the baud rate
    #TODO BAUD should be 9600 for XBEE
    comm = SerialComm(serial_baud_rate=57600, serial_timeout_seconds=2)
    
    if(not comm.serial_port_stats):
        logging.info("Failed to open serial port.")
        print("Failed to open serial port.")
        sys.exit(0)

    message_id = 0
    
    while(message_id != 99):

        print ("\n\nSelect an operation:")
        print (str(MESSAGE_ID_FUSE_STATUS)        , " -- to request fuse status.")
        print (str(MESSAGE_ID_IGNITE_FUSE)     , " -- to ignite a fuse.")

        print (str(99)                          , " -- Exit the application.")

        message_id = int(input("Enter the ID of the message (e.g. 0x01): "))

        #---------------------------------------------------------------#
        # Query the igniter for the fuse status
        #---------------------------------------------------------------#
        if(message_id == MESSAGE_ID_FUSE_STATUS):  
            logging.info("---------------------------------------------------")
            logging.info("Requesting fuse status.")
            
            tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_FUSE_STATUS,0x00,MESSAGE_EOF])
            
            comm.send_message_to_panel(tx_array)
            
            logging.info("Command sent to igniter: " + str(binascii.b2a_hex(tx_array)))
            print("Command sent to igniter: ", str(binascii.b2a_hex(tx_array)))

            bintoascii_data_str = comm.read_serial()

            _print_fuse_status(bintoascii_data_str)

            logging.info("Response from igniter: " + bintoascii_data_str)
            print("Response from igniter", bintoascii_data_str)
            
            # speed_value= 0xFF                         #Set a default value for while loop
            # TachVal = 0xFF

            # while (speed_value < 0 or speed_value > 50):
            #     speed_value = float(input("   Enter a commanded speed value (0 to 50MPH): "))
            
            # speed_value *= 10.0               # Speed value transmitted shall be speed ×10
            # speed_value = int(speed_value)

            # print ("\n   0 -- Set both TACHs to the same speed.")
            # print ("   1 -- Set only TACH 1 to commanded speed.")
            # print ("   2 -- Set only TACH 2 to the commanded speed.")

            # while (TachVal < 0 or TachVal > 2):
            #     TachVal = int(input("   Enter selection: "))

            # bcd_list = _bcd_of_value(speed_value)
            # message_length = len(bcd_list) + 1                       # Message length must include tach command byte which is entered next (see below)

            # tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_SET_SPEED,message_length,MESSAGE_EOF])
            
            # for i in range(0,len(bcd_list)):
            #     tx_array.insert((3+i),bcd_list[i])

            # tx_array.insert(3,TachVal)  #Insert how we want to set tachs
            # comm.send_message_to_panel(tx_array)

            # logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))
            # print("Command sent to panel: ", str(binascii.b2a_hex(tx_array)))

            # bintoascii_data_str = comm.read_serial()

            # logging.info("Panel Response: " + bintoascii_data_str)
            # print("Panel Response: ", bintoascii_data_str)
        
        #---------------------------------------------------------------#
        # Operation to ignite a fuse
        #---------------------------------------------------------------#
        elif(message_id == MESSAGE_ID_IGNITE_FUSE):                                        
            logging.info("---------------------------------------------------")
            logging.info("Igniting fuse")
            
            fuse_value = 0
            while (fuse_value <= 0 or fuse_value > 16):
                fuse_value = int(input("   Enter fuse number to light (1 to 16): "))
            
            bcd_list = _bcd_of_value(fuse_value)

            print("***DEBUG bcd list: ", bcd_list)

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

            # speed_value = ''
            # for i in range(6,len(bintoascii_data_str)-2):
            #     if(i % 2 != 0):
            #         speed_value += bintoascii_data_str[i]              # Concatinating a string here (i.e. "400" can be easily converted to an int)

            
            # print("Speed Setting: ", str(float(int(speed_value)/10.0)), " MPH")
            # logging.info("Speed Setting: " + str(float(int(speed_value)/10.0)) + " MPH")

        #---------------------------------------------------------------#
        # Send TACH control message
        #---------------------------------------------------------------#
        # elif(message_id == MESSAGE_ID_TACH_CONTROL):      
        #     logging.info("---------------------------------------------------")
        #     logging.info("Tachometer control message.")
            
        #     binary_input_data = '\0'
        #     tach_1_phase = 3
        #     tach_2_phase = 3

        #     print ("   Enter binary representation for which TACHs to enable.")
        #     print ("   Format is TACH 1A | TACH 1B | TACH 2A | TACH 2B")


        #     while ((len(FOUR_DIG_BIN_NUM_RE.findall(binary_input_data)) != 1) or len(binary_input_data) != 4):
        #         binary_input_data = input("\n   Define which channels to enable (i.e. 1011) : ")

        #     tach_enable_nibble =    (((int(binary_input_data[0]) ^ 1) << 3)   |
        #                             ((int(binary_input_data[1])  ^ 1)  << 2)   |
        #                             ((int(binary_input_data[2])  ^ 1)  << 1)   |
        #                             ((int(binary_input_data[3])  ^ 1)  << 0))

        #     print ('')
        #     print ("   0 -- Tach 1A leads 1B")
        #     print ("   1 -- Tach 1B leads 1A")
        #     while (tach_1_phase < 0 or tach_1_phase > 1):
        #         tach_1_phase = int(input("   Enter selection: "))
        #     print ('')
            
        #     print ("   0 -- Tach 2A leads 2B")
        #     print ("   1 -- Tach 2B leads 2A")
        #     while (tach_2_phase < 0 or tach_2_phase > 1):
        #         tach_2_phase = int(input("   Enter selection: "))
        #     print ('')


        #     message_length = 0x03                       # Always the case for this selection
        #     tx_array = bytearray([MESSAGE_SOF, MESSAGE_ID_TACH_CONTROL, message_length, tach_enable_nibble, tach_1_phase, tach_2_phase, MESSAGE_EOF])
        #     comm.send_message_to_panel(tx_array)
        #     print ("Command sent to panel: ", str(binascii.b2a_hex(tx_array)))
        #     logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))
            
        #     bintoascii_data_str = comm.read_serial()

        #     logging.info("Panel Response: " + bintoascii_data_str)
        #     print("Panel Response: ", bintoascii_data_str)

        # #---------------------------------------------------------------#
        # # Send Phase Flip control message
        # #---------------------------------------------------------------#
        # elif(message_id == MESSAGE_ID_PHASE_CTRL):  
        #     logging.info("---------------------------------------------------")
        #     logging.info("Tachometer control message.")
            
        #     PsEnableorDisable   = 0xFF
        #     PsPhaseRelationship = 0xFF
        #     PsReferenceSignal   = 0xFF

        #     print ("   1 -- Disable phase flips")
        #     print ("   0 -- Enable phase flips")
        #     while (PsEnableorDisable < 0 or PsEnableorDisable > 1):
        #         PsEnableorDisable = int(input("   Enter selection: "))
        #     print ('')

        #     print ("   0 -- Signals in phase.")
        #     print ("   1 -- Signals out of phase.")
        #     while (PsPhaseRelationship < 0 or PsPhaseRelationship > 1):
        #         PsPhaseRelationship = int(input("   Enter selection: "))
        #     print ('')

        #     print ("   0 -- Phase flips reference PWM 1")
        #     print ("   1 -- Phase flips reference PWM 2")
        #     while (PsReferenceSignal < 0 or PsReferenceSignal > 1):
        #         PsReferenceSignal = int(input("   Enter selection: "))

        #     message_length = 0x03                       # Always the case for this selection
        #     tx_array = bytearray([MESSAGE_SOF, MESSAGE_ID_PHASE_CTRL, message_length, PsEnableorDisable, PsPhaseRelationship, PsReferenceSignal, MESSAGE_EOF])
        #     comm.send_message_to_panel(tx_array)
        #     logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))
            
        #     bintoascii_data_str = comm.read_serial()

        #     logging.info("Panel Response: " + bintoascii_data_str)
        #     print("Panel Response: ", bintoascii_data_str)

        # #---------------------------------------------------------------#
        # # Define phase flip rate -- i.e. how many tach edges between
        # # between phase flips
        # #---------------------------------------------------------------#
        # elif(message_id == MESSAGE_ID_PS_RATE):  
        #     logging.info("---------------------------------------------------")
        #     logging.info("Phase flip rate message.")

        #     phase_flip_rate = -1

        #     while (phase_flip_rate < 0 or phase_flip_rate > 100):
        #         phase_flip_rate = float(input("   Enter phase flip rate (0 to 100): "))
            
        #     phase_flip_rate = int(phase_flip_rate)

        #     bcd_list = _bcd_of_value(phase_flip_rate)
        #     message_length = len(bcd_list)       

        #     tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_PS_RATE,message_length,MESSAGE_EOF])
            
        #     for i in range(0,len(bcd_list)):
        #         tx_array.insert((3+i),bcd_list[i])

        #     comm.send_message_to_panel(tx_array)

        #     logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))
        #     print("Command sent to panel: ", str(binascii.b2a_hex(tx_array)))

        #     bintoascii_data_str = comm.read_serial()

        #     logging.info("Panel Response: " + bintoascii_data_str)
        #     print("Panel Response: ", bintoascii_data_str)

        # #---------------------------------------------------------------#
        # # Perform self-test 
        # #---------------------------------------------------------------#
        # elif(message_id == MESSAGE_ID_SELF_TEST):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting panl perform self-test.")
            
        #     tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_SELF_TEST,0x00,MESSAGE_EOF])
        #     comm.send_message_to_panel(tx_array)
        #     logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))

        #     bintoascii_data_str = comm.read_serial()

        #     logging.info("Panel Response: " + bintoascii_data_str)
        #     print("Panel Response: ", bintoascii_data_str)
            
        #     print ("Self Test Byte: ", bintoascii_data_str[6:8])
        #     logging.info("Self Test Byte: " + bintoascii_data_str[6:8])
            


        # #---------------------------------------------------------------#
        # # Calibration status
        # #---------------------------------------------------------------#
        # elif(message_id == MESSAGE_ID_CAL_STATUS):      
        #     logging.info("---------------------------------------------------")
        #     logging.info("Inquiring panel of its calibration status.")

        #     tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_CAL_STATUS,0x00,MESSAGE_EOF])
        #     comm.send_message_to_panel(tx_array)
            
        #     logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))
        #     print("Command sent to panel: ", str(binascii.b2a_hex(tx_array)))
            
        #     bintoascii_data_str = comm.read_serial()

        #     logging.info("Panel Response: " + bintoascii_data_str)
        #     print("Panel Response: ", bintoascii_data_str)

        #     print("Calibration byte: ", bintoascii_data_str[6:8])
        #     logging.info("Calibration byte: " + bintoascii_data_str[6:8])

        # #---------------------------------------------------------------#
        # # PIC SW version request
        # #---------------------------------------------------------------#
        # elif(message_id == MESSAGE_ID_PIC_SW_VER):  
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting PIC SW version information.")
            
        #     tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_PIC_SW_VER,0x00,MESSAGE_EOF])
        #     comm.send_message_to_panel(tx_array)
        #     logging.info("SW version request message sent to panel: " + str(binascii.b2a_hex(tx_array)))
            
        #     bintoascii_data_str = comm.read_serial()

        #     logging.info("Panel Response: " + bintoascii_data_str)
        #     print("Panel Response: ", bintoascii_data_str)

        #     print ("PIC SW Version Number -- MAJOR:", bintoascii_data_str[6:10], " MINOR:", bintoascii_data_str[10:14], " MICRO:", bintoascii_data_str[14:18])
        #     logging.info("PIC SW Version Number -- MAJOR:" + bintoascii_data_str[6:10] + " MINOR:" + bintoascii_data_str[10:14] + " MICRO:" + bintoascii_data_str[14:18])
        
        # #---------------------------------------------------------------#
        # # CPLD FW version request
        # #---------------------------------------------------------------#
        # elif(message_id == MESSAGE_ID_CPLD_FW_VER):  
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting CPLD FW version information.")
            
        #     tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_CPLD_FW_VER,0x00,MESSAGE_EOF])
        #     comm.send_message_to_panel(tx_array)
        #     logging.info("FW version request message sent to panel: " + str(binascii.b2a_hex(tx_array)))
            
            
        #     bintoascii_data_str = comm.read_serial()

        #     logging.info("Panel Response: " + bintoascii_data_str)
        #     print("Panel Response: ", bintoascii_data_str)
            
        #     print ("CPLD FW Version Number -- HIGH BYTE:", bintoascii_data_str[7].strip() + bintoascii_data_str[9].strip(),
        #      " LO BYTE:", bintoascii_data_str[11].strip() + bintoascii_data_str[13].strip())
            
        #     logging.info ("CPLD FW Version Number -- HIGH BYTE:" + bintoascii_data_str[7].strip() + bintoascii_data_str[9].strip() +
        #      " LO BYTE:" + bintoascii_data_str[11].strip() + bintoascii_data_str[13].strip())
            

        # #---------------------------------------------------------------#
        # # Request Currents 
        # #---------------------------------------------------------------#
        # elif(message_id == MESSAGE_ID_TSL_1E_CURR):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting TSL 1E current.")

        #     _read_exciter_current(message_id)
        
        # elif(message_id == MESSAGE_ID_TSR_1E_CURR):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting TSR 1E current.")
            
        #     _read_exciter_current(message_id)
        
        # elif(message_id == MESSAGE_ID_TSR_2E_CURR):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting TSR 2E current.")
            
        #     _read_exciter_current(message_id)

        
        # elif(message_id == MESSAGE_ID_TSL_2E_CURR):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting TSL 2E current.")
            
        #     _read_exciter_current(message_id)

        # elif(message_id == MESSAGE_ID_IDd_1E_CURR):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting IDd 1E current.")
        #     _read_exciter_current(message_id)

        # elif(message_id == MESSAGE_ID_IDd_2E_CURR):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting IDd 2E current.")
        #     _read_exciter_current(message_id)

        # elif(message_id == MESSAGE_ID_IDg_1E_CURR):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting IDg 1E current.")
        #     _read_exciter_current(message_id)
        
        # elif(message_id == MESSAGE_ID_IDg_2E_CURR):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting IDg 1E current.")
        #     _read_exciter_current(message_id)

        # elif(message_id == MESSAGE_ID_PSA_1E_CURR):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting PSA 1E current.")
        #     _read_exciter_current(message_id)

        # elif(message_id == MESSAGE_ID_PSB_1E_CURR):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Requesting PSB 1E current.")
        #     _read_exciter_current(message_id)

        # #---------------------------------------------------------------#
        # # Configure signal relays 
        # #---------------------------------------------------------------#
        # elif(message_id == MESSAGE_ID_SIG_RLY_CONFIG):          
        #     logging.info("---------------------------------------------------")
        #     logging.info("Configuring interface panel signal relays.")
            
        #     print ('')
        #     print ("   Enter 0 for #1 END and Lobby Door Test Relay OFF.")
        #     print ("   Enter 1 for #2 END and Lobby Door Test Relay OFF.")
        #     print ("   Enter 2 for TS disabled, but Lobby Door Test Relay ON.")
        #     print ("   Enter 3 to make a custom selection.")
        #     print ("   Enter 4 to DEENERGIZE ALL.")
        #     usr_input = int(input("     Enter selection: "))

        #     tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_SIG_RLY_CONFIG,0x05,MESSAGE_EOF])

        #     relay_enable = [0x00 for x in range (5)]
            
        #     if(usr_input == 0):
        #         relay_enable[BIT_OFFSET_TSL_1E_RLY]     =  0x01 
        #         relay_enable[BIT_OFFSET_TSL_2E_RLY]     =  0x00 
        #         relay_enable[BIT_OFFSET_TSR_1E_RLY]     =  0x01 
        #         relay_enable[BIT_OFFSET_TSR_2E_RLY]     =  0x00 
        #         relay_enable[BIT_OFFSET_IDTX_TST_RLY]   =  0x00 
                
        #     elif(usr_input == 1):
        #         relay_enable[BIT_OFFSET_TSL_1E_RLY]     =  0x00
        #         relay_enable[BIT_OFFSET_TSL_2E_RLY]     =  0x01 
        #         relay_enable[BIT_OFFSET_TSR_1E_RLY]     =  0x00 
        #         relay_enable[BIT_OFFSET_TSR_2E_RLY]     =  0x01 
        #         relay_enable[BIT_OFFSET_IDTX_TST_RLY]   =  0x00 
            
        #     elif(usr_input == 2):
        #         relay_enable[BIT_OFFSET_TSL_1E_RLY]     =  0x00
        #         relay_enable[BIT_OFFSET_TSL_2E_RLY]     =  0x00
        #         relay_enable[BIT_OFFSET_TSR_1E_RLY]     =  0x00 
        #         relay_enable[BIT_OFFSET_TSR_2E_RLY]     =  0x00 
        #         relay_enable[BIT_OFFSET_IDTX_TST_RLY]   =  0x01 
            
        #     elif(usr_input == 3):
        #         print ("   Enter binary representation for which relays to enable.")
        #         print ("   Format is TSL 1E | TSL 2E | TSR 1E | TSR 2E | LBY DOOR.")

        #         binary_input_data = '\0'

        #         while ((len(FIVE_DIG_BIN_NUM_RE.findall(binary_input_data)) != 1) or len(binary_input_data) != 5):
        #             binary_input_data = input("\n   Define which channels to enable (i.e. 10100) : ")

        #         relay_enable[BIT_OFFSET_TSL_1E_RLY]     =   int(binary_input_data[0])
        #         relay_enable[BIT_OFFSET_TSL_2E_RLY]     =   int(binary_input_data[1])
        #         relay_enable[BIT_OFFSET_TSR_1E_RLY]     =   int(binary_input_data[2]) 
        #         relay_enable[BIT_OFFSET_TSR_2E_RLY]     =   int(binary_input_data[3]) 
        #         relay_enable[BIT_OFFSET_IDTX_TST_RLY]   =   int(binary_input_data[4]) 
            
        #     elif(usr_input == 4):
        #         relay_enable[BIT_OFFSET_TSL_1E_RLY]     =  0x00 
        #         relay_enable[BIT_OFFSET_TSL_2E_RLY]     =  0x00 
        #         relay_enable[BIT_OFFSET_TSR_1E_RLY]     =  0x00 
        #         relay_enable[BIT_OFFSET_TSR_2E_RLY]     =  0x00 
        #         relay_enable[BIT_OFFSET_IDTX_TST_RLY]   =  0x00 
                     
        #     else:
        #         print ("\n   Your selection was invalid.")
        #         print ("\n   Enableing Track Signal 1E by default.")
                
        #         relay_enable[BIT_OFFSET_TSL_1E_RLY]     =  0x01 
        #         relay_enable[BIT_OFFSET_TSL_2E_RLY]     =  0x00 
        #         relay_enable[BIT_OFFSET_TSR_1E_RLY]     =  0x01 
        #         relay_enable[BIT_OFFSET_TSR_2E_RLY]     =  0x00 
        #         relay_enable[BIT_OFFSET_IDTX_TST_RLY]   =  0x00 

        #     # Insert relay enable data into tx_array
        #     for i in range(0,5):                        
        #         tx_array.insert((3+i),relay_enable[i])
            
        #     comm.send_message_to_panel(tx_array)
            
        #     logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))
        #     print("Command sent to panel: ", str(binascii.b2a_hex(tx_array)))
            
        #     bintoascii_data_str = comm.read_serial()
            
        #     logging.info("Panel Response: " + bintoascii_data_str)
        #     print("Panel Response: ", bintoascii_data_str)
        
        # #---------------------------------------------------------------#
        # # Query panel for status of signal relays 
        # #---------------------------------------------------------------#
        # elif(message_id == MESSAGE_ID_SIG_RLY_STATUS):          
        #     logging.info("---------------------------------------------------")
        #     logging.info("Querying interface panel for signal relay status.")
            
        #     tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_SIG_RLY_STATUS,0x00,MESSAGE_EOF])
            
        #     comm.send_message_to_panel(tx_array)
            
        #     logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))
        #     print ('')
        #     print("Command sent to panel: ", str(binascii.b2a_hex(tx_array)))
            
        #     bintoascii_data_str = comm.read_serial()
            
        #     logging.info("Panel Response: " + bintoascii_data_str)
        #     print("Panel Response: ", bintoascii_data_str)

        #     print ('')
        #     print ("TSL 1E Signal Relay: ", bintoascii_data_str[6].strip() + bintoascii_data_str[7].strip())
        #     print ("TSL 2E Signal Relay: ", bintoascii_data_str[8].strip() + bintoascii_data_str[9].strip())
        #     print ("TSR 1E Signal Relay: ", bintoascii_data_str[10].strip() + bintoascii_data_str[11].strip())
        #     print ("TSR 2E Signal Relay: ", bintoascii_data_str[12].strip() + bintoascii_data_str[13].strip())
        #     print ("Lobby Door Signal Relay: ", bintoascii_data_str[14].strip() + bintoascii_data_str[15].strip())

        #     print ('')

        # #---------------------------------------------------------------#
        # # Custom ramp speed up and back down
        # #---------------------------------------------------------------#
        # elif(message_id == CUSTOM_ID_RAMP_TACH):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Ramping tachometer up, then back down.")
            
        #     speed_value= 0xFF                         #Set a default value for while loop
        #     TachVal = 0xFF

        #     for i in range (1,400,1):       # Start, Stop, Increment Value
        #         speed_value = i
                
        #         bcd_list = _bcd_of_value(speed_value)
        #         message_length = len(bcd_list) + 1                       # Message length must include tach command byte which is entered next (see below)
                
        #         tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_SET_SPEED,message_length,MESSAGE_EOF])
                
        #         for i in range(0,len(bcd_list)):
        #             tx_array.insert((3+i),bcd_list[i])

        #         tx_array.insert(3,0x00)     # Define that both tachs shall be set to the target speed value 
            
        #         comm.send_message_to_panel(tx_array)
            
        #         logging.info("Current speed setting: " + str(speed_value))
        #         logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))
        #         print("Current speed setting: ", str(speed_value))
        #         print("Command sent to panel: ", str(binascii.b2a_hex(tx_array)))

        #         bintoascii_data_str = comm.read_serial()

        #         logging.info("Panel Response: " + bintoascii_data_str)
        #         print("Panel Response: ", bintoascii_data_str)
                
        #         time.sleep(0.200)

        #     for i in range (399,0,-1):
        #         speed_value = i
                
        #         bcd_list = _bcd_of_value(speed_value)
        #         message_length = len(bcd_list) + 1                       # Message length must include tach command byte which is entered next (see below)
                
        #         tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_SET_SPEED,message_length,MESSAGE_EOF])
                
        #         for i in range(0,len(bcd_list)):
        #             tx_array.insert((3+i),bcd_list[i])

        #         tx_array.insert(3,0x00)     # Define that both tachs shall be set to the target speed value 
            
        #         comm.send_message_to_panel(tx_array)
            
        #         logging.info("Current speed setting: " + str(speed_value))
        #         logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))
        #         print("Current speed setting: ", str(speed_value))
        #         print("Command sent to panel: ", str(binascii.b2a_hex(tx_array)))

        #         bintoascii_data_str = comm.read_serial()

        #         logging.info("Panel Response: " + bintoascii_data_str)
        #         print("Panel Response: ", bintoascii_data_str)
                
        #         time.sleep(0.01)
        
        # #---------------------------------------------------------------#
        # # Repeatedly send same speed value
        # #---------------------------------------------------------------#
        # elif(message_id == CUSTOM_ID_SEND_SPEED):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Repeatedly sending speed value.")


        #     print ('')
        #     speed_value = int(input("    What speed value shall be sent repeatedly: "))
        #     count_value = int(input("    How many times shall the value be sent: "))
            
        #     bcd_list = _bcd_of_value(speed_value)
        #     message_length = len(bcd_list) + 1                       # Message length must include tach command byte which is entered next (see below)
        #     tx_array = bytearray([MESSAGE_SOF,MESSAGE_ID_SET_SPEED,message_length,MESSAGE_EOF])
            
        #     for i in range(0,len(bcd_list)):
        #         tx_array.insert((3+i),bcd_list[i])

        #     tx_array.insert(3,0x00)     # Define that both tachs shall be set to the target speed value 

        #     message_counter = 1
            
        #     for i in range (1,count_value,1):       # Start, Stop, Increment Value
                
        #         comm.send_message_to_panel(tx_array)
            
        #         logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))
        #         logging.info("Message number: " +  str(message_counter))
        #         print("Command sent to panel: ", str(binascii.b2a_hex(tx_array)))
        #         print("Message number: ",  str(message_counter))

        #         bintoascii_data_str = comm.read_serial()

        #         logging.info("Panel Response: " + bintoascii_data_str)
        #         print("Panel Response: ", bintoascii_data_str)
                
        #         time.sleep(0.01)
        #         message_counter += 1

        # #---------------------------------------------------------------#
        # # Repeatedly send tach control message
        # #---------------------------------------------------------------#
        # elif(message_id == CUSTOM_ID_BLAST_MSG):
        #     logging.info("---------------------------------------------------")
        #     logging.info("Repeatedly sending tach control value.")

        #     print ('')
        #     count_value = int(input("    How many times shall the value be sent: "))
            
        #     tach_enable_nibble = 0x0A               # Enable nibble 1010

        #     message_length = 0x03                       # Always the case for this selection
        #     tx_array = bytearray([MESSAGE_SOF, MESSAGE_ID_TACH_CONTROL, message_length, tach_enable_nibble, 0x01, 0x01, MESSAGE_EOF])
            
        #     message_counter = 1

        #     for i in range (count_value):

        #         comm.send_message_to_panel(tx_array)
                
        #         print ("Command sent to panel: ", str(binascii.b2a_hex(tx_array)))
        #         print("Message number: ",  str(message_counter))
        #         logging.info("Command sent to panel: " + str(binascii.b2a_hex(tx_array)))
        #         logging.info("Message number: " +  str(message_counter))
                
        #         bintoascii_data_str = comm.read_serial()

        #         logging.info("Panel Response: " + bintoascii_data_str)
        #         print("Panel Response: ", bintoascii_data_str)

        #         message_counter += 1

        #         time.sleep(0.01)
        
        else:
            "Invalid selection."


    #---------------------------------------------------------------
    # CLOSE EVERYTHING DOWN
    #---------------------------------------------------------------
    comm.close_serial_port() #Close the serial port so we don't hose up the system.

    logging.info("---------------------------------------------------")
    logging.info("Application closing.")
    print("\n\n     Application closing.") 