'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { TriageNote } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import PriorityBadge from '@/components/PriorityBadge';
import { DISCLAIMER } from '@/lib/constants';

export default function PatientNotePage({ params }: { params: { id: string } }) {
  const [note, setNote] = useState<TriageNote | null>(null);
  
  useEffect(() => {
    api.notes.get(params.id).then(setNote).catch(console.error);
  }, [params.id]);

  if (!note) return <LoadingSpinner />;

  return (
    <div className="max-w-6xl mx-auto p-4 pb-24 grid md:grid-cols-2 gap-6">
      <div className="space-y-6">
        <div className="card">
          <h2 className="font-bold text-lg mb-2">Original Input</h2>
          <div className="bg-gray-50 p-4 rounded text-gray-700 whitespace-pre-wrap text-sm border">
            {note.raw_input_text}
          </div>
        </div>
        
        {note.risk_assessment.missing_critical_info.length > 0 && (
          <div className="card bg-amber-50 border-amber-200">
            <h3 className="font-bold text-amber-800 mb-2">Missing Critical Info</h3>
            <ul className="list-disc pl-5 text-sm text-amber-900">
              {note.risk_assessment.missing_critical_info.map((i, idx) => <li key={idx}>{i}</li>)}
            </ul>
          </div>
        )}
      </div>

      <div className="space-y-6">
        <div className="card border-t-4 border-t-primary shadow-lg">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-xl font-bold">Structured Triage Note</h1>
              <div className="text-sm text-gray-500 font-mono mt-1">ID: {note.patient_info.patient_id}</div>
            </div>
            <PriorityBadge category={note.risk_assessment.priority} size="lg" />
          </div>

          <div className="mb-4">
            <span className="text-xs font-semibold uppercase text-gray-500 block mb-1">Chief Complaint</span>
            <p className="font-medium">{note.chief_complaint || 'None identified'}</p>
          </div>

          <div className="mb-4">
            <span className="text-xs font-semibold uppercase text-gray-500 block mb-1">Extracted Symptoms</span>
            <div className="flex flex-wrap gap-2">
              {note.symptoms.map((s, idx) => (
                <span key={idx} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                  {s.name} {s.severity && `(${s.severity})`} {s.duration && `- ${s.duration}`}
                </span>
              ))}
            </div>
          </div>

          <div className="mb-4">
            <span className="text-xs font-semibold uppercase text-gray-500 block mb-1">Risk Reasons</span>
            <ul className="list-disc pl-5 text-sm">
              {note.risk_assessment.reasons.map((r, idx) => <li key={idx}>{r}</li>)}
            </ul>
          </div>

          <div className="mt-8 border-t pt-4">
            <p className="text-xs text-center text-gray-500 font-bold uppercase">{DISCLAIMER}</p>
          </div>
        </div>

        <div className="flex gap-4">
          <button className="btn-primary flex-1">Approve Note</button>
          <button className="btn-secondary flex-1">Request Info</button>
        </div>
      </div>
    </div>
  );
}
