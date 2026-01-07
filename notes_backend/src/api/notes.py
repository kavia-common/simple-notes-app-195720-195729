from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

from src.api.db import get_connection

router = APIRouter(prefix="/notes", tags=["notes"])


class NoteBase(BaseModel):
    """Shared note fields."""

    title: str = Field(..., min_length=1, max_length=200, description="Note title")
    content: str = Field(..., min_length=1, max_length=20000, description="Note content/body")


class NoteCreate(NoteBase):
    """Payload to create a note."""


class NoteUpdate(BaseModel):
    """Payload to update a note (partial updates supported)."""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated note title")
    content: Optional[str] = Field(None, min_length=1, max_length=20000, description="Updated note content/body")


class NoteOut(NoteBase):
    """A note as returned by the API."""

    id: int = Field(..., description="Unique note identifier")
    created_at: str = Field(..., description="ISO timestamp when created")
    updated_at: str = Field(..., description="ISO timestamp when last updated")


def _row_to_note(row: sqlite3.Row) -> NoteOut:
    return NoteOut(
        id=int(row["id"]),
        title=str(row["title"]),
        content=str(row["content"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


@router.get(
    "",
    response_model=List[NoteOut],
    summary="List notes",
    description="Returns all notes sorted by most recently updated first.",
    operation_id="list_notes",
)
def list_notes() -> List[NoteOut]:
    """List all notes."""
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                SELECT id, title, content, created_at, updated_at
                FROM notes
                ORDER BY datetime(updated_at) DESC, id DESC
                """
            )
            rows = cur.fetchall()
            return [_row_to_note(r) for r in rows]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e


@router.post(
    "",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create note",
    description="Creates a new note and returns it.",
    operation_id="create_note",
)
def create_note(payload: NoteCreate) -> NoteOut:
    """Create a note."""
    now = datetime.utcnow().isoformat()
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO notes (title, content, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (payload.title, payload.content, now, now),
            )
            note_id = cur.lastrowid
            row = conn.execute(
                """
                SELECT id, title, content, created_at, updated_at
                FROM notes
                WHERE id = ?
                """,
                (note_id,),
            ).fetchone()
            return _row_to_note(row)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e


@router.get(
    "/{note_id}",
    response_model=NoteOut,
    summary="Get note",
    description="Returns a single note by id.",
    operation_id="get_note",
)
def get_note(note_id: int) -> NoteOut:
    """Fetch a single note by ID."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, title, content, created_at, updated_at
                FROM notes
                WHERE id = ?
                """,
                (note_id,),
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Note not found")
            return _row_to_note(row)
    except HTTPException:
        raise
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e


@router.put(
    "/{note_id}",
    response_model=NoteOut,
    summary="Update note",
    description="Updates a note by id and returns the updated note.",
    operation_id="update_note",
)
def update_note(note_id: int, payload: NoteUpdate) -> NoteOut:
    """Update a note by ID (partial updates supported)."""
    if payload.title is None and payload.content is None:
        raise HTTPException(status_code=422, detail="At least one of 'title' or 'content' must be provided")

    now = datetime.utcnow().isoformat()
    try:
        with get_connection() as conn:
            existing = conn.execute(
                """
                SELECT id, title, content, created_at, updated_at
                FROM notes
                WHERE id = ?
                """,
                (note_id,),
            ).fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Note not found")

            new_title = payload.title if payload.title is not None else str(existing["title"])
            new_content = payload.content if payload.content is not None else str(existing["content"])

            conn.execute(
                """
                UPDATE notes
                SET title = ?, content = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_title, new_content, now, note_id),
            )

            row = conn.execute(
                """
                SELECT id, title, content, created_at, updated_at
                FROM notes
                WHERE id = ?
                """,
                (note_id,),
            ).fetchone()
            return _row_to_note(row)
    except HTTPException:
        raise
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete note",
    description="Deletes a note by id.",
    operation_id="delete_note",
)
def delete_note(note_id: int) -> Response:
    """Delete a note by ID. Returns HTTP 204 with an empty body on success."""
    try:
        with get_connection() as conn:
            cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Note not found")

        # Explicit empty response (FastAPI enforces: 204 must not have a body).
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e

