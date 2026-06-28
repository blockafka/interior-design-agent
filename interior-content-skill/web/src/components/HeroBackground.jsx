import { useState, useEffect } from 'react'

const DEBUG_VISIBLE = true

const IMAGES = [
  'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=1200&q=60',
  'https://images.unsplash.com/photo-1616486338812-3dadae5b4458?w=1200&q=60',
  'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200&q=60',
  'https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=1200&q=60',
  'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=1200&q=60',
  'https://images.unsplash.com/photo-1616137466211-f736a1f38b54?w=1200&q=60',
  'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200&q=60',
  'https://images.unsplash.com/photo-1602872030219-ad2b9a54315c?w=1200&q=60',
]

const PARAMS = DEBUG_VISIBLE
  ? {
      imageOpacity: 0.8,
      imageFilter: 'blur(0px) saturate(1.08) contrast(1.08)',
      gridOpacity: 0.12,
    }
  : {
      imageOpacity: 0.55,
      imageFilter: 'blur(2px) saturate(1.05) contrast(1.05)',
      gridOpacity: 0.15,
    }

export default function HeroBackground({ static: isStatic = false }) {
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    if (isStatic) return
    const timeout = setTimeout(() => {
      setCurrentIndex(prev => (prev + 1) % IMAGES.length)
    }, 1500)
    const interval = setInterval(() => {
      setCurrentIndex(prev => (prev + 1) % IMAGES.length)
    }, 4000)
    return () => { clearTimeout(timeout); clearInterval(interval) }
  }, [isStatic])

  return (
    <div className="fixed inset-0 z-0 overflow-hidden">
      {/* 图片层 */}
      {IMAGES.map((url, i) => (
        <div
          key={i}
          className="absolute inset-0 bg-cover bg-center transition-opacity duration-[1000ms] ease-in-out"
          style={{
            backgroundImage: `url(${url})`,
            opacity: i === currentIndex ? PARAMS.imageOpacity : 0,
            filter: PARAMS.imageFilter,
            transform: 'scale(1.05)',
          }}
        />
      ))}

      {/* 中间暗、四周可见的径向遮罩 */}
      <div
        className="absolute inset-0"
        style={{
          background: DEBUG_VISIBLE
            ? 'radial-gradient(ellipse at center 42%, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.3) 36%, rgba(0,0,0,0.1) 70%, transparent 100%)'
            : 'radial-gradient(ellipse at center 42%, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.55) 36%, rgba(0,0,0,0.28) 70%, transparent 100%)',
        }}
      />

      {/* 顶部和底部微渐变 */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-transparent to-black/60" />

      {/* 蓝色光晕：标题区域 */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center 20%, rgba(59,130,246,0.06) 0%, transparent 50%)',
        }}
      />

      {/* 蓝紫光晕：表单区域 */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center 55%, rgba(99,102,241,0.04) 0%, transparent 45%)',
        }}
      />

      {/* 微弱网格纹理 */}
      <div
        className="absolute inset-0"
        style={{
          opacity: PARAMS.gridOpacity,
          backgroundImage:
            'linear-gradient(rgba(59, 130, 246, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(59, 130, 246, 0.05) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
        }}
      />
    </div>
  )
}
