'use client';

import {Player, type PlayerRef} from '@remotion/player';
import type {RefObject} from 'react';
import {Montaje} from '@/src/Montaje';
import type {Timeline} from '@/src/tipos';

/** El mismo componente que renderiza el video, dibujado en el navegador: lo que ves es lo que sale. */
export default function Reproductor({tl, playerRef}: {tl: Timeline; playerRef: RefObject<PlayerRef | null>}) {
  return (
    <Player
      ref={playerRef}
      component={Montaje}
      inputProps={tl}
      durationInFrames={Math.max(1, tl.duracion)}
      fps={tl.fps}
      compositionWidth={tl.ancho}
      compositionHeight={tl.alto}
      controls
      clickToPlay
      spaceKeyToPlayOrPause
      style={{width: '100%'}}
      acknowledgeRemotionLicense
    />
  );
}
