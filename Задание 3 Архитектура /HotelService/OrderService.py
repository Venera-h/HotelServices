import json
import threading
from confluent_kafka import Consumer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from event_bus import publish

# Словарь всех заказов: order_id → статус (PENDING / CONFIRMED / CANCELLED)
orders = {}

app = FastAPI()

# Разрешаем запросы с фронтенда (CORS)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Модель входящего запроса на создание заказа
class OrderRequest(BaseModel):
    order_id: str
    hotel_id: str
    amount: float

def create_order(order_id, hotel_id, amount):
    """
    Saga: шаг 1 — создаём заказ со статусом PENDING
    и публикуем событие OrderCreated в Kafka.
    HotelService подхватит это событие и попытается забронировать номер.
    """
    orders[order_id] = "PENDING"
    print(f"[OrderService] Заказ {order_id} создан (PENDING).")
    publish("OrderCreated", {"order_id": order_id, "hotel_id": hotel_id, "amount": amount})

@app.post("/orders")
def post_order(req: OrderRequest):
    # HTTP-эндпоинт для создания заказа с фронтенда
    create_order(req.order_id, req.hotel_id, req.amount)
    return {"order_id": req.order_id, "status": "PENDING"}

@app.get("/orders")
def get_orders():
    # Возвращает список всех заказов — используется фронтендом для истории заказов
    return [{"order_id": k, "status": v} for k, v in orders.items()]

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    # Возвращает статус конкретного заказа
    return {"order_id": order_id, "status": orders.get(order_id, "NOT_FOUND")}

# Обработчики Kafka-событий:
# PaymentCompleted  — оплата прошла, заказ подтверждён
# HotelReservationFailed — нет свободных номеров, заказ отменён
# PaymentFailed — оплата отклонена (компенсация), заказ отменён
handlers = {
    "PaymentCompleted":       lambda e: orders.update({e["order_id"]: "CONFIRMED"}) or print(f"[OrderService] Заказ {e['order_id']} подтверждён."),
    "HotelReservationFailed": lambda e: orders.update({e["order_id"]: "CANCELLED"}) or print(f"[OrderService] Заказ {e['order_id']} отменён — нет номеров."),
    "PaymentFailed":          lambda e: orders.update({e["order_id"]: "CANCELLED"}) or print(f"[OrderService] Заказ {e['order_id']} отменён — ошибка оплаты."),
}

def consume():
    """
    Kafka-консьюмер: слушает топики и вызывает нужный обработчик.
    Работает в отдельном потоке, чтобы не блокировать HTTP-сервер.
    """
    consumer = Consumer({
        "bootstrap.servers": "localhost:9092",
        "group.id": "order-service",
        "auto.offset.reset": "earliest"
    })
    consumer.subscribe(list(handlers.keys()))
    print("[OrderService] Ожидание событий...")
    while True:
        msg = consumer.poll(1.0)
        if msg and not msg.error():
            handlers[msg.topic()](json.loads(msg.value().decode("utf-8")))

if __name__ == "__main__":
    # Запускаем консьюмер в фоновом потоке
    threading.Thread(target=consume, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8004)
