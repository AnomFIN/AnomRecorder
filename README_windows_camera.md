Kamerajärjestelmä by AnomFIN (.exe) — Offline
==================================

Paikallinen Windows‑sovellus USB‑kameroille. UI:ssa on alasvetovalikot ("Valitse kamera"), näkymä 1 tai 2 kameralle, liikkeen- ja henkilötunnistus (HOG‑SVM), tapahtumatallennus (3 s ennen + koko liike + 5 s jälkeen), Tapahtumat‑välilehti toistolle ja merkinnöille, sekä Asetukset‑välilehti tallennustilan ja logon hallintaan. Kaikki toimii offline.

Käyttö Pythonilla (nopea testaus)
---------------------------------
1) Asenna Python 3.9+ Windowsille.
2) Avaa PowerShell/Command Prompt projektin kansiossa ja aja:
   - `py -3 -m venv .venv`
   - `.venv\\Scripts\\activate`
   - `pip install opencv-python pillow`
   - `py usb_cam_viewer.py`

Rakennus .exe (Windows)
-----------------------
1) Varmista, että Python 3.9+ ja `py`‑käynnistin ovat asennettu.
2) Aja Windowsissa:
   - `scripts\\build-windows-exe.bat`
3) Löydät binaarin: `dist\Kamerajarjestelma.exe`

Paketointi ZIPiksi (lähetettäväksi)
-----------------------------------
- Aja: `scripts\\package-zip.bat`
- Valmis paketti: `release\kamera_final.zip`
- Vastaanottaja: pura `.zip` ja suorita `Kamerajarjestelma.exe`.

Sovelluksen käyttö
------------------
- Käynnistä `Kamerajarjestelma.exe`.
- Valitse "Näkymä": 1, 2 tai Tallenteet.
- Valitse alasvetovalikosta kamerat (`usb-1`, `usb-2`, …). Videon pitäisi alkaa näkyä.
- Käytä valintoja: Liikkeentunnistus, Henkilötunnistus.
- Tallenteet: siirry Tapahtumat‑välilehdelle klikkaamalla listaa; valittu klippi toistuu oikealla.
- Lisää merkintä: valitse tapahtuma ja paina "Lisää merkintä" (esim. havainto tai nimi). Merkintä näkyy nimen perässä.
- Asetukset: säädä tallennusraja (GB), tyhjennä tallenteet ja valitse `logo.png` taustalogoksi; säädä läpinäkyvyys liukusäätimellä.
- Avaa kansio: Tapahtumat‑välilehdellä painike "Avaa kansio" avaa `recordings/`‑kansion.
- Kuvakaappaus: Live‑näkymässä painike "Kuvakaappaus" tallentaa still‑kuvan `recordings/`‑kansioon.

Huomioita
---------
- Kameralistaus: Sovellus testaa indeksit 0..9 ja nimentää löydetyt laitteet `usb-1`, `usb-2`, ...
- Ajaminen vain paikallisesti: Ei verkko‑/pilviasetuksia.
- Henkilötunnistus: Käyttää OpenCV HOG‑SVM:ää; piirtää laatikon ja prosenttiarvion (SVM‑pisteestä johdettu). Ei vaadi lisämalleja.
- Liikkeentunnistus: Taustan vähennys (MOG2); overlay "Motion" näkyy kun liike ylittää rajan.
- Tapahtumatallennus: 
  - Puskuroi jatkuvasti n. 3 s. Kun liike alkaa, luo "Tallenne N" ja tallentaa: 3 s ennen + liikkeen ajan + 5 s liikkeen päättymisen jälkeen.
  - Tallenteet tallentuvat kansioon `recordings/` AVI‑muodossa (MJPG), yhteensopiva Windowsin oletussoittimien kanssa.
- Asetukset: näyttää tallennustilan käytön esim. "Käyttöaste: 10%, 500 MB / 5.0 GB" ja pitää rajan automaattisesti voimassa poistamalla vanhimpia klippejä rajan ylittyessä.
- Logo: `logo.png` projektin juuressa näytetään automaattisesti videon päällä; läpinäkyvyys säädettävissä.
  - Jos `logo.png` puuttuu, sovellus käyttää pientä sisäänrakennettua paikkakuvaa.
- Suorituskyky: Oletusresoluutio pyydetään 1280x720; UI skaalataan (1 näkymä ~960x540, 2 näkymää ~640x360). Laske FPS/resoluutio tarvittaessa.
- Virhetilanteet: Jos kuva ei näy, irrota/kytke kamera ja paina "Päivitä lista" tai käynnistä sovellus uudelleen.

Riippuvuudet
------------
- `opencv-python`
- `Pillow`
- (rakennukseen) `pyinstaller`

Linux TL;DR — tee siirtopaketti Windowsia varten
-----------------------------------------------
- Aja komennot projektin juuressa (missä `usb_cam_viewer.py` sijaitsee).
- Jos `zip` on valmiina:
  - `zip -r kamera_final.zip usb_cam_viewer.py scripts README_windows_camera.md logo.png`
- Jos `zip` puuttuu (vaatii hetkeksi root):
  - `sudo apt-get update && sudo apt-get install -y zip`
  - sitten komento yllä.
- Siirrä `kamera_final.zip` Windowsiin, pura ja aja `scripts\package-zip.bat` tai `scripts\build-windows-exe.bat`.

Mallien sijoitus (valinnainen)
------------------------------
- Luo `models/` samaan kansioon kuin `Kamerajarjestelma.exe` tai projektin juureen kehityksessä.
- Aseta tiedostot:
  - `models/gender_deploy.prototxt`
  - `models/gender_net.caffemodel`
- Sovellus etsii nämä automaattisesti eikä käytä verkkoa.

Windows EXE‑metatiedot
----------------------
- Rakennus leimaa tiedostometatietoihin tekijän: `(C) Jugi@AnomFIN 2025`. Huom: tämä ei ole kryptografinen koodisignaus (se vaatii erillisen varmenteen ja `signtool`‑allekirjoituksen).
