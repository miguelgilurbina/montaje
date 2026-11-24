'use client';
// La consola de diales (direccion/CONSOLA.md): una fuente, una cadena de aparatos con sus perillas, la vista previa en
// la tarjeta de video, lo que se graba al girar con el video corriendo, el MIDI y el render del motor.
import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import Dial from '@/components/Dial';
import {Consola as Motor, EN_VIVO, claveLut, type Perillas, type Valor} from '@/lib/consola-gl';
import {aPistas, fusionar, tipoDe, valorEn, normal, desdeNormal, type PerillaInfo, type Punto, type Tipo} from '@/lib/consola-auto';

type AparatoInfo = {tipo: string; gesto: boolean; modulo: string; doc: string; perillas: Record<string, PerillaInfo>};
type CadenaGaleria = {id: string; frase: string; estado: string; aparatos: Record<string, unknown>[]; captura: string; semilla: number};
type Fuente = {ruta: string; carpeta: string; nombre: string; bytes: number};
type Salida = {ruta: string; tipo: 'render' | 'boceto'; cuando: number};
type Catalogo = {
  aparatos: Record<string, AparatoInfo>;
  cadenas: CadenaGaleria[];
  fuentes: Fuente[];
  sesiones: {nombre: string; cuando: number}[];
  salidas: Salida[];
};

type Modulo = {id: string; aparato: string; perillas: Perillas; activo: boolean};
type Auto = Record<string, Record<string, Punto[]>>;
type Mapeo = {entrada: string; canal: number; cc: number; modulo: string; perilla: string};
type Sesion = {
  version: 1;
  fuente: string | null;
  modulos: Modulo[];
  auto: Auto;
  midi: Mapeo[];
  entrada: number | null;
  salida: number | null;
  semilla: number;
};

const GUARDADA = 'montaje.consola.sesion';
const nuevoId = () => Math.random().toString(36).slice(2, 9);
const clave = (m: string, p: string) => `${m}.${p}`;
const medio = (ruta: string) => `/medios/${ruta.split('/').map(encodeURIComponent).join('/')}`;
const reloj = (t: number) => `${Math.floor(t / 60)}:${(t % 60).toFixed(2).padStart(5, '0')}`;

function sesionVacia(): Sesion {
  return {version: 1, fuente: null, modulos: [], auto: {}, midi: [], entrada: null, salida: null, semilla: 1};
}

/** Los aparatos de una cadena de la galería como módulos de la consola: sus perillas de fábrica con las de la cadena. */
function modulosDe(cadena: CadenaGaleria, aparatos: Record<string, AparatoInfo>): Modulo[] {
  return cadena.aparatos
    .filter((a) => typeof a.aparato === 'string' && aparatos[a.aparato as string])
    .map((a) => {
      const info = aparatos[a.aparato as string];
      const perillas: Perillas = {};
      for (const [k, p] of Object.entries(info.perillas)) perillas[k] = p.defecto as Valor;
      for (const [k, v] of Object.entries(a)) if (k !== 'aparato') perillas[k] = v as Valor;
      return {id: nuevoId(), aparato: a.aparato as string, perillas, activo: true};
    });
}

function fabrica(aparato: string, aparatos: Record<string, AparatoInfo>): Perillas {
  const perillas: Perillas = {};
  for (const [k, p] of Object.entries(aparatos[aparato]?.perillas ?? {})) perillas[k] = p.defecto as Valor;
  return perillas;
}

type Toque = {modulo: string; perilla: string; desde: number; ultimo: number; puntos: Punto[]};

