/*
	Author: Matthew Johnson
	File: Door_Knocker.cpp
	Purpose: This file is being created to implement the design of my Capstone I project.
	Information: It is intended to provide proof of	concept that the accelerometer can 
	be used to detect a knock on the door and that the data can be differentiated from 
	other vibrations and background "noise". Connect the SDA line to pin A4 and SCL line 
	to pin A5 on Ardiono Uno/Genuino Board or compatible. A pushbutton has been added to 
  pin 7 for this file to simulate the use of a normal doorbell. There has also been added
  a knock counter to eliminate unnecessary notification to the user. The serial monitor
  and any printed statements are for debugging/troubleshooting purposes and can be
  removed for the final implementation.
*/

#include <Wire.h>             // This is a standard library in the Arduino IDE.    
#include <Adafruit_Sensor.h>  // The other two libraries are open source and 
#include <Adafruit_LSM303.h>  // provided Adafruit to accompany their product.

// Included libraries to use for MQTT
#include <SPI.h>
#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"
#include <Adafruit_WINC1500.h>

// Pins to use with the WINC1500
#define CS  8
#define IRQ 7
#define RST 4

// Setup wifi with the pins
Adafruit_WINC1500 WiFi(CS, IRQ, RST);

// Network configuration
char ssid[] = "Goonies";
char pass[] = "default_pwd";

Adafruit_LSM303 lsm;          // Instantiate the accelerometer.

// Initialize all variables.
int lsmOldX = 0;              // The 'lsmold#' variables are created to allow
int lsmOldY = 0;              // comparison between a baseline and determine
int lsmOldZ = 0;              // when a knock has been generated.

int sensitivity = 1000;       // This variable is used to eliminate normal background
                              // vibrations. The sensor is very sensitive! By comparing
                              // the old readings to the current one it can be 
                              // determined that a loud enough 'knock' has been 
                              // detected.
                              
bool knock = true;         // This flag was created to signify that a large 'knock'
                              // has been detected.
                              
int bellPin = 7;              // This pin will be connected to the pushbutton.
int knocks = 0;               // This counter keeps track of consecutive knocks and
                              // lowers when another knock is not received within
                              // a certain time frame.

void setup() 
{
#ifndef ESP8266
	while (!Serial);            // This will pause Zero, Leonardo, etc until serial console
                              // is opened. It is used only for debugging purposes.
#endif
	Serial.begin(9600);
 pinMode(bellPin, INPUT);
  
	// Try to initialise and warn if we couldn't detect the chip
	if (!lsm.begin())
	{
		Serial.println("Oops ... unable to initialize the LSM303. Check your wiring!");
		while (1);
	} 

  // Checking if there is a WINC1500 breakout board
  if(WiFi.status() == WL_NO_SHIELD) {
    Serial.println("WINC1500 not present");
    while(true);  
  }

  Serial.println("WINC1500: OK");
}

void loop() 
{
  // Set a flag for when the bell is pushed.
  bool bell = false;

  // Read the analog input pin and set bell flag accordingly.
  if (digitalRead(bellPin) == LOW){
    bell = true;
  }
  else{
    bell = false;
  }  
  
  // Read the data from the accelerometer.
	lsm.read();
 
  // Check new data against old data and set to output if change is greater than sensitivity.
  if ((int)lsm.accelData.x - lsmOldX > sensitivity | (int)lsm.accelData.x - lsmOldX < (-1*sensitivity))
  {	  
    lsmOldX = lsm.accelData.x;
    knock = true;
  }
  if ((int)lsm.accelData.y - lsmOldY > sensitivity | (int)lsm.accelData.y - lsmOldY < (-1*sensitivity))
  {    
    lsmOldY = lsm.accelData.y;
    knock = true;
  }
  if ((int)lsm.accelData.z - lsmOldZ > sensitivity | (int)lsm.accelData.z - lsmOldZ < (-1*sensitivity))
  {
    lsmOldZ = lsm.accelData.z;
    knock = true;
  }

  // Print out new data if necessary.
  if (knock == true){

    knocks = knocks + 1;        
    Serial.print("Number of knocks: ");
    Serial.println(knocks);
    if (knocks >= 2){
      Serial.println("Someone is at the door! Send the notification.");
      delay(1000);
    }
    /*
    Serial.print("X: ");
    Serial.print(lsmOldX);
    Serial.print(" ");
    Serial.print("Y: ");
    Serial.print(lsmOldY);
    Serial.print(" ");
    Serial.print("Z: ");
    Serial.print(lsmOldZ);
    Serial.println(" ");
    */
    delay(200);
    lsm.read();
    lsmOldX = lsm.accelData.x;
    lsmOldY = lsm.accelData.y;
    lsmOldZ = lsm.accelData.z;
    delay(100);
  }
  if (knock == false && knocks > 0){
    knocks = knocks - 1;
  }

  if (bell == true){
    Serial.println("Ding-dong!");    
    delay(500);
  }

  // Reset the knock flag.
  knock = false;

  // Wait.
	// delay(1);
}
