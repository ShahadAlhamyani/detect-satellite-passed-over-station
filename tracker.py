import math
import os 
import struct

def telemetry(filename):
    sync_marker = bytes.fromhex("1ACFFC1D") #bytes as b'\xff

    with open(filename, "r") as f:
        hex_data = f.read().strip() # hex_data to string

    data = bytes.fromhex(hex_data) #bytes as b'\xff

    for i in range(len(data) - 3): #i as int
        if data[i:i+4] == sync_marker:
            print("signal detected at index", i) #i as int

            header = data[i+4:i+10] #bytes like data
            print("header:", header.hex()) #header.hex() as str

            APID = header[0:2]
            sequence_count= header[2:4]
            packet_length = header[4:6]

            #debug
            print(f"APID bytes = {APID.hex()}") 
            print(f"sequence_count bytes = {sequence_count.hex()}")
            print(f"packet_length bytes = {packet_length.hex()}")

            remaining_packet_len = int.from_bytes(packet_length, "big")
            remaining_packet = data[i+10 : i+10+remaining_packet_len]
            
            timestamp, sub_id, voltage, current, temp, crc = struct.unpack(
                ">IHHHHH", remaining_packet
            )

            arrival_time = "7:00" #variable for now

            print(f"Timestamp: {timestamp}")
            print(f"Subsystem ID: {sub_id}")
            print(f"Voltage Raw Value: {voltage}")
            print(f"Current: {current}")
            print(f"Temperature: {temp}")
            print(f"CRC: {crc}")

            data_fusion = (voltage,arrival_time)
            #def data_fusion(voltage,arrival_time,filename):         
            

            
       

#main
data =  telemetry("telemetry_log.bin") 
 
