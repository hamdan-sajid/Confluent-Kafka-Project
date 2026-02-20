# Real-Time Data Analytics Pipeline: Kafka + Flask + React

A high-performance streaming application that polls CSV data in real-time, processes it via **Confluent Kafka**, and visualizes aggregated metrics on a modern **React** dashboard.

---

## 🚀 Project Overview

This project demonstrates a complete real-time data lifecycle, bridging the gap between static data sources and dynamic visualization:

* **Producer:** A Python script monitors and polls CSV data, streaming records into a Kafka topic as they are detected.
* **Streaming Platform:** **Confluent Kafka** handles the message brokering, ensuring fault-tolerant, high-throughput, and scalable data delivery.
* **Consumer & Backend:** A **Flask** application acts as a Kafka consumer, fetching data streams and performing on-the-fly aggregations (e.g., averages, counts, or windowed sums).
* **Frontend:** A responsive **React** dashboard that updates in real-time as new data flows through the pipeline via WebSockets.

---

## 🏗️ Architecture

The pipeline is built using a modern full-stack data engineering architecture:

* **Data Source:** CSV files (simulating real-time sensor data or transaction logs).
* **Message Broker:** Confluent Kafka (Cloud or Local instance).
* **Backend:** Flask (Python) utilizing the `confluent-kafka-python` library.
* **Frontend:** React (JavaScript/TypeScript) for a component-based, high-performance UI.
* **Communication:** WebSockets (Socket.io) for pushing real-time updates from Flask to React.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Streaming** | Confluent Kafka |
| **Backend** | Python, Flask |
| **Frontend** | React.js |
| **Real-time** | Socket.io |
| **Data Handling** | Pandas |
