import math
import os 
import struct
import csv
import json
from sgp4.api import Satrec
from sgp4.api import jday
from datetime import datetime, UTC
from datetime import datetime, timedelta #to increase time manually


#Note that there are many (commented printing lines) in the both function, they were for debugging,
#However i should have written them in the main in the first place so it would not taken much time to add the loop 

def telemetry(filename,arrival_time,broken_packet):
    sync_marker = bytes.fromhex("1ACFFC1D") #bytes

    with open(filename, "r") as f: #Space path
        hex_data = f.read().strip() # hex_data to string

    data = bytes.fromhex(hex_data) #bytes
    all_packets = [] 
    
    for i in range(len(data) - 3): #i as int
        if data[i:i+4] == sync_marker:
            #print("signal detected at index", i) #i int

            header = data[i+4:i+10] # 6-byte header
            #print("checking header now and its value is : ", header.hex()) #header.hex() as string
            #print("\n----------------------------------------------")

            APID = header[0:2]
            sequence_count= header[2:4]
            packet_length = header[4:6]

            # #debug reading bytes as hex
            # print(f"APID bytes              = {APID.hex()}") 
            # print(f"sequence_count bytes    = {sequence_count.hex()}")
            # print(f"packet_length bytes     = {packet_length.hex()}")

            remaining_packet_len = int.from_bytes(packet_length, "big") # bytes to integer
            remaining_packet = data[i+10 : i+10+remaining_packet_len] # packet payload bytes
            
            if len(remaining_packet) < 14:
                broken_packet_count = 1 + broken_packet
                #print("Skipping broken packet")
                continue
            
            
            timestamp, sub_id, voltage, current, temp, crc = struct.unpack(
                ">IHHHHH", remaining_packet   # unpack: I = 4bytes & H = 2bytes 
            )


            # print(f"Timestamp               = {timestamp}")
            # print(f"Subsystem ID            = {sub_id}")
            # print(f"Voltage Raw Value       = {voltage}")
            # print(f"Current                 = {current}")
            # print(f"Temperature             = {temp}")
            # print(f"CRC                     = {crc}")
            
            # dt = datetime.fromtimestamp(timestamp, tz=UTC)
            # print(f"data time is {dt}")


            #print(arrival_time.strftime("%H:%M"))
            #arrival_time_inc = timedelta(minutes=1) + arrival_time

            arrival_time = arrival_time + timedelta(minutes=1)

            #print("----------------------------------------------\n")
            data_fusion = (voltage,arrival_time) # to be calculated on SGP4
            #all_packets.append(data_fusion) 

            all_packets.append({
                "APID": APID,
                "sequence_count": sequence_count,
                "packet_length": packet_length,
                "sat_time": timestamp,
                "Subsystem ID": sub_id,
                "current": current,
                "Temperature":temp,
                "CRC": crc,
                "arrival_time": arrival_time,
                "voltage": voltage,
                #"broken_packet":broken_packet
            })

            #no need
            #arrival_time = arrival_time_inc
    return all_packets,broken_packet_count
            



def satellite_position(packet,filename,broken_packet_count):            
    with open (filename, "r") as f: #Earth path 
        tle = f.readlines() # string

    line0 = tle[0].split()
    line1 = tle[1].strip()
    line2 = tle[2].strip()

    # print(f"Your satellite name is {line0[0]} and its TLE Data is below")
    # print(line1)
    # print(line2)
    # print()

    #print(f" Note that the voltage and arrival time are {data_fusion}\n") 

    sat = Satrec.twoline2rv(line1, line2) # create SGP4 satellite object


    arrival_time = packet["arrival_time"]

    jd, fr = jday(
        arrival_time.year,
        arrival_time.month,
        arrival_time.day,
        arrival_time.hour,
        arrival_time.minute,
        arrival_time.second
    )

    error, position, velocity = sat.sgp4(jd, fr)


    Vx, Vy, Vz = velocity  
    total_velocity = math.sqrt(Vx**2 + Vy**2 + Vz**2)
    
    elevation = 15
    status = "VISIBLE" if elevation > 10 else "NOT VISIBLE"

    #print(f"Satellite position is {r} km \nSatellite velocity is {v} km/s \nerror is {error} \n")
    return {
        "position": position,
        "velocity": velocity,
        "voltage": packet["voltage"],
        "arrival_time": packet["arrival_time"],
        "broken_packet": broken_packet_count,
        "total_velocity": total_velocity,
        "status": status
    }


