javascript
const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Inisialisasi Database SQLite
const db = new sqlite3.Database('./spip_dikbud_pohuwato.db', (err) => {
    if (err) {
        console.error('Gagal koneksi database:', err.message);
    } else {
        console.log('Database SPIP Dikbud Pohuwato terhubung.');
        initAndSeedDatabase();
    }
});

function initAndSeedDatabase() {
    db.serialize(() => {
        db.run(`CREATE TABLE IF NOT EXISTS konteks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tahun INTEGER, bidang TEXT, tujuan TEXT, sasaran TEXT, kegiatan TEXT
        )`);

        db.run(`CREATE TABLE IF NOT EXISTS risk_register (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            konteks_id INTEGER, kode_risiko TEXT UNIQUE, uraian_risiko TEXT, pemilik_risiko TEXT,
            sebab TEXT, sumber_sebab TEXT, sifat_sebab TEXT, dampak TEXT, pihak_terdampak TEXT,
            skala_dampak INTEGER, skala_kemungkinan INTEGER, skala_risiko INTEGER, tingkat_risiko TEXT, is_prioritas INTEGER DEFAULT 0
        )`);

        db.run(`CREATE TABLE IF NOT EXISTS rtp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            risk_id INTEGER, pengendalian_ada TEXT, celah_pengendalian TEXT,
            pengendalian_dibutuhkan TEXT, penanggung_jawab TEXT, target_waktu TEXT
        )`);

        db.run(`CREATE TABLE IF NOT EXISTS form8_komunikasi (
            id INTEGER PRIMARY KEY AUTOINCREMENT, kegiatan_pengendalian TEXT, media_komunikasi TEXT,
            penyedia_informasi TEXT, penerima_informasi TEXT, rencana_waktu TEXT, realisasi_waktu TEXT
        )`);

        db.run(`CREATE TABLE IF NOT EXISTS form9_pemantauan (
            id INTEGER PRIMARY KEY AUTOINCREMENT, kegiatan_dipantau TEXT, metode_pemantauan TEXT,
            penanggung_jawab TEXT, waktu_rencana TEXT, waktu_realisasi TEXT, keterangan_capaian TEXT
        )`);

        db.get("SELECT COUNT(*) AS count FROM risk_register", [], (err, row) => {
            if (row && row.count === 0) {
                console.log("Injeksi data Risk Register DIKBUD 2026...");
                seedData();
            }
        });
    });
}

