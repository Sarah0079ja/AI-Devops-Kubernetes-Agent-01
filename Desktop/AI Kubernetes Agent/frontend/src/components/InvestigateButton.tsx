"use client";

import { useState } from "react";

export function InvestigateButton() {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    // AI investigation will be wired here in a future prompt
    setTimeout(() => setLoading(false), 1000);
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 active:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
    >
      {loading ? "Investigating..." : "Investigate Cluster"}
    </button>
  );
}
