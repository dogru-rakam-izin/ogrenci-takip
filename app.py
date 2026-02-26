import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import requests
import urllib.parse

# --- GİRİŞ PANELİ ---
def giris_yap():
    if "giris_basarili" not in st.session_state:
        st.session_state["giris_basarili"] = False
    if not st.session_state["giris_basarili"]:
        st.title("🔒 Yetkili Girişi")
        sifre = st.text_input("Sistem Şifresi:", type="password")
        if st.button("Giriş Yap"):
            if sifre == "202026":
                st.session_state["giris_basarili"] = True
                st.rerun()
            else:
                st.error("❌ Hatalı şifre!")
        return False
    return True

# --- RENKLENDİRME ---
def renk_ata(val):
    colors = {'Hastane Sürecinde': '#FFA500', 'RAM Sürecinde': '#1E90FF', 
              'İptal': '#FF4B4B', 'Kaydedildi': '#28A745', 'Beklemede': '#6c757d'}
    return f'background-color: {colors.get(val, "white")}; color: white; font-weight: bold; border-radius: 5px;'

# --- AYARLAR ---
st.set_page_config(page_title="Rehabilitasyon Takip Sistemi", layout="wide")

# ÖNEMLİ: CSV formatında okuma linki (Sizin Spreadsheet ID'niz kullanıldı)
SHEET_ID = "1D3O81aBlU7emmHa--V9lugT01Vo0i_oJPFCCu6EQffw"
KAYITLAR_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Kayıtlar"
MHRS_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=MHRS"

GOOGLE_URL = "https://script.google.com/macros/s/AKfycbwu28U2gXrEypbRE2PgBEaq6AHnHnLv0j5tqAyiksk8An4XyA0REdEjAFakTIEsoLJ-uQ/exec"

if giris_yap():
    tab1, tab2, tab3 = st.tabs(["➕ İşlemler", "📋 Liste & Excel", "🏥 MHRS Bilgileri"])

    # --- TAB 1: ANA İŞLEMLER ---
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📝 Yeni Öğrenci Ekle")
            with st.form("yeni_form", clear_on_submit=True):
                ad = st.text_input("Ad Soyad")
                yas = st.text_input("Yaş - Sınıf")
                veli = st.text_input("Veli Adı")
                tel = st.text_input("Telefon")
                adres = st.text_area("Adres")
                deger = st.text_area("Değerlendirme")
                karar = st.selectbox("Karar", ["Gelişim Takibi", "Rapor", "Özel", "Beklemede"])
                sonuc = st.selectbox("Sonuç", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                
                if st.form_submit_button("💾 Kaydet"):
                    if ad:
                        payload = {
                            "form_tipi": "kayit", "tarih": str(datetime.now().date()), 
                            "ad": ad, "yas": yas, "veli": veli, "tel": tel, 
                            "adres": adres, "deger": deger, "karar": karar, "sonuc": sonuc
                        }
                        try:
                            requests.post(GOOGLE_URL, data=payload, timeout=10)
                            st.success(f"✅ {ad} Google Tabloya kaydedildi! Listeyi yenileyin.")
                            st.cache_data.clear() # Listeyi tazelemek için önbelleği siler
                        except:
                            st.error("❌ Google Tabloya gönderilemedi!")

    # --- TAB 2: LİSTE ---
    with tab2:
        try:
            # Veriyi SQLite yerine doğrudan Google Sheets'ten oku
            df = pd.read_csv(KAYITLAR_CSV)
            
            if not df.empty:
                # Tablodaki başlıkları düzelt (Pandas bazen boş sütun ekleyebilir)
                df = df.dropna(how='all', axis=1)
                
                st.dataframe(df.style.applymap(renk_ata, subset=['Sonuç'] if 'Sonuç' in df.columns else []), use_container_width=True)
                
                # Paylaşım Alanı
                st.markdown("---")
                st.subheader("📲 Kayıt Paylaş (WhatsApp)")
                # Google Sheets'te ID olmadığı için Ad Soyad üzerinden seçtirelim
                secilen_ad = st.selectbox("Paylaşılacak Öğrenciyi Seçin", df['Ad Soyad'].unique())
                if st.button("WhatsApp Hazırla"):
                    satir = df[df['Ad Soyad'] == secilen_ad].iloc[0]
                    mesaj = f"*Öğrenci Kayıt Bilgisi*\n\n👤 *İsim:* {satir['Ad Soyad']}\n📋 *Durum:* {satir['Sonuç']}\n👨‍👩‍👦 *Veli:* {satir['Veli']}"
                    wa_link = f"https://wa.me/?text={urllib.parse.quote(mesaj)}"
                    st.markdown(f'[🟢 WhatsApp ile Gönder]({wa_link})')
            else:
                st.info("Google Tabloda henüz kayıt bulunamadı.")
        except:
            st.warning("⚠️ Google Tabloya bağlanılamadı. Lütfen tablonuzun 'Paylaş' ayarlarından 'Bağlantıya sahip olan herkes görüntüleyebilir' seçeneğini aktif edin.")

    # --- TAB 3: MHRS ---
    with tab3:
        st.subheader("🏥 MHRS Kayıt Sistemi")
        # MHRS Formu (Aynı Payload yapısı)
        # ... (Önceki kodunuzdaki MHRS formunu buraya ekleyebilirsiniz)
        try:
            mhrs_df = pd.read_csv(MHRS_CSV)
            st.dataframe(mhrs_df, use_container_width=True)
        except:
            st.info("MHRS verileri yüklenemedi.")
