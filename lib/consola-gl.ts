// La vista previa de la consola: la cadena de aparatos aproximada en la tarjeta de video (WebGL2), a tiempo real.
//
// Miguel, el 2026-11-23: «podríamos además de tener una galería, tener un espacio para hacer edición manual de vídeo.
// Como modificación análoga de vídeo. Con diales manuales». El motor de Python simula cada aparato en su señal y es
// lento (segundos por cuadro); aquí cada aparato es un shader que se le parece, para girar las perillas y ver al
// instante. Lo que se renderiza al final lo hace el motor, con las mismas perillas y los mismos movimientos: la vista
// previa es una aproximación y lo dice.
//
// Cada aparato vivo es una pasada: lee la imagen que le deja el anterior (uImg), el video tal cual (uOrig, con mipmaps:
// su color medio sirve al tintado automático) y lo que esa misma pasada dibujó en el cuadro anterior (uPrev: el fósforo,
// el eco, la realimentación, el estrobo). Sus perillas llegan como uniformes con el nombre de la perilla (`u_nieve`).

export type Valor = number | string | boolean | null | unknown[];
export type Perillas = Record<string, Valor>;

const CABECERA = `#version 300 es
precision highp float;
in vec2 vUv;
out vec4 color;
uniform sampler2D uImg;
uniform sampler2D uOrig;
uniform sampler2D uPrev;
uniform vec2 uRes;
uniform float uT;
uniform float uK;
uniform float uHold;
float hash(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float hash3(vec3 p) { return hash(p.xy + p.z * 17.17); }
float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }
vec3 aYiq(vec3 c) { return mat3(0.299, 0.5959, 0.2115, 0.587, -0.2746, -0.5227, 0.114, -0.3213, 0.3112) * c; }
vec3 aRgb(vec3 y) { return mat3(1.0, 1.0, 1.0, 0.956, -0.272, -1.106, 0.621, -0.647, 1.703) * y; }
float suave(float x) { return x * x * (3.0 - 2.0 * x); }
float ruidoSuave(float t, float s) { float a = floor(t), f = fract(t); return mix(hash(vec2(a, s)), hash(vec2(a + 1.0, s)), suave(f)); }
`;

// Cada aparato: su fragment shader (sin cabecera) y qué perillas son números (el resto se pasa como índice de opción).
type Def = {frag: string; opciones?: Record<string, string[]>; memoria?: boolean};

