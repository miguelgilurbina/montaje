import Link from 'next/link';
import {listar} from '@/lib/proyectos';

export const dynamic = 'force-dynamic';

export default function Portada() {
  const proyectos = listar();
  return (
    <div className="portada">
      <h1>montaje · panel</h1>
      <p className="dato">Elige un experimento. El video se dibuja en el navegador, sin renderizar.</p>
      <Link href="/estilos" className="tarjeta estilos-entrada">
        <b>estilos</b>
        el catálogo: cada edición con su receta, su muestra y lo que dijo Miguel
      </Link>
      <Link href="/consola" className="tarjeta estilos-entrada">
        <b>consola</b>
        los diales: un video por los aparatos de la mesa, girando a mano y en vivo; lo que se graba lo renderiza el motor
      </Link>
      <Link href="/textos" className="tarjeta estilos-entrada">
        <b>textos</b>
        la galería de letreros: títulos, frases, rótulos, subtítulos y créditos, en vivo y con tipografías libres
      </Link>
      {proyectos.map((p) => (
        <Link key={p.nombre} href={`/p/${p.nombre}`} className="tarjeta">
          <b>{p.nombre}</b>
          {p.titulo}
          {p.tieneTimeline ? null : <span className="dato"> · sin timeline</span>}
        </Link>
      ))}
    </div>
  );
}
