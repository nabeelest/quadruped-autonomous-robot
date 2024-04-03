#!/usr/bin/env python3

import time
from math import *
import busio
import RPi.GPIO as GPIO
from board import SCL, SDA
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
import numpy as np
import curses

# Servo angle limits
servo_min = 0 # Minimum servo angle (degrees)
servo_max = 180  # Maximum servo angle (degrees)

# Servo offsets Left Front (for your specific configuration)
foot_offset_LF = -30  
leg_offset_LF = 10
shoulder_offset_LF = 5

# Servo offsets Left Back (for your specific configuration)
foot_offset_LB = -30  
leg_offset_LB = 10
shoulder_offset_LB = -5

# Servo offsets Right Front (for your specific configuration)
foot_offset_RF = 30  
leg_offset_RF = -10
shoulder_offset_RF = 10

# Servo offsets Right Back (for your specific configuration)
foot_offset_RB = 30  
leg_offset_RB = -10
shoulder_offset_RB = 10


def bodyIK(omega,phi,psi,xm,ym,zm):

    L = 220
    W = 110

    Rx = np.array([
        [1, 0, 0, 0], 
        [0, np.cos(omega), -np.sin(omega), 0],
        [0,np.sin(omega),np.cos(omega),0],
        [0,0,0,1]])

    Ry = np.array([
        [np.cos(phi),0, np.sin(phi), 0], 
        [0, 1, 0, 0],
        [-np.sin(phi),0, np.cos(phi),0],
        [0,0,0,1]])

    Rz = np.array([
        [np.cos(psi),-np.sin(psi), 0,0], 
        [np.sin(psi),np.cos(psi),0,0],
        [0,0,1,0],
        [0,0,0,1]])

    Rxyz=Rx@Ry@Rz

    T = np.array([[0,0,0,xm],[0,0,0,ym],[0,0,0,zm],[0,0,0,0]])
    Tm = T+Rxyz

    Trb = Tm @ np.array([
        [np.cos(pi/2),0,np.sin(pi/2),-L/2],
        [0,1,0,0],
        [-np.sin(pi/2),0,np.cos(pi/2),-W/2],
        [0,0,0,1]])

    Trf = Tm @ np.array([
        [np.cos(pi/2),0,np.sin(pi/2),L/2],
        [0,1,0,0],
        [-np.sin(pi/2),0,np.cos(pi/2),-W/2],
        [0,0,0,1]])

    Tlf = Tm @ np.array([
        [np.cos(pi/2),0,np.sin(pi/2),L/2],
        [0,1,0,0],
        [-np.sin(pi/2),0,np.cos(pi/2),W/2],
        [0,0,0,1]])

    Tlb = Tm @ np.array([
        [np.cos(pi/2),0,np.sin(pi/2),-L/2],
        [0,1,0,0],
        [-np.sin(pi/2),0,np.cos(pi/2),W/2],
        [0,0,0,1]])

    return (Tlf,Trf,Tlb,Trb,Tm)

# Inverse Kinematics for Left Front function
def LeftFrontIK(point):
    try:
        (x, y, z) = (point[0], point[1], point[2])

        # Constant lengths in mm
        upper_leg = 120
        lower_leg = 120
        shoulder_leg = 60

        y1 = sqrt(y*y + z*z - shoulder_leg*shoulder_leg)
        
        distance = sqrt(x*x + y1*y1)

        foot = acos((distance*distance - upper_leg*upper_leg - lower_leg*lower_leg)/(-2*upper_leg*lower_leg))
        
        leg = asin((lower_leg*sin(foot))/distance) - (atan(x/y) if y!=0 else 0)

        shoulder_leg = atan(distance/shoulder_leg) + atan(z/y)
    

        # Convert radians to degrees and add servo offsets
        foot_LF =  (foot/pi * 180) + foot_offset_LF
        leg_LF = (leg/pi * 180) + leg_offset_LF
        shoulder_LF = 180 - (shoulder_leg/pi * 180) + shoulder_offset_LF

        # Check if angles are within servo limits
        if (servo_min <= foot_LF <= servo_max) and (servo_min <= leg_LF <= servo_max) and (servo_min <= shoulder_LF <= servo_max):
            return foot_LF, leg_LF, shoulder_LF
        else:
            print("Error: Servo angles are out of bounds")
            print("Moving to ({}, {}, {})".format(x, y, z))
            print("FootLF angle:", foot_LF)
            print("LegLF angle:", leg_LF)
            print("ShoulderLF angle:", shoulder_LF)
            return None, None, None

    except ValueError as e:
        print("Error:", e)
        return None, None, None

