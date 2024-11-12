import cv2
import numpy as np
import paho.mqtt.client as mqtt
import time
import ssl
import json

# AWS IoT MQTT settings
AWS_IOT_ENDPOINT = "a1y00oqvba4yzv-ats.iot.ap-southeast-2.amazonaws.com"
AWS_IOT_PORT = 8883
AWS_IOT_TOPIC_IMAGE = "esp32/cam_0"  # Topic for image
AWS_IOT_TOPIC_RELAY = "home/relay1"   # Topic for relay command
CA_CERT = "aws/rootCa.pem"
CLIENT_CERT = "aws/cert.crt"
PRIVATE_KEY = "aws/private.key"

# MQTT client setup
mqtt_client = mqtt.Client()

# Configure TLS/SSL settings
mqtt_client.tls_set(ca_certs=CA_CERT, certfile=CLIENT_CERT, keyfile=PRIVATE_KEY, tls_version=ssl.PROTOCOL_TLSv1_2)

def connect_mqtt():
    try:
        mqtt_client.connect(AWS_IOT_ENDPOINT, AWS_IOT_PORT, 60)
        mqtt_client.loop_start()
        print("Connected to MQTT broker")
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")

def send_relay_command(command):
    payload = json.dumps({"command": command})
    try:
        mqtt_client.publish(AWS_IOT_TOPIC_RELAY, payload)
        print(f"Sent {command} command to MQTT")
    except Exception as e:
        print(f"Failed to send command to MQTT: {e}")

# Connect to MQTT
connect_mqtt()

# Load LBPH face recognizer and trained model
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("Trainer.yml")

# List of names corresponding to serial numbers
name_list = ["", "Bank", "Earn", "Jom", "Aum", "Mom", "Ice", "Tae", "Jill"]

# Load face detection classifier
facedetect = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

# Timing and relay state variables
face_detected_time = None
required_time = 2  # Seconds required to keep face in frame before opening relay
relay_state = "CLOSE"
last_open_frame = None  # Store the frame that triggered the relay
unlocked_name = ""  # Store the name of the person who triggered the relay

def on_message(client, userdata, message):
    global face_detected_time, relay_state, last_open_frame, unlocked_name

    # Convert byte payload to numpy array
    np_array = np.frombuffer(message.payload, np.uint8)
    frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    # Check if frame is valid
    if frame is not None:
        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = facedetect.detectMultiScale(gray, 1.3, 5)

        # Check if any faces are detected
        if len(faces) > 0:
            if face_detected_time is None:
                face_detected_time = time.time()
            else:
                elapsed_time = time.time() - face_detected_time
                if elapsed_time >= required_time and relay_state != "OPEN":
                    send_relay_command("OPEN")
                    relay_state = "OPEN"
                    last_open_frame = frame.copy()  # Capture the frame when relay opens

                    # Identify the name for unlocking message
                    for (x, y, w, h) in faces:
                        serial, conf = recognizer.predict(gray[y:y+h, x:x+w])
                        if conf > 50 and serial < len(name_list):
                            unlocked_name = name_list[serial]
                            break  # Use the first recognized face

                    # Show the saved frame with "Unlock door already for <name> !!!" message
                    if last_open_frame is not None:
                        message_text = f"Unlock door already for {unlocked_name} !!!"
                        cv2.putText(last_open_frame, message_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 3)
                        cv2.imshow("Triggered Frame", last_open_frame)
                        cv2.waitKey(1)  # Display the frame before sleeping
                        time.sleep(3)  # Keep the unlock message for 3 seconds
                        cv2.destroyWindow("Triggered Frame")  # Close the triggered frame after 3 seconds
        else:
            # Reset the face detection timer if no faces are detected
            face_detected_time = None
            if relay_state != "CLOSE":
                send_relay_command("CLOSE")
                relay_state = "CLOSE"

        # Draw rectangles and labels for detected faces
        for (x, y, w, h) in faces:
            serial, conf = recognizer.predict(gray[y:y+h, x:x+w])
            print(f"Serial: {serial}, Confidence: {conf}")

            if conf > 50 and serial < len(name_list):
                name = name_list[serial]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            else:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, "Unknown", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Display the frame
        cv2.imshow("Frame", frame)

        if cv2.waitKey(1) == ord('q'):
            client.disconnect()

# Subscribe to the image topic
mqtt_client.subscribe(AWS_IOT_TOPIC_IMAGE)
mqtt_client.on_message = on_message

# Start the MQTT loop
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")

# Cleanup
mqtt_client.loop_stop()
mqtt_client.disconnect()
cv2.destroyAllWindows()
