from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os
import json

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500"]}})


# In-memory storage
TASKS = []
NEXT_ID = 1
COMPLETED_TODAY = 0
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")
_STATE_LOADED = False


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def seed_data():
    global TASKS, NEXT_ID
    if TASKS:
        return
    demo = [
        {
            "title": "Grocery pickup for Mrs. Lee",
            "description": "Pick up basic groceries from Oak Market and drop at 12 Pine St.",
            "category": "Food",
            "urgency": "Medium",
            "location": "Downtown",
            "requesterName": "Mrs. Lee",
        },
        {
            "title": "Algebra tutoring for 9th grader",
            "description": "One-hour tutoring session focusing on linear equations.",
            "category": "Tutoring",
            "urgency": "High",
            "location": "Library Room B",
            "requesterName": "Carlos",
        },
        {
            "title": "Pharmacy pickup",
            "description": "Help picking up medication from Green Pharmacy.",
            "category": "Elderly Care",
            "urgency": "Low",
            "location": "Riverside",
            "requesterName": "Ahmed",
        },
        {
            "title": "Dog walking assistance",
            "description": "Walk Bella for 30 minutes in the afternoon.",
            "category": "Errands",
            "urgency": "Medium",
            "location": "Maple Ave",
            "requesterName": "Nina",
        },
        {
            "title": "Resume review session",
            "description": "Help review and edit resume for entry-level IT role.",
            "category": "Tutoring",
            "urgency": "Low",
            "location": "Community Center",
            "requesterName": "Sam",
        },
        {
            "title": "Meal prep for new parents",
            "description": "Cook/portion three simple meals for the week.",
            "category": "Food",
            "urgency": "High",
            "location": "Eastwood",
            "requesterName": "Priya",
        },
        {
            "title": "Ride to clinic",
            "description": "Provide a ride to 10am appointment and back.",
            "category": "Elderly Care",
            "urgency": "High",
            "location": "Westside",
            "requesterName": "George",
        },
        {
            "title": "Park cleanup volunteers",
            "description": "Join a 1-hour litter pickup at Willow Park.",
            "category": "Other",
            "urgency": "Medium",
            "location": "Willow Park",
            "requesterName": "City Youth Club",
        },
        {
            "title": "Tech help setting up phone",
            "description": "Assist with transferring contacts and apps to new phone.",
            "category": "Other",
            "urgency": "Medium",
            "location": "North End",
            "requesterName": "Lara",
        },
    ]
    # Pre-claim a couple of tasks to showcase claimed vs open
    for idx, item in enumerate(demo):
        global NEXT_ID
        task = {
            "id": NEXT_ID,
            "title": item["title"],
            "description": item["description"],
            "category": item["category"],
            "urgency": item["urgency"],
            "location": item["location"],
            "requesterName": item["requesterName"],
            "status": "Open",
            "volunteerName": None,
            "volunteerNote": None,
            "createdAt": now_iso(),
        }
        # mark some as claimed
        if idx in (1, 5):
            task["status"] = "Claimed"
            task["volunteerName"] = "Demo Volunteer"
            task["volunteerNote"] = "Happy to help!"
        TASKS.append(task)
        NEXT_ID += 1


def load_state():
    global TASKS, NEXT_ID, COMPLETED_TODAY
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        tasks = data.get("tasks", [])
        if isinstance(tasks, list):
            TASKS.clear()
            TASKS.extend(tasks)
        NEXT_ID = int(data.get("nextId", (max([t.get("id", 0) for t in TASKS]) if TASKS else 0) + 1))
        COMPLETED_TODAY = int(data.get("completedToday", 0))
    except FileNotFoundError:
        seed_data()
        save_state()
    except Exception:
        # On malformed file, fall back to seed
        TASKS = []
        NEXT_ID = 1
        COMPLETED_TODAY = 0
        seed_data()
        save_state()


def save_state():
    try:
        payload = {
            "tasks": TASKS,
            "nextId": NEXT_ID,
            "completedToday": COMPLETED_TODAY,
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        # Best-effort persistence; avoid crashing API
        pass


def ensure_state_loaded():
    global _STATE_LOADED
    if _STATE_LOADED:
        return
    if os.path.exists(DATA_FILE):
        load_state()
    else:
        seed_data()
        save_state()
    _STATE_LOADED = True


def validate_required_non_empty(data, required_keys):
    missing = [k for k in required_keys if not data.get(k)]
    if missing:
        return f"Missing fields: {', '.join(missing)}"
    return None


@app.get("/api/tasks")
def get_tasks():
    ensure_state_loaded()
    return jsonify(TASKS), 200


@app.post("/api/tasks")
def create_task():
    ensure_state_loaded()
    global NEXT_ID
    data = request.get_json(silent=True) or {}
    err = validate_required_non_empty(data, [
        "title", "description", "category", "urgency", "location", "requesterName"
    ])
    if err:
        return jsonify({"error": err}), 400

    if data["category"] not in ["Food", "Tutoring", "Elderly Care", "Errands", "Other"]:
        return jsonify({"error": "Invalid category"}), 400
    if data["urgency"] not in ["Low", "Medium", "High"]:
        return jsonify({"error": "Invalid urgency"}), 400

    task = {
        "id": NEXT_ID,
        "title": data["title"],
        "description": data["description"],
        "category": data["category"],
        "urgency": data["urgency"],
        "location": data["location"],
        "requesterName": data["requesterName"],
        "status": "Open",
        "volunteerName": None,
        "volunteerNote": None,
        "createdAt": now_iso(),
    }
    TASKS.append(task)
    NEXT_ID += 1
    save_state()
    return jsonify(task), 201


def find_task(task_id: int):
    return next((t for t in TASKS if t["id"] == task_id), None)


@app.post("/api/tasks/<int:task_id>/volunteer")
def volunteer_task(task_id):
    ensure_state_loaded()
    data = request.get_json(silent=True) or {}
    # volunteerName required, volunteerNote may be empty but must exist per contract
    if "volunteerName" not in data or not data["volunteerName"]:
        return jsonify({"error": "Missing fields: volunteerName"}), 400
    if "volunteerNote" not in data:
        return jsonify({"error": "Missing fields: volunteerNote"}), 400

    task = find_task(task_id)
    if not task:
        return jsonify({"error": "Not found"}), 404
    if task["status"] != "Open":
        return jsonify({"error": "Task not open"}), 400

    task["volunteerName"] = data.get("volunteerName")
    task["volunteerNote"] = data.get("volunteerNote")
    task["status"] = "Claimed"
    save_state()
    return jsonify(task), 200


@app.post("/api/tasks/<int:task_id>/complete")
def complete_task(task_id):
    ensure_state_loaded()
    global COMPLETED_TODAY
    task = find_task(task_id)
    if not task:
        return jsonify({"error": "Not found"}), 404
    if task["status"] != "Claimed":
        return jsonify({"error": "Task must be claimed before completing"}), 400

    task["status"] = "Completed"
    COMPLETED_TODAY += 1
    save_state()
    return jsonify(task), 200


@app.get("/api/impact")
def impact():
    ensure_state_loaded()
    open_tasks = sum(1 for t in TASKS if t.get("status") == "Open")
    return jsonify({"completedToday": COMPLETED_TODAY, "openTasks": open_tasks}), 200


if __name__ == "__main__":
    ensure_state_loaded()
    app.run(host="0.0.0.0", port=5001, debug=True)


