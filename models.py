from pydantic import BaseModel
from enum import IntEnum

class Action(IntEnum):
    WAIT = 0
    POLITE_REMINDER = 1
    FIRM_WARNING = 2

class Observation(BaseModel):
    days_overdue: int
    client_patience: int
    invoice_paid: bool

class State(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: dict
