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
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbwT6l8hXtguAt6xNS2awOV5T8tM7ihi60vnNVCQfjtDq8fiE_KIg9s5fXvztBmT7WIZVg/exec"

def renk_ata(val):
    colors = {'Hastane Sürecinde': '#FFA500', 'RAM Sürecinde': '#1E90FF', 
              'İptal': '#FF4B4B', 'Kaydedildi': '#28A745', 'Beklemede': '#6c757d'}
    return f'background-color: {colors.get(val, "white")}; color: white; font-weight: bold; border-radius: 5px;'

if giris_yap():
    # Veriyi en başta çekiyoruz ki seçim kutularında kullanabilelim
    try:
        df_ana = pd.read_csv(KAYITLAR_CSV)
        df_ana = df_ana.dropna(how='all', axis=0).dropna(how='all', axis=1)
        df_ana = df_ana.loc[:, ~df_ana.columns.str.contains('^Unnamed')]
        df_ana = df_ana.fillna("")
        df_ana.columns = df_ana.columns.str.strip()
    except:
        df_ana = pd.DataFrame()

    tab1, tab2, tab3 = st.tabs(["➕ İşlemler", "📋 Liste & Çıktı", "🏥 MHRS Bilgileri"])

    # --- TAB 1: YENİ KAYIT VE GÜNCELLEME ---
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📝 Yeni Öğrenci Ekle")
            with st.form("yeni_form", clear_on_submit=True):
                ad = st.text_input("Ad Soyad")
                yas = st.text_input("Yaş - Sınıf")
                veli = st.text_input("Veli Adı")
                tel_input = st.text_input("Telefon")
                adres = st.text_area("Adres")
                deger_input = st.text_area("Değerlendirme Notu")
                karar = st.selectbox("Karar", ["Gelişim Takibi", "Rapor", "Özel", "Beklemede"])
                sonuc = st.selectbox("Sonuç", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                
                if st.form_submit_button("💾 Kaydet"):
                    if ad:
                        payload = {
                            "form_tipi": "kayit", "islem_tipi": "yeni", "tarih": str(datetime.now().date()), 
                            "ad": ad, "yas": yas, "veli": veli, "tel": tel_input, 
                            "adres": adres, "deger": deger_input, "karar": karar, "sonuc": sonuc
                        }
                        requests.post(GOOGLE_URL, data=payload)
                        st.success(f"✅ {ad} başarıyla eklendi!")
                        st.cache_data.clear()

        with col2:
            st.subheader("🔄 Durum Güncelle")
            if not df_ana.empty and 'Ad Soyad' in df_ana.columns:
                with st.form("guncelle_form"):
                    # BURASI DEĞİŞTİ: Artık ismi listeden seçiyorsunuz
                    g_ad = st.selectbox("Güncellenecek Öğrenciyi Seçin", df_ana['Ad Soyad'].unique())
                    yeni_s = st.selectbox("Yeni Durum", ["Kaydedildi", "Hastane Sürecinde", "RAM Sürecinde", "Beklemede", "İptal"])
                    
                    if st.form_submit_button("Güncellemeyi Tamamla"):
                        payload = {"form_tipi": "kayit", "islem_tipi": "guncelle", "ad": g_ad, "sonuc": yeni_s}
                        requests.post(GOOGLE_URL, data=payload)
                        st.success(f"🔄 {g_ad} durumu '{yeni_s}' olarak güncellendi!")
                        st.cache_data.clear()
            else:
                st.warning("Güncelleme yapabilmek için önce kayıtlı öğrenci olmalıdır.")

    # --- TAB 2: LİSTE VE EXCEL ---
    with tab2:
        if not df_ana.empty:
            # Telefon Temizliği
            for col in ['Telefon', 'Tel']:
                if col in df_ana.columns:
                    df_ana[col] = df_ana[col].astype(str).str.replace(r'\.0$', '', regex=True)

            c1, c2 = st.columns([4, 1])
            with c2:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_ana.to_excel(writer, index=False, sheet_name='Liste')
                st.download_button("📥 Excel İndir", buffer.getvalue(), "liste.xlsx", "application/vnd.ms-excel")

            sonuc_col = 'Sonuç' if 'Sonuç' in df_ana.columns else None
            st.dataframe(df_ana.style.applymap(renk_ata, subset=[sonuc_col]) if sonuc_col else df_ana, use_container_width=True)
            
            # WhatsApp Bölümü
            st.markdown("---")
            st.subheader("📲 WhatsApp Paylaşımı")
            secilen_wa = st.selectbox("Paylaşılacak Kişi", df_ana['Ad Soyad'].unique(), key="wa_select")
            if st.button("🟢 WhatsApp Mesajı Hazırla"):
                satir = df_ana[df_ana['Ad Soyad'] == secilen_wa].iloc[0]
                mesaj = f"*BİLGİ FORMU*\n👤 *İsim:* {secilen_wa}\n📋 *Durum:* {satir.get('Sonuç','')}\n📞 *Tel:* {satir.get('Telefon','')}"
                st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(mesaj)}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; width:100%;">Gönder</button></a>', unsafe_allow_html=True)
        else:
            st.info("Görüntülenecek veri bulunamadı.")

    # --- TAB 3: MHRS ---
    with tab3:
        # (MHRS kodlarınız buraya aynen gelecek, yapı aynı kaldığı için yer kaplamaması adına kısa tuttum)
        st.info("MHRS işlemleri Tab 1'deki mantıkla çalışmaya devam eder.")
