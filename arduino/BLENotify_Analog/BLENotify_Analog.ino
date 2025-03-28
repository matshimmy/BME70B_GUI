#include <ArduinoBLE.h>

// Pin assignments
int digControl = 8;   // Digital pin controlling ECG/EMG selection
int acqOutput = A7;   // Analog input (simulated data source)
int acqDig = 0;       // Unused but declared

// Global variables
int sampFreq;
float freq;
bool streaming = false;

unsigned long lastConnectionCheck = 0;
const unsigned long connectionCheckInterval = 5000;  // check every 5 seconds
bool isConnected = false;                            // track connection state

// BLE Service and Characteristic UUIDs
const char* SERVICE_UUID = "12345678-1234-1234-1234-123456789abc";
const char* WRITE_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-123456789def";
const char* READ_CHARACTERISTIC_UUID  = "12345678-1234-1234-1234-12345678090e";

// Create BLE service and characteristics
BLEService mainService(SERVICE_UUID);
BLEStringCharacteristic writeCharacteristic(WRITE_CHARACTERISTIC_UUID, BLEWrite, 40);
BLEStringCharacteristic readCharacteristic(READ_CHARACTERISTIC_UUID, BLERead | BLENotify, 40);

// Timing variables for continuous data transmission
unsigned long lastSampleTime = 0;
unsigned long sampleInterval;    // microseconds between samples
unsigned long lastPacketTime = 0;
unsigned long packetInterval;    // microseconds between packets (6 samples/packet)

// Forward declarations
void onCommandReceived(BLEDevice central, BLECharacteristic characteristic);
String processCommand(const String& command);
String buildPacket();

// ----------------------------------------------------------------------------
// SETUP
// ----------------------------------------------------------------------------
void setup() {
  Serial.begin(9600);

  // wait up to 3s for Serial
  unsigned long startTime = millis();
  while (!Serial && (millis() - startTime < 3000)) {
    // do nothing
  }

  // Configure pins
  pinMode(digControl, OUTPUT);
  digitalWrite(digControl, LOW);
  pinMode(acqOutput, INPUT);

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

// ----------------------------------------------------------------------------
// LOOP
// ----------------------------------------------------------------------------
void loop() {
  // Keep BLE stack alive
  BLE.poll();

  // Periodically check connection status
  if (millis() - lastConnectionCheck >= connectionCheckInterval) {
    lastConnectionCheck = millis();

    if (BLE.connected()) {
      if (!isConnected) {
        isConnected = true;
        // If you want a connection message, uncomment:
        // Serial.println("Device connected!");
      }
    } else {
      if (isConnected) {
        isConnected = false;
        // If you want a disconnect message, uncomment:
        // Serial.println("Device disconnected. Restarting advertising...");
        BLE.advertise();
      }
    }
  }

  // If streaming is active and time for next packet
  if (streaming) {
    unsigned long currentTime = micros();
    if (currentTime - lastPacketTime >= packetInterval) {
      lastPacketTime = currentTime;

      // Build and send one packet
      String packet = buildPacket();
      readCharacteristic.writeValue(packet);
    }
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
  else if (command.startsWith("SET FREQ")) {
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

  String packet = "SINE,"; 
  const int numSamples = 6;
  int samples[numSamples];

  // Gather 6 readings
  for (int i = 0; i < numSamples; i++) {
    int adcValue = analogRead(acqOutput);
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

  // No extra prints here to avoid flooding
  // If you want to debug each packet uncomment: (could freeze)
  // Serial.println(packet);

  return packet;
}
