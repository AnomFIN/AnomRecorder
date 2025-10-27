# AnomRecorder

Valvontakamerajärjestelmä USB-kameroille Windows-käyttöjärjestelmässä. Offline-ratkaisu ilman pilviliityntää.

## Ominaisuudet

### 📹 Kameratuki
- 1-2 USB-kameran samanaikainen näkymä
- Säädettävä resoluutio ja kuvanopeus (FPS)
- Reaaliaikainen videokuva käyttöliittymässä

### 🔍 Tunnistus
- **Liikkeentunnistus**: Automaattinen liikkeen havaitseminen säädettävällä herkkyydellä
- **Henkilötunnistus**: HOG-SVM -pohjainen ihmisten tunnistus videokuvasta
- Tunnistusten visuaalinen merkintä videokuvaan

### 💾 Tallennus
- Automaattinen tapahtumatallennus liikkeen/henkilön havainnoinnin yhteydessä
- Säädettävä tallennuksen kesto
- Aikaleimaus tallenteisiin
- Automaattinen tallennusrajan hallinta (vanhat tallenteet poistetaan automaattisesti)

### 🎬 Toisto
- Sisäänrakennettu toistonäkymä tallenteille
- Tallennettujen tapahtumien selaus
- Toisto-ohjaimet (toista, pysäytä, tauko)

### 📸 Kuvakaappaukset
- Nopeasti kuvakaappaukset kaikista kameroista
- Tallentuu aikaleimalla erilliseen hakemistoon

### 🎨 Logo-overlay
- Valinnainen logon näyttö videokuvassa
- Säädettävä sijainti (kulmat)
- Säädettävä koko

### ⚙️ Asetukset
- Graafinen asetusvalikko
- Kameran asetukset (indeksit, resoluutio, FPS)
- Tunnistusasetukset (kynnysarvot, herkkyys)
- Tallennusasetukset (kesto, maksimikoko, sijainti)
- Logo-asetukset

## Järjestelmävaatimukset

- **Käyttöjärjestelmä**: Windows 10 tai uudempi
- **Python**: 3.8 tai uudempi (kehitykseen)
- **Laitteisto**:
  - USB-kamerat (1-2 kpl)
  - Vähintään 4 GB RAM
  - Riittävästi levytilaa tallenteille

## Asennus

### Vaihe 1: Asenna riippuvuudet

Suorita `install_dependencies.bat`:
```batch
install_dependencies.bat
```

Tämä asentaa kaikki tarvittavat Python-paketit:
- opencv-python (kameran käsittely ja kuvanmuokkaus)
- numpy (numeerinen laskenta)
- Pillow (kuvankäsittely GUI:ssa)

### Vaihe 2: Suorita ohjelma

Kehitystila (Python-skriptinä):
```batch
python usb_cam_viewer.py
```

## Itsenäisen .exe-tiedoston luonti

### PyInstaller-käännös

1. Yksinkertainen käännös ilman ikonia:
```batch
build_simple.bat
```

2. Käännös logolla (vaatii logo.ico-tiedoston):
```batch
build.bat
```

Valmis ohjelma löytyy hakemistosta `dist\AnomRecorder.exe`

### Siivous

Poista käännöksen väliaikaistiedostot:
```batch
clean.bat
```

## Käyttö

### Ensimmäinen käynnistys

1. Käynnistä sovellus
2. Kameran(oiden) pitäisi käynnistyä automaattisesti
3. Jos kameraa ei löydy, tarkista kameroiden indeksit asetuksista

### Pääikkuna

**Ohjainpainikkeet:**
- **Start**: Käynnistä kameravirta
- **Stop**: Pysäytä kameravirta
- **Screenshot**: Ota kuvakaappaus kaikista kameroista
- **Playback**: Avaa toistonäkymä
- **Settings**: Avaa asetusten muokkaus

**Videokuva:**
- Näyttää reaaliaikaisen kuvan kameroista
- Liike merkitty vihreällä kehyksellä
- Henkilöt merkitty punaisella kehyksellä
- Tila näkyy vasemmassa yläkulmassa (MOTION, PERSON, REC)
- Aikaleima näkyy vasemmassa alakulmassa

### Tallennus

Tallennus käynnistyy automaattisesti kun:
- Liikettä havaitaan TAI
- Henkilö havaitaan

Tallennus jatkuu määritellyn ajan (oletuksena 10 sekuntia).

Tallenteet tallentuvat hakemistoon `recordings/` nimellä:
```
cam0_20231027_143052.avi
```

### Toistonäkymä

1. Avaa **Playback**
2. Valitse tallenne listasta
3. Paina **Play** aloittaaksesi toiston
4. Käytä **Pause** ja **Stop** toiston hallintaan

### Kuvakaappaukset

1. Paina **Screenshot**
2. Kuvakaappaukset tallentuvat hakemistoon `screenshots/` nimellä:
```
cam0_20231027_143052.jpg
```

### Asetukset

#### Kamera-asetukset
- **Camera Indices**: Kameran laiteindeksit pilkulla erotettuna (esim. "0,1")
- **Resolution**: Resoluutio muodossa LxK (esim. "640x480")
- **FPS**: Kuvataajuus (oletuksena 30)

#### Tunnistusasetukset
- **Enable Motion Detection**: Kytke liikkeentunnistus päälle/pois
- **Enable Person Detection**: Kytke henkilötunnistus päälle/pois
- **Motion Threshold**: Liikkeentunnistuksen herkkyys (0-255)
- **Motion Min Area**: Pienin liikealue pikseleinä