export default function Consola() {
  const [cat, setCat] = useState<Catalogo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [s, setS] = useState<Sesion>(sesionVacia);
  const [vivos, setVivos] = useState<Record<string, Valor>>({});
  const [tiempo, setTiempo] = useState(0);
  const [duracion, setDuracion] = useState(0);
  const [corriendo, setCorriendo] = useState(false);
  const [grabando, setGrabando] = useState(false);
  const [bucle, setBucle] = useState(true);
  const [antes, setAntes] = useState(false);
  const [altoVista, setAltoVista] = useState(540);
  const [aprender, setAprender] = useState<null | 'perilla' | {modulo: string; perilla: string}>(null);
  const [midiEstado, setMidiEstado] = useState<string | null>(null);
  const [nombreSesion, setNombreSesion] = useState('');
  const [aviso, setAviso] = useState<string | null>(null);
  const [render, setRender] = useState<{log: string; corriendo: boolean; ruta: string | null} | null>(null);
  const [altoRender, setAltoRender] = useState(720);
  const [soloTramo, setSoloTramo] = useState(true);
  const [boceto, setBoceto] = useState<'grabando' | 'subiendo' | null>(null);
  const [rotos, setRotos] = useState<string[]>([]);
  const [viendo, setViendo] = useState<string | null>(null);
  // Hasta leer la sesión guardada no se guarda nada: si no, el estado vacío del primer dibujo la pisaría.
  const [restaurada, setRestaurada] = useState(false);

  const lienzo = useRef<HTMLCanvasElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const motor = useRef<Motor | null>(null);
  const historial = useRef<Sesion[]>([]);
  // Lo que lee el bucle de dibujo, sin esperar a React.
  const sRef = useRef(s);
  sRef.current = s;
  const vivosRef = useRef(vivos);
  vivosRef.current = vivos;
  const toques = useRef(new Map<string, Toque>());
  const grabandoRef = useRef(grabando);
  grabandoRef.current = grabando;
  const bucleRef = useRef(bucle);
  bucleRef.current = bucle;
  const antesRef = useRef(antes);
  antesRef.current = antes;
  const altoRef = useRef(altoVista);
  altoRef.current = altoVista;
  const grabador = useRef<MediaRecorder | null>(null);

  const aparatos = cat?.aparatos ?? {};

  // ── El catálogo y la última sesión ──
  const cargarCatalogo = useCallback(async (fresco = false) => {
    try {
      const r = await fetch(`/api/consola${fresco ? '?fresco=1' : ''}`);
      if (!r.ok) throw new Error(await r.text());
      setCat((await r.json()) as Catalogo);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    cargarCatalogo();
    try {
      const guardada = localStorage.getItem(GUARDADA);
      if (guardada) setS({...sesionVacia(), ...(JSON.parse(guardada) as Sesion)});
    } catch {
      /* sin almacenamiento: se empieza de cero */
    }
    setRestaurada(true);
  }, [cargarCatalogo]);

  useEffect(() => {
    if (!restaurada) return;
    try {
      localStorage.setItem(GUARDADA, JSON.stringify(s));
    } catch {
      /* sin almacenamiento */
    }
  }, [s, restaurada]);

  // ── El motor de la vista previa ──
  useEffect(() => {
    if (!lienzo.current) return;
    try {
      motor.current = new Motor(lienzo.current);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  // Las tablas de color que pide la cadena (la de cada `color` y las que aparecen en lo grabado) se piden al motor.
  const pidiendo = useRef(new Set<string>());
  useEffect(() => {
    const m = motor.current;
    if (!m) return;
    const claves = new Map<string, string>();
    for (const x of s.modulos) {
      if (x.aparato !== 'color') continue;
      const tablas = new Set<Valor>([x.perillas.tabla ?? null, ...(s.auto[x.id]?.tabla ?? []).map(([, v]) => v)]);
      for (const tabla of tablas) {
        const perillas = {...x.perillas, tabla};
        const clave = claveLut(perillas);
        const q = tabla === 'archivo' ? `archivo=${encodeURIComponent(String(x.perillas.archivo ?? ''))}` : `tabla=${encodeURIComponent(String(tabla))}`;
        if (tabla === 'archivo' && !x.perillas.archivo) continue;
        claves.set(clave, q);
      }
    }
    for (const [clave, q] of claves) {
      if (m.tieneLut(clave) || pidiendo.current.has(clave)) continue;
      pidiendo.current.add(clave);
      fetch(`/api/consola/lut?${q}`)
        .then(async (r) => {
          if (!r.ok) throw new Error(await r.text());
          const {n, datos} = (await r.json()) as {n: number; datos: number[]};
          m.fijarLut(clave, n, datos);
        })
        .catch((e) => setAviso(`la tabla ${clave}: ${(e as Error).message}`))
        .finally(() => pidiendo.current.delete(clave));
    }
  }, [s.modulos, s.auto]);

  /** Las perillas de cada módulo en el segundo t: las suyas, lo grabado encima y, si se está tocando, la mano. */
  const efectivas = useCallback(
    (t: number) => {
      const {modulos, auto} = sRef.current;
      const v = vivosRef.current;
      return modulos.map((m) => {
        const perillas: Perillas = {...m.perillas};
        for (const [p, puntos] of Object.entries(auto[m.id] ?? {})) {
          if (puntos.length) perillas[p] = valorEn(puntos, t, Boolean(aparatos[m.aparato]?.perillas[p]?.entero));
        }
        for (const p of Object.keys(m.perillas)) {
          const k = clave(m.id, p);
          if (k in v) perillas[p] = v[k];
        }
        return {aparato: m.aparato, perillas, activo: m.activo};
      });
    },
    [aparatos],
  );

  const cerrarToque = useCallback(
    (k: string, hasta: number) => {
      const toque = toques.current.get(k);
      toques.current.delete(k);
      if (!toque || toque.puntos.length < 2) return;
      setS((prev) => {
        const m = prev.modulos.find((x) => x.id === toque.modulo);
        if (!m) return prev;
        const info = aparatos[m.aparato]?.perillas[toque.perilla];
        if (!info) return prev;
        const tipo = tipoDe(info);
        const antesP = prev.auto[m.id]?.[toque.perilla] ?? [];
        const puntos = fusionar(antesP, toque.puntos, toque.desde, hasta, tipo, Boolean(info.entero));
        return {...prev, auto: {...prev.auto, [m.id]: {...(prev.auto[m.id] ?? {}), [toque.perilla]: puntos}}};
      });
    },
    [aparatos],
  );

  // ── El bucle de dibujo ──
  useEffect(() => {
    let id = 0;
    let ultimoEstado = 0;
    const paso = (ahora: number) => {
      const v = video.current;
      const m = motor.current;
      if (v && m && v.readyState >= 2) {
        const {entrada, salida} = sRef.current;
        if (bucleRef.current && salida !== null && v.currentTime >= salida - 0.01 && !v.paused) {
          v.currentTime = entrada ?? 0;
        }
        const t = v.currentTime;
        // Lo que se sostiene mientras corre el video se va escribiendo, aunque la mano no se mueva.
        if (!v.paused) {
          for (const [k, toque] of toques.current) {
            if (t < toque.ultimo - 0.05) {
              // El video volvió a empezar (el bucle): lo de esta vuelta se cierra y se abre otra.
              cerrarToque(k, toque.ultimo);
              toques.current.set(k, {...toque, desde: t, ultimo: t, puntos: [[t, vivosRef.current[k] ?? null]]});
            } else if (t - toque.ultimo >= 1 / 30) {
              toque.puntos.push([t, vivosRef.current[k] ?? toque.puntos[toque.puntos.length - 1][1]]);
              toque.ultimo = t;
            }
          }
        }
        try {
          m.dibujar(v, antesRef.current ? [] : efectivas(t), t, altoRef.current, !v.paused);
        } catch (e) {
          console.error(e);
        }
        if (ahora - ultimoEstado > 66) {
          ultimoEstado = ahora;
          setTiempo(t);
          if (m.rotos.size) setRotos([...m.rotos.keys()]);
        }
      }
      id = requestAnimationFrame(paso);
    };
    id = requestAnimationFrame(paso);
    return () => cancelAnimationFrame(id);
  }, [efectivas, cerrarToque]);

  // ── Cambios con historia ──
  const cambiar = (f: (prev: Sesion) => Sesion, guardar = true) => {
    setS((prev) => {
      if (guardar) historial.current = [...historial.current.slice(-30), prev];
      return f(prev);
    });
  };
  const deshacer = () => {
    const prev = historial.current.pop();
    if (prev) setS(prev);
    motor.current?.olvidar();
  };

  // ── Las perillas ──
  const tocar = (m: Modulo, p: string) => {
    const k = clave(m.id, p);
    const actual = efectivas(video.current?.currentTime ?? 0).find((_, i) => sRef.current.modulos[i]?.id === m.id)?.perillas[p] ?? null;
    setVivos((prev) => ({...prev, [k]: actual}));
    const v = video.current;
    if (grabandoRef.current && v && !v.paused) {
      toques.current.set(k, {modulo: m.id, perilla: p, desde: v.currentTime, ultimo: v.currentTime, puntos: [[v.currentTime, actual]]});
    }
  };
  const mover = (m: Modulo, p: string, valor: Valor) => {
    const k = clave(m.id, p);
    vivosRef.current = {...vivosRef.current, [k]: valor};
    setVivos((prev) => ({...prev, [k]: valor}));
    const toque = toques.current.get(k);
    const v = video.current;
    if (toque && v) {
      toque.puntos.push([v.currentTime, valor]);
      toque.ultimo = v.currentTime;
    }
  };
  const soltar = (m: Modulo, p: string) => {
    const k = clave(m.id, p);
    const valor = vivosRef.current[k];
    if (toques.current.has(k)) cerrarToque(k, video.current?.currentTime ?? 0);
    else if (!(sRef.current.auto[m.id]?.[p]?.length) && valor !== undefined) {
      // Sin nada grabado en esa perilla, lo girado queda como su valor.
      cambiar((prev) => ({...prev, modulos: prev.modulos.map((x) => (x.id === m.id ? {...x, perillas: {...x.perillas, [p]: valor}} : x))}), false);
    }
    setVivos((prev) => {
      const n = {...prev};
      delete n[k];
      return n;
    });
  };

  // ── MIDI ──
  const mapaRef = useRef<Mapeo[]>([]);
  mapaRef.current = s.midi;
  const aprenderRef = useRef(aprender);
  aprenderRef.current = aprender;
  const enganche = useRef(new Map<string, number>());
  const midiSoltar = useRef(new Map<string, number>());

  const alMidi = useCallback(
    (entrada: string, e: MIDIMessageEvent) => {
      const d = e.data;
      if (!d || d.length < 3 || (d[0] & 0xf0) !== 0xb0) return;
      const canal = d[0] & 0x0f;
      const cc = d[1];
      const n = d[2] / 127;
      const objetivo = aprenderRef.current;
      if (objetivo && objetivo !== 'perilla') {
        setS((prev) => ({
          ...prev,
          midi: [
            ...prev.midi.filter((x) => !(x.modulo === objetivo.modulo && x.perilla === objetivo.perilla) && !(x.entrada === entrada && x.canal === canal && x.cc === cc)),
            {entrada, canal, cc, ...objetivo},
          ],
        }));
        setAprender(null);
        setAviso(`atada: CC ${cc} (canal ${canal + 1}) → ${objetivo.perilla}`);
        return;
      }
      for (const mapa of mapaRef.current) {
        if (mapa.entrada !== entrada || mapa.canal !== canal || mapa.cc !== cc) continue;
        const m = sRef.current.modulos.find((x) => x.id === mapa.modulo);
        const info = m && aparatos[m.aparato]?.perillas[mapa.perilla];
        if (!m || !info) continue;
        const tipo = tipoDe(info);
        const k = clave(m.id, mapa.perilla);
        // Sin salto: la perilla de la pantalla espera a que la física pase por su valor.
        const actual = normal(tipo, efectivas(video.current?.currentTime ?? 0)[sRef.current.modulos.indexOf(m)]?.perillas[mapa.perilla] ?? null);
        const previa = enganche.current.get(k);
        const enganchada = previa === -1 || Math.abs(n - actual) < 0.03 || (previa !== undefined && (previa - actual) * (n - actual) <= 0);
        if (!enganchada) {
          enganche.current.set(k, n);
          continue;
        }
        enganche.current.set(k, -1);
        if (!midiSoltar.current.has(k)) tocar(m, mapa.perilla);
        else window.clearTimeout(midiSoltar.current.get(k));
        mover(m, mapa.perilla, desdeNormal(tipo, n));
        midiSoltar.current.set(
          k,
          window.setTimeout(() => {
            midiSoltar.current.delete(k);
            enganche.current.delete(k);
            soltar(m, mapa.perilla);
          }, 600),
        );
      }
    },
    [aparatos, efectivas],
  );

  const abrirMidi = async () => {
    if (!('requestMIDIAccess' in navigator)) {
      setMidiEstado('este navegador no tiene Web MIDI (Chrome o Firefox sí; Safari no)');
      return;
    }
    try {
      const acceso = await navigator.requestMIDIAccess();
      const atar = () => {
        const nombres: string[] = [];
        acceso.inputs.forEach((i) => {
          nombres.push(i.name ?? i.id);
          i.onmidimessage = (e) => alMidi(i.name ?? i.id, e as MIDIMessageEvent);
        });
        setMidiEstado(nombres.length ? `MIDI: ${nombres.join(', ')}` : 'MIDI abierto, sin controladores conectados');
      };
      atar();
      acceso.onstatechange = atar;
    } catch (e) {
      setMidiEstado(`sin permiso para MIDI: ${(e as Error).message}`);
    }
  };

  // ── Transporte y atajos ──
  const reproducir = () => {
    const v = video.current;
    if (!v) return;
    if (v.paused) v.play().catch(() => undefined);
    else v.pause();
  };

  useEffect(() => {
    const tecla = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA' || t.getAttribute('role') === 'slider')) return;
      const v = video.current;
      if (e.key === ' ') {
        e.preventDefault();
        reproducir();
      } else if (e.key === 'i' && v) setS((p) => ({...p, entrada: v.currentTime}));
      else if (e.key === 'o' && v) setS((p) => ({...p, salida: v.currentTime}));
      else if (e.key === 'r') setGrabando((g) => !g);
      else if (e.key === 'a') setAntes(true);
      else if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault();
        deshacer();
      }
    };
    const suelta = (e: KeyboardEvent) => {
      if (e.key === 'a') setAntes(false);
    };
    window.addEventListener('keydown', tecla);
    window.addEventListener('keyup', suelta);
    return () => {
      window.removeEventListener('keydown', tecla);
      window.removeEventListener('keyup', suelta);
    };
  });

  // ── La cadena ──
  const sumar = (aparato: string) => {
    if (!aparato) return;
    cambiar((p) => ({...p, modulos: [...p.modulos, {id: nuevoId(), aparato, perillas: fabrica(aparato, aparatos), activo: true}]}));
    motor.current?.olvidar();
  };
  const cargarCadena = (id: string) => {
    const c = cat?.cadenas.find((x) => x.id === id);
    if (!c) return;
    cambiar((p) => ({...p, modulos: modulosDe(c, aparatos), auto: {}, midi: [], semilla: c.semilla}));
    motor.current?.olvidar();
    setAviso(`cargada «${c.id}» (ctrl+z la deshace)`);
  };
  const quitar = (id: string) => {
    cambiar((p) => {
      const auto = {...p.auto};
      delete auto[id];
      return {...p, modulos: p.modulos.filter((m) => m.id !== id), auto, midi: p.midi.filter((x) => x.modulo !== id)};
    });
    motor.current?.olvidar();
  };
  const correr = (id: string, d: number) => {
    cambiar((p) => {
      const i = p.modulos.findIndex((m) => m.id === id);
      const j = i + d;
      if (i < 0 || j < 0 || j >= p.modulos.length) return p;
      const modulos = [...p.modulos];
      [modulos[i], modulos[j]] = [modulos[j], modulos[i]];
      return {...p, modulos};
    });
    motor.current?.olvidar();
  };
  const encender = (id: string) => {
    cambiar((p) => ({...p, modulos: p.modulos.map((m) => (m.id === id ? {...m, activo: !m.activo} : m))}));
    motor.current?.olvidar();
  };
  const borrarPista = (modulo: string, perilla: string) => {
    cambiar((p) => {
      const delModulo = {...(p.auto[modulo] ?? {})};
      delete delModulo[perilla];
      return {...p, auto: {...p.auto, [modulo]: delModulo}};
    });
  };

  // ── Sesiones ──
  const guardarSesion = async () => {
    const nombre = nombreSesion.trim().replace(/\s+/g, '-');
    if (!/^[\w.-]+$/.test(nombre)) {
      setAviso('el nombre de la sesión: letras, números, guiones y puntos');
      return;
    }
    const r = await fetch('/api/consola/sesion', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({nombre, sesion: s})});
    setAviso(r.ok ? `guardada «${nombre}»` : await r.text());
    if (r.ok) cargarCatalogo();
  };
  const abrirSesion = async (nombre: string) => {
    if (!nombre) return;
    const r = await fetch(`/api/consola/sesion?nombre=${encodeURIComponent(nombre)}`);
    if (!r.ok) {
      setAviso(await r.text());
      return;
    }
    const datos = (await r.json()) as Sesion;
    cambiar(() => ({...sesionVacia(), ...datos}));
    setNombreSesion(nombre);
    motor.current?.olvidar();
  };

  // ── El render del motor ──
  const renderizar = async () => {
    if (!s.fuente || !s.modulos.some((m) => m.activo)) return;
    const activos = s.modulos.filter((m) => m.activo);
    const cadena = {
      aparatos: activos.map((m) => {
        const info = aparatos[m.aparato];
        const salida: Record<string, unknown> = {aparato: m.aparato};
        // Sólo lo que se apartó del valor de fábrica: la receta queda corta y legible.
        for (const [k, v] of Object.entries(m.perillas)) {
          if (JSON.stringify(v) !== JSON.stringify(info?.perillas[k]?.defecto)) salida[k] = v;
        }
        return salida;
      }),
      semilla: s.semilla,
    };
    const tramo = soloTramo && s.entrada !== null && s.salida !== null && s.salida > s.entrada;
    setRender({log: '', corriendo: true, ruta: null});
    try {
      const r = await fetch('/api/consola/render', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          fuente: s.fuente,
          nombre: nombreSesion || s.fuente.split('/').pop()?.replace(/\.\w+$/, ''),
          cadena,
          automatizacion: aPistas(s.modulos, s.auto),
          desde: tramo ? s.entrada : undefined,
          hasta: tramo ? s.salida : undefined,
          alto: altoRender,
        }),
      });
      if (!r.ok || !r.body) {
        setRender({log: await r.text(), corriendo: false, ruta: null});
        return;
      }
      const lector = r.body.getReader();
      const dec = new TextDecoder();
      let log = '';
      for (;;) {
        const {done, value} = await lector.read();
        if (done) break;
        log += dec.decode(value, {stream: true});
        setRender({log, corriendo: true, ruta: null});
      }
      const ruta = /^→ (\S+)/.exec(log)?.[1] ?? null;
      const ok = log.includes('[fin: ok]');
      setRender({log, corriendo: false, ruta: ok ? ruta : null});
      if (ok) {
        cargarCatalogo();
        setViendo(ruta);
      }
    } catch (e) {
      setRender({log: (e as Error).message, corriendo: false, ruta: null});
    }
  };

  // ── El boceto: la vista previa grabada en el navegador ──
  const grabarBoceto = () => {
    const m = motor.current;
    const v = video.current;
    if (!m || !v) return;
    if (grabador.current) {
      grabador.current.stop();
      return;
    }
    const flujo = m.canvas.captureStream(30);
    const deVideo = (v as HTMLVideoElement & {captureStream?: () => MediaStream}).captureStream?.();
    deVideo?.getAudioTracks().forEach((pista) => flujo.addTrack(pista));
    const tipo = ['video/mp4;codecs=avc1', 'video/webm;codecs=vp9,opus', 'video/webm'].find((t) => MediaRecorder.isTypeSupported(t)) ?? '';
    const rec = new MediaRecorder(flujo, {mimeType: tipo, videoBitsPerSecond: 12_000_000});
    const trozos: Blob[] = [];
    rec.ondataavailable = (e) => e.data.size && trozos.push(e.data);
    rec.onstop = async () => {
      grabador.current = null;
      setBoceto('subiendo');
      const blob = new Blob(trozos, {type: rec.mimeType || 'video/webm'});
      const r = await fetch(`/api/consola/boceto?nombre=${encodeURIComponent(nombreSesion || 'boceto')}`, {
        method: 'POST',
        headers: {'Content-Type': blob.type.split(';')[0]},
        body: blob,
      });
      setBoceto(null);
      if (r.ok) {
        const {ruta} = (await r.json()) as {ruta: string};
        setAviso(`boceto guardado: ${ruta}`);
        cargarCatalogo();
      } else setAviso(await r.text());
    };
    rec.start(500);
    grabador.current = rec;
    setBoceto('grabando');
    if (v.paused) v.play().catch(() => undefined);
  };

  // ── Lo que se muestra ──
  const fuentesPorCarpeta = useMemo(() => {
    const g = new Map<string, Fuente[]>();
    for (const f of cat?.fuentes ?? []) g.set(f.carpeta, [...(g.get(f.carpeta) ?? []), f]);
    return [...g.entries()];
  }, [cat]);

  const pistas = useMemo(
    () =>
      s.modulos.flatMap((m) =>
        Object.entries(s.auto[m.id] ?? {})
          .filter(([, p]) => p.length)
          .map(([perilla, puntos]) => ({m, perilla, puntos, tipo: tipoDe(aparatos[m.aparato]?.perillas[perilla] ?? {defecto: null, rango: null})})),
      ),
    [s, aparatos],
  );

  // Lo que muestran los diales: se recalcula con el tiempo, la sesión y la mano (`efectivas` los lee por referencia).
  const efectivasAhora = useMemo(() => efectivas(tiempo), [efectivas, tiempo, s, vivos]);

  if (error && !cat) {
    return (
      <div className="tablero-vacio">
        <h1>consola</h1>
        <p className="error">{error}</p>
      </div>
    );
  }

  return (
    <div className="tablero">
      <header className="tablero-cabeza">
        <a href="/" className="dato">
          ← panel
        </a>
        <h1>consola</h1>
        <select
          value={s.fuente ?? ''}
          onChange={(e) => {
            setS((p) => ({...p, fuente: e.target.value || null, entrada: null, salida: null}));
            motor.current?.olvidar();
          }}
          aria-label="fuente"
        >
          <option value="">la fuente…</option>
          {fuentesPorCarpeta.map(([carpeta, fs]) => (
            <optgroup key={carpeta} label={carpeta}>
              {fs.map((f) => (
                <option key={f.ruta} value={f.ruta}>
                  {f.nombre}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
        <select value="" onChange={(e) => cargarCadena(e.target.value)} aria-label="cadena de la galería">
          <option value="">partir de una cadena de la galería…</option>
          {(cat?.cadenas ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.id} · {c.estado}
            </option>
          ))}
        </select>
        <span className="tablero-sesion">
          <input value={nombreSesion} onChange={(e) => setNombreSesion(e.target.value)} placeholder="nombre de la sesión" aria-label="nombre de la sesión" />
          <button type="button" onClick={guardarSesion}>
            guardar
          </button>
          <select value="" onChange={(e) => abrirSesion(e.target.value)} aria-label="abrir una sesión">
            <option value="">abrir…</option>
            {(cat?.sesiones ?? []).map((x) => (
              <option key={x.nombre} value={x.nombre}>
                {x.nombre}
              </option>
            ))}
          </select>
          <button type="button" onClick={deshacer} title="deshacer (ctrl+z)">
            deshacer
          </button>
        </span>
      </header>

      <section className="tablero-vista">
        <div className="tablero-pantalla">
          <canvas ref={lienzo} />
          {!s.fuente ? <p className="tablero-sin-fuente dato">Elige una fuente arriba.</p> : null}
          {antes ? <span className="tablero-antes">tal cual</span> : null}
          {boceto === 'grabando' ? <span className="tablero-rec">● boceto</span> : null}
        </div>
        <video
          ref={video}
          src={s.fuente ? medio(s.fuente) : undefined}
          className="tablero-fuente"
          crossOrigin="anonymous"
          playsInline
          preload="auto"
          onLoadedMetadata={(e) => setDuracion(e.currentTarget.duration)}
          onPlay={() => setCorriendo(true)}
          onPause={() => {
            setCorriendo(false);
            for (const k of [...toques.current.keys()]) cerrarToque(k, video.current?.currentTime ?? 0);
          }}
          onEnded={() => {
            const v = video.current;
            if (v && bucleRef.current) {
              v.currentTime = sRef.current.entrada ?? 0;
              v.play().catch(() => undefined);
            }
          }}
        />

        <div className="tablero-transporte">
          <button type="button" onClick={reproducir} className="tablero-boton-grande" disabled={!s.fuente} title="reproducir o parar (espacio)">
            {corriendo ? '❚❚' : '▶'}
          </button>
          <span className="dato tablero-reloj">
            {reloj(tiempo)} / {reloj(duracion || 0)}
          </span>
          <div className="tablero-barra">
            <input
              type="range"
              min={0}
              max={duracion || 1}
              step={0.01}
              value={tiempo}
              onChange={(e) => {
                if (video.current) video.current.currentTime = Number(e.target.value);
              }}
              aria-label="posición"
            />
            {s.entrada !== null && duracion ? <span className="tablero-marca entrada" style={{left: `${(s.entrada / duracion) * 100}%`}} /> : null}
            {s.salida !== null && duracion ? <span className="tablero-marca salida" style={{left: `${(s.salida / duracion) * 100}%`}} /> : null}
            {pistas.length && duracion ? (
              <svg className="tablero-pistas-mini" viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true">
                {pistas.map(({m, perilla, puntos, tipo}) => (
                  <polyline
                    key={clave(m.id, perilla)}
                    points={puntos.map(([t, v]) => `${((t / duracion) * 100).toFixed(2)},${(10 - normal(tipo, v) * 9.5).toFixed(2)}`).join(' ')}
                  />
                ))}
              </svg>
            ) : null}
          </div>
          <button type="button" onClick={() => video.current && setS((p) => ({...p, entrada: video.current!.currentTime}))} title="marca de entrada (i)">
            entrada
          </button>
          <button type="button" onClick={() => video.current && setS((p) => ({...p, salida: video.current!.currentTime}))} title="marca de salida (o)">
            salida
          </button>
          <button type="button" onClick={() => setS((p) => ({...p, entrada: null, salida: null}))} disabled={s.entrada === null && s.salida === null}>
            sin marcas
          </button>
          <label className="tablero-casilla">
            <input type="checkbox" checked={bucle} onChange={(e) => setBucle(e.target.checked)} /> en bucle
          </label>
          <button
            type="button"
            className={antes ? 'activo' : ''}
            onPointerDown={() => setAntes(true)}
            onPointerUp={() => setAntes(false)}
            onPointerLeave={() => setAntes(false)}
            title="mientras se sostiene, la fuente tal cual (o la tecla a)"
          >
            antes
          </button>
          <label className="tablero-casilla dato">
            vista
            <select value={altoVista} onChange={(e) => setAltoVista(Number(e.target.value))}>
              {[360, 540, 720].map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="tablero-acciones">
          <button type="button" className={`tablero-grabar${grabando ? ' activo' : ''}`} onClick={() => setGrabando((g) => !g)} title="grabar lo que se gira con el video corriendo (r)">
            ● {grabando ? 'grabando' : 'grabar'}
          </button>
          <button type="button" onClick={abrirMidi}>
            MIDI
          </button>
          <button type="button" className={aprender ? 'activo' : ''} onClick={() => setAprender(aprender ? null : 'perilla')} disabled={!midiEstado || midiEstado.startsWith('sin') || midiEstado.startsWith('este')}>
            {aprender === null ? 'aprender' : aprender === 'perilla' ? 'clic en una perilla…' : `mueve un control para ${aprender.perilla}…`}
          </button>
          <button type="button" onClick={grabarBoceto} disabled={!s.fuente || boceto === 'subiendo'} className={boceto === 'grabando' ? 'activo' : ''}>
            {boceto === 'grabando' ? '■ parar el boceto' : boceto === 'subiendo' ? 'guardando…' : 'boceto'}
          </button>
          <span className="tablero-render">
            <label className="tablero-casilla dato">
              alto
              <select value={altoRender} onChange={(e) => setAltoRender(Number(e.target.value))}>
                {[540, 720, 1080].map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </label>
            <label className="tablero-casilla dato">
              <input type="checkbox" checked={soloTramo} onChange={(e) => setSoloTramo(e.target.checked)} disabled={s.entrada === null || s.salida === null} /> sólo entre las marcas
            </label>
            <button type="button" className="tablero-renderizar" onClick={renderizar} disabled={!s.fuente || !s.modulos.some((m) => m.activo) || render?.corriendo}>
              {render?.corriendo ? 'renderizando…' : 'renderizar con el motor'}
            </button>
          </span>
        </div>
        {midiEstado ? <p className="dato">{midiEstado}</p> : null}
        {aviso ? (
          <p className="dato tablero-aviso" onClick={() => setAviso(null)}>
            {aviso}
          </p>
        ) : null}
        {rotos.length ? <p className="error">sin vista previa en esta tarjeta: {rotos.join(', ')} (pasan sin tocar; el render no cambia)</p> : null}

        {pistas.length ? (
          <div className="tablero-lista">
            <h2>lo grabado</h2>
            {pistas.map(({m, perilla, puntos}) => (
              <div key={clave(m.id, perilla)} className="tablero-pista">
                <span>
                  {m.aparato} · <b>{perilla}</b>
                </span>
                <span className="dato">
                  {puntos.length} puntos, de {reloj(puntos[0][0])} a {reloj(puntos[puntos.length - 1][0])}
                </span>
                <button type="button" onClick={() => borrarPista(m.id, perilla)}>
                  borrar
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="dato">
            Con <b>grabar</b> encendido y el video corriendo, lo que se gira queda escrito; al soltar, la perilla vuelve a leer lo
            grabado.
          </p>
        )}

        {render ? (
          <div className="tablero-lista">
            <h2>render</h2>
            <pre className="tablero-log">{render.log.split('\n').slice(-14).join('\n')}</pre>
          </div>
        ) : null}

        {cat?.salidas.length ? (
          <div className="tablero-lista">
            <h2>lo que salió</h2>
            {viendo ? <video key={viendo} src={medio(viendo)} controls className="tablero-salida" /> : null}
            {cat.salidas.slice(0, 12).map((x) => (
              <button type="button" key={x.ruta} className={`tablero-salida-fila${viendo === x.ruta ? ' activo' : ''}`} onClick={() => setViendo(x.ruta)}>
                <span>{x.ruta.split('/').pop()}</span>
                <span className="dato">{x.tipo}</span>
              </button>
            ))}
          </div>
        ) : null}
      </section>

      <section className="tablero-rack">
        <div className="tablero-sumar">
          <select value="" onChange={(e) => sumar(e.target.value)} aria-label="sumar un aparato">
            <option value="">sumar un aparato…</option>
            {Object.keys(aparatos)
              .sort()
              .map((a) => (
                <option key={a} value={a}>
                  {a}
                  {EN_VIVO.has(a) ? '' : ' (sólo en el render)'}
                </option>
              ))}
          </select>
          <button type="button" className="dato" onClick={() => cargarCatalogo(true)} title="volver a preguntarle al motor por los aparatos">
            ↻
          </button>
        </div>
        {!s.modulos.length ? <p className="dato">La cadena está vacía: suma aparatos o parte de una cadena de la galería.</p> : null}
        {s.modulos.map((m, i) => {
          const info = aparatos[m.aparato];
          const vivo = EN_VIVO.has(m.aparato) && !rotos.includes(m.aparato);
          const perillas = efectivasAhora[i]?.perillas ?? m.perillas;
          const fijas = Object.entries(info?.perillas ?? {}).filter(([, p]) => tipoDe(p).clase === 'fija');
          return (
            <article key={m.id} className={`tablero-modulo${m.activo ? '' : ' apagado'}`}>
              <header>
                <button type="button" className={`tablero-led${m.activo ? ' encendido' : ''}`} onClick={() => encender(m.id)} title={m.activo ? 'apagar (pasa sin tocar)' : 'encender'} aria-label={`encender ${m.aparato}`} />
                <b>{m.aparato}</b>
                <span className={`chip${vivo ? '' : ' chip-render'}`}>{vivo ? 'en vivo' : 'sólo en el render'}</span>
                <span className="tablero-mover">
                  <button type="button" onClick={() => correr(m.id, -1)} disabled={i === 0} aria-label="subir">
                    ↑
                  </button>
                  <button type="button" onClick={() => correr(m.id, 1)} disabled={i === s.modulos.length - 1} aria-label="bajar">
                    ↓
                  </button>
                  <button type="button" onClick={() => quitar(m.id)} aria-label="quitar">
                    ×
                  </button>
                </span>
              </header>
              {info?.doc ? <p className="dato tablero-doc">{info.doc}</p> : null}
              <div className="tablero-diales">
                {Object.entries(info?.perillas ?? {}).map(([p, pi]) => {
                  const tipo: Tipo = tipoDe(pi);
                  if (tipo.clase === 'fija') return null;
                  const k = clave(m.id, p);
                  return (
                    <Dial
                      key={p}
                      nombre={p}
                      tipo={tipo}
                      valor={perillas[p] ?? null}
                      defecto={pi.defecto as Valor}
                      automatizada={Boolean(s.auto[m.id]?.[p]?.length)}
                      tocada={k in vivos}
                      aprendiendo={aprender === 'perilla'}
                      atada={s.midi.some((x) => x.modulo === m.id && x.perilla === p)}
                      onTocar={() => tocar(m, p)}
                      onCambio={(v) => mover(m, p, v)}
                      onSoltar={() => soltar(m, p)}
                      onAprender={() => setAprender({modulo: m.id, perilla: p})}
                    />
                  );
                })}
              </div>
              {fijas
                .filter(([, pi]) => typeof pi.defecto === 'string')
                .map(([k]) => (
                  <label key={k} className="tablero-texto dato">
                    {k}
                    <input
                      defaultValue={String(m.perillas[k] ?? '')}
                      placeholder={k === 'archivo' ? 'luts/mi-tabla.cube (dentro de los medios)' : ''}
                      onKeyDown={(e) => e.key === 'Enter' && (e.target as HTMLInputElement).blur()}
                      onBlur={(e) => {
                        const v = e.target.value;
                        if (v !== String(m.perillas[k] ?? '')) {
                          cambiar((prev) => ({...prev, modulos: prev.modulos.map((x) => (x.id === m.id ? {...x, perillas: {...x.perillas, [k]: v}} : x))}));
                        }
                      }}
                    />
                  </label>
                ))}
              {fijas.some(([, pi]) => typeof pi.defecto !== 'string') ? (
                <p className="dato tablero-doc">
                  fijas (se escriben en la receta):{' '}
                  {fijas
                    .filter(([, pi]) => typeof pi.defecto !== 'string')
                    .map(([k]) => k)
                    .join(', ')}
                </p>
              ) : null}
            </article>
          );
        })}
      </section>
    </div>
  );
}
