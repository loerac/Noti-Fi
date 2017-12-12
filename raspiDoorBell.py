#!/usr/bin/python
#===========================================================+
# Desc: A simple program to read/write values from mariaDB  |
#       and display them on a Papirus screen                |
# Auth: Christian Loera                                     |
# Date: 25 Oct 2017                                         |
#===========================================================+
from __future__ import print_function

# Imports
# Paho 
import paho.mqtt.client as mqtt

# System
import os
import sys

# Image
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# Time
from datetime import datetime
from time import sleep

# Papirus
from papirus import Papirus
import RPi.GPIO as GPIO

# Threading
import multiprocessing

# Data size
MAX_DATA_SIZE=13

# Screen size
SIZE=27

hatdir = '/proc/device-tree/hat'
nameFont = '/usr/share/fonts/truetype/freefont/FreeMonoOblique.ttf'
dataFont = '/usr/share/fonts/truetype/freefont/FreeMono.ttf'

class Display:
    def __init__(self):
        self.screen = Screen()
        self.nameSize = self.screen.getNameSize()
        self.name = ""
        self.data = ""
        self.scroll = False
        self.nameList = []
        self.dataList = []
        self.scrollList = []
        self.run = 0
        self.mqttc = mqtt.Client()
        self.mqttc.on_message = self.on_message
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_publish = self.on_publish
        self.mqttc.on_subscribe = self.on_subscribe

        self.mqttc.connect("localhost",1883,60)
        self.mqttc.subscribe("Notifi/app-to-pi/#",0)
   
    # Client connects to server
    def on_connect(self,mqtt,obj,flags,rc):
        print("rc: " + str(rc))

    # Display what the client sends with their name and data
    def on_message(self,mqtt,obj,msg):
        name=msg.topic.split("Notifi/app-to-pi/")[1]
        data=msg.payload

        # Exit program only through linux command line
        if (name == "admin")and (data == "exit -n"):
            self.exit()
      
        # Change the size of the name if greater than 12
        self.nameOut(name)

        # If the Arduino sends a message, display only once
        if (name == "House"):
            self.screen.updateScreen(name,self.dataOut(data),self.scroll)
        else:
            # Else display the user data five times
            self.listStack(name,data,self.scroll)
            self.run = 5
            self.displayMessage()
        print(name + ": " + data)
       
    # Display what is on the list
    def displayMessage(self):
        if self.run:
            for i in range(len(self.nameList)): 
                self.nameOut(self.nameList[i])
                self.screen.updateScreen(self.nameList[i],self.dataOut(self.dataList[i]),self.scrollList[i])
                print(self.nameList[i] + ": " + self.dataList[i])
            self.run -= 1
        if not self.run:
            self.nameList = []
            self.dataList = []
            self.scrollList = []
    
    def on_publish(self,mqtt,obj,msg,mid):
        print("mid: " + str(mid))

    # When someone subscribes, list their number
    def on_subscribe(self,mqttc,obj,mid,granted_qos):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_log(self,mqttc,obj,level,string):
        print(string)
  
    # Continually loop to check clients
    def mqttLoop(self):
        self.mqttc.loop()

    # Make the name fit the screen
    def nameOut(self,n):
        self.nameSize = 37 if len(n) < 6 else (self.nameSize - 12)
        self.screen.setNameSize(self.nameSize)

    # Make the data from the message fit the screen
    def dataOut(self,d):
        if len(d) > 13:
            t=''
            s=''
            for i in range(len(d)):
                t+=d[i]
                if len(t)>=(MAX_DATA_SIZE+1):
                    r=t[::-1] # Reverse of t
                    m=''
                    j=0
                    while r[j]!=' ':
                        m+=r[j]
                        j+=1
                    s+=str(t[:len(t)-(j+1)])+"\n"
                    t=m[::-1]
            d = s + t
        # If the data is larger than 24,
        # Make the scroll up to read the rest
        self.scroll = True if len(d) > 24 else False
        return d
    
    # Creating a list with all the names and data
    def listStack(self,n,d,s):
        self.nameList.append(n)
        self.dataList.append(d)
        self.scrollList.append(s)

    # Exit raspiDoorBell.py
    def exit(self):
        self.screen.clearScreen()
        exit()

    # Display time when there is no client connected
    def displayTime(self):
        self.screen.displayTime()

