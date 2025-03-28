from flask import Flask, request, jsonify, render_template , session
#from firebase_admin import auth, credentials, initialize_app
from pymongo import MongoClient
from flask_cors import CORS
import os
import bcrypt
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
CORS(app)  # Enable CORS for frontend-backend communication

# MongoDB Atlas configuration
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.get_database("timesync")  # Database name
users_collection = db.users  # Collection for user data
schedules_collection = db.schedules  # Collection for generated schedules

@app.route("/")
def home():
    return render_template("landingpage.html")

@app.route("/login" , methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = users_collection.find_one({"email": email})
    if user:
        if bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            session.permanent = True  # Ensures session persists
            session["user"] = email  # Store user session
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"message": "Invalid password"}), 401
    else:
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        users_collection.insert_one({
            "email": email,
            "password": hashed_password
        })
        return jsonify({"message": "User created"})


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

def priority_value(priority):
    """Convert priority string to integer value (higher value = higher priority)."""
    priority_mapping = {"High": 3, "Medium": 2, "Low": 1, "None": 0}
    return priority_mapping.get(priority, 0)

@app.route("/generate-timetable", methods=["POST"])
def generate_timetable():
    if "user" not in session:
        return jsonify({"error": "User session not found. Please log in."}), 401  # Unauthorized

    data = request.json
    date = data.get("date")
    start_time = datetime.strptime(data["start_time"], "%H:%M")
    end_time = datetime.strptime(data["end_time"], "%H:%M")
    break_interval = data["break_interval"]  # Minutes (e.g., 60)
    break_duration = data["break_duration"]  # Minutes (e.g., 5)
    tasks = sorted(data["tasks"], key=lambda x: (-priority_value(x["priority"]), x["timestamp"]))

    current_time = start_time
    schedule = []
    work_time = 0  # Track uninterrupted work time

    while current_time < end_time and tasks:
        task = tasks.pop(0)
        task_name = task["task"]
        task_priority = task["priority"]
        task_duration = int(task["duration"])

        while task_duration > 0 and current_time < end_time:
            time_until_break = break_interval - work_time

            if task_duration > time_until_break:
                schedule.append({
                    "time": f"{current_time.strftime('%H:%M')} - {(current_time + timedelta(minutes=time_until_break)).strftime('%H:%M')}",
                    "task": task_name,
                    "priority": task_priority,
                    "duration": f"{time_until_break}m",
                })
                current_time += timedelta(minutes=time_until_break)
                task_duration -= time_until_break
                work_time = break_interval  # Force a break after this split
            else:
                schedule.append({
                    "time": f"{current_time.strftime('%H:%M')} - {(current_time + timedelta(minutes=task_duration)).strftime('%H:%M')}",
                    "task": task_name,
                    "priority": task_priority,
                    "duration": f"{task_duration}m",
                })
                current_time += timedelta(minutes=task_duration)
                work_time += task_duration
                task_duration = 0  

            if work_time >= break_interval:
                if current_time + timedelta(minutes=break_duration) <= end_time:
                    schedule.append({
                        "time": f"{current_time.strftime('%H:%M')} - {(current_time + timedelta(minutes=break_duration)).strftime('%H:%M')}",
                        "task": "Break",
                        "priority": "-",
                        "duration": f"{break_duration}m",
                    })
                    current_time += timedelta(minutes=break_duration)
                    work_time = 0  # Reset work time counter
    
    # Store schedule in MongoDB
    schedules_collection.insert_one({
        "user": session["user"],
        "date": date,
        "schedule": schedule
    })

    return jsonify(schedule)

@app.route("/get-schedule", methods=["GET"])
def get_schedule():
    date = request.args.get("date")
    if not date:
        return jsonify([])  # Return empty if no date is provided

    # Find the document matching the date
    schedule_doc = schedules_collection.find_one({"date": date}, {"_id": 0, "schedule": 1})

    # If no schedule found, return empty list
    if not schedule_doc or "schedule" not in schedule_doc:
        return jsonify([])

    return jsonify(schedule_doc["schedule"])  # Return only the nested schedule array

# Run the app
if __name__ == "__main__":
    app.run(debug=True)