# Inverse Kinematics for Left Back function
def LeftBackIK(point):
    try:
        (x, y, z) = (point[0], point[1], point[2])

        # Constant lengths in mm
        upper_leg = 120
        lower_leg = 120
        shoulder_leg = 60

        y1 = sqrt(y*y + z*z - shoulder_leg*shoulder_leg)
        
        distance = sqrt(x*x + y1*y1)

        foot = acos((distance*distance - upper_leg*upper_leg - lower_leg*lower_leg)/(-2*upper_leg*lower_leg))
        
        leg = asin((lower_leg*sin(foot))/distance) - (atan(x/y) if y!=0 else 0)

        shoulder_leg = atan(distance/shoulder_leg) + atan(z/y)
    

        # Convert radians to degrees and add servo offsets
        foot_LB =  (foot/pi * 180) + foot_offset_LB
        leg_LB = (leg/pi * 180) + leg_offset_LB
        shoulder_LB = 180 - (shoulder_leg/pi * 180) + shoulder_offset_LB

        # Check if angles are within servo limits
        if (servo_min <= foot_LB <= servo_max) and (servo_min <= leg_LB <= servo_max) and (servo_min <= shoulder_LB <= servo_max):
            return foot_LB, leg_LB, shoulder_LB
        else:
            print("Error: Servo angles are out of bounds")
            print("Moving to ({}, {}, {})".format(x, y, z))
            print("FootLB angle:", foot_LB)
            print("LegLB angle:", leg_LB)
            print("ShoulderLB angle:", shoulder_LB)
            return None, None, None

    except ValueError as e:
        print("Error:", e)
        return None, None, None
    

# Inverse Kinematics for Right Back function
def RightBackIK(point):
    try:    
        (x, y, z) = (point[0], point[1], point[2])

        # Constant lengths in mm
        upper_leg = 120
        lower_leg = 120
        shoulder_leg = 60

        y1 = sqrt(y*y + z*z - shoulder_leg*shoulder_leg)
        
        distance = sqrt(x*x + y1*y1)

        foot = acos((distance*distance - upper_leg*upper_leg - lower_leg*lower_leg)/(-2*upper_leg*lower_leg))
        
        leg = asin((lower_leg*sin(foot))/distance) - (atan(x/y) if y!=0 else 0)

        shoulder_leg = atan(distance/shoulder_leg) + atan(z/y)
    

        # Convert radians to degrees and add servo offsets
        foot_RB = 180 - (foot/pi * 180) + foot_offset_RB
        leg_RB = 180 - (leg/pi * 180) + leg_offset_RB
        shoulder_RB = (shoulder_leg/pi * 180) + shoulder_offset_RB

        # Check if angles are within servo limits
        if (servo_min <= foot_RB <= servo_max) and (servo_min <= leg_RB <= servo_max) and (servo_min <= shoulder_RB <= servo_max):
            return foot_RB, leg_RB, shoulder_RB
        else:
            print("Error: Servo angles are out of bounds")
            print("Moving to ({}, {}, {})".format(x, y, z))
            print("FootRB angle:", foot_RB)
            print("LegRB angle:", leg_RB)
            print("ShoulderRB angle:", shoulder_RB)
            return None, None, None
    except ValueError as e:
        print("Error:", e)
        return None, None, None
    
