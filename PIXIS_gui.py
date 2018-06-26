#!/usr/bin/python2
import Tkinter as tk
from PIXIS_gui_function import use_spectrometer

root = tk.Tk()
root.geometry('500x300')
root.resizable(width=False,height=False)

#TODO: Add error handling

#Tk variables
serial_port = tk.StringVar()
start_wave = tk.StringVar() #To be converted to integer using int()
start_grating = tk.IntVar() #(1 or 2 = 1800 or 300 resp.)
bool_picam = tk.BooleanVar()
bool_background = tk.BooleanVar()

#set initial values


def call_spectrometer():
  func_serial_port = serial_port.get()
  func_start_wave = int(start_wave.get())
  func_start_grating = start_grating.get()
  func_bool_picam = bool_picam.get()
  func_bool_background = bool_background.get()
  use_spectrometer(func_serial_port,
                   func_start_wave,
                   func_start_grating,
                   func_bool_picam,
                   func_bool_background)


#Serial Port
tk.Label(root,
         text="""Serial Port
Examples:
- COM4
- /dev/ttyUSB0""",
         justify=tk.LEFT).place(x=10,y=10)
tk.Entry(root, textvariable=serial_port, width=20).place(x=10,y=80)

#Start Wave
tk.Label(root,
         text="Center Wavelength",
         justify = tk.LEFT).place(x=10,y=130)
tk.Entry(root, textvariable=start_wave, width=10).place(x=10,y=150)

#Start Grating
tk.Label(root,
         text = "Start Grating:",
         justify = tk.LEFT).place(x=250,y=30)
tk.Radiobutton(root,
               text="300 (400 < Wavelength < 1800)",
               variable=start_grating,
               value=2).place(x=250,y=50)
tk.Radiobutton(root,
               text="1800 (400 < Wavelength < 1100)",
               variable=start_grating,
               value=1).place(x=250,y=70)

#PICAM or Micromanager
tk.Label(root,
         text = "Use PICAM or Micro-Manager?",
         justify = tk.LEFT).place(x=250,y=110)
tk.Radiobutton(root,
               text="PICAM",
               variable=bool_picam,
               value=True).place(x=250,y=130)
tk.Radiobutton(root,
               text="Micro-Manager",
               variable=bool_picam,
               value=False).place(x=250,y=150)

#Take New background image or not:
tk.Label(root,
         text = "Take new Background image?",
         justify = tk.LEFT).place(x=250,y=190)
tk.Radiobutton(root,
               text="Yes",
               variable=bool_background,
               value=True).place(x=250,y=210)
tk.Radiobutton(root,
               text="No",
               variable=bool_background,
               value=False).place(x=250,y=230)

#Button to run the program:
tk.Button(root,
          text="Run",
          command = call_spectrometer,
          width=20,
          height=3).place(x=10,y=210)

tk.mainloop()
