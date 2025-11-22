# IP/WiFi-kameran käyttöohje

AnomRecorder tukee nyt IP/WiFi-kameroiden liittämistä USB-kameroiden lisäksi. Tämä mahdollistaa esimerkiksi älypuhelimien ja verkkokameroiden käytön.

## Tuetut protokollat

- **RTSP** (Real-Time Streaming Protocol) - Yleisin IP-kameroiden protokolla
- **HTTP/MJPEG** - HTTP-pohjainen Motion JPEG -striimaus

## IP-kameran lisääminen

### Manuaalinen lisäys

1. Klikkaa **+ IP-kamera** -painiketta Live-välilehdellä
2. Valitse **Manuaalinen**-välilehti
3. Täytä seuraavat tiedot:
   - **IP-osoite**: Kameran IP-osoite verkossa (esim. 192.168.1.100)
   - **Portti**: Kameran portti (RTSP: 554, HTTP: 80/8080)
   - **Protokolla**: Valitse RTSP tai HTTP/MJPEG
   - **Käyttäjänimi** ja **Salasana**: Kameran kirjautumistiedot (jos vaaditaan)
   - **Polku**: Valinnainen URL-polku (esim. /stream1)

4. Klikkaa **Testaa yhteyttä** varmistaaksesi, että kamera vastaa
5. Klikkaa **Lisää kamera** tallentaaksesi kameran

### Automaattinen haku

1. Klikkaa **+ IP-kamera** -painiketta Live-välilehdellä
2. Valitse **Automaattinen haku** -välilehti
3. Voit syöttää valinnaiset kirjautumistiedot, jos kamerat vaativat autentikoinnin
4. Klikkaa **Aloita haku**
5. Odota, että haku skannaa paikallisen verkon (voi kestää useita minuutteja)
6. Valitse löydetty kamera listasta
7. Klikkaa **Lisää valittu kamera**

## WiFi-kameroiden tuki (Ring, EUFY jne.)

AnomRecorder tukee **Ring** ja **EUFY** WiFi-kameroita sekä muita suosittuja merkkejä RTSP/HTTP-protokollien kautta.

### Ring-kamerat

Ring-kamerat tukevat RTSP-protokollaa Ring Protect -tilauksella:

1. **Aktivoi RTSP Ring-sovelluksessa**:
   - Avaa Ring-sovellus älypuhelimessasi
   - Valitse kamera → Laitteen asetukset → Video-asetukset
   - Ota käyttöön "RTSP" (vaatii Ring Protect Plus -tilauksen)
   - Sovellus näyttää RTSP URL:n, käyttäjänimen ja salasanan

2. **Lisää kamera AnomRecorderiin**:
   - Klikkaa **+ IP-kamera** → **Manuaalinen**
   - Syötä Ring-sovelluksen antamat tiedot:
     - IP-osoite tai hostname
     - Portti: 554 (oletus)
     - Protokolla: RTSP
     - Käyttäjänimi ja salasana Ring-sovelluksesta
     - Polku: sovelluksen näyttämä polku (esim. `/live`)

**Huom**: Ring RTSP vaatii Ring Protect Plus -tilauksen ja ei ole saatavilla kaikille Ring-kameroille.

### EUFY-kamerat

EUFY-kamerat tukevat RTSP-yhteyttä paikallisessa verkossa:

1. **Aktivoi RTSP EUFY-sovelluksessa**:
   - Avaa EUFY Security -sovellus
   - Valitse kamera → Asetukset ⚙️
   - Siirry kohtaan "Streaming & Recording"
   - Ota käyttöön "RTSP Stream"
   - Sovellus näyttää RTSP URL:n muodossa: `rtsp://admin:password@192.168.x.x:8554/live0`

2. **Lisää kamera AnomRecorderiin**:
   - Klikkaa **+ IP-kamera** → **Manuaalinen**
   - Syötä EUFY-sovelluksen antamat tiedot:
     - IP-osoite: esim. 192.168.1.100
     - Portti: 8554 (EUFY oletus)
     - Protokolla: RTSP
     - Käyttäjänimi: admin (oletus)
     - Salasana: kameran salasana
     - Polku: /live0 tai /live1 (riippuu kameravirrasta)

