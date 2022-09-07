from typing import Literal
from typing import Optional
from typing import Union

import ulid

from pydantic import BaseModel
from pydantic import Field

JobType = Literal["spinner", "print", "checkboxes", "answer", "score", "select"]


class ErrorResponse(BaseModel):
    message: str


class InformationResponse(BaseModel):
    message: str


class SessionResponse(BaseModel):
    session_id: str


class _BaseJob(BaseModel):
    id: str = Field(default_factory=lambda: ulid.new().str)
    type: JobType


class PrintJob(_BaseJob):
    type: Literal["print"] = "print"
    message: str
    format_markdown: bool = False
    wait_for_confirmation: bool = False


class AnswerJob(_BaseJob):
    type: Literal["answer"] = "answer"
    prompt: str
    default: str = ""
    multiline: bool = False


class CheckboxesJob(_BaseJob):
    type: Literal["checkboxes"] = "checkboxes"
    prompt: Optional[str] = None
    choices: list[str]


class SelectJob(_BaseJob):
    type: Literal["select"] = "select"
    prompt: Optional[str] = None
    choices: list[str]


class ScoreJob(_BaseJob):
    type: Literal["score"] = "score"
    prompt: str
    default: Optional[float] = None


Job = Union[PrintJob, AnswerJob, CheckboxesJob, ScoreJob, SelectJob]