def calculate_doppler_shift(f0, relative_velocity,filename,position,velocity): #read ground station position 
    with open (filename, "r") as f:
        position_station = json.load(f) 
    c = 300000000
    position_Satellite = position

    #add logic of relative velocity here


    #Relative Position Vector(Rx,Ry,Rz)
    Rx = position_Satellite[0] - position_station["X_station"]
    Ry = position_Satellite[1] - position_station["y_station"]
    Rz = position_Satellite[2] - position_station["z_station"]

    R_Norm = math.sqrt(Rx**2 + Ry**2 + Rz**2)

    ux = Rx / R_Norm
    uy = Ry / R_Norm
    uz = Rz / R_Norm

    v_relative_km = (ux*velocity[0] + uy*velocity[1] + uz*velocity[2])  
    v_relative_m = v_relative_km * 1000
 


    doppler_shift = (abs(v_relative_m / c)) * f0

    if v_relative_m > 0 : ## there are some info related to Range Rate Extraction!
        received_frequency = f0 + doppler_shift # blue shift

    else:
        received_frequency = f0 - doppler_shift # red shift

    print(f"Doppler Shift: {doppler_shift:.2f} Hz | Received Frequency: {received_frequency:.2f} Hz")    
    return doppler_shift, received_frequency




    #extend()doppler_shift, received_frequency to be result oorr save result after function name :0




def writting_data(result,csv_filename,i,received_frequency,doppler_shift): 
    file_exists = os.path.exists(csv_filename)

    with open(csv_filename, "a", newline="") as csv_file:
        writer = csv.writer(csv_file) 

        if not file_exists:
            writer.writerow(
                ["Voltage", "Arrival_Time", "Total_Velocity","Status","received_frequency","doppler_shift"]
            )
        
        writer.writerow([
            #result["packet_number"], 
            result["voltage"], 
            result["arrival_time"], 
            result["total_velocity"], 
            result["status"],
            received_frequency,
            doppler_shift
        ])
           
    

#   -------------------main-------------------      

print("""
    This code is designed to calculate the coordinates(x,y,z) with respect to center of earht and the speed of the satellite 
    It takes two inputs: TLM which is earth path, and telemetry file to calculate (Time + Volt) which is space path 
    This code was designed by Shahad Alhamyani, it's an open source feel free to use it!
    """)

#variables for now!
arrival_time = datetime(2026, 6, 20, 7, 0)


broken_packet = 0
packets, broken_packet_count = telemetry("../telemetry_log.bin", arrival_time, broken_packet)
f0_target = 437500000
v_relative = 6500

for i, p in enumerate(packets):

    result = satellite_position(p, "../saudisat.tle",broken_packet_count)

    print("\n==================== PACKET", i, "===================")
    print("Voltage:", result["voltage"])
    print("Arrival Time:", result["arrival_time"])
    print("Position:", result["position"])
    print("Velocity:", result["velocity"]) 
    print("total_velocity:", result["total_velocity"])
    print("status", result["status"])

    received_frequency,doppler_shift = calculate_doppler_shift(f0_target, v_relative, "../ground_station.json",result["position"],result["velocity"])
    
    writting_data(result,"../satellite_telemetry_log.csv",i,received_frequency,doppler_shift)


if broken_packet_count >= 1:
    print("\n================ Found Broken Packet ================")
    print(f"Skipping broken packet number {broken_packet_count}")

    #end the loop and increase time but no idea how to adjust it cause it's not global variable!
    