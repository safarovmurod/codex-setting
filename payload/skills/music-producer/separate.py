#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Music Producer — ҷудокунии профессионалии вокал/минус/стемҳо бо Demucs.

Мисол:
    python skills/music-producer/separate.py "song.mp3" --mode pro
    python skills/music-producer/separate.py "song.mp3" --mode four --out separated

Ҳама кор локалӣ: soundfile (хониш/навишт) + demucs (модел). ffmpeg лозим нест.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np
import soundfile as sf

MODES = {
    # mode:  model,          two_stems, shifts, overlap
    "fast": ("htdemucs",     True,  1, 0.25),
    "pro":  ("htdemucs_ft",  True,  2, 0.50),
    "max":  ("htdemucs_ft",  True,  4, 0.75),
    "four": ("htdemucs",     False, 1, 0.25),
}

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def slugify(text: str) -> str:
    table = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j",
             "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
             "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
             "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
             "я": "ya", "ӣ": "i", "ӯ": "u", "қ": "q", "ғ": "g", "ҳ": "h", "ҷ": "j"}
    out = "".join(table.get(c, c) for c in text.lower())
    out = re.sub(r"[^a-z0-9]+", "-", out).strip("-")
    return out[:60] or "track"


def load(path: str) -> tuple[np.ndarray, int]:
    data, sr = sf.read(path, always_2d=True, dtype="float32")
    return data, sr


def ensure_stereo(data: np.ndarray) -> np.ndarray:
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    return data[:, :2]


def db(x: float) -> float:
    return float(20.0 * np.log10(max(x, 1e-12)))


def qc(orig: np.ndarray, sr: int, vocals: np.ndarray, acc: np.ndarray) -> dict:
    n = min(len(orig), len(vocals), len(acc))
    o, v, a = orig[:n, :2], vocals[:n, :2], acc[:n, :2]
    recon = v + a
    err_abs = float(np.max(np.abs(o - recon)))
    o_norm = float(np.linalg.norm(o))
    err_rel = float(np.linalg.norm(o - recon) / o_norm) if o_norm > 1e-9 else 1.0
    best_gain = float((o * recon).sum() / max(float((recon * recon).sum()), 1e-12))
    peak_v = float(np.max(np.abs(v))) if n else 0.0
    peak_a = float(np.max(np.abs(a))) if n else 0.0
    rms_v = float(np.sqrt(np.mean(v ** 2))) if n else 0.0
    rms_a = float(np.sqrt(np.mean(a ** 2))) if n else 0.0
    # leak: коррелятсияи вокал бо минус (ба ҳамдигар набояд вобаста бошанд)
    if n and v.std() > 1e-9 and a.std() > 1e-9:
        corr = float(np.corrcoef(v.mean(axis=1), a.mean(axis=1))[0, 1])
    else:
        corr = 0.0
    # паҳнои стерео дар минус: 1.0 = пурра моно
    if n and a.std() > 1e-9:
        mono_corr = float(np.corrcoef(a[:, 0], a[:, 1])[0, 1])
    else:
        mono_corr = 1.0
    return {
        "seconds": round(n / sr, 2),
        "sample_rate": sr,
        "sum_reconstruction_dbfs": round(db(err_abs), 1),
        "sum_error_db_rel": round(db(err_rel), 1),
        "sum_ok": bool(err_rel < 0.1),
        "best_gain_db": round(db(best_gain), 2),
        "peak_vocals_dbfs": round(db(peak_v), 2),
        "peak_accompaniment_dbfs": round(db(peak_a), 2),
        "rms_vocals_dbfs": round(db(rms_v), 2),
        "rms_accompaniment_dbfs": round(db(rms_a), 2),
        "vocals_vs_accompaniment_corr": round(corr, 4),
        "accompaniment_stereo_corr": round(mono_corr, 4),
        "clipping_samples": int(np.sum(np.abs(v) >= 0.999) + np.sum(np.abs(a) >= 0.999)),
    }


