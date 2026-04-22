"""
Schema Registry (in-memory).

Регистрирует JSON-схемы для топиков Kafka и валидирует payload перед публикацией.
Используется для топиков, где не применяется Outbox pattern (choreography-события).
"""

import jsonschema

# Реестр схем: topic → JSON Schema
_registry: dict[str, dict] = {}


def register(topic: str, schema: dict) -> None:
    """Регистрирует схему для топика."""
    _registry[topic] = schema


def validate(topic: str, payload: dict) -> None:
    """Валидирует payload по зарегистрированной схеме. Бросает ValueError при ошибке."""
    schema = _registry.get(topic)
    if schema is None:
        return  # схема не зарегистрирована — пропускаем
    try:
        jsonschema.validate(instance=payload, schema=schema)
    except jsonschema.ValidationError as e:
        raise ValueError(f"[SchemaRegistry] Невалидный payload для топика '{topic}': {e.message}")


# ── Схемы для всех choreography-топиков ──────────────────────────────────────

register("OrderCreated", {
    "type": "object",
    "required": ["order_id", "hotel_id", "amount"],
    "properties": {
        "order_id": {"type": "string"},
        "hotel_id": {"type": "string"},
        "amount":   {"type": "number"},
    },
    "additionalProperties": False,
})

register("HotelReserved", {
    "type": "object",
    "required": ["order_id", "hotel_id", "amount"],
    "properties": {
        "order_id": {"type": "string"},
        "hotel_id": {"type": "string"},
        "amount":   {"type": "number"},
    },
    "additionalProperties": False,
})

register("HotelReservationFailed", {
    "type": "object",
    "required": ["order_id"],
    "properties": {
        "order_id": {"type": "string"},
    },
    "additionalProperties": False,
})

register("PaymentCompleted", {
    "type": "object",
    "required": ["order_id"],
    "properties": {
        "order_id": {"type": "string"},
    },
    "additionalProperties": False,
})

register("PaymentFailed", {
    "type": "object",
    "required": ["order_id"],
    "properties": {
        "order_id": {"type": "string"},
    },
    "additionalProperties": False,
})