### Muut WiFi-kamerat

AnomRecorder tukee myös muita suosittuja WiFi-kameramerkkejä, jotka käyttävät RTSP/HTTP:

- **Wyze Cam**: RTSP tuki v2/v3-malleissa (RTSP-firmware vaadittava)
- **Nest Cam**: Rajoitettu RTSP-tuki (tietyt mallit)
- **Arlo**: RTSP-tuki Arlo Pro/Ultra -malleissa
- **TP-Link Tapo**: RTSP-tuki useimmissa malleissa
- **Reolink**: Laaja RTSP-tuki kaikissa malleissa

**Yleiset RTSP-polut eri valmistajille:**
```
Ring:      rtsp://username:password@ip:554/live
EUFY:      rtsp://admin:password@ip:8554/live0
Wyze:      rtsp://username:password@ip:554/live
Tapo:      rtsp://username:password@ip:554/stream1
Reolink:   rtsp://admin:password@ip:554/h264Preview_01_main
```

## Älypuhelimen käyttö kamerana

### Android

1. Asenna RTSP-palvelinsovelus (esim. "IP Webcam" tai "DroidCam")
2. Käynnistä sovellus ja merkitse muistiin IP-osoite ja portti
3. Lisää kamera manuaalisesti AnomRecorderiin käyttäen sovelluksen näyttämiä tietoja

### iOS

1. Asenna RTSP-palvelinsovelus (esim. "IP Camera Lite" tai "iVCam")
2. Käynnistä sovellus ja merkitse muistiin IP-osoite ja portti
3. Lisää kamera manuaalisesti AnomRecorderiin käyttäen sovelluksen näyttämiä tietoja

## Yleiset URL-muodot

### RTSP
```
rtsp://käyttäjä:salasana@192.168.1.100:554/stream1
rtsp://192.168.1.100:554/
```

### HTTP/MJPEG
```
http://käyttäjä:salasana@192.168.1.100:8080/video.mjpg
http://192.168.1.100:8080/video
```

## Vianetsintä

### Kamera ei yhdistä

1. **Tarkista verkkoyhteyttä**:
   - Varmista, että tietokone ja kamera ovat samassa WiFi-verkossa
   - Testaa yhteys pingaamalla kameran IP-osoite: `ping 192.168.1.100`

2. **Tarkista IP-osoite ja portti**:
   - Varmista, että IP-osoite on oikein
   - Kokeile eri portteja (RTSP: 554, 8554; HTTP: 80, 8080, 8081)

3. **Tarkista kirjautumistiedot**:
   - Jos kamera vaatii salasanaa, varmista että käyttäjänimi ja salasana ovat oikein
   - Jotkin kamerat käyttävät oletuskirjautumistietoja (admin/admin, admin/password)

4. **Kokeile eri polkuja**:
   - RTSP: /stream1, /stream, /live, /h264
   - HTTP: /video, /video.mjpg, /mjpeg, /videostream.cgi

5. **Palomuuriasetukset**:
   - Varmista, että Windows-palomuuri ei estä yhteyttä
   - Lisää AnomRecorder palomuurin poikkeuslistalle tarvittaessa

### Ring-kameran erityisongelmat

1. **RTSP ei ole saatavilla**:
   - Tarkista, että sinulla on Ring Protect Plus -tilaus (perus Ring Protect ei riitä)
   - Varmista, että kameramallisi tukee RTSP:tä (ei kaikki Ring-kamerat)
   - Tarkista Ring-sovelluksesta, että RTSP-asetus on otettu käyttöön

2. **Yhteys katkeaa usein**:
   - Ring RTSP-striimaus saattaa aikakatkaista 10-15 minuutin jälkeen
   - Tämä on Ring-palvelun rajoitus, ei AnomRecorderin ongelma
   - AnomRecorder yrittää automaattisesti yhdistää uudelleen

