#include "MCP_DAC.h"  // DAC

int sampFreq;
int sig;
bool simulation_mode = false;   // Flag for simulation mode
bool acquisition_mode = false;  // Flag for acquisition mode
bool stimulation_mode = false;  // Flag for stimulation mode
bool template_mode = false;     // Flag for template mode

int acqOutput = A7;
int digControl = 8;
int stimControl = 9; // temporary control pin for stimulation
int acqDig = 0;
float voltage = 0.00;

int simOut = A6;
MCP4921 DAC_pin;  // DAC

bool systemCheck = false;

// Variables for sine wave generation
float freq;
float sinArgIncrement;
float sinArg = 0.0;

// Variables for stimulation
int stimulation_frequency = 35;  // Default frequency
int stimulation_duty_cycle = 50; // Default duty cycle
bool stimulation_running = false;

int template_size;

void setup() {
  Serial.begin(9600);
  pinMode(digControl, OUTPUT);
  pinMode(acqOutput, INPUT);
  DAC_pin.begin(10);  // CS pin is D10 // DAC
}

void loop() {
  if (Serial.available()) {
    // get PC command
    String checkCommand = Serial.readStringUntil('\n');

    // remove whitespace, \n, carriage returns etc.
    checkCommand.trim();

    if (simulation_mode) {
      // In simulation mode, check for DATA: prefix
      if (checkCommand.startsWith("DATA:")) {
        // Extract the numeric value after DATA:
        String valueStr = checkCommand.substring(5);  // Skip "DATA:"
        valueStr.trim();  // Remove any whitespace
        
        // Convert to float voltage value
        float voltage = valueStr.toFloat();
        
        // Shift voltage from -1.65V to +1.65V range to 0V to 3.3V range
        voltage = voltage + 1.65;  // Add 1.65V to shift the range up
        
        // Convert voltage (0-3.3V) to DAC value (0-4095)
        uint16_t dacValue = (voltage * 4095) / 3.3;
        dacValue = constrain(dacValue, 0, 4095);  // Ensure it's within valid range
        
        DAC_pin.write(dacValue);
        Serial.println(dacValue);  // Send back the DAC value for verification
        return;  // Skip further command processing
      }
    }

    // Send acknowledgment for all other commands
    Serial.println("ACK");

    if (checkCommand.startsWith("CHECK POWER")) {
      // start reading integer from index 11 onwards
      // USB always 100
      Serial.println("POWER:100");
      digitalWrite(digControl, LOW);
    } else if (checkCommand.startsWith("TEST TRANSMISSION")) {
      simulation_mode = false;
      acquisition_mode = false;
      stimulation_mode = false;
      Serial.println("OK");
    } else if (checkCommand.startsWith("SET SAMPLE")) {
      // Handle sampling rate command (only needed for acquisition mode)
      sampFreq = checkCommand.substring(10).toInt();
    } else if (checkCommand.startsWith("SET CIRC")) {
      // Handle frequency command
      freq = checkCommand.substring(9).toInt();
      // calculate the sine increment based on the obtained values from pc
      sinArgIncrement = 2 * PI * (freq / sampFreq);
    } else if (checkCommand.startsWith("SET FREQ")) {
      // Handle stimulation frequency command
      stimulation_frequency = checkCommand.substring(8).toInt();
      Serial.println("FREQ SET");
    } else if (checkCommand.startsWith("SET DUTY")) {
      // Handle stimulation duty cycle command
      stimulation_duty_cycle = checkCommand.substring(8).toInt();
      Serial.println("DUTY SET");
    } else if (checkCommand == "START STIM") {
      stimulation_mode = true;
      stimulation_running = true;
      // digitalWrite(stimControl, HIGH);
      Serial.println("STIMULATION STARTED");
    } else if (checkCommand == "START SIM") {
      digitalWrite(digControl, HIGH);
      simulation_mode = true;    // Simulation mode
      acquisition_mode = false;  // Not acquisition mode
      stimulation_mode = false;  // Not stimulation mode
      Serial.println("SIMULATION STARTED");
    } else if (checkCommand == "START ACQ") {
      digitalWrite(digControl, HIGH);
      simulation_mode = false;  // Not simulation mode
      acquisition_mode = true;  // Acquisition mode
      stimulation_mode = false;  // Not stimulation mode
      sinArg = 0.0;             // Reset sine wave phase
      Serial.println("ACQUISITION STARTED");
    } else if (checkCommand == "STOP") {
      // digitalWrite(stimControl, LOW);
      simulation_mode = false;
      acquisition_mode = false;
      stimulation_mode = false;
      stimulation_running = false;
      template_mode = false;
      Serial.println("STOPPED");
    } else if (checkCommand == "SET TEMPLATE FALSE") {
      template_mode = false;
      Serial.println("OK");
    } else if (checkCommand.startsWith("SET TEMPLATE")) {
      template_size = checkCommand.substring(12).toInt();
      template_mode = true;
      Serial.println(template_size);
    }
  }

  // Handle acquisition mode data
  if (acquisition_mode) {
    // // Acquisition mode - send sine wave data with delay
    // float sineValue = sin(sinArg);
    // int adcValue = (sineValue + 1.0) * 2047;  // Scale to 12-bit (0 to 4095)
    // adcValue = constrain(adcValue, 0, 4095);  // Ensure it's within 12-bit range

    // // Send only the sine wave value
    // Serial.println(sineValue);

    // // Increment sine wave argument
    // sinArg += sinArgIncrement;
    // if (sinArg > 2 * PI) {
    //   sinArg -= 2 * PI;
    // }

    // // Wait for next sample
    // delayMicroseconds(1000000 / sampFreq);

    analogReadResolution(12);
    acqDig = analogRead(acqOutput);

    voltage = acqDig * (3.3 / 4095);

    Serial.println(voltage);

    // 1/fs
    delayMicroseconds(1000000 / sampFreq);
  }

  // Handle stimulation mode
  if (stimulation_mode && stimulation_running) {
    digitalWrite(stimControl, HIGH);
  } else {
    digitalWrite(stimControl, LOW);
  }
}
