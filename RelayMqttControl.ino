#include <WiFi.h>
#include <PubSubClient.h>

// ตั้งค่า WiFi
const char* ssid = "Bank";
const char* password = "0631412922";

// ตั้งค่า MQTT broker
const char* mqtt_server = "broker.emqx.io";  // ใช้ EMQX broker
const int mqtt_port = 1883;
const char* mqtt_topic = "home/relay1";

// พินรีเลย์และปุ่มกด
#define relay1 32
#define button1 4

WiFiClient espClient;
PubSubClient client(espClient);

// ฟังก์ชันเชื่อมต่อ WiFi
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  // เช็คการเชื่อมต่อ WiFi และลองเชื่อมซ้ำถ้าล้มเหลว
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

// ฟังก์ชัน callback ของ MQTT
void callback(char* topic, byte* message, unsigned int length) {
  String msg;
  for (int i = 0; i < length; i++) {
    msg += (char)message[i];
  }
  
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(msg);

  // ตรวจสอบถ้าข้อความที่รับมาเป็น "OPEN" หรือ "CLOSE"
  if (msg == "OPEN") {
    digitalWrite(relay1, LOW);   // เปิดรีเลย์
    Serial.println("Relay ON");
    delay(5000);
  } 
  else if (msg == "CLOSE") {
    digitalWrite(relay1, HIGH);  // ปิดรีเลย์
    Serial.println("Relay OFF");
  }
}

// ฟังก์ชันเชื่อมต่อ MQTT
void reconnect() {
  // พยายามเชื่อมต่อ MQTT ถ้ายังไม่เชื่อมต่อ
  if (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // เชื่อมต่อใหม่พร้อม Client ID
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
      client.subscribe(mqtt_topic);  // สมัครรับข้อมูลจากหัวข้อ relay
      Serial.println("Subscribed to topic: home/relay");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);  // รอ 5 วินาทีแล้วลองใหม่
    }
  }
}

void setup() {
  // ตั้งค่า Serial สำหรับการ debug
  Serial.begin(115200);

  // ตั้งค่ารีเลย์และปุ่ม
  pinMode(relay1, OUTPUT);
  pinMode(button1, INPUT_PULLUP);  // ใช้ INPUT_PULLUP สำหรับปุ่มที่ไม่มี resistor
  digitalWrite(relay1, HIGH);  // เริ่มต้นปิดรีเลย์

  // เชื่อมต่อ WiFi
  setup_wifi();

  // ตั้งค่า MQTT server และ callback function
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  // ถ้า WiFi หลุด ให้เชื่อมต่อใหม่
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    setup_wifi();
  }

  // ถ้าไม่เชื่อมต่อกับ MQTT ให้เชื่อมใหม่
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // ตัวอย่าง: เช็คปุ่มกด
  if (digitalRead(button1) == LOW) {
    digitalWrite(relay1, LOW);  // เปิดรีเลย์เมื่อกดปุ่ม
    Serial.println("Button pressed, relay ON");
  } else {
    digitalWrite(relay1, HIGH); // ปิดรีเลย์เมื่อปล่อยปุ่ม
    Serial.println("Button released, relay OFF");
  }

  delay(100); // เพิ่ม delay เล็กน้อยเพื่อป้องกันการ loop เร็วเกินไป
}
