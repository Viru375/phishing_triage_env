import requests
import time

BASE_URL = "http://localhost:8000"

def get_action_name(action_id):
    """Helper purely for printing nicely."""
    names = {
        0: "WAIT",
        1: "POLITE_REMINDER",
        2: "FIRM_WARNING"
    }
    return names.get(action_id, "UNKNOWN")

def print_state(state):
    """Nicely formats and prints the State payload returned from our API."""
    obs = state['observation']
    days = obs['days_overdue']
    patience = obs['client_patience']
    paid = obs['invoice_paid']
    reward = state['reward']
    done = state['done']
    
    print(f"  Day: {days:2d}/30 | Patience: {patience:3d}% | Paid: {str(paid):5s} | Step Reward: {reward:5.1f} | Done: {done}")
    if done:
        info_msg = state['info']['msg']
        print(f"  [RESULT] -> {info_msg}")

def run_episode(strategy_name="wait_only"):
    """
    Runs a complete episode until done is True.
    A strategy decides which action to pick based on the current state.
    """
    print(f"\n{'='*50}")
    print(f"Starting Episode - Strategy: '{strategy_name}'")
    print(f"{'='*50}")
    
    # 1. Reset Environment at start of episode
    resp = requests.post(f"{BASE_URL}/reset")
    if resp.status_code != 200:
        print("Failed to reset environment. Is the server running?")
        return
        
    state = resp.json()
    print("Initial State:")
    print_state(state)
    
    # Track metrics
    total_reward = state['reward']
    done = state['done']
    
    # 2. Loop until episode is done
    while not done:
        obs = state['observation']
        days = obs['days_overdue']
        
        # Decide action based on strategy
        if strategy_name == "wait_only":
            action = 0  # Always Wait
            
        elif strategy_name == "polite_only":
            action = 1  # Always Polite
            
        elif strategy_name == "firm_only":
            action = 2  # Always Firm
            
        elif strategy_name == "escalating":
            # Start gentle, escalate over time
            if days < 5:
                action = 0  # Wait early on
            elif days < 15:
                action = 1  # Polite reminders when getting slightly late
            else:
                action = 2  # Firm warnings when extremely late
        else:
            action = 0

        print(f"\nTaking action: {get_action_name(action)} ({action})")
        
        # POST step to the API
        step_resp = requests.post(f"{BASE_URL}/step", json={"action": action})
        state = step_resp.json()
        
        # Accumulate reward and print state
        total_reward += state['reward']
        done = state['done']
        print_state(state)
        
        time.sleep(0.1) # Small delay to make it easier to read
        
    print(f"\nEpisode Finished. Total Reward earned: {total_reward}")

if __name__ == "__main__":
    print("Welcome to OpenEnv Client: SaaS Invoice Collection!")
    
    # Health check before running
    try:
        # Pinging internal docs endpoint to see if fastAPI is alive
        requests.get(f"{BASE_URL}/docs")
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to {BASE_URL}.")
        print("Please ensure the backend is running (e.g., via 'uvicorn server.app:app' or Docker).")
        exit(1)
        
    # Run a few basic built-in strategies to see the environment in action
    run_episode("wait_only")
    run_episode("firm_only")
    run_episode("escalating")
