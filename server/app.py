import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add parent directory to path to import models and baseline
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import TriageAction, TriageObservation, TriageState
from server.environment import PhishingEnvironment

app = FastAPI(title="Phishing Email Triage Environment")
env = PhishingEnvironment()

@app.get("/")
def read_root():
    return {"status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/reset", response_model=TriageObservation)
def reset():
    return env.reset()

@app.post("/step", response_model=TriageObservation)
def step(action: TriageAction):
    return env.step(action)

@app.get("/state", response_model=TriageState)
def state():
    return env.state

# Hackathon specific endpoints
@app.post("/set_task")
def set_task(level: str):
    """Custom endpoint to allow changing the task difficulty before reset."""
    if level not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail="Invalid level. Choose easy, medium, or hard.")
    env.task_level = level
    return {"status": f"Task level set to {level} for next reset."}

@app.get("/tasks")
def tasks():
    return {
        "tasks": [
            {"name": "easy", "description": "Obvious phishing and clean emails."},
            {"name": "medium", "description": "Spear-phishing requiring header inspection."},
            {"name": "hard", "description": "Advanced evasion, weaponized attachments, and urgent legitimate emails."}
        ],
        "action_schema": TriageAction.schema()
    }

@app.get("/grader")
def grader():
    s = env.state
    if s.total_emails_processed == 0:
        return {"score": 0.0}
    # Calculate score between 0.0 and 1.0
    # Correct = 1 point, FP = -0.5, FN = -1.0
    total_emails = s.total_emails_processed
    raw_score = s.correct_classifications - (s.false_positives * 0.5) - (s.false_negatives * 1.0)
    # Normalize to 0.0 - 1.0
    normalized = max(0.0, min(1.0, raw_score / total_emails))
    return {"score": float(normalized)}

@app.post("/baseline")
def baseline():
    try:
        from inference import run_eval
        scores = run_eval(local=True)
        return {"scores": scores, "status": "success"}
    except ImportError as e:
        return {"error": f"Import error: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}

def main():
    """Main entry point for the OpenEnv server."""
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
