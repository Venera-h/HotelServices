import json
import threading
from confluent_kafka import Consumer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from outbox import save
from event_bus import publish

# Инвентарь отелей: hotel_id → { rooms: кол-во свободных номеров, price: цена за ночь }
hotel_inventory = {
    "H1": {"rooms": 2, "price": 300},
    "H2": {"rooms": 0, "price": 150},
}

# Активные брони: order_id → hotel_id
reservations = {}

app = FastAPI()

# Разрешаем запросы с фронтенда (CORS)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Модель входящего запроса
class HotelRequest(BaseModel):
    hotel_id: str
    rooms: int
    price: int = 0  # цена за ночь (опционально)

@app.get("/inventory")
def get_inventory():
    # Возвращает список всех отелей с количеством номеров и ценой
    return hotel_inventory

@app.post("/hotels")
def add_hotel(req: HotelRequest):
    # Добавляет новый отель в инвентарь
    if req.hotel_id in hotel_inventory:
        return {"error": f"Отель {req.hotel_id} уже существует"}
    hotel_inventory[req.hotel_id] = {"rooms": req.rooms, "price": req.price}
    return {"hotel_id": req.hotel_id, "rooms": req.rooms, "price": req.price}

@app.put("/inventory/{hotel_id}")
def update_inventory(hotel_id: str, req: HotelRequest):
    # Пополняет количество номеров в существующем отеле
    if hotel_id not in hotel_inventory:
        return {"error": f"Отель {hotel_id} не найден"}
    hotel_inventory[hotel_id]["rooms"] += req.rooms
    return {"hotel_id": hotel_id, "rooms": hotel_inventory[hotel_id]["rooms"]}

@app.get("/reservations")
def get_reservations():
    # Возвращает все активные брони
    return reservations

@app.delete("/reservations/{order_id}")
def cancel_reservation(order_id: str):
    """
    Ручная отмена брони администратором.
    Outbox pattern: атомарно освобождаем номер и кладём PaymentFailed в outbox.
    """
    if order_id not in reservations:
        return {"error": f"Бронь {order_id} не найдена"}
    hotel_id = reservations[order_id]
    save(
        db_write=lambda: (
            reservations.pop(order_id),
            hotel_inventory[hotel_id].__setitem__("rooms", hotel_inventory[hotel_id]["rooms"] + 1),
        ),
        topic="PaymentFailed",
        payload={"order_id": order_id},
    )
    return {"order_id": order_id, "status": "CANCELLED"}

def handle_order_created(event):
    """
    Saga: шаг 2 — обработка события OrderCreated.
    Outbox pattern: атомарно обновляем reservations/inventory и кладём событие в outbox.
    """
    hotel_id = event["hotel_id"]
    order_id = event["order_id"]
    if hotel_inventory.get(hotel_id, {}).get("rooms", 0) > 0:
        print(f"[HotelService] Номер забронирован для заказа {order_id}.")
        save(
            db_write=lambda: (
                hotel_inventory[hotel_id].__setitem__("rooms", hotel_inventory[hotel_id]["rooms"] - 1),
                reservations.update({order_id: hotel_id}),
            ),
            topic="HotelReserved",
            payload={"order_id": order_id, "hotel_id": hotel_id, "amount": event["amount"]},
        )
    else:
        print(f"[HotelService] Нет свободных номеров в отеле {hotel_id}.")
        save(
            db_write=lambda: None,
            topic="HotelReservationFailed",
            payload={"order_id": order_id},
        )

def handle_payment_failed(event):
    """
    Saga: компенсирующая транзакция — обработка события PaymentFailed.
    Освобождаем номер обратно в инвентарь, если оплата не прошла.
    """
    order_id = event["order_id"]
    if order_id in reservations:
        hotel_inventory[reservations.pop(order_id)]["rooms"] += 1
        print(f"[HotelService] Компенсация: номер освобождён для заказа {order_id}.")

# Словарь обработчиков: топик Kafka → функция
handlers = {
    "OrderCreated":  handle_order_created,
    "PaymentFailed": handle_payment_failed,
}

def consume():
    """
    Kafka-консьюмер: слушает топики и вызывает нужный обработчик.
    Работает в отдельном потоке, чтобы не блокировать HTTP-сервер.
    auto.offset.reset=latest — читаем только новые события, не старые.
    """
    consumer = Consumer({
        "bootstrap.servers": "localhost:9092",
        "group.id": "hotel-service",
        "auto.offset.reset": "latest"
    })
    consumer.subscribe(list(handlers.keys()))
    print("[HotelService] Ожидание событий...")
    while True:
        msg = consumer.poll(1.0)
        if msg and not msg.error():
            handlers[msg.topic()](json.loads(msg.value().decode("utf-8")))

if __name__ == "__main__":
    # Запускаем консьюмер в фоновом потоке
    threading.Thread(target=consume, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8002)
