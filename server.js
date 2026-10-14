const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Inisialisasi Database SQLite
const db = new sqlite3.Database('./spip_dikbud_pohuwato.db', (err) => {
    if (err) console.error('Gagal koneksi database:', err.message);
    else console.log('Database SPIP Dikbud Pohuwato terhubung.');
});

// Pembuatan Tabel (Pastikan Query SQL Dibungkus Backtick `...`)
db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS konteks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tahun INTEGER,
        bidang TEXT,
        tujuan TEXT,
        sasaran TEXT,
        kegiatan TEXT
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS risk_register (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        konteks_id INTEGER,
        kode_risiko TEXT UNIQUE,
        uraian_risiko TEXT,
        pemilik_risiko TEXT,
        sebab TEXT,
        sumber_sebab TEXT,
        sifat_sebab TEXT,
        dampak TEXT,
        pihak_terdampak TEXT,
        skala_dampak INTEGER,
        skala_kemungkinan INTEGER,
        skala_risiko INTEGER,
        tingkat_risiko TEXT,
        is_prioritas INTEGER DEFAULT 0,
        FOREIGN KEY (konteks_id) REFERENCES konteks(id)
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS rtp (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        risk_id INTEGER,
        pengendalian_ada TEXT,
        celah_pengendalian TEXT,
        pengendalian_dibutuhkan TEXT,
        penanggung_jawab TEXT,
        target_waktu TEXT,
        FOREIGN KEY (risk_id) REFERENCES risk_register(id)
    )`);
});

// API Endpoint Ambil Data Risiko
app.get('/api/risks', (req, res) => {
    const query = `
        SELECT r.*, k.bidang, k.tujuan, k.sasaran, k.kegiatan, 
               rtp.pengendalian_dibutuhkan, rtp.penanggung_jawab, rtp.target_waktu
        FROM risk_register r
        LEFT JOIN konteks k ON r.konteks_id = k.id
        LEFT JOIN rtp ON r.id = rtp.risk_id
        ORDER BY r.skala_risiko DESC
    `;
    db.all(query, [], (err, rows) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(rows);
    });
});

app.listen(PORT, () => {
    console.log(`Server SPIP Dikbud Pohuwato berjalan di: http://localhost:${PORT}`);
});