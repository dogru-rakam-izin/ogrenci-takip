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
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbxJizfXbGNz7G67ZwNhnxq3Aro1g4RAq1xvuCKQEssgCjAM9xcBs8mS3i9WJy14CgDDuA/exec"

def renk_ata(val):
    colors = {'Hastane Sürecinde': '#FFA500', 'RAM Sürecinde': '#1E90FF', 
              'İptal': '#FF4B4B', 'Kaydedildi': '#28A745', 'Beklemede': '#6c757d'}
    return f'background-color: {colors.get(val, "white")}; color: white; font-weight: bold; border-radius: 5px;'

if giris_yap():
    # Veriyi Çek
    try:
        # Veriyi okurken hata payını düşürmek için engine ve on_bad_lines ekledik
        df_ana = pd.read_csv(KAYITLAR_CSV, on_bad_lines='skip').dropna(how='all', axis=0).fillna("")
        df_ana.columns = df_ana.columns.str.strip()
        for c in ['Telefon', 'Tel']:
            if c in df_ana.columns:
                df_ana[c] = df_ana[c].astype(str).str.replace(r'\.0$', '', regex=True)
    except:
        df_ana = pd.DataFrame()

    tab1, tab2, tab3 = st.tabs(["➕ İşlemler", "📋 Liste & Excel", "🏥 MHRS Bilgileri"])

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
                    if ad:
                        payload = {"form_tipi": "kayit", "islem_tipi": "yeni", "tarih": str(datetime.now().date()), "ad": ad, "yas": yas, "veli": veli, "tel": tel, "adres": adres, "deger": deger, "karar": karar, "sonuc": sonuc}
                        requests.post(GOOGLE_URL, data=payload)
                        st.success(f"✅ {ad} kaydedildi!")
                        st.cache_data.clear()

        with col2:
            st.subheader("🔄 Durum Güncelle")
            if not df_ana.empty and 'Ad Soyad' in df_ana.columns:
                with st.form("guncelle_form"):
                    secilen_ad = st.selectbox("Öğrenci Seçin", df_ana['Ad Soyad'].unique())
                    yeni_durum = st.selectbox("Yeni Durum", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                    if st.form_submit_button("Güncellemeyi Tamamla"):
                        payload = {"form_tipi": "kayit", "islem_tipi": "guncelle", "ad": secilen_ad, "sonuc": yeni_durum}
                        requests.post(GOOGLE_URL, data=payload)
                        st.success(f"🔄 {secilen_ad} güncellendi!")
                        st.cache_data.clear()

    with tab2:
        if not df_ana.empty:
            buffer = io.BytesIO()
            df_ana.to_excel(buffer, index=False)
            st.download_button("📥 Excel İndir", buffer.getvalue(), "liste.xlsx")
            
            # --- HATA DÜZELTME BURADA ---
            # applymap yerine map kullanarak yeni Pandas sürümüyle uyumlu hale getirdik.
            # Ayrıca subset kontrolünü güçlendirdik.
            try:
                if 'Sonuç' in df_ana.columns:
                    st.dataframe(df_ana.style.map(renk_ata, subset=['Sonuç']), use_container_width=True)
                else:
                    st.dataframe(df_ana, use_container_width=True)
            except:
                # Eğer map de hata verirse (eski pandas), applymap'e geri döner
                try:
                    st.dataframe(df_ana.style.applymap(renk_ata, subset=['Sonuç']), use_container_width=True)
                except:
                    st.dataframe(df_ana, use_container_width=True)

            # WhatsApp
            st.markdown("---")
            st.subheader("📲 WhatsApp ile Paylaş")
            secilen_wa = st.selectbox("Paylaşılacak Kişi", df_ana['Ad Soyad'].unique(), key="wa_box")
            if st.button("🟢 WhatsApp Mesajı Hazırla"):
                satir = df_ana[df_ana['Ad Soyad'] == secilen_wa].iloc[0]
                mesaj = f"*BİLGİ FORMU*\n👤 *İsim:* {secilen_wa}\n📋 *Durum:* {satir.get('Sonuç','-')}\n📞 *Tel:* {satir.get('Telefon', satir.get('Tel', '-'))}\n📝 *Not:* {satir.get('Değerlendirme', '-')}"
                st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(mesaj)}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:12px 20px; border-radius:8px; width:100%; font-weight:bold;">WhatsApp ile Gönder</button></a>', unsafe_allow_html=True)

    with tab3:
        m1, m2 = st.columns([1, 2])
        with m1:
            st.subheader("🏥 MHRS Bilgi Ekle")
            with st.form("mhrs_form"):
                m_ad = st.text_input("Öğrenci Ad Soyad")
                m_tc = st.text_input("TC No")
                m_sifre = st.text_input("MHRS Şifre")
                if st.form_submit_button("🏥 MHRS Kaydet"):
                    requests.post(GOOGLE_URL, data={"form_tipi": "mhrs", "ad": m_ad, "tc": m_tc, "sifre": m_sifre})
                    st.success("MHRS Eklendi!")
        with m2:
            st.subheader("📋 MHRS Listesi")
            try:
                m_df = pd.read_csv(MHRS_CSV).fillna("")
                for c in m_df.columns: m_df[c] = m_df[c].astype(str).str.replace(r'\.0$', '', regex=True)
                st.dataframe(m_df, use_container_width=True)
            except:
                st.info("MHRS verisi bulunamadı.")
