import React, { useEffect, useState } from "react";
import axios from "axios";

const API = "http://localhost:8002";
const ORDER_API = "http://localhost:8004";

export default function App() {
  const [inventory, setInventory] = useState<Record<string, number>>({});
  const [reservations, setReservations] = useState<Record<string, string>>({});
  const [hotelId, setHotelId] = useState("");
  const [rooms, setRooms] = useState(0);
  const [refillHotelId, setRefillHotelId] = useState("");
  const [refillRooms, setRefillRooms] = useState(0);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<"success" | "error">("success");

  // Форма заказа
  const [orderId, setOrderId] = useState("");
  const [orderHotelId, setOrderHotelId] = useState("");
  const [orderAmount, setOrderAmount] = useState(0);

  const fetchAll = async () => {
    const [inv, res] = await Promise.all([
      axios.get(`${API}/inventory`),
      axios.get(`${API}/reservations`),
    ]);
    setInventory(inv.data);
    setReservations(res.data);
  };

  useEffect(() => { fetchAll(); }, []);

  const notify = (msg: string, type: "success" | "error" = "success") => {
    setMessage(msg);
    setMessageType(type);
    setTimeout(() => setMessage(""), 4000);
  };

  const createOrder = async () => {
    // Проверяем наличие мест до отправки
    const available = inventory[orderHotelId] ?? 0;
    if (available === 0) {
      notify(`❌ Нет свободных номеров в отеле ${orderHotelId}`, "error");
      return;
    }
    try {
      await axios.post(`${ORDER_API}/orders`, {
        order_id: orderId,
        hotel_id: orderHotelId,
        amount: orderAmount,
      });
      notify(`✅ Заказ ${orderId} создан! Ожидайте подтверждения.`);
      setOrderId(""); setOrderHotelId(""); setOrderAmount(0);
      setTimeout(fetchAll, 1500);
    } catch {
      notify("❌ Ошибка при создании заказа", "error");
    }
  };

  const addHotel = async () => {
    const res = await axios.post(`${API}/hotels`, { hotel_id: hotelId, rooms });
    notify(res.data.error ?? `Отель ${hotelId} добавлен`);
    setHotelId(""); setRooms(0); fetchAll();
  };

  const refill = async () => {
    const res = await axios.put(`${API}/inventory/${refillHotelId}`, { hotel_id: refillHotelId, rooms: refillRooms });
    notify(res.data.error ?? `Номера пополнены: ${refillHotelId}`);
    setRefillHotelId(""); setRefillRooms(0); fetchAll();
  };

  const cancelReservation = async (orderId: string) => {
    const res = await axios.delete(`${API}/reservations/${orderId}`);
    notify(res.data.error ?? `Бронь ${orderId} отменена`);
    fetchAll();
  };

  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: 700, margin: "40px auto", padding: "0 20px" }}>
      <h1>🏨 Hotel Service</h1>

      {message && (
        <div style={{
          background: messageType === "error" ? "#f8d7da" : "#d4edda",
          color: messageType === "error" ? "#721c24" : "#155724",
          padding: "10px", borderRadius: 6, marginBottom: 16
        }}>
          {message}
        </div>
      )}

      {/* Забронировать номер */}
      <section style={card}>
        <h2>Забронировать номер</h2>
        <input placeholder="ID заказа (напр. ORD-001)" value={orderId} onChange={e => setOrderId(e.target.value)} style={input} />
        <input placeholder="ID отеля (напр. H1)" value={orderHotelId} onChange={e => setOrderHotelId(e.target.value)} style={input} />
        <input placeholder="Сумма" type="number" value={orderAmount} onChange={e => setOrderAmount(+e.target.value)} style={input} />
        <button onClick={createOrder} style={btn}>Забронировать</button>
      </section>

      {/* Инвентарь */}
      <section style={card}>
        <h2>Инвентарь отелей</h2>
        <button onClick={fetchAll} style={btn}>Обновить</button>
        <table style={{ width: "100%", marginTop: 10, borderCollapse: "collapse" }}>
          <thead><tr><th style={th}>Отель</th><th style={th}>Свободных номеров</th></tr></thead>
          <tbody>
            {Object.entries(inventory).map(([id, count]) => (
              <tr key={id}>
                <td style={td}>{id}</td>
                <td style={td}>{count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Добавить отель */}
      <section style={card}>
        <h2>Добавить отель</h2>
        <input placeholder="ID отеля" value={hotelId} onChange={e => setHotelId(e.target.value)} style
