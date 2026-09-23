import { AlertTriangle } from 'lucide-react';
import { DISCLAIMER } from '@/lib/constants';

interface DisclaimerBannerProps {
  position?: 'top' | 'bottom';
}

export default function DisclaimerBanner({ position = 'bottom' }: DisclaimerBannerProps) {
  return (
    <div 
      className={`fixed ${position === 'bottom' ? 'bottom-0' : 'top-0'} left-0 right-0 z-50 bg-amber-100 text-amber-900 px-4 py-2 flex items-center justify-center border-${position === 'bottom' ? 't' : 'b'} border-amber-300 shadow-md`}
      role="alert"
    >
      <AlertTriangle className="w-5 h-5 mr-2 flex-shrink-0 text-amber-600" />
      <span className="text-sm font-semibold text-center leading-tight">
        {DISCLAIMER}
      </span>
    </div>
  );
}
