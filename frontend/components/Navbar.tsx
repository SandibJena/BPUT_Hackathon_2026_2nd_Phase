'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useTranslation, useI18nStore } from '@/lib/i18n';
import { getUserRole, clearToken, isAuthenticated } from '@/lib/auth';
import { useState, useEffect } from 'react';
import { Cross, Menu, X } from 'lucide-react';

export default function Navbar() {
  const { t } = useTranslation();
  const { lang, setLang } = useI18nStore();
  const router = useRouter();
  const [role, setRole] = useState<string | null>(null);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) {
      setRole(getUserRole());
    }
  }, []);

  const handleLogout = () => {
    clearToken();
    setRole(null);
    router.push('/login');
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="bg-primary text-white p-1 rounded">
            <Cross size={24} />
          </div>
          <span className="font-bold text-lg hidden sm:block">TriageAssist</span>
        </div>

        <div className="hidden md:flex items-center gap-6">
          {role && (
            <>
              <Link href="/intake" className="text-gray-600 hover:text-primary font-medium">{t('Intake Form')}</Link>
              <Link href="/dashboard" className="text-gray-600 hover:text-primary font-medium">{t('Patient Queue')}</Link>
              {role === 'admin' && (
                <Link href="/admin" className="text-gray-600 hover:text-primary font-medium">{t('Admin Panel')}</Link>
              )}
            </>
          )}
        </div>

        <div className="flex items-center gap-4">
          <select 
            value={lang} 
            onChange={(e) => setLang(e.target.value as any)}
            className="border-gray-300 rounded text-sm min-h-[44px] px-2 py-1 bg-white focus:ring-primary focus:border-primary"
          >
            <option value="en">EN</option>
            <option value="hi">हिं</option>
            <option value="od">ଓ</option>
          </select>

          {role ? (
            <button onClick={handleLogout} className="text-sm font-medium text-red-600 hover:text-red-800 min-h-[44px] px-2">
              {t('Logout')}
            </button>
          ) : (
            <Link href="/login" className="text-sm font-medium text-primary hover:text-blue-800 min-h-[44px] px-2 flex items-center">
              {t('Login')}
            </Link>
          )}

          <button className="md:hidden p-2 min-h-[44px]" onClick={() => setIsMobileOpen(!isMobileOpen)}>
            {isMobileOpen ? <X /> : <Menu />}
          </button>
        </div>
      </div>

      {isMobileOpen && role && (
        <div className="md:hidden bg-white border-t border-gray-100 p-4 flex flex-col gap-4 shadow-lg">
          <Link href="/intake" onClick={() => setIsMobileOpen(false)} className="block font-medium p-2">{t('Intake Form')}</Link>
          <Link href="/dashboard" onClick={() => setIsMobileOpen(false)} className="block font-medium p-2">{t('Patient Queue')}</Link>
          {role === 'admin' && (
            <Link href="/admin" onClick={() => setIsMobileOpen(false)} className="block font-medium p-2">{t('Admin Panel')}</Link>
          )}
        </div>
      )}
    </nav>
  );
}
