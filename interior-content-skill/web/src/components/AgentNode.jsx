import { useEffect, useState } from 'react'

export default function AgentNode({ icon, label, status }) {
  const [justDone, setJustDone] = useState(false)

  useEffect(() => {
    if (status === 'done') {
      setJustDone(true)
      const t = setTimeout(() => setJustDone(false), 600)
      return () => clearTimeout(t)
    }
  }, [status])

  const base = 'flex flex-col items-center gap-1 p-2 sm:p-3 rounded-lg border transition-all duration-500 min-w-[56px] sm:min-w-[70px]'

  let style = ''
  if (status === 'done') {
    style = 'border-green-500/50 bg-green-500/10'
  } else if (status === 'running') {
    style = 'border-blue-500/50 bg-blue-500/10 animate-pulse-blue'
  } else {
    style = 'border-white/10 bg-white/5'
  }

  return (
    <div className={`${base} ${style} ${justDone ? 'animate-bounce-once' : ''}`}>
      <span className="text-xl sm:text-2xl">{icon}</span>
      <span className="text-[10px] sm:text-xs text-slate-300">{label}</span>
      {status === 'done' && <span className="text-green-400 text-xs">✓</span>}
      {status === 'running' && <span className="text-blue-400 text-xs animate-pulse">●</span>}
    </div>
  )
}
