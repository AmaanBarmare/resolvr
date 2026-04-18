import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Resolvr — The Arbitration Desk',
  description: 'When your AI agents disagree, the Arbitration Desk decides. Forensic divergence analysis, market-grounded verification, and a published decision brief.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT@9..144,300..900,0..100&family=Newsreader:opsz,wght,ital@6..72,200..800,0;6..72,200..800,1&family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@300;400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
