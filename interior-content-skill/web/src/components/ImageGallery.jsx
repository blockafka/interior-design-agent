import { useState } from 'react'

export default function ImageGallery({ images }) {
  const [selected, setSelected] = useState(0)

  if (!images.length) {
    return (
      <div className="bg-[#1e1e2e] rounded-xl p-8 border border-white/5 text-center text-slate-500">
        暂无图片
      </div>
    )
  }

  const labels = ['封面主图', '空间细节', '生活氛围']

  return (
    <div className="space-y-3">
      {/* 主图 */}
      <div className="bg-[#1e1e2e] rounded-xl border border-white/5 overflow-hidden">
        <img
          src={images[selected]}
          alt={labels[selected] || '效果图'}
          className="w-full aspect-[3/4] object-cover"
          onError={(e) => { e.target.src = 'https://placehold.co/600x800/1e1e2e/666?text=Loading...' }}
        />
      </div>

      {/* 缩略图 */}
      <div className="flex gap-2">
        {images.map((url, i) => (
          <button
            key={i}
            onClick={() => setSelected(i)}
            className={`flex-1 rounded-lg overflow-hidden border-2 transition-all ${
              i === selected ? 'border-blue-500' : 'border-transparent opacity-60 hover:opacity-100'
            }`}
          >
            <img
              src={url}
              alt={labels[i] || `图${i + 1}`}
              className="w-full aspect-square object-cover"
              onError={(e) => { e.target.src = 'https://placehold.co/200x200/1e1e2e/666?text=' + (i + 1) }}
            />
            <div className="text-xs text-center py-1 text-slate-400 bg-[#1e1e2e]">
              {labels[i] || `图${i + 1}`}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
