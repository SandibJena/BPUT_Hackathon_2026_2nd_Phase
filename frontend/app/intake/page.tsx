'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AlertTriangle, Mic, FileText, ChevronDown, Send, RefreshCw } from 'lucide-react';
import VoiceRecorder from '@/components/VoiceRecorder';
import DisclaimerBanner from '@/components/DisclaimerBanner';
import PriorityBadge from '@/components/PriorityBadge';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

const AGE_BANDS = ['0-12', '13-17', '18-30', '31-45', '46-60', '61-75', '76+', 'unknown'];
const FACILITY_TYPES = ['OPD', 'PHC', 'CHC', 'district', 'camp', 'company_clinic', 'industrial_unit', 'campus'];
const SCENARIOS = ['opd_queue', 'maternal_health', 'industrial_screening', 'campus_health', 'health_camp', 'emergency'];
const LANGUAGES = [
  { code: 'en', label: 'English', speech: 'en-IN' },
  { code: 'hi', label: 'हिन्दी', speech: 'hi-IN' },
  { code: 'or', label: 'ଓଡ଼ିଆ', speech: 'or-IN' },
];

type Tab = 'text' | 'voice';

interface TriageResult {
  id: string;
  chief_complaint: string;
  risk: { category: string; reasons: string[]; triggered_rules: string[] };
  symptoms: { name: string; assertion: string }[];
  missing_info: { field: string; why_it_matters: string }[];
  follow_up_questions: { question: string; target_role: string }[];
  disclaimer: string;
}

