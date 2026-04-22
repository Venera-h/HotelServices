import json
from confluent_kafka import Producer
from schema_registry import validate

# Kafka-продюсер — отправляет события в топики
producer = Producer({"bootstrap.servers": "localhost:9092"})

def publish(topic, payload):
    """
    Публикует событие в Kafka-топик.
    Перед отправкой валидирует payload по Schema Registry.
    topic   — название события (например, "OrderCreated", "HotelReserved")
    payload — данные события в виде словаря, сериализуются в JSON
    """
    validate(topic, payload)
    print(f"\n[Kafka] >>> {topic}: {payload}")
    producer.produce(topic, json.dumps(payload).encode("utf-8"))
    producer.flush()  # Гарантирует что сообщение отправлено до выхода из функции
