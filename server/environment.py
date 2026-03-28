import uuid
from typing import List, Dict, Tuple
from models import TriageAction, TriageObservation, TriageState, EmailOverview

class InternalEmail:
    """Internal representation of an email containing hidden details."""
    def __init__(self, id, sender, subject, body, headers, links, attachments, is_phishing, is_spear_phishing, is_urgent_legit):
        self.id = id
        self.sender = sender
        self.subject = subject
        self.body = body
        self.headers = headers
        self.links = links
        self.attachments = attachments
        self.is_phishing = is_phishing
        self.is_spear_phishing = is_spear_phishing
        self.is_urgent_legit = is_urgent_legit

class PhishingEnvironment:
    """The simulator environment representing the SOC Analyst's inbox."""
    def __init__(self):
        self.episode_id = str(uuid.uuid4())
        self.step_count = 0
        self.task_level = "easy"
        self.inbox: List[InternalEmail] = []
        self.processed = 0
        self.correct = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.score = 0.0
        self.done = False
        self.last_result = "Environment initialized."

    def load_task(self, level: str) -> TriageObservation:
        self.task_level = level
        self.inbox = []
        self.episode_id = str(uuid.uuid4())
        self.step_count = 0
        self.processed = 0
        self.correct = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.score = 0.0
        self.done = False
        self.last_result = f"Loaded {level} task."

        if level == "easy":
            self.inbox.extend([
                InternalEmail("em_1", "prince@nigeria.xyz", "URGENT INVESTMENT", "Please send $1000.", {"SPF": "FAIL"}, ["http://scam.xyz/invest"], [], True, False, False),
                InternalEmail("em_2", "hr@company.com", "Holiday Schedule", "Attached is the schedule.", {"SPF": "PASS"}, [], ["schedule.pdf"], False, False, False),
                InternalEmail("em_3", "admin@it-helpdesk-portal.net", "Password Expiring", "Click below.", {"SPF": "FAIL"}, ["http://it-helpdesk-portal.net/login"], [], True, False, False)
            ])
        elif level == "medium":
            self.inbox.extend([
                InternalEmail("em_1", "ceo@company.com", "Wire Transfer", "Send money ASAP.", {"SPF": "FAIL", "DKIM": "FAIL"}, [], ["instructions.pdf"], True, True, False),
                InternalEmail("em_2", "vendor@trusted.com", "Invoice 102", "Please pay invoice.", {"SPF": "PASS", "DKIM": "PASS"}, [], ["invoice.pdf"], False, False, False),
                InternalEmail("em_3", "support@github.com", "Action Required", "Verify account.", {"SPF": "FAIL"}, ["http://githud.com/verify"], [], True, True, False),
                InternalEmail("em_4", "marketing@company.com", "New Assets", "Here are the new logos.", {"SPF": "PASS"}, ["https://company.com/assets"], [], False, False, False),
                InternalEmail("em_5", "alerts@aws.amazon.com", "Usage Alert", "EC2 usage high.", {"SPF": "PASS"}, ["https://console.aws.amazon.com"], [], False, False, False),
            ])
        else: # hard
            self.inbox.extend([
                InternalEmail("em_1", "investors@company.com", "Q3 Earnings SECURE", "Confidential.", {"SPF": "PASS"}, ["https://legit-share.com/redirect?to=malicious.com"], [], True, True, False),
                InternalEmail("em_2", "ceo@company.com", "CRITICAL: Mergers", "Review and sign today or deal falls through.", {"SPF": "PASS", "DKIM": "PASS"}, [], ["term_sheet.docx"], False, False, True),
                InternalEmail("em_3", "hr@company.com", "Benefits Update", "Update your direct deposit.", {"SPF": "FAIL"}, ["https://company-benefits.com/login"], [], True, True, False),
                InternalEmail("em_4", "it@company.com", "Routine scan", "No action needed.", {"SPF": "PASS"}, [], [], False, False, False),
                InternalEmail("em_5", "vendor@billing.com", "Overdue Invoice", "Pay now.", {"SPF": "PASS"}, [], ["invoice_final.pdf.exe"], True, True, False),
                InternalEmail("em_6", "sales@company.com", "Lead list", "Attached.", {"SPF": "PASS"}, [], ["leads.csv"], False, False, False),
                InternalEmail("em_7", "ops@company.com", "Server down", "Restart PRD-1 immediately.", {"SPF": "PASS"}, [], [], False, False, True),
                InternalEmail("em_8", "external_recruiter@tech.com", "Job Opportunity", "Are you looking?", {"SPF": "PASS"}, ["https://linkedin.com/in/recruiter"], [], False, False, False),
                InternalEmail("em_9", "admin@company.com", "Update Policy", "Review attached changes.", {"SPF": "PASS"}, [], ["policy.doc"], True, True, False),
                InternalEmail("em_10", "legal@company.com", "Compliance Training", "Required by Friday.", {"SPF": "PASS"}, ["https://training.company.com"], [], False, False, False),
            ])
        
        return self._get_observation(0.0)

    def reset(self) -> TriageObservation:
        """Required by OpenEnv standard logic format"""
        return self.load_task(self.task_level)

    def _get_observation(self, reward: float) -> TriageObservation:
        overview = []
        for em in self.inbox:
            overview.append(EmailOverview(
                id=em.id,
                sender=em.sender,
                subject=em.subject,
                body_snippet=em.body[:50] + "..." if len(em.body) > 50 else em.body,
                link_ids=[f"link_{i}" for i in range(len(em.links))],
                attachment_ids=[f"att_{i}" for i in range(len(em.attachments))]
            ))
        return TriageObservation(
            inbox=overview,
            last_action_result=self.last_result,
            current_score=self.score,
            reward=reward,
            done=self.done,
            metadata={"step": self.step_count}
        )

    def step(self, action: TriageAction) -> TriageObservation:
        if self.done:
            self.last_result = "Episode is already done."
            return self._get_observation(0.0)

        self.step_count += 1
        reward = 0.0
        
        # Find the requested email securely
        email = None
        for em in self.inbox:
            if em.id == action.email_id:
                email = em
                break
                
        if not email:
            self.last_result = f"Error: Email '{action.email_id}' not found in inbox."
            return self._get_observation(-0.1)

        op = action.operation.lower()
        if op == "inspect_headers":
            self.last_result = f"Headers for {email.id}: " + ", ".join([f"{k}={v}" for k,v in email.headers.items()])
            reward = -0.05
        elif op == "analyze_link":
            if not action.target_id:
                self.last_result = "Error: target_id required for analyze_link"
            else:
                try:
                    idx = int(action.target_id.split('_')[-1])
                    if 0 <= idx < len(email.links):
                        link = email.links[idx]
                        if "scam" in link or "redirect?to=" in link or "githud" in link or "it-helpdesk-portal" in link or "company-benefits" in link:
                            self.last_result = f"Link analysis for {action.target_id}: MALICIOUS URL DETECTED"
                        else:
                            self.last_result = f"Link analysis for {action.target_id}: CLEAN"
                    else:
                        self.last_result = "Error: Link ID out of range."
                except Exception:
                    self.last_result = "Error: Invalid target_id format."
            reward = -0.05
        elif op == "scan_attachment":
             if not action.target_id:
                 self.last_result = "Error: target_id required for scan_attachment"
             else:
                 try:
                     idx = int(action.target_id.split('_')[-1])
                     if 0 <= idx < len(email.attachments):
                         att = email.attachments[idx]
                         if att.endswith(".exe") or att == "policy.doc":
                             self.last_result = f"Scan for {action.target_id}: MALWARE DETECTED"
                         else:
                             self.last_result = f"Scan for {action.target_id}: CLEAN"
                     else:
                         self.last_result = "Error: Attachment ID out of range."
                 except Exception:
                     self.last_result = "Error: Invalid target_id format."
             reward = -0.05
        elif op == "mark_safe":
            self.processed += 1
            if email.is_phishing:
                self.last_result = f"CRITICAL INCIDENT: Email {email.id} was phishing but marked safe! (False Negative)"
                reward = -1.0
                self.false_negatives += 1
            else:
                self.last_result = f"Email {email.id} correctly marked safe."
                reward = 1.0
                self.correct += 1
            self.inbox.remove(email)
        elif op == "mark_phishing":
            self.processed += 1
            if email.is_phishing:
                self.last_result = f"Email {email.id} correctly neutralized as phishing."
                reward = 1.0
                self.correct += 1
            else:
                if email.is_urgent_legit:
                    self.last_result = f"BUSINESS DISRUPTION: Blocked urgent legitimate email {email.id}! (False Positive)"
                    reward = -1.0
                else:
                    self.last_result = f"Email {email.id} was safe but marked phishing. (False Positive)"
                    reward = -0.5
                self.false_positives += 1
            self.inbox.remove(email)
        elif op == "escalate":
            self.processed += 1
            if email.is_urgent_legit:
                 self.last_result = f"BUSINESS DISRUPTION: Escalated urgent legitimate email {email.id}, causing delays!"
                 reward = -1.0
            else:
                self.last_result = f"Email {email.id} escalated to Tier-2. Safe action, but inefficient."
                reward = 0.0
            self.inbox.remove(email)
        else:
            self.last_result = f"Error: Unknown operation '{op}'"
            reward = -0.1

        self.score += reward
        
        if len(self.inbox) == 0:
            self.done = True
            self.last_result += " | Inbox is empty. Task complete."

        return self._get_observation(reward)

    @property
    def state(self) -> TriageState:
        return TriageState(
            episode_id=self.episode_id,
            step_count=self.step_count,
            total_emails_processed=self.processed,
            correct_classifications=self.correct,
            false_positives=self.false_positives,
            false_negatives=self.false_negatives,
            current_score=self.score
        )
