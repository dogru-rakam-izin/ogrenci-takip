import sqlite3
from datetime import datetime

class RehabOtomasyon:
    def __init__(self):
        self.conn = sqlite3.connect('rehabilitasyon.db')
        self.cursor = self.conn.cursor()
        self.tablo_olustur()

    def tablo_olustur(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ogrenciler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_soyad TEXT,
                yas_sinif TEXT,
                degerlendirme TEXT,
                karar TEXT,
                sonuc TEXT,
                veli_ad_soyad TEXT,
                telefon TEXT,
                adres TEXT,
                kayit_tarihi TEXT
            )
        ''')
        self.conn.commit()

    def ogrenci_ekle(self):
        print("\n--- Yeni Öğrenci Kaydı ---")
        ad = input("Ad Soyad: ")
        yas_sinif = input("Yaş - Sınıf: ")
        degerlendirme = input("Değerlendirme: ")
        karar = input("Karar: ")
        sonuc = input("Sonuç: ")
        veli = input("Veli Ad Soyad: ")
        tel = input("Telefon: ")
        adres = input("Adres: ")
        tarih = datetime.now().strftime("%d-%m-%Y %H:%M")

        self.cursor.execute('''
            INSERT INTO ogrenciler (ad_soyad, yas_sinif, degerlendirme, karar, sonuc, veli_ad_soyad, telefon, adres, kayit_tarihi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ad, yas_sinif, degerlendirme, karar, sonuc, veli, tel, adres, tarih))
        self.conn.commit()
        print(f"\n✅ {ad} başarıyla kaydedildi.")

    def listele(self):
        self.cursor.execute("SELECT * FROM ogrenciler")
        veriler = self.cursor.fetchall()
        print(f"\n{'ID':<3} | {'Ad Soyad':<20} | {'Yaş/Sınıf':<10} | {'Veli':<15} | {'Sonuç':<10}")
        print("-" * 70)
        for satir in veriler:
            print(f"{satir[0]:<3} | {satir[1]:<20} | {satir[2]:<10} | {satir[6]:<15} | {satir[5]:<10}")

def menu():
    sistem = RehabOtomasyon()
    while True:
        print("\n--- REHABİLİTASYON MERKEZİ TAKİP SİSTEMİ ---")
        print("1. Yeni Öğrenci Ekle")
        print("2. Tüm Öğrencileri Listele")
        print("3. Çıkış")
        
        secim = input("Seçiminiz: ")
        
        if secim == '1':
            sistem.ogrenci_ekle()
        elif secim == '2':
            sistem.listele()
        elif secim == '3':
            print("Sistemden çıkılıyor...")
            break
        else:
            print("Geçersiz seçim!")

if __name__ == "__main__":
    menu()
