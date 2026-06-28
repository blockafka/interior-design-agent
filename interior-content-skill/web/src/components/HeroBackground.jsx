import { useState, useEffect } from 'react'

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

export default function HeroBackground() {
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex(prev => (prev + 1) % IMAGES.length)
    }, 6000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="fixed inset-0 z-0 overflow-hidden">
      {/* 图片层：淡入淡出轮播 */}
      {IMAGES.map((url, i) => (
        <div
          key={i}
          className="absolute inset-0 bg-cover bg-center transition-opacity duration-[3000ms] ease-in-out"
          style={{
            backgroundImage: `url(${url})`,
            opacity: i === currentIndex ? 0.25 : 0,
            filter: 'blur(4px)',
            transform: 'scale(1.05)',
          }}
        />
      ))}

      {/* 暗色遮罩 */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/65 to-black/80" />

      {/* 中央径向暗色遮罩：保证表单区域更暗 */}
      <div
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse at center 40%, rgba(0,0,0,0.6) 0%, transparent 70%)',
        }}
      />

      {/* 微弱网格纹理（保留科技感） */}
      <div
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage:
            'linear-gradient(rgba(59, 130, 246, 0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(59, 130, 246, 0.04) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
        }}
      />
    </div>
  )
}
