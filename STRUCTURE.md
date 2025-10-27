# AnomRecorder - Projektirakenne

## 📁 Tiedostorakenne

```
AnomRecorder/
│
├── 📄 usb_cam_viewer.py          ⭐ Pääohjelma (1000+ riviä Python-koodia)
│   ├── Config                      - Asetusten hallinta
│   ├── StorageManager              - Tallennustilan hallinta
│   ├── CameraCapture               - Kameran käsittely ja tunnistus
│   ├── CameraViewer                - Pää-GUI (Tkinter)
│   ├── PlaybackWindow              - Toisto-ikkuna
│   └── SettingsWindow              - Asetusikkuna
│
├── 📄 requirements.txt            📦 Python-riippuvuudet
│   ├── opencv-python >= 4.8.1.78   (kamera + tunnistus)
│   ├── numpy >= 1.24.0             (laskelmat)
│   └── Pillow >= 10.2.0            (kuvankäsittely)
│
├── 📄 config.json                 ⚙️ Oletusasetukset
├── 📄 config_example.json         📝 Asetusesimerkit kommenteilla
│
├── 📄 README.md                   📖 Täysi dokumentaatio (suomeksi)
├── 📄 QUICKSTART.md               🚀 Pikaopas (englanniksi)
│
├── 🔧 Windows Skriptit (.bat)
│   ├── install_dependencies.bat   📥 Asenna riippuvuudet
│   ├── run.bat                    ▶️  Suorita ohjelma
│   ├── build.bat                  🔨 Luo .exe (logolla)
│   ├── build_simple.bat           🔨 Luo .exe (ilman logoa)
│   └── clean.bat                  🧹 Siivoa rakennustiedostot
│
├── 📄 test_anomrecorder.py        🧪 Testiskripti
├── 📄 .gitignore                  🚫 Git-ohitukset
│
└── 📁 Automaattisesti luodut:
    ├── recordings/                 📹 Videotallenteet
    ├── screenshots/                📸 Kuvakaappaukset
    └── dist/                       💿 Käännetty .exe (build jälkeen)
```

## 🎯 Keskeiset ominaisuudet

### 📹 Kamerajärjestelmä
```
[USB Kamera 1] ──┐
                 ├──> [usb_cam_viewer.py] ──> [GUI Näyttö]
[USB Kamera 2] ──┘           │
                             ├──> [Liikkeentunnistus]
                             ├──> [Henkilötunnistus HOG-SVM]
                             ├──> [Tallennus]
                             └──> [Kuvakaappaus]
```

### 🔍 Tunnistusjärjestelmä
```
Video Frame
    │
    ├─> Liikkeentunnistus
    │   ├─> Harmaasävy-muunnos
    │   ├─> Gaussian blur
    │   ├─> Frame differencing
    │   └─> Contour detection
    │
    └─> Henkilötunnistus
        ├─> HOG (Histogram of Oriented Gradients)
        ├─> SVM (Support Vector Machine)
        └─> Bounding box piirto
```

### 💾 Tallennusjärjestelmä
```
Tunnistus havaittu
    │
    ├─> Käynnistä tallennus (10 sek oletuksena)
    │   ├─> Luo tiedosto: cam0_YYYYMMDD_HHMMSS.avi
    │   ├─> Tallenna framet XVID-kodekilla
    │   └─> Lisää aikaleima ja tila-indikaattorit
    │
    └─> Tarkista tallennustila
        ├─> Jos ylittää maksimin (10 GB)
        └─> Poista vanhimmat tallenteet
```

### 🎨 GUI-rakenne
```
┌─────────────────────────────────────────────────┐
│ [Start] [Stop] [Screenshot] [Playback] [Settings]│
│                                         Status: ●│
├─────────────────────┬──────────────────────────┤
│                     │                          │
│   Kamera 1          │   Kamera 2               │
│   [MOTION | REC]    │   [PERSON]               │
│   2023-10-27 14:30  │   2023-10-27 14:30       │
│   🏢 [Logo]         │                          │
│                     │                          │
└─────────────────────┴──────────────────────────┘
```

