from typing import Any, Optional

from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    context: str
    final_answer: str
    score: float
    tool_output: Optional[Any] = None
