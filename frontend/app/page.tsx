import Link from 'next/link';

export default function Home() {
  return (
    <div className="space-y-8">
      <section className="grid overflow-hidden rounded-3xl border border-teal-100 bg-mist md:grid-cols-[1.5fr_1fr]">
        <div className="p-7 md:p-10">
          <p className="eyebrow">Built for India · Designed around people</p>
          <h1 className="mt-4 max-w-xl text-4xl font-bold leading-tight tracking-tight md:text-5xl">Clearer information.<br />Human-led care.</h1>
          <p className="mt-5 max-w-lg leading-relaxed text-slate-700">A shared workspace to organize symptoms, reports and patient narratives for qualified healthcare staff. Every decision stays with a professional.</p>
          <Link className="button mt-7" href="/intake">Explore demo intake <span aria-hidden="true" className="ml-3">→</span></Link>
          <p className="mt-3 text-xs text-slate-600">Local preview only. Nothing is submitted or stored.</p>
        </div>
        <div className="m-6 rounded-2xl bg-white p-6 shadow-sm md:my-10 md:mr-10">
          <p className="eyebrow">The intended care journey</p>
          <ol className="mt-6 space-y-6">
            {[
              ['01', 'Listen with consent', 'Capture the patient’s own words.'],
              ['02', 'Organize, never diagnose', 'Show grounded information and missing details.'],
              ['03', 'Support qualified review', 'Make urgency signals and their sources visible.'],
            ].map(([step, title, text]) => (
              <li className="flex gap-4" key={step}><span className="font-mono text-xl text-brand">{step}</span><div><h2 className="font-bold">{title}</h2><p className="mt-1 text-sm text-slate-600">{text}</p></div></li>
            ))}
          </ol>
        </div>
      </section>
      <section aria-labelledby="status-title" className="card">
        <div className="flex flex-wrap items-center justify-between gap-3"><h2 id="status-title" className="text-xl font-bold">Foundation, not a clinical service</h2><span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-bold">Phase 1 of 8</span></div>
        <p className="mt-3 leading-relaxed text-slate-600">This phase provides a consent-first interface, typed data contracts and fictional fixtures. AI processing, live prioritization, reviewer sign-off and exports are not enabled yet.</p>
      </section>
      <section aria-label="Design commitments" className="grid gap-4 md:grid-cols-3">
        {[
          ['Professional review', 'No autonomous discharge, treatment or final decision.'],
          ['India-wide contexts', 'From PHCs and health camps to campuses and industrial clinics.'],
          ['Visible uncertainty', 'Unknown information must never become an assumed negative.'],
        ].map(([title, text]) => <article className="card" key={title}><h2 className="font-bold">{title}</h2><p className="mt-3 text-sm leading-relaxed text-slate-600">{text}</p></article>)}
      </section>
    </div>
  );
}
