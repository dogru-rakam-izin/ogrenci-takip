import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import urllib.parse
import requests

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
    conn.commit()
    return conn

# Renk Fonksiyonu
def renk_ata(val):
    colors = {'Hastane Sürecinde': '#FFA500', 'RAM Sürecinde': '#1E90FF', 
              'İptal': '#FF4B4B', 'Kaydedildi': '#28A745', 'Beklemede': '#6c757d'}
    return f'background-color: {colors.get(val, "white")}; color: white; font-weight: bold; border-radius: 5px;'

# --- ANA PROGRAM ---
st.set_page_config(page_title="Rehabilitasyon Takip Sistemi", layout="wide")

if giris_yap():
    st.sidebar.success("✅ Sisteme Giriş Yapıldı")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state["giris_basarili"] = False
        st.rerun()

    st.title("🏥 Rehabilitasyon Merkezi Yönetim Paneli")
    tab1, tab2 = st.tabs(["➕ Yeni Kayıt & İşlemler", "📋 Liste & Excel"])

    with tab1:
        col1, col2 = st.columns(2)
        
        # --- SOL TARAF: YENİ KAYIT ---
        with col1:
            st.subheader("📝 Yeni Öğrenci Ekle")
            with st.form("yeni_kayit_formu", clear_on_submit=True):
                ad = st.text_input("Ad Soyad")
                yas = st.text_input("Yaş - Sınıf")
                veli = st.text_input("Veli Adı")
                tel = st.text_input("Telefon")
                deger = st.text_area("Değerlendirme")
                karar = st.selectbox("Karar", ["Gelişim Takibi", "Rapor", "Özel", "Beklemede"])
                sonuc = st.selectbox("Sonuç Durumu", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                
                submitted = st.form_submit_button("💾 Kaydet ve Gönder")
                if submitted:
                    if ad:
                        conn = db_baglan()
                        cur = conn.cursor()
                        cur.execute("INSERT INTO kayitlar (ad_soyad, yas_sinif, degerlendirme, karar, sonuc, veli_adi, tel, tarih) VALUES (?,?,?,?,?,?,?,?)",
                                    (ad, yas, deger, karar, sonuc, veli, tel, datetime.now().date()))
                        conn.commit()
                        conn.close()
                        
                        # Google Sheets Entegrasyonu
                        google_url = "https://script.google.com/macros/s/AKfycbz3kGhyk15B_o0qTm-mQoI7GLIgMaLo4Z2ElHM5RwE9ta-1zm_6LL83pied4zrQrx-QBA/exec"
                        payload = {"ad": ad, "yas": yas, "veli": veli, "tel": tel, "deger": deger, "karar": karar, "sonuc": sonuc, "tarih": str(datetime.now().date())}
                        try:
                            requests.post(google_url, data=payload, timeout=10)
                            st.success(f"✅ {ad} başarıyla kaydedildi!")
                        except:
                            st.warning("⚠️ Google Sheets bağlantısı kurulamadı ama sisteme kaydedildi.")
                        
                        m = f"📢 *YENİ KAYIT*\n👤 *Ad:* {ad}\n📍 *Durum:* {sonuc}"
                        st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(m)}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; width:100%; cursor:pointer;">🟢 WhatsApp Bildir</button></a>', unsafe_allow_html=True)

        # --- SAĞ TARAF: GÜNCELLEME VE SİLME ---
        with col2:
            st.subheader("⚙️ Kayıt Düzenleme")
            
            # 🔄 DURUM GÜNCELLEME
            with st.expander("🔄 Durum Güncelle", expanded=True):
                g_id = st.number_input("Güncellenecek ID Girin", min_value=1, step=1, key="upd_id")
                yeni_durum = st.selectbox("Yeni Durum Seçin", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"], key="upd_status")
                if st.button("Güncellemeyi Tamamla"):
                    conn = db_baglan()
                    conn.execute("UPDATE kayitlar SET sonuc = ? WHERE id = ?", (yeni_durum, g_id))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ ID {g_id} güncellendi!")
                    st.rerun()

            st.markdown("---")
            
            # 🗑️ KAYIT SİLME
            with st.expander("🗑️ Kayıt Sil"):
                st.error("Silme işlemi geri alınamaz!")
                sil_id = st.number_input("Silinecek ID Girin", min_value=1, step=1, key="del_id")
                if st.button("🔴 KAYDI KALICI OLARAK SİL"):
                    conn = db_baglan()
                    conn.execute("DELETE FROM kayitlar WHERE id=?", (sil_id,))
                    conn.commit()
                    conn.close()
                    st.error(f"❌ ID {sil_id} silindi!")
                    st.rerun()

    with tab2:
        conn = db_baglan()
        df = pd.read_sql_query("SELECT * FROM kayitlar", conn)
        conn.close()
        if not df.empty:
            st.subheader("📋 Öğrenci Listesi")
            arama = st.text_input("🔍 İsimle Listede Ara")
            if arama:
                df = df[df['ad_soyad'].str.contains(arama, case=False, na=False)]
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Excel İndir", buffer.getvalue(), "Rehab_Liste.xlsx")
            st.dataframe(df.style.applymap(renk_ata, subset=['sonuc']), use_container_width=True)
        else:
            st.info("Henüz kayıtlı veri bulunamadı.")
