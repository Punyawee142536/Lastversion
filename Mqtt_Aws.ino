#include "secrets.h" // ไฟล์นี้ควรเก็บข้อมูล AWS_CERT_CA, AWS_CERT_CRT, AWS_CERT_PRIVATE, AWS_IOT_ENDPOINT, WIFI_SSID, WIFI_PASSWORD, และ THINGNAME
#include <WiFiClientSecure.h>
#include <MQTTClient.h>
#include <ArduinoJson.h>
#include "WiFi.h"

// ตั้งค่า MQTT Topic สำหรับ Subscribe
#define AWS_IOT_SUBSCRIBE_TOPIC "home/relay1"

// พินรีเลย์
#define relay1 32

WiFiClientSecure net;
MQTTClient client(256);

void connectAWS()
{
  // เชื่อมต่อ WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.println("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");

  // ตั้งค่า WiFiClientSecure ด้วยใบรับรองของ AWS IoT
  net.setCACert(AWS_CERT_CA);
  net.setCertificate(AWS_CERT_CRT);
  net.setPrivateKey(AWS_CERT_PRIVATE);

  // เชื่อมต่อ MQTT broker บน AWS IoT
  client.begin(AWS_IOT_ENDPOINT, 8883, net);
  client.onMessage(messageHandler); // กำหนด handler สำหรับข้อความที่รับ

  Serial.print("Connecting to AWS IoT");
  while (!client.connect(THINGNAME)) {
    Serial.print(".");
    delay(100);
  }

  if (!client.connected()) {
    Serial.println("AWS IoT Timeout!");
    return;
  }

  client.subscribe(AWS_IOT_SUBSCRIBE_TOPIC); // Subscribe หัวข้อที่ต้องการ
  Serial.println("AWS IoT Connected!");
}

void messageHandler(String &topic, String &payload) {
  Serial.println("Incoming message: " + topic + " - " + payload);

  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, payload);
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.f_str());
    return;
  }

  const char* command = doc["command"];
  if (String(command) == "OPEN") {
    digitalWrite(relay1, LOW); // เปิดรีเลย์
    Serial.println("Relay ON");
  } else if (String(command) == "CLOSE") {
    digitalWrite(relay1, HIGH); // ปิดรีเลย์
    Serial.println("Relay OFF");
  }
}

void setup() {
  Serial.begin(115200);

  // ตั้งค่าพินสำหรับรีเลย์
  pinMode(relay1, OUTPUT);
  digitalWrite(relay1, HIGH); // ปิดรีเลย์เป็นค่าเริ่มต้น

  connectAWS(); // เชื่อมต่อกับ AWS IoT
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    connectAWS(); // เชื่อมต่อ WiFi และ AWS IoT ใหม่ถ้าหลุด
  }

  if (!client.connected()) {
    connectAWS(); // เชื่อมต่อ AWS IoT ใหม่ถ้าหลุด
  }

  client.loop(); // เรียกใช้ client.loop() สำหรับการรับข้อความใหม่
  delay(1000); // หน่วงเวลา 1 วินาที
}
