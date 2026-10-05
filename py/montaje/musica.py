"""La partitura del montaje: lo que la canción dice en números y en una imagen.

Claude no escucha. Lee el pulso (beats y su BPM), dónde cae el primer tiempo de
cada compás, la energía golpe a golpe y las secciones; y mira `musica.png`,
que pone todo eso sobre el espectrograma. El planificador corta sobre esto.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .rutas import Proyecto, escribir_json, leer_json, salir

SR = 22050


def _normalizar(x: np.ndarray) -> np.ndarray:
    bajo, alto = np.percentile(x, [5, 95])
    if alto - bajo < 1e-9:
        return np.zeros_like(x)
    return np.clip((x - bajo) / (alto - bajo), 0, 1)


def _suavizar(x: np.ndarray, ventana: int) -> np.ndarray:
    if ventana <= 1 or len(x) < ventana:
        return x
    nucleo = np.ones(ventana) / ventana
    relleno = np.pad(x, (ventana // 2, ventana - 1 - ventana // 2), mode="edge")
    return np.convolve(relleno, nucleo, mode="valid")


def analizar(p: Proyecto, archivo: str | None = None) -> Path:
    import librosa

    relativo = archivo or p.cfg.get("musica")
    if not relativo:
        salir("el proyecto no tiene `musica` y no pasaste --archivo")
    ruta = p.medios / relativo
    if not ruta.exists():
        salir(f"no encuentro el audio en {ruta}")

    # Un experimento puede usar sólo un tramo de la canción: todos los tiempos que
    # salen de aquí cuentan desde el comienzo del tramo, no de la canción.
    tramo = p.cfg.get("tramo") if not archivo else None
    if tramo:
        y, sr = librosa.load(ruta, sr=SR, mono=True, offset=tramo[0], duration=tramo[1] - tramo[0])
    else:
        y, sr = librosa.load(ruta, sr=SR, mono=True)
    duracion = len(y) / sr

    onset = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, cuadros = librosa.beat.beat_track(onset_envelope=onset, sr=sr, units="frames")
    bpm = float(np.atleast_1d(tempo)[0])
    beats = librosa.frames_to_time(cuadros, sr=sr)
    if len(beats) < 8:
        salir(f"sólo encontré {len(beats)} golpes; ¿la pista tiene pulso?")

    # Una intro sin batería no tiene golpes que detectar, pero el pulso ya existe:
    # se extiende hacia atrás al mismo período para que el montaje pueda usar la intro.
    periodo = float(np.median(np.diff(beats)))
    previos = []
    t0 = beats[0] - periodo
    while t0 > -0.05:  # hasta el comienzo, incluido un golpe que caiga justo en 0
        previos.append(t0)
        t0 -= periodo
    golpes_intro = len(previos)
    if previos:
        beats = np.concatenate([previos[::-1], beats])
        cuadros = librosa.time_to_frames(beats, sr=sr)

    # Energía por golpe: RMS medio entre un golpe y el siguiente.
    rms = librosa.feature.rms(y=y)[0]
    t_rms = librosa.times_like(rms, sr=sr)
    bordes = np.append(beats, duracion)
    energia = np.array(
        [rms[(t_rms >= a) & (t_rms < b)].mean() if np.any((t_rms >= a) & (t_rms < b)) else 0.0 for a, b in zip(bordes[:-1], bordes[1:])]
    )
    energia = _suavizar(_normalizar(energia), 4)

    # Primer tiempo del compás (asumiendo 4/4): la fase con más ataque. Con un tramo
    # corto hay pocos datos y puede errar (la batería de la Tonada entra con una
    # anacrusa, en el cuarto tiempo): `fase_compas` en proyecto.json la fija a mano.
    fuerza = onset[np.clip(cuadros, 0, len(onset) - 1)]
    if "fase_compas" in p.cfg:
        fase = int(p.cfg["fase_compas"])
    else:
        fase = int(np.argmax([fuerza[f::4].mean() for f in range(4)]))
    primeros = beats[fase::4]

    # Secciones: agrupación de compases parecidos en timbre y armonía.
    croma = librosa.feature.chroma_cqt(y=y, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    rasgos = np.vstack([librosa.util.sync(croma, cuadros), librosa.util.sync(mfcc, cuadros)])
    rasgos = (rasgos - rasgos.mean(axis=1, keepdims=True)) / (rasgos.std(axis=1, keepdims=True) + 1e-9)
    k = int(np.clip(round(duracion / 30), 3, 12))
    limites = librosa.segment.agglomerative(rasgos, k)
    limites = sorted(set(int(b) for b in limites) | {0})
    secciones = []
    for i, ini in enumerate(limites):
        fin = limites[i + 1] if i + 1 < len(limites) else len(beats)
        ini_t = float(bordes[min(ini, len(beats) - 1)])
        fin_t = float(bordes[min(fin, len(beats))])
        secciones.append(
            {
                "beat_ini": ini,
                "beat_fin": fin,
                "ini": round(ini_t, 3),
                "fin": round(fin_t, 3),
                "energia": round(float(energia[ini:fin].mean()) if fin > ini else 0.0, 3),
            }
        )

    salida = {
        "archivo": relativo,
        "tramo": [tramo[0], tramo[1]] if tramo else [0, round(duracion, 3)],
        "duracion": round(duracion, 3),
        "bpm": round(bpm, 2),
        "golpes_intro": golpes_intro,
        "beats": [round(float(b), 3) for b in beats],
        "energia": [round(float(e), 3) for e in energia],
        "fase_compas": fase,
        "primeros_tiempos": [round(float(b), 3) for b in primeros],
        "secciones": secciones,
    }
    destino = p.salida("analisis", "musica.json")
    escribir_json(destino, salida, compacto=True)
    _dibujar(y, sr, salida, p.salida("analisis", "musica.png"))

    print(
        f"{relativo}: {int(duracion // 60)} min {duracion % 60:.0f} s, {bpm:.1f} BPM, {len(beats)} golpes "
        f"({golpes_intro} extrapolados en la intro), {len(secciones)} secciones"
    )
    for s in secciones:
        barra = "█" * int(round(s["energia"] * 20))
        print(f"  {s['ini']:7.1f}–{s['fin']:7.1f} s  golpes {s['beat_ini']:4d}–{s['beat_fin']:4d}  {barra}")
    print(f"→ {destino}\n→ {destino.with_suffix('.png')}")
    return destino


def _dibujar(y, sr, a: dict, destino: Path) -> None:
    import librosa
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 8), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    S = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=2048, hop_length=512)), ref=np.max)
    librosa.display.specshow(S, sr=sr, hop_length=512, x_axis="time", y_axis="log", ax=ax1, cmap="magma")
    ax1.set_title(f"{a['archivo']} · {a['bpm']} BPM · {len(a['beats'])} golpes")
    ax1.set_xlabel("")

    ax2.plot(a["beats"], a["energia"], color="#e0a030", lw=1.6)
    ax2.fill_between(a["beats"], a["energia"], color="#e0a030", alpha=0.25)
    for t in a["primeros_tiempos"]:
        ax2.axvline(t, color="#888", lw=0.3, alpha=0.5)
    for i, s in enumerate(a["secciones"]):
        ax1.axvline(s["ini"], color="white", lw=1.2)
        ax2.axvline(s["ini"], color="#222", lw=1.2)
        ax2.text(s["ini"] + 0.5, 1.02, f"S{i + 1}", fontsize=9)
    ax2.set_ylim(0, 1.1)
    ax2.set_ylabel("energía")
    ax2.set_xlabel("segundos")
    fig.tight_layout()
    fig.savefig(destino, dpi=100)
    plt.close(fig)


def cargar(p: Proyecto) -> dict:
    ruta = p.salidas / "analisis" / "musica.json"
    if not ruta.exists():
        salir("falta el análisis de la música; corre primero: python montaje.py musica " + p.nombre)
    return leer_json(ruta)


def pista_prueba(p: Proyecto, bpm: float = 112.0, duracion: float = 180.0) -> Path:
    """Una pista sintética con pulso y arco (calma → subida → pico → respiro → pico → salida).

    Sólo para probar el montaje mientras llega la canción de verdad.
    """
    import soundfile as sf

    sr = 44100
    n = int(duracion * sr)
    t = np.arange(n) / sr
    golpe = 60.0 / bpm
    rng = np.random.default_rng(7)

    # Arco de energía en el tiempo (0..1).
    puntos = np.array([0, 0.12, 0.3, 0.45, 0.55, 0.62, 0.85, 1.0]) * duracion
    valores = np.array([0.15, 0.25, 0.7, 1.0, 0.3, 0.35, 1.0, 0.1])
    arco = np.interp(t, puntos, valores)

    audio = 0.08 * np.sin(2 * np.pi * 110 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t))  # colchón
    largo_bombo = int(0.25 * sr)
    env_bombo = np.exp(-np.arange(largo_bombo) / (0.05 * sr))
    bombo = np.sin(2 * np.pi * 55 * np.arange(largo_bombo) / sr * (1 + 2 * env_bombo)) * env_bombo
    largo_plato = int(0.06 * sr)
    for i in range(int(duracion / golpe)):
        ini = int(i * golpe * sr)
        fuerza = arco[min(ini, n - 1)]
        fin = min(n, ini + largo_bombo)
        audio[ini:fin] += (0.4 + 0.5 * fuerza) * bombo[: fin - ini] * (1.3 if i % 4 == 0 else 1.0)
        if fuerza > 0.5:  # platillo a contratiempo cuando hay energía
            medio = int((i + 0.5) * golpe * sr)
            fin = min(n, medio + largo_plato)
            ruido = rng.standard_normal(fin - medio) * np.exp(-np.arange(fin - medio) / (0.01 * sr))
            audio[medio:fin] += 0.25 * fuerza * ruido
    audio += 0.05 * arco * rng.standard_normal(n)
    audio /= np.abs(audio).max() * 1.1

    destino = p.medio("audio", "prueba.wav")
    sf.write(destino, audio.astype(np.float32), sr)
    print(f"pista de prueba: {bpm} BPM, {duracion:.0f} s → {destino}")
    return destino
