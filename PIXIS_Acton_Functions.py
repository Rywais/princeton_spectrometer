from time import sleep

STANDARD_DELAY = 0

def serial_read(ser):
  val = ""
  last_val_len = None
  tries_remaining = 5
  while True:
    val = val + ser.read()
    if len(val) > 0:
      last_val_len = len(val)
      break

  while True:
    sleep(0.01)
    val = val + ser.read()
    if len(val) == last_val_len and tries_remaining <= 0:
      break
    elif len(val) == last_val_len:
      tries_remaining = tries_remaining - 1
    else:
      last_val_len = len(val)
      tries_remaining = 5

  return val
###########################################################################
### Functions for SP2300i 
### inspiration for this code came from: http://juluribk.com/2014/09/19/controlling-sp2150i-monochromator-with-pythonpyvisa/
### however, we changed the way that our device communicates with the
### computer as well as changed to code to run in matlab. As well, some of
### the functions were omitted because they were irrelevant to our device
###########################################################################
# the explanations for these functions can be found in the device manual
def get_nm(ser):
  ser.write('?NM\r')
  sleep(STANDARD_DELAY)
  return ser.read()

def get_nm_per_min(ser):
  ser.write('?NM/MIN\r')
  sleep(STANDARD_DELAY)
  return ser.read()

def get_serial_num(ser):
  ser.write('SERIAL\r')
  sleep(STANDARD_DELAY)
  return ser.read()

def get_model_num(ser):
  ser.write('MODEL\r')
  sleep(STANDARD_DELAY)
  return ser.read()

def goto_nm_max_speed(ser,nm):
  ser.write('%0.2f GOTO\r' % nm)
  return serial_read(ser)
  #return ser.read_until('?')

def get_turret(ser):
  ser.write('?TURRET\r')
  sleep(STANDARD_DELAY)
  return ser.read()

def get_filter(ser):
  ser.write('?FILTER\r')
  sleep(STANDARD_DELAY)
  return ser.read()

def get_grating(ser):
  ser.write('?GRATING\r')
  sleep(STANDARD_DELAY)
  return ser.read()

def set_turret(ser, num):
  if num <= 2:
    ser.write(str(num) + ' TURRET\r')
    sleep(STANDARD_DELAY)
    return ser.read()
  else:
    print 'There is no turret with this input'
  return None

def set_filter(ser,num):
  if num <= 6:
    ser.write(str(num)+' FILTER\r')
    sleep(STANDARD_DELAY)
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
    ser.write(str(num)+' GRATING\r')
    sleep(STANDARD_DELAY)
    return serial_read(ser)
    #return ser.read_until()
  else:
    print 'There is no grating with this input'
  return None

def goto_nm_with_set_nm_per_min(ser, nm, nm_per_min):
  ser.write('%0.2f NM/MIN\r' % nm_per_min)
  ser.write('%0.2f >NM\r' % nm)
  char = 0
  while char != 1:
    ser.write('MONO-?DONE\r')
    char = ser.read()
    time.sleep(0.2)
  print 'Scan is done!'
  ser.write('MONO-STOP\r')
  ser.write('?NM\r')
  sleep(STANDARD_DELAY)
  return ser.read()

def init_wavelength(ser, start_wave):
  ser.write('%0.2f INIT-WAVELENGTH\r' % start_wave)
  sleep(STANDARD_DELAY)
  return ser.read()

def init_grating(ser, start_grating):
  ser.write('0.2f INIT-GRATING\r' % start_grating)
  sleep(STANDARD_DELAY)
  return ser.read()

def init_srate(ser, start_rate):
  ser.write('0.2f INIT-SRATE\r' % start_rate)
  sleep(STANDARD_DELAY)
  return ser.read()
############################################################
### End of Functions for SP2300i
############################################################
