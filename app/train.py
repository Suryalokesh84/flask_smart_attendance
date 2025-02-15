import cv2
import mediapipe as mp
import face_recognition
import numpy as np
import os
import time
import json

mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

if not os.path.exists('trained_images'):
    os.makedirs('trained_images')
if not os.path.exists('user_data'):
    os.makedirs('user_data')

def detect_faces(frame):
    with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
        results = face_detection.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if results.detections:
            return results.detections
        return []

def process_frame(frame, face_encodings):
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)  # Speed up encoding
    encodings = face_recognition.face_encodings(small_frame)
    
    if len(encodings) == 0:
        return frame, False, "No face detected. Ensure good lighting and a clear face."
    
    face_encoding = encodings[0]
    matches = face_recognition.compare_faces(face_encodings, face_encoding, tolerance=0.4)
    
    if True in matches:
        return frame, False, "This face is already registered."
    
    return frame, True, face_encoding

def save_images(frames, user_details, face_encodings):
    avg_encoding = np.mean(face_encodings, axis=0)
    for i, frame in enumerate(frames):
        filename = f"trained_images/{user_details['rollNumber']}_{i}.jpg"
        cv2.imwrite(filename, frame)
        print(f"Image saved as {filename}")

    user_data_file = f"user_data/{user_details['rollNumber']}.json"
    user_details['encoding'] = avg_encoding.tolist()
    with open(user_data_file, 'w') as f:
        json.dump(user_details, f)
    print(f"User details saved as {user_data_file}")

def draw_text_with_background(frame, text, position, font, font_scale, text_color, background_color):
    text_size, _ = cv2.getTextSize(text, font, font_scale, thickness=2)
    x, y = position
    cv2.rectangle(frame, (x, y - text_size[1] - 10), (x + text_size[0], y + 5), background_color, -1)
    cv2.putText(frame, text, (x, y), font, font_scale, text_color, thickness=2, lineType=cv2.LINE_AA)

def main():
    branches = ["CSM", "CSD", "CAI", "AID", "CSC"]

    user_details = {
        'name': input("Enter your name: "),
        'rollNumber': input("Enter your roll number: "),
        'email': input("Enter your email: "),
        'branch': input(f"Enter your branch ({'/'.join(branches)}): ")
    }

    known_face_encodings = []
    cap = cv2.VideoCapture(0)
    training_complete = False
    captured_frames = []
    face_encodings = []
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame, is_valid, face_encoding = process_frame(frame, known_face_encodings)
        if not is_valid:
            draw_text_with_background(frame, face_encoding, (50, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), (255, 255, 255))
        else:
            if not training_complete:
                frame_count += 1
                captured_frames.append(frame)
                face_encodings.append(face_encoding)
                print(f"Captured image {frame_count}/10")  # Updated message
                time.sleep(0.1)  # Keep it small to speed up
                
                if frame_count >= 10:  # Now capturing only 10 images
                    save_images(captured_frames, user_details, face_encodings)
                    training_complete = True
                    message = "Training completed successfully!"
                    draw_text_with_background(frame, message, (50, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), (255, 255, 255))
        
        cv2.imshow('Training', frame)
        if training_complete:
            cv2.waitKey(2000)  # Show "Training completed" message for 2 seconds
            break
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
