# Laporan UTS: Pub-Sub Log Aggregator

**Nama:** Nabil Ahmed Savero
**NIM:** 11221041

## Ringkasan dan Arsitektur Sistem

Sistem ini adalah sebuah *log aggregator* yang dibangun dengan arsitektur *publish-subscribe*. Komponen utama adalah sebuah *aggregator service* yang berjalan di dalam container Docker, dibangun menggunakan Python dan FastAPI. Service ini mengekspos API untuk menerima *event* (log) dari *publisher* manapun.

Fitur inti dari sistem ini adalah **idempotency** dan **deduplication**. Setiap *event* yang diidentifikasi secara unik oleh kombinasi `(topic, event_id)` dijamin hanya akan diproses dan disimpan satu kali. Untuk mencapai persistensi data dan toleransi terhadap *crash*, sistem menggunakan database **SQLite** yang file-nya disimpan di luar container melalui Docker Volume.

**Diagram Alur Sederhana:**

`Publisher` -> `POST /publish` -> `Aggregator Service (FastAPI)` -> `Deduplication Check (SQLite UNIQUE constraint)` -> `Simpan ke events.db`

## Keputusan Desain

Implementasi sistem ini didasari oleh beberapa keputusan desain kunci untuk memenuhi syarat tugas:

* **Idempotency & Deduplication Store**: Dipilih **SQLite** sebagai *dedup store* karena bersifat *embedded* (local-only), andal, dan mendukung `UNIQUE constraint` secara native. Idempotency dicapai dengan menangkap `sqlite3.IntegrityError` saat ada upaya memasukkan duplikat `(topic, event_id)`.

* **Ordering & Retry**: Sistem dirancang untuk menangani skenario *at-least-once delivery* di mana *retry* dari *publisher* dapat terjadi. Oleh karena itu, *total ordering* tidak menjadi prioritas. Sistem menerima *event* dan mengandalkan `timestamp` yang dibawa oleh *event* itu sendiri untuk pengurutan jika diperlukan nanti.

## Analisis Performa dan Metrik

Untuk menguji performa, sebuah *stress test* dijalankan menggunakan script `stress_test.py`. Skenario pengujian adalah mengirimkan **5.000 event** (dengan 25% duplikasi) secara *batch* ke endpoint `/publish`.

**Hasil:**

* **Waktu Eksekusi**: Seluruh 5.000 event berhasil diproses dalam **108.21 detik**.

* **Responsivitas**: Selama pengujian, server tetap responsif dan tidak mengalami *crash*.

**Analisis Metrik dari `/stats`:**

* **`received`**: Menunjukkan total beban yang diterima sistem.

* **`unique_processed`**: Mengonfirmasi jumlah data unik yang berhasil disimpan setelah proses deduplikasi.

* **`duplicate_dropped`**: Secara kuantitatif membuktikan bahwa mekanisme deduplikasi bekerja di bawah beban tinggi.

Hasil ini membuktikan bahwa arsitektur yang dipilih mampu memenuhi syarat performa minimum dan metrik yang disediakan efektif untuk memantau kesehatan sistem.

## Keterkaitan ke Teori Sistem Terdistribusi

### T1: Karakteristik Sistem Terdistribusi dan Trade-off

Sistem ini menunjukkan karakteristik **konkurensi**, **tidak adanya jam global**, dan **potensi kegagalan parsial**. *Trade-off* utamanya adalah memilih **availability** dan **eventual consistency** di atas *strong consistency*, sesuai dengan tantangan fundamental dalam mendesain sistem terdistribusi.

(Tanenbaum & Van Steen, 2023, Bab 1)

### T2: Arsitektur Client-Server vs. Publish-Subscribe

Arsitektur **publish-subscribe** dipilih karena memberikan *loose coupling*, berbeda dengan model client-server yang lebih kaku. Hal ini membuat sistem lebih **skalabel** dan **fleksibel**, sejalan dengan prinsip arsitektur sistem terdistribusi modern.

(Tanenbaum & Van Steen, 2023, Bab 2)

### T3: At-least-once vs. Exactly-once Delivery

Sistem dirancang sebagai **idempotent consumer** untuk menangani *at-least-once delivery*. Implementasi di `src/aggregator.py` dengan `UNIQUE constraint` adalah contoh praktis dari mekanisme komunikasi pesan yang andal tanpa memerlukan protokol *exactly-once* yang kompleks.

(Tanenbaum & Van Steen, 2023, Bab 3)

### T4: Skema Penamaan Topic dan Event ID

Kombinasi **`topic`** (sebagai *namespace*) dan **`event_id`** (sebagai *identifier* unik) adalah implementasi dari skema penamaan datar (*flat naming*) yang efektif untuk deduplikasi. Ini memastikan setiap entitas memiliki nama yang unik secara global di dalam konteks topiknya.

(Tanenbaum & Van Steen, 2023, Bab 4)

### T5: Ordering dan Waktu

**Total ordering** tidak diimplementasikan karena tidak krusial untuk log aggregator. Sistem mengandalkan *physical clocks* (`timestamp` dari event), yang cukup untuk sebagian besar kasus analisis, tanpa memerlukan kompleksitas *logical clocks*.

(Tanenbaum & Van Steen, 2023, Bab 5)

### T6: Mitigasi Failure Modes

Sistem memitigasi kegagalan melalui:
* **Duplikasi Event**: Diatasi dengan *idempotency* via `UNIQUE constraint`.
* **Crash pada Aggregator**: Diatasi dengan Docker Volume (`-v "%cd%\data":/app/data`) yang merupakan bentuk *fault tolerance* melalui persistensi state.

(Tanenbaum & Van Steen, 2023, Bab 6)

### T7: Eventual Consistency

Sistem ini adalah contoh nyata dari model **eventual consistency**. Ini adalah salah satu model konsistensi data-sentris yang paling umum di mana, jika tidak ada pembaruan baru, semua replika (dalam hal ini, state akhir database) pada akhirnya akan menjadi konsisten.

(Tanenbaum & Van Steen, 2023, Bab 7)

### T8: Metrik Evaluasi Sistem

Endpoint `/stats` menyediakan metrik yang merefleksikan efektivitas keputusan desain dari Bab 1-7, seperti membuktikan kebutuhan akan *fault tolerance* (dari tingginya `duplicate_dropped`) dan skalabilitas sistem.

(Tanenbaum & Van Steen, 2023)

## Sitasi

Tanenbaum, A. S., & Van Steen, M. (2023). *Distributed systems* (4th ed.). Maarten van Steen.