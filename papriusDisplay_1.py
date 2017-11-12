#!/usr/bin/python
#===========================================================+
# Desc: A simple program to read/write values from mariaDB  |
#       and display them on a Papirus screen                |
# Auth: Christian Loera                                     |
# Date: 25 Oct 2017                                         |
#===========================================================+
from __future__ import print_function

# Imports
# MariaDB
import MySQLdb as mariadb

# System
import os
import sys

# Image
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# Time
from datetime import datetime
import time

# Papirus
from papirus import Papirus
import RPi.GPIO as GPIO

# Data size
MAX_DATA_SIZE=13

# Screen size
SIZE=27

hatdir='/proc/device-tree/hat'

class Display:
    # Connect to the database with the username, password, and database name
    def __init__(self):
        self.m=mariadb.connect(user='capstone',passwd='2017capstoneProject',db='display')
        self.c=self.m.cursor()
        self.screen=Screen()

    # Checking if someone is at the door
    def door_input(self):
        self.m.commit()
        self.c.execute("SELECT data FROM item WHERE door=1")
        for d in self.c:
            t = d.split('')
            #self.screen.updateScreen("Hello",self.output(str(d)))
            return True
        return False
   
    # Send data to the door and display it
    def update(self):
        self.m.commit()
        # Search for any newData in the database to display
        self.c.execute("SELECT name,data FROM item WHERE newData=1")
        for n,d in self.c:
            print(n,d)
            self.screen.updateScreen(n,self.output(d))
            time.sleep(3)
    
    def output(self,d):
        t=''
        s=''
        d=str(d)
        for i in range(len(d)):
            t+=d[i]
        d=t
        t=''
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
        return str(s) + str(t)

    def exit(self):
        self.c.execute("UPDATE item SET newData=0 WHERE 1=1")
        self.m.commit()
        self.screen.clearScreen()

    def displayTime(self):
        self.screen.displayTime()

    def getSW1(self):
        return self.screen.getSW1()

    def getSW2(self):
        return self.screen.getSW2()

    def getSW3(self):
        return self.screen.getSW3()
    
class Screen:    
    def __init__(self):
        # Check EPD_SIZE is defined
        EPD_SIZE=0.0
        if os.path.exists('/etc/default/epd-fuse'):
            exec(open('/etc/default/epd-fuse').read())
        if EPD_SIZE==0.0:
            print("Please select your screen size by running 'papirus-config'.")

        self.sw1=21
        self.sw2=16
        self.sw3=20
        if(os.path.exists(hatdir+'/product'))and(os.path.exists(hatdir+'/vendor')):
            with open(hatdir+'/product') as f:prod=f.read()
            with open(hatdir+'/vendor') as f:vend=f.read()
            if(prod.find('PaPiRus ePaper HAT')==0)and(vend.find('Pi Supply')==0):
                self.sw1=16
                self.sw2=26
                self.sw3=20

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.sw1,GPIO.IN)
        GPIO.setup(self.sw2,GPIO.IN)
        GPIO.setup(self.sw3,GPIO.IN)

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
        self.nameFont=ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoOblique.ttf',self.nameSize)

        # Setting the size/font for the data
        self.dataSize=int((self.width-MAX_DATA_SIZE)/(MAX_DATA_SIZE*0.65))
        self.dataFont=ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMono.ttf',self.dataSize)

        # Setting the size/font for time and date
        self.clockSize=int((self.width-4)/(8*0.65))
        self.clockFont=ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoOblique.ttf',self.clockSize)
        self.dateSize=int((self.width-10)/(10*0.65))
        self.dateFont=ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMono.ttf',self.dateSize)

    def updateScreen(self,n,d):
        self.image=Image.new('1',self.papirus.size,self.WHITE)
        self.draw=ImageDraw.Draw(self.image)
        # Display the data
        #self.draw.rectangle((2,2,self.width-2,self.height-2), fill=self.WHITE, outline=self.BLACK)
        self.draw.text((5,self.dataSize+MAX_DATA_SIZE),('%s' %d), fill=self.BLACK, font=self.dataFont)

        # Display the name
        #self.draw.rectangle((5,10,self.width-1,10+self.nameSize), fill=self.WHITE, outline=self.WHITE)
        self.draw.text((5,5),('%s:' %n), fill=self.BLACK, font=self.nameFont)

        # Update the screen
        self.papirus.display(self.image)
        self.papirus.update()

    # Display the time and date
    def displayTime(self):
        self.image=Image.new('1',self.papirus.size,self.WHITE)
        self.draw=ImageDraw.Draw(self.image)

        now=datetime.today()
        self.draw.text((10,self.dateSize+10),'{d:02d}.{m:02d}.{y:04d}'.format(y=now.year,m=now.month,d=now.day),fill=self.BLACK,font=self.dateFont)
        self.draw.text((40,10),'{h:02d}:{m:02d}'.format(h=now.hour,m=now.minute),fill=self.BLACK,font=self.clockFont)
        self.papirus.display(self.image)
        self.papirus.update()

    def getSW1(self):
        return self.sw1

    def getSW2(self):
        return self.sw2

    def getSW3(self):
        return self.sw3

    def clearScreen(self):
        self.papirus.clear()

if __name__=="__main__":
    disp=Display()     # Display object
    sw1=disp.getSW1()  # Door is knocked/bell
    sw2=disp.getSW2()  # Door is opened 
    sw3=disp.getSW3()  # Exit
    cont=False

    welcome="================================\n\tWelcome to Noti-fi\n================================"
    print(welcome)
    #print("================================")
    #print("       Welcome to Noti-Fi")
    #print("================================")


    while GPIO.input(sw3)!=False:
        if (GPIO.input(sw1)==False or cont) and GPIO.input(sw2)!=False:
            disp.update()
            cont=True
        else:
            cont=False
        disp.displayTime()

    #while 1:
    #    while disp.door_input():
    #        disp.update()
    #    disp.displayTime()

    disp.exit()
    print("Bye")