# Inverse Kinematics for Right Front function
def RightFrontIK(point):
    try:
        (x, y, z) = (point[0], point[1], point[2])

        # Constant lengths in mm
        upper_leg = 120
        lower_leg = 120
        shoulder_leg = 60

        y1 = sqrt(y*y + z*z - shoulder_leg*shoulder_leg)
        
        distance = sqrt(x*x + y1*y1)

        foot = acos((distance*distance - upper_leg*upper_leg - lower_leg*lower_leg)/(-2*upper_leg*lower_leg))
        
        leg = asin((lower_leg*sin(foot))/distance) - (atan(x/y) if y!=0 else 0)

        shoulder_leg = atan(distance/shoulder_leg) + atan(z/y)
    

        # Convert radians to degrees and add servo offsets
        foot_RF = 180 - (foot/pi * 180) + foot_offset_RF
        leg_RF = 180 - (leg/pi * 180) + leg_offset_RF
        shoulder_RF = (shoulder_leg/pi * 180) + shoulder_offset_RF

        # Check if angles are within servo limits
        if (servo_min <= foot_RF <= servo_max) and (servo_min <= leg_RF <= servo_max) and (servo_min <= shoulder_RF <= servo_max):
            return foot_RF, leg_RF, shoulder_RF
        else:
            print("Error: Servo angles are out of bounds")
            print("Moving to ({}, {}, {})".format(x, y, z))
            print("FootRF angle:", foot_RF)
            print("LegRF angle:", leg_RF)
            print("ShoulderRF angle:", shoulder_RF)
            return None, None, None
    except ValueError as e:
        print("Error:", e)
        return None, None, None


# Initialize GPIO
GPIO.setmode(GPIO.BCM)
gpio_port = 18  # Change this to your desired GPIO port
GPIO.setup(gpio_port, GPIO.OUT)
GPIO.output(gpio_port, False)

# Initialize PCA9685
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# Set up curses
stdscr = curses.initscr()
curses.cbreak()
stdscr.keypad(True)

