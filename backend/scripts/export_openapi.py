import json
from pathlib import Path

from app.main import app


def main() -> None:
    snapshot = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.json"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(
        json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {snapshot}")


if __name__ == "__main__":
    main()
