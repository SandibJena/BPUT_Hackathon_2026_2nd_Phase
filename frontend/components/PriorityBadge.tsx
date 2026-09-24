'use client';

import { AlertTriangle, Shield, AlertCircle, CheckCircle, HelpCircle } from 'lucide-react';

type Priority = 'EMERGENCY' | 'HIGH' | 'INSUFFICIENT_INFO' | 'NORMAL';
type Size = 'sm' | 'md' | 'lg';

interface PriorityBadgeProps {
  category: string;
  size?: Size;
  pulse?: boolean;
}

const CONFIG: Record<Priority, {
  label: string;
  bg: string;
  text: string;
  border: string;
  icon: React.ElementType;
}> = {
  EMERGENCY: {
    label: 'EMERGENCY',
    bg: 'bg-red-600',
    text: 'text-white',
    border: 'border-red-700',
    icon: Shield,
  },
  HIGH: {
    label: 'HIGH',
    bg: 'bg-amber-500',
    text: 'text-white',
    border: 'border-amber-600',
    icon: AlertTriangle,
  },
  INSUFFICIENT_INFO: {
    label: 'INSUFFICIENT INFO',
    bg: 'bg-gray-400',
    text: 'text-white',
    border: 'border-gray-500',
    icon: HelpCircle,
  },
  NORMAL: {
    label: 'NORMAL',
    bg: 'bg-green-600',
    text: 'text-white',
    border: 'border-green-700',
    icon: CheckCircle,
  },
};

const SIZE: Record<Size, { wrapper: string; icon: string; text: string }> = {
  sm: { wrapper: 'px-2 py-0.5 gap-1', icon: 'h-3 w-3', text: 'text-xs font-semibold' },
  md: { wrapper: 'px-3 py-1 gap-1.5', icon: 'h-4 w-4', text: 'text-sm font-bold' },
  lg: { wrapper: 'px-4 py-2 gap-2', icon: 'h-5 w-5', text: 'text-base font-bold' },
};

export default function PriorityBadge({
  category,
  size = 'md',
  pulse,
}: PriorityBadgeProps) {
  const cfg = CONFIG[category as Priority] ?? {
    label: category,
    bg: 'bg-gray-300',
    text: 'text-gray-800',
    border: 'border-gray-400',
    icon: AlertCircle,
  };
  const s = SIZE[size];
  const Icon = cfg.icon;
  const shouldPulse = pulse ?? category === 'EMERGENCY';

  return (
    <span
      className={[
        'inline-flex items-center rounded-full border',
        cfg.bg, cfg.text, cfg.border, s.wrapper,
        shouldPulse ? 'animate-pulse' : '',
      ].join(' ')}
      role="status"
      aria-label={`Priority: ${cfg.label}`}
    >
      <Icon className={s.icon} aria-hidden />
      <span className={s.text}>{cfg.label}</span>
    </span>
  );
}
