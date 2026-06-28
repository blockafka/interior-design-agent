export default function NavBar() {
  return (
    <nav className="border-b border-white/10 bg-black/30 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-blue-400 text-xl">✦</span>
          <span className="font-semibold text-white text-lg">Interior Agent</span>
          <span className="text-xs text-slate-500 ml-2 hidden sm:inline">AI 家装内容生成引擎</span>
        </div>
        <div className="flex items-center gap-4 text-sm text-slate-400">
          <a
            href="https://github.com/blockafka/interior-design-agent"
            target="_blank"
            rel="noreferrer"
            className="hover:text-white transition-colors"
          >
            GitHub
          </a>
        </div>
      </div>
    </nav>
  )
}