export const VIVOS: Record<string, Def> = {
  // La cinta: el color corrido y borroneado (más cuanto más lenta la cinta), el halo del realce, el temblor de las
  // líneas, el ruido de luma y de color (a rayitas, como en la cinta), las rayas donde falta óxido, la costura del
  // cabezal abajo y la banda del tracking que sube.
  cinta: {
    opciones: {formato: ['SP', 'LP', 'EP', 'S-VHS', 'Betamax', 'Video8', 'Hi8']},
    frag: `
uniform float u_formato, u_desgaste, u_temblor, u_tracking, u_cabezal, u_cabezal_lineas, u_realce, u_retraso_croma, u_saturacion, u_arrugas, u_generaciones;
float anchoDeBanda(float f) {
  if (f < 0.5) return 1.0;    // SP
  if (f < 1.5) return 1.4;    // LP
  if (f < 2.5) return 1.9;    // EP: la más lenta, la más borrosa
  if (f < 3.5) return 0.55;   // S-VHS
  if (f < 4.5) return 0.9;    // Betamax
  if (f < 5.5) return 1.2;    // Video8
  return 0.7;                 // Hi8
}
void main() {
  vec2 uv = vUv;
  float esc = uRes.y / 480.0;
  float linea = floor(uv.y * 480.0);
  float k = floor(uK);
  float bw = anchoDeBanda(u_formato) * (1.0 + 0.35 * (u_generaciones - 1.0));
  float temblor = (ruidoSuave(uT * 7.0 + linea * 0.05, 3.0) - 0.5) * 0.004 * u_temblor;
  // La banda del tracking: sube despacio; dentro, las líneas se corren y hay nieve.
  float banda = fract(1.0 - uT * 0.07);
  float enBanda = u_tracking * smoothstep(0.07, 0.0, abs(uv.y - banda));
  temblor += (hash(vec2(linea, k)) - 0.5) * 0.08 * enBanda;
  // La costura del cabezal: las últimas líneas corridas.
  float costura = step(1.0 - u_cabezal_lineas / 480.0, 1.0 - uv.y) * u_cabezal;
  temblor += costura * (0.02 + 0.03 * hash(vec2(linea, k + 1.0)));
  // Las arrugas: a ratos, un salto de toda la imagen.
  float arruga = step(0.985 - u_arrugas * 0.002, hash(vec2(floor(uT * 12.0), 9.0)));
  uv.y += arruga * 0.03 * (hash(vec2(k, 2.0)) - 0.5);
  uv.x += temblor;
  float px = 1.0 / uRes.x;
  float blando = bw * esc * px;
  vec3 c0 = aYiq(texture(uImg, uv).rgb);
  float y = 0.0, peso = 0.0;
  for (int i = -3; i <= 3; i++) {
    float w = exp(-float(i * i) / 4.5);
    y += aYiq(texture(uImg, uv + vec2(float(i) * blando, 0.0)).rgb).x * w;
    peso += w;
  }
  y /= peso;
  y += u_realce * (c0.x - y) * 1.2 + u_realce * 0.05 * (y - aYiq(texture(uImg, uv - vec2(3.0 * blando, 0.0)).rgb).x);
  // El color: corrido a la derecha y muy borroneado (la cinta guarda el color con poco ancho de banda).
  float corre = (4.0 + u_retraso_croma) * esc * px * bw;
  vec2 q = vec2(0.0);
  for (int i = -5; i <= 5; i++) { q += aYiq(texture(uImg, uv - vec2(corre + float(i) * 3.0 * bw * esc * px, 0.0)).rgb).yz; }
  q /= 11.0;
  q *= u_saturacion * (1.0 - 0.2 * u_desgaste);
  // El ruido: de luma, fino; de color, a rayitas horizontales (cada línea su ruido, estirado a lo largo).
  vec2 celda = vec2(floor(vUv.x * uRes.x / (1.5 * esc)), linea);
  float ruidoY = (hash(celda + k * 1.3) - 0.5) * (0.04 + 0.16 * u_desgaste + 0.04 * u_generaciones) * sqrt(bw);
  vec2 celdaC = vec2(floor(vUv.x * uRes.x / (6.0 * esc * bw)), linea);
  vec2 ruidoC = vec2(hash(celdaC + k * 2.1), hash(celdaC + k * 3.7 + 11.0)) - 0.5;
  q += ruidoC * (0.03 + 0.28 * u_desgaste) * (0.6 + 0.4 * bw);
  float raya = step(1.0 - 0.002 * u_desgaste * bw, hash(vec2(linea, floor(vUv.x * 30.0) + k * 7.0)));
  y = y + ruidoY + raya * 0.7 + enBanda * (hash(vUv * uRes + k * 3.1) - 0.5) * 0.7 + costura * (hash(vUv * 900.0 + k) - 0.5) * 0.3;
  color = vec4(clamp(aRgb(vec3(y, q)), 0.0, 1.0), 1.0);
}`,
  },
  // La antena: la nieve de la señal débil, la barra del zumbido que sube, la imagen que rueda y las líneas que se
  // tuercen cuando se pierde el sincronismo.
  antena: {
    frag: `
uniform float u_nieve, u_zumbido, u_rodar, u_desenganche;
void main() {
  vec2 uv = vUv;
  uv.y = fract(uv.y + uT * u_rodar * 0.35);
  float borrado = smoothstep(0.0, 0.03, uv.y) * smoothstep(0.0, 0.03, 1.0 - uv.y);
  borrado = mix(1.0, borrado, step(0.001, abs(u_rodar)));
  uv.x += u_desenganche * (0.06 * sin(uv.y * 24.0 + uT * 3.0) + 0.12 * (uv.y - 0.5) * sin(uT * 0.7));
  vec3 c = texture(uImg, fract(uv)).rgb;
  float k = floor(uK);
  vec3 nieve = vec3(hash(vUv * uRes + k), hash(vUv * uRes + k + 1.7), hash(vUv * uRes + k + 3.3));
  nieve = mix(vec3(luma(nieve)), nieve, 0.35);
  c = mix(c, nieve, clamp(u_nieve * 1.1, 0.0, 0.95));
  float barra = smoothstep(0.18, 0.0, abs(fract(vUv.y + uT * 0.05) - 0.5) - 0.1);
  c *= 1.0 - u_zumbido * 0.9 * barra;
  color = vec4(c * borrado, 1.0);
}`,
  },
  // El televisor: el vidrio curvo, las líneas de barrido, la máscara de fósforos, la convergencia, el resplandor y la
  // persistencia del fósforo.
  pantalla: {
    opciones: {mascara: ['rejilla', 'puntos', 'ranuras', 'ninguna']},
    memoria: true,
    frag: `
uniform float u_lineas, u_mascara, u_mascara_fuerza, u_curva, u_brillo, u_persistencia, u_convergencia, u_vineta, u_gamma, u_parpadeo;
void main() {
  vec2 c = vUv * 2.0 - 1.0;
  c *= 1.0 + u_curva * dot(c, c) * 1.5;
  vec2 uv = c * 0.5 + 0.5;
  if (any(lessThan(uv, vec2(0.0))) || any(greaterThan(uv, vec2(1.0)))) { color = vec4(0.0, 0.0, 0.0, 1.0); return; }
  float px = 1.0 / uRes.x;
  float conv = u_convergencia * px;
  vec3 img = vec3(texture(uImg, uv + vec2(conv, 0.0)).r, texture(uImg, uv).g, texture(uImg, uv - vec2(conv, 0.0)).b);
  img = pow(img, vec3(u_gamma / 2.2));
  float linea = 0.5 + 0.5 * cos(uv.y * uRes.y * 3.14159 * 480.0 / uRes.y);
  img *= mix(1.0, 0.45 + 0.55 * linea, u_lineas * (1.0 - 0.5 * luma(img)));
  vec2 p = floor(gl_FragCoord.xy);
  vec3 m = vec3(1.0);
  if (u_mascara < 0.5) { float s = mod(p.x, 3.0); m = vec3(s == 0.0, s == 1.0, s == 2.0) * 1.0 + 0.35; }
  else if (u_mascara < 1.5) { float s = mod(p.x + mod(p.y, 2.0) * 1.5, 3.0); m = vec3(s < 1.0, s >= 1.0 && s < 2.0, s >= 2.0) + 0.35; }
  else if (u_mascara < 2.5) { float s = mod(p.x, 3.0); m = vec3(s == 0.0, s == 1.0, s == 2.0) * step(0.5, mod(p.y + floor(p.x / 3.0) * 2.0, 4.0)) + 0.35; }
  img *= mix(vec3(1.0), m, u_mascara_fuerza);
  vec3 halo = textureLod(uImg, uv, 4.0).rgb;
  img += halo * halo * u_brillo * 0.6;
  img *= 1.0 - u_vineta * 0.6 * dot(c, c);
  img *= 1.0 - u_parpadeo * 0.08 * sin(uT * 60.0);
  vec3 antes = texture(uPrev, vUv).rgb;
  img = max(img, antes * u_persistencia);
  vec2 esq = abs(c) - (1.0 - 0.06);
  float redondo = smoothstep(0.06, 0.05, length(max(esq, 0.0)));
  color = vec4(clamp(img, 0.0, 1.0) * redondo, 1.0);
}`,
  },
  // La película: el color de la emulsión, la exposición y el filtro, el halo rojo de las luces, el grano, el cuadro
  // que baila, el parpadeo, la viñeta, el polvo y las rayas; con `cuadros`, el paso a saltitos.
  pelicula: {
    opciones: {
      formato: ['super8', '8mm', '16mm', '35mm'],
      emulsion: ['kodachrome', 'ektachrome', 'blanco-y-negro', 'kodak-gold', 'fuji-superia'],
      balance: ['correcto', 'naranja', 'azul'],
    },
    memoria: true,
    frag: `
uniform float u_formato, u_emulsion, u_balance, u_exposicion, u_grano, u_halo, u_vaiven, u_parpadeo, u_vineta, u_polvo, u_rayas, u_desvanecido, u_cuadros;
void main() {
  if (uHold > 0.5) { color = texture(uPrev, vUv); return; }
  float j = floor(uK);
  vec2 baila = (vec2(ruidoSuave(uT * 3.0, 1.0), ruidoSuave(uT * 3.0, 2.0)) - 0.5) * 0.006 * u_vaiven + (vec2(hash(vec2(j, 5.0)), hash(vec2(j, 6.0))) - 0.5) * 0.002 * u_vaiven;
  vec2 uv = vUv + baila;
  vec3 c = texture(uImg, uv).rgb;
  vec3 bal = u_balance < 0.5 ? vec3(1.0) : (u_balance < 1.5 ? vec3(1.0, 0.74, 0.44) : vec3(0.66, 0.86, 1.22));
  c *= bal * exp2(u_exposicion);
  float contraste = 1.25, sat = 1.3; vec3 eq = vec3(1.05, 1.0, 0.92);
  if (u_emulsion > 0.5 && u_emulsion < 1.5) { contraste = 1.05; sat = 1.08; eq = vec3(0.95, 1.0, 1.08); }
  else if (u_emulsion > 1.5 && u_emulsion < 2.5) { contraste = 1.3; sat = 0.0; eq = vec3(1.0); }
  else if (u_emulsion > 2.5 && u_emulsion < 3.5) { contraste = 0.92; sat = 1.15; eq = vec3(1.08, 1.02, 0.86); }
  else if (u_emulsion > 3.5) { contraste = 0.95; sat = 1.18; eq = vec3(0.98, 1.05, 1.0); }
  c *= eq;
  float l = luma(c);
  c = mix(vec3(l), c, sat);
  c = clamp((c - 0.5) * contraste + 0.5, 0.0, 1.0);
  c = mix(c, vec3(c.r * 1.08 + 0.04, c.g * 0.72, c.b * 0.78), u_desvanecido);
  vec3 luces = max(textureLod(uImg, uv, 5.0).rgb - 0.65, 0.0);
  c += vec3(1.0, 0.35, 0.15) * luma(luces) * u_halo * 0.9;
  c *= 1.0 + (hash(vec2(j, 11.0)) - 0.5) * 0.12 * u_parpadeo;
  float celdaGrano = (2.4 - 0.45 * u_formato) * uRes.y / 540.0;   // super 8 grueso, 35 mm fino
  float g = (hash(floor(vUv * uRes / celdaGrano) + j * 1.37) - 0.5) * (0.15 - 0.025 * u_formato) * u_grano;
  c += g;
  vec2 d = vUv - 0.5;
  c *= 1.0 - u_vineta * 1.6 * dot(d, d);
  float polvo = step(1.0 - 0.0006 * u_polvo, hash(floor(vUv * uRes / 2.0) + j * 3.7));
  c *= 1.0 - polvo * 0.85;
  float raya = step(0.985, hash(vec2(floor(vUv.x * 300.0), floor(uT * 1.5)))) * step(0.6, hash(vec2(floor(uT * 1.5), 1.0))) * u_rayas;
  c = mix(c, vec3(0.85), clamp(raya * 0.5, 0.0, 0.6));
  color = vec4(clamp(c, 0.0, 1.0), 1.0);
}`,
  },
  // El color del cine mudo: tintado (por la escena, con `auto`), virado, los dos colores y los dos colores que se corren.
  tinte: {
    opciones: {modo: ['tintado', 'virado', 'dos-colores', 'kinemacolor'], tinta: ['auto', 'azul', 'ambar', 'rojo', 'verde', 'sepia', 'rosa']},
    memoria: true,
    frag: `
uniform float u_modo, u_tinta, u_fuerza;
vec3 tinta(float i) {
  if (i < 1.5) return vec3(0.40, 0.60, 1.00);
  if (i < 2.5) return vec3(1.00, 0.76, 0.42);
  if (i < 3.5) return vec3(1.00, 0.42, 0.32);
  if (i < 4.5) return vec3(0.62, 1.00, 0.60);
  if (i < 5.5) return vec3(1.00, 0.86, 0.66);
  return vec3(1.00, 0.70, 0.80);
}
void main() {
  vec3 c = texture(uImg, vUv).rgb;
  float l = luma(c);
  vec3 sale;
  if (u_modo < 0.5) {
    vec3 t = tinta(u_tinta);
    if (u_tinta < 0.5) {
      vec3 m = textureLod(uOrig, vec2(0.5), 12.0).rgb;
      float lm = luma(m);
      float az = 1.0 / (1.0 + exp(-(0.28 - lm) / 0.04)), am = 1.0 / (1.0 + exp(-((m.r - m.b) - 0.05) / 0.03)),
            ve = 1.0 / (1.0 + exp(-((m.g - (m.r + m.b) * 0.5) - 0.04) / 0.02));
      t = (az * tinta(1.0) + am * tinta(2.0) + ve * tinta(4.0) + 0.35 * tinta(5.0)) / (az + am + ve + 0.35);
    }
    sale = l * (t * u_fuerza + (1.0 - u_fuerza));
  } else if (u_modo < 1.5) {
    vec3 oscuro = u_tinta > 0.5 && u_tinta < 1.5 ? vec3(0.08, 0.2, 0.42) : (u_tinta > 3.5 && u_tinta < 4.5 ? vec3(0.1, 0.3, 0.16) : (u_tinta > 2.5 && u_tinta < 3.5 ? vec3(0.42, 0.1, 0.08) : vec3(0.36, 0.2, 0.09)));
    sale = 1.0 - (1.0 - l) * ((1.0 - oscuro) * u_fuerza + (1.0 - u_fuerza));
  } else if (u_modo < 2.5) {
    float a = 1.0 - c.r, b = 1.0 - c.g;
    sale = mix(vec3(l), vec3(1.0 - a, (1.0 - b) * (1.0 - 0.08 * a), (1.0 - 0.3 * a) * (1.0 - 0.85 * b)), u_fuerza);
  } else {
    // El verde llega un cuadro tarde (la rueda de filtros): lo de este cuadro se guarda en el alfa de la memoria.
    vec4 antes = texture(uPrev, vUv);
    float verde = antes.a > 0.0 ? antes.a : c.g;
    sale = mix(vec3(l), vec3(c.r, verde, 0.45 * verde + 0.15 * c.r), u_fuerza);
    color = vec4(clamp(sale, 0.0, 1.0), max(c.g, 1.0 / 255.0));
    return;
  }
  color = vec4(clamp(sale, 0.0, 1.0), 1.0);
}`,
  },
  // La imprenta: la serigrafía en tres tintas, la riso en dos tramas, el diario en cuatro, la fotocopia.
  imprenta: {
    opciones: {tecnica: ['serigrafia', 'riso', 'trama', 'fotocopia']},
    frag: `
uniform float u_tecnica, u_registro, u_trama, u_papel, u_grano, u_copias;
float puntos(float v, vec2 p, float celda, float ang) {
  float a = radians(ang);
  vec2 uv = mat2(cos(a), -sin(a), sin(a), cos(a)) * p / celda;
  vec2 f = fract(uv) - 0.5;
  float r = sqrt(clamp(v, 0.0, 1.0) / 3.14159);
  return clamp((r - length(f)) * celda + 0.5, 0.0, 1.0);
}
void main() {
  vec2 p = vUv * uRes;
  float k = floor(uK);
  vec3 papel = vec3(0.953, 0.918, 0.831) * (1.0 + (hash(floor(p / 2.0)) - 0.5) * 0.04 * u_papel);
  vec2 reg = vec2(hash(vec2(k, 1.0)), hash(vec2(k, 2.0))) - 0.5;
  float px = u_registro * uRes.y / 540.0;
  vec3 c = texture(uImg, vUv).rgb;
  float l = luma(c);
  vec3 sale = papel;
  if (u_tecnica < 0.5) {
    vec3 tintas[3] = vec3[](vec3(0.902, 0.706, 0.235), vec3(0.714, 0.286, 0.141), vec3(0.149, 0.224, 0.416));
    float umbral[3] = float[](0.78, 0.54, 0.3);
    for (int i = 0; i < 3; i++) {
      vec2 o = (vec2(hash(vec2(float(i), 9.0)), hash(vec2(float(i), 8.0))) - 0.5 + reg * 0.5) * px * 2.0 / uRes;
      float li = luma(texture(uImg, vUv - o).rgb) + (hash(p + k) - 0.5) * 0.04;
      float capa = clamp((umbral[i] - li) * 12.0, 0.0, 1.0);
      sale = mix(sale, tintas[i] * (1.0 + (ruidoSuave(p.x / 40.0 + p.y / 33.0, float(i)) - 0.5) * 0.08 * u_grano), capa);
    }
  } else if (u_tecnica < 1.5) {
    float celda = uRes.y / (0.55 * u_trama);
    vec3 a = vec3(0.129, 0.329, 0.773), b = vec3(0.714, 0.286, 0.141);
    float calido = clamp((c.r - c.b) * 1.5 + 0.5, 0.0, 1.0);
    float oscuro = 1.0 - l;
    float da = pow(clamp((oscuro - 0.15) / 0.85, 0.0, 1.0), 1.25) * (1.1 - 0.55 * calido);
    float db = pow(clamp((oscuro - 0.3) / 0.7, 0.0, 1.0), 1.1) * clamp(calido * 1.4 - 0.2, 0.0, 1.0);
    sale *= 1.0 - puntos(da, p + reg * px * 3.0, celda, 22.5) * 0.92 * (1.0 - a);
    sale *= 1.0 - puntos(db, p - reg * px * 3.0, celda, 67.5) * 0.92 * (1.0 - b);
  } else if (u_tecnica < 2.5) {
    float celda = uRes.y / u_trama;
    vec3 cmy = 1.0 - c;
    float kk = min(min(cmy.r, cmy.g), cmy.b) * 0.85;
    vec3 col = (cmy - kk) / (1.0 - kk + 1e-4);
    sale = vec3(0.90, 0.89, 0.83);
    sale *= 1.0 - puntos(col.b, p, celda, 0.0) * (1.0 - vec3(1.0, 0.92, 0.05));
    sale *= 1.0 - puntos(col.r, p, celda, 15.0) * (1.0 - vec3(0.0, 0.62, 0.89));
    sale *= 1.0 - puntos(col.g, p, celda, 75.0) * (1.0 - vec3(0.89, 0.05, 0.48));
    sale *= 1.0 - puntos(kk, p, celda, 45.0) * (1.0 - vec3(0.12, 0.11, 0.11));
  } else {
    float v = l;
    for (float i = 0.0; i < 6.0; i++) { if (i < u_copias) v = 1.0 / (1.0 + exp(-7.0 * (v - 0.5))); }
    float negro = (1.0 - v) * (1.0 + (hash(floor(p / 3.0) + k) - 0.5) * 0.14 * u_grano);
    negro = max(negro, step(0.9997 - 0.0002 * u_copias * u_grano, hash(p + k * 3.0)));
    negro = max(negro, pow(clamp((vUv.x - 0.955) / 0.045, 0.0, 1.0), 1.5) * 0.9);
    sale = mix(vec3(0.96, 0.96, 0.94), vec3(0.07, 0.07, 0.08), clamp(negro, 0.0, 1.0));
  }
  color = vec4(clamp(sale, 0.0, 1.0), 1.0);
}`,
  },
  // El cinetismo: la vibración, el moiré y la inducción del color (técnicas, no obras).
  cinetico: {
    opciones: {tecnica: ['vibracion', 'moire', 'induccion']},
    frag: `
uniform float u_tecnica, u_paso, u_angulo, u_deriva;
float lineas(float u, float periodo, float ancho) { float f = fract(u / periodo); float d = abs(f - 0.5) * periodo; return clamp(ancho * periodo / 2.0 - d + 0.5, 0.0, 1.0); }
void main() {
  vec2 p = vUv * uRes;
  float periodo = max(3.0, u_paso * uRes.y / 1080.0);
  vec3 fondo = vec3(0.953, 0.918, 0.831), linea = vec3(0.027, 0.035, 0.051);
  vec3 c = textureLod(uImg, vUv, 1.0).rgb;
  float oscuro = clamp(0.08 + 0.84 * (1.0 - luma(c)), 0.0, 1.0);
  float cubre = lineas(p.x, periodo, oscuro);
  vec3 sale = mix(fondo, linea, cubre);
  if (u_tecnica > 0.5 && u_tecnica < 1.5) {
    float giro = radians(u_angulo + 1.5 * u_deriva * sin(6.2832 * uT / 11.0));
    float v = p.x * cos(giro) + p.y * sin(giro);
    float otra = lineas(v + u_deriva * uT * periodo * 0.3, periodo * 1.04, 0.5);
    sale = mix(sale, linea, 0.85 * otra);
  } else if (u_tecnica > 1.5) {
    float grupo = 3.0 * periodo;
    float esColor = step(2.0 / 3.0, fract((p.x + u_deriva * uT * periodo * 0.5) / grupo));
    vec3 tonos[5] = vec3[](vec3(0.129, 0.329, 0.773), vec3(0.765, 0.404, 0.071), vec3(0.714, 0.286, 0.141), vec3(0.902, 0.706, 0.235), vec3(0.78, 0.788, 0.11));
    vec3 cc = c / (c.r + c.g + c.b + 1e-3);
    int mejor = 0; float dm = 9.0;
    for (int i = 0; i < 5; i++) { vec3 t = tonos[i] / (tonos[i].r + tonos[i].g + tonos[i].b); float d = dot(cc - t, cc - t); if (d < dm) { dm = d; mejor = i; } }
    vec3 franja = max(c.r, max(c.g, c.b)) - min(c.r, min(c.g, c.b)) < 0.08 ? fondo : tonos[mejor];
    sale = mix(sale, mix(franja, linea, oscuro), esColor);
  }
  color = vec4(sale, 1.0);
}`,
  },
  // La lente, como `optica.lente`: en luz lineal; el foco, el barril y la aberración; la viñeta; los cinco
  // fantasmas de colores de lo que más brilla (los de FANTASMAS) y, con `sol`, los del sol aunque quede fuera del
  // cuadro, su velo y el sol mismo; la raya anamórfica; la niebla; la suciedad.
  lente: {
    frag: `
uniform float u_aberracion, u_barril, u_foco, u_niebla, u_destello, u_raya, u_vineta, u_suciedad, u_sol_fuerza, u_sol_paseo, u_sol_hay;
uniform vec2 u_sol_xy;
vec3 lin(vec3 c) { return pow(max(c, 0.0), vec3(2.2)); }
float disco(vec2 p, vec2 centro, float r, float asp) {
  float d = length((p - centro) * vec2(asp, 1.0));
  return clamp((r - d) / (0.35 * r + 0.002), 0.0, 1.0) * (0.7 + 0.3 * clamp(d / max(r, 1e-3), 0.0, 1.0));
}
void main() {
  float asp = uRes.x / uRes.y;
  vec2 c = vUv - 0.5;
  float r2 = dot(c * vec2(asp, 1.0), c * vec2(asp, 1.0)) / (asp * asp * 0.25 + 0.25);
  vec2 uv = 0.5 + c * (1.0 + u_barril * 0.25 * r2) / (1.0 + u_barril * 0.06);
  vec2 ab = c * u_aberracion * 0.006;
  float lod = log2(1.0 + u_foco * 1.6 * uRes.y / 1080.0 * 2.0);
  vec3 img = lin(vec3(textureLod(uImg, uv + ab, lod).r, textureLod(uImg, uv, lod).g, textureLod(uImg, uv - ab, lod).b));
  img *= 1.0 - u_vineta * 0.9 * r2;
  vec3 extra = vec3(0.0);
  // Lo que brilla: lo más claro de la imagen, a un cuarto.
  float umbral = 0.55;
  vec2 centro = vec2(0.5);
  vec3 fan[5] = vec3[](vec3(-0.45, 0.030, 0.55), vec3(-0.95, 0.055, 0.35), vec3(-1.35, 0.090, 0.22), vec3(0.40, 0.020, 0.30), vec3(0.72, 0.045, 0.18));
  vec3 tin[5] = vec3[](vec3(1.0, 0.72, 0.35), vec3(0.45, 1.0, 0.55), vec3(0.95, 0.45, 1.0), vec3(0.55, 0.85, 1.0), vec3(1.0, 0.85, 0.6));
  vec2 sol = vec2(u_sol_xy.x, 1.0 - u_sol_xy.y)
           + vec2(u_sol_paseo * (ruidoSuave(uT * 0.12, 21.0) - 0.5) * 2.0, -0.6 * u_sol_paseo * (ruidoSuave(uT * 0.1, 22.0) - 0.5) * 2.0);
  if (u_destello > 0.0) {
    for (int i = 0; i < 5; i++) {
      float s = fan[i].x;
      vec2 donde = centro + (vUv - centro) / s;
      float dentro = step(0.0, donde.x) * step(donde.x, 1.0) * step(0.0, donde.y) * step(donde.y, 1.0);
      vec3 l = lin(textureLod(uImg, donde, 5.0).rgb);
      float m = max(l.r, max(l.g, l.b));
      vec3 luz = l * pow(max(m - umbral, 0.0) / (1.0 - umbral), 2.0) / (m + 1e-4);
      extra += u_destello * fan[i].z * 2.2 * luz * tin[i] * dentro;
      if (u_sol_hay > 0.5) extra += u_destello * fan[i].z * 0.9 * u_sol_fuerza * disco(vUv, centro + s * (sol - centro), 1.6 * fan[i].y, asp) * tin[i];
    }
    if (u_sol_hay > 0.5) {
      float d = length((vUv - sol) * vec2(asp, 1.0));
      extra += u_destello * u_sol_fuerza * (0.06 + 0.5 * exp(-d / 0.35)) * vec3(1.0, 0.82, 0.6) * 0.35;
      extra += u_sol_fuerza * (2.5 * exp(-pow(d / 0.035, 2.0)) + 0.6 * exp(-d / 0.08)) * vec3(1.0, 0.92, 0.78);
    }
  }
  if (u_raya > 0.0) {
    float raya = 0.0;
    for (int i = -8; i <= 8; i++) {
      vec3 l = lin(textureLod(uImg, vec2(vUv.x + float(i) * 0.022, vUv.y), 3.0).rgb);
      float m = max(l.r, max(l.g, l.b));
      raya += pow(max(m - umbral, 0.0) / (1.0 - umbral), 2.0) / 17.0;
    }
    if (u_sol_hay > 0.5) raya += u_sol_fuerza * 0.9 * exp(-pow((vUv.y - sol.y) / 0.008, 2.0)) * (0.35 + exp(-abs(vUv.x - sol.x) / 0.45));
    extra += u_raya * 2.2 * raya * vec3(0.35, 0.6, 1.0);
  }
  if (u_niebla > 0.0) {
    vec3 glow = lin(textureLod(uImg, vUv, 4.0).rgb) * 0.6 + lin(textureLod(uImg, vUv, 6.0).rgb) * 0.4;
    extra += u_niebla * 0.45 * glow;
    img *= 1.0 - 0.25 * min(1.0, u_niebla);
  }
  if (u_suciedad > 0.0) extra *= 1.0 - min(0.9, u_suciedad * 0.5) * smoothstep(0.45, 0.7, ruidoSuave(vUv.x * 7.0 + floor(vUv.y * 5.0) * 3.1, 4.0));
  color = vec4(pow(clamp(img + extra, 0.0, 1.0), vec3(1.0 / 2.2)), 1.0);
}`,
  },
  // La consola de mezcla de los 90 (siempre, en la vista previa): mosaico, estrobo, multi, pintura, negativo, llave.
  consola: {
    opciones: {efecto: ['mosaico', 'estrobo', 'multi', 'pintura', 'negativo', 'llave']},
    memoria: true,
    frag: `
uniform float u_efecto, u_bloque, u_cada, u_celdas, u_niveles, u_umbral;
void main() {
  vec3 c = texture(uImg, vUv).rgb;
  vec3 sale = c;
  if (u_efecto < 0.5) {
    vec2 b = vec2(u_bloque) / uRes * (uRes.y / 480.0);
    sale = texture(uImg, (floor(vUv / b) + 0.5) * b).rgb;
  } else if (u_efecto < 1.5) {
    sale = mod(floor(uK), u_cada) < 0.5 ? c : texture(uPrev, vUv).rgb;
  } else if (u_efecto < 2.5) {
    sale = texture(uImg, fract(vUv * u_celdas)).rgb;
  } else if (u_efecto < 3.5) {
    sale = floor(c * u_niveles + 0.5) / u_niveles;
  } else if (u_efecto < 4.5) {
    sale = 1.0 - c;
  } else {
    sale = luma(c) < u_umbral ? texture(uPrev, vUv).rgb * 0.98 : c;
  }
  color = vec4(sale, 1.0);
}`,
  },
  // La barra del mezclador: el cuadro como entró, fundido con lo que salió de la cadena hasta aquí.
  cruce: {
    frag: `
uniform float u_cantidad;
void main() { color = vec4(mix(texture(uOrig, vUv).rgb, texture(uImg, vUv).rgb, u_cantidad), 1.0); }`,
  },
  // El imán junto al tubo: la imagen se tuerce alrededor de un punto que se pasea.
  iman: {
    frag: `
uniform float u_fuerza, u_radio, u_velocidad, u_ondas;
void main() {
  vec2 centro = vec2(0.5 + 0.3 * sin(uT * u_velocidad * 2.1), 0.5 + 0.25 * cos(uT * u_velocidad * 1.7));
  vec2 d = vUv - centro;
  float r = length(d * vec2(uRes.x / uRes.y, 1.0));
  float f = u_fuerza * exp(-pow(r / max(u_radio, 0.01), 2.0));
  float a = f * 2.0 + u_ondas * 0.1 * sin(r * 40.0 - uT * 4.0);
  vec2 uv = centro + mat2(cos(a), -sin(a), sin(a), cos(a)) * d;
  vec3 c = texture(uImg, uv).rgb;
  vec3 y = aYiq(c);
  float h = f * 1.5;
  y.yz = mat2(cos(h), -sin(h), sin(h), cos(h)) * y.yz;
  color = vec4(clamp(aRgb(y), 0.0, 1.0), 1.0);
}`,
  },
  // La cámara que mira su monitor: lo de antes vuelve más chico, girado y corrido de color.
  realimentacion: {
    opciones: {modo: ['aclarar', 'fundir']},
    memoria: true,
    frag: `
uniform float u_mezcla, u_zoom, u_giro, u_tono, u_contraste, u_modo;
void main() {
  vec3 c = texture(uImg, vUv).rgb;
  vec2 d = vUv - 0.5;
  float a = radians(u_giro);
  vec2 uv = 0.5 + mat2(cos(a), -sin(a), sin(a), cos(a)) * d / u_zoom;
  vec3 antes = texture(uPrev, uv).rgb;
  vec3 y = aYiq(antes);
  float h = radians(u_tono);
  y.yz = mat2(cos(h), -sin(h), sin(h), cos(h)) * y.yz;
  antes = clamp((aRgb(y) - 0.5) * u_contraste + 0.5, 0.0, 1.0) * u_mezcla;
  vec3 sale = u_modo < 0.5 ? max(c, antes) : mix(c, antes, u_mezcla * 0.7);
  color = vec4(sale, 1.0);
}`,
  },
  // El colorizador del sintetizador de video: el brillo en las tintas de Curiana.
  colorizador: {
    frag: `
uniform float u_bandas, u_mezcla;
void main() {
  vec3 c = texture(uImg, vUv).rgb;
  float l = luma(c);
  if (u_bandas > 0.5) l = floor(l * u_bandas) / max(u_bandas - 1.0, 1.0);
  vec3 t[6] = vec3[](vec3(0.027, 0.035, 0.051), vec3(0.149, 0.224, 0.416), vec3(0.129, 0.329, 0.773), vec3(0.765, 0.404, 0.071), vec3(0.902, 0.706, 0.235), vec3(0.953, 0.918, 0.831));
  float x = clamp(l, 0.0, 1.0) * 5.0;
  int i = int(min(floor(x), 4.0));
  vec3 col = mix(t[i], t[i + 1], fract(x));
  color = vec4(mix(c, col, u_mezcla), 1.0);
}`,
  },
  // La cámara de tubo y de los 90: la columna clara sobre las luces, la cola de cometa, los blancos que se queman.
  camara: {
    memoria: true,
    frag: `
uniform float u_mancha, u_blancos, u_balance, u_detalle, u_ruido, u_estela;
void main() {
  vec3 c = texture(uImg, vUv).rgb;
  float col = 0.0;
  for (int i = 0; i < 12; i++) { col += max(luma(texture(uImg, vec2(vUv.x, float(i) / 11.0)).rgb) - 0.85, 0.0); }
  c += vec3(col * u_mancha * 0.35);
  c = min(c, vec3(u_blancos)) / u_blancos;
  c *= mix(vec3(1.0), vec3(1.05, 1.0, 0.9), u_balance);
  c += (hash(vUv * uRes + uK) - 0.5) * 0.08 * u_ruido;
  vec3 antes = texture(uPrev, vUv).rgb;
  c = max(c, antes * u_estela * step(0.6, luma(antes)));
  color = vec4(clamp(c, 0.0, 1.0), 1.0);
}`,
  },
  // El sensor de lo digital temprano: pocos pixeles, ruido, el blanco que se va de tono.
  sensor: {
    opciones: {tinte: ['azul', 'naranja', 'verde']},
    memoria: true,
    frag: `
uniform float u_ruido, u_tinte, u_balance, u_detalle, u_aliasing, u_cuadros;
void main() {
  if (uHold > 0.5) { color = texture(uPrev, vUv); return; }
  vec2 celda = vec2(320.0, 240.0);
  vec2 uv = (floor(vUv * celda) + 0.5) / celda;
  vec3 c = mix(texture(uImg, uv).rgb, textureLod(uImg, uv, 2.0).rgb, 1.0 - u_aliasing);
  vec3 t = u_tinte < 0.5 ? vec3(0.9, 1.0, 1.15) : (u_tinte < 1.5 ? vec3(1.12, 1.0, 0.85) : vec3(0.95, 1.1, 0.95));
  c *= mix(vec3(1.0), t, u_balance);
  c += (hash(floor(vUv * celda) + uK) - 0.5) * 0.09 * u_ruido;
  color = vec4(clamp(c, 0.0, 1.0), 1.0);
}`,
  },
  // La compresión: los bloques del códec y, con errores, los bloques que se arrastran.
  compresion: {
    opciones: {modo: ['mpeg', 'jpeg', 'dv']},
    memoria: true,
    frag: `
uniform float u_calidad, u_errores, u_residuo;
void main() {
  vec2 b = vec2(8.0) / uRes * (uRes.y / 480.0);
  vec2 celda = floor(vUv / b);
  vec3 media = texture(uImg, (celda + 0.5) * b).rgb;
  vec3 c = texture(uImg, vUv).rgb;
  vec3 sale = mix(media, c, u_calidad);
  sale = floor(sale * (6.0 + 26.0 * u_calidad)) / (6.0 + 26.0 * u_calidad);
  float roto = step(1.0 - 0.06 * u_errores, hash(celda + floor(uK / 3.0)));
  vec3 antes = texture(uPrev, vUv + vec2(0.004, 0.0)).rgb;
  sale = mix(sale, antes, roto * (1.0 - u_residuo * 0.5));
  color = vec4(sale, 1.0);
}`,
  },
};

