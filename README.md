# AnomRecorder

AnomRecorder tuo AnomFINin kyberhenkisen tumman käyttöliittymän USB- ja IP-kameroille. Sovellus on offline-tilassa toimiva valvontaratkaisu, jossa tallennus, katselu ja asetukset löytyvät yhdestä futuristisesta näkymästä.

## Pääominaisuudet
- **Dark mode -teema** anomfin-website -sivuston tyyliin: tumma paletti, minimalistiset aksentit.
- **USB- ja IP-kameratuki**: Liitä USB-kameroita tai WiFi/IP-kameroita (RTSP, HTTP/MJPEG).
- **WiFi-kameratuki**: Tukee Ring, EUFY, Wyze, TP-Link ja muita RTSP-yhteensopivia kameroita.
- **Automaattinen kamerahaku**: Skannaa WiFi-verkko automaattisesti yhteensopivien IP-kameroiden löytämiseksi.
- **Zoom-ohjaimet** kummallekin kameralle (+ / − / reset).
- **Jatkuva tallennus**: tallennus ei keskeydy vaikka selaat tallenteita.
- **Playback-kontrollit**: play, pause, stop sekä 0.5x / 1x / 2x -nopeudet.
- Liike- ja henkilötunnistus OpenCV:n avulla, aikaleimat ja logon overlay.
- Tallennusrajojen hallinta, levytilan valvonta, merkintöjen lisäys ja kuvakaappaukset.

## Kansiostruktuuri
```
src/
  core/          # Puhtaat apufunktiot (esim. humanize, detection)
  services/      # IO-rajapinnat (kamerat, tallennus)
  ui/            # Tkinter-käyttöliittymä ja teemat
  utils/         # Pienet uudelleenkäytettävät apurit
usb_cam_viewer.py  # Legacy-entry, delegoi src.index.mainille
tests/             # Pytest-yksikkötestit
```

## Asennus ja ajaminen

### 🚀 Automaattinen asennus (suositeltu)

#### Windows (Bulletproof Installer)
AnomRecorder sisältää täysin automaattisen Windows-asennusohjelman:

```batch
install.bat
```

Tai PowerShell:
```powershell
.\install.ps1
```

**Ominaisuudet:**
- ✅ 100% automaattinen - ei manuaalisia vaiheita
- ✅ Ei kaadu koskaan - kattava virheidenkäsittely
- ✅ Luo ja käyttää virtuaaliympäristöä (.venv)
- ✅ Automaattinen riippuvuuksien asennus
- ✅ Yrityslogiikka ohimeneviin virheisiin
- ✅ Ammattimaiset virheviestit (ei raakoja stack traceja)
- ✅ Kattava lokitus tiedostoon (installer.log)
- ✅ Valinnainen automaattinen käynnistys

📖 **Katso yksityiskohtaiset ohjeet:** [WINDOWS_INSTALLER.md](WINDOWS_INSTALLER.md)

**Linux/Mac/CLI:**
```bash
python install.py
```

> GUI käynnistää asennuksen automaattisesti heti kun järjestelmätarkistus valmistuu – erillistä "Start"-painallusta ei tarvita.

Asennusohjelma:
- ✓ Tarkistaa Python-version
- ✓ Asentaa kaikki riippuvuudet
- ✓ Testaa asennuksen
- ✓ Havaitsee ja korjaa virheet automaattisesti
- ✓ Varmistaa että sovellus toimii

### Manuaalinen asennus
Jos haluat asentaa manuaalisesti (esim. virtuaaliympäristössä):
```bash
python -m pip install -r requirements.txt
python -m pip install pytest
```

### Virtuaaliympäristöautomaatti (`venvi.py`)
Kaikki komennot voi ajaa yhdellä tiedostolla, joka luo `.venv`-hakemiston, asentaa riippuvuudet, ajaa testit ja tarvittaessa käynnistää Node-palvelun (jos `package.json` löytyy):

