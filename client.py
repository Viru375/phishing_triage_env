import requests
from typing import Dict, Any, Optional
from models import TriageAction, TriageObservation, TriageState

class PhishingEnvClient:
    """Client wrapper to interact with the deployed Phishing Triage Environment."""
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def set_task_level(self, level: str) -> bool:
        response = requests.post(f"{self.base_url}/set_task?level={level}")
        response.raise_for_status()
        return True

    def reset(self) -> TriageObservation:
        response = requests.post(f"{self.base_url}/reset")
        response.raise_for_status()
        return TriageObservation(**response.json())

    def step(self, action: TriageAction) -> TriageObservation:
        response = requests.post(f"{self.base_url}/step", json=action.dict())
        response.raise_for_status()
        return TriageObservation(**response.json())

    def state(self) -> TriageState:
        response = requests.get(f"{self.base_url}/state")
        response.raise_for_status()
        return TriageState(**response.json())

    def get_grader_score(self) -> float:
        response = requests.get(f"{self.base_url}/grader")
        response.raise_for_status()
        return response.json().get("score", 0.0)

    def trigger_baseline(self) -> Dict[str, Any]:
        response = requests.post(f"{self.base_url}/baseline")
        response.raise_for_status()
        return response.json()
