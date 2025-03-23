#include "MCP_DAC.h"  // DAC

int sampFreq;
int sig;
bool streaming = false;
bool acquisition_mode = false;  // Flag to distinguish between regular and acquisition modes

int acqOutput = A7;
int digControl = 8;
int acqDig = 0;
float voltage = 0.00;

int simOut = A6;
MCP4921 DAC_pin;  // DAC

bool systemCheck = false;

// Variables for sine wave generation
float freq;
float sinArgIncrement;
float sinArg = 0.0;

void setup() {
  Serial.begin(9600);
  pinMode(digControl, OUTPUT);
  pinMode(acqOutput, INPUT);
  DAC_pin.begin(10);  // CS pin is D10 // DAC
}

void loop() {
  if (systemCheck == false) {
    if (Serial.available()) {
      // get PC command
      String checkCommand = Serial.readStringUntil('\n');

      // remove whitespace, \n, carriage returns etc.
      checkCommand.trim();

      // Send acknowledgment that we received the command
      Serial.println("ACK");

      if (checkCommand.startsWith("CHECK POWER")) {
        // start reading integer from index 11 onwards
        // USB always 100
        Serial.println("POWER:100");
        digitalWrite(digControl, LOW);
      } else if (checkCommand.startsWith("TEST TRANSMISSION")) {
        Serial.println("OK");
      } else if (checkCommand.startsWith("SET SAMPLE")) {
        // Handle sampling rate command
        sampFreq = checkCommand.substring(10).toInt();
        Serial.println("Sampling rate set");
      } else if (checkCommand.startsWith("SET FREQ")) {
        // Handle frequency command
        freq = checkCommand.substring(9).toInt();
        // calculate the sine increment based on the obtained values from pc
        sinArgIncrement = 2 * PI * (freq / sampFreq);
        Serial.println("Frequency set");
      } else if (checkCommand == "START") {
        digitalWrite(digControl, HIGH);
        streaming = true;
        acquisition_mode = false;  // Regular mode
      } else if (checkCommand == "START ACQ") {
        digitalWrite(digControl, HIGH);
        streaming = true;
        acquisition_mode = true;  // Acquisition mode
        sinArg = 0.0;  // Reset sine wave phase
      } else if (checkCommand == "STOP" || checkCommand == "STOP ACQ") {
        streaming = false;
        acquisition_mode = false;
      }
    }
  }

  // Handle streaming data
  if (streaming) {
    if (acquisition_mode) {
      // Acquisition mode - send sine wave data
      float sineValue = sin(sinArg);
      int adcValue = (sineValue + 1.0) * 2047;  // Scale to 12-bit (0 to 4095)
      adcValue = constrain(adcValue, 0, 4095);  // Ensure it's within 12-bit range
      
      // Send only the sine wave value
      Serial.println(sineValue);
      
      // Increment sine wave argument
      sinArg += sinArgIncrement;
      if (sinArg > 2 * PI) {
        sinArg -= 2 * PI;
      }
      
      // Wait for next sample
      delayMicroseconds(1000000 / sampFreq);
    } else {
      // Regular mode - handle existing functionality
      if (Serial.available()) {
        String data_line = Serial.readStringUntil('\n');
        data_line.trim();

        // Parse CSV format: time,value
        int comma_idx = data_line.indexOf(',');
        if (comma_idx != -1) {
          String time_str = data_line.substring(0, comma_idx);
          String value_str = data_line.substring(comma_idx + 1);

          float time_val = time_str.toFloat();
          float value_val = value_str.toFloat();

          DAC_pin.write(value_val);  // DAC

          // Output in format for Serial Plotter
          Serial.print(time_val);
          Serial.print(",");
          Serial.println(value_val);
        }
      }
    }
  }
}
