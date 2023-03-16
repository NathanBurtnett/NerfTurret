#define MLX90640_DEBUG

#include <Arduino.h>

#include <Wire.h>
#include "MLX.h"
#define ADDR 0x33
MLX mlx(Wire);

void setup()
{
  Serial.begin(1500000);
  Serial2.begin(115200, 15, 2);
  mlx.init();
}

void push_serial()
{
  static long last_push = 0;

  if (millis() - last_push < 1000)
    return;
  Serial2.printf("%f, %f\n", 1.0, -1.0);
  // Serial.printf("%f, %f\n", 1.0, -1.0);

  last_push = millis();
}

void loop()
{
  static long last_img = millis();

  push_serial();

  mlx.read_img();
  mlx.preprocess();
  mlx.detect_centroid();
  mlx.tx_current_image();
  mlx.tx_timings();
  mlx.tx_analysis();

  if(Serial.available()) {
    mlx.tx_debugf("Serial Byte RXd!! %d", Serial.available());
  }

  while (Serial.available())
  {
    mlx.rx(Serial.read());
  }
}