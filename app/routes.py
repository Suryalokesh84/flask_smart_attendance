from flask import Blueprint, render_template, request, redirect, url_for, flash
import cv2
import mediapipe as mp
import face_recognition
import numpy as np
import json
import os
from .train import detect_faces, process_frame, save_images

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_details = {
            'name': request.form['name'],
            'rollNumber': request.form['rollNumber'],
            'email': request.form['email']
        }
        cap = cv2.VideoCapture(0)
        known_face_encodings = []
        training_complete = False
        captured_frames = []
        face_encodings = []
        frame_count = 0

        while cap.isOpened() and not training_complete:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame, is_valid, face_encoding = process_frame(frame, known_face_encodings)
            if is_valid:
                frame_count += 1
                captured_frames.append(frame)
                face_encodings.append(face_encoding)
                if frame_count >= 50:
                    save_images(captured_frames, user_details, face_encodings)
                    training_complete = True
                    flash("Training completed successfully!")
            else:
                flash(face_encoding)
        
        cap.release()
        return redirect(url_for('main.index'))
    
    return render_template('register.html')

@main.route('/capture-attendance', methods=['GET'])
def capture_attendance():
    from .attendance import load_user_data, preload_encodings

    user_data = load_user_data()
    known_face_encodings, known_face_names = preload_encodings(user_data)
    
    cap = cv2.VideoCapture(0)
    attendance_recorded = False
    name = "Unknown"

    while cap.isOpened() and not attendance_recorded:
        ret, frame = cap.read()
        if not ret:
            break
        
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.4)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                attendance_recorded = True
                flash(f"Attendance recorded for {name}")
                break
        
        if attendance_recorded:
            break

    cap.release()
    return redirect(url_for('main.index'))

@main.route('/attendance-records')
def attendance_records():
    # Code to display attendance records
    return render_template('attendance_records.html')