**PowerShell / CMD:**
```powershell
# Luo .venv, asentaa riippuvuudet, ajaa testit ja käynnistää sovelluksen
python .\venvi.py run

# Sama ilman testejä (nopeampi dev-sykli)
python .\venvi.py run --skip-tests

# Pelkkä ympäristön valmistelu ilman käynnistystä
python .\venvi.py setup

# Testien ajo omilla pytest-parametreilla
python .\venvi.py test --pytest-args -q

# Node-palvelu mukaan, jos package.json löytyy
python .\venvi.py run --with-npm
```

**Linux/macOS:**
```bash
# Luo .venv, asentaa riippuvuudet, ajaa testit ja käynnistää sovelluksen
python venvi.py run

# Sama ilman testejä (nopeampi dev-sykli)
python venvi.py run --skip-tests

# Pelkkä ympäristön valmistelu ilman käynnistystä
python venvi.py setup

# Testien ajo omilla pytest-parametreilla
python venvi.py test --pytest-args -q

# Node-palvelu mukaan, jos package.json löytyy
python venvi.py run --with-npm
```

### Sovelluksen käynnistäminen
```bash
python usb_cam_viewer.py
```
tai
```bash
python -m src.index
```

## Testit
```bash
pytest
```

## Verifiointiohje
1. Käynnistä sovellus (`python -m src.index`).
2. Valitse USB-kamera ja tarkista, että live-näkymä avautuu tummalla teemalla.
3. Säädä zoomia ±-painikkeilla – kuvavirta rajautuu keskitetysti.
4. Mene Tallenteet-välilehdelle ja paina *Play*; videon pitäisi toistua ja live-näkymä jatkaa tallennusta.
5. Vaihda nopeutta 0.5x → 2x ja varmista päivittyvä tila-indikaattori.
6. Lisää merkintä tallenteeseen ja tarkista, että se näkyy listassa.

## Miksi tämä arkkitehtuuri
- **Functional core, imperative shell**: puhtaat apurit (humanize, zoom) eriytetty UI:sta → helppo testata.
- **Turvallinen oletus**: tallennusrajoitukset, virheiden lokitus ja välitön resurssien vapautus.
- **DX-ystävällinen**: selkeä pakettirakenne, `main()`-entry ja pytestit pikaraportointiin.

## Runbook & vianetsintä
- `recordings/`-hakemisto luodaan automaattisesti käynnistyksessä.
- Jos USB-kamera ei löydy, paina **Päivitä** ja tarkista että laite näkyy Windowsin Laitehallinnassa.
- **IP-kameran lisäys**: Klikkaa **+ IP-kamera** ja seuraa ohjeita. Katso yksityiskohtaiset ohjeet tiedostosta [README_IP_CAMERA.md](README_IP_CAMERA.md).
- Tallenteiden toisto käyttää OpenCV:tä; jos playback ei käynnisty, varmista että `opencv-video`-koodekki on saatavilla.
- Lokit tulostuvat konsoliin (INFO-taso). PyInstaller-versiossa lokit ohjautuvat järjestelmän logiin.

## Tunnetut rajoitteet
- Testit kattavat vain puhtaat apurit; OpenCV/Tkinter -rajapintojen instrumentointi vaatii laiteympäristön.
- Playback-ikkuna ei tue scrubbausta tai ääntä (vain video + nopeus).
- Linuxissa kameranhakeminen käyttää DirectShow-lippua; tarvittaessa päivitä `cv2.VideoCapture` -parametrit.
- IP-kameroiden automaattinen skannaus voi kestää useita minuutteja verkosta riippuen.

## Seuraavat iteroinnit
- Lisää scrubber ja frame-by-frame -ohjaimet tallenteiden katseluun.
- Toteuta automaattinen terveysraportointi (levytila, kamera offline) esim. sähköposti-ilmoituksin.
