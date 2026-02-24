import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse
import requests  # Google Script'e veri yollamak için gerekli

# --- 1. GİRİŞ PANELİ ---
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
                st.error("❌ Hatalı şifre! Lütfen tekrar deneyin.")
        return False
    return True

# --- 2. VERİTABANI BAĞLANTISI ---
def db_baglan():
    conn = sqlite3.connect('rehab_merkezi.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kayitlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, yas_sinif TEXT, 
                  degerlendirme TEXT, karar TEXT, sonuc TEXT, veli_adi TEXT, 
                  tel TEXT, adres TEXT, tarih DATE)''')
    conn.commit()
    return conn

# Renk Fonksiyonu
def renk_ata(val):
    color = 'white'
    colors = {'Hastane Sürecinde': '#FFA500', 'RAM Sürecinde': '#1E90FF', 
              'İptal': '#FF4B4B', 'Kaydedildi': '#28A745', 'Beklemede': '#6c757d'}
    return f'background-color: {colors.get(val, "white")}; color: white; font-weight: bold; border-radius: 5px;'

# --- ANA PROGRAM ---
st.set_page_config(page_title="Rehabilitasyon Pro Takip", layout="wide")

if giris_yap():
    st.sidebar.success("✅ Giriş Yapıldı")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state["giris_basarili"] = False
        st.rerun()

    st.title("🏥 Rehabilitasyon Merkezi Yönetim Paneli")

    sekme1, sekme2 = st.tabs(["➕ Yeni Kayıt & Güncelleme", "📋 Liste & Excel"])

    with sekme1:
        col_yeni, col_guncelle = st.columns(2)
        
        with col_yeni:
            st.subheader("Yeni Öğrenci Ekle")
            with st.form("yeni_kayit", clear_on_submit=True):
                ad = st.text_input("Ad Soyad")
                yas = st.text_input("Yaş - Sınıf")
                veli = st.text_input("Veli Adı")
                tel = st.text_input("Telefon")
                deger = st.text_area("Değerlendirme")
                karar = st.selectbox("Karar", ["Gelişim Takibi", "Rapor", "Özel", "Beklemede"])
                sonuc = st.selectbox("Sonuç Durumu", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                adres = st.text_area("Adres")
                tarih = st.date_input("Kayıt Tarihi", datetime.now())
                
                if st.form_submit_button("Sisteme Kaydet"):
                    if ad:
                        # 1. Yerel Veritabanına Kaydet
                        conn = db_baglan()
                        cur = conn.cursor()
                        cur.execute("INSERT INTO kayitlar (ad_soyad, yas_sinif, degerlendirme, karar, sonuc, veli_adi, tel, adres, tarih) VALUES (?,?,?,?,?,?,?,?,?)",
                                    (ad, yas, deger, karar, sonuc, veli, tel, adres, tarih))
                        conn.commit()
                        conn.close()
                        
                        # 2. GOOGLE SCRIPT'E GÖNDER (Senin linkin)
                        google_url = "https://script.google.com/macros/s/AKfycbxbTnCrJpQQCHhrVb10LoZ29n9Ej2_sHnNW2eDhKSLXAIzqz71TvQdfmpLjiqlWoO4y5w/exec"
                        veri_paketi = {
                            "ad": ad, "yas": yas, "veli": veli, "tel": tel, 
                            "karar": karar, "sonuc": sonuc, "tarih": str(tarih)
                        }
                        try:
                            requests.post(google_url, data=veri_paketi)
                        except:
                            pass # Bağlantı hatası olsa bile yerel kaydı bozmaz
                        
                        st.success(f"✅ {ad} başarıyla kaydedildi!")
                        
                        # WhatsApp Bildirimi
                        mesaj = f"📢 *YENİ ÖĞRENCİ KAYDI*\n👤 *Ad:* {ad}\n📍 *Sonuç:* {sonuc}"
                        wa_link = f"https://wa.me/?text={urllib.parse.quote(mesaj)}"
                        st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; width:100%; cursor:pointer;">🟢 WhatsApp Grubuna Bildir</button></a>', unsafe_allow_html=True)

        with col_guncelle:
            st.subheader("🔄 Durum Güncelle")
            g_id = st.number_input("Güncellenecek ID", min_value=1, step=1)
            g_durum = st.selectbox("Yeni Durum", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
            if st.button("Durumu Güncelle"):
                conn = db_baglan()
                cur = conn.cursor()
                cur.execute("UPDATE kayitlar SET sonuc = ? WHERE id = ?", (g_durum, g_id))
                conn.commit()
                conn.close()
                st.success("Güncellendi!")
                st.rerun()

    with sekme2:
        # --- SİLME PANELİ (EN ÜSTTE) ---
        st.error("🚨 KAYIT SİLME BÖLÜMÜ")
        sil_c1, sil_c2 = st.columns([1, 2])
        with sil_c1:
            sil_id = st.number_input("Silinecek ID'yi girin", min_value=1, step=1, key="delete_box")
        with sil_c2:
            st.write(" ")
            st.write(" ")
            if st.button("🔴 BU KAYDI SİSTEMDEN KALICI OLARAK SİL"):
                conn = db_baglan()
                cur = conn.cursor()
                cur.execute("DELETE FROM kayitlar WHERE id=?", (sil_id,))
                conn.commit()
                conn.close()
                st.success(f"ID {sil_id} silindi!")
                st.rerun()
        
        st.markdown("---")
        
        # LİSTELEME
        conn = db_baglan()
        df = pd.read_sql_query("SELECT * FROM kayitlar", conn)
        conn.close()

        if not df.empty:
            df['tarih'] = pd.to_datetime(df['tarih'])
            # Filtreler
            f1, f2, f3 = st.columns(3)
            with f1: ay = st.selectbox("Ay", ["Hepsi"] + [str(i).zfill(2) for i in range(1, 13)])
            with f2: yil = st.selectbox("Yıl", ["Hepsi"] + [str(i) for i in range(2024, 2030)])
            with f3: arama = st.text_input("🔍 İsim Ara")
            
            if ay != "Hepsi": df = df[df['tarih'].dt.strftime('%m') == ay]
            if yil != "Hepsi": df = df[df['tarih'].dt.strftime('%Y') == yil]
            if arama: df = df[df['ad_soyad'].str.contains(arama, case=False, na=False)]

            # Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Excel İndir", buffer.getvalue(), "Rehab_Liste.xlsx")

            # Tablo
            st.dataframe(df.style.applymap(renk_ata, subset=['sonuc']), use_container_width=True)
        else:
            st.warning("Veri bulunamadı.")
