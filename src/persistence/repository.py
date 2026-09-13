"""Atomic, per-run JSON storage with typed deserialization."""

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Protocol
from uuid import UUID

from pydantic import ValidationError

from src.core.errors import PersistenceError
from src.schemas.run import RunState


class ResultRepository(Protocol):
    """Persistence boundary owned by the application service."""

    def save(self, result: RunState) -> RunState: ...

    def get(self, run_id: UUID) -> RunState | None: ...

    def find_by_idempotency_key(self, key: str) -> RunState | None: ...


class FileResultRepository:
    """Persist one immutable ``RunState`` as ``{run_id}.json``.

    A temporary file is fully flushed and fsynced before ``os.replace`` exposes
    it at the final path. Terminal artifacts are never intentionally overwritten.
    """

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = Path(output_dir)
        self._lock = Lock()

    @property
    def output_dir(self) -> Path:
        return self._output_dir

    def save(self, result: RunState) -> RunState:
        destination = self._path_for(result.run_id)
        with self._lock:
            directory = self._ensure_directory()
            if destination.exists():
                existing = self._read_path(destination, result.run_id)
                if existing == result:
                    return existing
                raise PersistenceError(
                    "A different terminal artifact already exists for this run.",
                    run_id=str(result.run_id),
                    operation="result_save",
                )

            temporary_path: Path | None = None
            try:
                with NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    prefix=f".{result.run_id}.",
                    suffix=".tmp",
                    dir=directory,
                    delete=False,
                ) as temporary_file:
                    temporary_path = Path(temporary_file.name)
                    json.dump(
                        result.model_dump(mode="json"),
                        temporary_file,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    temporary_file.flush()
                    os.fsync(temporary_file.fileno())
                os.replace(temporary_path, destination)
                self._sync_directory(directory)
                return result
            except PersistenceError:
                raise
            except (OSError, TypeError, ValueError) as exc:
                raise PersistenceError(
                    "The analysis result could not be saved.",
                    run_id=str(result.run_id),
                    operation="result_save",
                    context={"failure_type": type(exc).__name__},
                ) from exc
            finally:
                if temporary_path is not None:
                    try:
                        temporary_path.unlink(missing_ok=True)
                    except OSError:
                        pass

    def get(self, run_id: UUID) -> RunState | None:
        path = self._path_for(run_id)
        if not path.exists():
            return None
        return self._read_path(path, run_id)

    def find_by_idempotency_key(self, key: str) -> RunState | None:
        if not self._output_dir.exists():
            return None
        if not self._output_dir.is_dir():
            raise PersistenceError(
                "The analysis result directory is unavailable.",
                operation="idempotency_lookup",
            )
        try:
            paths = sorted(self._output_dir.glob("*.json"))
        except OSError as exc:
            raise PersistenceError(
                "Existing analysis results could not be checked.",
                operation="idempotency_lookup",
                context={"failure_type": type(exc).__name__},
            ) from exc
        for path in paths:
            result = self._read_path(path)
            if result.request.idempotency_key == key:
                return result
        return None

    def _ensure_directory(self) -> Path:
        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            if not self._output_dir.is_dir():
                raise NotADirectoryError(str(self._output_dir))
            return self._output_dir.resolve()
        except OSError as exc:
            raise PersistenceError(
                "The analysis result directory is unavailable.",
                operation="result_save",
                context={"failure_type": type(exc).__name__},
            ) from exc

    def _path_for(self, run_id: UUID) -> Path:
        return self._output_dir / f"{run_id}.json"

    def _read_path(self, path: Path, expected_run_id: UUID | None = None) -> RunState:
        try:
            with path.open(encoding="utf-8") as result_file:
                result = RunState.model_validate(json.load(result_file))
            if expected_run_id is not None and result.run_id != expected_run_id:
                raise ValueError("artifact run identity does not match its path")
            return result
        except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
            raise PersistenceError(
                "A persisted analysis result could not be read.",
                run_id=str(expected_run_id) if expected_run_id is not None else None,
                operation="result_read",
                context={"failure_type": type(exc).__name__},
            ) from exc

    @staticmethod
    def _sync_directory(directory: Path) -> None:
        """Best-effort metadata durability after an atomic rename."""

        if os.name == "nt":
            return
        descriptor: int | None = None
        try:
            descriptor = os.open(directory, os.O_RDONLY)
            os.fsync(descriptor)
        except OSError:
            # The replacement is still atomic; directory fsync support varies.
            pass
        finally:
            if descriptor is not None:
                os.close(descriptor)
