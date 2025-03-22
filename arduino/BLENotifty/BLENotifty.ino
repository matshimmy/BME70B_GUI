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
// Using lower case a-f for hex characters as Bleak might be case-sensitive
const char* SERVICE_UUID = "12345678-1234-1234-1234-123456789abc";
const char* WRITE_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-123456789def";
const char* READ_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-12345678090e";

// Create service and characteristics
// buffer = 40 bytes (i believe this is the max for the arduino)
BLEService mainService(SERVICE_UUID);
BLEStringCharacteristic writeCharacteristic(WRITE_CHARACTERISTIC_UUID, BLEWrite, 40);
BLEStringCharacteristic readCharacteristic(READ_CHARACTERISTIC_UUID, BLERead | BLENotify, 40);

void setup() {
  // Start serial comms
  Serial.begin(9600);

  // Wait up to 3 seconds for serial to connect, but continue regardless
  unsigned long startTime = millis();
  while (!Serial && (millis() - startTime < 3000))
    ;

  Serial.println("Starting BLE initialization...");

  // Begin BLE initialization
  if (!BLE.begin()) {
    Serial.println("ERROR: Could not initialize BLE!");
    while (1)
      ;
  }

  // Set up the BLE device
  BLE.setDeviceName("Nano33BLE");
  BLE.setLocalName("Nano33BLE");

  // Set initial values for characteristics
  readCharacteristic.writeValue("Ready");

  // Add characteristics to service
  mainService.addCharacteristic(writeCharacteristic);
  mainService.addCharacteristic(readCharacteristic);

  // Add service to BLE
  BLE.addService(mainService);

  writeCharacteristic.setEventHandler(BLEWritten, onCommandReceived);

  // Start advertising
  BLE.advertise();

  // Log service and characteristic UUIDs for debugging
  Serial.println("BLE device ready and advertising.");
  Serial.print("Service UUID: ");
  Serial.println(SERVICE_UUID);
  Serial.print("Write Characteristic UUID: ");
  Serial.println(WRITE_CHARACTERISTIC_UUID);
  Serial.print("Read Characteristic UUID: ");
  Serial.println(READ_CHARACTERISTIC_UUID);
}

void onCommandReceived(BLEDevice central, BLECharacteristic characteristic) {
  String command = writeCharacteristic.value();
  command.trim();

  Serial.print("Received command: ");
  Serial.println(command);

  // Process the command and send response
  String response = processCommand(command);
  Serial.print("Sending response: ");
  Serial.println(response);

  // Notify new response
  readCharacteristic.writeValue(response);
}

String processCommand(String command) {
  // Trim any whitespace or newlines
  command.trim();

  // Handle the different commands from the Python app
  if (command == "CHECK POWER") {
    // For now, return a fixed power level of 50%
    return "POWER:50";
  } else if (command == "TEST TRANSMISSION") {
    // Return OK for transmission test
    return "OK";
  } else if (command.startsWith("SET SAMPLE")) {
    // Handle sampling rate command
    sampFreq = command.substring(10).toInt();
    return "Sampling rate set";
  }
  // calc sine wave stuff
  else if (command.startsWith("SET FREQ")) {
    // Handle frequency command
    freq = command.substring(9).toInt();
    Serial.print("Signal freq = ");
    Serial.println(freq);

    // calculate the sine increment based on the obatained values from pc
    sinArgIncrement = 2 * PI * (freq / sampFreq);

    return "Frequency set";
  } else if (command.startsWith("SET SIG")) {
    // ecg or emg
    int sig = command.substring(8).toInt();

    if (sig == 0) {
      digitalWrite(digControl, LOW);
      return "ECG Selected";
    }

    if (sig == 1) {
      digitalWrite(digControl, HIGH);
      return "EMG Selected";
    }
  } else if (command == "START") {
    // Handle start command
    return "Streaming started";
  } else if (command == "GET DATA") {
    return sendSinePacket();
  }


  else {
    // Unknown command
    Serial.print("Unknown command received: '");
    Serial.print(command);
    Serial.println("'");
    return "ERROR: Unknown command";
  }
}

String sendSinePacket() {
  // Create the packet string
  String packet = "SINE,";  // Header

  static float sinArg = 0.0;
  const int numSamples = 6;  // Number of samples per packet
  int samples[numSamples];

  // Generate 10 sine samples
  for (int i = 0; i < numSamples; i++) {
    float sineValue = sin(sinArg);            // Generate sine wave
    int adcValue = (sineValue + 1.0) * 2047;  // Scale to 12-bit (0 to 4095)
    // add one to make all values positive
    // multiply by 2047 because 0.0 in the sine is technically in the middle of the ADC range

    samples[i] = constrain(adcValue, 0, 4095);  // Ensure it's within 12-bit range

    // Convert to string with 4-digit padding (e.g., "0345")
    packet += String(samples[i]);

    // Add comma separator (except for last value)
    if (i < numSamples - 1) {
      packet += ",";
    }

    // Increment sine wave argument
    sinArg += sinArgIncrement;
    if (sinArg > 2 * PI) {
      sinArg -= 2 * PI;
    }
  }


  // Calculate simple checksum (CRC) - sum of ASCII values mod 256
  // its not really a true crc, but that involves polynomial division and i think it might
  // unnecessarily complicate things. this simple checksum should be enough for our purposes
  int crc = 0;

  int startIndex = packet.indexOf(',') + 1;

  while (startIndex > 0) {
    int endIndex = packet.indexOf(',', startIndex);
    String numberStr;

    if (endIndex == -1) {  // Last number
      numberStr = packet.substring(startIndex);
    } else {
      numberStr = packet.substring(startIndex, endIndex);
    }

    int num = numberStr.toInt();                        // Convert to integer
    crc += num;                                         // Accumulate the sum
    startIndex = (endIndex == -1) ? -1 : endIndex + 1;  // Move to next number
  }
  crc = crc % 256;

  // Append CRC (as 3-digit number)
  packet += "," + String(crc);

  // Debug output
  Serial.print("Sending packet: ");
  Serial.println(packet);

  // Send packet over BLE
  return packet;
}

void loop() {
  BLE.poll();  // Handles BLE communication

  // Periodically check connection status
  if (millis() - lastConnectionCheck >= connectionCheckInterval) {
    lastConnectionCheck = millis();

    if (BLE.connected()) {
      if (!isConnected) {
        Serial.println("Device connected!");
        isConnected = true;
      }
    } else {
      if (isConnected) {
        Serial.println("Device disconnected. Restarting advertising...");
        isConnected = false;
        BLE.advertise();
      }
    }
  }
}
