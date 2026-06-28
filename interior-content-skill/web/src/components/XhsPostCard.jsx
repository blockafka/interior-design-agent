import { useState } from 'react'

export default function XhsPostCard({ copy }) {
  const [copied, setCopied] = useState(false)

  const fullText = `${copy.title || ''}\n\n${copy.body || ''}\n\n${(copy.hashtags || []).join(' ')}`

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(fullText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      const ta = document.createElement('textarea')
      ta.value = fullText
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="bg-[#1e1e2e] rounded-xl border border-white/5 p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-slate-400 flex items-center gap-2">
          <span className="text-red-400">📱</span> 小红书成稿预览
        </h3>
        <button
          onClick={handleCopy}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            copied
              ? 'bg-green-500/20 text-green-400'
              : 'bg-blue-500/20 text-blue-300 hover:bg-blue-500/30'
          }`}
        >
          {copied ? '✓ 已复制' : '复制文案'}
        </button>
      </div>

      {/* 模拟小红书卡片 */}
      <div className="flex-1 bg-white rounded-lg p-5 text-gray-900 overflow-y-auto max-h-[500px]">
        {/* 标题 */}
        <h2 className="text-lg font-bold mb-3 leading-snug">
          {copy.title || '标题生成中...'}
        </h2>

        {/* 正文 */}
        <div className="text-sm leading-relaxed whitespace-pre-line text-gray-700 mb-4">
          {copy.body || '正文生成中...'}
        </div>

        {/* Hashtags */}
        <div className="flex flex-wrap gap-1.5">
          {(copy.hashtags || []).map((tag, i) => (
            <span
              key={i}
              className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
