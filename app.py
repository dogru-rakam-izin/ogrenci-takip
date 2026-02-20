import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Veritabanı bağlantısı
def veritabani_hazirla():
    conn = sqlite3.connect('rehabilitasyon.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ogrenciler 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, yas_sinif TEXT, 
                  degerlendirme TEXT, karar TEXT, sonuc TEXT, veli_adi TEXT, 
                  telefon TEXT, adres TEXT, tarih TEXT)''')
    conn.commit()
    return conn

st.set_page_config(page_title="Rehab Takip", layout="wide")

# Görseldeki başlıklarla Form oluşturma
st.title("🏥 Rehabilitasyon Merkezi Takip Sistemi")
st.markdown("---")

with st.form("kayit_formu"):
    col1, col2 = st.columns(2)
    
    with col1:
        ad = st.text_input("Ad Soyad")
        yas = st.text_input("Yaş - Sınıf")
        veli = st.text_input("Veli Adı")
        tel = st.text_input("Telefon")
        
    with col2:
        degerlendirme = st.text_area("Değerlendirme")
        karar = st.selectbox("Karar", ["Gelişim Takibi", "Rapor Bekleniyor", "Mezun", "Destek Eğitimi"])
        sonuc = st.text_input("Sonuç")
        adres = st.text_area("Adres")

    submit = st.form_submit_button("Sisteme Kaydet")

if submit:
    conn = veritabani_hazirla()
    c = conn.cursor()
    tarih = datetime.now().strftime("%d-%m-%Y")
    c.execute("INSERT INTO ogrenciler (ad_soyad, yas_sinif, degerlendirme, karar, sonuc, veli_adi, telefon, adres, tarih) VALUES (?,?,?,?,?,?,?,?,?)",
              (ad, yas, degerlendirme, karar, sonuc, veli, tel, adres, tarih))
    conn.commit()
    conn.close()
    st.success(f"{ad} kaydı başarıyla eklendi!")

# Kayıtları Listeleme
st.markdown("### 📋 Güncel Öğrenci Listesi")
conn = veritabani_hazirla()
df = pd.read_sql_query("SELECT * FROM ogrenciler", conn)
conn.close()

if not df.empty:
    st.dataframe(df, use_container_width=True)
