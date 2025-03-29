#include <ArduinoBLE.h>

int digControl = 8;
int acqOutput = A7;
int acqDig = 0;

int sampFreq;
float freq;
float sinArgIncrement;
bool streaming = false;

unsigned long lastConnectionCheck = 0;
const unsigned long connectionCheckInterval = 5000;  // Check every 5 seconds
bool isConnected = false;                            // Track connection state

// Define the Service and Characteristic UUIDs in the standard format
const char* SERVICE_UUID = "12345678-1234-1234-1234-123456789abc";
const char* WRITE_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-123456789def";
const char* READ_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-12345678090e";

// Use a characteristic size large enough to avoid overflow
BLEService mainService(SERVICE_UUID);
BLEStringCharacteristic writeCharacteristic(WRITE_CHARACTERISTIC_UUID, BLEWrite, 40);
BLEStringCharacteristic readCharacteristic(READ_CHARACTERISTIC_UUID, BLERead | BLENotify, 40);

// Timing variables for continuous data transmission
unsigned long lastSampleTime = 0;
unsigned long sampleInterval;   // microseconds between samples, set by SET SAMPLE
unsigned long lastPacketTime = 0;
unsigned long packetInterval;   // time between packets (6 samples per packet)

void onCommandReceived(BLEDevice central, BLECharacteristic characteristic);
String processCommand(String command);
String sendSinePacket();

void setup() {
  Serial.begin(9600);

  // Wait for up to 3 seconds for Serial to connect
  unsigned long startTime = millis();
  while (!Serial && (millis() - startTime < 3000)) {
    // wait
  }

  // Configure digControl pin
  pinMode(digControl, OUTPUT);
  digitalWrite(digControl, LOW);

  // Initialize BLE
  if (!BLE.begin()) {
    Serial.println("ERROR: Could not initialize BLE!");
    while (1) {
      // If BLE fails don't move on
    }
  }

  // Set up BLE device
  BLE.setDeviceName("Nano33BLE");
  BLE.setLocalName("Nano33BLE");

  // Set initial values
  readCharacteristic.writeValue("Ready");

  // Add characteristics to the service
  mainService.addCharacteristic(writeCharacteristic);
  mainService.addCharacteristic(readCharacteristic);

  // Add service and set write handler
  BLE.addService(mainService);
  writeCharacteristic.setEventHandler(BLEWritten, onCommandReceived);

  // Start advertising
  BLE.advertise();

  // Ensure valid sample frequency on first run
  if (sampFreq <= 0) sampFreq = 1;
  sampleInterval = 1000000UL / sampFreq;
  packetInterval = sampleInterval * 6;
}

void loop() {
  // Keep BLE stack alive
  BLE.poll();

  // Periodically check connection status
  if (millis() - lastConnectionCheck >= connectionCheckInterval) {
    lastConnectionCheck = millis();

    if (BLE.connected()) {
      if (!isConnected) {
        // Just detected a new connection
        isConnected = true;
      }
    } else {
      if (isConnected) {
        // Lost a connection; start advertising again
        isConnected = false;
        BLE.advertise();
      }
    }
  }

  // If streaming is active, send periodic packets
  if (streaming) {
    unsigned long currentTime = micros();
    if (currentTime - lastPacketTime >= packetInterval) {
      lastPacketTime = currentTime;
      String packet = sendSinePacket();
      readCharacteristic.writeValue(packet);
    }
  }
}

void onCommandReceived(BLEDevice central, BLECharacteristic characteristic) {
  String command = writeCharacteristic.value();
  command.trim();

  // Process the command
  String response = processCommand(command);

  // Send response back
  readCharacteristic.writeValue(response);
}

String processCommand(String command) {
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
      sampFreq = 1;  // Prevent divide-by-zero or invalid
    }
    sampleInterval = 1000000UL / sampFreq;
    packetInterval = sampleInterval * 6;
    return "Sampling rate set";
  } 
  else if (command.startsWith("SET CIRC")) {
    // freq = command.substring(9).toFloat();
    freq = 1;
    sinArgIncrement = 2.0f * PI * (freq / sampFreq);
    return "Frequency set";
  } 
  else if (command.startsWith("SET SIG")) {
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
  Serial.print("ERROR: Unknown command received: ");
  Serial.println(command);
  return "ERROR: Unknown command";
}

String sendSinePacket() {
  // Create the packet string
  String packet = "SINE,";
  static float sinArg = 0.0f;
  const int numSamples = 6;
  int samples[numSamples];

  // Generate 6 sine samples
  for (int i = 0; i < numSamples; i++) {
    float sineValue = sin(sinArg);
    // Scale [-1,1] to [0,4095] (12-bit)
    int adcValue = (int)((sineValue + 1.0f) * 2047);
    samples[i] = constrain(adcValue, 0, 4095);

    // Append to packet
    packet += samples[i];
    if (i < numSamples - 1) {
      packet += ",";
    }

    sinArg += sinArgIncrement;
    if (sinArg > 2.0f * PI) {
      sinArg -= 2.0f * PI;
    }
  }

  // Calculate a simple checksum
  int crc = 0;
  int startIndex = packet.indexOf(',') + 1; // skip "SINE," part

  while (startIndex > 0 && startIndex < (int)packet.length()) {
    int endIndex = packet.indexOf(',', startIndex);
    String numberStr;

    if (endIndex == -1) {
      // Last number
      numberStr = packet.substring(startIndex);
    } else {
      numberStr = packet.substring(startIndex, endIndex);
    }

    int num = numberStr.toInt();
    crc += num;
    startIndex = (endIndex == -1) ? -1 : endIndex + 1;
  }

  crc = crc % 256;
  packet += "," + String(crc);

  return packet;
}
