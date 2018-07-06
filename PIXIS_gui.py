#!/usr/bin/python2
import Tkinter as tk
from PIXIS_gui_function import *

root = tk.Tk()
root.geometry('500x760')
root.resizable(width=False,height=False)

#TODO: Add error handling

#Tk variables
serial_port = tk.StringVar()
start_wave = tk.StringVar() #To be converted to integer using float()
exposure = tk.StringVar() #To be converted to integer using int()
n_images = tk.StringVar() #To be converted to integer using int()
shutter_delay = tk.StringVar() #To be converted to integer using int()
start_grating = tk.IntVar() #(1 or 2 = 1800 or 300 resp.)
bool_picam = tk.BooleanVar()
bool_background = tk.IntVar()
shutter_mode = tk.IntVar()
save_fig = tk.BooleanVar()
line_cam = tk.StringVar()

#set initial values
serial_port.set('COM4')
shutter_mode.set(3)
bool_picam.set(True)
bool_background.set(1)
start_grating.set(2)
start_wave.set('900')
exposure.set('100')
n_images.set('1')
shutter_delay.set('0')
save_fig.set(False)
line_cam.set('0')

#Temperature Update Function
def update_temperature():
  #Update CCD Temperature Display
  if (time.time() - my_time) > 0.5 and picam_button["state"] == 'disabled':
    if bool_picam.get() == True:
      pixis_temp = int(float(cam.getParameter('SensorTemperatureReading')))
    else:
      pixis_temp = int(float(mmc.getProperty('PIXIS','CCDTemperature')))
    temperature_status.set('CCD Temperature: ' + str(pixis_temp))
    my_time = time.time()
  root.after(1000,update_temperature)

#Functions to be called by button presses
def call_spectrometer():
  for i in disable_list:
    i.config(state=tk.DISABLED)
  func_serial_port = serial_port.get()
  func_start_wave = float(start_wave.get())
  func_start_grating = start_grating.get()
  func_bool_picam = bool_picam.get()
  func_bool_background = bool_background.get()
  func_shutter_status = shutter_mode.get()
  func_shutter_delay = int(shutter_delay.get())
  func_exposure = int(exposure.get())
  func_bool_save_fig = save_fig.get()
  func_line_cam = int(line_cam.get())
  func_n_image = int(n_images.get())
  use_spectrometer(ser=func_serial_port,
                   start_wave=func_start_wave,
                   start_grating=func_start_grating,
                   shutter_status=func_shutter_status,
                   shutter_delay=func_shutter_delay,
                   exposure=func_exposure,
                   bool_picam=func_bool_picam,
                   bool_background=func_bool_background,
                   bool_save_fig=func_bool_save_fig,
                   n_image=func_n_image,
                   line_cam=func_line_cam)

def call_spectrometer_cts():
  for i in disable_list:
    i.config(state=tk.DISABLED)
  func_serial_port = serial_port.get()
  func_start_wave = float(start_wave.get())
  func_start_grating = start_grating.get()
  func_bool_picam = bool_picam.get()
  func_bool_background = bool_background.get()
  func_shutter_status = shutter_mode.get()
  func_shutter_delay = int(shutter_delay.get())
  func_exposure = int(exposure.get())
  func_bool_save_fig = save_fig.get()
  func_line_cam = int(line_cam.get())
  func_n_image = int(n_images.get())
  live_spectrometer(ser=func_serial_port,
                   start_wave=func_start_wave,
                   start_grating=func_start_grating,
                   shutter_status=func_shutter_status,
                   shutter_delay=func_shutter_delay,
                   exposure=func_exposure,
                   bool_picam=func_bool_picam,
                   bool_background=func_bool_background,
                   bool_save_fig=func_bool_save_fig,
                   n_image=func_n_image,
                   line_cam=func_line_cam)

def call_shutter_mode():
  for i in disable_list:
    i.config(state=tk.DISABLED)
  func_shutter_mode = shutter_mode.get()
  func_bool_picam = bool_picam.get()
  set_shutter_status(shutter_status=func_shutter_mode,
                     bool_picam=func_bool_picam)

def call_set_monochromator():
  for i in disable_list:
    i.config(state=tk.DISABLED)
  func_center_wave = float(start_wave.get())
  func_start_grating = start_grating.get()
  func_serial_port = serial_port.get()
  set_monochromator(serial_port=func_serial_port,
                    center_wave=func_center_wave,
                    grating=func_start_grating)

def reset_monochromator():
  func_center_wave = float(start_wave.get())
  func_serial_port = serial_port.get()
  set_monochromator(serial_port=func_serial_port,
                    center_wave=func_center_wave,
                    grating=1)
  

############################################################
### Monochromator Section ##################################
############################################################

#Monochromator Label
tk.Label(root,
         text="Monochromator Settings",
         font='Verdana 16 bold',
         justify = tk.LEFT).place(x=10,y=10)

#Start Wave
tk.Label(root,
         text="Center Wavelength",
         justify = tk.LEFT).place(x=10,y=40)
