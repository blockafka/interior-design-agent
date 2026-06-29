import { useEffect, useRef, useState } from 'react'
import AgentNode from './AgentNode'

const STEPS = [
  { key: 'collector', label: '采集', icon: '📂', weight: 5 },
  { key: 'analyzer', label: '风格分析', icon: '📊', weight: 15 },
  { key: 'prompter', label: '提示词', icon: '🎨', weight: 10 },
  { key: 'generator', label: '生图', icon: '🖼️', weight: 55 },
  { key: 'copywriter', label: '文案', icon: '✍️', weight: 15 },
]

const GENERATOR_TIPS = [
  '正在渲染空间光影效果...',
  '调整材质质感与纹理细节...',
  '优化色彩搭配与氛围感...',
  '处理软装陈设与空间比例...',
  '精修自然光照与阴影层次...',
  '生成高分辨率效果图中...',
]

export default function GeneratingView({ formData, steps, setSteps, onComplete }) {
  const [currentMessage, setCurrentMessage] = useState('正在初始化...')
  const [intermediateResults, setIntermediateResults] = useState({})
  const [elapsed, setElapsed] = useState(0)
  const [tipIndex, setTipIndex] = useState(0)
  const startTimeRef = useRef(Date.now())
  const timerRef = useRef(null)
  const tipTimerRef = useRef(null)

  useEffect(() => {
    startTimeRef.current = Date.now()
    timerRef.current = setInterval(() => {
      setElapsed(Math.round((Date.now() - startTimeRef.current) / 1000))
    }, 1000)
    return () => clearInterval(timerRef.current)
  }, [])

  useEffect(() => {
    const isGenerating = steps.some(s => s.key === 'generator' && s.status === 'running')
    if (isGenerating) {
      tipTimerRef.current = setInterval(() => {
        setTipIndex(prev => (prev + 1) % GENERATOR_TIPS.length)
      }, 4000)
    } else {
      clearInterval(tipTimerRef.current)
    }
    return () => clearInterval(tipTimerRef.current)
  }, [steps])

  useEffect(() => {
    const abortController = new AbortController()
    const body = JSON.stringify(formData)

    fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      signal: abortController.signal,
    }).then(async (response) => {
      if (!response.ok) {
        setCurrentMessage(`服务端错误: ${response.status}`)
        return
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let eventType = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          const lines = part.split('\n')
          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7).trim()
            } else if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                handleEvent(eventType, data)
              } catch (e) {
                console.warn('SSE parse error:', e)
              }
            }
          }
        }
      }
    }).catch((err) => {
      if (err.name !== 'AbortError') {
        setCurrentMessage(`连接失败: ${err.message}`)
      }
    })

    return () => {
      abortController.abort()
    }
  }, [])

  const handleEvent = (event, data) => {
    if (event === 'step_start') {
      setSteps(prev => [...prev, { key: data.step, status: 'running' }])
      setCurrentMessage(data.message)
    } else if (event === 'step_done') {
      setSteps(prev =>
        prev.map(s => s.key === data.step ? { ...s, status: 'done' } : s)
      )
      if (data.result) {
        setIntermediateResults(prev => ({ ...prev, [data.step]: data.result }))
      }
      if (data.message) {
        setCurrentMessage(data.message)
      }
    } else if (event === 'complete') {
      clearInterval(timerRef.current)
      const totalElapsed = Math.round((Date.now() - startTimeRef.current) / 1000)
      onComplete(data, totalElapsed)
    } else if (event === 'error') {
      setCurrentMessage(`❌ 错误: ${data.message}`)
    }
  }

  const getStepStatus = (stepKey) => {
    const step = steps.find(s => s.key === stepKey)
    return step ? step.status : 'idle'
  }

  const isGeneratorRunning = steps.some(s => s.key === 'generator' && s.status === 'running')
  const displayMessage = isGeneratorRunning ? GENERATOR_TIPS[tipIndex] : currentMessage

  const progress = (() => {
    let total = 0
    for (const step of STEPS) {
      const s = steps.find(st => st.key === step.key)
      if (s?.status === 'done') total += step.weight
      else if (s?.status === 'running') total += step.weight * 0.3
    }
    return Math.min(Math.round(total), 99)
  })()

  return (
    <div className="animate-fade-in-up max-w-2xl mx-auto">
      <div className="text-center mb-10">
        <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">🧠 AI Agent 正在为你创作</h2>
        <p className="text-slate-300 text-sm md:text-base">多个 Agent 协同工作中，请稍候...</p>
        <p className="text-slate-400 text-xs mt-2 tabular-nums">已用时 {elapsed}s</p>
      </div>

      {/* Pipeline 可视化 */}
      <div className="glass-card rounded-xl p-5 mb-6">
        <div className="flex items-center justify-center gap-1 sm:gap-2">
          {STEPS.map((step, i) => (
            <div key={step.key} className="flex items-center gap-1 sm:gap-2">
              <AgentNode
                icon={step.icon}
                label={step.label}
                status={getStepStatus(step.key)}
              />
              {i < STEPS.length - 1 && (
                <div className="text-slate-500 text-sm sm:text-lg">→</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 进度条 */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-slate-200 transition-all duration-500">{displayMessage}</span>
          <span className="text-white font-medium tabular-nums">{progress}%</span>
        </div>
        <div className="h-2.5 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full progress-bar-striped transition-all duration-1000 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* 中间结果摘要 */}
      {intermediateResults.analyzer && (
        <div className="bg-[#1e1e2e] rounded-xl p-5 border border-white/5 animate-fade-in-up">
          <h3 className="text-sm font-medium text-blue-400 mb-3">💡 已提取：风格 DNA</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-slate-500">主色调：</span>
              <span className="text-white">
                {intermediateResults.analyzer.visual?.color_palette?.join('、') || '—'}
              </span>
            </div>
            <div>
              <span className="text-slate-500">材质：</span>
              <span className="text-white">
                {intermediateResults.analyzer.visual?.material?.join('、') || '—'}
              </span>
            </div>
            <div>
              <span className="text-slate-500">光线：</span>
              <span className="text-white">
                {intermediateResults.analyzer.visual?.lighting || '—'}
              </span>
            </div>
            <div>
              <span className="text-slate-500">语气：</span>
              <span className="text-white">
                {intermediateResults.analyzer.copy_dna?.voice || '—'}
              </span>
            </div>
          </div>
        </div>
      )}

      {intermediateResults.prompter && (
        <div className="bg-[#1e1e2e] rounded-xl p-5 border border-white/5 mt-4 animate-fade-in-up">
          <h3 className="text-sm font-medium text-blue-400 mb-2">🎨 已生成：图片提示词</h3>
          <p className="text-xs text-slate-400 line-clamp-3">
            {intermediateResults.prompter.positive_prompt?.slice(0, 200)}...
          </p>
        </div>
      )}
    </div>
  )
}