#### Tallennusasetukset
- **Recording Duration**: Tallennuksen kesto sekunteina liikkeenhavainnon jälkeen
- **Max Storage**: Maksimi tallennustila gigatavuina
- **Recordings Path**: Tallenteiden sijainti

#### Logo-asetukset
- **Logo Path**: Polku logotiedostoon (PNG, JPG, BMP)
- **Logo Position**: Logon sijainti (kulmat)
- **Logo Scale**: Logon suhteellinen koko (0.0-1.0)

## Konfiguraatiotiedosto

Asetukset tallentuvat automaattisesti tiedostoon `config.json`. 

Esimerkki:
```json
{
    "camera_indices": [0],
    "resolution": [640, 480],
    "fps": 30,
    "motion_detection": true,
    "person_detection": true,
    "motion_threshold": 25,
    "motion_min_area": 500,
    "recording_duration": 10,
    "max_storage_gb": 10,
    "recordings_path": "recordings",
    "screenshots_path": "screenshots",
    "logo_path": "",
    "logo_position": "top-right",
    "logo_scale": 0.15
}
```

## Tallennusrajan hallinta

Ohjelma tarkistaa automaattisesti tallennustilan:
- Jos tallennustila ylittää määritellyn maksimin, vanhat tallenteet poistetaan automaattisesti
- Poistetaan vanhimmat tallenteet ensiksi
- Jätetään 10% puskuri maksimirajan alle

## Tietoturva ja yksityisyys

- **Offline-toiminta**: Ei yhteyksiä internetiin tai pilveen
- **Paikalliset tallenteet**: Kaikki data tallennetaan paikallisesti
- **Ei analytiikkaa**: Ei käyttäjädatan keräystä
- **Avoimen lähdekoodin**: Täysin läpinäkyvä toiminta

## Ongelmanratkaisu

### Kameraa ei löydy
- Tarkista että kamera on kytketty USB-porttiin
- Varmista että kamera toimii (testaa Windows Kamera-sovelluksella)
- Kokeile eri kameraindeksejä asetuksista (0, 1, 2, jne.)
- Käynnistä ohjelma uudelleen

### Henkilötunnistus ei toimi
- Henkilötunnistus vaatii riittävän suuren resoluution
- Henkilön tulee olla selkeästi näkyvissä kuvassa
- Tunnistus toimii parhaiten kun henkilö on pystyasennossa
- HOG-SVM on optimoitu päivänvalolle

### Tallennus ei käynnisty
- Tarkista että liikkeentunnistus tai henkilötunnistus on päällä
- Säädä liikkeentunnistuksen herkkyyttä (motion_threshold)
- Tarkista että recordings-hakemistoon voi kirjoittaa

### Suorituskykyongelmat
- Alenna resoluutiota
- Alenna FPS-arvoa
- Kytke henkilötunnistus pois päältä (raskas operaatio)
- Käytä vain yhtä kameraa

## Tiedostorakenne

```
AnomRecorder/
├── usb_cam_viewer.py          # Pääohjelma
├── requirements.txt            # Python-riippuvuudet
├── config.json                 # Asetustiedosto (luodaan automaattisesti)
├── build.bat                   # Käännösskripti (logolla)
├── build_simple.bat            # Käännösskripti (ilman logoa)
├── clean.bat                   # Siivousskripti
├── install_dependencies.bat    # Riippuvuuksien asennus
├── README.md                   # Tämä tiedosto
├── recordings/                 # Tallenteet (luodaan automaattisesti)
└── screenshots/                # Kuvakaappaukset (luodaan automaattisesti)
```

## Tekninen toteutus

### Arkkitehtuuri

**Moduulit:**
- `Config`: Konfiguraation hallinta
- `StorageManager`: Tallennustilan hallinta
- `CameraCapture`: Yksittäisen kameran käsittely
- `CameraViewer`: Pääikkunan GUI (Tkinter)
- `PlaybackWindow`: Toiston GUI
- `SettingsWindow`: Asetusten GUI

### Käytetyt teknologiat

- **OpenCV**: Kameran käsittely, kuvanmuokkaus, tunnistus
- **NumPy**: Numeerinen laskenta
- **Tkinter**: Graafinen käyttöliittymä
- **Pillow (PIL)**: Kuvankäsittely GUI:ssa
- **HOG-SVM**: Henkilötunnistus (OpenCV:n sisäänrakennettu)

### Liikkeentunnistus

1. Muunna kuva harmaasävyiksi
2. Suodata Gaussian blur -menetelmällä
3. Laske ero edelliseen kuvaan
4. Kynnysarvoistus ja dilatointi
5. Etsi ääriviivat (contours)
6. Tunnista riittävän suuret alueet

### Henkilötunnistus

- HOG (Histogram of Oriented Gradients)
- SVM (Support Vector Machine) -luokitin
- OpenCV:n esikoulutettu malli
- Optimoitu pystysuorille henkilöille

## Lisenssi

Tämä projekti on vapaasti käytettävissä ja muokattavissa.

## Tekijä

AnomFIN

## Tuki

Jos kohtaat ongelmia, tarkista ensin Ongelmanratkaisu-osio.

## Versiohistoria

### v1.0.0
- Alkuperäinen julkaisu
- 1-2 kameran tuki
- Liike- ja henkilötunnistus
- Automaattinen tapahtumatallennus
- Toisto-ominaisuus
- Kuvakaappaukset
- Logo-overlay
- Tallennusrajan hallinta
- Graafinen käyttöliittymä
