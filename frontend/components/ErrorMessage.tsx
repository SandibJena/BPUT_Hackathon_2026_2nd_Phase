import { AlertCircle } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="card border-red-200 bg-red-50 text-red-800 flex flex-col items-center p-6 text-center">
      <AlertCircle className="w-10 h-10 text-red-500 mb-3" />
      <p className="mb-4">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary min-h-[44px]">
          Try Again
        </button>
      )}
    </div>
  );
}
