import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import urllib.parse
import io

# --- GİRİŞ ---
def giris_yap():
    if "giris_basarili" not in st.session_state: st.session_state["giris_basarili"] = False
    if not st.session_state["giris_basarili"]:
        st.title("🔒 Yetkili Girişi")
        sifre = st.text_input("Şifre:", type="password")
        if st.button("Giriş"):
            if sifre == "202026":
                st.session_state["giris_basarili"] = True
                st.rerun()
            else: st.error("Hatalı!")
        return False
    return True

st.set_page_config(page_title="Rehabilitasyon Sistemi", layout="wide")

SHEET_ID = "1D3O81aBlU7emmHa--V9lugT01Vo0i_oJPFCCu6EQffw"
KAYITLAR_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Kay%C4%B1tlar"
MHRS_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=MHRS"
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbxJizfXbGNz7G67ZwNhnxq3Aro1g4RAq1xvuCKQEssgCjAM9xcBs8mS3i9WJy14CgDDuA/exec"

if giris_yap():
    # Veriyi Çek
    try:
        df = pd.read_csv(KAYITLAR_CSV).dropna(how='all', axis=0).fillna("")
        df.columns = df.columns.str.strip()
        for c in ['Telefon', 'Tel']: 
            if c in df.columns: df[c] = df[c].astype(str).str.replace(r'\.0$', '', regex=True)
    except: df = pd.DataFrame()

    t1, t2, t3 = st.tabs(["➕ İşlemler", "📋 Liste", "🏥 MHRS"])

    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📝 Yeni Kayıt")
            with st.form("yeni"):
                ad = st.text_input("Ad Soyad")
                yas = st.text_input("Yaş")
                veli = st.text_input("Veli")
                tel = st.text_input("Telefon")
                adr = st.text_area("Adres")
                dgr = st.text_area("Değerlendirme")
                krr = st.selectbox("Karar", ["Gelişim Takibi", "Rapor", "Özel"])
                snc = st.selectbox("Sonuç", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                if st.form_submit_button("Kaydet"):
                    requests.post(GOOGLE_URL, data={"form_tipi":"kayit","islem_tipi":"yeni","tarih":str(datetime.now().date()),"ad":ad,"yas":yas,"veli":veli,"tel":tel,"adres":adr,"deger":dgr,"karar":krr,"sonuc":snc})
                    st.success("Kaydedildi!")
                    st.cache_data.clear()
        
        with c2:
            st.subheader("🔄 Durum Güncelle")
            if not df.empty:
                with st.form("guncelle"):
                    secilen = st.selectbox("Öğrenci Seç", df['Ad Soyad'].unique())
                    yeni_snc = st.selectbox("Yeni Durum", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                    if st.form_submit_button("Güncelle"):
                        requests.post(GOOGLE_URL, data={"form_tipi":"kayit","islem_tipi":"guncelle","ad":secilen,"sonuc":yeni_snc})
                        st.success("Güncellendi!")
                        st.cache_data.clear()

    with t2:
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False)
            st.download_button("📥 Excel İndir", buffer.getvalue(), "liste.xlsx")
        else: st.info("Liste boş.")

    with t3:
        m1, m2 = st.columns([1,2])
        with m1:
            st.subheader("🏥 MHRS Ekle")
            with st.form("mhrs_f"):
                m_ad = st.text_input("Ad Soyad")
                m_tc = st.text_input("TC")
                m_sf = st.text_input("Şifre")
                if st.form_submit_button("MHRS Kaydet"):
                    requests.post(GOOGLE_URL, data={"form_tipi":"mhrs","ad":m_ad,"tc":m_tc,"sifre":m_sf})
                    st.success("MHRS Eklendi")
                    st.cache_data.clear()
        with m2:
            st.subheader("📋 MHRS Listesi")
            try:
                m_df = pd.read_csv(MHRS_CSV).fillna("")
                for c in m_df.columns: m_df[c] = m_df[c].astype(str).str.replace(r'\.0$', '', regex=True)
                st.dataframe(m_df, use_container_width=True)
            except: st.info("MHRS verisi yok.")
