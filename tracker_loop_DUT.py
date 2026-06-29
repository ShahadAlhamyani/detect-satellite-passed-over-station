import math
import os 
import struct
import csv
import json
from sgp4.api import Satrec
from sgp4.api import jday
from datetime import datetime, UTC
from datetime import datetime, timedelta #to increase time manually


class Tracker: 
    def __init__(self, arrival_time,f0_target, tle_filename,json_filename): 
        self.arrival_time = arrival_time 
        self.f0_target = f0_target 
        self.broken_packet = 0 

        with open(tle_filename, "r") as f:
            tle = f.readlines()

        self.sat = Satrec.twoline2rv(
            tle[1].strip(),
            tle[2].strip()
        )

        with open (json_filename, "r") as f:
            self.position_station = json.load(f) 



    def telemetry(self,filename):
        sync_marker = bytes.fromhex("1ACFFC1D") #bytes

        with open(filename, "r") as f: #Space path
            hex_data = f.read().strip() # hex_data to string

        data = bytes.fromhex(hex_data) #bytes
        all_packets = [] 
        
        for i in range(len(data) - 3): #i as int
            if data[i:i+4] == sync_marker:

                header = data[i+4:i+10] # 6-byte header

                APID = header[0:2]
                sequence_count= header[2:4]
                packet_length = header[4:6]


                remaining_packet_len = int.from_bytes(packet_length, "big") # bytes to integer
                remaining_packet = data[i+10 : i+10+remaining_packet_len] # packet payload bytes
                
                if len(remaining_packet) < 14:
                    self.broken_packet += 1
                    continue
                
                
                timestamp, sub_id, voltage, current, temp, crc = struct.unpack(
                    ">IHHHHH", remaining_packet   # unpack: I = 4bytes & H = 2bytes 
                )



                self.arrival_time = self.arrival_time + timedelta(minutes=1)

                all_packets.append({
                    "APID": APID,
                    "sequence_count": sequence_count,
                    "packet_length": packet_length,
                    "sat_time": timestamp,
                    "Subsystem ID": sub_id,
                    "current": current,
                    "Temperature":temp,
                    "CRC": crc,
                    "arrival_time": self.arrival_time,
                    "voltage": voltage
                })

                
        return all_packets 
   


    def satellite_position(self,packet):            
       
        arrival_time = packet["arrival_time"]

        jd, fr = jday(
            arrival_time.year,
            arrival_time.month,
            arrival_time.day,
            arrival_time.hour,
            arrival_time.minute,
            arrival_time.second
        )

        error, position, velocity = self.sat.sgp4(jd, fr)


        Vx, Vy, Vz = velocity  
        total_velocity = math.sqrt(Vx**2 + Vy**2 + Vz**2)
        
        elevation = 15
        status = "VISIBLE" if elevation > 10 else "NOT VISIBLE"

        return {
            "position": position,
            "velocity": velocity,
            "voltage": packet["voltage"],
            "arrival_time": packet["arrival_time"],
            "total_velocity": total_velocity,
            "status": status
        }

 


    def calculate_doppler_shift(self,result): #read ground station position 
        c = 300000000 #(speed of light)
        position_Satellite = result["position"]


        #Relative Position Vector(Rx,Ry,Rz)
        Rx = position_Satellite[0] - self.position_station["X_station"]
        Ry = position_Satellite[1] - self.position_station["y_station"]
        Rz = position_Satellite[2] - self.position_station["z_station"]

        R_Norm = math.sqrt(Rx**2 + Ry**2 + Rz**2)

        ux = Rx / R_Norm
        uy = Ry / R_Norm
        uz = Rz / R_Norm

        v_relative_km = (ux * result["velocity"][0] + uy * result["velocity"][1] + uz * result["velocity"][2])  
        v_relative_m = v_relative_km * 1000
    


        doppler_shift = (abs(v_relative_m / c)) * self.f0_target

        if v_relative_m > 0 : # there are some info related to Range Rate Extraction!
            received_frequency = self.f0_target + doppler_shift # blue shift

        else:
            received_frequency = self.f0_target - doppler_shift # red shift

        return {
        "doppler_shift": doppler_shift,
        "received_frequency": received_frequency
        }   





#---------main--------
arrival_time = datetime(2026, 6, 20, 7, 0)
f0_target = 437500000

traker = Tracker(
    arrival_time,
    f0_target,
    "../saudisat.tle",
    "../ground_station.json")

all_packets = traker.telemetry("../telemetry_log.bin")
for packet in all_packets:

    position_result = traker.satellite_position(packet)
    doppler_result = traker.calculate_doppler_shift(position_result)

    print(position_result["position"])
    print(position_result["velocity"])
    print(doppler_result["doppler_shift"])
    print(doppler_result["received_frequency"])


    # def writting_data(result,csv_filename,i,received_frequency,doppler_shift): 
    #     file_exists = os.path.exists(csv_filename)

    #     with open(csv_filename, "a", newline="") as csv_file:
    #         writer = csv.writer(csv_file) 

    #         if not file_exists:
    #             writer.writerow(
    #                 ["Voltage", "Arrival_Time", "Total_Velocity","Status","received_frequency","doppler_shift"]
    #             )
            
    #         writer.writerow([
    #             #result["packet_number"], 
    #             result["voltage"], 
    #             result["arrival_time"], 
    #             result["total_velocity"], 
    #             result["status"],
    #             received_frequency,
    #             doppler_shift
    #         ])
            
        

    # #   -------------------main-------------------      

    # print("""
    #     This code is designed to calculate the coordinates(x,y,z) with respect to center of earht and the speed of the satellite 
    #     It takes two inputs: TLM which is earth path, and telemetry file to calculate (Time + Volt) which is space path 
    #     This code was designed by Shahad Alhamyani, it's an open source feel free to use it!
    #     """)

    # #variables for now!
    # arrival_time = datetime(2026, 6, 20, 7, 0)


    # broken_packet = 0
    # packets, broken_packet_count = telemetry("../telemetry_log.bin", arrival_time, broken_packet)
    # f0_target = 437500000
    # v_relative = 6500

    # for i, p in enumerate(packets):

    #     result = satellite_position(p, "../saudisat.tle",broken_packet_count)

    #     print("\n==================== PACKET", i, "===================")
    #     print("Voltage:", result["voltage"])
    #     print("Arrival Time:", result["arrival_time"])
    #     print("Position:", result["position"])
    #     print("Velocity:", result["velocity"]) 
    #     print("total_velocity:", result["total_velocity"])
    #     print("status", result["status"])

    #     received_frequency,doppler_shift = calculate_doppler_shift(f0_target, v_relative, "../ground_station.json",result["position"],result["velocity"])
        
    #     writting_data(result,"../satellite_telemetry_log.csv",i,received_frequency,doppler_shift)


    # if broken_packet_count >= 1:
    #     print("\n================ Found Broken Packet ================")
    #     print(f"Skipping broken packet number {broken_packet_count}")

    #     #end the loop and increase time but no idea how to adjust it cause it's not global variable!
        