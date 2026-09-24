'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  RefreshCw, X, CheckCircle, AlertTriangle, ArrowUpCircle,
  ClipboardCheck, Clock, Users, Shield, ChevronRight, LogOut,
} from 'lucide-react';
import PriorityBadge from '@/components/PriorityBadge';
import DisclaimerBanner from '@/components/DisclaimerBanner';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';
const REFRESH_MS = 30_000;

// ── Types ────────────────────────────────────────────────────────────────────
interface NoteListItem {
  id: string;
  pseudonym_id: string;
  chief_complaint: string | null;
  risk_category: string;
  review_status: string;
  facility_type: string | null;
  created_at: string | null;
  triggered_rules: string[];
  symptoms_preview: string[];
}

interface NoteDetail {
  id: string;
  pseudonym_id: string;
  age_band: string;
  sex: string | null;
  language: string;
  facility_type: string;
  scenario: string;
  chief_complaint: string | null;
  symptoms: { name: string; assertion: string; evidence?: string }[];
  vitals: Record<string, number | null>;
  history: { chronic_conditions?: string[]; meds_mentioned?: string[] };
  missing_info: { field: string; why_it_matters: string }[];
  follow_up_questions: { question: string; target_role: string }[];
  risk_category: string;
  risk_reasons: string[];
  triggered_rules: string[];
  risk_source: string;
  review_status: string;
  reviewer_comments: string[];
  disclaimer: string;
  created_at: string | null;
}

interface Stats {
  total: number;
  pending: number;
  approved: number;
  emergency: number;
  high: number;
  insufficient_info: number;
  normal: number;
}