# The class for the Paprius eInk Display
class Screen:    
    def __init__(self):
        # Check EPD_SIZE is defined
        EPD_SIZE=0.0
        if os.path.exists('/etc/default/epd-fuse'):
            exec(open('/etc/default/epd-fuse').read())
        if EPD_SIZE==0.0:
            print("Please select your screen size by running 'papirus-config'.")

        self.papirus=Papirus(rotation=0)
        self.papirus.clear()

        # Setting the screen color
        self.BLACK=0
        self.WHITE=1

        # Initally set all white background
        self.image=Image.new('1',self.papirus.size,self.WHITE)

        # Prepare for drawing
        self.draw=ImageDraw.Draw(self.image)
        self.width,self.height=self.image.size
        
        # Setting the size/font for the name
        self.nameSize=int((self.width-4)/(8*0.65))
        self.nameFont=ImageFont.truetype(nameFont,self.nameSize)

        # Setting the size/font for the data
        self.dataSize=int((self.width-MAX_DATA_SIZE)/(MAX_DATA_SIZE*0.65))
        self.dataFont=ImageFont.truetype(dataFont,self.dataSize)

        # Setting the size/font for time and date
        self.clockSize=int((self.width-4)/(8*0.65))
        self.clockFont=ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoOblique.ttf',self.clockSize)
        self.dateSize=int((self.width-10)/(10*0.65))
        self.dateFont=ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMono.ttf',self.dateSize)

    def updateScreen(self,n,d,s):
        self.image=Image.new('1',self.papirus.size,self.WHITE)
        self.draw=ImageDraw.Draw(self.image)

        # Display the data first
        self.draw.rectangle((0,0,self.papirus.size[0],self.papirus.size[1]), fill=self.WHITE, outline=self.WHITE)
        self.draw.text((5,self.dataSize+MAX_DATA_SIZE),('%s' %d), fill=self.BLACK, font=self.dataFont)

        # Display the name second
        self.draw.rectangle((3,3,self.width-3,self.nameSize),fill=self.WHITE, outline=self.WHITE)
        self.nameFont=ImageFont.truetype(nameFont,self.nameSize)
        self.draw.text((5,5),('%s:' %n),fill=self.BLACK,font=self.nameFont)

        if s:
            axis_y = self.dataSize+MAX_DATA_SIZE
            while axis_y > ((-96 * 2) + (len(d)/2)):
                self.draw.text((5,axis_y),('%s' %d), fill=self.BLACK, font=self.dataFont)
                self.displayScreen()
                if axis_y == self.dataSize+MAX_DATA_SIZE:
                    sleep(3)
                axis_y -= 5
                sleep(0.05)
                self.draw.rectangle((0,0,self.papirus.size[0],self.papirus.size[1]), fill=self.WHITE, outline=self.WHITE)
    
        self.displayScreen()
        sleep(3)

    # Update the screen
    def displayScreen(self):
        self.papirus.display(self.image)
        self.papirus.partial_update()

    # Display the time and date
    def displayTime(self):
        self.image=Image.new('1',self.papirus.size,self.WHITE)
        self.draw=ImageDraw.Draw(self.image)

        now=datetime.today()
        self.draw.text((10,self.dateSize+10),'{d:02d}.{m:02d}.{y:04d}'.format(y=now.year,m=now.month,d=now.day),fill=self.BLACK,font=self.dateFont)
        self.draw.text((40,10),'{h:02d}:{m:02d}'.format(h=now.hour,m=now.minute),fill=self.BLACK,font=self.clockFont)
        self.displayScreen()
    
    # Set the size of the name
    # Either 37 or 25
    def setNameSize(self,ns):
       self.nameSize = ns

    def getNameSize(self):
        return self.nameSize 

    def clearScreen(self):
        self.papirus.clear()

if __name__=="__main__":
    disp=Display()     # Display object

    print("================================")
    print("       Welcome to Noti-Fi")
    print("================================")


    while(True):
        disp.displayTime()
        disp.mqttLoop()
        disp.displayMessage()

    disp.exit()
    print("Bye")
