import os
import json
import re
from huggingface_hub import InferenceClient
from client import PhishingEnvClient
from models import TriageAction

# ==========================================
# STEP 1: Define what the AI Analyst does
# ==========================================
SYSTEM_PROMPT = """You are a Tier-1 SOC Phishing Email Triage Analyst AI.
Your goal is to clear the inbox by processing each email. You have several tools at your disposal:
- inspect_headers (target_id should be null)
- analyze_link (target_id must be the link id, e.g., 'link_0')
- scan_attachment (target_id must be the attachment id, e.g., 'att_0')
- mark_safe (target_id should be null)
- mark_phishing (target_id should be null)
- escalate (target_id should be null)

For each step, return ONLY a JSON object representing your action.

CRITICAL INSTRUCTIONS:
1. Pay attention to the 'last_action_result' to learn what the tools returned.
2. Inspect attachments and links if they look suspicious before classifying!
3. If an email has "SPF: FAIL" in headers, verify it before marking safe.
4. False negatives (missing a phishing email) are penalized very heavily!
5. False positives (blocking an urgent legitimate email) causes business disruption.
6. Return EXACTLY a JSON dict and absolutely no other markdown or text.
"""

def extract_json_from_text(text):
    """Helper to cut out just the JSON part from the AI's text."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return json.loads(text)

# ==========================================
# STEP 2: The Main Evaluation Loop
# ==========================================
def run_eval(local=False):
    """
    Evaluates the LLM against the Phishing Environment.
    Runs tasks: easy, medium, hard.
    """
    # 1. Connect to Hugging Face API
    api_key = os.environ.get("HF_TOKEN") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Warning: Please set your HF_TOKEN environment variable!")
        return {"error": "Missing API token"}
            
    llm_client = InferenceClient(api_key=api_key)
    
    # 2. Connect to our Local FastAPI Environment
    env_client = PhishingEnvClient(base_url="http://localhost:8000")
    
    levels = ["easy", "medium", "hard"]
    final_scores = {}

    # 3. Play through each difficulty level
    for task_level in levels:
        print(f"\n=== Starting {task_level.upper()} Task ===")
        
        # Reset the environment for this level
        env_client.set_task_level(task_level)
        observation = env_client.reset()
        
        step_count = 0
        
        # Keep playing until the inbox is completely empty (or max steps)
        while not observation.done and step_count < 30:
            step_count += 1
            
            # Format the inbox data so the AI can read it easily
            inbox_json = json.dumps([email.dict() for email in observation.inbox], indent=2)
            user_prompt = f"LAST ACTION RESULT:\n{observation.last_action_result}\n\nINBOX:\n{inbox_json}\n\nWhat is your next action in strict JSON?"
            
            try:
                # Ask the Llama 3 AI for the next action!
                response = llm_client.chat_completion(
                    model="meta-llama/Meta-Llama-3-8B-Instruct",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.1
                )
                
                # Parse the AI's response into a valid Action
                raw_text = response.choices[0].message.content
                action_data = extract_json_from_text(raw_text)
                action = TriageAction(**action_data)
                
                print(f"Step {step_count}: AI chose '{action.operation}' on {action.email_id}")
            
            except Exception as e:
                # If the AI hallucinates bad JSON, default to safe escalation
                print(f"AI error: {e}. Defaulting to escalate.")
                safe_email_id = observation.inbox[0].id if observation.inbox else "em_1"
                action = TriageAction(operation="escalate", email_id=safe_email_id)

            # Important: Send the action to the environment and get the new state
            observation = env_client.step(action)

        # 4. Get the final grade for this level
        score = env_client.get_grader_score()
        print(f"Score for {task_level}: {score}")
        final_scores[task_level] = score

    return final_scores

# Run the test if executing this file directly
if __name__ == "__main__":
    scores = run_eval(local=True)
    print("\nFinal Baseline Scores:", scores)
