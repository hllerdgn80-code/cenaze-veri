# Mac'e GitHub self-hosted runner kurulumu (Turkiye'den okuma)

Amac: Kocaeli, Van ve Mugla (Milas) kaynaklari GitHub'in yurt disi sunucularindan acilmiyor. Bu Mac'ten aciliyor. Runner, yalniz bu illeri okuyup sonucu depoya (`veri-tr/`) yazar; ana is (`topla.yml`) o veriyi alip siteye ekler.

Calisma saatleri: her gun TR saatiyle 06:41, 09:41, 12:41 (ana islerden 6 dk once; Aksaray, Malatya ve Arnavutkoy artik GitHub uzerinden Cloudflare kopru Worker ile okunur). Elle de baslatilabilir: GitHub > Actions > "Turkiye'den oku" > Run workflow.

## 1. Kurulum (bir kez)

1. Tarayicida depoyu ac > **Settings > Actions > Runners > New self-hosted runner**.
2. Isletim sistemi: **macOS**. Mimari: Mac'in Intel ise **x64** (2020 Air Intel'dir).
3. Sayfadaki **Download** bolumundeki komutlari Terminal'e sirayla yapistir (klasoru `actions-runner` olusturur; yani `~/actions-runner`).
4. Sayfadaki **Configure** bolumundeki `./config.sh --url ... --token ...` komutunu yapistir (token sayfada hazir gelir, 1 saat gecerli).
   - "Enter the name of the runner group": **Enter** (varsayilan)
   - "Enter the name of runner": **halil-mac** yaz, Enter
   - "Enter any additional labels": **Enter** (bos gec; etiket gerekmez)
   - "Enter name of work folder": **Enter** (varsayilan `_work`)
5. Servis olarak kur (Mac acilinca kendiliginden baslar):

```bash
cd ~/actions-runner
./svc.sh install
./svc.sh start
./svc.sh status
```

6. GitHub > Settings > Actions > Runners sayfasinda `halil-mac` **Idle** (yesil) gorunmeli.
7. Deneme: Actions > "Turkiye'den oku" > Run workflow. Bitince depoda `veri-tr/` klasoru olusur.

## 2. Mac uykudayken

Runner yalniz Mac **uyanikken** calisir. Uyku modunda is kacar. Iki yol:
- **Sistem Ayarlari > Pil/Enerji Tasarrufu > "Ekran kapaliyken Mac'in uyumasini engelle"** (masaustu/guc adaptorlu) acik olsun ya da gerekli saatlerde Mac'i uyanik birak.
- Kacan turlarda sorun olmaz: `topla.yml` yurt disinda okumayi surdurur, yalniz bu 3 kaynak eski veriyle kalir. `veri-tr` verisi 36 saatten eskiyse `topla.yml` onu kullanmaz ve Actions gunlugune "TR runner calismiyor" uyarisi basar.

## 3. Guvenlik (onemli, okuyun)

- Runner **yalniz bu depoya** baglidir. Baska depoda kullanilmaz.
- Depo **herkese acik** (public). GitHub belgesi: public depoda self-hosted runner, fork'tan gelen bir Pull Request'in kodunu Mac'inizde calistirabilir. Bu **gercek bir risktir**; kotu niyetli biri PR ile Mac'inizde komut calistirabilir.
- Onlem (kurulumdan sonra kontrol edin): **Settings > Actions > General > Fork pull request workflows**: "Run workflows from fork pull requests" **kapali (isaretsiz)** olsun; "Require approval for all outside collaborators" secenegini **degistirmeyin** (varsayilani koruyun). Bu workflow zaten yalniz `schedule` ve `workflow_dispatch` ile tetiklenir, `pull_request` tetikleyicisi yoktur; bunu bozmayin, ileride ona `pull_request` eklemeyin.
- Runner, kullanici hesabinizla calisir: Mac'te onemli dosyalar varsa (sifreler, belgeler) bunu goz onunde bulundurun. Isterseniz bu is icin ayri bir macOS kullanici hesabi acip runner'i orada kurun.
- Depoya yazma yetkisi yalniz bu workflow'da (`contents: write`) tanimlidir; depoyu Private yaparsaniz fork riski kalmaz.

## 4. Kaldirma

```bash
cd ~/actions-runner
./svc.sh stop
./svc.sh uninstall
./config.sh remove --token <GitHub'in Runners sayfasinda "Remove" dediginde verdigi token>
cd ~ && rm -rf ~/actions-runner
```

Gecici durdurma icin yalniz `./svc.sh stop` yeter; tekrar `./svc.sh start`.

## 4. Mac açılınca tur (sahibi 16.10.2026: "saate bağlı değil, Mac'i açtığımda başlasın")

`araclar/mac_tetik.py` + `sunucu/mac-tetik.plist`: oturum açılışında ve sonra her 10 dakikada bir çalışır; "Türkiye'den oku" için son 2 saatte koşu yoksa
tetikler (Mac açılır açılmaz tur; açık kaldıkça en çok 2 saatte bir). Sunucudaki saatli tetikleyici ve bekçi sürer; koşu varsa hepsi atlar, çift tur olmaz.
Kurulum (bir kez):

```bash
cp ~/Desktop/model-arastirmasi/cenaze-uygulamasi/sunucu/mac-tetik.plist ~/Library/LaunchAgents/com.kimincenazesi.mac-tetik.plist && launchctl unload ~/Library/LaunchAgents/com.kimincenazesi.mac-tetik.plist 2>/dev/null; launchctl load ~/Library/LaunchAgents/com.kimincenazesi.mac-tetik.plist && launchctl list | grep mac-tetik
```

Kontrol: `tail -3 ~/Desktop/model-arastirmasi/cenaze-uygulamasi/araclar/mac_tetik.log` ("TETİKLENDİ" ya da "ATLANDI: koşu zaten var"). Kaldırmak: `launchctl unload ~/Library/LaunchAgents/com.kimincenazesi.mac-tetik.plist`.
Not: uykudan uyanınca ilk deneme Wi-Fi bağlanmadan düşebilir ("ağ yok"); 10 dk sonra kendiliğinden yeniden dener.
