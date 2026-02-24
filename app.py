import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import io
import urllib.parse

# --- AYARLAR ---
# Sizin verdiğiniz Apps Script URL'si
URL = "https://script.google.com/macros/s/AKfycbxbTnCrJpQQCHhrVb10LoZ29n9Ej2_sHnNW2eDhKSLXAIzqz71TvQdfmpLjiqlWoO4y5w/exec" 
# Sizin verdiğiniz Google Sheets ID
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
        # Cache çakışmasını önlemek için zaman damgası ekliyoruz
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
                        requests.post(URL, data=json.dumps(payload))
                        st.success(f"✅ {ad} başarıyla Google Sheets'e kaydedildi!")
                        
                        mesaj = f"📢 *YENİ ÖĞRENCİ KAYDI*\n👤 *Ad:* {ad}\n📍 *Durum:* {sonuc}\n📅 *Tarih:* {tarih}"
                        wa_link = f"https://wa.me/?text={urllib.parse.quote(mesaj)}"
                        st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; width:100%; cursor:pointer;">🟢 WhatsApp Grubuna Bildir</button></a>', unsafe_allow_html=True)
                    except:
                        st.error("❌ Kayıt gönderilirken bir hata oluştu.")

    with sekme2:
        st.subheader("📋 Kayıtlı Öğrenci Listesi")
        df = verileri_yukle()
        
        if not df.empty:
            # Sütunlardaki olası boşlukları temizle
            df.columns = [c.strip() for c in df.columns]
            
            # Arama ve Filtreleme
            f1, f2 = st.columns(2)
            with f1:
                isim_ara = st.text_input("🔍 İsimle Ara")
            with f2:
                yil_listesi = ["Hepsi"]
                if 'Tarih' in df.columns:
                    yillar = sorted(list(set(df['Tarih'].astype(str).str[-4:].tolist())))
                    yil_listesi += yillar
                yil_sec = st.selectbox("Yıl Filtresi", yil_listesi)

            # Filtre Uygulama
            filtered_df = df.copy()
            if isim_ara:
                filtered_df = filtered_df[filtered_df['Ad Soyad'].str.contains(isim_ara, case=False, na=False)]
            if yil_sec != "Hepsi":
                filtered_df = filtered_df[filtered_df['Tarih'].astype(str).str.endswith(yil_sec)]

            # Excel İndirme (Sütun ayrımı için noktalı virgül kullanıldı)
            csv_data = filtered_df.to_csv(index=False, sep=';').encode('utf-8-sig')
            st.download_button(
                label="📥 Listeyi Excel (CSV) Olarak İndir", 
                data=csv_data, 
                file_name="Ogrenci_Takip_Listesi.csv", 
                mime="text/csv"
            )
            
            # Tablo Gösterimi
            st.dataframe(filtered_df.style.applymap(renk_ata, subset=['Sonuç']), use_container_width=True)
        else:
            st.info("Henüz görüntülenecek veri bulunamadı.")