const VERTICE = `#version 300 es
in vec2 aPos;
out vec2 vUv;
void main() { vUv = aPos * 0.5 + 0.5; gl_Position = vec4(aPos, 0.0, 1.0); }`;

const COPIAR = `
void main() { color = vec4(texture(uImg, vUv).rgb, 1.0); }`;
const COPIAR_TAL = `
void main() { color = texture(uImg, vUv); }`;

type Pasada = {prog: WebGLProgram; uniformes: Map<string, WebGLUniformLocation | null>};
type Destino = {tex: WebGLTexture; fbo: WebGLFramebuffer};

export type Modulo = {aparato: string; perillas: Perillas; activo: boolean};

/** El valor de una perilla como número para el shader: los números tal cual; las opciones, su lugar en la lista. */
function aNumero(aparato: string, perilla: string, v: Valor): number {
  if (typeof v === 'number') return v;
  if (typeof v === 'boolean') return v ? 1 : 0;
  const ops = VIVOS[aparato]?.opciones?.[perilla];
  return ops && typeof v === 'string' ? Math.max(0, ops.indexOf(v)) : 0;
}

/** Los aparatos que la consola puede mostrar en vivo (los demás pasan sin tocar y sólo se ven en el render). */
export const EN_VIVO = new Set(Object.keys(VIVOS));

