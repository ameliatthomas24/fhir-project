import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import asyncpg
from auth import hash_password

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id         SERIAL PRIMARY KEY,
    email      TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role       TEXT NOT NULL CHECK (role IN ('clinician', 'patient')),
    fhir_patient_id TEXT
)
"""

SEED_USERS = [
    {
        "email": "clinician@demo.com",
        "password": "clinician123",
        "role": "clinician",
        "fhir_patient_id": None,
    },
    {
        "email": "patient1@demo.com",
        "password": "patient123",
        "role": "patient",
        "fhir_patient_id": None,  
    },
    {
        "email": "patient2@demo.com",
        "password": "patient456",
        "role": "patient",
        "fhir_patient_id": None,  
    },
    {
        "email": "patient3@demo.com",
        "password": "patient789",
        "role": "patient",
        "fhir_patient_id": None,  
    },
]


async def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)

    conn = await asyncpg.connect(db_url)
    try:
        await conn.execute(CREATE_USERS_TABLE)
        for u in SEED_USERS:
            existing = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1", u["email"]
            )
            if existing:
                print(f"  skipped (exists): {u['email']}")
                continue
            await conn.execute(
                """INSERT INTO users (email, hashed_password, role, fhir_patient_id)
                   VALUES ($1, $2, $3, $4)""",
                u["email"],
                hash_password(u["password"]),
                u["role"],
                u["fhir_patient_id"],
            )
            print(f"  created: {u['email']}  role={u['role']}")
    finally:
        await conn.close()

    print("Done.")


asyncio.run(main())
