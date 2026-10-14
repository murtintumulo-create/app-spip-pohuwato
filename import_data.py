import sqlite3
import pandas as pd

def main():
    # 1. Hubungkan ke Database SQLite
    conn = sqlite3.connect('spip_dikbud_pohuwato.db')
    cursor = conn.cursor()

    excel_path = 'Risk Register DIKBUD 2026.xlsx'

    # 2. Baca Sheet Excel
    df_3c = pd.read_excel(excel_path, sheet_name='Form 3.c Id. Operasional')
    df_4 = pd.read_excel(excel_path, sheet_name='Form 4 Analisis Risiko')
    df_7 = pd.read_excel(excel_path, sheet_name='Form 7 Pengendalian & RTP')

    # 3. Bersihkan Data
    df_3c_clean = df_3c.iloc[2:24, [0, 1, 2, 3, 4, 5, 6, 7, 8]].copy()
    df_3c_clean.columns = ['No', 'SubKegiatan', 'KodeRisiko', 'PernyataanRisiko', 'AkarPenyebab', 'Sumber', 'C_UC', 'Dampak', 'PemilikRisiko']

    df_4_clean = df_4.iloc[2:24, [2, 3, 4, 5, 6]].copy()
    df_4_clean.columns = ['KodeRisiko', 'SkalaDampak', 'SkalaKemungkinan', 'SkorRisiko', 'Kategori']

    df_7_clean = df_7.iloc[2:9, [2, 3, 4, 5, 6, 7]].copy()
    df_7_clean.columns = ['KodeRisiko', 'PengendalianAda', 'CelahPengendalian', 'RTP', 'PJ', 'TargetWaktu']

    # Merge Data
    merged = pd.merge(df_3c_clean, df_4_clean, on='KodeRisiko', how='left')
    merged = pd.merge(merged, df_7_clean, on='KodeRisiko', how='left')

    # 4. Re-create Tabel SQLite
    cursor.execute('DROP TABLE IF EXISTS rtp')
    cursor.execute('DROP TABLE IF EXISTS risk_register')
    cursor.execute('DROP TABLE IF EXISTS konteks')

    cursor.execute('CREATE TABLE konteks (id INTEGER PRIMARY KEY AUTOINCREMENT, tahun INTEGER, bidang TEXT, tujuan TEXT, sasaran TEXT, kegiatan TEXT)')
    
    cursor.execute('CREATE TABLE risk_register (id INTEGER PRIMARY KEY AUTOINCREMENT, konteks_id INTEGER, kode_risiko TEXT UNIQUE, uraian_risiko TEXT, pemilik_risiko TEXT, sebab TEXT, sumber_sebab TEXT, sifat_sebab TEXT, dampak TEXT, pihak_terdampak TEXT, skala_dampak INTEGER, skala_kemungkinan INTEGER, skala_risiko INTEGER, tingkat_risiko TEXT, is_prioritas INTEGER DEFAULT 0)')
    
    cursor.execute('CREATE TABLE rtp (id INTEGER PRIMARY KEY AUTOINCREMENT, risk_id INTEGER, pengendalian_ada TEXT, celah_pengendalian TEXT, pengendalian_dibutuhkan TEXT, penanggung_jawab TEXT, target_waktu TEXT)')

    # 5. Insert Data
    count = 0
    for idx, row in merged.iterrows():
        pemilik = str(row['PemilikRisiko'])
        subkeg = str(row['SubKegiatan'])
        tujuan_text = 'Meningkatnya mutu dan akses pendidikan serta kebudayaan'
        
        cursor.execute('INSERT INTO konteks (tahun, bidang, tujuan, sasaran, kegiatan) VALUES (2026, ?, ?, ?, ?)', (pemilik, tujuan_text, tujuan_text, subkeg))
        konteks_id = cursor.lastrowid

        skor = int(row['SkorRisiko'])
        tingkat = str(row['Kategori']).upper()
        is_prio = 1 if tingkat in ['SANGAT TINGGI', 'TINGGI', 'EKSTRIM'] else 0

        cursor.execute('INSERT INTO risk_register (konteks_id, kode_risiko, uraian_risiko, pemilik_risiko, sebab, sumber_sebab, sifat_sebab, dampak, pihak_terdampak, skala_dampak, skala_kemungkinan, skala_risiko, tingkat_risiko, is_prioritas) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                       (konteks_id, str(row['KodeRisiko']), str(row['PernyataanRisiko']), pemilik, str(row['AkarPenyebab']), str(row['Sumber']), str(row['C_UC']), str(row['Dampak']), 'Sekolah / Masyarakat', int(row['SkalaDampak']), int(row['SkalaKemungkinan']), skor, tingkat, is_prio))
        risk_id = cursor.lastrowid

        rtp_val = str(row['RTP']) if pd.notna(row['RTP']) else 'Pemantauan dan supervisi rutin pelaksanaan kegiatan'
        pj_val = str(row['PJ']) if pd.notna(row['PJ']) else pemilik
        tw_val = str(row['TargetWaktu']) if pd.notna(row['TargetWaktu']) else 'Triwulan I - IV 2026'
        peng_ada = str(row['PengendalianAda']) if pd.notna(row['PengendalianAda']) else '-'
        celah = str(row['CelahPengendalian']) if pd.notna(row['CelahPengendalian']) else '-'

        cursor.execute('INSERT INTO rtp (risk_id, pengendalian_ada, celah_pengendalian, pengendalian_dibutuhkan, penanggung_jawab, target_waktu) VALUES (?, ?, ?, ?, ?, ?)',
                       (risk_id, peng_ada, celah, rtp_val, pj_val, tw_val))
        count += 1

    conn.commit()
    conn.close()
    print("Berhasil mengimpor " + str(count) + " data risiko ke database SQLite!")

if __name__ == '__main__':
    main()