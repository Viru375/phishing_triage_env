from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Assuming Action, Observation, State from core.env_server are compatible with BaseModel 
# or can be omitted if not required by the validator strictly.
# The hackathon instructions requested Pydantic models specifically.

class TriageAction(BaseModel):
    """
    Actions the agent can perform.
    Valid operations:
    - 'inspect_headers': Reveals SPF/DKIM status.
    - 'analyze_link': Returns URL reputation.
    - 'scan_attachment': Antivirus scan.
    - 'mark_safe': Resolves email as safe.
    - 'mark_phishing': Resolves email as malicious.
    - 'escalate': Escalate to Tier-2.
    """
    operation: str = Field(description="The action to perform (e.g., 'inspect_headers', 'mark_safe', 'mark_phishing', 'escalate', 'analyze_link', 'scan_attachment').")
    email_id: str = Field(description="The ID of the target email.")
    target_id: Optional[str] = Field(default=None, description="The link ID or attachment ID if required by the operation.")

class EmailOverview(BaseModel):
    id: str
    sender: str
    subject: str
    body_snippet: str
    link_ids: List[str] = Field(default_factory=list, description="IDs of links present in the email.")
    attachment_ids: List[str] = Field(default_factory=list, description="IDs of attachments present in the email.")

class TriageObservation(BaseModel):
    inbox: List[EmailOverview] = Field(description="List of emails currently waiting for triage.")
    last_action_result: str = Field(description="Textual outcome of the previous action.")
    current_score: float = Field(description="The agent's current task score.")
    reward: float = Field(description="Reward from the last action.")
    done: bool = Field(description="True if the task is complete.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Internal OpenEnv tracking metadata.")

class TriageState(BaseModel):
    episode_id: str
    step_count: int
    total_emails_processed: int
    correct_classifications: int
    false_positives: int
    false_negatives: int
    current_score: float
