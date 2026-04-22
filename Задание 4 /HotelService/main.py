import time
from OrderService import create_order

# Небольшая пауза, чтобы консьюмеры успели подключиться
time.sleep(1)

print("=" * 50)
print("Сценарий 1: Успешное бронирование")
print("=" * 50)
create_order(order_id="ORD-001", hotel_id="H1", amount=300)

time.sleep(1)

print("\n" + "=" * 50)
print("Сценарий 2: Нет свободных номеров")
print("=" * 50)
create_order(order_id="ORD-002", hotel_id="H2", amount=200)

time.sleep(1)

print("\n" + "=" * 50)
print("Сценарий 3: Оплата отклонена — компенсация")
print("=" * 50)
create_order(order_id="ORD-003", hotel_id="H1", amount=999)
