import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests
import urllib.parse

# --- 1. GİRİŞ PANELİ ---
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

# --- 2. AYARLAR VE LİNKLER ---
st.set_page_config(page_title="Rehabilitasyon Takip Sistemi", layout="wide")

# Sizin Tablo ID'niz
SHEET_ID = "1D3O81aBlU7emmHa--V9lugT01Vo0i_oJPFCCu6EQffw"
# Google Sheets'ten veri çekme linkleri
KAYITLAR_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Kayıtlar"
MHRS_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=MHRS"

# YENİ ALDIĞINIZ GOOGLE SCRIPT URL'Sİ
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbwT6l8hXtguAt6xNS2awOV5T8tM7ihi60vnNVCQfjtDq8fiE_KIg9s5fXvztBmT7WIZVg/exec"

def renk_ata(val):
    colors = {'Hastane Sürecinde': '#FFA500', 'RAM Sürecinde': '#1E90FF', 
              'İptal': '#FF4B4B', 'Kaydedildi': '#28A745', 'Beklemede': '#6c757d'}
    return f'background-color: {colors.get(val, "white")}; color: white; font-weight: bold; border-radius: 5px;'

if giris_yap():
    tab1, tab2, tab3 = st.tabs(["➕ İşlemler", "📋 Liste & Excel", "🏥 MHRS Bilgileri"])

    # --- TAB 1: YENİ ÖĞRENCİ KAYDI ---
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
                        # form_tipi: "kayit" -> Bu veriyi "Kayıtlar" sayfasına gönderir
                        payload = {
                            "form_tipi": "kayit", "tarih": str(datetime.now().date()), 
                            "ad": ad, "yas": yas, "veli": veli, "tel": tel, 
                            "adres": adres, "deger": deger, "karar": karar, "sonuc": sonuc
                        }
                        try:
                            requests.post(GOOGLE_URL, data=payload, timeout=10)
                            st.success(f"✅ {ad} Kayıtlara eklendi!")
                            st.cache_data.clear()
                        except:
                            st.error("❌ Veri gönderilemedi!")

    # --- TAB 2: ÖĞRENCİ LİSTESİ ---
    with tab2:
        try:
            df = pd.read_csv(KAYITLAR_CSV)
            if not df.empty:
                st.dataframe(df.style.applymap(renk_ata, subset=['Sonuç'] if 'Sonuç' in df.columns else []), use_container_width=True)
                
                # WhatsApp Paylaşım
                st.markdown("---")
                st.subheader("📲 WhatsApp ile Paylaş")
                secilen_ogrenci = st.selectbox("Paylaşılacak Kişiyi Seçin", df['Ad Soyad'].unique())
                if st.button("🟢 WhatsApp Mesajı Hazırla"):
                    satir = df[df['Ad Soyad'] == secilen_ogrenci].iloc[0]
                    mesaj = f"*Öğrenci Bilgisi*\n👤 *İsim:* {satir['Ad Soyad']}\n📋 *Durum:* {satir['Sonuç']}\n👨‍👩‍👦 *Veli:* {satir['Veli Adı']}"
                    wa_link = f"https://wa.me/?text={urllib.parse.quote(mesaj)}"
                    st.markdown(f'[Mesajı Göndermek İçin Buraya Tıklayın]({wa_link})')
            else:
                st.info("Kayıtlar sayfasında veri bulunamadı.")
        except:
            st.error("⚠️ Veriler yüklenemedi. Sayfa isminin 'Kayıtlar' olduğundan emin olun.")

    # --- TAB 3: MHRS BİLGİLERİ ---
    with tab3:
        m_col1, m_col2 = st.columns([1, 2])
        with m_col1:
            st.subheader("🏥 MHRS Bilgisi Ekle")
            with st.form("mhrs_form", clear_on_submit=True):
                m_ad = st.text_input("Öğrenci Ad Soyad")
                m_tc = st.text_input("TC No")
                m_sifre = st.text_input("MHRS Şifre")
                m_anne = st.text_input("Anne Adı")
                m_baba = st.text_input("Baba Adı")
                
                if st.form_submit_button("🏥 MHRS Kaydet"):
                    if m_ad:
                        # form_tipi: "mhrs" -> Bu veriyi "MHRS" sayfasına gönderir
                        payload_mhrs = {
                            "form_tipi": "mhrs", "ad": m_ad, "tc": m_tc, 
                            "sifre": m_sifre, "anne": m_anne, "baba": m_baba
                        }
                        try:
                            requests.post(GOOGLE_URL, data=payload_mhrs, timeout=10)
                            st.success(f"✅ {m_ad} MHRS listesine eklendi!")
                            st.cache_data.clear()
                        except:
                            st.error("❌ Gönderilemedi!")

        with m_col2:
            st.subheader("📋 MHRS Listesi")
            try:
                mhrs_df = pd.read_csv(MHRS_CSV)
                if not mhrs_df.empty:
                    st.dataframe(mhrs_df, use_container_width=True)
                else:
                    st.info("MHRS sayfasında henüz veri yok.")
            except:
                st.error("⚠️ MHRS verileri okunamadı. Sayfa isminin 'MHRS' olduğundan emin olun.")
