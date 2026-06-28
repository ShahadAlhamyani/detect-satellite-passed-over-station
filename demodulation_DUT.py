import math

# this is DSP team work calcultaing frequency IQ samples 
modulation_type = "QPSK"
extracted_bits = []

iq_samples = [ #(I + jQ)
    complex(1.0, 1.0),  
    complex(1.0, -1.0), 
    complex(-1.0, 1.0), 
    complex(-1.0, -1.0)  
]
prev_theta = 0
sample_rate = 2400000

for sample in iq_samples :
    I = sample.real  # horizontal axis
    Q = sample.imag  # vertical axis 

    if modulation_type == "BPSK" :
        if I >= 0 :
            extracted_bits.append ("1")       
        elif I < 0 :
            extracted_bits.append ("0")
    
    elif modulation_type == "QPSK":  #  gray Coding
        if I > 0 and Q > 0 :
            extracted_bits.append ("00")
        elif I < 0 and Q > 0 : 
            extracted_bits.append ("01")
        elif I < 0 and Q < 0 :
            extracted_bits.append ("11")
        elif I > 0 and Q < 0 : 
            extracted_bits.append ("10")
            

    amplitude = math.sqrt(I**2 + Q**2)
    theta = math.atan2(Q,I)
    theta_deg = math.degrees(theta)

    
    delta_theta =  theta_deg - prev_theta
    prev_theta = theta_deg

    # unwrapping
    if delta_theta < -180 :
        delta_theta = delta_theta + 360
    elif delta_theta > 180 :
        delta_theta = delta_theta - 360    

    frequency = (delta_theta / 360) * sample_rate  

    print(f"Amplitude = {amplitude}")
    print(f"Theta = {theta_deg:.1f}")
    print(f"delta theta = {delta_theta:.1f}")
    print(f"frequency = {frequency} Hz")
    print()


