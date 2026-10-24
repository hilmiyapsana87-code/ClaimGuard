CREATE TABLE IF NOT EXISTS approved_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    fact_text TEXT NOT NULL,
    evidence_source TEXT NOT NULL,
    approval_status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (
            approval_status IN (
                'APPROVED',
                'PENDING',
                'REJECTED'
            )
        ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verification_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);