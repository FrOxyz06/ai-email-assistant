from pathlib import Path
from datetime import datetime, timedelta
from typing import List
import json
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "data" / "state.json"

app = FastAPI(title="Mohamed AI Productivity")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

class EmailItem(BaseModel):
    id: int
    sender: str
    subject: str
    body: str
    received: str

class EmailSummary(BaseModel):
    id: int
    sender: str
    subject: str
    summary: str
    priority: str
    reasons: List[str]
    received: str

class CalendarItem(BaseModel):
    id: int
    title: str
    start: str
    location: str = ""

IMPORTANT_WORDS = {
    "interview": 5, "recruiter": 4, "action required": 4, "urgent": 4,
    "immigration": 4, "visa": 4, "appointment": 3, "deadline": 3,
    "exam": 3, "application": 2, "quiz": 2, "due": 2, "assignment": 2
}
LOW_PRIORITY_WORDS = {
    "newsletter": -2, "sale": -2, "promotion": -2, "unsubscribe": -1
}

def load_state():
    if not DATA_FILE.exists():
        return {"emails": [], "calendar": []}
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def save_state(state):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def clean_summary(text: str, max_words: int = 26):
    clean = re.sub(r"\s+", " ", text).strip()
    words = clean.split()
    return clean if len(words) <= max_words else " ".join(words[:max_words]) + "..."

def classify(email: EmailItem):
    text = f"{email.sender} {email.subject} {email.body}".lower()
    score = 0
    reasons = []

    for word, value in IMPORTANT_WORDS.items():
        if re.search(r"\b" + re.escape(word) + r"\b", text):
            score += value
            reasons.append(word)

    for word, value in LOW_PRIORITY_WORDS.items():
        if re.search(r"\b" + re.escape(word) + r"\b", text):
            score += value

    if score >= 5:
        priority = "high"
    elif score >= 2:
        priority = "medium"
    else:
        priority = "low"

    if not reasons:
        reasons = ["no strong urgency signal"]

    return priority, reasons[:4]

def summarize(email: EmailItem):
    priority, reasons = classify(email)
    return EmailSummary(
        id=email.id,
        sender=email.sender,
        subject=email.subject,
        summary=clean_summary(email.body),
        priority=priority,
        reasons=reasons,
        received=email.received,
    )

@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(BASE / "static" / "manifest.webmanifest",
                        media_type="application/manifest+json")

@app.get("/sw.js")
def service_worker():
    return FileResponse(BASE / "static" / "sw.js",
                        media_type="application/javascript")

@app.get("/api/dashboard")
def dashboard():
    state = load_state()
    emails = [summarize(EmailItem(**item)) for item in state["emails"]]
    rank = {"high": 0, "medium": 1, "low": 2}
    emails.sort(key=lambda item: item.received, reverse=True)
    emails.sort(key=lambda item: rank[item.priority])

    events = [CalendarItem(**item) for item in state["calendar"]]
    events = [item for item in events if datetime.fromisoformat(item.start) >= datetime.now()]
    events.sort(key=lambda item: item.start)

    return {
        "emails": emails,
        "calendar": events,
        "counts": {
            "high": sum(e.priority == "high" for e in emails),
            "medium": sum(e.priority == "medium" for e in emails),
            "low": sum(e.priority == "low" for e in emails),
        }
    }

@app.post("/api/analyze", response_model=EmailSummary)
def analyze(email: EmailItem):
    return summarize(email)

@app.post("/api/demo/reset")
def reset_demo():
    now = datetime.now()
    state = {
        "emails": [
            {
                "id": 1,
                "sender": "Recruiting Team",
                "subject": "Software Engineering Interview",
                "body": "Please choose an interview time by Friday. Action required to keep your application active.",
                "received": (now - timedelta(minutes=22)).isoformat(timespec="minutes"),
            },
            {
                "id": 2,
                "sender": "Course Announcement",
                "subject": "Quiz due Sunday",
                "body": "Reminder that Quiz 4 is due Sunday at 11:59 PM. Review the posted material before starting.",
                "received": (now - timedelta(hours=2)).isoformat(timespec="minutes"),
            },
            {
                "id": 3,
                "sender": "Tech Store",
                "subject": "Weekend sale",
                "body": "Our newsletter has this week's promotion and new products. Unsubscribe at any time.",
                "received": (now - timedelta(hours=4)).isoformat(timespec="minutes"),
            },
            {
                "id": 4,
                "sender": "International Student Office",
                "subject": "Visa document reminder",
                "body": "Please review your visa documents and complete the requested action before the stated deadline.",
                "received": (now - timedelta(hours=5)).isoformat(timespec="minutes"),
            },
        ],
        "calendar": [
            {
                "id": 1,
                "title": "CS class",
                "start": (now + timedelta(hours=3)).isoformat(timespec="minutes"),
                "location": "Campus",
            },
            {
                "id": 2,
                "title": "Project work",
                "start": (now + timedelta(days=1, hours=1)).isoformat(timespec="minutes"),
                "location": "Home",
            },
        ],
    }
    save_state(state)
    return {"ok": True}

@app.get("/api/connections")
def connections():
    # These are intentionally truthful: the app shell is ready, but OAuth
    # credentials must be configured before real account access is enabled.
    return {
        "gmail": {"connected": False, "status": "OAuth setup required"},
        "outlook": {"connected": False, "status": "OAuth setup required"},
        "calendar": {"connected": False, "status": "OAuth setup required"},
        "ai": {"connected": False, "status": "AI provider key/setup required"},
    }
