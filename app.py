import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import io
import urllib.parse

# --- GÜNCEL AYARLARINIZ ---
URL = "https://script.google.com/macros/s/AKfycbxbTnCrJpQQCHhrVb10LoZ29n9Ej2_sHnNW2eDhKSLXAIzqz71TvQdfmpLjiqlWoO4y5w/exec" 
S_ID = "1D3O81aBlU7emmHa--V9lugT01Vo0i_oJPFCCu6EQffw"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Doğru Rakam Öğrenci Takip", layout="wide")

# --- GİRİŞ PANELİ ---
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

def verileri_yukle():
    try:
        # Cache temizleme için timestamp ekliyoruz
        df = pd.read_csv(f"{CSV_URL}&cache={datetime.now().timestamp()}")
        return df
    except:
        return pd.DataFrame()

def renk_ata(val):
    color = 'white'
    if val == 'Hastane Sürecinde': color = '#FFA500' 
    elif val == 'RAM Sürecinde': color = '#1E90FF' 
    elif val == 'İptal': color = '#FF4B4B' 
    elif val == 'Kaydedildi': color = '#28A745' 
    elif val == 'Beklemede': color = '#6c757d'
    return f'background-color: {color}; color: white; font-weight: bold; border-radius: 5px;'

# --- ANA PROGRAM ---
if giris_yap():
    st.sidebar.success("✅ Giriş Yapıldı")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state["giris_basarili"] = False
        st.rerun()

    st.title("🏥 Doğru Rakam Öğrenci Yönetim Paneli")
    sekme1, sekme2 = st.tabs(["➕ Yeni Kayıt", "📋 Liste & Excel"])

    with sekme1:
        st.subheader("Yeni Öğrenci Ekle")
        with st.form("yeni_kayit", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                ad = st.text_input("Ad Soyad").upper()
                yas = st.text_input("Yaş - Sınıf")
                veli = st.text_input("Veli Adı").upper()
            with col2:
                tel = st.text_input("Telefon")
                karar = st.selectbox("Karar", ["Gelişim Takibi", "Rapor", "Özel", "Beklemede"])
                sonuc = st.selectbox("Sonuç Durumu", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
            
            deger = st.text_area("Değerlendirme")
            adres = st.text_area("Adres")
            tarih = datetime.now().strftime("%d/%m/%Y")
            
            if st.form_submit_button("Sisteme Kaydet"):
                if ad:
                    payload = {
                        "id": datetime.now().strftime("%H%M%S"), 
                        "ad": ad, "yas": yas, "deger": deger, "karar": karar,
                        "sonuc": sonuc, "veli": veli, "tel": tel, "adres": adres, "tarih": tarih
                    }
                    try:
                        response = requests.post(URL, data=json.dumps(payload))
                        st.success(f"✅ {ad} başarıyla kaydedildi!")
                        
                        mesaj = f"📢 *YENİ ÖĞRENCİ KAYDI*\n👤 *Ad:* {ad}\n📍 *Durum:* {sonuc}\n📅 *Tarih:* {tarih}"
                        wa_link = f"https://wa.me/?text={urllib.parse.quote(mesaj)}"
                        st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; width:100%; cursor:pointer;">🟢 WhatsApp Grubuna Bildir</button></a>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"❌ Hata: {e}")

    with sekme2:
        st.subheader("📋 Kayıtlı Öğrenci Listesi")
        df = verileri_yukle()
        
        if not df.empty:
            df.columns = [c.strip() for c in df.columns]
            
            # Hataya sebep olan kısım düzeltildi:
            csv_data = df.to_csv(index=False, sep=';').encode('utf-8-sig')
            st.download_button(
                label="📥 Excel İndir (Sütunlar Ayrılmış)", 
                data=csv_data, 
                file_name="Ogrenci_Takip_Listesi.csv", 
                mime="text/csv"
            )
            
            st.dataframe(df.style.applymap(renk_ata, subset=['Sonuç']), use_container_width=True)
        else:
            st.info("Henüz kayıtlı veri yok.")
