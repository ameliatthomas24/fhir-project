from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from auth import get_current_user, require_patient_access

router = APIRouter()


# ── Pydantic models ──────────────────────────────────────────────────────────

class NoteIn(BaseModel):
    id: str
    content: str
    createdAt: str
    author: str

class NoteOut(BaseModel):
    id: str
    content: str
    createdAt: str
    author: str

class AppointmentIn(BaseModel):
    id: str
    date: str
    time: str
    type: str
    reason: str
    status: str = "upcoming"
    patient_name: Optional[str] = None

class AppointmentOut(BaseModel):
    id: str
    date: str
    time: str
    type: str
    reason: str
    status: str

class AppointmentAllOut(BaseModel):
    id: str
    patient_id: str
    patient_name: Optional[str]
    date: str
    time: str
    type: str
    reason: str
    status: str

class MessageIn(BaseModel):
    id: str
    patientName: str
    subject: str
    body: str
    sentAt: str
    fromRole: str = "patient"

class MessageOut(BaseModel):
    id: str
    patientId: str
    patientName: str
    subject: str
    body: str
    sentAt: str
    read: bool
    reply: Optional[str] = None
    patientRead: bool
    fromRole: str

class ReplyIn(BaseModel):
    reply: str


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ── Notes ────────────────────────────────────────────────────────────────────

@router.get("/notes/{patient_id}", response_model=list[NoteOut])
async def get_notes(
    patient_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    require_patient_access(patient_id, current_user)
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, content, created_at, author FROM notes WHERE patient_id = $1 ORDER BY created_at DESC",
            patient_id,
        )
    return [NoteOut(id=r["id"], content=r["content"], createdAt=r["created_at"].isoformat(), author=r["author"]) for r in rows]


@router.post("/notes/{patient_id}", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    patient_id: str,
    body: NoteIn,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    require_patient_access(patient_id, current_user)
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO notes (id, patient_id, content, created_at, author) VALUES ($1, $2, $3, $4, $5)",
            body.id, patient_id, body.content, _parse_dt(body.createdAt), body.author,
        )
    return NoteOut(id=body.id, content=body.content, createdAt=body.createdAt, author=body.author)


# ── Appointments ─────────────────────────────────────────────────────────────

@router.get("/appointments/{patient_id}", response_model=list[AppointmentOut])
async def get_appointments(
    patient_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    require_patient_access(patient_id, current_user)
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, date, time, type, reason, status FROM appointments WHERE patient_id = $1 ORDER BY date DESC, time DESC",
            patient_id,
        )
    return [AppointmentOut(id=r["id"], date=r["date"], time=r["time"], type=r["type"], reason=r["reason"], status=r["status"]) for r in rows]


@router.post("/appointments/{patient_id}", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    patient_id: str,
    body: AppointmentIn,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    require_patient_access(patient_id, current_user)
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO appointments (id, patient_id, patient_name, date, time, type, reason, status) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
            body.id, patient_id, body.patient_name, body.date, body.time, body.type, body.reason, body.status,
        )
    return AppointmentOut(id=body.id, date=body.date, time=body.time, type=body.type, reason=body.reason, status=body.status)


@router.get("/appointments", response_model=list[AppointmentAllOut])
async def get_all_appointments(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "clinician":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinician access required")
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, patient_id, patient_name, date, time, type, reason, status FROM appointments ORDER BY date ASC, time ASC"
        )
    return [AppointmentAllOut(id=r["id"], patient_id=r["patient_id"], patient_name=r["patient_name"], date=r["date"], time=r["time"], type=r["type"], reason=r["reason"], status=r["status"]) for r in rows]


@router.get("/messages", response_model=list[MessageOut])
async def get_all_messages(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "clinician":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinician access required")
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, patient_id, patient_name, subject, body, sent_at, read, reply, patient_read, from_role "
            "FROM messages ORDER BY sent_at DESC"
        )
    return [
        MessageOut(
            id=r["id"],
            patientId=r["patient_id"],
            patientName=r["patient_name"],
            subject=r["subject"],
            body=r["body"],
            sentAt=r["sent_at"].isoformat(),
            read=r["read"],
            reply=r["reply"],
            patientRead=r["patient_read"],
            fromRole=r["from_role"],
        )
        for r in rows
    ]


# ── Messages ─────────────────────────────────────────────────────────────────

@router.get("/messages/{patient_id}", response_model=list[MessageOut])
async def get_messages(
    patient_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    require_patient_access(patient_id, current_user)
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, patient_name, subject, body, sent_at, read, reply, patient_read, from_role "
            "FROM messages WHERE patient_id = $1 ORDER BY sent_at DESC",
            patient_id,
        )
    return [
        MessageOut(
            id=r["id"],
            patientId=patient_id,
            patientName=r["patient_name"],
            subject=r["subject"],
            body=r["body"],
            sentAt=r["sent_at"].isoformat(),
            read=r["read"],
            reply=r["reply"],
            patientRead=r["patient_read"],
            fromRole=r["from_role"],
        )
        for r in rows
    ]


@router.post("/messages/{patient_id}", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    patient_id: str,
    body: MessageIn,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    require_patient_access(patient_id, current_user)
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO messages (id, patient_id, patient_name, subject, body, sent_at, from_role) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            body.id, patient_id, body.patientName, body.subject, body.body, _parse_dt(body.sentAt), body.fromRole,
        )
    return MessageOut(
        id=body.id,
        patientId=patient_id,
        patientName=body.patientName,
        subject=body.subject,
        body=body.body,
        sentAt=body.sentAt,
        read=False,
        patientRead=False,
        fromRole=body.fromRole,
    )


@router.patch("/messages/{patient_id}/{message_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    patient_id: str,
    message_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    require_patient_access(patient_id, current_user)
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE messages SET read = TRUE WHERE id = $1 AND patient_id = $2",
            message_id, patient_id,
        )


@router.patch("/messages/{patient_id}/{message_id}/reply", response_model=MessageOut)
async def reply_message(
    patient_id: str,
    message_id: str,
    body: ReplyIn,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    require_patient_access(patient_id, current_user)
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE messages SET reply = $1, patient_read = FALSE WHERE id = $2 AND patient_id = $3",
            body.reply, message_id, patient_id,
        )
        row = await conn.fetchrow(
            "SELECT id, patient_name, subject, body, sent_at, read, reply, patient_read, from_role FROM messages WHERE id = $1",
            message_id,
        )
    return MessageOut(
        id=row["id"],
        patientId=patient_id,
        patientName=row["patient_name"],
        subject=row["subject"],
        body=row["body"],
        sentAt=row["sent_at"].isoformat(),
        read=row["read"],
        reply=row["reply"],
        patientRead=row["patient_read"],
        fromRole=row["from_role"],
    )


@router.patch("/messages/{patient_id}/{message_id}/patient-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_patient_read(
    patient_id: str,
    message_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    require_patient_access(patient_id, current_user)
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE messages SET patient_read = TRUE WHERE id = $1 AND patient_id = $2",
            message_id, patient_id,
        )
