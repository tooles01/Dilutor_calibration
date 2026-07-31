/*
 * Control motor with L9110 motor driver
 * 
 * based on https://www.youtube.com/watch?v=YkfBtjs8uWg
 * 
 * 
 * 7/31/2026
 */

// Control motor speed
int delayTime = 4000;

// PWM pins
const int A1A = 4;
const int A1B = 5;

int speed = 255;

void setup() {
  Serial.begin(9600);
  pinMode(A1A, OUTPUT);
  pinMode(A1B, OUTPUT);

  Serial.println("~~~~~~~~~~~~~~~~~~~~~~~~Starting~~~~~~~~~~~~~~~~~~");
  Serial.println("Enter speed value (0-255)");
  analogWrite(A1A, speed);
  analogWrite(A1B, 0);
}


void loop() {
  
  if (Serial.available()) {
    int receivedValue = Serial.parseInt();
    if (receivedValue >= 0 && receivedValue <= 255) {
      // but we need to reverse it lmao
      speed = (255-receivedValue);
      //speed = receivedValue;
      analogWrite(A1A, speed);
      analogWrite(A1B, 0);
      Serial.print("Speed set to: ");
      Serial.println(receivedValue);
    }
    else {
      Serial.print("Error: ");
      Serial.print(receivedValue);
      Serial.println(" is out of range (0-255)");
    }

    // Clear buffer
    while (Serial.available() > 0) {
      Serial.read();
    }
  }
  

  /*
  delay(delayTime);
  
  speed = speed + 51;
  if (speed > 255) {
    speed = 51;
  }
  Serial.print("new speed: ");
  Serial.println(speed);
  */
}
