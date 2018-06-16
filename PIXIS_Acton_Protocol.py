#!/usr/bin/python2

# This code will try to specifically replicate the previous Generation matlab
# code of the same name in the same structure/order. Previous comment blocks
# for sectioning will be carried forwards.

import serial
import time
import numpy as np
from PIL import Image
import datetime
import matplotlib.pyplot as plt

######################################################################
#Configuration of SP2300i parameters
######################################################################

start_wave = 1064
# grating 1 = 1800 grooves/mm Blz = 500nm, grating 2 = 300grooves/mm Blz = 750nm
start_grating = 2;

dynamic = 0 #keep capturing images if 1, or 1 image at a time if 0
exposure = 100 #in ms
gain = 1
# 1.) Always Closed 2.) Always Open 3.) Normal 4.) Open Before Trigger
shutter = 3;
shutterdelay = 0
n_image = 1
line_cam = 0 #Which line to view, average the whole image if zero

from picam import *
cam = picam()
cam.loadLibrary()
cam.getAvailableCameras()
cam.connect()

#TODO: mmc.loadSystemConfiguration ('MMConfig.cfg');

######################################################################
#Beginning of control parameters for SP2300i
######################################################################

ser = serial.Serial(baudrate=9600,port=SERIAL_PORT,timeout=0.1)

if start_grating == 1:
  grating_num = 1800
else:
  grating_num = 300

print 'Changing the grating to: %d' % grating_num
print 'Changing the wavelength to: %d' % start_wave
print 'Please wait for the changes to be made. Thanks!'
# goes to the central wavelength at the maximum speed
# returns a statement that indicates whether the command was followed
goto_nm_max_speed(ser, start_wave)
# sets the grating of choice
# returns a statement that indicates whether the command was followed
set_grating(ser, start_grating)
############################################################
### End of control parameters for SP2300i
############################################################


############################################################
### Beginning of Calibration Function
############################################################

# note: so far everything is in terms of mm
# number of pixels from the centre
nth_pixel = np.linspace(1,670,3)
# Central wavelength
_lambda = start_wave*1e-6
# pixel width um
x = 20*1e-3
# focal length mm
f = 300
# inclusion angle (degrees)
gamma = 30.3
# detector angle (degrees)
delta = 1.38
# diffraction order
m = 1
# distance between grooves in mm
d = 1/grating_num

# predicts the value of lambda at pixel n 
# these equations come from pages 503-505 of the WinSpec Software User
# Manual, version 2.4M
lambda_at_pixel = np.array([])

for i in nth_pixel:
  zeta_angle = i*x*np.cos(delta*np.pi/180.)/(f+i*x*np.sin(delta*np.pi/180.))
  zeta = np.arctan(zeta_angle)*180./np.pi
  #psi is the rotational angle of the grating
  psi = np.arcsin(m*_lambda/(2.*d*np.cos(gamma/2*np.pi/180.)))*180./np.pi
  lambda_prime = ( (d/m) * ( \
  np.sin( (psi-gamma/2.) *180./np.pi) + \
  np.sin( (psi + gamma/2. + zeta) * 180./np.pi) ) \
  ) * 1e-3
  lambda_at_pixel = np.append(lambda_at_pixel, lambda_prime)

# use linear regression to fit the data to a second degree polynomial,
# where it solves for the values of the coefficients
pixel_points = np.array([670.,1005,1340])
fit = np.polyfit(pixel_points, lambda_at_pixel,2)
true_lambda = np.array([])
# converts the pixel number to wavelength using the coefficients found
# above
for k in np.linspace(1,1340,1340):
  _lambda = (fit[0]*k^2 + fit[1]*k + fit[2])*1e+9
  true_lambda = np.append(true_lambda, _lambda)

############################################################
### End of Calibration Function
############################################################


############################################################
### Beginning of Camera Parameters, Image Acquisition, Subraction of
### Background Noise, and Graphing of Data
############################################################
# the above loads the configuration file. HOWEVER, this does not that the
# camera will read all of those values. We have to set the device to those
# specific values

# the following makes sure that the camera operates at the correct
# temperature
pixis_temp = float(cam.getParameter('CCDTemperature'))
print 'Initial Pixis Temperature: %f' % pixis_temp

while pixis_temp > -75. :
  pixis_temp = float(cam.getParameter('CCDTemperature'))
  print 'Wait for camera to cool to -75C. Current Temperature: %f' % pixis_temp
  time.sleep(5)

############################################################
### This next section asks the user to input parameters for the camera
### using propmts. More information about the camera functions can be found
### here: https://micro-manager.org/wiki/Micro-Manager_Programming_Guide
### and here: https://javadoc.imagej.net/Micro-Manager-Core/mmcorej/CMMCore.html
### There is another section within this one that is currently commented
### out. It simply prints out the camera settings so that you know you
### input them correctly.
############################################################

cam.setParameter('Exposure', exposure)
cam.setParameter('Gain', gain)

if shutter == 1:
  shutter = 'Always closed'
elif shutter == 2:
  shutter = 'Always Open'
elif shutter == 3:
  shutter = 'Normal'