tk.Entry(root, textvariable=start_wave, width=10).place(x=10,y=60)

#Start Grating
tk.Label(root,
         text = "Start Grating:",
         justify = tk.LEFT).place(x=10,y=90)
tk.Radiobutton(root,
               text="300 (400 < Wavelength < 1800)",
               variable=start_grating,
               value=2).place(x=10,y=108)
tk.Radiobutton(root,
               text="1800 (400 < Wavelength < 1100)",
               variable=start_grating,
               value=1).place(x=10,y=126)

#Button to run the program:
tk.Button(root,
          text="Set Monochromator",
          command = call_set_monochromator,
          width=20,
          height=3).place(x=250,y=90)

############################################################
### CCD Section ############################################
############################################################

#CCD Label
tk.Label(root,
         text="CCD Settings",
         font='Verdana 16 bold',
         justify = tk.LEFT).place(x=10,y=160)

#Select Shutter Mode
tk.Label(root,
         text="Shutter Mode",
         justify = tk.LEFT).place(x=10,y=200)
tk.Radiobutton(root,
                text="Normal",
                variable=shutter_mode,
                value=3).place(x=10,y=220)
tk.Radiobutton(root,
                text="Always Closed",
                variable=shutter_mode,
                value=1).place(x=10,y=240)
tk.Radiobutton(root,
                text="Always Open",
                variable=shutter_mode,
                value=2).place(x=10,y=260)
tk.Radiobutton(root,
                text="Open Before Trigger",
                variable=shutter_mode,
                value=4).place(x=10,y=280)

#Button to run the program:
tk.Button(root,
          text="Set Shutter Mode",
          command = call_shutter_mode,
          width=20,
          height=3).place(x=250,y=240)

############################################################
### Take Image Section #####################################
############################################################

#Image Label
tk.Label(root,
         text="Image Settings",
         font='Verdana 16 bold',
         justify = tk.LEFT).place(x=10,y=320)

#Serial Port
tk.Label(root,
         text="""Serial Port
Examples:
- COM4
- /dev/ttyUSB0""",
         justify=tk.LEFT).place(x=250,y=380)
serial_entry = tk.Entry(root, textvariable=serial_port, width=20)
serial_entry.place(x=250,y=440)

#PICAM or Micromanager
tk.Label(root,
         text = "Use PICAM or Micro-Manager?",
         justify = tk.LEFT).place(x=10,y=360)
picam_button = tk.Radiobutton(root,
               text="PICAM",
               variable=bool_picam,
               value=True)
picam_button.place(x=10,y=380)
mm_button = tk.Radiobutton(root,
               text="Micro-Manager",
               variable=bool_picam,
               value=False)
mm_button.place(x=10,y=400)

#Exposure
tk.Label(root,
         text="Exposure (ms)",
         justify = tk.LEFT).place(x=10,y=440)
tk.Entry(root, textvariable=exposure, width=10).place(x=10,y=460)

#Number of Images
tk.Label(root,
         text="Number of images to take:",
         justify = tk.LEFT).place(x=250,y=480)
tk.Entry(root, textvariable=n_images, width=10).place(x=250,y=500)

#Shutter Delay
tk.Label(root,
         text="Shutter Delay:",
         justify = tk.LEFT).place(x=10,y=500)
tk.Entry(root, textvariable=shutter_delay, width=10).place(x=10,y=520)

#Take New background image or not:
tk.Label(root,
         text = "Take new Background image?",
         justify = tk.LEFT).place(x=10,y=560)
tk.Radiobutton(root,
               text="Yes",
               variable=bool_background,
               value=1).place(x=10,y=580)
tk.Radiobutton(root,
               text="No",
               variable=bool_background,
               value=0).place(x=10,y=600)
tk.Radiobutton(root,
               text="Don't use background image",
               variable=bool_background,
               value=2).place(x=10,y=620)

#Line cam
tk.Label(root,
         text="Line Cam (0 for averaging)",
         justify = tk.LEFT).place(x=10,y=660)
tk.Entry(root, textvariable=line_cam, width=10).place(x=10,y=680)

#Start Grating
tk.Label(root,
         text = "Save Plots?",
         justify = tk.LEFT).place(x=10,y=700)
tk.Radiobutton(root,
               text="Yes",
               variable=save_fig,
               value=True).place(x=10,y=720)
tk.Radiobutton(root,
               text="No",
               variable=save_fig,
               value=False).place(x=10,y=740)

#Button to take images:
tk.Button(root,
          text="Take Image(s)",
          command = call_spectrometer,
          width=20,
          height=3).place(x=250,y=560)

#Button to take images:
tk.Button(root,
          text="Continuous View",
          command = call_spectrometer_cts,
          width=20,
          height=3).place(x=250,y=640)

#global disabled_list
disable_list = (serial_entry,picam_button,mm_button)

root.protocol("WM_DELETE_WINDOW", reset_monochromator)
root.mainloop()
