'use client';

import { useState, type FormEvent } from 'react';
import { FACILITIES, SCENARIOS } from '@/lib/constants';

const COPY = {
  en: {
    consent: 'I consent to the use of this information for triage-support demonstration purposes.',
    title: 'Start with consent', complaint: 'Main complaint / symptom narrative',
    preview: 'Preview locally', detail: 'Use fictional information only. No names, phone numbers, addresses or Aadhaar numbers.',
  },
  hi: {
    consent: 'मैं इस जानकारी का उपयोग केवल ट्रायेज-सहायता प्रदर्शन के लिए करने की सहमति देता/देती हूँ।',
    title: 'सहमति से शुरुआत करें', complaint: 'मुख्य शिकायत / लक्षणों का विवरण',
    preview: 'स्थानीय पूर्वावलोकन', detail: 'केवल काल्पनिक जानकारी दें। नाम, फोन नंबर, पता या आधार नंबर न दें।',
  },
};

export default function Intake() {
  const [language, setLanguage] = useState<'en' | 'hi'>('en');
  const [consent, setConsent] = useState(false);
  const [preview, setPreview] = useState<Record<string, string> | null>(null);
  const copy = COPY[language];

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!consent) return;
    const data = new FormData(event.currentTarget);
    setPreview(Object.fromEntries(Array.from(data.entries()).map(([key, value]) => [key, String(value)])));
  }

  return <div className="mx-auto max-w-3xl space-y-6">
    <div><p className="eyebrow">Intake workspace · Synthetic demo only</p><h1 className="mt-3 text-3xl font-bold">Listen first. Keep the original words.</h1><p className="mt-3 text-slate-600">This is an ephemeral form preview, not a triage submission. No model is called and no information is sent to the backend.</p></div>
    <section className="card" aria-labelledby="consent-heading">
      <label className="block max-w-xs font-semibold">Consent and narrative language
        <select className="field" value={language} onChange={event => { setLanguage(event.target.value as 'en' | 'hi'); setConsent(false); setPreview(null); }}>
          <option value="en">English</option><option value="hi">हिन्दी — Hindi</option>
        </select>
      </label>
      <p className="mt-2 text-xs text-slate-600">Full UI localization and Odia input arrive in later phases.</p>
      <h2 id="consent-heading" className="mt-6 text-xl font-bold" lang={language}>{copy.title}</h2>
      <p className="mt-3 text-sm text-slate-600" lang={language}>{copy.detail}</p>
      <label className="mt-4 flex min-h-12 cursor-pointer items-start gap-3 rounded-xl bg-mist p-4" lang={language}>
        <input type="checkbox" className="mt-1 h-5 w-5 accent-teal-700" checked={consent} onChange={event => { setConsent(event.target.checked); setPreview(null); }} />
        <span>{copy.consent}</span>
      </label>
      <p className="mt-3 text-xs text-slate-600">Unchecking consent clears the form. This preview does not create a persistent consent record.</p>
    </section>
    {!consent ? <p role="status" className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-slate-600">Intake stays unavailable until you give demo consent.</p> :
      <form onSubmit={submit} onChange={() => setPreview(null)} className="card space-y-6">
        <h2 className="text-xl font-bold">Fictional patient details</h2>
        <div className="grid gap-5 sm:grid-cols-2">
          <label className="font-semibold">Pseudonym ID<input className="field" name="pseudonym_id" required defaultValue="DEMO-001" pattern="[A-Z][A-Z0-9\-]{2,39}" maxLength={40} autoComplete="off" /></label>
          <label className="font-semibold">Age in years (optional)<input className="field" name="age" type="number" min="0" max="120" step="1" /></label>
          <label className="font-semibold">Sex (optional)<select className="field" name="sex" defaultValue="not_reported"><option value="not_reported">Not reported</option><option value="female">Female</option><option value="male">Male</option><option value="intersex">Intersex</option></select></label>
          <label className="font-semibold">Facility<select className="field" name="facility_type" defaultValue="PHC">{FACILITIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label className="font-semibold sm:col-span-2">Scenario<select className="field" name="scenario">{SCENARIOS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        </div>
        <input type="hidden" name="language" value={language} />
        <label className="block font-semibold" lang={language}>{copy.complaint}<textarea className="field min-h-32" name="complaint" required maxLength={4000} placeholder={language === 'hi' ? 'तीन दिन से बुखार, खांसी और कमजोरी है।' : 'Fever and cough for three days; also feeling weak.'} /></label>
        <div className="grid gap-5 sm:grid-cols-2">
          {[
            ['symptoms', 'Symptoms (as reported)'], ['duration', 'Duration / onset'],
            ['conditions', 'Existing conditions (reported)'], ['medications', 'Medicines mentioned (history only)'],
            ['allergies', 'Allergies (reported)'],
          ].map(([name, label]) => <label key={name} className="font-semibold">{label}<input className="field" name={name} maxLength={500} /></label>)}
        </div>
        <fieldset><legend className="font-bold">Available measurements — leave unknown values blank</legend>
          <div className="mt-3 grid gap-5 sm:grid-cols-2">
            {[
              ['temperature', 'Temperature (°C)', 0, 60], ['bp_sys', 'Systolic BP (mmHg)', 0, 400],
              ['bp_dia', 'Diastolic BP (mmHg)', 0, 300], ['spo2', 'SpO₂ (%)', 0, 100],
            ].map(([name, label, min, max]) => <label key={name} className="font-semibold">{label}<input className="field" name={String(name)} type="number" step="0.1" min={min} max={max} /></label>)}
          </div>
        </fieldset>
        <p className="text-sm text-slate-600">Voice, reports, images and scenario-specific forms are not enabled yet. A missing answer is not a negative finding.</p>
        <div className="flex flex-wrap gap-3"><button className="button" type="submit" lang={language}>{copy.preview}</button><button className="min-h-12 rounded-xl border border-slate-300 px-5 font-semibold hover:bg-slate-50" type="button" onClick={() => { setConsent(false); setPreview(null); }}>Clear and revoke demo consent</button></div>
      </form>}
    {preview && consent && <section className="card" aria-live="polite">
      <h2 className="text-xl font-bold">Local input preview — not a triage note</h2>
      <p className="mt-2 text-sm text-slate-600">Nothing is saved. No urgency category is assigned. Professional review and processing are not enabled.</p>
      <dl className="mt-5 divide-y divide-slate-100">{Object.entries(preview).map(([key, value]) => <div key={key} className="grid gap-1 py-3 sm:grid-cols-[180px_1fr]"><dt className="text-sm font-semibold">{key.replaceAll('_', ' ')}</dt><dd className="whitespace-pre-wrap break-words text-sm">{value || 'Not reported'}</dd></div>)}</dl>
    </section>}
  </div>;
}
