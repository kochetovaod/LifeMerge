"""Lightweight fallback implementation of aiosqlite for offline testing.

This minimal subset wraps the standard ``sqlite3`` driver with asyncio
executors so SQLAlchemy's async SQLite dialect can run in environments
where the real ``aiosqlite`` package is unavailable.
"""
from __future__ import annotations

import asyncio
import sqlite3
from functools import partial
from typing import Any, Iterable, Optional

__all__ = ["connect", "Connection", "Cursor", "Row"]

# DB-API compatibility attributes expected by SQLAlchemy
Error = sqlite3.Error
Warning = sqlite3.Warning
InterfaceError = sqlite3.InterfaceError
DatabaseError = sqlite3.DatabaseError
DataError = sqlite3.DataError
OperationalError = sqlite3.OperationalError
IntegrityError = sqlite3.IntegrityError
InternalError = sqlite3.InternalError
ProgrammingError = sqlite3.ProgrammingError
NotSupportedError = sqlite3.NotSupportedError
paramstyle = "qmark"
threadsafety = 1
apilevel = "2.0"
version = sqlite3.version
sqlite_version = sqlite3.sqlite_version
sqlite_version_info = sqlite3.sqlite_version_info
version_info = sqlite3.version_info
Binary = sqlite3.Binary

Row = sqlite3.Row


class Cursor:
    def __init__(self, cursor: sqlite3.Cursor, loop: asyncio.AbstractEventLoop):
        self._cursor = cursor
        self._loop = loop

    @property
    def description(self):
        return self._cursor.description

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    async def execute(self, sql: str, parameters: Iterable[Any] | None = None):
        func = partial(self._cursor.execute, sql, parameters or [])
        await self._loop.run_in_executor(None, func)
        return self

    async def executemany(self, sql: str, seq_of_parameters: Iterable[Iterable[Any]]):
        func = partial(self._cursor.executemany, sql, seq_of_parameters)
        await self._loop.run_in_executor(None, func)
        return self

    async def fetchone(self):
        return await self._loop.run_in_executor(None, self._cursor.fetchone)

    async def fetchall(self):
        return await self._loop.run_in_executor(None, self._cursor.fetchall)

    async def fetchmany(self, size: int | None = None):
        func = partial(self._cursor.fetchmany, size) if size else self._cursor.fetchmany
        return await self._loop.run_in_executor(None, func)

    async def close(self):
        await self._loop.run_in_executor(None, self._cursor.close)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    def __await__(self):
        async def _return_self():
            return self

        return _return_self().__await__()


class Connection:
    def __init__(self, connection: sqlite3.Connection, loop: asyncio.AbstractEventLoop):
        self._connection = connection
        self._loop = loop
        self.daemon = False

    @property
    def total_changes(self) -> int:
        return self._connection.total_changes

    @property
    def row_factory(self):
        return self._connection.row_factory

    @row_factory.setter
    def row_factory(self, value):
        self._connection.row_factory = value

    @property
    def text_factory(self):
        return self._connection.text_factory

    @text_factory.setter
    def text_factory(self, value):
        self._connection.text_factory = value

    def cursor(self, *args, **kwargs) -> Cursor:
        return Cursor(self._connection.cursor(*args, **kwargs), self._loop)

    async def execute(self, sql: str, parameters: Iterable[Any] | None = None):
        cursor = self.cursor()
        await cursor.execute(sql, parameters)
        return cursor

    async def executemany(self, sql: str, seq_of_parameters: Iterable[Iterable[Any]]):
        cursor = self.cursor()
        await cursor.executemany(sql, seq_of_parameters)
        return cursor

    async def executescript(self, script: str):
        func = partial(self._connection.executescript, script)
        await self._loop.run_in_executor(None, func)
        return self

    async def create_function(self, *args, **kwargs):
        func = partial(self._connection.create_function, *args, **kwargs)
        await self._loop.run_in_executor(None, func)

    async def commit(self):
        await self._loop.run_in_executor(None, self._connection.commit)

    async def rollback(self):
        await self._loop.run_in_executor(None, self._connection.rollback)

    async def close(self):
        await self._loop.run_in_executor(None, self._connection.close)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc is None:
            await self.commit()
        else:
            await self.rollback()
        await self.close()

    def __await__(self):
        async def _return_self():
            return self

        return _return_self().__await__()

    def __getattr__(self, item: str) -> Any:
        return getattr(self._connection, item)


def connect(
    database: str,
    timeout: float = 5.0,
    detect_types: int = 0,
    isolation_level: Optional[str] = None,
    check_same_thread: bool = False,
    factory: type[sqlite3.Connection] | None = None,
    cached_statements: int = 128,
    uri: bool = False,
    loop: asyncio.AbstractEventLoop | None = None,
    **kwargs: Any,
) -> Connection:
    loop = loop or asyncio.get_event_loop()
    connect_kwargs = dict(
        database=database,
        timeout=timeout,
        detect_types=detect_types,
        isolation_level=isolation_level,
        check_same_thread=check_same_thread,
        factory=factory,
        cached_statements=cached_statements,
        uri=uri,
        **kwargs,
    )
    if factory is None:
        connect_kwargs.pop("factory")
    connection = sqlite3.connect(**connect_kwargs)
    # This fallback uses run_in_executor -> DB work can happen in a different thread.
    connect_kwargs["check_same_thread"] = False
    connection = sqlite3.connect(**connect_kwargs)
    return Connection(connection, loop)
