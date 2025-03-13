int sampFreq;
int sig;
bool streaming = false;

int acqOutput = A7;
int digControl = 8;
int acqDig = 0;
float voltage = 0.00;

bool systemCheck = false;

void setup() {
  Serial.begin(9600);
  pinMode(digControl, OUTPUT);
  pinMode(acqOutput, INPUT);
}

void loop() {
  if (systemCheck == false) {
    // Serial.println(1);

    // if (Serial.available()) {
    //   // get PC response
    //   int received = Serial.parseInt();
    //   if (received == true) {
    //     systemCheck = true;
    //   }
    //   else {
    //     Serial.println("Incomplete test");
    //   }

    // }

    if (Serial.available()) {
      // get PC commadn
      String checkCommand = Serial.readStringUntil('\n');

      // remove whitesapce, \n, carriage returns etc.
      checkCommand.trim();

      if(checkCommand.startsWith("CHECK POWER")) {
        // start reading integer from index 11 onwards
        Serial.println("POWER:50");
        // delay(1000);
      } else if(checkCommand.startsWith("TEST TRANSMISSION")) {
        Serial.println("OK");
        // delay(1000);
      }
    }
  }

  // if (Serial.available()) {
  //   // get PC commadn
  //   String command = Serial.readStringUntil('\n');

  //   // remove whitesapce, \n, carriage returns etc.
  //   command.trim();

  //   if (command.startsWith("SET SAMPLE ")) {
  //     // start reading integer from index 11 onwards
  //     sampFreq = command.substring(11).toInt();
  //     Serial.print("Sampling freq =  ");
  //     Serial.println(sampFreq);
  //     delay(3000);
  //   }


  //   else if (command.startsWith("SET SIG ")) {
  //     // start reading float from index 9 onwards
  //     sig = command.substring(8).toInt();

  //     if (sig == 0) {
  //       Serial.println("Signal = ECG");
  //       digitalWrite(digControl, LOW);
  //       delay(3000);
  //     }

  //     else if (sig == 1) {
  //       Serial.println("Signal = EMG");
  //       digitalWrite(digControl, HIGH);
  //       delay(3000);
  //     }

  //     delay(3000);
  //   }

  //   // start streaming
  //   else if (command == "START") {
  //     streaming = true;
  //     Serial.println("Streaming started");
  //   }
  //   // stop streaming
  //   else if (command == "STOP") {
  //     streaming = false;
  //     Serial.println("Streaming stopped");
  //   }
  // }

  // // if streaming started
  // if (streaming) {
  //   analogReadResolution(12);
  //   acqDig = analogRead(acqOutput);

  //   voltage = acqDig * (3.3 / 4095);

  //   Serial.println(voltage);

  //   // 1/fs
  //   delayMicroseconds(1000000 / sampFreq);
  // }
}
