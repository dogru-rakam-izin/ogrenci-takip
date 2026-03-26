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

# Google Sheets Bilgileri
SHEET_ID = "1D3O81aBlU7emmHa--V9lugT01Vo0i_oJPFCCu6EQffw"
KAYITLAR_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Kay%C4%B1tlar"
MHRS_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=MHRS"

# YENİ DAĞITIM URL'NİZ BURAYA EKLENDİ
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbxJizfXbGNz7G67ZwNhnxq3Aro1g4RAq1xvuCKQEssgCjAM9xcBs8mS3i9WJy14CgDDuA/exec"

def renk_ata(val):
    colors = {'Hastane Sürecinde': '#FFA500', 'RAM Sürecinde': '#1E90FF', 
              'İptal': '#FF4B4B', 'Kaydedildi': '#28A745', 'Beklemede': '#6c757d'}
    return f'background-color: {colors.get(val, "white")}; color: white; font-weight: bold; border-radius: 5px;'

if giris_yap():
    # Ana Veriyi Çek
    try:
        df_ana = pd.read_csv(KAYITLAR_CSV).dropna(how='all', axis=0).fillna("")
        df_ana.columns = df_ana.columns.str.strip()
        # .0 Temizliği
        for c in ['Telefon', 'Tel']:
            if c in df_ana.columns:
                df_ana[c] = df_ana[c].astype(str).str.replace(r'\.0$', '', regex=True)
    except:
        df_ana = pd.DataFrame()

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
            if not df_ana.empty:
                with st.form("guncelle_form"):
                    secilen_ad = st.selectbox("Öğrenci Seçin", df_ana['Ad Soyad'].unique())
                    yeni_durum = st.selectbox("Yeni Durum", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                    if st.form_submit_button("Güncellemeyi Tamamla"):
                        payload = {"form_tipi": "kayit", "islem_tipi": "guncelle", "ad": secilen_ad, "sonuc": yeni_durum}
                        requests.post(GOOGLE_URL, data=payload)
                        st.success(f"🔄 {secilen_ad} durumu güncellendi!")
                        st.cache_data.clear()

    # --- TAB 2: LİSTE VE WHATSAPP ---
    with tab2:
        if not df_ana.empty:
            # Excel Butonu
            buffer = io.BytesIO()
            df_ana.to_excel(buffer, index=False)
            st.download_button("📥 Listeyi Excel Olarak İndir", buffer.getvalue(), "rehabilitasyon_liste.xlsx")
            
            # Tablo
            st.dataframe(df_ana.style.applymap(renk_ata, subset=['Sonuç'] if 'Sonuç' in df_ana.columns else []), use_container_width=True)
            
            # WhatsApp Bölümü (Geniş ve Detaylı)
            st.markdown("---")
            st.subheader("📲 WhatsApp ile Paylaş")
            secilen_wa = st.selectbox("Paylaşılacak Kişi", df_ana['Ad Soyad'].unique(), key="wa_box")
            
            if st.button("🟢 WhatsApp Mesajı Hazırla"):
                satir = df_ana[df_ana['Ad Soyad'] == secilen_wa].iloc[0]
                
                v_ad = satir.get('Veli Adı', satir.get('Veli', '-'))
                s_durum = satir.get('Sonuç', '-')
                d_notu = satir.get('Değerlendirme', satir.get('Değerlendirme Notu', '-'))
                t_no = satir.get('Telefon', satir.get('Tel', '-'))
                
                mesaj = (
                    f"*ÖĞRENCİ BİLGİ FORMU*\n\n"
                    f"👤 *İsim:* {secilen_wa}\n"
                    f"📋 *Durum:* {s_durum}\n"
                    f"👨‍👩‍👦 *Veli:* {v_ad}\n"
                    f"📞 *Telefon:* {t_no}\n"
                    f"📝 *Değerlendirme:* {d_notu}"
                )
                
                wa_url = f"https://wa.me/?text={urllib.parse.quote(mesaj)}"
                st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:12px 20px; border-radius:8px; cursor:pointer; font-weight:bold; width:100%;">WhatsApp ile Gönder</button></a>', unsafe_allow_html=True)
        else:
            st.info("Henüz kayıtlı veri bulunamadı.")

    # --- TAB 3: MHRS BİLGİLERİ ---
    with tab3:
        m1, m2 = st.columns([1, 2])
        with m1:
            st.subheader("🏥 MHRS Bilgisi Ekle")
            with st.form("mhrs_form", clear_on_submit=True):
                m_ad = st.text_input("Öğrenci Ad Soyad")
                m_tc = st.text_input("TC No")
                m_sifre = st.text_input("MHRS Şifre")
                m_anne = st.text_input("Anne Adı")
                m_baba = st.text_input("Baba Adı")
                if st.form_submit_button("🏥 MHRS Kaydet"):
                    requests.post(GOOGLE_URL, data={"form_tipi": "mhrs", "ad": m_ad, "tc": m_tc, "sifre": m_sifre, "anne": m_anne, "baba": m_baba})
                    st.success("MHRS Bilgisi Eklendi!")
                    st.cache_data.clear()
        
        with m2:
            st.subheader("📋 MHRS Listesi")
            try:
                mhrs_df = pd.read_csv(MHRS_CSV).fillna("")
                for col in mhrs_df.columns:
                    mhrs_df[col] = mhrs_df[col].astype(str).str.replace(r'\.0$', '', regex=True)
                st.dataframe(mhrs_df, use_container_width=True)
            except:
                st.info("MHRS verisi henüz yüklenemedi.")
