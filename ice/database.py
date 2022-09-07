import json
import re

import ulid

from fastapi import encoders
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Column
from sqlmodel import Field
from sqlmodel import SQLModel
from structlog import get_logger

from ice import events
from ice import execution_context
from ice.settings import settings

log = get_logger()


class NodeResult(SQLModel, table=True):  # type: ignore[call-arg]
    __table_args__ = {"keep_existing": True}  # For streamlit

    id: str = Field(
        default_factory=lambda: ulid.new().str, primary_key=True, nullable=False
    )
    name: str = Field(nullable=False, index=True)
    recipe: str = Field(nullable=False, index=True)
    inputs: dict = Field(default={}, sa_column=Column(JSONB))
    result: dict = Field(default={}, sa_column=Column(JSONB))
    context: dict = Field(default={}, sa_column=Column(JSONB))

    # Needed for Column(JSONB)
    class Config:
        arbitrary_types_allowed = True


def db_url() -> str:
    return re.sub(r"^.*://", "postgresql+asyncpg://", settings.DATABASE_URL)


def safe_serializer(obj):
    """I work better than json.dumps to serialize arbitrary objects."""
    return json.dumps(encoders.jsonable_encoder(obj))


engine = create_async_engine(db_url(), future=True, json_serializer=safe_serializer)


async def get_db_session() -> AsyncSession:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        return session


@events.on("node_completed")
async def _store_completion(*, node_name, recipe, inputs, result) -> None:
    context = execution_context.context()

    log.debug(
        "storing node completion",
        name=node_name,
        recipe=recipe,
        inputs=inputs,
        result={"result": result},
        context=context,
    )
    record = NodeResult(
        name=node_name,
        recipe=recipe,
        inputs=inputs,
        result={"result": result},
        context=context,
    )
    db_session = await get_db_session()
    db_session.add(record)
    await db_session.commit()
