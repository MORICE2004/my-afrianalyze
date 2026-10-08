// Skeletons for pages whose shape is known before their data arrives. Server components: no JavaScript needed.
export function Block({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} aria-hidden />;
}

export function WorkspaceSkeleton() {
  return (
    <div className="space-y-5" aria-busy="true" aria-label="Loading company research">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2"><Block className="h-3 w-40" /><Block className="h-8 w-72" /><Block className="h-4 w-56" /></div>
        <div className="space-y-2 lg:items-end"><Block className="h-8 w-52" /><Block className="h-4 w-44" /></div>
      </div>
      <Block className="h-12 w-full rounded-xl" />
      <Block className="h-32 w-full rounded-xl" />
      <div className="grid gap-5 lg:grid-cols-3"><Block className="h-80 rounded-xl lg:col-span-2" /><Block className="h-80 rounded-xl" /></div>
    </div>
  );
}

export function MarketsSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading markets">
      <div className="space-y-2"><Block className="h-7 w-40" /><Block className="h-4 w-80" /></div>
      <div className="grid gap-5 lg:grid-cols-3"><Block className="h-96 rounded-xl lg:col-span-2" /><Block className="h-96 rounded-xl" /></div>
      <div className="grid gap-5 lg:grid-cols-3"><Block className="h-72 rounded-xl" /><Block className="h-72 rounded-xl lg:col-span-2" /></div>
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-8" aria-busy="true" aria-label="Loading">
      <div className="mx-auto max-w-3xl space-y-4 pt-10"><Block className="mx-auto h-9 w-80" /><Block className="mx-auto h-4 w-96 max-w-full" /><Block className="h-14 w-full rounded-lg" /></div>
      <Block className="h-40 w-full rounded-xl" />
      <Block className="h-36 w-full rounded-xl" />
    </div>
  );
}
