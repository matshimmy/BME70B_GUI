#include <ArduinoBLE.h>

// Define the Service and Characteristic UUIDs in the standard format
// Using lower case a-f for hex characters as Bleak might be case-sensitive
const char* SERVICE_UUID = "12345678-1234-1234-1234-123456789abc";
const char* WRITE_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-123456789def";
const char* READ_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-12345678090e";

// Create service and characteristics - increase buffer size to 40 bytes
BLEService mainService(SERVICE_UUID);
BLEStringCharacteristic writeCharacteristic(WRITE_CHARACTERISTIC_UUID, BLEWrite, 40);
BLEStringCharacteristic readCharacteristic(READ_CHARACTERISTIC_UUID, BLERead | BLENotify, 40);

void setup() {
  // Start serial comms
  Serial.begin(9600);
  
  // Wait up to 3 seconds for serial to connect, but continue regardless
  unsigned long startTime = millis();
  while (!Serial && (millis() - startTime < 3000));

  Serial.println("Starting BLE initialization...");
  
  // Begin BLE initialization
  if (!BLE.begin()) {
    Serial.println("ERROR: Could not initialize BLE!");
    while (1);
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

// Main loop
void loop() {
  // Listen for BLE peripherals to connect
  BLEDevice central = BLE.central();

  // If a central is connected
  if (central) {
    Serial.print("Connected to device: ");
    Serial.println(central.address());

    // While the central is still connected
    while (central.connected()) {
      // If data is written to the characteristic
      if (writeCharacteristic.written()) {
        // Get the value that was written
        String command = writeCharacteristic.value();
        
        Serial.print("Received command: ");
        Serial.println(command);
        
        // Process the command and send response
        String response = processCommand(command);
        Serial.print("Sending response: ");
        Serial.println(response);
        
        // Write the response back
        readCharacteristic.writeValue(response);
      }
    }

    // Central disconnected
    Serial.println("Central disconnected.");
  }
}

String processCommand(String command) {
  // Trim any whitespace or newlines
  command.trim();
  
  // Handle the different commands from the Python app
  if (command == "CHECK POWER") {
    // For now, return a fixed power level of 50%
    return "POWER:50";
  }
  else if (command == "TEST TRANSMISSION") {
    // Return OK for transmission test
    return "OK";
  }
  else if (command.startsWith("SET SAMPLE")) {
    // Handle sampling rate command
    return "Sampling rate set";
  }
  else if (command.startsWith("SET FREQ")) {
    // Handle frequency command
    return "Frequency set";
  }
  else if (command == "START") {
    // Handle start command
    return "Streaming started";
  }
  else {
    // Unknown command
    Serial.print("Unknown command received: '");
    Serial.print(command);
    Serial.println("'");
    return "ERROR: Unknown command";
  }
}