else:
  shutter = 'Open Before Trigger'


cam.setParameter('ShutterMode', shutter)
cam.setParameter('ShutterCloseDelay', shutterdelay)

cam.sendConfiguration() # TODO: is this deviation from original code necessary?

############################################################
### End of camera parameters
############################################################

print 'Taking a background image. . .'
# the code for taking an image came from:
# https://micro-manager.org/wiki/Matlab_Configuration, and then some slight
# modifications were made
img = cam.readNFrames(N=1,timeout=100) #TODO: is this correct? \
#Assuming this returns a numpy 2D array then the following code *should* work
width = len(img[0,:])
height = len(img[:,0])
img  = img.transpose()

t = Image.fromarray(img)
#TODO: validate that the stuff missing from here is irrelevant
t.save('background_image.tif')

prompt = 'Input 1 when the lightsource is ready and running.\n\n'
while True:
  my_input = raw_input(prompt)
  if my_input == '1':
    break

print 'Camera will now take the images and the program will analyze them!'
for i in range(n_image):
  img = cam.readNFrames(N=1,timeout=100) #TODO: is this correct?
  img = img.transpose()
  img.show()
  now = datetime.datetime.now()
  full_name = now.strftime('Raw_Image_Data_%Y-%m-%dT%H-%M-%S.tif')
  
  t = Image.fromarray(img)
  t.save(fullname)

  current_image = t.convert('L')
  background_image = Image.open('background_image.tif').convert('L')
  difference = ImageChops.subtract(current_image, background_image)
  t = difference
  difference = np.array(difference).astype('float64')
  
  intensity = np.zeros(len(difference[0,:]))

  if line_cam == 0:
    for i in range(len(difference[0,:])):
      intensity[i] = np.sum(difference[:,i])/100
  else:
    for i in range(len(difference[0,:])):
      intensity[i] = difference[line_cam, i]
  
  #plot next...
  fig = plt.figure()
  fig.suptitle('corrected spectrum')
  ax = fig.add_subplot(111)

  ax.set_xlabel('Wavelength (nm)')
  ax.set_ylabel('Intensity')

  ax.plot(true_lambda, intensity)
  plt.show()

  current_date_time = now.strftime('%Y-%m-%dT%H-%M-%S')
  final_name = 'Calibrated_Image_No_Noise_' + current_date_time + '.tif'

  t.save(final_name)


print 'Program is finished, so at least this much hasn\'t gone wrong today!'

ser.close()
###########################################################
### End of Image Acquisition, Subraction of Background Noise, and Calibration
###########################################################


###########################################################################
### Functions for SP2300i 
### inspiration for this code came from: http://juluribk.com/2014/09/19/controlling-sp2150i-monochromator-with-pythonpyvisa/
### however, we changed the way that our device communicates with the
### computer as well as changed to code to run in matlab. As well, some of
### the functions were omitted because they were irrelevant to our device
###########################################################################
# the explanations for these functions can be found in the device manual
def get_nm(ser):
  ser.write('?NM')
  return ser.read()

def get_nm_per_min(ser):
  ser.write('?NM/MIN')
  return ser.read()

def get_serial_num(ser):
  ser.write('SERIAL')
  return ser.read()

def get_model_num(ser):
  ser.write('MODEL')
  return ser.read()

def goto_nm_max_speed(ser,nm):
  ser.write('%0.2f GOTO' % nm)
  return ser.read()

def get_turret(ser):
  ser.write('?TURRET')
  return ser.read()

def get_filter(ser):
  ser.write('?FILTER')
  return ser.read()

def get_grating(ser):
  ser.write('?GRATING')
  return ser.read()

def set_turret(ser, num):
  if num <= 2:
    ser.write(str(num) + ' TURRET')
    return ser.read()
  else:
    print 'There is no turret with this input'
  return None

def set_filter(ser,num):
  if num <= 6:
    ser.write(str(num)+' FILTER')
    val = ser.read()
    print 'Filter changed and waiting with additional delay...'
    time.sleep(1)
    print 'Done Waiting'
    return val
  else:
    print 'There is no filter with this input'
  return None

def set_grating(ser, num):
  if num <= 2:
    ser.write(str(num)+' GRATING')
    return ser.read()
  else:
    print 'There is no grating with this input'
  return None

def goto_nm_with_set_nm_per_min(ser, nm, nm_per_min):
  ser.write('%0.2f NM/MIN' % nm_per_min)
  ser.write('%0.2f >NM' % nm)
  char = 0
  while char != 1:
    ser.write('MONO-?DONE')
    char = ser.read()
    time.sleep(0.2)
  print 'Scan is done!'
  ser.write('MONO-STOP')
  ser.write('?NM')
  return ser.read()

def init_wavelength(ser, start_wave):
  ser.write('%0.2f INIT-WAVELENGTH' % start_wave)
  return ser.read()

def init_grating(ser, start_grating):
  ser.write('0.2f INIT-GRATING' % start_grating)
  return ser.read()

def init_srate(ser, start_rate):
  ser.write('0.2f INIT-SRATE' % start_rate)
  return ser.read()
############################################################
### End of Functions for SP2300i
############################################################
