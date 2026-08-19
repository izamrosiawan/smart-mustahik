# SMART-MUSTAHIK: Sistem Pendukung Keputusan Penyaluran Zakat Presisi Berbasis Machine Learning

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine%20Learning-orange.svg)](https://scikit-learn.org/)
[![Domain](https://img.shields.io/badge/Domain-Islamic%20Philanthropy%20Analytics-green.svg)](#)
[![Tests](https://img.shields.io/badge/Tests-Pytest%20Passing-brightgreen.svg)](#)

Sistem Pendukung Keputusan Penyaluran Zakat Presisi Menggunakan Analisis Machine Learning Berbasis QS. At-Taubah: 60 dan Had Kifayah.

Karya Tulis Ilmiah Qur'an (KTIQ) SERI-FEST 2026 - IPB University  
**Penulis:** Izam Rosiawan & Clairine Anargya Athallah  
**Instansi:** Telkom University Surabaya  

---

## 1. Pembahasan Bisnis & Konteks Filantropi Islam

Penyaluran zakat menghadapi tantangan ketimpangan alokasi (*spatial targeting inefficiency*), di mana lembaga amil zakat rentan mengalami dua jenis kesalahan sasaran:
1. **Inclusion Error**: Bantuan tersalurkan ke wilayah atau individu yang sebenarnya mampu secara finansial.
2. **Exclusion Error**: Fakir miskin yang berhak menerima zakat terlewatkan dari distribusi bantuan.

SMART-MUSTAHIK memodelkan data sosio-ekonomi BPS Provinsi Jawa Timur (2020-2024, 38 Kabupaten/Kota, 190 observasi) menggunakan *Random Forest Classifier* untuk membantu lembaga amil zakat menentukan prioritas wilayah penerima manfaat secara objektif dan transparan.

---

## 2. Struktur Repositori

```
├── .gitignore          # Konfigurasi pengabaian cache Git
├── data/
│   ├── dataset_jatim_2020_2024.csv  # Dataset sosio-ekonomi BPS Jatim (190 observasi)
│   └── evaluasi_performa.csv        # Tabel metrik hasil pengujian
├── images/             # Visualisasi plot hasil render (300 DPI)
│   ├── grafik_hasil_smart_mustahik.png
│   ├── feature_importance.png
│   ├── distribusi_mustahik.png
│   └── confusion_matrix.png
├── src/                # Modular Python classifier engine (SmartMustahikClassifier)
├── tests/              # Automated unit tests (Pytest)
├── notebook.ipynb      # Mesin pemrosesan: Zero-leakage modeling & evaluasi
├── requirements.txt    # Pinned stable dependencies
└── README.md           # Laporan utama: Konteks fiqih, rumus, tabel metrik, dan rekomendasi
```

---

## 3. Metodologi Analisis & Formulasi Kuantitatif

Sistem menggunakan 6 fitur prediktor sosio-ekonomi tanpa kebocoran target (*zero target reconstruction leakage*): `hdi` (IPM), `sanitation_access_percent`, `drinking_water_access_percent`, `school_participation_rate`, `unemployment_rate`, dan `population_density`.

### Formulasi Metrik Error Penyaluran:
* **Inclusion Error Rate (IER)**:
  $$\text{IER} = \frac{\text{False Positive}}{\text{Total Prediksi Prioritas}}$$
* **Exclusion Error Rate (EER)**:
  $$\text{EER} = \frac{\text{False Negative}}{\text{Total Fakir Miskin Aktual}}$$

---

## 4. Hasil Kuantitatif & Pembahasan Visualisasi

Pengujian dilakukan menggunakan *Stratified Split* 75:25 (48 sampel uji) membandingkan SMART-MUSTAHIK dengan Pendekatan Konvensional Berbasis Verifikasi Lapangan (Baseline Simulasi Random Label Noise 16,67%):

![Hasil Performa & Error Penyaluran](images/grafik_hasil_smart_mustahik.png)
![Feature Importance](images/feature_importance.png)

### Tabel Perbandingan Metrik Evaluasi:

| Metrik Evaluasi | Baseline Simulasi Noise (16,67%) | SMART-MUSTAHIK | Selisih | Dampak Operasional |
| :--- | :---: | :---: | :---: | :--- |
| **Akurasi** | 83,33% | **87,50%** | +4,17 pp | Peningkatan ketepatan klasifikasi menyeluruh |
| **Precision** | 64,71% | **73,33%** | +8,62 pp | Mengurangi salah sasaran ke non-mustahik |
| **Recall** | 84,62% | **84,62%** | 0,00 pp | Menjaga perlindungan jaring pengaman sosial |
| **F1-Score** | 73,33% | **78,57%** | +5,24 pp | Keseimbangan presisi dan cakupan penerima |
| **Inclusion Error Rate** | 17,14% | **11,43%** | -5,71 pp | **Efisiensi Dana Zakat Meningkat 5,71%** |
| **Exclusion Error Rate** | 15,38% | **15,38%** | 0,00 pp | Tingkat mustahik terlewat tetap terkendali |

---

## 5. Implementasi Modular & Pengujian Otomatis

Modul klasifikasi mustahik tersedia di `src/mustahik_engine.py`:

```python
from src.mustahik_engine import SmartMustahikClassifier
import pandas as pd

engine = SmartMustahikClassifier()
# Pelatihan dan inferensi prioritas mustahik
```

Jalankan automated test:
```bash
pytest tests/
```

---

## 6. Rekomendasi Pengelolaan Zakat Nasional

1. **Alokasi Dana Zakat Berbasis Indeks Komposit**: Lembaga Amil Zakat Nasional (BAZNAS) dan LAZ disarankan mengintegrasikan indikator sanitasi dan air bersih sebagai pembobot prioritas selain garis kemiskinan moneter.
2. **Triase Penyaluran Dua Jalur**:
   * *Wilayah Prioritas Utama*: Penyaluran program zakat produktif (pemberdayaan ekonomi UMKM).
   * *Wilayah Prioritas Transisi*: Penyaluran program zakat konsumtif darurat (bantuan pangan dan kesehatan).

---

## 7. Cara Menjalankan

1. **Pasang Dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Eksekusi Notebook**:
   ```bash
   jupyter notebook notebook.ipynb
   ```

---
*Karya Tulis Ilmiah Qur'an (KTIQ) SMART-MUSTAHIK - Telkom University Surabaya.*