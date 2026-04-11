---
title: Phishing Triage Env
emoji: 🛡️
colorFrom: blue
colorTo: red
sdk: docker
pinned: false
license: mit
---

# Phishing Triage RL Environment

An OpenEnv-compliant Reinforcement Learning environment where an agent acts as a SaaS account manager trying to collect overdue invoices from clients without causing them to churn.

## Environment Details

- **Task**: SaaS Invoice Collection Simulator
- **Action Space**: Discrete (3 actions: WAIT, POLITE_REMINDER, FIRM_WARNING)
- **Observation Space**: `days_overdue`, `client_patience`, `invoice_paid`
- **Reward Range**: [-50, +50]

## Graded Tasks

| ID | Name | Description |
|----|------|-------------|
| 0 | Easy — Polite Collection | Client has high patience |
| 1 | Medium — Impatient Client | Reduced patience, balance urgency |
| 2 | Hard — Last-Minute Collection | 20 days overdue, aggressive tactics needed |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| POST | `/reset` | Reset environment |
| POST | `/step` | Take one step |
| GET | `/state` | Get current state |
| GET | `/tasks` | List graded tasks |
| POST | `/grader/{task_id}` | Run graded episode |
| POST | `/v1/chat/completions` | OpenAI-compatible endpoint |
