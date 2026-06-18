import { InvestigateButton } from "@/components/InvestigateButton";
import { StatusBadge } from "@/components/StatusBadge";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center gap-8 px-4">
      <div className="text-center space-y-3">
        <h1 className="text-4xl font-bold tracking-tight">
          AI Kubernetes Agent
        </h1>
        <p className="text-lg text-gray-400">
          Troubleshoot Kubernetes with AI
        </p>
      </div>

      <InvestigateButton />

      <StatusBadge />
    </main>
  );
}
