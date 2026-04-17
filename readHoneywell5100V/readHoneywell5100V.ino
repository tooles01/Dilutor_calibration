/*
readHoneywell5100V.ino

Read flow sensor from Arduino
*/

const int analogInPin = A2;
int sensorValue = 0;
int timeBetweenRequests = 50;  //can go down to 100 microsec -> serial print takes 400-600 microsec,so -> I can go as fast as 1000 microsec prob
unsigned long prevTime = 0;


void setup() {
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    String inString = Serial.readString();
    parseSerial(inString);
  }
  else {
    unsigned long currentTime = millis();
    unsigned long prevReqTime = prevTime;
    int timeSinceLast = currentTime - prevReqTime;
    if (timeSinceLast >= timeBetweenRequests) {
      prevTime = currentTime;
      sensorValue = analogRead(analogInPin);
      Serial.println(sensorValue);
    }
  }
}

void parseSerial(String inString) {
  char firstChar = inString[0];
  if (firstChar == 'M') {
    char secChar = inString[1];
    String param = inString;  param.remove(0,3);   // starting at 0, remove first 3 chars
    String value = param;
    
    int USidx = param.indexOf('_'); // find underscore
    param.remove(USidx);            // remove everything from underscore to end
    value.remove(0,USidx+1);        // starting at 0, remove everything up to & including underscore

    if (secChar == 'M') {
      if (param.indexOf("timebt")>=0) {
        timeBetweenRequests = value.toFloat();
      }
    }
    
  }

}
