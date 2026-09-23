'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { TriageNote } from '@/lib/types';
import PriorityBadge from '@/components/PriorityBadge';
import LoadingSpinner from '@/components/LoadingSpinner';
import { useTranslation } from '@/lib/i18n';
import { AlertCircle } from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const { t } = useTranslation();
  const [notes, setNotes] = useState<TriageNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasEmergency, setHasEmergency] = useState(false);

  useEffect(() => {
    const fetchNotes = async () => {
      try {
        const data = await api.notes.list();
        setNotes(data);
        setHasEmergency(data.some(n => n.risk_assessment.priority === 'EMERGENCY' && n.status === 'PENDING'));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchNotes();
    const interval = setInterval(fetchNotes, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="max-w-7xl mx-auto p-4 pb-24">
      {hasEmergency && (
        <div className="bg-red-600 text-white p-3 rounded mb-6 flex items-center shadow-lg font-bold">
          <AlertCircle className="mr-2 animate-pulse" />
          EMERGENCY CASES WAITING FOR REVIEW
        </div>
      )}

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">{t('Patient Queue')}</h1>
        <button onClick={() => router.push('/intake')} className="btn-primary">New Patient</button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[600px]">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="p-4 font-medium">Patient ID</th>
                <th className="p-4 font-medium">Priority</th>
                <th className="p-4 font-medium">Chief Complaint</th>
                <th className="p-4 font-medium">Status</th>
                <th className="p-4 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {notes.length === 0 && (
                <tr><td colSpan={5} className="p-8 text-center text-gray-500">No patients in queue</td></tr>
              )}
              {notes.map(note => (
                <tr key={note.id} className={`border-b hover:bg-gray-50 ${note.risk_assessment.priority === 'EMERGENCY' ? 'bg-red-50' : ''}`}>
                  <td className="p-4 font-mono text-sm">{note.patient_info.patient_id}</td>
                  <td className="p-4">
                    <PriorityBadge category={note.risk_assessment.priority} size="sm" />
                  </td>
                  <td className="p-4 truncate max-w-xs">{note.chief_complaint || 'N/A'}</td>
                  <td className="p-4 text-sm">{note.status}</td>
                  <td className="p-4">
                    <button onClick={() => router.push(`/patient/${note.id}`)} className="btn-secondary text-sm">
                      Review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