export class Consola {
  private gl: WebGL2RenderingContext;
  private pasadas = new Map<string, Pasada>();
  private copiar: Pasada;
  private copiarTal: Pasada;
  private vao: WebGLVertexArrayObject;
  private orig: WebGLTexture;
  private ancho = 0;
  private alto = 0;
  private temporales: Destino[] = [];
  // Lo que cada módulo dibujó en el cuadro anterior (por su lugar en la cadena): su memoria.
  private memorias: Destino[] = [];
  private retener = new Map<number, number>();
  private cuadro = 0;

  constructor(private lienzo: HTMLCanvasElement) {
    const gl = lienzo.getContext('webgl2', {premultipliedAlpha: false, preserveDrawingBuffer: true});
    if (!gl) throw new Error('Este navegador no tiene WebGL2: la consola necesita la tarjeta de video.');
    this.gl = gl;
    gl.getExtension('EXT_color_buffer_float');
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    this.vao = gl.createVertexArray()!;
    gl.bindVertexArray(this.vao);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    this.orig = this.textura();
    this.copiar = this.compilar('copiar', COPIAR);
    this.copiarTal = this.compilar('copiar-tal', COPIAR_TAL);
  }

  private textura(mip = true): WebGLTexture {
    const gl = this.gl;
    const t = gl.createTexture()!;
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, mip ? gl.LINEAR_MIPMAP_LINEAR : gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return t;
  }

