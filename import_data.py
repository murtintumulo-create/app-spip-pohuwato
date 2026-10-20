import sqlite3
import pandas as pd
import os
import glob

def find_sheet_name(xls_sheets, keyword):
    """Mencari nama sheet berdasarkan kata kunci secara fleksibel"""
    for sheet in xls_sheets:
        if keyword.lower() in sheet.lower().replace(" ", "").replace(".", ""):
            return sheet
        # Pencarian alternatif dengan spasi/titik
        if keyword.lower() in sheet.lower():
            return sheet
    return None

def main():
    conn = sqlite3.connect('spip_dikbud_pohuwato.db')
    cursor = conn.cursor()

    # Cari file .xlsx di folder saat ini
    excel_files = glob.glob('Risk Register*.xlsx')
    if not excel_files:
        excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and not f.startswith('~$')]

    if not excel_files:
        print("❌ Error: Tidak ditemukan file Excel .xlsx di folder D:\\app-spip-pohuwato!")
        return

    # Ambil file excel yang paling baru dimodifikasi
    excel_path = sorted(excel_files, key=os.path.getmtime, reverse=True)[0]
    print(f"📖 Mengakses berkas Excel: {excel_path}")

    xls = pd.ExcelFile(excel_path)
    sheets = xls.sheet_names
    print(f"📋 Sheet yang ditemukan di berkas Excel: {sheets}")

    # Identifikasi Nama Sheet Secara Otomatis
    sheet_3c = find_sheet_name(sheets, "3c") or find_sheet_name(sheets, "operasional") or sheets[0]
    sheet_4  = find_sheet_name(sheets, "form4") or find_sheet_name(sheets, "analisis") or sheets[1]
    sheet_7  = find_sheet_name(sheets, "form7") or find_sheet_name(sheets, "rtp") or sheets[2]
    sheet_8  = find_sheet_name(sheets, "form8") or find_sheet_name(sheets, "komunikasi")
    sheet_9  = find_sheet_name(sheets, "form9") or find_sheet_name(sheets, "pemantauan")

    print(f"🎯 Menggunakan Sheet 3.c: '{sheet_3c}'")
    print(f"🎯 Menggunakan Sheet 4  : '{sheet_4}'")
    print(f"🎯 Menggunakan Sheet 7  : '{sheet_7}'")

    # Read Data Sheet
    df_3c = pd.read_excel(excel_path, sheet_name=sheet_3c, skiprows=1)
    df_4  = pd.read_excel(excel_path, sheet_name=sheet_4, skiprows=1)
    df_7  = pd.read_excel(excel_path, sheet_name=sheet_7, skiprows=1)
    
    df_8  = pd.read_excel(excel_path, sheet_name=sheet_8, skiprows=1) if sheet_8 else pd.DataFrame()
    df_9  = pd.read_excel(excel_path, sheet_name=sheet_9, skiprows=1) if sheet_9 else pd.DataFrame()

    # Reset & Re-create SQLite Database Tables
    cursor.execute('DROP TABLE IF EXISTS form8_komunikasi')
    cursor.execute('DROP TABLE IF EXISTS form9_pemantauan')
    cursor.execute('DROP TABLE IF EXISTS rtp')
    cursor.execute('DROP TABLE IF EXISTS risk_register')
    cursor.execute('DROP TABLE IF EXISTS konteks')

    cursor.execute('''CREATE TABLE konteks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tahun INTEGER, bidang TEXT, tujuan TEXT, sasaran TEXT, kegiatan TEXT
    )''')
    
    cursor.execute('''CREATE TABLE risk_register (
        id INTEGER PRIMARY KEY AUTOINCREMENT, konteks_id INTEGER, kode_risiko TEXT UNIQUE, 
        uraian_risiko TEXT, pemilik_risiko TEXT, sebab TEXT, sumber_sebab TEXT, 
        sifat_sebab TEXT, dampak TEXT, pihak_terdampak TEXT, skala_dampak INTEGER, 
        skala_kemungkinan INTEGER, skala_risiko INTEGER, tingkat_risiko TEXT, is_prioritas INTEGER DEFAULT 0
    )''')
    
    cursor.execute('''CREATE TABLE rtp (
        id INTEGER PRIMARY KEY AUTOINCREMENT, risk_id INTEGER, pengendalian_ada TEXT, 
        celah_pengendalian TEXT, pengendalian_dibutuhkan TEXT, penanggung_jawab TEXT, target_waktu TEXT,
        FOREIGN KEY (risk_id) REFERENCES risk_register(id)
    )''')

    cursor.execute('''CREATE TABLE form8_komunikasi (
        id INTEGER PRIMARY KEY AUTOINCREMENT, kegiatan_pengendalian TEXT, media_komunikasi TEXT, 
        penyedia_informasi TEXT, penerima_informasi TEXT, rencana_waktu TEXT, realisasi_waktu TEXT
    )''')

    cursor.execute('''CREATE TABLE form9_pemantauan (
        id INTEGER PRIMARY KEY AUTOINCREMENT, kegiatan_dipantau TEXT, metode_pemantauan TEXT, 
        penanggung_jawab TEXT, waktu_rencana TEXT, waktu_realisasi TEXT, keterangan_capaian TEXT
    )''')

    # Import Form 3.c, 4, 7 (Data Risiko & Pengendalian)
    for idx, row in df_3c.iterrows():
        if len(row) < 3: continue
        kode = str(row.iloc[2]).strip()
        if not kode or kode == 'nan' or 'RSK' not in kode:
            continue
        
        subkeg = str(row.iloc[1])
        uraian = str(row.iloc[3])
        sebab  = str(row.iloc[4]) if len(row) > 4 else '-'
        sumber = str(row.iloc[5]) if len(row) > 5 else 'Internal'
        sifat  = str(row.iloc[6]) if len(row) > 6 else 'C'
        dampak = str(row.iloc[7]) if len(row) > 7 else '-'
        pemilik= str(row.iloc[8]) if len(row) > 8 else 'Dinas Pendidikan'

        cursor.execute('INSERT INTO konteks (tahun, bidang, kegiatan) VALUES (2026, ?, ?)', (pemilik, subkeg))
        konteks_id = cursor.lastrowid

        f4_match = df_4[df_4.iloc[:, 2].astype(str).str.contains(kode, na=False)]
        skala_d = int(f4_match.iloc[0, 3]) if not f4_match.empty and str(f4_match.iloc[0, 3]).isdigit() else 3
        skala_k = int(f4_match.iloc[0, 4]) if not f4_match.empty and str(f4_match.iloc[0, 4]).isdigit() else 3
        skor    = int(f4_match.iloc[0, 5]) if not f4_match.empty and str(f4_match.iloc[0, 5]).isdigit() else skala_d * skala_k
        tingkat = str(f4_match.iloc[0, 6]).upper() if not f4_match.empty else 'SEDANG'
        is_prio = 1 if skor >= 12 else 0

        cursor.execute('''INSERT INTO risk_register 
            (konteks_id, kode_risiko, uraian_risiko, pemilik_risiko, sebab, sumber_sebab, sifat_sebab, dampak, skala_dampak, skala_kemungkinan, skala_risiko, tingkat_risiko, is_prioritas) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (konteks_id, kode, uraian, pemilik, sebab, sumber, sifat, dampak, skala_d, skala_k, skor, tingkat, is_prio))
        risk_id = cursor.lastrowid

        f7_match = df_7[df_7.iloc[:, 2].astype(str).str.contains(kode, na=False)]
        peng_ada = str(f7_match.iloc[0, 3]) if not f7_match.empty else '-'
        celah    = str(f7_match.iloc[0, 4]) if not f7_match.empty else '-'
        rtp_val  = str(f7_match.iloc[0, 5]) if not f7_match.empty else '-'
        pj_val   = str(f7_match.iloc[0, 6]) if not f7_match.empty else pemilik
        tw_val   = str(f7_match.iloc[0, 7]) if not f7_match.empty else '2026'

        cursor.execute('INSERT INTO rtp (risk_id, pengendalian_ada, celah_pengendalian, pengendalian_dibutuhkan, penanggung_jawab, target_waktu) VALUES (?, ?, ?, ?, ?, ?)',
                       (risk_id, peng_ada, celah, rtp_val, pj_val, tw_val))

    # Import Form 8 (Pengkomunikasian) Jika Ada
    if not df_8.empty:
        for idx, row in df_8.dropna(subset=[df_8.columns[1]]).iterrows():
            if idx == 0 or 'Kegiatan' in str(row.iloc[1]): continue
            cursor.execute('INSERT INTO form8_komunikasi (kegiatan_pengendalian, media_komunikasi, penyedia_informasi, penerima_informasi, rencana_waktu, realisasi_waktu) VALUES (?, ?, ?, ?, ?, ?)',
                           (str(row.iloc[1]), str(row.iloc[2]), str(row.iloc[3]), str(row.iloc[4]), str(row.iloc[5]), str(row.iloc[6])))

    # Import Form 9 (Pemantauan Intern) Jika Ada
    if not df_9.empty:
        for idx, row in df_9.dropna(subset=[df_9.columns[1]]).iterrows():
            if idx == 0 or 'Kegiatan' in str(row.iloc[1]): continue
            cursor.execute('INSERT INTO form9_pemantauan (kegiatan_dipantau, metode_pemantauan, penanggung_jawab, waktu_rencana, waktu_realisasi, keterangan_capaian) VALUES (?, ?, ?, ?, ?, ?)',
                           (str(row.iloc[1]), str(row.iloc[2]), str(row.iloc[3]), str(row.iloc[4]), str(row.iloc[5]), str(row.iloc[6])))

    conn.commit()
    conn.close()
    print("✅ BERHASIL! Seluruh data dari berkas Excel baru berhasil diimpor ke Database SQLite tanpa error.")

if __name__ == '__main__':
    main()