def ffmpeg_exe() -> str | None:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def decode(path: str, tmpdir: str) -> tuple[np.ndarray, int]:
    """soundfile аввал; агар формат (m4a/aac/wma) дастгирӣ нашавад — ffmpeg."""
    try:
        return load(path)
    except Exception as exc:
        ff = ffmpeg_exe()
        if not ff:
            raise RuntimeError(
                f"Формати файл бо soundfile хонда нашуд ({exc}). ffmpeg нест — "
                "`pip install imageio-ffmpeg` иҷро кунед."
            ) from exc
        out = os.path.join(tmpdir, "decoded.wav")
        print(f"→ soundfile ин форматров надонад ({type(exc).__name__}); бо ffmpeg табдил медиҳам…")
        subprocess.run([ff, "-v", "error", "-y", "-i", path, "-vn",
                        "-ac", "2", "-c:a", "pcm_f32le", out], check=True)
        return load(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Demucs: вокал / минус / 4 стем")
    ap.add_argument("input", help="файли аудио (mp3, wav, flac, m4a, ogg…)")
    ap.add_argument("--mode", choices=sorted(MODES), default="pro")
    ap.add_argument("--out", default="separated", help="папкаи натиҷа")
    ap.add_argument("--name", default=None, help="номи папкаи натиҷа")
    ap.add_argument("--keep-wav", action="store_true", help="танҳо WAV (пешфарз ҳамин аст)")
    ap.add_argument("--device", default=None, help="cpu ё cuda (пешфарз: худкор)")
    args = ap.parse_args()

    src = os.path.abspath(args.input)
    if not os.path.exists(src):
        print(f"ХАТО: файл нест: {src}", file=sys.stderr)
        return 2

    model, two_stems, shifts, overlap = MODES[args.mode]
    out_root = os.path.abspath(args.out)
    track = args.name or slugify(os.path.splitext(os.path.basename(src))[0])
    dest = os.path.join(out_root, track)
    os.makedirs(out_root, exist_ok=True)

    print(f"→ манбаъ : {os.path.basename(src)}")
    print(f"→ реҷа  : {args.mode}  (model={model}, shifts={shifts}, overlap={overlap})")

    tmp = tempfile.mkdtemp(prefix="demucs_")
    data, sr = decode(src, tmp)
    data = ensure_stereo(data)
    print(f"→ аудио : {len(data)/sr:.1f} с, {sr} Hz, stereo")
    src_wav = os.path.join(tmp, "input.wav")
    sf.write(src_wav, data, sr, subtype="FLOAT")

    cmd = [sys.executable, "-m", "demucs", "-n", model,
           "--shifts", str(shifts), "--overlap", str(overlap),
           "--clip-mode", "rescale", "--out", tmp]
    if two_stems:
        cmd += ["--two-stems=vocals"]
    if args.device:
        cmd += ["-d", args.device]
    cmd.append(src_wav)

    print("→ Demucs кор карда истодааст (ин метавонад дароз кашад)…")
    t0 = time.time()
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = "\n".join((proc.stdout or "").strip().splitlines()[-15:])
        print("ХАТОИ DEMUCS:\n" + tail, file=sys.stderr)
        shutil.rmtree(tmp, ignore_errors=True)
        return proc.returncode
    elapsed = time.time() - t0

    produced = os.path.join(tmp, model, "input")
    if not os.path.isdir(produced):
        print("ХАТО: натиҷа ёфт нашуд: " + produced, file=sys.stderr)
        return 3

    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)
    for fn in sorted(os.listdir(produced)):
        if fn.lower().endswith((".wav", ".flac", ".mp3")):
            shutil.copy2(os.path.join(produced, fn), os.path.join(dest, fn))

    stems = {}
    for fn in os.listdir(dest):
        if not fn.lower().endswith(".wav"):
            continue
        d, rsr = load(os.path.join(dest, fn))
        wav16 = os.path.join(dest, fn)
        if rsr == sr:
            sf.write(wav16, d, rsr, subtype="PCM_16")
        stems[os.path.splitext(fn)[0]] = d

    result = {"input": os.path.basename(src), "mode": args.mode, "model": model,
              "shifts": shifts, "overlap": overlap, "seconds_audio": round(len(data) / sr, 2),
              "seconds_processing": round(elapsed, 1), "out_dir": dest,
              "stems": sorted(stems)}

    v = stems.get("vocals")
    a = stems.get("no_vocals")
    if a is None:
        a = stems.get("accompaniment")
    if v is not None and a is not None:
        metrics = qc(data, sr, v, a)
        result["qc"] = metrics
        print("\n— САНҶИШ —")
        print(f"  хатогии нисбии сумма: {metrics['sum_error_db_rel']} dB "
              f"({'OK' if metrics['sum_ok'] else 'ШАКК'}; меъёр < -20 dB)")
        print(f"  фоидаи беҳтарин    : {metrics['best_gain_db']} dB (бояд ~0)")
        print(f"  пик вокал/минус    : {metrics['peak_vocals_dbfs']} / "
              f"{metrics['peak_accompaniment_dbfs']} dBFS")
        print(f"  клиппинг           : {metrics['clipping_samples']} намуна")
        print(f"  вобастагии вокал↔минус: {metrics['vocals_vs_accompaniment_corr']}")
        print(f"  стерео дар минус   : {metrics['accompaniment_stereo_corr']} (1.0 = моно)")

    with open(os.path.join(dest, "_qc.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n✅ Тайёр: {dest}  ({elapsed:.0f} с коркард)")
    for s in result["stems"]:
        print("   • " + s + ".wav")
    return 0


if __name__ == "__main__":
    sys.exit(main())
