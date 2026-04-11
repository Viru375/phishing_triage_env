"""
inference.py — OpenEnv Hackathon Baseline Inference Script

Runs 3 graded task episodes against the environment using the OpenAI client.
Emits structured stdout logs in the required [START]/[STEP]/[END] format.

Environment Variables:
  API_BASE_URL     — The API endpoint for the LLM/env (default: http://localhost:7860/v1)
  MODEL_NAME       — The model identifier to use for inference (default: saas-invoice-env)
  HF_TOKEN         — Your Hugging Face / API key (NO default — must be set explicitly)
  LOCAL_IMAGE_NAME — Optional: local Docker image name if using from_docker_image()
"""

import os
import json
from openai import OpenAI

# Defaults are set ONLY for API_BASE_URL and MODEL_NAME — NOT for HF_TOKEN.
# Why: The hackathon grader requires HF_TOKEN to be explicitly set at runtime.
API_BASE_URL       = os.environ.get("API_BASE_URL", "http://localhost:7860/v1")
MODEL_NAME         = os.environ.get("MODEL_NAME",   "saas-invoice-env")
HF_TOKEN           = os.environ.get("HF_TOKEN")           # No default — must be set at runtime
LOCAL_IMAGE_NAME   = os.environ.get("LOCAL_IMAGE_NAME")   # Optional — only needed for from_docker_image()


def build_openai_client() -> OpenAI:
    """
    Initialize the OpenAI client with the env-specified base URL and token.
    Why: OpenEnv mandates that all LLM/env calls go through the OpenAI client.
    """
    return OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)


def choose_action(days_overdue: int) -> int:
    """
    Rule-based escalating strategy — deterministic for reproducible baseline scoring.
    Returns action ID: 0=WAIT, 1=POLITE_REMINDER, 2=FIRM_WARNING.
    """
    if days_overdue < 5:
        return 0   # WAIT — too early to push
    elif days_overdue < 15:
        return 1   # POLITE_REMINDER — nudge the client
    else:
        return 2   # FIRM_WARNING — running out of time


def run_task_episode(client: OpenAI, task_id: int) -> dict:
    """
    Run a single complete episode for the given task_id.
    Emits [START], [STEP], and [END] structured logs to stdout.
    Wraps risky operations (network, parsing) in try/except as required.
    """
    # ── [START] log ──────────────────────────────
    print(json.dumps({"tag": "[START]", "task_id": task_id, "model": MODEL_NAME}))

    total_reward = 0.0
    step_count   = 0

    # 1. Reset the environment (empty messages list = reset signal)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME, messages=[]
        )
        state = json.loads(response.choices[0].message.content)
    except Exception as reset_error:
        print(json.dumps({"tag": "[END]", "task_id": task_id, "score": 0.0, "error": str(reset_error)}))
        return {"task_id": task_id, "score": 0.0, "total_reward": 0.0}

    done = state.get("done", False)

    # 2. Step loop until episode ends or max steps reached
    while not done and step_count < 35:
        days_overdue = state.get("observation", {}).get("days_overdue", 0)
        action_id    = choose_action(days_overdue)

        try:
            step_response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": str(action_id)}]
            )
            state = json.loads(step_response.choices[0].message.content)
        except Exception as step_error:
            print(json.dumps({"tag": "[STEP]", "step": step_count, "error": str(step_error)}))
            break

        step_reward   = state.get("reward", 0.0)
        done          = state.get("done", False)
        total_reward += step_reward
        step_count   += 1

        # ── [STEP] log ───────────────────────────
        print(json.dumps({
            "tag":    "[STEP]",
            "step":   step_count,
            "action": action_id,
            "reward": round(step_reward, 4),
            "done":   done
        }))

    # 3. Compute final normalized score in [0.0, 1.0]
    invoice_paid = state.get("observation", {}).get("invoice_paid", False)
    if invoice_paid:
        final_score = 1.0
    elif total_reward > -20.0:
        final_score = 0.5
    else:
        final_score = 0.0

    # ── [END] log ────────────────────────────────
    print(json.dumps({
        "tag":          "[END]",
        "task_id":      task_id,
        "score":        round(final_score, 4),
        "total_reward": round(total_reward, 4),
        "steps":        step_count,
        "invoice_paid": invoice_paid
    }))

    return {"task_id": task_id, "score": final_score, "total_reward": total_reward}


def main():
    client = build_openai_client()
    all_scores = []

    # Run all 3 graded tasks sequentially
    for task_id in range(3):
        result = run_task_episode(client, task_id)
        all_scores.append(result["score"])

    average_score = round(sum(all_scores) / len(all_scores), 4)
    print(json.dumps({
        "tag":           "[SUMMARY]",
        "scores":        all_scores,
        "average_score": average_score
    }))


if __name__ == "__main__":
    main()
