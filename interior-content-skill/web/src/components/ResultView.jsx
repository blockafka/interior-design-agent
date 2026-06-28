import ImageGallery from './ImageGallery'
import XhsPostCard from './XhsPostCard'
import TechDetails from './TechDetails'

export default function ResultView({ result, elapsed, onReset }) {
  if (!result) return null

  const images = result.images?.image_urls || []
  const copy = result.copy_content || {}
  const styleDna = result.style_dna || {}

  return (
    <div className="animate-fade-in-up">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
            <span className="animate-bounce-once inline-block">✅</span> 生成完成
          </h2>
          <p className="text-sm text-slate-400 mt-1">用时 {elapsed} 秒 · {images.length} 张效果图 + 小红书文案</p>
        </div>
        <button
          onClick={onReset}
          className="px-4 py-2 border border-white/10 rounded-lg text-sm text-slate-300 hover:bg-white/5 hover:border-white/20 transition-all hover:scale-105"
        >
          重新生成
        </button>
      </div>

      {/* 主内容区 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左：图片 */}
        <div>
          <ImageGallery images={images} />
        </div>

        {/* 右：小红书文案 */}
        <div>
          <XhsPostCard copy={copy} />
        </div>
      </div>

      {/* 技术详情 */}
      <TechDetails
        styleDna={styleDna}
        promptBundle={result.images?.prompts_used}
        requestId={result.request_id}
      />
    </div>
  )
}
