import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import requests

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

# --- 2. VERİTABANI BAĞLANTISI ---
def db_baglan():
    conn = sqlite3.connect('rehab_merkezi.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kayitlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, yas_sinif TEXT, 
                  degerlendirme TEXT, karar TEXT, sonuc TEXT, veli_adi TEXT, 
                  tel TEXT, adres TEXT, tarih DATE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mhrs_bilgileri 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, tc_no TEXT, 
                  sifre TEXT, anne_adi TEXT, baba_adi TEXT)''')
    conn.commit()
    return conn

def renk_ata(val):
    colors = {'Hastane Sürecinde': '#FFA500', 'RAM Sürecinde': '#1E90FF', 
              'İptal': '#FF4B4B', 'Kaydedildi': '#28A745', 'Beklemede': '#6c757d'}
    return f'background-color: {colors.get(val, "white")}; color: white; font-weight: bold; border-radius: 5px;'

# --- AYARLAR ---
st.set_page_config(page_title="Rehabilitasyon Takip Sistemi", layout="wide")

# Google Script URL
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbwu28U2gXrEypbRE2PgBEaq6AHnHnLv0j5tqAyiksk8An4XyA0REdEjAFakTIEsoLJ-uQ/exec"

if giris_yap():
    tab1, tab2, tab3 = st.tabs(["➕ İşlemler", "📋 Liste & Excel", "🏥 MHRS Bilgileri"])

    # --- TAB 1: ANA İŞLEMLER ---
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
                        tarih_str = str(datetime.now().date())
                        conn = db_baglan()
                        conn.execute("INSERT INTO kayitlar (ad_soyad, yas_sinif, degerlendirme, karar, sonuc, veli_adi, tel, adres, tarih) VALUES (?,?,?,?,?,?,?,?,?)",
                                    (ad, yas, deger, karar, sonuc, veli, tel, adres, tarih_str))
                        conn.commit()
                        conn.close()
                        
                        payload = {"form_tipi": "kayit", "tarih": tarih_str, "ad": ad, "yas": yas, "veli": veli, "tel": tel, "adres": adres, "deger": deger, "karar": karar, "sonuc": sonuc}
                        try:
                            requests.post(GOOGLE_URL, data=payload, timeout=10)
                            st.success(f"✅ {ad} kaydedildi!")
                        except:
                            st.error("❌ Google Tabloya gönderilemedi!")
                        st.rerun()

        with col2:
            st.subheader("⚙️ Düzenle / Sil")
            with st.expander("🔄 Durum Güncelle"):
                g_id = st.number_input("Güncellenecek ID", min_value=1, step=1)
                yeni_s = st.selectbox("Yeni Durum", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                if st.button("Durumu Güncelle"):
                    conn = db_baglan()
                    cur = conn.cursor()
                    cur.execute("SELECT ad_soyad, yas_sinif, veli_adi, tel, adres, degerlendirme, karar FROM kayitlar WHERE id=?", (g_id,))
                    o = cur.fetchone()
                    if o:
                        conn.execute("UPDATE kayitlar SET sonuc=? WHERE id=?", (yeni_s, g_id))
                        conn.commit()
                        conn.close()
                        payload = {"form_tipi": "kayit", "tarih": str(datetime.now().date()) + " (GÜNCEL)", "ad": o[0], "yas": o[1], "veli": o[2], "tel": o[3], "adres": o[4], "deger": o[5], "karar": o[6], "sonuc": yeni_s}
                        requests.post(GOOGLE_URL, data=payload)
                        st.success("Durum güncellendi!")
                        st.rerun()
                    else:
                        st.error("❌ ID bulunamadı!")

            with st.expander("🗑️ Kayıt Sil"):
                sil_id = st.number_input("Silinecek ID", min_value=1, step=1)
                if st.button("🔴 SİL"):
                    conn = db_baglan()
                    conn.execute("DELETE FROM kayitlar WHERE id=?", (sil_id,))
                    conn.commit()
                    conn.close()
                    st.error("Kayıt silindi!")
                    st.rerun()

    # --- TAB 2: LİSTE ---
    with tab2:
        conn = db_baglan()
        df = pd.read_sql_query("SELECT * FROM kayitlar", conn)
        conn.close()
        if not df.empty:
            st.dataframe(df.style.applymap(renk_ata, subset=['sonuc']), use_container_width=True)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Excel İndir", buffer.getvalue(), "Rehab_Liste.xlsx")
        else:
            st.info("Henüz kayıt yok.")

    # --- TAB 3: MHRS BİLGİLERİ ---
    with tab3:
        st.subheader("🏥 MHRS Kayıt Sistemi")
        m_col1, m_col2 = st.columns([1, 2])
        with m_col1:
            with st.form("mhrs_form", clear_on_submit=True):
                m_ad = st.text_input("Öğrenci Ad Soyad")
                m_tc = st.text_input("TC No")
                m_sifre = st.text_input("MHRS Şifre")
                m_anne = st.text_input("Anne Adı")
                m_baba = st.text_input("Baba Adı")
                if st.form_submit_button("MHRS Kaydet"):
                    if m_ad and m_tc:
                        conn = db_baglan()
                        conn.execute("INSERT INTO mhrs_bilgileri (ad_soyad, tc_no, sifre, anne_adi, baba_adi) VALUES (?,?,?,?,?)", (m_ad, m_tc, m_sifre, m_anne, m_baba))
                        conn.commit()
                        conn.close()
                        payload_mhrs = {"form_tipi": "mhrs", "ad": m_ad, "tc": m_tc, "sifre": m_sifre, "anne": m_anne, "baba": m_baba}
                        try:
                            requests.post(GOOGLE_URL, data=payload_mhrs)
                            st.success("✅ MHRS bilgileri tabloya işlendi!")
                        except:
                            st.error("❌ Tabloya gönderilemedi!")
                        st.rerun()

        with m_col2:
            conn = db_baglan()
            mhrs_df = pd.read_sql_query("SELECT * FROM mhrs_bilgileri", conn)
            conn.close()
            if not mhrs_df.empty:
                st.dataframe(mhrs_df, use_container_width=True)
                sil_m_id = st.number_input("Silinecek MHRS ID", min_value=1, step=1, key="m_sil")
                if st.button("Seçili MHRS Kaydını Sil"):
                    conn = db_baglan()
                    conn.execute("DELETE FROM mhrs_bilgileri WHERE id=?", (sil_m_id,))
                    conn.commit()
                    conn.close()
                    st.rerun()
