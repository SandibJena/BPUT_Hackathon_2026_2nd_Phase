import { PRIORITY_COLORS, PRIORITY_LABELS } from '@/lib/constants';
import { PriorityCategory } from '@/lib/types';
import clsx from 'clsx';

interface PriorityBadgeProps {
  category: PriorityCategory;
  size?: 'sm' | 'md' | 'lg';
}

export default function PriorityBadge({ category, size = 'md' }: PriorityBadgeProps) {
  const isEmergency = category === 'EMERGENCY';
  const colorClass = PRIORITY_COLORS[category] || 'bg-gray-500';
  const label = PRIORITY_LABELS[category] || category;

  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-2 font-bold',
  };

  return (
    <span 
      className={clsx(
        'inline-flex items-center rounded-full text-white font-medium whitespace-nowrap',
        colorClass,
        sizeClasses[size],
        isEmergency && 'animate-pulse'
      )}
    >
      {label}
    </span>
  );
}
