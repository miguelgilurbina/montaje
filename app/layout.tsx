import type {Metadata} from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'montaje · panel',
  description: 'Ver y ajustar la edición antes de renderizar.',
};

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
