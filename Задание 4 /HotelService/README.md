# 🏨 Hotel Booking — Saga Choreography

Учебный проект, демонстрирующий паттерн **Saga Choreography** на примере бронирования отеля.  
Три независимых микросервиса координируются через события Kafka без центрального оркестратора.

---

## Архитектура

```
Пользователь
     │
     ▼
[React Frontend] :3002
     │
     ├──► [OrderService]  :8004
     ├──► [HotelService]  :8002
     └──► [PaymentService]:8003
              │
         [Kafka] :9092
```

---

## Сервисы

| Сервис | Порт | Описание |
|---|---|---|
| OrderService | 8004 | Создаёт заказы, отслеживает статусы |
| HotelService | 8002 | Управляет инвентарём и бронями |
| PaymentService | 8003 | Обрабатывает оплату |
| React Frontend | 3002 | UI для управления системой |

---

## Saga — цепочка событий

### ✅ Успешное бронирование
```
OrderService  →  OrderCreated
HotelService  →  HotelReserved       (номер забронирован)
PaymentService → PaymentCompleted    (оплата прошла)
OrderService  →  статус: CONFIRMED
```

### ❌ Нет свободных номеров
```
OrderService  →  OrderCreated
HotelService  →  HotelReservationFailed  (нет мест)
OrderService  →  статус: CANCELLED
```

### ❌ Оплата отклонена (компенсация)
```
OrderService  →  OrderCreated
HotelService  →  HotelReserved       (номер забронирован)
PaymentService → PaymentFailed       (сумма превышает лимит 500₽)
HotelService  →  компенсация: номер освобождён
OrderService  →  статус: CANCELLED
```

---

## Запуск

### 1. Запустить Kafka
Kafka должна быть запущена на `localhost:9092`.

### 2. Запустить сервисы (каждый в отдельном терминале)

```bash
python3 OrderService.py    # порт 8004
python3 HotelService.py    # порт 8002
python3 PaymentService.py  # порт 8003
```

### 3. Запустить фронтенд

```bash
cd ../hotel-frontend
npm install
npm start                  # порт 3002
```

### 4. Открыть в браузере

```
http://localhost:3002
```

---

## API

### OrderService `:8004`
| Метод | Путь | Описание |
|---|---|---|
| POST | `/orders` | Создать заказ |
| GET | `/orders` | Список всех заказов |
| GET | `/orders/{order_id}` | Статус заказа |

### HotelService `:8002`
| Метод | Путь | Описание |
|---|---|---|
| GET | `/inventory` | Список отелей с ценами |
| POST | `/hotels` | Добавить отель |
| PUT | `/inventory/{hotel_id}` | Пополнить номера |
| GET | `/reservations` | Активные брони |
| DELETE | `/reservations/{order_id}` | Отменить бронь |

### PaymentService `:8003`
| Метод | Путь | Описание |
|---|---|---|
| GET | `/limit` | Текущий лимит оплаты |

---

## Структура проекта

```
HotelService/
├── event_bus.py       # Kafka-продюсер, публикация событий
├── OrderService.py    # Сервис заказов
├── HotelService.py    # Сервис отелей
├── PaymentService.py  # Сервис оплаты
├── main.py            # Скрипт для запуска тестовых сценариев
└── scenarios.md       # Описание тестовых сценариев

hotel-frontend/
└── src/
    └── App.tsx        # React UI
```

---

## Зависимости

```bash
pip install fastapi uvicorn confluent-kafka pydantic
```
