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
KAYITLAR_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Kay%C4%B1tlar"
MHRS_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=MHRS"
# Veri gönderme (Yeni Aldığınız Script URL)
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbwT6l8hXtguAt6xNS2awOV5T8tM7ihi60vnNVCQfjtDq8fiE_KIg9s5fXvztBmT7WIZVg/exec"

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
            st.info("Not: Bu işlem mevcut kaydın sonucunu değiştirir.")
            with st.form("guncelle_form"):
                g_ad = st.text_input("Güncellenecek Öğrenci Ad Soyad")
                yeni_s = st.selectbox("Yeni Durum Seçin", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                if st.form_submit_button("Güncellemeyi Gönder"):
                    payload = {"form_tipi": "kayit", "ad": g_ad, "sonuc": yeni_s, "tarih": str(datetime.now().date()) + " (GÜNCEL)"}
                    requests.post(GOOGLE_URL, data=payload)
                    st.success("Güncelleme isteği gönderildi!")
                    st.cache_data.clear()

    # --- TAB 2: ÖĞRENCİ LİSTESİ ---
    with tab2:
        try:
            # Veriyi çek
            df = pd.read_csv(KAYITLAR_CSV)
            
            if not df.empty:
                # 1. TEMİZLİK: Tamamen boş olan satır ve sütunları kaldır
                df = df.dropna(how='all', axis=0) # Boş satırlar
                df = df.dropna(how='all', axis=1) # Boş sütunlar
                
                # 2. TEMİZLİK: "Unnamed" sütunları filtrele
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                
                # 3. TEMİZLİK: None veya NaN yazan yerleri boşlukla değiştir
                df = df.fillna("")
                
                # Sütun isimlerini temizle
                df.columns = df.columns.str.strip()
                
                # Tabloyu Göster
                sonuc_col = 'Sonuç' if 'Sonuç' in df.columns else None
                if sonuc_col:
                    st.dataframe(df.style.applymap(renk_ata, subset=[sonuc_col]), use_container_width=True)
                else:
                    st.dataframe(df, use_container_width=True)
                
                # WhatsApp Paylaşım
               
st.markdown("---")
st.subheader("📲 WhatsApp ile Paylaş")
if 'Ad Soyad' in df.columns:
    secilen_ogrenci = st.selectbox("Paylaşılacak Kişiyi Seçin", df['Ad Soyad'].unique())
    
    if st.button("🟢 WhatsApp Mesajı Hazırla"):
        # Seçilen öğrencinin satırını bul
        satir = df[df['Ad Soyad'] == secilen_ogrenci].iloc[0]
        
        # Sütun isimlerini kontrol ederek verileri çek (Boşsa 'Belirtilmemiş' yazar)
        veli_ismi = satir.get('Veli Adı', satir.get('Veli', 'Belirtilmemiş'))
        durum_bilgisi = satir.get('Sonuç', 'Belirtilmemiş')
        # DEĞERLENDİRME alanını buradan ekliyoruz:
        degerlendirme_notu = satir.get('Değerlendirme', satir.get('Değer', 'Belirtilmemiş'))
        
        # WhatsApp Mesaj Taslağı
        mesaj = (
            f"*Öğrenci Bilgisi*\n"
            f"👤 *İsim:* {secilen_ogrenci}\n"
            f"📋 *Durum:* {durum_bilgisi}\n"
            f"👨‍👩‍👦 *Veli:* {veli_ismi}\n"
            f"📝 *Değerlendirme:* {degerlendirme_notu}"
        )
        
        # URL kodlama ve Link oluşturma
        wa_link = f"https://wa.me/?text={urllib.parse.quote(mesaj)}"
        
        # Şık bir buton ile yönlendirme
        st.markdown(f'''
            <a href="{wa_link}" target="_blank">
                <button style="
                    background-color:#25D366; 
                    color:white; 
                    border:none; 
                    padding:12px 24px; 
                    border-radius:8px; 
                    cursor:pointer; 
                    font-weight:bold;
                    width:100%;
                    font-size:16px;">
                    WhatsApp ile Gönder
                </button>
            </a>
            ''', unsafe_allow_html=True)
            else:
                st.info("Kayıtlar sayfasında henüz veri yok.")
        except Exception as e:
            st.error(f"⚠️ Veriler yüklenemedi: {e}")

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
                st.info("MHRS verileri henüz yüklenmedi.")