  private destino(mip = true): Destino {
    const gl = this.gl;
    const tex = this.textura(mip);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, this.ancho, this.alto, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    const fbo = gl.createFramebuffer()!;
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return {tex, fbo};
  }

  private compilar(nombre: string, frag: string): Pasada {
    const gl = this.gl;
    const sombra = (tipo: number, src: string) => {
      const s = gl.createShader(tipo)!;
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(`${nombre}: ${gl.getShaderInfoLog(s)}`);
      return s;
    };
    const prog = gl.createProgram()!;
    gl.attachShader(prog, sombra(gl.VERTEX_SHADER, VERTICE));
    gl.attachShader(prog, sombra(gl.FRAGMENT_SHADER, CABECERA + frag));
    gl.bindAttribLocation(prog, 0, 'aPos');
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(`${nombre}: ${gl.getProgramInfoLog(prog)}`);
    return {prog, uniformes: new Map()};
  }

  /** Los aparatos cuyo shader no compiló en esta tarjeta, con el porqué: pasan sin tocar. */
  readonly rotos = new Map<string, string>();

  private pasada(aparato: string): Pasada | null {
    const def = VIVOS[aparato];
    if (!def || this.rotos.has(aparato)) return null;
    let p = this.pasadas.get(aparato);
    if (!p) {
      try {
        p = this.compilar(aparato, def.frag);
      } catch (e) {
        this.rotos.set(aparato, (e as Error).message);
        console.error(e);
        return null;
      }
      this.pasadas.set(aparato, p);
    }
    return p;
  }

