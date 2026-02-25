# --- TAB 2: LİSTE ---
    with tab2:
        conn = db_baglan()
        df = pd.read_sql_query("SELECT * FROM kayitlar", conn)
        conn.close()
        
        if not df.empty:
            # Tabloyu göster
            st.dataframe(df.style.applymap(renk_ata, subset=['sonuc']), use_container_width=True)
            
            # --- WHATSAPP PAYLAŞIM ALANI ---
            st.subheader("📲 Kayıt Paylaş (WhatsApp)")
            w_col1, w_col2 = st.columns([1, 2])
            
            with w_col1:
                secilen_id = st.number_input("Paylaşılacak Öğrenci ID", min_value=1, step=1)
            
            if secilen_id:
                # Seçilen öğrencinin verilerini çek
                ogrenci = df[df['id'] == secilen_id]
                if not ogrenci.empty:
                    # Mesaj içeriğini hazırla
                    isim = ogrenci['ad_soyad'].values[0]
                    durum = ogrenci['sonuc'].values[0]
                    veli = ogrenci['veli_adi'].values[0]
                    telefon = ogrenci['tel'].values[0]
                    
                    mesaj = f"*Öğrenci Kayıt Bilgisi*\n\n" \
                            f"👤 *İsim:* {isim}\n" \
                            f"📋 *Durum:* {durum}\n" \
                            f"👨‍👩‍👦 *Veli:* {veli}\n" \
                            f"📞 *İletişim:* {telefon}"
                    
                    # WhatsApp Linki Oluştur
                    encoded_msj = urllib.parse.quote(mesaj)
                    wa_link = f"https://wa.me/?text={encoded_msj}"
                    
                    with w_col2:
                        st.write(f"👉 **{isim}** için paylaşım hazır:")
                        st.markdown(f'<a href="{wa_link}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">🟢 WhatsApp ile Gönder</button></a>', unsafe_allow_html=True)

            # Excel İndirme Butonu (Eski yerinde kalsın)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Excel İndir", buffer.getvalue(), "Rehab_Liste.xlsx")
