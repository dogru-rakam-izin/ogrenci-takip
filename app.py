import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# --- 1. GİRİŞ PANELİ ---
def giris_yap():
    if "giris_basarili" not in st.session_state:
        st.session_state["giris_basarili"] = False
    if not st.session_state["giris_basarili"]:
        st.title("🔒 Yetkili Girişi")
        sifre = st.text_input("Şifre:", type="password")
        if st.button("Sisteme Gir"):
            if sifre == "202026":
                st.session_state["giris_basarili"] = True
                st.rerun()
            else:
                st.error("❌ Hatalı şifre!")
        return False
    return True

# --- 2. VERİTABANI ---
def db_baglan():
    conn = sqlite3.connect('rehab_merkezi.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kayitlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, yas_sinif TEXT, 
                  degerlendirme TEXT, karar TEXT, sonuc TEXT, veli_adi TEXT, 
                  tel TEXT, adres TEXT, tarih DATE)''')
    conn.commit()
    return conn

def renk_ata(val):
    colors = {'Hastane Sürecinde': '#FFA500', 'RAM Sürecinde': '#1E90FF', 
              'İptal': '#FF4B4B', 'Kaydedildi': '#28A745', 'Beklemede': '#6c757d'}
    return f'background-color: {colors.get(val, "white")}; color: white; font-weight: bold'

# --- ANA PROGRAM ---
st.set_page_config(page_title="Rehabilitasyon Yönetim", layout="wide")

if giris_yap():
    st.title("🏥 Rehabilitasyon Merkezi Paneli")
    
    # SEKMELER
    tab1, tab2 = st.tabs(["📝 İşlemler", "📊 Veri Listesi"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Yeni Kayıt")
            with st.form("kayit_form"):
                ad = st.text_input("Ad Soyad")
                yas = st.text_input("Yaş/Sınıf")
                durum = st.selectbox("Durum", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                if st.form_submit_button("Kaydet"):
                    if ad:
                        conn = db_baglan()
                        conn.execute("INSERT INTO kayitlar (ad_soyad, yas_sinif, sonuc, tarih) VALUES (?,?,?,?)",
                                    (ad, yas, durum, datetime.now().date()))
                        conn.commit()
                        st.success("Kaydedildi!")
                        st.rerun()
        
        with c2:
            st.subheader("Düzenle ve Sil")
            # GÜNCELLEME
            edit_id = st.number_input("İşlem Yapılacak ID", min_value=1, step=1)
            yeni_s = st.selectbox("Yeni Durum Seç", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
            if st.button("Durumu Güncelle"):
                conn = db_baglan()
                conn.execute("UPDATE kayitlar SET sonuc = ? WHERE id = ?", (yeni_s, edit_id))
                conn.commit()
                st.success("Güncellendi!")
                st.rerun()
            
            st.markdown("---")
            # SİLME BUTONU (BURADA!)
            if st.button("🔴 BU ID'Yİ SİSTEMDEN SİL"):
                conn = db_baglan()
                conn.execute("DELETE FROM kayitlar WHERE id = ?", (edit_id,))
                conn.commit()
                st.error(f"ID {edit_id} silindi!")
                st.rerun()

    with tab2:
        # FİLTRELER VE LİSTE
        conn = db_baglan()
        df = pd.read_sql_query("SELECT * FROM kayitlar", conn)
        if not df.empty:
            st.dataframe(df.style.applymap(renk_ata, subset=['sonuc']), use_container_width=True)
            
            # EXCEL İNDİRME
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Excel İndir", buffer.getvalue(), "liste.xlsx")
        else:
            st.info("Kayıt yok.")
