#!/usr/bin/env python
# captures and publishes the rudder and sail winch servo positions as pulse width in ms
# (used to be duty cycle which doesn't make sense for a servo)

# topics
# /rudder rudder pulse width in ms, right/starboard is smaller value, left/port is higher value
# /sail position, in smaller, out larger

import rospy
from std_msgs.msg import Float64
import serial
import RPi.GPIO as GPIO
import time
import numpy as np

def getTimex():
	return time.time()

channel1 = rospy.Publisher('sail', Float64, queue_size=10)
channel2 = rospy.Publisher('rudder', Float64, queue_size=10)
rospy.init_node('pwm', anonymous=True,log_level=rospy.INFO)
rate = rospy.Rate(10) # sample rate in Hz

inPINS=[18,23] #pinnumbers that are used(BCM nameingconvention)
smoothingWindowLength=1 # number of samples to box filter over


GPIO.setmode(GPIO.BCM)
GPIO.setup(inPINS, GPIO.IN)
upTimes = [[0] for i in range(len(inPINS))]
downTimes = [[0] for i in range(len(inPINS))]
deltaTimes = [[0] for i in range(len(inPINS))]

def my_callback1(channel):
	i=inPINS.index(channel)
	v=GPIO.input(inPINS[i])
	if (v==0): # falling edge
		downTimes[i].append(getTimex())
		if len(downTimes[i])>smoothingWindowLength: del downTimes[i][0]
                deltaTimes[i].append(1e3*(downTimes[i][-1]-upTimes[i][-1])) # delta time in seconds
	else: # rising edge
		upTimes[i].append(getTimex())
		if len(upTimes[i])>smoothingWindowLength: del upTimes[i][0]
	if len(deltaTimes[i])>smoothingWindowLength: del deltaTimes[i][0]



GPIO.add_event_detect(inPINS[0], GPIO.BOTH, callback=my_callback1)	#channel 1
GPIO.add_event_detect(inPINS[1], GPIO.BOTH, callback=my_callback1)	#channel 2
#GPIO.add_event_detect(inPINS[2], GPIO.BOTH, callback=my_callback1)	#channel 3
#GPIO.add_event_detect(inPINS[3], GPIO.BOTH, callback=my_callback1)	#channel 4

rospy.loginfo("Initialization completed")

def pwm():
	try:
		while not rospy.is_shutdown():

			ovl1 = deltaTimes[0][-smoothingWindowLength:]
			ov1 = sorted(ovl1)[len(ovl1) // 2]

			ovl2 = deltaTimes[1][-smoothingWindowLength:]
			ov2 = sorted(ovl2)[len(ovl2) // 2]

			#ovl3 = deltaTimes[2][-smoothingWindowLength:]
			#ov3 = sorted(ovl3)[len(ovl3) // 2]

			#ovl4 = deltaTimes[3][-smoothingWindowLength:]
			#ov4 = sorted(ovl4)[len(ovl4) // 2]
			#time.sleep(0.1)
                        rospy.logdebug("pulse widths: sail: %.3f ms, rudder: %.3f ms",ov1,ov2)

			channel1.publish(ov1)
			channel2.publish(ov2)

			rate.sleep()
	except KeyboardInterrupt:
		GPIO.cleanup()
if __name__ == '__main__':
    try:
        pwm()
    except rospy.ROSInterruptException:
        pass

