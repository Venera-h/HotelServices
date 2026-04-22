import json
import threading
from confluent_kafka import Consumer
from fastapi import FastAPI
import uvicorn
from event_bus import publish

# Лимит суммы, выше которого оплата отклоняется
PAYMENT_LIMIT = 500

app = FastAPI()

@app.get("/limit")
def get_limit():
    # Возвращает текущий лимит оплаты
    return {"payment_limit": PAYMENT_LIMIT}

def handle_hotel_reserved(event):
    """
    Saga: шаг 3 — обработка события HotelReserved.
    Если сумма заказа не превышает лимит — оплата проходит и публикуется PaymentCompleted.
    Иначе публикуется PaymentFailed, и HotelService компенсирует бронь.
    """
    order_id = event["order_id"]
    amount = event["amount"]
    if amount <= PAYMENT_LIMIT:
        print(f"[PaymentService] Оплата {amount} для заказа {order_id} прошла успешно.")
        publish("PaymentCompleted", {"order_id": order_id})
    else:
        print(f"[PaymentService] Оплата {amount} для заказа {order_id} отклонена (лимит {PAYMENT_LIMIT}).")
        publish("PaymentFailed", {"order_id": order_id})

# Словарь обработчиков: топик Kafka → функция
handlers = {
    "HotelReserved": handle_hotel_reserved,
}

def consume():
    """
    Kafka-консьюмер: слушает топики и вызывает нужный обработчик.
    Работает в отдельном потоке, чтобы не блокировать HTTP-сервер.
    """
    consumer = Consumer({
        "bootstrap.servers": "localhost:9092",
        "group.id": "payment-service",
        "auto.offset.reset": "earliest"
    })
    consumer.subscribe(list(handlers.keys()))
    print("[PaymentService] Ожидание событий...")
    while True:
        msg = consumer.poll(1.0)
        if msg and not msg.error():
            handlers[msg.topic()](json.loads(msg.value().decode("utf-8")))

if __name__ == "__main__":
    # Запускаем консьюмер в фоновом потоке
    threading.Thread(target=consume, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8003)
