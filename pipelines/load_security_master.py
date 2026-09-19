r"""Load config/securities.json into the securities table (idempotent).

    .venv\Scripts\python -m pipelines.load_security_master
"""
import json
from datetime import date

from packages.core.config import settings
from packages.database.models import Security
from packages.database.session import SessionLocal


def main() -> None:
    data = json.loads((settings.CONFIG_DIR / "securities.json").read_text(encoding="utf-8"))
    with SessionLocal() as session:
        for row in data["securities"]:
            row = {**row, "verified_at": date.fromisoformat(row["verified_at"])}
            session.merge(Security(**row))
        session.commit()
        print(f"Loaded {len(data['securities'])} securities")


if __name__ == "__main__":
    main()
