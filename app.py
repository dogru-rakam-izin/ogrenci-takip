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

# Sizin Tablo Bilgileriniz
SHEET_ID = "1D3O81aBlU7emmHa--V9lugT01Vo0i_oJPFCCu6EQffw"
# Google Sheets'ten veri çekme linkleri (CSV formatında)
KAYITLAR_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Kayıtlar"
MHRS_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=MHRS"
# Veri gönderme (Script) linki
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbwu28U2gXrEypbRE2PgBEaq6AHnHnLv0j5tqAyiksk8An4XyA0REdEjAFakTIEsoLJ-uQ/exec"

def renk_ata(val):
    colors = {'Hastane Sürecinde': '#FFA500', 'RAM Sürecinde': '#1E90FF', 
              'İptal': '#FF4B4B', 'Kaydedildi': '#28A745', 'Beklemede': '#6c757d'}
    return f'background-color: {colors.get(val, "white")}; color: white; font-weight: bold; border-radius: 5px;'

if giris_yap():
    tab1, tab2, tab3 = st.tabs(["➕ İşlemler", "📋 Liste & Excel", "🏥 MHRS Bilgileri"])

    # --- TAB 1: YENİ KAYIT VE GÜNCELLEME ---
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
                            st.success(f"✅ {ad} başarıyla eklendi!")
                            st.cache_data.clear()
                        except:
                            st.error("❌ Veri gönderilemedi!")

        with col2:
            st.subheader("🔄 Durum Güncelle")
            with st.expander("Öğrenci Durumunu Değiştir"):
                st.info("Not: Güncelleme yapmak için önce Liste sekmesinden güncel verileri kontrol edin.")
                g_ad = st.text_input("Güncellenecek Öğrenci Ad Soyad")
                yeni_s = st.selectbox("Yeni Durum Seçin", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                if st.button("Güncellemeyi Gönder"):
                    payload = {"form_tipi": "kayit", "ad": g_ad, "sonuc": yeni_s, "tarih": str(datetime.now().date()) + " (GÜNCEL)"}
                    requests.post(GOOGLE_URL, data=payload)
                    st.success("Güncelleme isteği gönderildi!")

    # --- TAB 2: LİSTE VE WHATSAPP ---
    with tab2:
        try:
            # Google Sheets'ten veriyi oku
            df = pd.read_csv(KAYITLAR_CSV)
            if not df.empty:
                st.dataframe(df.style.applymap(renk_ata, subset=['Sonuç'] if 'Sonuç' in df.columns else []), use_container_width=True)
                
                # WhatsApp Paylaşım
                st.markdown("---")
                st.subheader("📲 WhatsApp ile Paylaş")
                secilen_ogrenci = st.selectbox("Paylaşılacak Kişiyi Seçin", df['Ad Soyad'].unique())
                if st.button("🟢 WhatsApp Mesajı Hazırla"):
                    satir = df[df['Ad Soyad'] == secilen_ogrenci].iloc[0]
                    mesaj = f"*Öğrenci Bilgisi*\n👤 *İsim:* {satir['Ad Soyad']}\n📋 *Durum:* {satir['Sonuç']}\n📞 *Tel:* {satir['Telefon']}"
                    wa_link = f"https://wa.me/?text={urllib.parse.quote(mesaj)}"
                    st.markdown(f'<a href="{wa_link}" target="_blank">Mesajı Göndermek İçin Buraya Tıklayın</a>', unsafe_allow_html=True)
            else:
                st.info("Kayıt bulunamadı.")
        except:
            st.error("⚠️ Veriler yüklenemedi. Google Tablo Paylaşım ayarlarını 'Bağlantıya sahip olan herkes' olarak güncelleyin.")

    # --- TAB 3: MHRS ---
    with tab3:
        st.subheader("🏥 MHRS Bilgileri")
        try:
            m_df = pd.read_csv(MHRS_CSV)
            st.dataframe(m_df, use_container_width=True)
        except:
            st.info("MHRS verisi henüz yok veya okunamadı.")
