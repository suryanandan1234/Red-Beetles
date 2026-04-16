#include <AccelStepper.h>

// --- PINS ---
#define X_STEP 2
#define X_DIR  5
#define Y_STEP 3
#define Y_DIR  6
#define Z_STEP 4
#define Z_DIR  7
#define A_STEP 12 
#define A_DIR  13 
#define ENABLE_PIN 8
#include <AccelStepper.h>

// --- PINS ---
#define X_STEP 2
#define X_DIR  5
#define Y_STEP 3
#define Y_DIR  6
#define Z_STEP 4
#define Z_DIR  7
#define A_STEP 12 
…  motorBR.runSpeed();
  motorFL.runSpeed();
  motorBL.runSpeed();
}
8

AccelStepper motorFR(AccelStepper::DRIVER, X_STEP, X_DIR);
AccelStepper motorBR(AccelStepper::DRIVER, Y_STEP, Y_DIR);
AccelStepper motorFL(AccelStepper::DRIVER, Z_STEP, Z_DIR);
AccelStepper motorBL(AccelStepper::DRIVER, A_STEP, A_DIR);

float targetL = 0, targetR = 0;
float currentL = 0, currentR = 0;
const float RAMP = 0.05; 

void setup() {
  Serial.begin(115200);
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW); // Start Enabled

  motorFR.setMaxSpeed(3000);
  motorBR.setMaxSpeed(3000);
  motorFL.setMaxSpeed(3000);
  motorBL.setMaxSpeed(3000);
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    
    if (data == "DISABLE") {
      digitalWrite(ENABLE_PIN, HIGH); // Lock/Unlock Motors
      targetL = 0;
      targetR = 0;
    } else {
      digitalWrite(ENABLE_PIN, LOW); // Re-enable if we get movement data
      int commaIndex = data.indexOf(',');
      if (commaIndex > 0) {
        targetL = data.substring(0, commaIndex).toFloat();
        targetR = data.substring(commaIndex + 1).toFloat();
      }
    }
  }

  currentL += (targetL - currentL) * RAMP;
  currentR += (targetR - currentR) * RAMP;

  motorFR.setSpeed(currentR * 1);
  motorBR.setSpeed(currentR * 1);
  motorFL.setSpeed(currentL * -1);
  motorBL.setSpeed(currentL * -1);

  motorFR.runSpeed();
  motorBR.runSpeed();
  motorFL.runSpeed();
  motorBL.runSpeed();
}