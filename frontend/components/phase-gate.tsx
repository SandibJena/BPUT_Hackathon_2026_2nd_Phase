import Link from 'next/link';

export function PhaseGate({ title, description }: { title: string; description: string }) {
  return <section className="card mx-auto max-w-2xl py-10">
    <p className="eyebrow">Not enabled in Phase 1</p>
    <h1 className="mt-3 text-3xl font-bold">{title}</h1>
    <p className="mt-5 leading-relaxed text-slate-600">{description}</p>
    <p className="mt-4 text-sm text-slate-600">No live patient records or clinical actions are available in this foundation.</p>
    <Link href="/intake" className="button mt-6">Explore local intake preview</Link>
  </section>;
}
