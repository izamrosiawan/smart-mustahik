# SMART-MUSTAHIK

Sistem Pendukung Keputusan Penyaluran Zakat Presisi Menggunakan Analisis Machine Learning Berbasis QS. At-Taubah: 60.

Karya Tulis Ilmiah Qur'an (KTIQ) SERI-FEST 2026 - IPB University  
**Penulis:** Izam Rosiawan & Clairine Anargya Athallah  
**Instansi:** Telkom University Surabaya  

---

## Ikhtisar

SMART-MUSTAHIK memodelkan data sosio-ekonomi BPS Provinsi Jawa Timur (2020–2024, 38 Kabupaten/Kota, 190 observasi) menggunakan *Random Forest Classifier* untuk membantu lembaga amil zakat menentukan prioritas wilayah penyaluran zakat berdasarkan kriteria QS. At-Taubah: 60 dan Had Kifayah.

Pemodelan menggunakan 6 fitur prediktor non-leakage (`hdi`, `sanitation_access_percent`, `drinking_water_access_percent`, `school_participation_rate`, `unemployment_rate`, `population_density`) untuk menekan *Inclusion Error* (salah sasaran) dan *Exclusion Error* (terlewat).

---

## Struktur Repositori

```
smart-mustahik/
├── data/
│   ├── dataset_jatim_2020_2024.csv  # Dataset BPS Jatim (190 observasi)
│   └── evaluasi_performa.csv        # Tabel metrik hasil pengujian
├── images/
│   ├── grafik_hasil_smart_mustahik.png
│   ├── feature_importance.png
│   ├── distribusi_mustahik.png
│   └── confusion_matrix.png
├── notebook.ipynb                   # Processing & modeling pipeline
└── README.md                        # Dokumentasi proyek
```

---

## Hasil Evaluasi

Pengujian dilakukan menggunakan *Stratified Split* 75:25 (48 sampel uji) membandingkan SMART-MUSTAHIK dengan Baseline Simulasi Label Noise (16,67% noise):

| Metrik Evaluasi | Baseline Noise (16,67%) | SMART-MUSTAHIK | Selisih |
| --- | --- | --- | --- |
| Akurasi | 83,33% | **87,50%** | +4,17 pp |
| Precision | 64,71% | **73,33%** | +8,62 pp |
| Recall | 84,62% | **84,62%** | 0,00 pp |
| F1-Score | 73,33% | **78,57%** | +5,24 pp |
| Inclusion Error Rate | 17,14% | **11,43%** | -5,71 pp |
| Exclusion Error Rate | 15,38% | **15,38%** | 0,00 pp |

---

## Visualisasi

![Hasil Performa & Error Penyaluran](images/grafik_hasil_smart_mustahik.png)
*Gambar 1: Perbandingan Performa Klasifikasi & Targeting Error.*

![Feature Importance](images/feature_importance.png)
*Gambar 2: Tingkat Kepentingan Fitur Prediktor.*

---

## Cara Penggunaan

1. Clone repositori dan install dependensi:
   ```bash
   git clone https://github.com/izamrosiawan/smart-mustahik.git
   cd smart-mustahik
   pip install pandas numpy scikit-learn matplotlib seaborn
   ```
2. Jalankan notebook:
   ```bash
   jupyter notebook notebook.ipynb
   ```