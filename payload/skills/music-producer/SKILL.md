---
name: music-producer
description: Профессионалии ҷудокунии вокал аз мусиқӣ (минус/стемҳо), таҳлили техникии овоз (BPM, кулид, пик, клиппинг), санҷиши сифат ва сохтани промпт/матн барои суруди нав. Use when the user asks to split vocals from a track, make a minus/karaoke, get 4 stems, analyze a mix, or check separation quality.
---

# Music Producer (локалӣ, ройгон, бе интернет баъд аз зеркашӣ)

Ҳама кор дар компютери корбар иҷро мешавад: **Demucs 4.1.0** + PyTorch (CPU) + soundfile.
Ягон сервиси пулакӣ истифода намешавад.

## Муҳит (тафтишшуда 2026-10-20)

| Чиз | Ҳолат |
|---|---|
| `python -m demucs` | ✅ 4.1.0 |
| `torch` / `torchaudio` | ✅ 2.14.1+cpu / 2.11.0+cpu |
| `librosa`, `soundfile`, `numpy`, `scipy` | ✅ |
| Моделҳо `htdemucs`, `htdemucs_ft` | ✅ кэш дар `%USERPROFILE%\.cache\huggingface\hub` |
| `ffmpeg` | ✅ 7.1 тавассути бастаи `imageio-ffmpeg` (83 MB). Дар PATH нест — скрипт худаш роҳи онро меёбад. Барои m4a/aac/wma ҳатмист |
| `soundfile` (mp3) | ✅ mp3-и оддӣ мехонад; m4a/aac-ро не → худкор ба ffmpeg мегузарад |
| Стенди браузерӣ | `python music-lab/server.py` → http://127.0.0.1:8765 |

## Дастурҳои асосӣ

> Скрипт дар ду ҷо ҳаст: `skills/music-producer/separate.py` (коргоҳ) ва `~/.cursor/skills/music-producer/separate.py` (скилли насбшуда). Ҳар кадомер ба шумо наздиктар аст, истифода баред.

```powershell
# 1) Тез: вокал + минус (htdemucs)
python skills/music-producer/separate.py "song.mp3" --mode fast

# 2) Профессионалӣ: htdemucs_ft + shifts + overlap (тавсия)
python skills/music-producer/separate.py "song.mp3" --mode pro

# 3) Максимум сифат (қиммат вақт: ~3-5× давомнокии суруд дар CPU)
python skills/music-producer/separate.py "song.mp3" --mode max

# 4) 4 стем: vocals / drums / bass / other
python skills/music-producer/separate.py "song.mp3" --mode four
```

Натиҷа: `<out>/<номи суруд>/vocals.wav`, `no_vocals.wav`, `_qc.json`.

## Реҷаҳо (сирри «ҳамеша дақиқ»)

| Реҷа | Модел | shifts | overlap | clip-mode | Вақт (суруди 4 дақ) |
|---|---|---|---|---|---|
| `fast` | htdemucs | 1 | 0.25 | rescale | ~4-6 дақ |
| `pro` | htdemucs_ft | 2 | 0.50 | rescale | ~20-30 дақ |
| `max` | htdemucs_ft | 4 | 0.75 | rescale | ~40-60 дақ |

`shifts` артефактҳои «гоҳ-гоҳ» (dips, хрип)-ро кам мекунад; `overlap` дарзи байнҳолаҳоро ҳамвор мекунад; `rescale` клиппингро нест мекунад. Барои суруди реп/вокали зич `max` — беҳтарин.

## Санҷиши ҳатмии сифат (баъд аз ҳар ҷудокунӣ)

1. **Хатогии нисбии сумма**: `20*log10(||original - (vocals+minus)|| / ||original||)` бояд **< -20 dB** бошад. (Demucs модели маска нест — суммааш 100% дақиқ нест; -20…-40 dB меъёри нормалӣ аст.)
2. **Фоида (gain)**: `best_gain` бояд **~0 dB** бошад. Агар аз ±3 dB зиёд бошад — яке аз стемҳо нодуруст миқёс шудааст (одатан `rescale`).
3. **Ифлосӣ (leak)**: минусро гӯш кунед — овози асосӣ набояд шунавад. Андозаи ададӣ: коррелятсияи `vocals` бо `no_vocals` бояд наздик ба 0 бошад (0.0-0.1 хуб).
4. **Клиппинг**: `clipping_samples` бояд 0 бошад; пик < -0.1 dBFS.
5. **Стерео**: `accompaniment_stereo_corr` набояд 1.0 бошад (1.0 = минус моно шудааст).

`separate.py` ҳамаи ин 5 санҷишро худкор мекунад ва дар `_qc.json` нависад. Намунаи воқеӣ (8 сония, реҷаи `fast`): хатогии сумма -36.3 dB, фоида 0.03 dB, коррелятсия 0.013, клиппинг 0, вақти коркард 13 с.

## Қоидаҳои кор

- Ҳеҷ гоҳ ба корбар нагӯед «дақиқ аст» бе санҷиши ададӣ — `_qc.json`-ро нишон диҳед.
- Агар суруд аз YouTube/Spotify бошад — сифати манбаъ муҳимтар аз реҷа аст; аввал 320 kbps/FLAC талаб кунед.
- mp3-и натиҷа: бо soundfile нависед (`sf.write(..., format='MP3')` танҳо агар libsndfile дастгирӣ кунад), вагарна WAV 16-bit диҳед.
- Барои гӯш кардан: `python music-lab/server.py` → http://127.0.0.1:8765 (плеер + китобхона дар `music-lab/songs/`).

## Вақте ки кор намекунад

| Аломат | Сабаб | Ҳал |
|---|---|---|
| `ffmpeg not found` | m4a/aac ё `--mp3`-и demucs | `pip install imageio-ffmpeg` (аллакай насб аст); скрипт худаш ffmpeg-ро меёбад |
| Файли `.mp3` хонда намешавад (`skip_junk`, M4A) | дар воқеъ контейнери MP4 аст | скрипт бо ffmpeg мехонад; танҳо `--mode` диҳед |
| Пики манбаъ > 1.0 (клиппинги аслӣ) | аудиои манбаъ вайрон аст | `rescale` ҷуброн мекунад, лекин сифат барнамегардад — манбаи беҳтар ҷӯед |
| Зеркашии модел оҳиста | HF бе токен | як маротиба интизор шавед; баъд офлайн кор мекунад |
| `CUDA out of memory` | GPU нест/кам | `--device cpu` (скрипт худкор CPU мегирад) |
| Натиҷа «хрип» дорад | shifts=1 | `--mode pro` ё `max` |
| Вокал дар минус мондааст | омехтаи зич | `--mode max`, ё 4 стем ва `other`-ро гӯш кунед |

## Ҳамкорӣ бо агентҳо

- Таҳлили мусиқӣ/маслиҳат → агент **分析师**
- Сохтани матн/промпт барои суруди нав → **документнавис** (`文档撰写师`)
- Санҷиши мустақили сифат → **审阅者**
