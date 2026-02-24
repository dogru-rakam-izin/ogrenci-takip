import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse
import requests

# --- 1. GİRİŞ PANELİ ---
def giris_yap():
    if "giris_basarili" not in st.session_state:
        st.session_state["giris_basarili"] = False
    if not st.session_state["giris_basarili"]:
        st.title("🔒 Yetkili Girişi")
        sifre = st.text_input("Lütfen sistem şifresini giriniz:", type="password")
        if st.button("Giriş Yap"):
            if sifre == "202026":
                st.session_state["giris_basarili"] = True
                st.rerun()
            else:
                st.error("❌ Hatalı şifre!")
        return False
    return True

# --- 2. VERİTABANI BAĞLANTISI ---
def db_baglan():
    conn = sqlite3.connect('rehab_merkezi.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kayitlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, yas_sinif TEXT, 
                  degerlendirme TEXT, karar TEXT, sonuc TEXT, veli_adi TEXT, 
                  tel TEXT, tarih DATE)''')
    conn.commit()
    return conn

# Renk Fonksiyonu
def renk_ata(val):
    colors = {'Hastane Sürecinde': '#FFA500', 'RAM Sürecinde': '#1E90FF', 
              'İptal': '#FF4B4B', 'Kaydedildi': '#28A745', 'Beklemede': '#6c757d'}
    return f'background-color: {colors.get(val, "white")}; color: white; font-weight: bold; border-radius: 5px;'

# --- ANA PROGRAM ---
st.set_page_config(page_title="Rehabilitasyon Takip Sistemi", layout="wide")

# Google Script URL (Senin Yeni Linkin)
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbzV_uZh3duC_if_sgs3R1aAz09DaPqi97nvEOpFdqVhQwIIjJMCma3Kml4NZNoJ_AzEIQ/exec"

if giris_yap():
    st.sidebar.success("✅ Sisteme Giriş Yapıldı")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state["giris_basarili"] = False
        st.rerun()

    st.title("🏥 Rehabilitasyon Merkezi Yönetim Paneli")
    tab1, tab2 = st.tabs(["➕ İşlemler", "📋 Liste & Excel"])

    with tab1:
        col1, col2 = st.columns(2)
        
        # --- YENİ KAYIT ---
        with col1:
            st.subheader("📝 Yeni Öğrenci Ekle")
            with st.form("yeni_form", clear_on_submit=True):
                ad = st.text_input("Ad Soyad")
                yas = st.text_input("Yaş - Sınıf")
                veli = st.text_input("Veli Adı")
                tel = st.text_input("Telefon")
                deger = st.text_area("Değerlendirme")
                karar = st.selectbox("Karar", ["Gelişim Takibi", "Rapor", "Özel", "Beklemede"])
                sonuc = st.selectbox("Sonuç", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                
                if st.form_submit_button("💾 Kaydet"):
                    if ad:
                        tarih_str = str(datetime.now().date())
                        # 1. SQLite Kayıt
                        conn = db_baglan()
                        conn.execute("INSERT INTO kayitlar (ad_soyad, yas_sinif, degerlendirme, karar, sonuc, veli_adi, tel, tarih) VALUES (?,?,?,?,?,?,?,?)",
                                    (ad, yas, deger, karar, sonuc, veli, tel, tarih_str))
                        conn.commit()
                        conn.close()
                        
                        # 2. Google Sheets Kayıt (Sıralı Paket)
                        payload = {
                            "tarih": tarih_str, "ad": ad, "yas": yas, "veli": veli, 
                            "tel": tel, "deger": deger, "karar": karar, "sonuc": sonuc
                        }
                        try:
                            requests.post(GOOGLE_URL, data=payload, timeout=10)
                            st.success(f"✅ {ad} hem sisteme hem tabloya işlendi!")
                        except:
                            st.warning("⚠️ Sisteme kaydedildi ama tabloya gönderilemedi.")
                        
                        st.rerun()

        # --- GÜNCELLEME VE SİLME ---
        with col2:
            st.subheader("⚙️ Düzenle / Sil")
            
            with st.expander("🔄 Durum Güncelle"):
                g_id = st.number_input("ID Girin", min_value=1, step=1, key="upd_id")
                yeni_s = st.selectbox("Yeni Durum", ["Kaydedildi", "Hastane Sürecinde", "RAM
