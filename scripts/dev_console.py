"""Local dev console — talk to the bot without a MAX token.

It runs the REAL pipeline (message_router → handlers → DB), but swaps the MAX
network client for a fake one that just prints the bot's replies. This lets you
play the whole product end to end while the bot is still under review.

Requirements: a reachable Postgres (the docker-compose `db` service is enough).

    docker compose up -d db          # start only Postgres
    # point DATABASE_URL at it (localhost), then:
    DATABASE_URL=postgresql+psycopg2://chrono:chrono@localhost:5432/chrono \
        python scripts/dev_console.py

Type messages as a user would. Special console commands:
    :user <id>     switch the simulated MAX user id (default: 1001)
    :name <name>   set the simulated display name
    :raw           show the raw MAX update that gets sent into the router
    :quit          exit
"""

from __future__ import annotations

import json
import sys

from app.db import engine, session_scope
from app.models import Base
from app.services.message_router import handle_update


class FakeMaxClient:
    """Stand-in for MaxClient: prints replies instead of calling MAX."""

    def send_message(self, user_id: str | int, text: str) -> bool:
        print(f"\n🤖 bot → user {user_id}:\n{text}\n")
        return True

    def set_webhook(self, url: str) -> bool:  # not used in console
        return True

    def close(self) -> None:
        pass


def build_update(user_id: str, name: str, text: str) -> dict:
    """Construct a MAX/TamTam-style message_created update."""
    return {
        "update_type": "message_created",
        "message": {
            "sender": {"user_id": user_id, "name": name},
            "recipient": {"chat_id": int(user_id), "chat_type": "dialog"},
            "body": {"text": text},
        },
    }


def main() -> None:
    # Dev convenience: create tables directly (skip Alembic for the sandbox).
    Base.metadata.create_all(engine)

    client = FakeMaxClient()
    user_id = "1001"
    name = "Тест"
    show_raw = False

    print("Dev-консоль бота. Пиши как пользователь. :quit для выхода.")
    print(f"Текущий пользователь: id={user_id}, name={name}\n")

    while True:
        try:
            line = input("👤 you: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue
        if line == ":quit":
            break
        if line.startswith(":user "):
            user_id = line.split(" ", 1)[1].strip()
            print(f"-> переключился на user id={user_id}")
            continue
        if line.startswith(":name "):
            name = line.split(" ", 1)[1].strip()
            print(f"-> display_name={name}")
            continue
        if line == ":raw":
            show_raw = not show_raw
            print(f"-> показ сырого update: {show_raw}")
            continue

        update = build_update(user_id, name, line)
        if show_raw:
            print("RAW:", json.dumps(update, ensure_ascii=False))

        with session_scope() as session:
            handle_update(update, session, max_client=client)


if __name__ == "__main__":
    sys.exit(main())
