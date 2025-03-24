from flask import Flask, request, jsonify, render_template
from firebase_admin import auth, credentials, initialize_app
from pymongo import MongoClient
from flask_cors import CORS
import os
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# Firebase configuration (commented out for now)
# cred = credentials.Certificate("path/to/firebase-admin-sdk.json")
# initialize_app(cred)

# MongoDB Atlas configuration
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.get_database("timesync")  # Database name
users_collection = db.users  # Collection for user data
schedules_collection = db.schedules  # Collection for generated schedules

@app.route("/")
def home():
    return render_template("landingpage.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

@app.route("/generate-calendar")
def generate_calendar():
    return render_template("generate_calendar.html")

@app.route("/insights")
def insights():
    return render_template("insights.html")

# Helper function to verify Firebase ID token
def verify_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        return None

# New route to generate timetable
@app.route("/generate-timetable", methods=["POST"])
def generate_timetable():
    data = request.get_json()
    
    # Extract user input
    start_time = datetime.strptime(data.get("start_time"), "%H:%M")
    end_time = datetime.strptime(data.get("end_time"), "%H:%M")
    tasks = data.get("tasks")  # List of tasks [{task, priority, duration}]
    break_interval = int(data.get("break_interval", 60))  # Default: 1 hour
    break_duration = int(data.get("break_duration", 5))  # Default: 5 minutes
    
    # Sort tasks by priority (Higher first) and FCFS (First Come First Serve)
    tasks.sort(key=lambda x: (-get_priority_value(x["priority"]), x["timestamp"]))

    schedule = []
    current_time = start_time

    while tasks and current_time < end_time:
        task = tasks.pop(0)
        duration = int(task["duration"])  # Convert duration to int

        if current_time + timedelta(minutes=duration) <= end_time:
            schedule.append({
                "time": f"{current_time.strftime('%H:%M')} - {(current_time + timedelta(minutes=duration)).strftime('%H:%M')}",
                "task": task["task"],
                "priority": task["priority"],
                "duration": f"{duration}m",
                "status": "Pending"
            })
            current_time += timedelta(minutes=duration)

            # Add a break if needed
            if (current_time - start_time).seconds / 60 % break_interval == 0:
                if current_time + timedelta(minutes=break_duration) <= end_time:
                    schedule.append({
                        "time": f"{current_time.strftime('%H:%M')} - {(current_time + timedelta(minutes=break_duration)).strftime('%H:%M')}",
                        "task": "Break",
                        "priority": "-",
                        "duration": f"{break_duration}m",
                        "status": "Pending"
                    })
                    current_time += timedelta(minutes=break_duration)

    # Store the generated schedule in MongoDB
    schedules_collection.insert_one({"schedule": schedule})

    return jsonify(schedule), 201

# Helper function to assign priority value
def get_priority_value(priority):
    priority_map = {"High": 3, "Medium": 2, "Low": 1}
    return priority_map.get(priority, 0)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
