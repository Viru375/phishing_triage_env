import time
from fastapi import FastAPI, Request
from pydantic import BaseModel
from models import Action, Observation, State
from server.environment import InvoiceEnv, TASK_DEFINITIONS

# Shared environment instance and app initialization
env = InvoiceEnv()
app = FastAPI(title="OpenEnv - SaaS Invoice Collection Simulator")


class ActionRequest(BaseModel):
    """Request model for the /step endpoint."""
    action: Action


# ─────────────────────────────────────────────
# Health & Spec Endpoints
# ─────────────────────────────────────────────

@app.get("/")
def health_check():
    """Root health check required by OpenEnv validator and Hugging Face Spaces."""
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    """Return all available graded tasks and their descriptions."""
    tasks = []
    for task_id, definition in TASK_DEFINITIONS.items():
        tasks.append({
            "task_id": task_id,
            "name": definition["name"],
            "description": definition["description"]
        })
    return {"tasks": tasks}


@app.post("/grader/{task_id}")
def run_grader(task_id: int):
    """
    Run a full deterministic episode for the given task_id.
    Returns a normalized score in [0.0, 1.0] for hackathon evaluation.
    """
    if task_id not in TASK_DEFINITIONS:
        return {"error": f"task_id {task_id} does not exist. Valid: 0, 1, 2"}, 404
    return env.grade_task(task_id)


# ─────────────────────────────────────────────
# Standard OpenEnv Endpoints
# ─────────────────────────────────────────────

@app.post("/reset", response_model=State)
def reset_environment():
    """Reset the environment to default starting conditions."""
    return env.reset()


@app.post("/step", response_model=State)
def step_environment(req: ActionRequest):
    """Take one step in the environment using the given action."""
    return env.step(req.action)


@app.get("/state", response_model=Observation)
def get_state():
    """Return the current observable state without advancing the episode."""
    return env.state()


# ─────────────────────────────────────────────
# OpenAI-Compatible Endpoint (OpenEnv Spec)
# ─────────────────────────────────────────────

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    OpenAI-compatible chat completions endpoint for inference script integration.
    Translates OpenAI messages format into environment step/reset calls.
    Why: OpenEnv requires agents to interact using the standard OpenAI client interface.
    """
    data = await request.json()
    messages = data.get("messages", [])

    user_messages = [m for m in messages if m.get("role") == "user"]

    if not user_messages:
        # No user messages means start a fresh episode
        state = env.reset()
    else:
        last_user_message = user_messages[-1]
        try:
            action_value = int(last_user_message.get("content", "0").strip())
            action = Action(action_value)
        except (ValueError, KeyError):
            # Default to WAIT if parsing fails — safe fallback
            action = Action.WAIT

        state = env.step(action)

    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": data.get("model", "saas-invoice-env"),
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": state.model_dump_json()
                },
                "finish_reason": "stop" if state.done else "length"
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    }


# ─────────────────────────────────────────────
# Entry Point (required by openenv validate)
# ─────────────────────────────────────────────

def main(host: str = "0.0.0.0", port: int = 7860) -> None:
    """
    Start the FastAPI server via uvicorn.
    Why: openenv validate requires a main() function declared in server/app.py
    and a [project.scripts] server = 'server.app:main' entry in pyproject.toml.
    """
    import uvicorn
    uvicorn.run("server.app:app", host=host, port=port)


if __name__ == "__main__":
    main()
