export default function LoadingScreen() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-surface-900">
      <div className="flex flex-col items-center gap-4">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 border-2 border-primary-500/30 rounded-full animate-ping" />
          <div className="absolute inset-2 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
        </div>
        <p className="text-slate-400 text-sm animate-pulse">Loading PriceTracker...</p>
      </div>
    </div>
  )
}
