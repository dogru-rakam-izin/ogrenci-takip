import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import urllib.parse
import io

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

SHEET_ID = "1D3O81aBlU7emmHa--V9lugT01Vo0i_oJPFCCu6EQffw"
KAYITLAR_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Kay%C4%B1tlar"
MHRS_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=MHRS"
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbwT6l8hXtguAt6xNS2awOV5T8tM7ihi60vnNVCQfjtDq8fiE_KIg9s5fXvztBmT7WIZVg/exec"

def renk_ata(val):
    colors = {'Hastane Sürecinde': '#FFA500', 'RAM Sürecinde': '#1E90FF', 
              'İptal': '#FF4B4B', 'Kaydedildi': '#28A745', 'Beklemede': '#6c757d'}
    return f'background-color: {colors.get(val, "white")}; color: white; font-weight: bold; border-radius: 5px;'

if giris_yap():
    # Verileri çek
    try:
        df_ana = pd.read_csv(KAYITLAR_CSV).dropna(how='all', axis=0).fillna("")
        df_ana.columns = df_ana.columns.str.strip()
    except:
        df_ana = pd.DataFrame()

    tab1, tab2, tab3 = st.tabs(["➕ İşlemler", "📋 Liste & Çıktı", "🏥 MHRS Bilgileri"])

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
                deger = st.text_area("Değerlendirme Notu")
                karar = st.selectbox("Karar", ["Gelişim Takibi", "Rapor", "Özel", "Beklemede"])
                sonuc = st.selectbox("Sonuç", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                if st.form_submit_button("💾 Kaydet"):
                    payload = {"form_tipi": "kayit", "islem_tipi": "yeni", "tarih": str(datetime.now().date()), "ad": ad, "yas": yas, "veli": veli, "tel": tel, "adres": adres, "deger": deger, "karar": karar, "sonuc": sonuc}
                    requests.post(GOOGLE_URL, data=payload)
                    st.success("Kayıt Başarılı!")
                    st.cache_data.clear()

        with col2:
            st.subheader("🔄 Durum Güncelle")
            if not df_ana.empty:
                with st.form("guncelle_form"):
                    secilen_ad = st.selectbox("Öğrenci Seçin", df_ana['Ad Soyad'].unique())
                    yeni_durum = st.selectbox("Yeni Durum", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                    if st.form_submit_button("Güncelle"):
                        payload = {"form_tipi": "kayit", "islem_tipi": "guncelle", "ad": secilen_ad, "sonuc": yeni_durum}
                        requests.post(GOOGLE_URL, data=payload)
                        st.success("Güncelleme Gönderildi!")
                        st.cache_data.clear()

    # --- TAB 2: LİSTE ---
    with tab2:
        if not df_ana.empty:
            # Excel Hazırla
            buffer = io.BytesIO()
            df_ana.to_excel(buffer, index=False)
            st.download_button("📥 Excel İndir", buffer.getvalue(), "liste.xlsx")
            
            # Tabloyu Göster
            st.dataframe(df_ana.style.applymap(renk_ata, subset=['Sonuç'] if 'Sonuç' in df_ana.columns else []), use_container_width=True)
            
            # WhatsApp
            st.subheader("📲 WhatsApp")
            wa_ogrenci = st.selectbox("Mesaj Hazırla", df_ana['Ad Soyad'].unique())
            if st.button("Hazırla"):
                s = df_ana[df_ana['Ad Soyad'] == wa_ogrenci].iloc[0]
                m = f"*BİLGİ*\n👤 {wa_ogrenci}\n📋 {s.get('Sonuç','')}\n📞 {s.get('Telefon','')}"
                st.markdown(f'[WhatsApp Gönder](https://wa.me/?text={urllib.parse.quote(m)})')

    # --- TAB 3: MHRS (Geri Geldi) ---
    with tab3:
        m1, m2 = st.columns([1, 2])
        with m1:
            st.subheader("🏥 Bilgi Ekle")
            with st.form("mhrs_yeni"):
                m_ad = st.text_input("Ad Soyad")
                m_tc = st.text_input("TC")
                m_sf = st.text_input("Şifre")
                if st.form_submit_button("MHRS Kaydet"):
                    requests.post(GOOGLE_URL, data={"form_tipi": "mhrs", "ad": m_ad, "tc": m_tc, "sifre": m_sf})
                    st.success("MHRS Eklendi")
        with m2:
            st.subheader("📋 MHRS Listesi")
            try:
                mhrs_df = pd.read_csv(MHRS_CSV).fillna("")
                st.dataframe(mhrs_df, use_container_width=True)
            except:
                st.info("Veri yok.")
