# pip install opencv-python==4.5.2
import cv2
import numpy as np
import os

# ตั้งค่ากล้องและโหลดโมเดลตรวจจับใบหน้า
video = cv2.VideoCapture(0)
facedetect = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

id = input("Enter Your ID: ")
counts = {'normal': 0, 'gray': 0, 'noise': 0, 'blur': 0, 'flip': 0, 'threshold': 0, 'contrast': 0, 'brightness': 0}
target_counts = {'normal': 300, 'gray': 300, 'noise': 200, 'blur': 200, 'flip': 200, 'threshold': 100, 'contrast': 200, 'brightness': 200}

# ฟังก์ชันสำหรับบันทึกภาพ
def save_image(prefix, image):
    count = 1
    while os.path.exists(f'datasets/{prefix}{count}.jpg'):
        count += 1
    cv2.imwrite(f'datasets/{prefix}{count}.jpg', image)

# ฟังก์ชันแปลงภาพ
def process_image(face_img, effect):
    if effect == 'noise':
        gauss = np.random.normal(0, 25, face_img.shape)
        return np.clip(face_img + gauss, 0, 255).astype(np.uint8)
    elif effect == 'blur':
        return cv2.GaussianBlur(face_img, (5, 5), 0)
    elif effect == 'flip':
        return cv2.flip(face_img, 1)
    elif effect == 'threshold':
        return cv2.threshold(face_img, 127, 255, cv2.THRESH_BINARY)[1]
    elif effect == 'contrast':
        return cv2.convertScaleAbs(face_img, alpha=1.5)
    elif effect == 'brightness':
        return cv2.convertScaleAbs(face_img, beta=50)
    return face_img

# วนลูปบันทึกภาพจากกล้อง
while True:
    ret, frame = video.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        face_img = gray[y:y+h, x:x+w]
        for effect, max_count in target_counts.items():
            if counts[effect] < max_count:
                processed_img = process_image(face_img, effect if effect != 'normal' else None)
                save_image(f'User.{id}_{effect}', processed_img)
                counts[effect] += 1
        cv2.rectangle(frame, (x, y), (x+w, y+h), (55, 55, 255), 2)

    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) == 27 or all(counts[eff] >= max_count for eff, max_count in target_counts.items()):
        break

video.release()
cv2.destroyAllWindows()
print("Dataset Collection Done")
