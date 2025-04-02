from flask import Flask, request, jsonify, render_template, session
from pymongo import MongoClient
from flask_cors import CORS
import os
import bcrypt
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")  # Ensure this is set in your environment
CORS(app)

# MongoDB Configuration
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.get_database("timesync")
users_collection = db.users
schedules_collection = db.schedules

@app.route("/")
def home():
    return render_template("landingpage.html")

@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    
    try:
        data = request.json
        name = data.get("name")  # Fixed capitalization
        age = data.get("age")
        gender = data.get("gender")
        role = data.get("role")
        email = data.get("email")
        password = data.get("password")

        if not all([name, age, gender, role, email, password]):
            return jsonify({"message": "All fields are required"}), 400

        if users_collection.find_one({"email": email}):
            return jsonify({"message": "User already exists"}), 409  # Conflict

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        users_collection.insert_one({
            "name": name,
            "age": age,
            "gender": gender,
            "role": role,
            "email": email,
            "password": hashed_password.decode("utf-8")  # Store as string
        })

        return jsonify({"message": "User created successfully"}), 201  # Created

    except Exception as e:
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    try:
        data = request.get_json() or request.form
        print("Received data:", data)  # Debugging

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        user = users_collection.find_one({"email": email})
        print("User found:", user)  # Debugging

        if not user:
            return jsonify({"message": "User not found"}), 404  # Not Found

        stored_password = user["password"]
        print("Stored Password:", stored_password)  # Debugging

        # Fix: Convert stored password to bytes if it's a string
        if isinstance(stored_password, str):
            stored_password = stored_password.encode("utf-8")

        if bcrypt.checkpw(password.encode("utf-8"), stored_password):
            session.permanent = True
            session["user"] = {"email": email, "name": user.get("name", "")}  # Fix missing 'name'
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"message": "Invalid password"}), 401  # Unauthorized

    except Exception as e:
        print("Internal Server Error:", str(e))  # Print the real error
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500


@app.route("/logout")
def logout():
    session.pop("user", None)  # Remove user session
    return jsonify({"message": "Logged out successfully"}), 200


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return render_template("login.html")
    return render_template("dashboard.html", user = session["user"])

@app.route("/calendar")
def calendar():
    if "user" not in session:
        return render_template("login.html")
    return render_template("calendar.html")

@app.route("/generate-calendar")
def generate_calendar():
    if "user" not in session:
        return render_template("login.html")
    return render_template("generate_calendar.html")

@app.route("/insights")
def insights():
    if "user" not in session:
        return render_template("login.html")
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
    if "user" not in session:
        return jsonify({"error": "User session not found. Please log in."}), 401

    user_email = session["user"]  # Get logged-in user's email
    date = request.args.get("date")

    if not date:
        return jsonify({"error": "Date is required"}), 400

    # Fetch schedule for the logged-in user on the given date
    schedule_doc = schedules_collection.find_one(
        {"user": user_email, "date": date},
        {"_id": 0, "schedule": 1}
    )

    if not schedule_doc or "schedule" not in schedule_doc:
        return jsonify([])  # Return an empty list if no schedule is found

    return jsonify(schedule_doc["schedule"])  # Return the user's schedule

@app.route("/update-task-status", methods=["POST"])
def update_task_status():
    print("Received request at /update-task-status") 
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401

    data = request.json
    date = data.get("date")
    task_name = data.get("task")
    action = data.get("action")  # "start" or "stop"

    # Find user's schedule for the given date
    schedule_doc = schedules_collection.find_one({"user": session["user"], "date": date})

    if not schedule_doc:
        return jsonify({"error": "No schedule found"}), 404

    schedule = schedule_doc.get("schedule", [])

    for task in schedule:
        # Ignore breaks (No start/stop actions for them)
        if task["task"] == "Break":
            continue  

        if task["task"] == task_name:
            if action == "start":
                task["status"] = "in-progress"
                task["start_time"] = datetime.now().isoformat()
            elif action == "stop":
                print(f"Stopping task: {task_name}, Start Time: {task.get('start_time')}")
                if "start_time" not in task:
                    return jsonify({"error": "Task was never started"}), 400
                
                task["status"] = "completed"
                start_time = datetime.fromisoformat(task.get("start_time", datetime.now().isoformat()))
                task["time_spent"] = (datetime.now() - start_time).seconds // 60  # Time in minutes
            else:
                task["status"] = "skipped"
                task["time_spent"] = 0

    # Update the database
    schedules_collection.update_one(
        {"user": session["user"], "date": date},
        {"$set": {"schedule": schedule}}
    )

    return jsonify({"message": "Task status updated successfully"})

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
