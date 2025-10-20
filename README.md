# UTS SISTER: Pub-Sub Log Aggregator

Proyek ini adalah implementasi dari sebuah layanan log aggregator sederhana dengan arsitektur Publish-Subscribe. Layanan ini dirancang untuk menerima event (log), melakukan deduplikasi agar setiap event hanya diproses sekali, dan menyimpannya secara persisten.

Tujuan utama sistem ini adalah menjadi *idempotent consumer*, yang artinya meskipun sebuah event dikirim berkali-kali, efeknya akan sama seperti hanya dikirim sekali.

## Teknologi yang Digunakan

* **Bahasa**: Python 3.11
* **Framework API**: FastAPI
* **Database**: SQLite
* **Containerization**: Docker

## Cara Menjalankan Aplikasi

Pastikan Anda sudah menginstall Docker di komputer Anda.

### 1. Build Docker Image

Buka terminal (disarankan **Command Prompt/CMD** di Windows) di folder utama proyek, lalu jalankan perintah ini untuk membuat "cetakan" aplikasi:

```bash
docker build -t uts-aggregator .
```

### 2. Jalankan Docker Container

Setelah image selesai dibuat, jalankan container dengan perintah berikut. Perintah `-v` di bawah ini sangat penting untuk memastikan data database Anda tidak hilang saat container berhenti.

```bash
docker run --name my-aggregator -p 8080:8080 -v "%cd%\data":/app/data uts-aggregator
```

Aplikasi sekarang berjalan dan bisa diakses di [http://localhost:8080](http://localhost:8080).

## Asumsi

**Lingkungan**: Sistem dirancang untuk berjalan secara lokal di dalam Docker. Tidak ada dependensi ke layanan eksternal.

**Format Event**: Diasumsikan bahwa publisher mengirimkan event sesuai dengan skema JSON yang telah ditentukan. Validasi skema ditangani oleh Pydantic di sisi server.

**Persistensi**: Untuk menjamin persistensi data, diasumsikan container dijalankan dengan Docker Volume (`-v`) yang memetakan direktori data di host.

## Daftar Endpoint API

### 1. Publish Events

- **URL**: `/publish`
- **Method**: `POST`
- **Body**: Sebuah array JSON berisi satu atau lebih objek Event.

Contoh Body:

```json
[
  {
    "topic": "user-activity",
    "event_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "timestamp": "2025-10-26T10:00:00Z",
    "source": "webapp-frontend",
    "payload": {
      "user_id": 123,
      "action": "login"
    }
  }
]
```

### 2. Get Processed Events

- **URL**: `/events`
- **Method**: `GET`
- **Query Parameter**: `topic` (wajib)

Contoh Penggunaan: [http://localhost:8080/events?topic=user-activity](http://localhost:8080/events?topic=user-activity)

### 3. Get System Stats

- **URL**: `/stats`
- **Method**: `GET`

Contoh Response:

```json
{
  "received": 10,
  "unique_processed": 8,
  "duplicate_dropped": 2,
  "topics": [
    "user-activity",
    "payment"
  ],
  "uptime_seconds": 125
}
```

## Menjalankan Unit Tests

Untuk menjalankan tes secara lokal (di luar Docker), pastikan Anda sudah menginstall semua dependensi.

```bash
# Install semua dependensi
pip install -r requirements.txt

# Jalankan tes
python -m pytest
```

## Link Video Demo YouTube

https://youtu.be/cjs0RRmdrms?si=r56Rw4cfE8UrvhM3