// ── Status badge ─────────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
  const cfg: Record<string, string> = {
    pending:   'bg-yellow-100 text-yellow-800 border-yellow-300',
    approved:  'bg-green-100 text-green-800 border-green-300',
    escalated: 'bg-red-100 text-red-800 border-red-300',
    edited:    'bg-blue-100 text-blue-800 border-blue-300',
    closed:    'bg-gray-100 text-gray-600 border-gray-300',
  };
  return (
    <span className={`inline-block rounded-full border px-2 py-0.5 text-xs font-semibold ${cfg[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  );
}

// ── Review Modal ──────────────────────────────────────────────────────────────
function ReviewModal({
  note,
  userRole,
  token,
  onClose,
  onDone,
}: {
  note: NoteDetail;
  userRole: string;
  token: string;
  onClose: () => void;
  onDone: () => void;
}) {
  const [comment, setComment] = useState('');
  const [signoff, setSignoff] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState('');

  const canApprove = userRole === 'nurse' || userRole === 'doctor' || userRole === 'admin';

  async function submitReview(newStatus: string) {
    setErr('');
    setSubmitting(true);
    try {
      const resp = await fetch(`${API}/notes/${note.id}/review`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ review_status: newStatus, comment, signoff }),
      });
      if (!resp.ok) {
        const e = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(e.detail ?? 'Review failed');
      }
      onDone();
      onClose();
    } catch (e: any) {
      setErr(e.message ?? 'Error submitting review');
    } finally {
      setSubmitting(false);
    }
  }

  const approveOk = canApprove && signoff && comment.trim().length > 3;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 p-4 pt-8">
      <div className="w-full max-w-2xl rounded-2xl bg-white shadow-2xl">
        {/* Header */}
        <div className={`flex items-center justify-between rounded-t-2xl p-4 ${
          note.risk_category === 'EMERGENCY' ? 'bg-red-600 text-white' :
          note.risk_category === 'HIGH' ? 'bg-amber-500 text-white' : 'bg-gray-100 text-gray-900'
        }`}>
          <div className="flex items-center gap-3">
            <PriorityBadge category={note.risk_category} size="md" />
            <div>
              <p className="font-bold">{note.pseudonym_id}</p>
              <p className="text-xs opacity-80">
                {note.age_band} · {note.sex ?? 'sex not specified'} · {note.facility_type}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="rounded-full p-1.5 hover:bg-black/10">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4 p-5">
          {/* Disclaimer */}
          <div className="flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-xs text-amber-800">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            {note.disclaimer}
          </div>

          {/* Chief complaint */}
          {note.chief_complaint && (
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">Chief Complaint</p>
              <p className="text-sm font-medium text-gray-800">{note.chief_complaint}</p>
            </div>
          )}

          {/* Urgency signals */}
          {note.risk_reasons.length > 0 && (
            <div className="rounded-lg bg-red-50 p-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-red-600">Urgency Signals</p>
              <ul className="space-y-1">
                {note.risk_reasons.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-red-800">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" />
                    {r}
                  </li>
                ))}
              </ul>
              {note.triggered_rules.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {note.triggered_rules.map((r) => (
                    <span key={r} className="rounded bg-red-200 px-1.5 py-0.5 text-xs font-mono text-red-800">{r}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Symptoms */}
          {note.symptoms.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Reported Symptoms</p>
              <div className="flex flex-wrap gap-1.5">
                {note.symptoms
                  .filter((s) => s.assertion === 'reported')
                  .map((s, i) => (
                    <span key={i} className="rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-700">
                      {s.name.replace(/_/g, ' ')}
                    </span>
                  ))}
              </div>
            </div>
          )}

          {/* Vitals */}
          {Object.values(note.vitals).some((v) => v != null) && (
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Vitals</p>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { key: 'spo2', label: 'SpO₂', unit: '%', warn: (v: number) => v < 92 },
                  { key: 'pulse', label: 'Pulse', unit: 'bpm', warn: () => false },
                  { key: 'temp', label: 'Temp', unit: '°C', warn: (v: number) => v > 38 },
                  { key: 'bp_sys', label: 'BP Sys', unit: 'mmHg', warn: (v: number) => v > 160 },
                  { key: 'bp_dia', label: 'BP Dia', unit: 'mmHg', warn: (v: number) => v > 100 },
                  { key: 'resp_rate', label: 'Resp', unit: '/min', warn: (v: number) => v > 25 },
                ].map(({ key, label, unit, warn }) => {
                  const val = (note.vitals as any)[key];
                  if (val == null) return null;
                  const isWarn = warn(val);
                  return (
                    <div
                      key={key}
                      className={`rounded-lg border p-2 text-center ${isWarn ? 'border-red-300 bg-red-50' : 'border-gray-200 bg-gray-50'}`}
                    >
                      <p className="text-xs text-gray-500">{label}</p>
                      <p className={`text-base font-bold ${isWarn ? 'text-red-700' : 'text-gray-900'}`}>
                        {val} <span className="text-xs font-normal">{unit}</span>
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Missing info */}
          {note.missing_info.length > 0 && (
            <div className="rounded-lg bg-yellow-50 p-3">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-yellow-700">Missing Information</p>
              <ul className="space-y-1">
                {note.missing_info.map((m, i) => (
                  <li key={i} className="text-xs text-yellow-800">
                    <span className="font-medium">{m.field}:</span> {m.why_it_matters}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Follow-up questions */}
          {note.follow_up_questions.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">Follow-up Questions</p>
              <ol className="list-decimal list-inside space-y-1">
                {note.follow_up_questions.map((q, i) => (
                  <li key={i} className="text-xs text-gray-700">{q.question}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Existing comments */}
          {note.reviewer_comments.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">Previous Comments</p>
              {note.reviewer_comments.map((c, i) => (
                <p key={i} className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600">{c}</p>
              ))}
            </div>
          )}

          {/* Review actions */}
          {canApprove && note.review_status !== 'approved' && note.review_status !== 'closed' && (
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
              <p className="mb-3 text-sm font-semibold text-gray-800">Reviewer Action</p>

              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Add a reviewer comment (required to approve or close)…"
                rows={3}
                className="mb-3 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />

              <label className="mb-4 flex cursor-pointer items-start gap-2.5">
                <input
                  type="checkbox"
                  className="mt-0.5 h-5 w-5 rounded"
                  checked={signoff}
                  onChange={(e) => setSignoff(e.target.checked)}
                />
                <span className="text-xs text-gray-700">
                  I confirm I have reviewed this note as a qualified health professional.
                  This is an advisory summary only — not a medical diagnosis or treatment plan.
                </span>
              </label>

              {err && (
                <p className="mb-3 flex items-center gap-2 rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">
                  <AlertTriangle className="h-3.5 w-3.5" /> {err}
                </p>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => submitReview('escalated')}
                  disabled={submitting}
                  className="flex min-h-[44px] flex-1 items-center justify-center gap-1.5 rounded-lg border border-orange-400 bg-orange-50 text-sm font-semibold text-orange-700 hover:bg-orange-100 disabled:opacity-50"
                >
                  <ArrowUpCircle className="h-4 w-4" />
                  Escalate
                </button>
                <button
                  onClick={() => submitReview('approved')}
                  disabled={!approveOk || submitting}
                  className="flex min-h-[44px] flex-1 items-center justify-center gap-1.5 rounded-lg bg-green-700 text-sm font-semibold text-white hover:bg-green-800 disabled:opacity-40"
                >
                  <CheckCircle className="h-4 w-4" />
                  Approve & Sign Off
                </button>
              </div>
              {!approveOk && (
                <p className="mt-2 text-xs text-gray-400 text-center">
                  Sign-off checkbox + comment required to approve
                </p>
              )}
            </div>
          )}

          {!canApprove && (
            <p className="rounded-lg bg-gray-100 px-3 py-2 text-xs text-gray-500">
              Your role (viewer) can read notes but cannot approve. Contact a nurse or doctor.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState('');
  const [userRole, setUserRole] = useState('health_worker');
  const [notes, setNotes] = useState<NoteListItem[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNote, setSelectedNote] = useState<NoteDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    const t = localStorage.getItem('auth_token') ?? '';
    const r = localStorage.getItem('user_role') ?? 'health_worker';
    if (!t) { router.push('/login'); return; }
    setToken(t);
    setUserRole(r);
  }, [router]);

  const fetchNotes = useCallback(async (tk: string) => {
    if (!tk) return;
    const params = new URLSearchParams();
    if (filterStatus) params.set('review_status', filterStatus);
    if (filterPriority) params.set('risk_category', filterPriority);
    try {
      const [nResp, sResp] = await Promise.all([
        fetch(`${API}/notes?${params}`, { headers: { Authorization: `Bearer ${tk}` } }),
        fetch(`${API}/notes/stats`, { headers: { Authorization: `Bearer ${tk}` } }),
      ]);
      if (nResp.ok) setNotes(await nResp.json());
      if (sResp.ok) setStats(await sResp.json());
    } finally {
      setLoading(false);
    }
  }, [filterStatus, filterPriority]);

  useEffect(() => {
    if (!token) return;
    fetchNotes(token);
    timerRef.current = setInterval(() => fetchNotes(token), REFRESH_MS);
    return () => clearInterval(timerRef.current);
  }, [token, fetchNotes]);

  async function openNote(id: string) {
    setLoadingDetail(true);
    try {
      const resp = await fetch(`${API}/notes/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) setSelectedNote(await resp.json());
    } finally {
      setLoadingDetail(false);
    }
  }

  function logout() {
    localStorage.clear();
    router.push('/login');
  }

  if (!token) return null;

  const emergencyNotes = notes.filter((n) => n.risk_category === 'EMERGENCY');

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      {/* Navbar */}
      <header className="sticky top-0 z-40 border-b border-gray-200 bg-white px-4 py-3">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-700" />
            <span className="font-bold text-gray-900">Triage Dashboard</span>
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">{userRole}</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => fetchNotes(token)}
              className="flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </button>
            <button
              onClick={() => router.push('/intake')}
              className="rounded-lg bg-blue-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-800"
            >
              + New Intake
            </button>
            <button onClick={logout} className="p-1.5 text-gray-400 hover:text-gray-600">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-4 py-5">
        {/* EMERGENCY alert banner */}
        {emergencyNotes.length > 0 && (
          <div className="mb-4 flex animate-pulse items-center gap-3 rounded-xl bg-red-600 px-4 py-3 text-white">
            <Shield className="h-5 w-5 shrink-0" />
            <div>
              <p className="font-bold text-sm">
                {emergencyNotes.length} EMERGENCY {emergencyNotes.length === 1 ? 'case' : 'cases'} require immediate attention
              </p>
              <p className="text-xs opacity-90">
                {emergencyNotes.map((n) => n.pseudonym_id).join(', ')}
              </p>
            </div>
          </div>
        )}

        {/* Stats row */}
        {stats && (
          <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: 'Total Notes', value: stats.total, icon: ClipboardCheck, color: 'text-gray-700' },
              { label: 'Pending Review', value: stats.pending, icon: Clock, color: 'text-amber-600' },
              { label: 'Emergency', value: stats.emergency, icon: Shield, color: 'text-red-600' },
              { label: 'Approved', value: stats.approved, icon: CheckCircle, color: 'text-green-600' },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="rounded-xl border border-gray-200 bg-white p-3 shadow-sm">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-gray-500">{label}</p>
                  <Icon className={`h-4 w-4 ${color}`} />
                </div>
                <p className={`mt-1 text-2xl font-bold ${color}`}>{value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Filters */}
        <div className="mb-4 flex flex-wrap gap-2">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="escalated">Escalated</option>
            <option value="closed">Closed</option>
          </select>
          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">All priorities</option>
            <option value="EMERGENCY">🔴 Emergency</option>
            <option value="HIGH">🟡 High</option>
            <option value="INSUFFICIENT_INFO">⬜ Insufficient Info</option>
            <option value="NORMAL">🟢 Normal</option>
          </select>
          <span className="self-center text-xs text-gray-400">
            Auto-refreshes every 30s
          </span>
        </div>

        {/* Note list */}
        {loading ? (
          <div className="flex items-center justify-center py-16 text-gray-400">
            <RefreshCw className="mr-2 h-5 w-5 animate-spin" />
            Loading notes…
          </div>
        ) : notes.length === 0 ? (
          <div className="rounded-xl border border-dashed border-gray-300 py-16 text-center text-gray-400">
            <Users className="mx-auto mb-2 h-8 w-8 opacity-40" />
            <p className="text-sm">No triage notes found.</p>
            <button
              onClick={() => router.push('/intake')}
              className="mt-3 rounded-lg bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800"
            >
              Create first intake
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {notes.map((note) => (
              <button
                key={note.id}
                onClick={() => openNote(note.id)}
                disabled={loadingDetail}
                className={`w-full rounded-xl border bg-white p-4 text-left shadow-sm transition-all hover:shadow-md ${
                  note.risk_category === 'EMERGENCY'
                    ? 'border-red-400 ring-1 ring-red-300'
                    : note.risk_category === 'HIGH'
                    ? 'border-amber-300'
                    : 'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="font-semibold text-gray-900 text-sm">{note.pseudonym_id}</span>
                      <PriorityBadge category={note.risk_category} size="sm" />
                      <StatusBadge status={note.review_status} />
                    </div>
                    {note.chief_complaint && (
                      <p className="text-sm text-gray-700 truncate">{note.chief_complaint}</p>
                    )}
                    {note.symptoms_preview.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {note.symptoms_preview.map((s) => (
                          <span key={s} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                            {s.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    )}
                    {note.triggered_rules.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {note.triggered_rules.map((r) => (
                          <span key={r} className="rounded bg-red-100 px-1.5 py-0.5 text-xs font-mono text-red-700">{r}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="shrink-0 flex flex-col items-end gap-1">
                    {note.created_at && (
                      <span className="text-xs text-gray-400">
                        {new Date(note.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    )}
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Review modal */}
      {selectedNote && (
        <ReviewModal
          note={selectedNote}
          userRole={userRole}
          token={token}
          onClose={() => setSelectedNote(null)}
          onDone={() => fetchNotes(token)}
        />
      )}

      <DisclaimerBanner />
    </div>
  );
}