## 🔐 Turvallisuus

### ✅ Tietoturvatarkistukset suoritettu
- ✓ CodeQL skannaus: 0 haavoittuvuutta
- ✓ GitHub Advisory: Kaikki riippuvuudet päivitetty
- ✓ CVE-2023-4863 (libwebp): Korjattu
- ✓ Pillow haavoittuvuudet: Korjattu
- ✓ Koodikatselmointi: Hyväksytty

### 🔒 Yksityisyys
- ❌ Ei internet-yhteyksiä
- ❌ Ei pilvipalveluita
- ❌ Ei analytiikkaa
- ✅ 100% paikallinen toiminta
- ✅ Avoimen lähdekoodin

## 📊 Tekninen spesifikaatio

| Komponentti | Teknologia | Tarkoitus |
|-------------|-----------|-----------|
| GUI | Tkinter | Windows-käyttöliittymä |
| Kamera | OpenCV | Video capture ja käsittely |
| Liikkeentunnistus | OpenCV | Frame differencing + contours |
| Henkilötunnistus | HOG-SVM | Esikoulutettu OpenCV-malli |
| Tallennus | OpenCV VideoWriter | AVI-tiedostot (XVID codec) |
| Kuvankäsittely | NumPy + Pillow | Frame-manipulaatio |
| Konfiguraatio | JSON | Asetustiedostot |
| Paketointi | PyInstaller | Standalone .exe |

## 🚀 Käyttöönotto

### Vaihtoehto A: Python-kehitys
```batch
install_dependencies.bat
run.bat
```

### Vaihtoehto B: Standalone .exe
```batch
build_simple.bat
dist\AnomRecorder.exe
```

## 📈 Suorituskyky

| Asetus | CPU-käyttö | Tarkkuus | Suositus |
|--------|-----------|----------|----------|
| 640x480, 30 FPS, liike + henkilö | Keskitaso | Hyvä | Oletus ✓ |
| 1280x720, 30 FPS, liike + henkilö | Korkea | Erinomainen | Tehokkaat PC:t |
| 640x480, 15 FPS, vain liike | Matala | Hyvä | Vanhemmat PC:t |
| 1920x1080, 60 FPS, liike + henkilö | Erittäin korkea | Erinomainen | Vaatii tehoa |

## 🎓 Koodimäärät

| Tiedosto | Rivit | Kuvaus |
|----------|-------|---------|
| usb_cam_viewer.py | ~1000 | Pääohjelma (kaikki toiminnallisuus) |
| test_anomrecorder.py | ~130 | Testit |
| README.md | ~320 | Dokumentaatio (FI) |
| QUICKSTART.md | ~90 | Pikaopas (EN) |
| **YHTEENSÄ** | **~1540** | **Koodia + dokumentaatio** |

## 🏗️ Arkkitehtuuriperiaatteet

1. **Modulaarisuus**: Jokainen luokka hoitaa yhden asian
2. **Yksinkertaisuus**: Yksi tiedosto, helppo ymmärtää
3. **Offline**: Ei ulkoisia riippuvuuksia
4. **Turvallisuus**: Päivitetyt riippuvuudet, tietoturvatarkistettu
5. **Käytettävyys**: Graafinen käyttöliittymä, helppo asennus
6. **Dokumentointi**: Kattava suomen- ja englanninkielinen

## 📝 Lisätietoja

- Lisensoitu vapaaseen käyttöön
- Avoimen lähdekoodin projekti
- Ei vaadi rekisteröitymistä tai aktivointia
- Toimii täysin ilman internet-yhteyttä
- Tukee Windows 10 ja uudemmat

---
**AnomRecorder** - Suomalainen valvontakamerajärjestelmä 🇫🇮
