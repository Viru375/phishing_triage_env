---
title: Phishing Triage Env
emoji: 📧
colorFrom: blue
colorTo: red
sdk: docker
pinned: false
---

# Phishing Email Triage Analyst (OpenEnv)

A complete, real-world OpenEnv-compliant Reinforcement Learning environment for a **Tier-1 SOC Phishing Email Triage Analyst**. 
Designed for the OpenEnv Hackathon.

## Motivation
This environment directly models the daily operations of a Tier-1 Security Operations Center (SOC) analyst evaluating an inbox queue of emails. It moves beyond toy games by requiring the AI agent to utilize standard security tooling (inspecting SPF/DKIM headers, analyzing URLs, and scanning attachments) to uncover advanced spear-phishing and evasion attempts, while penalizing them heavily for blocking urgent legitimate business communications (false positives).

## Spaces

### Observation Space
The agent receives a `TriageObservation` mapping representing the SOC Dashboard:
- `inbox`: A list of currently queued emails showing `id`, `sender`, `subject`, `body_snippet` and counts of links/attachments.
- `last_action_result`: The textual result of the tool just used (e.g. malware detected, SPF failed).
- `current_score`: The agent's current tally.

### Action Space
The agent can execute `TriageAction` mapping with the following operations:
- `inspect_headers`: Reveals SPF/DKIM/DMARC status.
- `analyze_link`: Returns URL reputation (simulated sandbox).
- `scan_attachment`: Returns antivirus scan result.
- `mark_safe`: Consumes the email and marks it harmless.
- `mark_phishing`: Consumes the email and neutralizes it.
- `escalate`: Consumes the email and defers to Tier-2.

## Tasks & Difficulty
There are 3 built-in tasks with deterministic graders (0.0 to 1.0):
1. **Easy Task**: 3 emails containing obvious Nigerian prince scams, bad links, and clear internal HR emails.
2. **Medium Task**: 5 emails introducing spear-phishing, where the sender address is spoofed to look exactly like the CEO, but SPF/DKIM validation via `inspect_headers` will flag it.
3. **Hard Task**: 10 emails featuring advanced evasion (clean URLs that redirect to malicious ones), weaponized attachments named `policy.doc`, mixed with highly urgent legitimate executive emails (like a Merger Term Sheet).

## Setup & Usage

### 1. Locally with Uvicorn
```bash
uv pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### 2. Docker
```bash
docker build -t phishing-triage-env .
docker run -p 8000:8000 phishing-triage-env
```

### 3. Inference / Evaluation
Start the server, export your key, and run the baseline:
```bash
export OPENAI_API_KEY="sk-..."
python baseline.py
```

## Baseline Scores
Running `baseline.py` using `gpt-4o-mini` consistently solves the Easy task (Score: 1.0) and struggles appropriately on Medium and Hard tasks as it forgets to scan specific obfuscated attachments or escalate urgent queries. 
