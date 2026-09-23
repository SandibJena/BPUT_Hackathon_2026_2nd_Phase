'use client';
import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { useTranslation } from '@/lib/i18n';

interface ConsentModalProps {
  isOpen: boolean;
  onConsent: () => void;
}

export default function ConsentModal({ isOpen, onConsent }: ConsentModalProps) {
  const { t } = useTranslation();
  const [checked, setChecked] = useState(false);

  return (
    <Dialog.Root open={isOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white p-6 rounded-lg shadow-xl z-50 w-[90vw] max-w-md">
          <Dialog.Title className="text-xl font-bold mb-4">Consent Required</Dialog.Title>
          <div className="mb-6">
            <label className="flex items-start gap-3 cursor-pointer">
              <input 
                type="checkbox" 
                className="w-5 h-5 mt-1"
                checked={checked}
                onChange={(e) => setChecked(e.target.checked)}
              />
              <span className="text-sm text-gray-700 leading-tight">
                {t('Consent Disclaimer')}
              </span>
            </label>
          </div>
          <button 
            onClick={onConsent}
            disabled={!checked}
            className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {t('Proceed')}
          </button>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
