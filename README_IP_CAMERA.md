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

1. **Älä jaa kirjautumistietoja**: Kameran salasanat tallennetaan paikallisesti
2. **Käytä vahvoja salasanoja**: Vaihda kameran oletussalasana
3. **Paikallinen verkko**: Käytä kameroita vain luotetussa verkossa
4. **Päivitä kameran laiteohjelmisto**: Pidä kamerat ajan tasalla tietoturvan vuoksi
