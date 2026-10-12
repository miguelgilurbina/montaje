import type {NextConfig} from 'next';

// El panel vive en el mismo paquete que la composición de Remotion (src/), así
// hay una sola copia de `remotion` y el reproductor dibuja el mismo código que
// renderiza. Los medios no pasan por Next: los sirve app/medios con rangos.
const config: NextConfig = {};

export default config;
