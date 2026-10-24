import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "claimguard.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with get_connection() as connection:
        connection.executescript(schema)


def add_approved_fact(
    company_name: str,
    fact_text: str,
    evidence_source: str,
):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO approved_facts
            (
                company_name,
                fact_text,
                evidence_source,
                approval_status
            )
            VALUES (?, ?, ?, 'PENDING')
            """,
            (
                company_name.strip(),
                fact_text.strip(),
                evidence_source.strip(),
            ),
        )


def get_approved_facts(company_name: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, company_name, fact_text, evidence_source
            FROM approved_facts
            WHERE company_name = ?
              AND approval_status = 'APPROVED'
            ORDER BY id
            """,
            (company_name,),
        ).fetchall()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    initialize_database()

    print("ClaimGuard database initialized.")
    print(f"Database location: {DB_PATH}")


def get_pending_facts() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, company_name, fact_text, evidence_source
            FROM approved_facts
            WHERE approval_status = 'PENDING'
            ORDER BY id
            """
        ).fetchall()

    return [dict(row) for row in rows]


def review_fact(fact_id: int, decision: str):
    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError("Invalid review decision.")

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE approved_facts
            SET approval_status = ?
            WHERE id = ? AND approval_status = 'PENDING'
            """,
            (decision, fact_id),
        )


def save_verification(
    company_name: str,
    claim_text: str,
    verification_status: str,
    reason: str,
):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO verification_history (
                company_name,
                claim_text,
                verification_status,
                reason
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                company_name.strip(),
                claim_text.strip(),
                verification_status,
                reason,
            ),
        )


def get_verification_history(limit: int = 50) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                company_name,
                claim_text,
                verification_status,
                reason,
                created_at
            FROM verification_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]