if __name__ == "__main__":
    try:

        # Set up PCA9685 servo controller Left Front
        shoulder_servo_LF = servo.Servo(pca.channels[12])
        leg_servo_LF = servo.Servo(pca.channels[0])
        foot_servo_LF = servo.Servo(pca.channels[1])
        # Set up PCA9685 servo controller Left Back
        shoulder_servo_LB = servo.Servo(pca.channels[8])
        leg_servo_LB = servo.Servo(pca.channels[2])
        foot_servo_LB = servo.Servo(pca.channels[3])

        # Set up PCA9685 servo controller Right Front
        shoulder_servo_RF = servo.Servo(pca.channels[13])
        leg_servo_RF = servo.Servo(pca.channels[4])
        foot_servo_RF = servo.Servo(pca.channels[5])

        # Set up PCA9685 servo controller Right Back
        shoulder_servo_RB = servo.Servo(pca.channels[9])
        leg_servo_RB = servo.Servo(pca.channels[6])
        foot_servo_RB = servo.Servo(pca.channels[7])

        # Set pulse width range for Left servos
        shoulder_servo_LF.set_pulse_width_range(min_pulse=500, max_pulse=2500)
        leg_servo_LF.set_pulse_width_range(min_pulse=500, max_pulse=2500)
        foot_servo_LF.set_pulse_width_range(min_pulse=500, max_pulse=2500)
        shoulder_servo_LB.set_pulse_width_range(min_pulse=500, max_pulse=2500)
        leg_servo_LB.set_pulse_width_range(min_pulse=500, max_pulse=2500)
        foot_servo_LB.set_pulse_width_range(min_pulse=500, max_pulse=2500)

        # Set pulse width range for Right servos
        shoulder_servo_RF.set_pulse_width_range(min_pulse=500, max_pulse=2500)
        leg_servo_RF.set_pulse_width_range(min_pulse=500, max_pulse=2500)
        foot_servo_RF.set_pulse_width_range(min_pulse=500, max_pulse=2500)
        shoulder_servo_RB.set_pulse_width_range(min_pulse=500, max_pulse=2500)
        leg_servo_RB.set_pulse_width_range(min_pulse=500, max_pulse=2500)
        foot_servo_RB.set_pulse_width_range(min_pulse=500, max_pulse=2500)



        x = 0
        z = 60
        
        omega = 0
        phi = 0
        psi = 0

        xm = 0
        ym = 0
        zm = 0

        p = [0,100,60,1]

        # Lp=np.array([[170,  y,55,1],[170, y,-55,1],[-50,y, 55,1],[-50, y,-55,1]])
        # Lp = np.array([[100, -100, 100, 1], [100, -100, -100, 1], [-100, -100, 100, 1], [-100, -100, -100, 1]])


        (Tlf,Trf,Tlb,Trb,Tm) = bodyIK(omega,phi,psi,xm,ym,zm)
        
        # print(Trf@p)
        # print(Tlf@p)
        # print(Trb@p)
        # print(Tlb@p)


        FP=[0,0,0,1]
        CP=[x@FP for x in [Tlf,Trf,Tlb,Trb]]
        # print(CP)

        # Invert local X
        Ix=np.array([[-1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
        # print(np.linalg.inv(Tlf) @ Lp[0])
        # Qlf=LeftFrontIK((np.linalg.inv(Tlf) @ Lp[0]))
        # # Point Left Back
        # Qlb=LeftBackIK(np.linalg.inv(Tlb) @ Lp[2])
        # # print(Qlb)
        # # # Point Right Front
        # Qrf=RightFrontIK(np.linalg.inv(Trf) @ Lp[1])
        # # print(Qrf)
        # # # Point Right Back
        # Qrb= RightBackIK(np.linalg.inv(Trb) @ Lp[3])

        y = 170
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Use arrow keys to move. Press q to quit.")
            print("here")
            key = stdscr.getch()
            if key == curses.KEY_RIGHT:
                # if ym > -5:
                    # x -= 5
                    # psi -= 0.01
                zm -= 1
            elif key == curses.KEY_LEFT:
                # if ym < 5:
                    # x += 5
                    #  += 0.01
                zm += 1
            elif key == ord('q'):
                break

            Lp=np.array([[170, 170,55,1],[170, 170,-55,1],[-50,170, 55,1],[-50, 170,-55,1]])
            (Tlf,Trf,Tlb,Trb,Tm) = bodyIK(omega,phi,psi,xm,ym,zm)


    

            foot_LF, leg_LF, shoulder_LF = LeftFrontIK((np.linalg.inv(Tlf) @ Lp[0]))
            foot_LB, leg_LB, shoulder_LB = LeftBackIK(np.linalg.inv(Tlb) @ Lp[2])
            foot_RF, leg_RF, shoulder_RF = RightFrontIK(Ix @ np.linalg.inv(Trf) @ Lp[1])
            foot_RB, leg_RB, shoulder_RB = RightBackIK(Ix @ np.linalg.inv(Trb) @ Lp[3])

        
        
            if foot_LF is not None and leg_LF is not None and shoulder_LF is not None and foot_LB is not None and leg_LB is not None and shoulder_LB is not None and foot_RF is not None and leg_RF is not None and shoulder_RF is not None and foot_RB is not None and leg_RB is not None and shoulder_RB is not None:
                # print("FootLFq angle:{}, LegLF angle:{},ShoulderLF angle:{}".format(foot_LF,leg_LF,shoulder_LF))
                # print("FootLB angle:{}, LegLB angle:{},ShoulderLB angle:{}".format(foot_LB,leg_LB,shoulder_LB))
                # print("FootRF angle:{}, LegRF angle:{},ShoulderRF angle:{}".format(foot_RF,leg_RF,shoulder_RF))
                # print("FootRB angle:{}, LegRB angle:{},ShoulderRB angle:{}".format(foot_RB,leg_RB,shoulder_RB))


                    # Move Left Front servos to calculated angles
                shoulder_servo_LF.angle = shoulder_LF 
                leg_servo_LF.angle = leg_LF 
                foot_servo_LF.angle = foot_LF 

                    # Move Left Back servos to calculated angles
                shoulder_servo_LB.angle = shoulder_LB
                leg_servo_LB.angle = leg_LB
                foot_servo_LB.angle = foot_LB
                
                # Move Right Front servos to calculated angles
                shoulder_servo_RF.angle = shoulder_RF 
                leg_servo_RF.angle = leg_RF 
                foot_servo_RF.angle = foot_RF 
            
                # Move Right Back servos to calculated angles
                shoulder_servo_RB.angle = shoulder_RB
                leg_servo_RB.angle = leg_RB
                foot_servo_RB.angle = foot_RB

    except KeyboardInterrupt:
        pass