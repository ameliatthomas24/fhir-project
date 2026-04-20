import asyncpg
from fastapi import APIRouter, HTTPException, Request, status

from auth import create_access_token, verify_password
from auth_models import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    pool: asyncpg.Pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, hashed_password, role, fhir_patient_id FROM users WHERE email = $1",
            body.email,
        )

    if not row or not verify_password(body.password, row["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({
        "user_id": row["id"],
        "role": row["role"],
        "fhir_patient_id": row["fhir_patient_id"],
    })
    return TokenResponse(access_token=token, role=row["role"], user_id=row["id"])
