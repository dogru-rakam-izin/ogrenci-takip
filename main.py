import streamlit as st

st.title("Rehabilitasyon Merkezi Test")
st.write("Eğer bu yazıyı görüyorsan program çalışıyor!")

# Görseldeki sütunları buraya ekleyelim
ad_soyad = st.text_input("Öğrenci Adı Soyadı")
if st.button("Kaydet"):
    st.success(f"{ad_soyad} için kayıt denemesi başarılı!")
