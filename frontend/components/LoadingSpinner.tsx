export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="w-8 h-8 border-4 border-blue-200 border-t-primary rounded-full animate-spin"></div>
    </div>
  );
}
