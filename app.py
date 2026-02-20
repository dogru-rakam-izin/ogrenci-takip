import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# 1. Veritabanı Fonksiyonları
def db_baglan():
    conn = sqlite3.connect('rehab_merkezi.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kayitlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, yas_sinif TEXT, 
                  degerlendirme TEXT, karar TEXT, sonuc TEXT, veli_adi TEXT, 
                  tel TEXT, adres TEXT, tarih DATE)''')
    conn.commit()
    return conn

# Sayfa Ayarları
st.set_page_config(page_title="Rehabilitasyon Profesyonel Takip", layout="wide")

# Renk Fonksiyonu
def renk_ata(val):
    color = 'white'
    if val == 'Hastane Sürecinde': color = '#FFA500' # Turuncu
    elif val == 'RAM Sürecinde': color = '#1E90FF' # Mavi
    elif val == 'İptal': color = '#FF4B4B' # Kırmızı
    elif val == 'Kaydedildi': color = '#28A745' # Yeşil
    return f'background-color: {color}; color: white; font-weight: bold'

st.title("🏥 Rehabilitasyon Merkezi | Profesyonel Yönetim Paneli")
st.markdown("---")

# Sekmeli Yapı (Kayıt, Güncelleme ve Listeleme için)
sekme1, sekme2 = st.tabs(["➕ Yeni Kayıt & Güncelleme", "📋 Liste & Raporlama"])

# --- SEKME 1: KAYIT VE GÜNCELLEME ---
with sekme1:
    col_yeni, col_guncelle = st.columns(2)
    
    with col_yeni:
        st.subheader("Yeni Öğrenci Ekle")
        with st.form("yeni_kayit", clear_on_submit=True):
            ad = st.text_input("Ad Soyad")
            yas = st.text_input("Yaş - Sınıf")
            veli = st.text_input("Veli Adı")
            tel = st.text_input("Telefon")
            deger = st.text_area("Değerlendirme")
            karar = st.selectbox("Karar", ["Gelişim Takibi", "Rapor Yenileme", "Mezun", "Beklemede"])
            sonuc = st.selectbox("Sonuç Durumu", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "İptal"])
            adres = st.text_area("Adres")
            tarih = st.date_input("Kayıt Tarihi", datetime.now())
            
            submit = st.form_submit_button("Sisteme Kaydet")
            if submit and ad:
                conn = db_baglan()
                cur = conn.cursor()
                cur.execute("INSERT INTO kayitlar (ad_soyad, yas_sinif, degerlendirme, karar, sonuc, veli_adi, tel, adres, tarih) VALUES (?,?,?,?,?,?,?,?,?)",
                            (ad, yas, deger, karar, sonuc, veli, tel, adres, tarih))
                conn.commit()
                conn.close()
                st.success(f"✅ {ad} kaydedildi!")
                st.rerun()

    with col_guncelle:
        st.subheader("🔄 Durum Güncelle (Hastane -> Kaydedildi vb.)")
        st.info("Değiştirmek istediğiniz kaydın ID numarasını sağdaki listeden bakıp buraya yazın.")
        guncel_id = st.number_input("Güncellenecek ID", min_value=1, step=1)
        yeni_durum = st.selectbox("Yeni Sonuç Durumu Seçin", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "İptal"], key="update_status")
        
        if st.button("Durumu Güncelle"):
            conn = db_baglan()
            cur = conn.cursor()
            cur.execute("UPDATE kayitlar SET sonuc = ? WHERE id = ?", (yeni_durum, guncel_id))
            conn.commit()
            conn.close()
            st.success(f"ID {guncel_id} başarıyla '{yeni_durum}' olarak güncellendi!")
            st.rerun()

# --- SEKME 2: LİSTE VE EXCEL ---
with sekme2:
    st.subheader("Veri Filtreleme ve Excel Aktarımı")
    
    f1, f2, f3 = st.columns(3)
    with f1: ay_sec = st.selectbox("Ay", ["Hepsi"] + [str(i).zfill(2) for i in range(1, 13)])
    with f2: yil_sec = st.selectbox("Yıl", ["Hepsi"] + [str(i) for i in range(2024, 2030)])
    with f3: isim_ara = st.text_input("🔍 İsimle Ara")

    conn = db_baglan()
    df = pd.read_sql_query("SELECT * FROM kayitlar", conn)
    conn.close()

    if not df.empty:
        df['tarih'] = pd.to_datetime(df['tarih'])
        if ay_sec != "Hepsi": df = df[df['tarih'].dt.strftime('%m') == ay_sec]
        if yil_sec != "Hepsi": df = df[df['tarih'].dt.strftime('%Y') == yil_sec]
        if isim_ara: df = df[df['ad_soyad'].str.contains(isim_ara, case=False, na=False)]

        # --- EXCEL İNDİRME BUTONU ---
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Ogrenci_Takip')
            writer.close()
        
        st.download_button(
            label="📥 Listeyi Excel Olarak İndir",
            data=buffer,
            file_name=f"Rehab_Liste_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.ms-excel"
        )

        # Tabloyu Renkli Göster
        styled_df = df.style.applymap(renk_ata, subset=['sonuc'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # SİLME BÖLÜMÜ
        with st.expander("🗑️ Kayıt Sil"):
            sil_id = st.number_input("Silinecek ID seçin", min_value=1, step=1, key="delete_id")
            if st.button("Kayıt Sil"):
                conn = db_baglan()
                cur = conn.cursor()
                cur.execute(f"DELETE FROM kayitlar WHERE id={sil_id}")
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.warning("Görüntülenecek veri bulunamadı.")
