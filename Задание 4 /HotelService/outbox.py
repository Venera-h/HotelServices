"""
Outbox Pattern (in-memory).

Вместо прямой публикации в Kafka:
  1. save(db_write, topic, payload) — атомарно обновляет "БД" и кладёт запись в outbox.
  2. relay() — фоновый поток читает outbox и публикует в Kafka, затем помечает как sent.
"""

import threading
import uuid
from event_bus import publish

# Outbox: список записей {"id", "topic", "payload", "sent"}
_outbox: list[dict] = []
_lock = threading.Lock()


def save(db_write: callable, topic: str, payload: dict) -> None:
    """Атомарно выполняет db_write() и добавляет событие в outbox."""
    with _lock:
        db_write()
        _outbox.append({"id": str(uuid.uuid4()), "topic": topic, "payload": payload, "sent": False})


def _relay():
    """Фоновый поток: публикует неотправленные записи из outbox в Kafka."""
    import time
    while True:
        with _lock:
            pending = [r for r in _outbox if not r["sent"]]
        for record in pending:
            try:
                publish(record["topic"], record["payload"])
                with _lock:
                    record["sent"] = True
            except Exception as e:
                print(f"[Outbox] Ошибка публикации {record['topic']}: {e}")
        time.sleep(0.1)


# Запускаем relay при импорте модуля
threading.Thread(target=_relay, daemon=True).start()
