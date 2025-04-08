#include <ArduinoBLE.h>
#include <mbedtls/aes.h>
#include <Arduino.h>

#include "MCP_DAC.h"  // DAC
#include "mbed.h"

const byte aes_key[16] = {
  0x60, 0x3d, 0xeb, 0x10, 0x15, 0xca, 0x71, 0xbe,
  0x2b, 0x73, 0xae, 0xf0, 0x85, 0x7d, 0x77, 0x81
};

// Pin assignments
int digControl = 8;   // Digital pin controlling ECG/EMG selection
int acqOutput = A7;   // Analog input (simulated data source)
int acqDig = 0;       // Unused but declared
float voltage = 0.00;

int simOut = A6;
MCP4921 DAC_pin;  // DAC

const int stimpin = D9;
mbed::PwmOut pwm(digitalPinToPinName(stimpin));

bool simulation_mode = false;   // Flag for simulation mode
bool acquisition_mode = false;  // Flag for acquisition mode
bool stimulation_mode = false;  // Flag for stimulation mode
bool template_mode = false;     // Flag for template mode

// Global variables
int sampFreq;
float freq;
bool streaming = false;
float sinArgIncrement;
float sinArg = 0.0;

unsigned long lastConnectionCheck = 0;
const unsigned long connectionCheckInterval = 5000;  // check every 5 seconds
bool isConnected = false;                            // track connection state

// BLE Service and Characteristic UUIDs
const char* SERVICE_UUID = "12345678-1234-1234-1234-123456789abc";
const char* WRITE_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-123456789def";
const char* READ_CHARACTERISTIC_UUID  = "12345678-1234-1234-1234-12345678090e";

// Create BLE service and characteristics
BLEService mainService(SERVICE_UUID);
BLEStringCharacteristic writeCharacteristic(WRITE_CHARACTERISTIC_UUID, BLEWrite, 96);
BLEStringCharacteristic readCharacteristic(READ_CHARACTERISTIC_UUID, BLERead | BLENotify, 96);

// Timing variables for continuous data transmission
unsigned long lastSampleTime = 0;
unsigned long sampleInterval;    // microseconds between samples
unsigned long lastPacketTime = 0;
unsigned long packetInterval;    // microseconds between packets (6 samples/packet)

// Forward declarations
void onCommandReceived(BLEDevice central, BLECharacteristic characteristic);
String processCommand(const String& command);
String buildPacket();

// Variables for stimulation
volatile int stimulation_frequency;  // Default frequency
float stimulation_duty_cycle;        // Default duty cycle
volatile int stimulation_pulse_width;
bool stimulation_running = false;
static bool lastStimState = false;

int template_size;

bool serialConnected = false;
bool bleConnected = false;
bool checkSerial = true;


void setup() {
  // put your setup code here, to run once:

  // wait up to 3s for Serial
  unsigned long startTime = millis();
  while (!Serial && (millis() - startTime < 3000)) {
    // do nothing
  }

  Serial.begin(9600);
  SPI.begin();
  pinMode(digControl, OUTPUT);
  digitalWrite(digControl, LOW);
  pinMode(acqOutput, INPUT);
  DAC_pin.begin(10);  // CS pin is D10 // DAC

  // while (!Serial);

  // BLE CODE
  // Initialize BLE
  if (!BLE.begin()) {
    // Critical error message only
    Serial.println("ERROR: Could not initialize BLE!");
    while (true) {
      // hang if BLE fails to init
    }
  }

  // Set BLE device name
  BLE.setDeviceName("Nano33BLE");
  BLE.setLocalName("Nano33BLE");

  // Put initial value in read characteristic
  readCharacteristic.writeValue("Ready");

  // Add characteristics to service, then add service
  mainService.addCharacteristic(writeCharacteristic);
  mainService.addCharacteristic(readCharacteristic);
  BLE.addService(mainService);

  // Set write handler
  writeCharacteristic.setEventHandler(BLEWritten, onCommandReceived);

  // Start advertising
  BLE.advertise();

  // Ensure sampFreq is valid (avoid divide-by-zero)
  if (sampFreq <= 0) {
    sampFreq = 1;
  }
  // Calculate intervals
  sampleInterval = 1000000UL / sampFreq;
  packetInterval = sampleInterval * 6;

}