export default function IntakePage() {
  const router = useRouter();
  const [token, setToken] = useState('');
  const [tab, setTab] = useState<Tab>('text');
  const [lang, setLang] = useState(LANGUAGES[0]);
  const [consent, setConsent] = useState(false);
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TriageResult | null>(null);
  const [error, setError] = useState('');

  // Form state
  const [pseudonymId, setPseudonymId] = useState(() => `PHC-${Date.now().toString(36).toUpperCase()}`);
  const [ageBand, setAgeBand] = useState('31-45');
  const [sex, setSex] = useState('');
  const [facilityType, setFacilityType] = useState('OPD');
  const [scenario, setScenario] = useState('opd_queue');
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [symptomsText, setSymptomsText] = useState('');
  const [spo2, setSpo2] = useState('');
  const [pulse, setPulse] = useState('');
  const [temp, setTemp] = useState('');

  useEffect(() => {
    const t = localStorage.getItem('auth_token') ?? '';
    if (!t) { router.push('/login'); return; }
    setToken(t);
  }, [router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!consent) { setError('Patient consent is required.'); return; }
    if (!symptomsText.trim()) { setError('Please describe the symptoms.'); return; }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const body = {
        pseudonym_id: pseudonymId,
        age_band: ageBand,
        sex: sex || null,
        language: lang.code,
        facility_type: facilityType,
        scenario,
        chief_complaint: chiefComplaint || symptomsText.slice(0, 80),
        symptoms_text: symptomsText,
        consent_given: true,
        vitals: {
          spo2: spo2 ? parseFloat(spo2) : null,
          pulse: pulse ? parseInt(pulse) : null,
          temp: temp ? parseFloat(temp) : null,
        },
      };

      const resp = await fetch(`${API}/intake/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(body),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail ?? 'Submission failed');
      }

      const data = await resp.json();
      setResult(data);
      // scroll to result
      setTimeout(() => document.getElementById('triage-result')?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch (err: any) {
      setError(err.message ?? 'Unexpected error. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  if (!token) return null;

  return (
    <div className="mx-auto max-w-2xl px-4 pb-24 pt-6">
      <h1 className="mb-1 text-xl font-bold text-gray-900">Patient Intake</h1>
      <p className="mb-6 text-sm text-gray-500">
        Complete all sections, then submit for triage assessment.
      </p>

      {/* Consent gate */}
      {!consentConfirmed ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
          <div className="mb-3 flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
            <div>
              <h2 className="font-semibold text-amber-900">Patient Consent Required</h2>
              <p className="mt-1 text-sm text-amber-800">
                This system collects symptom information for triage support demonstration.
                Information is used only for this session and is not shared with any third party.
              </p>
              <div className="mt-2 text-xs text-amber-700 italic">
                यह प्रणाली केवल ट्राइएज सहायता के लिए है। / ଏହି ସିଷ୍ଟମ ଟ୍ରାଏଜ ସହାୟତା ପାଇଁ।
              </div>
            </div>
          </div>
          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              className="mt-0.5 h-5 w-5 rounded"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            <span className="text-sm text-amber-900">
              I confirm that the patient has consented to this information being used for
              triage-support demonstration purposes.
            </span>
          </label>
          <button
            disabled={!consent}
            onClick={() => setConsentConfirmed(true)}
            className="mt-4 min-h-[44px] w-full rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-700 disabled:opacity-40"
          >
            Confirm Consent & Continue
          </button>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-5">
          {/* Language selector */}
          <div className="flex gap-2">
            {LANGUAGES.map((l) => (
              <button
                key={l.code}
                type="button"
                onClick={() => setLang(l)}
                className={`min-h-[36px] rounded-lg border px-3 py-1 text-sm ${
                  lang.code === l.code
                    ? 'border-blue-500 bg-blue-50 font-semibold text-blue-700'
                    : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>

          {/* Patient info */}
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <h3 className="mb-3 font-semibold text-gray-800">Patient Information</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600">Pseudonym ID</label>
                <input
                  value={pseudonymId}
                  onChange={(e) => setPseudonymId(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600">Age Band</label>
                <select
                  value={ageBand}
                  onChange={(e) => setAgeBand(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                >
                  {AGE_BANDS.map((b) => <option key={b}>{b}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600">Sex</label>
                <select
                  value={sex}
                  onChange={(e) => setSex(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="">Not specified</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600">Facility Type</label>
                <select
                  value={facilityType}
                  onChange={(e) => setFacilityType(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                >
                  {FACILITY_TYPES.map((f) => <option key={f}>{f}</option>)}
                </select>
              </div>
              <div className="col-span-2">
                <label className="mb-1 block text-xs font-medium text-gray-600">Scenario</label>
                <select
                  value={scenario}
                  onChange={(e) => setScenario(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                >
                  {SCENARIOS.map((s) => <option key={s}>{s}</option>)}
                </select>
              </div>
            </div>
          </div>

          {/* Vitals (optional) */}
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <h3 className="mb-3 font-semibold text-gray-800">Vitals <span className="text-xs font-normal text-gray-400">(optional)</span></h3>
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'SpO₂ (%)', value: spo2, set: setSpo2, placeholder: '94' },
                { label: 'Pulse (bpm)', value: pulse, set: setPulse, placeholder: '80' },
                { label: 'Temp (°C)', value: temp, set: setTemp, placeholder: '37.5' },
              ].map(({ label, value, set, placeholder }) => (
                <div key={label}>
                  <label className="mb-1 block text-xs font-medium text-gray-600">{label}</label>
                  <input
                    type="number"
                    value={value}
                    onChange={(e) => set(e.target.value)}
                    placeholder={placeholder}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Symptoms — text / voice tabs */}
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex gap-1 rounded-lg bg-gray-100 p-1">
              {(['text', 'voice'] as Tab[]).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setTab(t)}
                  className={`flex min-h-[36px] flex-1 items-center justify-center gap-1.5 rounded-md text-sm font-medium transition-all ${
                    tab === t ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {t === 'text' ? <FileText className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                  {t === 'text' ? 'Type symptoms' : 'Voice input'}
                </button>
              ))}
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">
                Chief Complaint
              </label>
              <input
                value={chiefComplaint}
                onChange={(e) => setChiefComplaint(e.target.value)}
                placeholder="e.g. Chest pain since morning"
                className="mb-3 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>

            {tab === 'text' ? (
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600">
                  Describe symptoms in detail
                </label>
                <textarea
                  value={symptomsText}
                  onChange={(e) => setSymptomsText(e.target.value)}
                  rows={5}
                  placeholder={
                    lang.code === 'hi'
                      ? 'लक्षण यहाँ लिखें...'
                      : lang.code === 'or'
                      ? 'ଲକ୍ଷଣ ଏଠାରେ ଲିଖନ୍ତୁ...'
                      : 'Describe symptoms, duration, severity…'
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                />
              </div>
            ) : (
              <div className="space-y-3">
                <VoiceRecorder
                  language={lang.speech}
                  onTranscript={(text) => {
                    setSymptomsText((prev) => (prev ? prev + ' ' + text : text).trim());
                  }}
                />
                {symptomsText && (
                  <div>
                    <label className="mb-1 block text-xs font-medium text-gray-600">
                      Transcript (editable)
                    </label>
                    <textarea
                      value={symptomsText}
                      onChange={(e) => setSymptomsText(e.target.value)}
                      rows={4}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="flex min-h-[52px] w-full items-center justify-center gap-2 rounded-xl bg-blue-700 px-6 py-3 text-base font-semibold text-white hover:bg-blue-800 disabled:opacity-60"
          >
            {loading ? (
              <>
                <RefreshCw className="h-5 w-5 animate-spin" />
                Running triage assessment…
              </>
            ) : (
              <>
                <Send className="h-5 w-5" />
                Submit for Triage
              </>
            )}
          </button>
        </form>
      )}

      {/* Result */}
      {result && (
        <div id="triage-result" className="mt-8 space-y-4">
          <div className={`rounded-xl border-2 p-5 ${
            result.risk?.category === 'EMERGENCY'
              ? 'border-red-500 bg-red-50'
              : result.risk?.category === 'HIGH'
              ? 'border-amber-400 bg-amber-50'
              : result.risk?.category === 'NORMAL'
              ? 'border-green-400 bg-green-50'
              : 'border-gray-300 bg-gray-50'
          }`}>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-bold text-gray-900">Triage Result</h2>
              {result.risk && <PriorityBadge category={result.risk.category} size="lg" />}
            </div>

            {result.chief_complaint && (
              <p className="mb-3 text-sm font-medium text-gray-800">
                Chief complaint: {result.chief_complaint}
              </p>
            )}

            {result.risk?.reasons?.length > 0 && (
              <div className="mb-3">
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">Urgency signals</p>
                <ul className="space-y-1">
                  {result.risk.reasons.map((r, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-gray-500" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.risk?.triggered_rules?.length > 0 && (
              <div className="mb-3 flex flex-wrap gap-1.5">
                {result.risk.triggered_rules.map((r) => (
                  <span key={r} className="rounded-md bg-gray-200 px-2 py-0.5 text-xs font-mono text-gray-700">
                    {r}
                  </span>
                ))}
              </div>
            )}

            {result.missing_info?.length > 0 && (
              <div className="mb-3 rounded-lg bg-white/70 p-3">
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">Missing information</p>
                <ul className="space-y-1">
                  {result.missing_info.map((m, i) => (
                    <li key={i} className="text-xs text-gray-600">
                      <span className="font-medium">{m.field}:</span> {m.why_it_matters}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.follow_up_questions?.length > 0 && (
              <div className="mb-3 rounded-lg bg-white/70 p-3">
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">Suggested follow-up questions</p>
                <ol className="list-decimal list-inside space-y-1">
                  {result.follow_up_questions.map((q, i) => (
                    <li key={i} className="text-xs text-gray-700">{q.question}</li>
                  ))}
                </ol>
              </div>
            )}

            <p className="mt-3 text-xs italic text-gray-500">{result.disclaimer}</p>
          </div>

          <button
            onClick={() => { setResult(null); setSymptomsText(''); setChiefComplaint(''); setConsentConfirmed(false); setConsent(false); }}
            className="w-full rounded-lg border border-gray-300 py-2.5 text-sm text-gray-600 hover:bg-gray-50"
          >
            New patient intake
          </button>
        </div>
      )}

      <DisclaimerBanner />
    </div>
  );
}
