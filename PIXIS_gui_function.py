import serial
import time
import numpy as np
from PIL import Image
from PIL import ImageChops
import datetime
import matplotlib.pyplot as plt
import PIXIS_Acton_Functions as pix
from tkMessageBox import *
from picam import *
import my_globals
try:
  import MMCorePy
except ImportError:
  pass

def use_spectrometer(ser,
                     start_wave=900,
                     start_grating=1,
                     shutter_status=3,
                     shutter_delay=0,
                     exposure=100,
                     bool_picam=True,
                     bool_background=1):
  ######################################################################
  ### Python code specific User Parameters
  ######################################################################
  
  SERIAL_PORT = ser
  
  ######################################################################
  #Configuration of SP2300i parameters
  ######################################################################
  
  # grating 1 = 1800 grooves/mm Blz = 500nm, grating 2 = 300grooves/mm Blz = 750nm

  
  dynamic = 0 #keep capturing images if 1, or 1 image at a time if 0
  gain = 1
  # 1.) Always Closed 2.) Always Open 3.) Normal 4.) Open Before Trigger
  shutter = shutter_status
  shutterdelay = shutter_delay
  n_image = 1
  line_cam = 0 #Which line to view, average the whole image if zero
  
  global mmc
  global cam
  
  try:
    mmc
  except NameError:
    mmc_exists = False
  else:
    mmc_exists = True
  
  try:
    cam
  except NameError:
    cam_exists = False
  else:
    cam_exists = True
  
  #Code will be split like this between the two implementations as necessary
  if bool_picam and cam_exists == False:
    cam = picam()
    cam.loadLibrary()
    cam.getAvailableCameras()
    cam.connect()
  elif bool_picam == False and mmc_exists == False:
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration ('MMConfig.cfg');
  

  ######################################################################
  #Beginning of control parameters for SP2300i
  ######################################################################
  
  global gui_serial
  
  try:
    gui_serial
  except NameError:
    ser_exists = False
  else:
    ser_exists = True
  
  if ser_exists == False:
    gui_serial = serial.Serial(baudrate=9600,port=SERIAL_PORT,timeout=20)
  
  if start_grating == 1:
    grating_num = 1800
  else:
    grating_num = 300
  
  print 'Changing the grating to: %d' % grating_num
  print 'Changing the wavelength to: %d' % start_wave
  print 'Please wait for the changes to be made. Thanks!'
  # goes to the central wavelength at the maximum speed
  # returns a statement that indicates whether the command was followed
  pix.goto_nm_max_speed(gui_serial, start_wave)
  # sets the grating of choice
  # returns a statement that indicates whether the command was followed
  pix.set_grating(gui_serial, start_grating)
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
  d = 1./grating_num
  
  # predicts the value of lambda at pixel n 
  # these equations come from pages 503-505 of the WinSpec Software User
  # Manual, version 2.4M
  lambda_at_pixel = np.array([])
  
  # Non-functional, just use Matlab values below
  for i in nth_pixel:
    zeta_angle = i*x*np.cos(delta*np.pi/180.)/(f+i*x*np.sin(delta*np.pi/180.))
    zeta = np.arctan(zeta_angle)*180./np.pi
    #psi is the rotational angle of the grating
    psi = np.arcsin(m*_lambda/(2.*d*np.cos(gamma/2*np.pi/180.)))*180./np.pi
    lambda_prime = ( (d/m) * ( \
    np.sin( (psi-gamma/2.) *np.pi/180.) + \
    np.sin( (psi + gamma/2. + zeta) * np.pi/180.) ) \
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
    _lambda = (fit[0]*k*k + fit[1]*k + fit[2])*1e+9
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

  if bool_picam:
    pixis_temp = float(cam.getParameter('SensorTemperatureReading'))
    
    if pixis_temp > -75. :
      showinfo('CCD Cooling','Please wait for the CCD to cool to -75C, and try again')
      return

    while pixis_temp > -75. :
      pixis_temp = float(cam.getParameter('SensorTemperatureReading'))
      time.sleep(5)
  else:
    pixis_temp = float(mmc.getProperty('PIXIS','CCDTemperature'))

    if pixis_temp > -75. :
      showinfo('CCD Cooling','Please wait for the CCD to cool to -75C, and try again')
      return

    while pixis_temp > -75. :
      pixis_temp = float(mmc.getProperty('PIXIS','CCDTemperature'))
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
  
  if bool_picam:
    cam.setParameter('ExposureTime', exposure)
    cam.setParameter('AdcAnalogGain', gain)
    
    if shutter == 1:
      shutter = 'Always closed'
      shutter = 2 #In compliance with PICAM library
    elif shutter == 2:
      shutter = 'Always Open'
      shutter = 3
    elif shutter == 3:
      shutter = 'Normal'
      shutter = 1
    else:
      shutter = 'Open Before Trigger'
      shutter = 4
    
    
    cam.setParameter('ShutterTimingMode', shutter)
    cam.setParameter('ShutterClosingDelay', shutterdelay)
    
    cam.sendConfiguration() 
  else:
   mmc.setProperty('PIXIS','Exposure',exposure);
   mmc.setProperty('PIXIS','Gain',gain)

   if shutter == 1:
     shutter = 'Always closed'
   elif shutter == 2:
     shutter = 'Always Open'
   elif shutter == 3:
     shutter = 'Normal'
   else:
     shutter = 'Open Before Trigger'

   mmc.setProperty('PIXIS','ShutterMode',shutter)
   mmc.setProperty('PIXIS','ShutterCloseDelay',shutterdelay);
  #End of if/else block

  ############################################################
  ### End of camera parameters
  ############################################################
  if bool_background == 1:
    # the code for taking an image came from:
    # https://micro-manager.org/wiki/Matlab_Configuration, and then some slight
    # modifications were made
    img = None
    if bool_picam:
      img = cam.readNFrames(N=1,timeout=5000)
      
      width = 1340
      height = 100
    else:
      mmc.snapImage()
      img = mmc.getImage()
      width = mmc.getImageWidth()
      height = mmc.getImageHeight()
  
    
    #Erase extraneous dimesnions to treat image as 2D numpy array
    if bool_picam:
      img = np.array(img)
      img = np.squeeze(img)
      img = np.reshape(img,(height,width)) 
      img = img.astype('uint16')
      
      t = Image.fromarray(img, mode='I;16')
      t.save('background_image.tif')
      t.close()
      my_file = open('background.npy', 'w')
      np.save(my_file, img)
      my_file.close()
    else:
      img = np.array(img)
  
      img = np.reshape(img, (height,width))
      img = img.astype('uint32')
  
      t = Image.fromarray(img.astype('uint16'), mode='I;16')
      t.save('background_image.tif')
      t.close()
      my_file = open('background.npy', 'w')
      np.save(my_file, img)
      my_file.close()
    #End of if/else block
    
    background_array = img
  else:
    width=1340
    height=100
  #End of Background acquisition block
  
  while True:
    if askyesno('Verify','Is Light Source Ready?'):
      break
  
  for i in range(n_image):
    if bool_picam:
      img = cam.readNFrames(N=1,timeout=5000)
      img = np.array(img)
      img = np.squeeze(img)
      img = np.reshape(img,(height,width)) 
      img = img.astype('uint16')
    else:
      mmc.snapImage()
      img = mmc.getImage()
      width = mmc.getImageWidth()
      height = mmc.getImageHeight()
      img = np.array(img)
      img = np.reshape(img, (height,width))
      img = img.astype('uint32')
    now = datetime.datetime.now()
    fullname = now.strftime('Raw_Image_Data_%Y-%m-%dT%H-%M-%S.tif')
    
    t = Image.fromarray(img.astype('uint16'), mode='I;16')
    t.save(fullname)
    t.close()
  
    #Ryan's approach using Saved Numpy Arrays
    if bool_background == 0:
      background_array = np.load('background.npy')

    if bool_background != 2:
      difference = img.astype('int32') - background_array.astype('int32')
    else:
      difference = img.astype('int32')
    difference = (difference.clip(min=0)).astype('uint32')
    t = Image.fromarray(difference)
  
    
    intensity = np.zeros(len(difference[0,:]))

    if line_cam == 0:
      for i in range(len(difference[0,:])):
        intensity[i] = np.sum(difference[:,i].astype('float64'))/100.
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
    t.close()
  
  if bool_picam:
    #cam.disconnect()
    #cam.unloadLibrary()
    pass
  else:
    pass #What to do for releasing Micromanager Resources?
  #ser.close()

  
  ###########################################################
  ### End of Image Acquisition, Subraction of Background Noise, and Calibration
  ###########################################################

def set_shutter_status(shutter_status=3,bool_picam=True):
  shutter = shutter_status

  global mmc
  global cam
  
  try:
    mmc
  except NameError:
    mmc_exists = False
  else:
    mmc_exists = True
  
  try:
    cam
  except NameError:
    cam_exists = False
  else:
    cam_exists = True
  
  if bool_picam and cam_exists == False:
    cam = picam()
    cam.loadLibrary()
    cam.getAvailableCameras()
    cam.connect()
  elif bool_picam == False and mmc_exists == False:
    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration ('MMConfig.cfg');

  if bool_picam:
    if shutter == 1:
      shutter = 'Always closed'
      shutter = 2 #In compliance with PICAM library
    elif shutter == 2:
      shutter = 'Always Open'
      shutter = 3
    elif shutter == 3:
      shutter = 'Normal'
      shutter = 1
    else:
      shutter = 'Open Before Trigger'
      shutter = 4
    
    
    cam.setParameter('ShutterTimingMode', shutter)
    cam.sendConfiguration() 
  else:
   if shutter == 1:
     shutter = 'Always closed'
   elif shutter == 2:
     shutter = 'Always Open'
   elif shutter == 3:
     shutter = 'Normal'
   else:
     shutter = 'Open Before Trigger'

   mmc.setProperty('PIXIS','ShutterMode',shutter)
  #End of if/else block

  if bool_picam:
    #cam.disconnect()
    #cam.unloadLibrary()
    pass
  else:
    pass #What to do for releasing Micromanager Resources?

def set_monochromator(serial_port="", center_wave=900, grating=1):
  global gui_serial
  
  try:
    gui_serial
  except NameError:
    ser_exists = False
  else:
    ser_exists = True
  
  if ser_exists == False:
    gui_serial = serial.Serial(baudrate=9600,port=serial_port,timeout=20)

  if grating == 1:
    grating_num = 1800
  else:
    grating_num = 300
  
  # goes to the central wavelength at the maximum speed
  # returns a statement that indicates whether the command was followed
  pix.goto_nm_max_speed(gui_serial, center_wave)
  # sets the grating of choice
  # returns a statement that indicates whether the command was followed
  pix.set_grating(gui_serial, grating)

def start_cooling(bool_picam):
  pass
