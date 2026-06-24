import math

# this is DSP team work calcultaing frequency IQ samples 

iq_samples = [ #(I + jQ)
    complex(1.0, 0.0),  
    complex(0.0, 1.0), 
    complex(-1.0, 0.0), 
    complex(0.0, -1.0)  
]
prev_theta = 0
sample_rate = 2400000

for sample in iq_samples :
    I = sample.real
    Q = sample.imag

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