void loop() {
  // === Check BLE connection state ===
  // Keep BLE stack alive
  BLE.poll();

  // Check BLE connection status
  if (millis() - lastConnectionCheck >= connectionCheckInterval) {
    lastConnectionCheck = millis();

    if (BLE.connected()) {
      if (!bleConnected) {
        bleConnected = true;
        serialConnected = false;
        checkSerial = false;
        Serial.println("BLE connected.");
      }
    } else {
      if (bleConnected) {
        bleConnected = false;
        Serial.println("BLE disconnected. Restarting advertising...");
        BLE.advertise();
      }
    }
  }

  // --- BLE-specific logic ---
  if (bleConnected) {
    if (streaming) {
      checkSerial = false;
      unsigned long currentTime = micros();
      if (currentTime - lastPacketTime >= packetInterval) {
        lastPacketTime = currentTime;
        String packet = buildPacket();
        readCharacteristic.writeValue(packet);

      }
    }
    else {
      checkSerial = true;
    }
  }

  else if (checkSerial == true) {
    // Serial.println("entered checkserial");
    if (Serial.available()) {
      serialConnected = true;
      bleConnected = false;  // prioritize Serial
    }
  }

  // --- Serial-specific logic ---
  if (serialConnected) {

    // Handle acquisition mode data
  if (acquisition_mode) {

    analogReadResolution(12);
    acqDig = analogRead(acqOutput);

    voltage = acqDig * (3.3 / 4095);

    Serial.println(voltage);

    // 1/fs
    delayMicroseconds(1000000 / sampFreq);
  }

  // Handle stimulation mode
  if (stimulation_mode && stimulation_running) {
    if (!lastStimState) {
      float T = 1.0 / stimulation_frequency;  // Convert frequency to period (seconds)
      pwm.period(T);                          // Set period
      stimulation_pulse_width = (stimulation_duty_cycle * 1000000) / stimulation_frequency;
      pwm.pulsewidth_us(stimulation_pulse_width);
      lastStimState = true;
    }
  } else {
    lastStimState = false;
  }

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
        valueStr.trim();                              // Remove any whitespace

        // Convert to float voltage value
        float voltage = valueStr.toFloat();

        // Shift voltage from -1.65V to +1.65V range to 0V to 3.3V range
        voltage = voltage + 1.65;  // Add 1.65V to shift the range up

        // Convert voltage (0-3.3V) to DAC value (0-4095)
        uint16_t dacValue = (voltage * 4095) / 3.3;
        dacValue = constrain(dacValue, 0, 4095);  // Ensure it's within valid range

        // Serial.println(dacValue);  // Send back the DAC value for verification
        DAC_pin.fastWriteA(dacValue);
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
      if (freq == 0) {
        Serial.println("ECG (LOW) ");
        digitalWrite(digControl, LOW);
      } else if (freq == 1) {
        Serial.println("EMG (HIGH) ");
        digitalWrite(digControl, HIGH);
      }
    } else if (checkCommand.startsWith("SET FREQ")) {
      // Handle stimulation frequency command
      stimulation_frequency = checkCommand.substring(8).toInt();
      Serial.println("FREQ SET");
    } else if (checkCommand.startsWith("SET DUTY")) {
      // Handle stimulation duty cycle command
      stimulation_duty_cycle = checkCommand.substring(8).toInt() / 100.0;
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
      // digitalWrite(digControl, HIGH);
      simulation_mode = false;   // Not simulation mode
      acquisition_mode = true;   // Acquisition mode
      stimulation_mode = false;  // Not stimulation mode
      sinArg = 0.0;              // Reset sine wave phase
      Serial.println("ACQUISITION STARTED");
    } else if (checkCommand == "STOP") {
      // digitalWrite(stimControl, LOW);
      simulation_mode = false;
      acquisition_mode = false;
      stimulation_mode = false;
      stimulation_running = false;
      template_mode = false;
      lastStimState = false;
      pwm.pulsewidth_us(0);
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
    // String input = Serial.readStringUntil('\n');
    // Serial.print("Received: ");
    // Serial.println(input);
    // // Add your serial logic here


  }

}

