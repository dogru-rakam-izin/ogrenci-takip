import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. Veritabanı Ayarları
def db_baglan():
    conn = sqlite3.connect('rehab_merkezi.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kayitlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, yas_sinif TEXT, 
                  degerlendirme TEXT, karar TEXT, sonuc TEXT, veli_adi TEXT, 
                  tel TEXT, adres TEXT, tarih DATE)''')
    conn.commit()
    return conn

st.set_page_config(page_title="Rehabilitasyon Gelişmiş Takip", layout="wide")

# Renk Fonksiyonu (Tablodaki sonuçları renklendirmek için)
def renk_ata(val):
    color = 'white'
    if val == 'Hastane Sürecinde':
        color = '#FFA500' # Turuncu
    elif val == 'RAM Sürecinde':
        color = '#1E90FF' # Mavi
    elif val == 'İptal':
        color = '#FF4B4B' # Kırmızı
    elif val == 'Kaydedildi':
        color = '#28A745' # Yeşil
    return f'background-color: {color}; color: white; font-weight: bold'

st.title("🏥 Rehabilitasyon Merkezi | Gelişmiş Takip Sistemi")
st.markdown("---")

col_form, col_liste = st.columns([1, 2.5])

# --- SOL TARAF: KAYIT FORMU ---
with col_form:
    st.subheader("➕ Yeni Kayıt Ekle")
    with st.form("yeni_kayit", clear_on_submit=True):
        ad = st.text_input("Öğrenci Ad Soyad")
        yas = st.text_input("Yaş - Sınıf")
        veli = st.text_input("Veli Adı")
        tel = st.text_input("Telefon")
        deger = st.text_area("Değerlendirme")
        karar = st.selectbox("Karar", ["Gelişim Takibi", "Rapor Yenileme", "Mezun", "Beklemede"])
        
        # Sonuç Kısmı (İstediğin seçeneklerle)
        sonuc = st.selectbox("Sonuç Durumu", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "İptal"])
        
        adres = st.text_area("Adres")
        tarih = st.date_input("Kayıt Tarihi", datetime.now()) # Geçmişe dönük kayıt imkanı
        
        submit = st.form_submit_button("Sisteme Kaydet")

    if submit:
        if ad:
            conn = db_baglan()
            cur = conn.cursor()
            cur.execute("INSERT INTO kayitlar (ad_soyad, yas_sinif, degerlendirme, karar, sonuc, veli_adi, tel, adres, tarih) VALUES (?,?,?,?,?,?,?,?,?)",
                        (ad, yas, deger, karar, sonuc, veli, tel, adres, tarih))
            conn.commit()
            conn.close()
            st.success(f"✅ {ad} için işlem başarıyla tamamlandı!")
            st.rerun()

# --- SAĞ TARAF: FİLTRELEME VE LİSTELEME ---
with col_liste:
    st.subheader("📋 Kayıt Filtreleme ve Listeleme")
    
    # TARİHSEL ARAMA ALANI
    filtre_col1, filtre_col2, filtre_col3 = st.columns(3)
    
    with filtre_col1:
        ay_secimi = st.selectbox("Ay Seçiniz", ["Hepsi"] + [str(i).zfill(2) for i in range(1, 13)])
    with filtre_col2:
        yil_secimi = st.selectbox("Yıl Seçiniz", ["Hepsi"] + [str(i) for i in range(2023, 2030)])
    with filtre_col3:
        isim_ara = st.text_input("🔍 İsimle Ara")

    conn = db_baglan()
    df = pd.read_sql_query("SELECT * FROM kayitlar", conn)
    conn.close()

    if not df.empty:
        # Tarih formatını düzenle
        df['tarih'] = pd.to_datetime(df['tarih'])
        
        # Filtreleme İşlemleri
        if ay_secimi != "Hepsi":
            df = df[df['tarih'].dt.strftime('%m') == ay_secimi]
        if yil_secimi != "Hepsi":
            df = df[df['tarih'].dt.strftime('%Y') == yil_secimi]
        if isim_ara:
            df = df[df['ad_soyad'].str.contains(isim_ara, case=False, na=False)]

        # TABLO RENKLENDİRME
        st.write(f"Toplam {len(df)} kayıt bulundu.")
        styled_df = df.style.applymap(renk_ata, subset=['sonuc'])
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # SİLME BÖLÜMÜ
        with st.expander("🗑️ Kayıt Silme Paneli"):
            sil_id = st.number_input("Silinecek ID", min_value=1, step=1)
            if st.button("ID'ye Göre Sil"):
                conn = db_baglan()
                cur = conn.cursor()
                cur.execute(f"DELETE FROM kayitlar WHERE id={sil_id}")
                conn.commit()
                conn.close()
                st.warning(f"ID {sil_id} silindi!")
                st.rerun()
    else:
        st.info("Kriterlere uygun kayıt bulunamadı.")
