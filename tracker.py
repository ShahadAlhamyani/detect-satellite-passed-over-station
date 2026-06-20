import math
import os 
import struct
from sgp4.api import Satrec
from sgp4.api import jday

def telemetry(filename):
    sync_marker = bytes.fromhex("1ACFFC1D") #bytes

    with open(filename, "r") as f:
        hex_data = f.read().strip() # hex_data to string

    data = bytes.fromhex(hex_data) #bytes

    for i in range(len(data) - 3): #i as int
        if data[i:i+4] == sync_marker:
            print("signal detected at index", i) #i int

            header = data[i+4:i+10] # 6-byte header
            print("checking header now and its value is : ", header.hex()) #header.hex() as string
            print("\n----------------------------------------------")

            APID = header[0:2]
            sequence_count= header[2:4]
            packet_length = header[4:6]

            #debug reading bytes as hex
            print(f"APID bytes              = {APID.hex()}") 
            print(f"sequence_count bytes    = {sequence_count.hex()}")
            print(f"packet_length bytes     = {packet_length.hex()}")

            remaining_packet_len = int.from_bytes(packet_length, "big") # bytes to integer
            remaining_packet = data[i+10 : i+10+remaining_packet_len] # packet payload bytes
            
            timestamp, sub_id, voltage, current, temp, crc = struct.unpack(
                ">IHHHHH", remaining_packet   # unpack: I = 4bytes & H = 2bytes 
            )

            arrival_time = "7:00" #variable for now

            print(f"Timestamp               = {timestamp}")
            print(f"Subsystem ID            = {sub_id}")
            print(f"Voltage Raw Value       = {voltage}")
            print(f"Current                 = {current}")
            print(f"Temperature             = {temp}")
            print(f"CRC                     = {crc}")
            
            print("----------------------------------------------\n")

            data_fusion = (voltage,arrival_time) # to be calculated on SGP4
            return data_fusion


def satellite_position(data_fusion,filename):            
    with open (filename, "r") as f:
        tle = f.readlines() # string

    line0 = tle[0].split()
    line1 = tle[1].strip()
    line2 = tle[2].strip()

    print(f"Your satellite name is {line0[0]} and its TLE Data is below")
    print(line1)
    print(line2)
    print()

    print(f" Note that the voltage and arrival time are {data_fusion}\n") 

    sat = Satrec.twoline2rv(line1, line2) # create SGP4 satellite object

    jd, fr = jday(2026, 6, 20, 12, 30, 0) # Julian date and fractional day

    error, r, v = sat.sgp4(jd, fr)

    print(f"Satellite position is {r} km \nSatellite velocity is {v} km/s \nerror is {error} \n")

      

#main

print("""
    This code is designed to calculate the coordinates(x,y,z) with respect to center of earht and the speed of the satellite 
    It takes two inputs: TLM which is earth path, and telemetry file to calculate (Time + Volt) which is space path 
    This code was designed by Shahad Alhamyani, it's an open source feel free to use it!
    """)

data =  telemetry("../telemetry_log.bin")
tle = satellite_position(data,"../saudisat.tle")

