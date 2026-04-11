import random
from models import Action, Observation, State

# Predefined task scenarios — seeded for deterministic, reproducible grading.
# Each task defines starting conditions and a fixed random seed.
TASK_DEFINITIONS = {
    0: {
        "name": "Easy — Polite Collection",
        "description": "Client has high patience. Practice using gentle reminders early.",
        "initial_days_overdue": 0,
        "initial_patience": 100,
        "seed": 42
    },
    1: {
        "name": "Medium — Impatient Client",
        "description": "Client starts with reduced patience. Balance urgency without triggering churn.",
        "initial_days_overdue": 0,
        "initial_patience": 50,
        "seed": 77
    },
    2: {
        "name": "Hard — Last-Minute Collection",
        "description": "Invoice is already 20 days overdue. Aggressive tactics needed to collect in time.",
        "initial_days_overdue": 20,
        "initial_patience": 40,
        "seed": 13
    },
}

class InvoiceEnv:
    """Core simulation logic for the SaaS Invoice Collection environment."""

    def __init__(self):
        self.days_overdue = 0
        self.client_patience = 100
        self.invoice_paid = False
        self._rng = random.Random()

    # ─────────────────────────────────────────────
    # Standard OpenEnv Interface
    # ─────────────────────────────────────────────

    def reset(self) -> State:
        """Reset to default starting conditions (days=0, patience=100)."""
        self.days_overdue = 0
        self.client_patience = 100
        self.invoice_paid = False
        self._rng = random.Random()

        return State(
            observation=self.state(),
            reward=0.0,
            done=False,
            info={"msg": "Environment reset."}
        )

    def step(self, action: Action) -> State:
        """Apply an action and advance the simulation by one day."""
        # Guard: episode already finished
        if self.invoice_paid or self.client_patience <= 0 or self.days_overdue >= 30:
            return State(
                observation=self.state(),
                reward=0.0,
                done=True,
                info={"msg": "Episode already finished. Please reset."}
            )

        self.days_overdue += 1
        payment_chance = self._apply_action(action)

        if self._rng.random() < payment_chance:
            self.invoice_paid = True

        return self._evaluate_outcome()

    def state(self) -> Observation:
        """Return the current observable state of the environment."""
        return Observation(
            days_overdue=self.days_overdue,
            client_patience=max(0, self.client_patience),
            invoice_paid=self.invoice_paid
        )

    # ─────────────────────────────────────────────
    # Task + Grader Support (Hackathon-specific)
    # ─────────────────────────────────────────────

    def reset_task(self, task_id: int) -> State:
        """
        Reset to a specific task's starting conditions using a fixed seed.
        Why: A fixed seed ensures the grader always produces the same evaluation.
        """
        if task_id not in TASK_DEFINITIONS:
            raise ValueError(f"Unknown task_id: {task_id}")

        task = TASK_DEFINITIONS[task_id]
        self.days_overdue = task["initial_days_overdue"]
        self.client_patience = task["initial_patience"]
        self.invoice_paid = False
        # Seeded RNG guarantees reproducible outcomes for fair grading
        self._rng = random.Random(task["seed"])

        return State(
            observation=self.state(),
            reward=0.0,
            done=False,
            info={"msg": f"Task {task_id} reset: {task['name']}"}
        )

    def grade_task(self, task_id: int) -> dict:
        """
        Run a complete, auto-play episode for a task and return a graded score.
        Scoring: 1.0 = paid, 0.5 = escaped, 0.0 = churned or timed out.
        Why: Deterministic auto-play ensures consistent reproducible scores.
        """
        self.reset_task(task_id)

        state: State = State(
            observation=self.state(), reward=0.0, done=False,
            info={"msg": ""}
        )
        total_reward = 0.0
        steps = 0

        # Auto-play strategy: escalate over time
        while not state.done and steps < 35:
            days = state.observation.days_overdue
            if days < 5:
                action = Action.WAIT
            elif days < 15:
                action = Action.POLITE_REMINDER
            else:
                action = Action.FIRM_WARNING

            state = self.step(action)
            total_reward += state.reward
            steps += 1

        # Compute normalized score in [0.0, 1.0]
        if state.observation.invoice_paid:
            score = 1.0
        elif total_reward > -20.0:
            score = 0.5
        else:
            score = 0.0

        return {
            "task_id": task_id,
            "score": round(score, 4),
            "total_reward": round(total_reward, 4),
            "steps": steps,
            "invoice_paid": state.observation.invoice_paid,
            "msg": state.info.get("msg", "")
        }

    # ─────────────────────────────────────────────
    # Internal Helpers
    # ─────────────────────────────────────────────

    def _apply_action(self, action: Action) -> float:
        """Apply the action effect to patience and return the payment probability."""
        if action == Action.WAIT:
            self.client_patience -= 1
            return 0.05
        elif action == Action.POLITE_REMINDER:
            self.client_patience -= 5
            return 0.20
        elif action == Action.FIRM_WARNING:
            self.client_patience -= 30
            return 0.50
        else:
            self.client_patience -= 1
            return 0.0

    def _evaluate_outcome(self) -> State:
        """Evaluate whether the episode is done and compute the step reward."""
        if self.invoice_paid:
            return State(
                observation=self.state(), reward=50.0, done=True,
                info={"msg": "Invoice paid! Success."}
            )
        elif self.client_patience <= 0:
            return State(
                observation=self.state(), reward=-50.0, done=True,
                info={"msg": "Client churned due to zero patience."}
            )
        elif self.days_overdue >= 30:
            return State(
                observation=self.state(), reward=-20.0, done=True,
                info={"msg": "30 days reached. Failed to collect."}
            )
        else:
            return State(
                observation=self.state(), reward=-1.0, done=False,
                info={"msg": "Step taken. Collection ongoing."}
            )