  private u(p: Pasada, nombre: string): WebGLUniformLocation | null {
    if (!p.uniformes.has(nombre)) p.uniformes.set(nombre, this.gl.getUniformLocation(p.prog, nombre));
    return p.uniformes.get(nombre) ?? null;
  }

  private medir(ancho: number, alto: number, modulos: number) {
    if (ancho === this.ancho && alto === this.alto && this.memorias.length >= modulos) return;
    const cambio = ancho !== this.ancho || alto !== this.alto;
    this.ancho = ancho;
    this.alto = alto;
    this.lienzo.width = ancho;
    this.lienzo.height = alto;
    if (cambio) {
      for (const d of [...this.temporales, ...this.memorias]) this.borrar(d);
      this.temporales = [this.destino(), this.destino()];
      this.memorias = [];
    }
    while (this.memorias.length < modulos) this.memorias.push(this.destino(false));
  }

  private borrar(d: Destino) {
    this.gl.deleteTexture(d.tex);
    this.gl.deleteFramebuffer(d.fbo);
  }

  /** Olvida lo que los aparatos recordaban (al cambiar de fuente o de cadena). */
  olvidar() {
    for (const d of this.memorias) this.borrar(d);
    this.memorias = [];
    this.retener.clear();
  }

  /** El lienzo, para grabar el boceto (`captureStream`). */
  get canvas() {
    return this.lienzo;
  }

