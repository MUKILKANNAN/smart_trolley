#include <ESP32Servo.h>

// ---------------- SERVO ----------------
Servo myservo;
#define SERVO_PIN 2   // D2

// ---------------- L298N ----------------
#define ENA 4
#define IN1 16
#define IN2 17

#define ENB 5
#define IN3 18
#define IN4 19

// ---------------- ULTRASONIC ----------------
#define TRIGPIN 12
#define ECHOPIN 14

long duration;
int distance;
int distanceR;
int distanceL;

// ----------------------------------------

void setup() {

  Serial.begin(115200);

  // Motor pins
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Enable motors full speed
  digitalWrite(ENA, HIGH);
  digitalWrite(ENB, HIGH);

  // Ultrasonic
  pinMode(TRIGPIN, OUTPUT);
  pinMode(ECHOPIN, INPUT);

  // Servo
  myservo.attach(SERVO_PIN);
  myservo.write(90);

  Serial.println("Robot Ready");
}

// ---------------- MOTOR FUNCTIONS ----------------

void Forward() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void Reverse() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void Left() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void Right() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void Stop() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

// ---------------- DISTANCE FUNCTION ----------------

int readDistance() {
  digitalWrite(TRIGPIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIGPIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIGPIN, LOW);

  duration = pulseIn(ECHOPIN, HIGH);
  int d = duration / 29 / 2;

  if (d == 0) d = 200;
  return d;
}

// ---------------- MAIN LOOP ----------------

void loop() {

  myservo.write(90);
  delay(300);
  distance = readDistance();

  Serial.print("Distance: ");
  Serial.println(distance);

  if (distance <= 25) {

    Stop();
    delay(300);

    Reverse();
    delay(400);

    Stop();
    delay(300);

    // look right
    myservo.write(20);
    delay(500);
    distanceR = readDistance();

    // look left
    myservo.write(160);
    delay(500);
    distanceL = readDistance();

    myservo.write(90);

    if (distanceR > distanceL) {
      Right();
      delay(600);
    } else {
      Left();
      delay(600);
    }

    Stop();
    delay(300);
  }

  else {
    Forward();
  }
}