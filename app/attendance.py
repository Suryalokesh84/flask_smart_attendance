import os
import datetime
import json
import numpy as np
import cv2
import face_recognition

def save_attendance_record(name, roll_number, branch):
    attendance_record = {
        'name': name,
        'rollNumber': roll_number,
        'branch': branch,
        'date': datetime.datetime.now().strftime("%Y-%m-%d"),
        'time': datetime.datetime.now().strftime("%H:%M:%S"),
        'status': 'Present'
    }

    # Load existing attendance records
    attendance_data = []
    if os.path.exists('attendance_records.json'):
        with open('attendance_records.json', 'r') as f:
            attendance_data = json.load(f)

    # Append new record and save back to JSON file
    attendance_data.append(attendance_record)
    with open('attendance_records.json', 'w') as f:
        json.dump(attendance_data, f)

def load_user_data():
    user_data = {}
    for filename in os.listdir('user_data'):
        if filename.endswith('.json'):
            with open(os.path.join('user_data', filename), 'r') as f:
                user_details = json.load(f)
                user_data[user_details['rollNumber']] = user_details
    return user_data

def preload_encodings(user_data):
    known_face_encodings = []
    known_face_names = []
    known_face_roll_numbers = []
    known_face_branches = []

    for rollNumber, details in user_data.items():
        if 'encoding' in details:
            known_face_encodings.append(np.array(details['encoding']))
            known_face_names.append(details['name'])
            known_face_roll_numbers.append(details['rollNumber'])
            known_face_branches.append(details.get('branch', 'Unknown'))

    return known_face_encodings, known_face_names, known_face_roll_numbers, known_face_branches
