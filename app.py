import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse

# --- 1. GİRİŞ PANELİ (ŞİFRE GÜNCELLENDİ) ---
def giris_yap():
    if "giris_basarili" not in st.session_state:
        st.session_state["giris_basarili"] = False

    if not st.session_state["giris_basarili"]:
        st.title("🔒 Yetkili Girişi")
        # Yeni şifren: 202026
        sifre = st.text_input("Lütfen sistem şifresini giriniz:", type="password")
        if st.button("Giriş Yap"):
            if sifre == "202026":  # ŞİFRE BURADA GÜNCELLENDİ
                st.session_state["giris_basarili"] = True
                st.rerun()
            else:
                st.error("❌ Hatalı şifre! Lütfen tekrar deneyin.")
        return False
    return True

# --- 2. VERİTABANI VE AYARLAR ---
def db_baglan():
    conn = sqlite3.connect('rehab_merkezi.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kayitlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, yas_sinif TEXT, 
                  degerlendirme TEXT, karar TEXT, sonuc TEXT, veli_adi TEXT, 
                  tel TEXT, adres TEXT, tarih DATE)''')
    conn.commit()
    return conn

# Renk Fonksiyonu (Beklemede eklendi)
def renk_ata(val):
    color = 'white'
    if val == 'Hastane Sürecinde': color = '#FFA500' 
    elif val == 'RAM Sürecinde': color = '#1E90FF' 
    elif val == 'İptal': color = '#FF4B4B' 
    elif val == 'Kaydedildi': color = '#28A745' 
    elif val == 'Beklemede': color = '#6c757d'
    return f'background-color: {color}; color: white; font-weight: bold; border-radius: 5px;'

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
                        conn = db_baglan()
                        cur = conn.cursor()
                        cur.execute("INSERT INTO kayitlar (ad_soyad, yas_sinif, degerlendirme, karar, sonuc, veli_adi, tel, adres, tarih) VALUES (?,?,?,?,?,?,?,?,?)",
                                    (ad, yas, deger, karar, sonuc, veli, tel, adres, tarih))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ {ad} kaydedildi!")
                        
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
        f1, f2, f3 = st.columns(3)
        with f1: ay_sec = st.selectbox("Ay", ["Hepsi"] + [str(i).zfill(2) for i in range(1, 13)])
        with f2: yil_sec = st.selectbox("Yıl", ["Hepsi"] + [str(i) for i in range(2024, 2030)])
        with f3: isim_ara = st.text_input("🔍 İsimle Ara")

        conn = db_baglan()
        df = pd.read_sql_query("SELECT * FROM kayitlar", conn)
        conn.close()

        if not df.empty:
            df['tarih'] = pd.to_datetime(df['tarih'])
            if ay_sec != "Hepsi": df = df[df['tarih'].dt.strftime('%m') == ay_sec]
            if yil_sec != "Hepsi": df = df[df['tarih'].dt.strftime('%Y') == yil_sec]
            if isim_ara: df = df[df['ad_soyad'].str.contains(isim_ara, case=False, na=False)]

            # Excel İndirme
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Liste')
            st.download_button(label="📥 Excel İndir", data=buffer.getvalue(), file_name="Rehab_Liste.xlsx")

            # Tablo Gösterimi
            st.dataframe(df.style.applymap(renk_ata, subset=['sonuc']), use_container_width=True, hide_index=True)
        else:
            st.warning("Veri bulunamadı.")