function seedData() {
    const risks = [
        { kode: 'RSK-DPA-DIKDAS-002', kegiatan: 'Pengelolaan Dana BOSP SD', uraian: 'BOS SD: Belanja modal Rp 5,19 M & salur BOSP lambat', pemilik: 'Kabid Pembinaan Dikdas', sebab: 'Pengesahan RKAS ARKAS lambat, SPJ menumpuk', dampak: 'Operasional 129 SD terganggu, pemblokiran rekening', d: 5, k: 4, skor: 20, tingkat: 'SANGAT TINGGI', prio: 1, peng_ada: 'Monitoring ARKAS berkala', celah: 'Belum ada klinik asistensi meja', rtp: 'Klinik Asistensi ARKAS BOSP & cut-off H-14 batas salur', pj: 'Kabid Dikdas & Tim BOS', tw: 'Feb - Okt 2026' },
        { kode: 'RSK-DPA-DIKDAS-003', kegiatan: 'Pengelolaan Dana BOSP SMP', uraian: 'BOS SMP: Belanja modal Rp 1,77 M & pajak SPJ', pemilik: 'Kabid Pembinaan Dikdas', sebab: 'Kapasitas operator ARKAS rendah, aset lambat rekon', dampak: 'Pengadaan sarana terhambat, temuan BPK', d: 4, k: 4, skor: 16, tingkat: 'TINGGI', prio: 1, peng_ada: 'Verifikasi berkas manual', celah: 'Verifikasi SIPLah & aset lambat', rtp: 'Pendampingan e-purchasing SIPLah & rekon aset triwulanan', pj: 'PPTK SMP & Pengurus Barang', tw: 'Mar - Nov 2026' },
        { kode: 'RSK-DPA-PAUD-004', kegiatan: 'Penyaluran BOP PAUD', uraian: 'BOP PAUD: Salur terhambat kendala rekening lembaga', pemilik: 'Kabid PAUD & Dikmas', sebab: 'Administrasi paruh waktu, Dapodik lambat', dampak: 'KBM PAUD mandek, honor pendidik tertunda', d: 4, k: 4, skor: 16, tingkat: 'TINGGI', prio: 1, peng_ada: 'Surat edaran batas waktu', celah: 'Surat edaran sering diabaikan', rtp: 'Pemberdayaan PKG sebagai simpul verifikasi berjenjang', pj: 'Kabid PAUD & Kasi Lembaga', tw: 'Apr - Okt 2026' },
        { kode: 'RSK-DPA-GTK-014', kegiatan: 'Pemetaan & Pemerataan Guru', uraian: 'Pemetaan Guru: Data ABK tidak akurat & penolakan mutasi', pemilik: 'Kabid Ketenagaan (GTK)', sebab: 'Sinkronisasi Dapodik lambat, resistensi guru', dampak: 'Disparitas guru daerah terpencil tetap tinggi', d: 4, k: 4, skor: 16, tingkat: 'TINGGI', prio: 1, peng_ada: 'Pengecekan di Dapodik', celah: 'Dapodik belum link peta zonasi', rtp: 'Rekonsiliasi data guru berbasis spasial & Perbup Zonasi', pj: 'Kabid Ketenagaan (GTK)', tw: 'Mei - Okt 2026' },
        { kode: 'RSK-DPA-ZERO-021', kegiatan: 'Penyusunan Dokumen SAKIP', uraian: 'SAKIP & Renja: Pagu Rp 0 penyusunan LAKIP terhambat', pemilik: 'Sekretaris Dinas', sebab: 'Fiskal APBD dialihkan ke belanja wajib gaji', dampak: 'LAKIP & Renja terhambat, nilai RB turun', d: 4, k: 4, skor: 16, tingkat: 'TINGGI', prio: 1, peng_ada: 'Rapat LAKIP tahunan ad-hoc', celah: 'Tidak ada anggaran operasional', rtp: 'Pemanfaatan sistem digital e-SAKIP mandiri perangkat daerah', pj: 'Sekretaris & Kasubag Ren', tw: 'Triwulan I - IV' },
        { kode: 'RSK-DPA-ZERO-022', kegiatan: 'Registrasi Cagar Budaya', uraian: 'Cagar Budaya: Pagu Rp 0 pendaftaran ODCB stagnan', pemilik: 'Kabid Kebudayaan', sebab: 'Pagu kebudayaan terserap penuh festival budaya', dampak: 'Target penetapan cagar budaya stagnan 0', d: 4, k: 4, skor: 16, tingkat: 'TINGGI', prio: 1, peng_ada: 'Pendaftaran mandiri warga', celah: 'Nihil biaya sidang tim ahli TACB', rtp: 'Kemitraan swakelola riset cagar budaya bersama Balai BPK', pj: 'Kabid Kebudayaan', tw: 'Feb - Nov 2026' },
        { kode: 'RSK-DPA-SEKR-001', kegiatan: 'Pembayaran Gaji ASN', uraian: 'Gaji ASN: Keterlambatan/kesalahan pembayaran gaji ASN/PPPK', pemilik: 'Sekretaris Dinas', sebab: 'Data SIMGAJI/BPKAD terlambat dimutakhirkan', dampak: 'Keresahan ribuan guru/pegawai, demotivasi', d: 5, k: 3, skor: 15, tingkat: 'TINGGI', prio: 1, peng_ada: 'Rekonsiliasi bulanan BPKAD', celah: 'Rekon sering mepet tanggal 1', rtp: 'Jadwal cut-off mutasi tanggal 20 tiap bulan & slip digital', pj: 'Kasubag Keu & Bendahara', tw: 'Rutin Bulanan' },
        { kode: 'RSK-DPA-SEKR-020', kegiatan: 'Pemeliharaan Kantor', uraian: 'Gedung Kantor: Atap bocor merusak arsip SPJ & IT', pemilik: 'Kasubag Umum & Perlengkapan', sebab: 'Pagu pemeliharaan sangat minim (Rp 9,47 Juta)', dampak: 'Kerusakan berkas arsip SPJ & perangkat server', d: 4, k: 3, skor: 12, tingkat: 'TINGGI', prio: 1, peng_ada: 'Pemeliharaan rutin kantor', celah: 'Pagu anggaran sangat terbatas', rtp: 'Perbaikan darurat & digitalisasi arsip SPJ ke cloud storage', pj: 'Kasubag Umum & Perlengkapan', tw: 'Triwulan I 2026' }
    ];

    risks.forEach(r => {
        db.run("INSERT INTO konteks (tahun, bidang, kegiatan) VALUES (2026, ?, ?)", [r.pemilik, r.kegiatan], function(err) {
            const kId = this.lastID;
            db.run(`INSERT INTO risk_register 
                (konteks_id, kode_risiko, uraian_risiko, pemilik_risiko, sebab, sumber_sebab, sifat_sebab, dampak, skala_dampak, skala_kemungkinan, skala_risiko, tingkat_risiko, is_prioritas) 
                VALUES (?, ?, ?, ?, ?, 'Internal', 'C', ?, ?, ?, ?, ?, ?)`,
                [kId, r.kode, r.uraian, r.pemilik, r.sebab, r.dampak, r.d, r.k, r.skor, r.tingkat, r.prio], function(err) {
                    const rId = this.lastID;
                    db.run(`INSERT INTO rtp (risk_id, pengendalian_ada, celah_pengendalian, pengendalian_dibutuhkan, penanggung_jawab, target_waktu) 
                        VALUES (?, ?, ?, ?, ?, ?)`, [rId, r.peng_ada, r.celah, r.rtp, r.pj, r.tw]);
                });
        });
    });

    db.run(`INSERT INTO form8_komunikasi (kegiatan_pengendalian, media_komunikasi, penyedia_informasi, penerima_informasi, rencana_waktu, realisasi_waktu) VALUES 
        ('Jadwal cut-off rekonsiliasi data gaji tanggal 20', 'Nota Dinas & Rekonsiliasi Tatap Muka', 'Kasubag Keuangan', 'BPKAD & Korwil Pendidikan', 'Jan - Des 2026', 'Rutin Tiap Bulan'),
        ('Klinik Asistensi ARKAS BOSP', 'Desk Asistensi & WA Group Korwil', 'Tim BOSP Dikbud', 'Kepala Sekolah & Bendahara SD', 'Feb - Okt 2026', 'Terlaksana Triwulan I')`);

    db.run(`INSERT INTO form9_pemantauan (kegiatan_dipantau, metode_pemantauan, penanggung_jawab, waktu_rencana, waktu_realisasi, keterangan_capaian) VALUES 
        ('Rekonsiliasi mutasi pegawai dan SIMGAJI BPKAD', 'Laporan Rekonsiliasi Gaji Bulanan', 'Sekretaris Dinas', 'Tiap Bulan (Tgl 25)', 'Jan - Des 2026', 'Nihil keluhan pembayaran'),
        ('Penyaluran dan LPJ Dana BOSP SD/SMP', 'Monitoring dan Evaluasi Lapangan', 'Kabid Dikdas & Tim BOS', 'Triwulanan', 'Mar, Jun, Sep, Des 2026', 'Capaian salur 100%')`);
}

// Endpoint /api/risks
app.get('/api/risks', (req, res) => {
    const query = `
        SELECT r.*, k.bidang, k.tujuan, k.sasaran, k.kegiatan, 
               rtp.pengendalian_ada, rtp.celah_pengendalian,
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

app.get('/api/form8', (req, res) => {
    db.all("SELECT * FROM form8_komunikasi", [], (err, rows) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(rows);
    });
});

app.get('/api/form9', (req, res) => {
    db.all("SELECT * FROM form9_pemantauan", [], (err, rows) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(rows);
    });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server SPIP Dikbud Pohuwato berjalan di port: ${PORT}`);
});