// ----------------------------------------------------------------------------
// BLE WRITE EVENT HANDLER
// ----------------------------------------------------------------------------
void onCommandReceived(BLEDevice central, BLECharacteristic characteristic) {
  // Get command
  String command = writeCharacteristic.value();
  command.trim();

  // Process and send response
  String response = processCommand(command);
  readCharacteristic.writeValue(response);
}

// ----------------------------------------------------------------------------
// COMMAND PROCESSING
// ----------------------------------------------------------------------------
String processCommand(const String& commandIn) {
  // We trim up front in onCommandReceived(), but do it here again if needed
  String command = commandIn;
  command.trim();

  if (command == "CHECK POWER") {
    return "POWER:50";
  }
  else if (command == "TEST TRANSMISSION") {
    return "OK";
  }
  else if (command.startsWith("SET SAMPLE")) {
    sampFreq = command.substring(10).toInt();
    if (sampFreq <= 0) {
      sampFreq = 1;
    }
    sampleInterval = 1000000UL / sampFreq;
    packetInterval = sampleInterval * 6;
    return "Sampling rate set";
  }
  else if (command.startsWith("SET CIRC")) {
    // Re-purposed to toggle digital pin
    int sig = command.substring(8).toInt();
    if (sig == 0) {
      digitalWrite(digControl, LOW);
      return "ECG Selected";
    } else if (sig == 1) {
      digitalWrite(digControl, HIGH);
      return "EMG Selected";
    }
  }
  else if (command == "START ACQ") {
    streaming = true;
    lastSampleTime = micros();
    return "Streaming started";
  }
  else if (command == "STOP ACQ") {
    streaming = false;
    return "Streaming stopped";
  }

  // Unknown command
  Serial.print("Unknown command received: ");
  Serial.println(command);
  return "ERROR: Unknown command";
}

// ----------------------------------------------------------------------------
// BUILD PACKET (ANALOG READ VERSION)
// ----------------------------------------------------------------------------
String buildPacket() {
  // We build a packet in the format:
  //   SINE, val0, val1, ... val5, CRC
  // but here reading from analog pin A7 for each sample.

  byte encrypted[48];

  String packet = "SINE,"; 
  const int numSamples = 6;
  int samples[numSamples];

  // Gather 6 readings
  for (int i = 0; i < numSamples; i++) {
    int adcValue = analogRead(acqOutput);
    // int adcValue = 4000;
    // If you want to treat it as 12-bit, ensure 0-4095
    samples[i] = constrain(adcValue, 0, 4095);

    packet += samples[i];
    if (i < numSamples - 1) {
      packet += ",";
    }
  }

  // Compute simple checksum (sum of values mod 256)
  int crc = 0;
  int startIndex = packet.indexOf(',') + 1; // skip "SINE,"

  while (startIndex > 0 && startIndex < (int)packet.length()) {
    int endIndex = packet.indexOf(',', startIndex);
    String numberStr;

    if (endIndex == -1) {
      // last number
      numberStr = packet.substring(startIndex);
    } else {
      numberStr = packet.substring(startIndex, endIndex);
    }

    int val = numberStr.toInt();
    crc += val;
    startIndex = (endIndex == -1) ? -1 : endIndex + 1;
  }

  crc = crc % 256;
  packet += "," + String(crc);

  if ((int)packet.length() <= 49) {
    packet += ",";
    for (int i = (int)packet.length(); i <= 49; i++) {
      packet += "0";
    }
  }

  encryptAES_ECB((byte *)packet.c_str(), encrypted, (int)packet.length());

  // Convert to hex string for return
  String encryptedHex = "";
  for (int i = 0; i < 48; i++) {
    if (encrypted[i] < 0x10) encryptedHex += "0";
    encryptedHex += String(encrypted[i], HEX);
  }



  // No extra prints here to avoid flooding
  // If you want to debug each packet uncomment: (could freeze)
  // Serial.println(packet);

  // return packet;
  return encryptedHex;
}


void encryptAES_ECB(const byte *input, byte *output, size_t length) {
  mbedtls_aes_context aes;
  mbedtls_aes_init(&aes);
  mbedtls_aes_setkey_enc(&aes, aes_key, 128);

  for (size_t i = 0; i < length; i += 16) {
    mbedtls_aes_crypt_ecb(&aes, MBEDTLS_AES_ENCRYPT, input + i, output + i);
  }

  mbedtls_aes_free(&aes);
}