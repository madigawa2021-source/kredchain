"use client";

import { useState } from "react";

export default function Home() {
  const [address, setAddress] = useState(
    "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function analyze() {
    try {
      setLoading(true);
      setError("");
      setResult(null);

      const response = await fetch(
        `https://kredchain-api.onrender.com/analyze/${address}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Analysis failed");
      }

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function getTierColor(tier) {
    switch (tier) {
      case "TRUSTED MERCHANT": return "border-green-500 bg-green-500/20 text-green-400";
      case "RELIABLE": return "border-blue-500 bg-blue-500/20 text-blue-400";
      case "DEVELOPING": return "border-yellow-500 bg-yellow-500/20 text-yellow-400";
      case "LIMITED HISTORY": return "border-orange-500 bg-orange-500/20 text-orange-400";
      default: return "border-red-500 bg-red-500/20 text-red-400";
    }
  }

  function getBarColor(tier) {
    switch (tier) {
      case "TRUSTED MERCHANT": return "bg-green-500";
      case "RELIABLE": return "bg-blue-500";
      case "DEVELOPING": return "bg-yellow-500";
      case "LIMITED HISTORY": return "bg-orange-500";
      default: return "bg-red-500";
    }
  }

  function getTierHex(tier) {
    switch (tier) {
      case "TRUSTED MERCHANT": return "#22c55e";
      case "RELIABLE": return "#3b82f6";
      case "DEVELOPING": return "#eab308";
      case "LIMITED HISTORY": return "#f97316";
      default: return "#ef4444";
    }
  }

  function downloadCertificate() {
    if (!result) return;

    const tier = result.tier;
    const color = getTierHex(tier);
    const date = new Date(result.metadata.analyzed_at).toUTCString();
    const aiStatus = result.ai?.anomaly ? "⚠ Anomalous Pattern Detected" : "✓ Normal Behavioral Pattern";
    const utxoWarning = !result.metadata?.utxo_data_available
      ? `<div style="background:#7c2d0e;border:1px solid #f97316;color:#fed7aa;padding:10px;border-radius:6px;margin:16px 0;font-size:13px;">
          ⚠ UTXO data unavailable — some features estimated from transaction history
        </div>` : "";

    const featureRows = Object.entries(result.features)
      .map(([key, f]) => `
        <tr>
          <td style="padding:8px;border-bottom:1px solid #374151;color:#9ca3af;">${f.feature_name}</td>
          <td style="padding:8px;border-bottom:1px solid #374151;text-align:center;">${f.raw}</td>
          <td style="padding:8px;border-bottom:1px solid #374151;text-align:center;">
            <div style="background:#374151;border-radius:4px;overflow:hidden;height:8px;width:100px;margin:auto;">
              <div style="background:${color};height:100%;width:${Math.round(f.normalized * 100)}%;"></div>
            </div>
          </td>
          <td style="padding:8px;border-bottom:1px solid #374151;text-align:right;color:${color};">+${f.contribution}</td>
        </tr>
      `).join("");

    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <title>KredChain Trust Certificate</title>
  <style>
    @media print { body { -webkit-print-color-adjust: exact; } }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #030712; color: #f9fafb; padding: 40px; min-height: 100vh; }
  </style>
</head>
<body>
  <div style="text-align:center;margin-bottom:32px;">
    <div style="font-size:36px;font-weight:900;color:#f97316;letter-spacing:2px;">KredChain</div>
    <div style="color:#6b7280;font-size:14px;margin-top:4px;">Decentralized Trust Layer for the Unbanked</div>
    <div style="border-top:1px solid #374151;margin-top:20px;"></div>
  </div>
  <div style="text-align:center;margin-bottom:32px;">
    <div style="font-size:13px;color:#6b7280;letter-spacing:3px;text-transform:uppercase;">Bitcoin Reputation Certificate</div>
    <div style="font-size:12px;color:#4b5563;margin-top:8px;">Issued: ${date}</div>
  </div>
  <div style="display:flex;justify-content:center;margin-bottom:32px;">
    <div style="width:160px;height:160px;border-radius:50%;border:6px solid ${color};display:flex;flex-direction:column;align-items:center;justify-content:center;background:${color}18;">
      <div style="font-size:48px;font-weight:900;color:${color};">${result.score}</div>
      <div style="font-size:11px;color:${color};margin-top:2px;">out of 100</div>
    </div>
  </div>
  <div style="text-align:center;margin-bottom:8px;">
    <span style="background:${color}22;border:1px solid ${color};color:${color};padding:6px 20px;border-radius:20px;font-weight:700;font-size:14px;">${tier}</span>
  </div>
  <div style="text-align:center;margin:20px 0;color:#9ca3af;font-size:13px;">
    Address: <span style="color:#f9fafb;font-family:monospace;">${result.address}</span>
  </div>
  ${utxoWarning}
  <div style="background:#111827;border:1px solid #374151;border-radius:8px;padding:12px 20px;margin-bottom:24px;display:flex;justify-content:space-between;align-items:center;">
    <span style="color:#6b7280;font-size:13px;">AI Anomaly Detection</span>
    <span style="color:${result.ai?.anomaly ? "#f87171" : "#4ade80"};font-weight:600;font-size:13px;">${aiStatus}</span>
  </div>
  <div style="background:#111827;border:1px solid #374151;border-radius:8px;overflow:hidden;margin-bottom:32px;">
    <div style="padding:16px 20px;border-bottom:1px solid #374151;">
      <span style="font-weight:700;font-size:15px;">Score Breakdown</span>
    </div>
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:#1f2937;">
          <th style="padding:10px;text-align:left;color:#6b7280;font-size:12px;">Feature</th>
          <th style="padding:10px;text-align:center;color:#6b7280;font-size:12px;">Raw Value</th>
          <th style="padding:10px;text-align:center;color:#6b7280;font-size:12px;">Signal</th>
          <th style="padding:10px;text-align:right;color:#6b7280;font-size:12px;">Points</th>
        </tr>
      </thead>
      <tbody>${featureRows}</tbody>
    </table>
  </div>
  <div style="border-top:1px solid #374151;padding-top:20px;display:flex;justify-content:space-between;font-size:11px;color:#4b5563;">
    <div>Data Source: ${result.metadata.data_source}</div>
    <div>Model: ${result.metadata.model_version}</div>
    <div>KredChain — Decentralized AI Reputation Protocol</div>
  </div>
</body>
</html>`;

    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `kredchain-certificate-${result.address.slice(0, 10)}.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const tierColor = result ? getTierColor(result.tier) : "";
  const barColor = result ? getBarColor(result.tier) : "";

  const descriptions = {
    "F1 account_age_days": "How long this address has been active — older addresses signal established history",
    "F2 oldest_utxo_age_days": "Age of the oldest unspent coin — long-held funds indicate financial stability",
    "F3 active_months_ratio": "Consistency of activity over time — regular usage signals a real business",
    "F4 tx_frequency_weekly_std": "Stability of weekly transaction rate — low variance means predictable cash flow",
    "F5 monthly_volume_cv": "Monthly volume consistency — stable income patterns increase creditworthiness",
    "F6 avg_utxo_age_days": "Average age of unspent outputs — older holdings signal responsible fund management",
    "F7 script_type_score": "Bitcoin script sophistication — modern script types signal technical awareness",
    "F8 counterparty_diversity": "Number of unique transaction partners — high diversity signals active commerce",
    "F9 utxo_count": "Number of spendable outputs — confirms wallet is actively receiving payments",
    "F10 total_tx_count": "Total lifetime transactions — more transactions mean a longer verifiable track record",
    "F11 incoming_outgoing_ratio": "Ratio of incoming vs outgoing — higher incoming ratio signals merchant activity",
    "F12 recency_score": "How recently this address was active — recent activity confirms ongoing operations",
    "F13 avg_tx_value_sats": "Average transaction size — reflects the scale of business operations",
    "F14 address_reuse_score": "Privacy practice score — lower reuse indicates better financial hygiene",
  };

  return (
    <main className="min-h-screen bg-gray-950 text-white px-6 py-10">
      <div className="max-w-5xl mx-auto">

        {/* HEADER */}
        <div className="text-center mb-10">
          <h1 className="text-5xl font-bold text-orange-500">KredChain</h1>
          <p className="text-gray-400 mt-3">
            Decentralized Trust Layer for the Unbanked
          </p>
        </div>

        {/* INPUT */}
        <div className="flex gap-3 mb-10">
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="Enter Bitcoin address..."
            className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-orange-500"
          />
          <button
            onClick={analyze}
            className="bg-orange-500 hover:bg-orange-600 px-6 py-3 rounded-lg font-semibold"
          >
            Analyze
          </button>
        </div>

        {/* LOADING */}
        {loading && (
          <div className="flex justify-center py-20">
            <div className="w-16 h-16 border-4 border-gray-700 border-t-orange-500 rounded-full animate-spin" />
          </div>
        )}

        {/* ERROR */}
        {error && (
          <div className="bg-red-900/30 border border-red-500 text-red-400 p-4 rounded-lg text-center">
            {error}
          </div>
        )}

        {/* RESULTS */}
        {!loading && result && (
          <div>

            {/* SCORE CIRCLE */}
            <div className="flex flex-col items-center">
              <div className={`w-56 h-56 rounded-full border-8 flex items-center justify-center text-5xl font-bold ${tierColor}`}>
                {result.score}
              </div>
              <div className={`mt-5 px-5 py-2 rounded-full font-semibold ${tierColor}`}>
                {result.tier}
              </div>
            </div>

            {/* DOWNLOAD BUTTON */}
            <div className="flex justify-center mt-6">
              <button
                onClick={downloadCertificate}
                className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 border border-gray-600 hover:border-orange-500 text-white px-6 py-3 rounded-lg font-semibold transition-all"
              >
                <span>📄</span>
                <span>Download Trust Certificate</span>
              </button>
            </div>

           {/* AI SCORING */}
{result.ai && result.ai.enabled && (
  <div className="mt-8 bg-gray-900 rounded-xl p-5">
    <div className="flex items-center justify-between">
      <div>
        <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">
          Decentralized AI Score
        </div>
        <div className="text-xs text-gray-600">
          GradientBoosting Regressor · {result.metadata.training_samples || 309} addresses · 14 features · R² 0.93
        </div>
      </div>
      <div className="text-right">
        <div className={`text-4xl font-bold ${tierColor.split(' ').find(c => c.startsWith('text-')) || 'text-orange-400'}`}>
          {result.ai.ai_score}
        </div>
        <div className="text-xs text-gray-500 mt-1">out of 100</div>
      </div>
    </div>
  </div>
)}

            {/* UTXO WARNING */}
            {!result.metadata?.utxo_data_available && (
              <div className="mt-8 bg-yellow-900/30 border border-yellow-500 text-yellow-300 rounded-lg p-3 text-center">
                ⚠ UTXO data unavailable — F1/F2/F6/F9 estimated
              </div>
            )}

            {/* BREAKDOWN */}
            <div className="mt-12">
              <h2 className="text-2xl font-bold mb-6">Score Breakdown</h2>
              <div className="space-y-4">
                {Object.entries(result.features).map(([key, feature]) => {
                  const percent = feature.normalized * 100;
                  const desc = descriptions[feature.feature_name] || "";
                  return (
                    <div key={key} className="bg-gray-900 p-4 rounded-lg">
                      <div className="flex justify-between text-sm mb-1">
  <span className="font-medium">{feature.feature_name}</span>
  <span className="text-gray-400 text-xs">{Math.round(feature.normalized * 100)}% signal</span>
</div>
                      {desc && (
                        <p className="text-xs text-gray-500 mb-2">{desc}</p>
                      )}
                      <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${barColor} transition-all duration-500`}
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-gray-600 mt-1">
                        <span>Raw: {feature.raw}</span>
                        <span>{Math.round(percent)}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* METADATA */}
            <div className="mt-10 text-sm text-gray-400 border-t border-gray-800 pt-5">
              <div>Address: {result.address.slice(0, 12)}...{result.address.slice(-8)}</div>
              <div>Time: {result.metadata.analyzed_at}</div>
              <div>Source: {result.metadata.data_source}</div>
              <div>Training samples: {result.metadata.training_samples}</div>
              {result.metadata.retrain_triggered && (
                <div className="text-green-400 mt-1">✓ AI model retrained with new data</div>
              )}
            </div>

          </div>
        )}
      </div>
    </main>
  );
}