  /** Dibuja un cuadro: el video por los módulos activos (los que no tienen vista previa pasan sin tocar).
   * `corriendo`: si el video avanza. Quieto, cada dibujo procesa el cuadro de ahora (no hay paso a saltitos que
   * retener, y la memoria puede estar vacía: retenerla dejaba la pantalla en negro). */
  dibujar(video: HTMLVideoElement | HTMLCanvasElement, modulos: Modulo[], t: number, alto = 540, corriendo = true) {
    const gl = this.gl;
    const vw = video instanceof HTMLVideoElement ? video.videoWidth : video.width;
    const vh = video instanceof HTMLVideoElement ? video.videoHeight : video.height;
    if (!vw || !vh) return;
    const h = Math.min(alto, vh);
    const w = Math.round((vw * h) / vh / 2) * 2;
    this.medir(w, h, modulos.length);
    this.cuadro += 1;
    gl.bindVertexArray(this.vao);
    gl.viewport(0, 0, w, h);
    gl.bindTexture(gl.TEXTURE_2D, this.orig);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, video);
    gl.generateMipmap(gl.TEXTURE_2D);
    let entrada = this.orig;
    let turno = 0;
    const fps = 30;
    modulos.forEach((m, i) => {
      if (!m.activo) return;
      const p = this.pasada(m.aparato);
      if (!p) return;
      // El paso a saltitos de la película y del sensor: mientras dura un cuadro suyo, se repite el anterior.
      let hold = 0;
      const cps = Number(m.perillas.cuadros ?? 0);
      if ((m.aparato === 'pelicula' || m.aparato === 'sensor') && cps > 0 && cps < fps) {
        const j = Math.floor(t * cps);
        hold = corriendo && this.retener.get(i) === j ? 1 : 0;
        this.retener.set(i, j);
      }
      const salida = this.temporales[turno % 2];
      turno += 1;
      gl.bindFramebuffer(gl.FRAMEBUFFER, salida.fbo);
      gl.useProgram(p.prog);
      this.atar(p, 'uImg', 0, entrada);
      this.atar(p, 'uOrig', 1, this.orig);
      this.atar(p, 'uPrev', 2, this.memorias[i].tex);
      gl.uniform2f(this.u(p, 'uRes'), w, h);
      gl.uniform1f(this.u(p, 'uT'), t);
      gl.uniform1f(this.u(p, 'uK'), Math.floor(t * fps));
      gl.uniform1f(this.u(p, 'uHold'), hold);
      for (const [k, v] of Object.entries(m.perillas)) {
        if (Array.isArray(v)) {
          const par = v.length === 2 && typeof v[0] === 'number' && typeof v[1] === 'number';
          const hay = this.u(p, `u_${k}_hay`);
          if (hay) gl.uniform1f(hay, par ? 1 : 0);
          const xy = this.u(p, `u_${k}_xy`);
          if (xy && par) gl.uniform2f(xy, v[0] as number, v[1] as number);
          continue;
        }
        const loc = this.u(p, `u_${k}`);
        if (loc) gl.uniform1f(loc, aNumero(m.aparato, k, v));
      }
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      // Lo que dibujó queda como su memoria para el cuadro que viene.
      this.copiarA(salida.tex, this.memorias[i]);
      gl.bindTexture(gl.TEXTURE_2D, salida.tex);
      gl.generateMipmap(gl.TEXTURE_2D);
      entrada = salida.tex;
    });
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.useProgram(this.copiar.prog);
    this.atar(this.copiar, 'uImg', 0, entrada);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  private atar(p: Pasada, nombre: string, unidad: number, tex: WebGLTexture) {
    const gl = this.gl;
    gl.activeTexture(gl.TEXTURE0 + unidad);
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.uniform1i(this.u(p, nombre), unidad);
  }

  private copiarA(tex: WebGLTexture, a: Destino) {
    const gl = this.gl;
    gl.bindFramebuffer(gl.FRAMEBUFFER, a.fbo);
    gl.useProgram(this.copiarTal.prog);
    this.atar(this.copiarTal, 'uImg', 0, tex);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }
}
