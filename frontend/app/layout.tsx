import type { Metadata } from 'next';
import Link from 'next/link';
import { DISCLAIMER } from '@/lib/constants';
import './globals.css';

export const metadata: Metadata = {
  title: 'Saathi | Human-reviewed triage support',
  description: 'Synthetic educational prototype. Non-diagnostic, human-reviewed information organization.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a href="#main" className="sr-only focus:not-sr-only focus:block focus:p-4">Skip to main content</a>
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-4">
            <Link href="/" className="flex min-h-12 items-center gap-3" aria-label="Saathi home">
              <span aria-hidden="true" className="rounded-xl bg-brand px-3 py-1 text-3xl text-white">+</span>
              <span><strong className="block text-xl tracking-tight">Saathi</strong><span className="text-xs text-slate-600">Care starts with listening</span></span>
            </Link>
            <nav aria-label="Main navigation" className="flex flex-wrap gap-1 text-sm font-semibold">
              {[['/', 'Overview'], ['/intake', 'Intake'], ['/dashboard', 'Review queue'], ['/admin', 'Admin']].map(([href, label]) => (
                <Link key={href} href={href} className="flex min-h-12 items-center rounded-lg px-3 hover:bg-mist">{label}</Link>
              ))}
            </nav>
          </div>
        </header>
        <aside aria-label="Prototype disclaimer" className="border-b border-amber-200 bg-amber-50">
          <p className="mx-auto max-w-6xl px-5 py-3 text-sm leading-relaxed text-amber-950"><strong>Synthetic demo only. </strong>{DISCLAIMER}</p>
        </aside>
        <main id="main" className="mx-auto min-h-[65vh] max-w-6xl px-5 py-8">{children}</main>
        <footer className="mx-auto flex max-w-6xl flex-wrap justify-between gap-3 border-t border-slate-200 px-5 py-6 text-xs text-slate-600">
          <span>BPUT Hackathon 2026 · Foundation phase</span><span>No diagnosis. No prescriptions. Professional review required.</span>
        </footer>
      </body>
    </html>
  );
}
