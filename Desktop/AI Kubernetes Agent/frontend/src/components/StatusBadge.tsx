"use client";

import { useHealth } from "@/hooks/useHealth";

export function StatusBadge() {
  const { data, isLoading, isError } = useHealth();

  if (isLoading) {
    return (
      <p className="text-sm text-gray-400">
        System Status:{" "}
        <span className="text-yellow-400 font-medium">Checking...</span>
      </p>
    );
  }

  if (isError || !data) {
    return (
      <p className="text-sm text-gray-400">
        System Status:{" "}
        <span className="text-red-400 font-medium">Unavailable</span>
      </p>
    );
  }

  return (
    <p className="text-sm text-gray-400">
      System Status:{" "}
      <span className="text-green-400 font-medium">Ready</span>
    </p>
  );
}
