import {Composition} from 'remotion';
import {Montaje} from './Montaje';
import {TIMELINE_VACIO, type Timeline} from './tipos';

export const Root: React.FC = () => (
  <Composition
    id="Montaje"
    component={Montaje}
    defaultProps={TIMELINE_VACIO}
    // El timeline manda: duración, cuadros por segundo y lienzo salen de él.
    calculateMetadata={({props}: {props: Timeline}) => ({
      durationInFrames: Math.max(1, props.duracion),
      fps: props.fps,
      width: props.ancho,
      height: props.alto,
    })}
    durationInFrames={TIMELINE_VACIO.duracion}
    fps={TIMELINE_VACIO.fps}
    width={TIMELINE_VACIO.ancho}
    height={TIMELINE_VACIO.alto}
  />
);
