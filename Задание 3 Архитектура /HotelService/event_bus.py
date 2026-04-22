import json
from confluent_kafka import Producer

# Kafka-продюсер — отправляет события в топики
producer = Producer({"bootstrap.servers": "localhost:9092"})

def publish(topic, payload):
    """
    Публикует событие в Kafka-топик.
    topic   — название события (например, "OrderCreated", "HotelReserved")
    payload — данные события в виде словаря, сериализуются в JSON
    """
    print(f"\n[Kafka] >>> {topic}: {payload}")
    producer.produce(topic, json.dumps(payload).encode("utf-8"))
    producer.flush()  # Гарантирует что сообщение отправлено до выхода из функции
