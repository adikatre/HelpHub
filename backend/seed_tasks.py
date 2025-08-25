import json
import os
import random
from datetime import datetime, timedelta, timezone

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

categories = [
    "Food", "Tutoring", "Elderly Care", "Errands", "Other"
]
urgencies = ["Low", "Medium", "High"]
locations = [
    "Downtown", "Riverside", "Maple Ave", "Eastwood", "Westside",
    "North End", "South Park", "Community Center", "Library Room B",
    "Willow Park", "Cedar Street", "Oak Market"
]
requester_names = [
    "Ava", "Noah", "Mia", "Liam", "Sofia", "Ethan", "Zoe", "Lucas",
    "Emma", "Oliver", "Amir", "Priya", "Carlos", "Nina", "George", "Lara",
    "Ahmed", "Sam", "Harper", "Grace"
]
volunteer_names = [
    "Alex", "Jordan", "Taylor", "Riley", "Quinn", "Morgan", "Casey", "Drew",
    "Reese", "Skyler"
]

titles_by_category = {
    "Food": [
        "Grocery pickup for {name}",
        "Meal prep help for a family",
        "Food pantry sorting shift",
        "Cook and portion simple meals"
    ],
    "Tutoring": [
        "Math tutoring for 9th grader",
        "ESL conversation practice",
        "Resume review session",
        "Homework help (science)"
    ],
    "Elderly Care": [
        "Ride to clinic appointment",
        "Pharmacy pickup",
        "Check-in call with senior",
        "Light home assistance"
    ],
    "Errands": [
        "Dog walking assistance",
        "Package drop-off",
        "Small hardware store run",
        "Library book return"
    ],
    "Other": [
        "Park cleanup volunteers",
        "Tech help setting up phone",
        "Community board setup",
        "Event flyering"
    ],
}

descriptions = [
    "Please help with a quick task to support a neighbor.",
    "One-time assistance needed; flexible timing possible.",
    "This will make a big difference for our community.",
    "Short and simple task—thank you for volunteering!",
    "Looking for a kind helper; supplies will be provided.",
]

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def generate_task(task_id: int) -> dict:
    cat = random.choice(categories)
    title_tpl = random.choice(titles_by_category[cat])
    requester = random.choice(requester_names)
    title = title_tpl.format(name=requester)
    created_days_ago = random.randint(0, 14)
    created_at = iso(datetime.now(timezone.utc) - timedelta(days=created_days_ago, hours=random.randint(0, 23)))
    urg = random.choices(urgencies, weights=[3, 5, 2], k=1)[0]
    status = random.choices(["Open", "Claimed", "Completed"], weights=[4, 3, 3], k=1)[0]
    volunteer_name = None
    volunteer_note = None
    if status in ("Claimed", "Completed"):
        volunteer_name = random.choice(volunteer_names)
        volunteer_note = random.choice([
            "Happy to help!", "Can be there after 5pm", "Have a car", "Bringing supplies"
        ])
    return {
        "id": task_id,
        "title": title,
        "description": random.choice(descriptions),
        "category": cat,
        "urgency": urg,
        "location": random.choice(locations),
        "requesterName": requester,
        "status": status,
        "volunteerName": volunteer_name,
        "volunteerNote": volunteer_note,
        "createdAt": created_at,
    }

def main():
    tasks = [generate_task(i) for i in range(1, 501)]
    # Ensure several are completed today to reflect in counter; we don't track completedAt,
    # so set completedToday to a reasonable number based on tasks marked Completed.
    completed_count = sum(1 for t in tasks if t["status"] == "Completed")
    completed_today = max(10, min(40, completed_count // 5))
    data = {
        "tasks": tasks,
        "nextId": 501,
        "completedToday": completed_today,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(tasks)} tasks to {DATA_FILE}; completedToday={completed_today}")

if __name__ == "__main__":
    main()