3. **Kirjautumistiedot eivät toimi**:
   - Käytä täsmälleen Ring-sovelluksen näyttämiä kirjautumistietoja
   - Älä käytä Ring-tilisi salasanaa, vaan sovelluksen luomaa RTSP-salasanaa
   - Varmista, että salasanassa ei ole ylimääräisiä välilyöntejä

### EUFY-kameran erityisongelmat

1. **RTSP-asetus ei löydy**:
   - Varmista, että kameran firmware on ajan tasalla
   - Tarkista, että kameramallisi tukee RTSP:tä (useimmat EUFY-kamerat tukevat)
   - Joissakin malleissa RTSP löytyy kohdasta "Advanced Settings"

2. **"Admin" ei toimi käyttäjänimena**:
   - Kokeile tyhjää käyttäjänimeä tai kameran alkuperäistä käyttäjänimeä
   - Jotkin EUFY-mallit käyttävät kameran sarjanumeroa käyttäjänimenä
   - Tarkista oikea käyttäjänimi EUFY-sovelluksen RTSP-asetuksista

3. **Portti 8554 ei vastaa**:
   - Tarkista EUFY-sovelluksesta oikea portti (voi vaihdella mallista riippuen)
   - Kokeile portteja 554, 8554, ja 8555
   - Varmista, että kamera on samassa WiFi-verkossa kuin tietokone

### Kuva pätkii tai viivästyy

1. **Verkkoyhteys**:
   - Tarkista WiFi-signaalin vahvuus
   - Kokeile käyttää langallista verkkoa (Ethernet)

2. **Kameran asetukset**:
   - Alenna kameran resoluutiota tai laatua kameran asetuksista
   - Vähennä kuvataajuutta (fps)

3. **Resurssit**:
   - Sulje muita verkkoa käyttäviä sovelluksia
   - Tarkista tietokoneen CPU- ja muistikäyttö

## Suositellut sovellukset

### Android
- **IP Webcam** - Ilmainen, monipuolinen, tukee RTSP ja HTTP
- **DroidCam** - Yksinkertainen, toimii hyvin
- **Alfred Home Security Camera** - Hyvä yölliseen tallennukseen

### iOS
- **IP Camera Lite** - Ilmainen, helppo käyttää
- **iVCam** - Tukee USB- ja WiFi-yhteyttä
- **EpocCam** - Korkealaatuinen, maksullinen

## Tekninen tuki

Jos kohtaat ongelmia:

1. Tarkista konsoliloki virheilmoituksista
2. Varmista, että kaikki riippuvuudet on asennettu: `pip install -r requirements.txt`
3. Kokeile yhteyttä toisella ohjelmalla (VLC Media Player voi avata RTSP-striimejä)
4. Ota yhteyttä tukeen GitHub Issues -sivun kautta

## Tietoturvavinkit

⚠️ **TÄRKEÄÄ - SALASANOJEN TALLENNUS**

IP-kameran salasanat tallennetaan **selkokielisena** paikalliseen `config.json`-tiedostoon. Tämä on tarpeen, jotta sovellus voi yhdistää kameroihin automaattisesti. **ÄLÄ** käytä samoja salasanoja, joita käytät muissa palveluissa.

**Suositukset:**

1. **Käytä erillisiä salasanoja**: Luo kameralle oma salasana, jota et käytä missään muualla
2. **Vaihda oletussalasanat**: Vaihda kameran tehdasasetuksissa olevat salasanat (admin/admin, admin/password)
3. **Paikallinen verkko**: Käytä kameroita vain luotetussa, yksityisessä verkossa
4. **Rajoita pääsy**: Varmista, että tietokoneesi ja config.json-tiedosto eivät ole jaettu muiden kanssa
5. **Päivitä laiteohjelmisto**: Pidä kamerat ajan tasalla tietoturvan vuoksi
6. **Ei julkisiin verkkoihin**: Älä käytä IP-kameroita julkisissa WiFi-verkoissa

Jos haluat poistaa tallennetut salasanat, voit:
- Poistaa IP-kameran käyttöliittymästä
- Muokata config.json-tiedostoa manuaalisesti
- Poistaa config.json-tiedoston kokonaan (poistaa kaikki asetukset)
