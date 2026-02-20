import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. Veritabanı Fonksiyonu
def db_baglan():
    conn = sqlite3.connect('rehab_merkezi.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kayitlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, yas_sinif TEXT, 
                  degerlendirme TEXT, karar TEXT, sonuc TEXT, veli_adi TEXT, 
                  tel TEXT, adres TEXT, tarih TEXT)''')
    conn.commit()
    return conn

# Sayfa Ayarları
st.set_page_config(page_title="Rehabilitasyon Takip", layout="wide")

# Başlık ve Logo Alanı
st.title("🏥 Rehabilitasyon Merkezi Takip Sistemi")
st.markdown("---")

# 2. Kayıt Formu (Sol Taraf) ve Arama/Tablo (Sağ Taraf) Düzeni
col_form, col_liste = st.columns([1, 2])

with col_form:
    st.subheader("➕ Yeni Öğrenci Kaydı")
    with st.form("yeni_kayit", clear_on_submit=True):
        ad = st.text_input("Öğrenci Ad Soyad")
        yas = st.text_input("Yaş - Sınıf")
        veli = st.text_input("Veli Adı")
        tel = st.text_input("Telefon")
        deger = st.text_area("Değerlendirme Notu")
        karar = st.selectbox("Karar", ["Gelişim Takibi", "Rapor Yenileme", "Mezun", "Beklemede"])
        sonuc = st.text_input("Sonuç")
        adres = st.text_area("Adres")
        
        submit = st.form_submit_button("Sisteme İşle")

    if submit:
        if ad: # İsim boş değilse kaydet
            conn = db_baglan()
            cur = conn.cursor()
            tarih_bugun = datetime.now().strftime("%d/%m/%Y")
            cur.execute("INSERT INTO kayitlar (ad_soyad, yas_sinif, degerlendirme, karar, sonuc, veli_adi, tel, adres, tarih) VALUES (?,?,?,?,?,?,?,?,?)",
                        (ad, yas, deger, karar, sonuc, veli, tel, adres, tarih_bugun))
            conn.commit()
            conn.close()
            st.success(f"✅ {ad} başarıyla kaydedildi!")
            st.rerun()
        else:
            st.error("Lütfen öğrenci adını girin!")

with col_liste:
    st.subheader("📋 Kayıtlı Öğrenci Listesi")
    
    # 3. Arama Çubuğu Özelliği
    arama_terimi = st.text_input("🔍 Öğrenci Ara (İsim giriniz...)", "")

    conn = db_baglan()
    # Arama terimine göre veriyi filtrele
    sorgu = "SELECT * FROM kayitlar"
    if arama_terimi:
        sorgu = f"SELECT * FROM kayitlar WHERE ad_soyad LIKE '%{arama_terimi}%'"
    
    df = pd.read_sql_query(sorgu, conn)
    conn.close()

    if not df.empty:
        # Tabloyu göster
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        # 4. Kayıt Silme Alanı
        col_sil1, col_sil2 = st.columns([1, 1])
        with col_sil1:
            sil_id = st.number_input("Silinecek Kayıt ID'si", min_value=1, step=1)
        with col_sil2:
            st.write("") # Boşluk için
            st.write("") 
            if st.button("🗑️ Seçili Kaydı Kalıcı Olarak Sil"):
                conn = db_baglan()
                cur = conn.cursor()
                cur.execute(f"DELETE FROM kayitlar WHERE id={sil_id}")
                conn.commit()
                conn.close()
                st.warning(f"ID {sil_id} başarıyla silindi.")
                st.rerun()
    else:
        st.info("Henüz kayıt bulunmamaktadır veya arama sonucu boş.")

# Alt Bilgi
st.markdown("<br><br><center><small>Doğru Rakam İzin - Öğrenci Takip Sistemi v2.0</small></center>", unsafe_allow_html=True)
