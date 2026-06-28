import { useState } from 'react'

export default function TechDetails({ styleDna, promptBundle, requestId }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="mt-6">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
      >
        <span className={`transition-transform ${open ? 'rotate-90' : ''}`}>▶</span>
        技术详情
      </button>

      {open && (
        <div className="mt-3 bg-[#1e1e2e] rounded-xl border border-white/5 p-5 space-y-4 animate-fade-in-up">
          {/* StyleDNA */}
          {styleDna && (
            <div>
              <h4 className="text-xs font-medium text-blue-400 mb-2">StyleDNA</h4>
              <pre className="text-xs text-slate-400 bg-black/30 rounded-lg p-3 overflow-x-auto max-h-40">
                {JSON.stringify(styleDna, null, 2)}
              </pre>
            </div>
          )}

          {/* Prompt */}
          {promptBundle && (
            <div>
              <h4 className="text-xs font-medium text-blue-400 mb-2">Positive Prompt</h4>
              <p className="text-xs text-slate-400 bg-black/30 rounded-lg p-3">
                {promptBundle.positive_prompt}
              </p>
              <h4 className="text-xs font-medium text-blue-400 mb-2 mt-3">Negative Prompt</h4>
              <p className="text-xs text-slate-400 bg-black/30 rounded-lg p-3">
                {promptBundle.negative_prompt}
              </p>
            </div>
          )}

          {/* Request ID */}
          {requestId && (
            <div className="text-xs text-slate-500">
              Request ID: <code className="text-slate-400">{requestId}</code>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
