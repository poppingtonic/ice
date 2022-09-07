import asyncio

from asyncio import Future
from dataclasses import dataclass
from dataclasses import field
from time import monotonic_ns
from typing import Any

import ulid

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from ice.database import get_db_session
from ice.models import ErrorResponse
from ice.models import InformationResponse
from ice.models import Job
from ice.models import SessionResponse
from ice.peekable_queue import PeekableQueue

app = FastAPI()
log = get_logger()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JobWithFuture = tuple[Job, Future]


@dataclass
class Session:
    db: AsyncSession
    __jobs_q: PeekableQueue = field(default_factory=PeekableQueue)

    async def first_job(self) -> JobWithFuture:
        jwf = await self.__jobs_q.peek()
        return jwf

    def complete_job(self, job_id: str, result: Any | None) -> None:
        _priority, jwf = self.__jobs_q.get_nowait()
        job, future = jwf
        if job.id != job_id:
            log.error(
                "Attempt to complete jobs out of order",
                given_job=job_id,
                expected_job=job.id,
                queue_size=self.__jobs_q.qsize(),
            )
            raise RuntimeError("Attempt to complete jobs out of order")
        future.set_result(result)

    def enqueue_job(self, job: Job, future: Future):
        priority = monotonic_ns()
        self.__jobs_q.put_nowait((priority, (job, future)))


_sessions: dict[str, Session] = {}


@app.get("/")
def root():
    return {}


@app.post("/session", response_model=SessionResponse)
async def create_session(
    db: AsyncSession = Depends(get_db_session),
):

    from main import main_web

    session_id = ulid.new().str
    _sessions[session_id] = Session(db=db)
    asyncio.create_task(main_web(_sessions[session_id]))
    return SessionResponse(session_id=session_id)


@app.get(
    "/{session_id}/job",
    responses={
        200: {"model": Job},
        204: {},
        404: {"model": ErrorResponse},
    },
)
async def next_job(session_id: str):
    if session_id not in _sessions:
        return JSONResponse(status_code=404, content={"message": "session not found"})

    try:
        jwf: JobWithFuture = await asyncio.wait_for(
            _sessions[session_id].first_job(), timeout=20
        )
    except asyncio.TimeoutError:
        return Response(status_code=204)

    (job, _future) = jwf
    return job


@app.put(
    "/{session_id}/job/{job_id}",
    response_model=InformationResponse,
    responses={404: {"model": ErrorResponse}},
)
async def complete(*, session_id: str, job_id: str, answer: str | list[str]):
    if session_id not in _sessions:
        return JSONResponse(status_code=404, content={"message": "session not found"})

    try:
        _sessions[session_id].complete_job(job_id, answer)

    except KeyError:
        return JSONResponse(status_code=404, content={"message": "job not found"})
    return {"message": "job completed"}
