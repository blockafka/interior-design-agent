import { useState, useRef, useEffect } from 'react'

const LAYOUTS = ['一室一厅', '两室一厅', '三室两厅', '四室两厅', '复式', '别墅']
const SPACES = ['客厅', '客餐厅', '主卧', '儿童房', '书房', '厨房', '卫生间', '全屋']
const ORIENTATIONS = ['南北通透', '东西朝向', '南向', '北向', '东向', '西向']

const ACCOUNTS = [
  { id: '厚来设计', name: '厚来设计', initial: '厚', gradient: 'from-blue-500 to-purple-500', stats: '1284 赞 · 1210 收藏', tags: '静奢老钱风', city: '北京', category: '高端私宅', available: true },
  { id: '纯白空间', name: '纯白空间', initial: '纯', gradient: 'from-emerald-400 to-cyan-500', stats: '3.2w 粉丝', tags: '极简侘寂风', city: '上海', category: '精装改造', available: false },
  { id: '木子设计', name: '木子设计', initial: '木', gradient: 'from-amber-400 to-orange-500', stats: '8600 粉丝', tags: '日式原木风', city: '杭州', category: '小户型收纳', available: false },
  { id: '宅匠空间', name: '宅匠空间', initial: '宅', gradient: 'from-rose-400 to-pink-500', stats: '1.5w 粉丝', tags: '现代轻奢风', city: '深圳', category: '大平层', available: false },
  { id: '归心设计', name: '归心设计', initial: '归', gradient: 'from-violet-400 to-indigo-500', stats: '6200 粉丝', tags: '新中式国风', city: '成都', category: '别墅庭院', available: false },
]

const DEFAULT_NOTES = '180㎡四室两厅，三代同堂改善住宅。客户希望有静奢老钱风的高级感，但不要酒店样板间式的冰冷；需要开放客餐厨、充足收纳、儿童活动空间，并照顾长辈日常动线。'

function AccountPicker({ selected, onSelect, onOpenChange }) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const panelRef = useRef(null)

  const toggleOpen = (val) => {
    setOpen(val)
    onOpenChange?.(val)
  }

  useEffect(() => {
    const handleClick = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        toggleOpen(false)
      }
    }
    if (open) document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  const selectedAccount = ACCOUNTS.find(a => a.id === selected)
  const filtered = ACCOUNTS.filter(a =>
    a.name.includes(search) || a.tags.includes(search) || a.city.includes(search) || a.category.includes(search)
  )

  return (
    <div className="relative" ref={panelRef}>
      {/* 已选卡片（触发器） */}
      <button
        type="button"
        onClick={() => toggleOpen(!open)}
        className="w-full flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/10 hover:border-blue-500/40 transition-all text-left group"
      >
        {selectedAccount && (
          <>
            <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${selectedAccount.gradient} flex items-center justify-center text-white font-bold shrink-0`}>
              {selectedAccount.initial}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-white">{selectedAccount.name}</div>
              <div className="text-xs text-slate-400 truncate">{selectedAccount.tags} · {selectedAccount.city}{selectedAccount.category}</div>
            </div>
          </>
        )}
        <div className="text-slate-400 group-hover:text-blue-400 transition-colors shrink-0">
          <svg className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* 浮层 */}
      {open && (
        <div className="absolute z-50 top-full left-0 right-0 mt-2 bg-[#1a1a2e] border border-white/10 rounded-xl shadow-2xl shadow-black/50 overflow-hidden animate-fade-in-up">
          {/* 搜索框 */}
          <div className="p-3 border-b border-white/5">
            <div className="relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="搜索账号、风格、城市..."
                className="w-full bg-white/5 border border-white/10 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                autoFocus
              />
            </div>
          </div>

          {/* 账号列表 */}
          <div className="max-h-[280px] overflow-y-auto p-2">
            {filtered.length === 0 ? (
              <div className="text-center text-slate-500 text-sm py-6">未找到匹配账号</div>
            ) : (
              <div className="grid gap-1">
                {filtered.map(account => (
                  <button
                    key={account.id}
                    type="button"
                    onClick={() => {
                      if (account.available) {
                        onSelect(account.id)
                        toggleOpen(false)
                        setSearch('')
                      }
                    }}
                    className={`flex items-center gap-3 p-3 rounded-lg text-left transition-all ${
                      selected === account.id
                        ? 'bg-blue-500/10 border border-blue-500/30'
                        : account.available
                          ? 'hover:bg-white/5 border border-transparent'
                          : 'opacity-40 cursor-not-allowed border border-transparent'
                    }`}
                  >
                    <div className={`w-9 h-9 rounded-full bg-gradient-to-br ${account.gradient} flex items-center justify-center text-white font-bold text-sm shrink-0`}>
                      {account.initial}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-white flex items-center gap-2">
                        {account.name}
                        <span className="text-[10px] text-slate-500">{account.city}</span>
                      </div>
                      <div className="text-xs text-slate-400 truncate">{account.stats} · {account.tags} · {account.category}</div>
                    </div>
                    {selected === account.id ? (
                      <span className="text-blue-400 shrink-0">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/></svg>
                      </span>
                    ) : !account.available ? (
                      <span className="text-[10px] text-slate-500 bg-white/5 px-1.5 py-0.5 rounded shrink-0">即将上线</span>
                    ) : null}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 底部统计 */}
          <div className="px-3 py-2 border-t border-white/5 text-[10px] text-slate-500 flex justify-between">
            <span>已收录 {ACCOUNTS.length} 个对标账号</span>
            <span>{ACCOUNTS.filter(a => a.available).length} 个可用</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default function InputView({ onGenerate }) {
  const [form, setForm] = useState({
    target_account_id: '厚来设计',
    area_sqm: 180,
    layout: '四室两厅',
    space_type: '客餐厅',
    orientation: '南北通透',
    target_customer: '三代同堂改善型家庭',
    pain_points: '高级感不能冰冷，要兼顾长辈孩子和年轻夫妻互动',
    notes: DEFAULT_NOTES,
  })
  const [loading, setLoading] = useState(false)
  const [pickerOpen, setPickerOpen] = useState(false)

  const update = (key, value) => setForm(prev => ({ ...prev, [key]: value }))

  const handleSubmit = (e) => {
    e.preventDefault()
    setLoading(true)
    onGenerate(form)
  }

  return (
    <div className="animate-fade-in-up">
      {/* Hero */}
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold text-white mb-3">
          输入户型，<span className="text-blue-400">AI 生成获客内容</span>
        </h1>
        <p className="text-slate-400 text-lg">
          对标爆款账号风格 · 定制设计效果图 · 小红书营销文案
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5 max-w-2xl mx-auto">
        {/* Step 1 */}
        <div className={`glass-card rounded-xl p-6 relative ${pickerOpen ? 'z-20' : 'z-10'}`}>
          <h2 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs flex items-center justify-center font-bold">1</span>
            对标账号
          </h2>
          <AccountPicker
            selected={form.target_account_id}
            onSelect={(id) => update('target_account_id', id)}
            onOpenChange={setPickerOpen}
          />
        </div>

        {/* Step 2 */}
        <div className="glass-card rounded-xl p-6 relative z-0">
          <h2 className="text-sm font-medium text-slate-400 mb-4 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs flex items-center justify-center font-bold">2</span>
            客户户型需求
          </h2>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-xs text-slate-500 mb-1">面积（㎡）</label>
              <input
                type="number"
                value={form.area_sqm}
                onChange={(e) => update('area_sqm', Number(e.target.value))}
                className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">户型</label>
              <select
                value={form.layout}
                onChange={(e) => update('layout', e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none appearance-none"
              >
                {LAYOUTS.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">空间类型</label>
              <select
                value={form.space_type}
                onChange={(e) => update('space_type', e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none appearance-none"
              >
                {SPACES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">朝向</label>
              <select
                value={form.orientation}
                onChange={(e) => update('orientation', e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none appearance-none"
              >
                {ORIENTATIONS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">目标客户</label>
              <input
                type="text"
                value={form.target_customer}
                onChange={(e) => update('target_customer', e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">核心诉求</label>
              <input
                type="text"
                value={form.pain_points}
                onChange={(e) => update('pain_points', e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">详细备注</label>
              <textarea
                value={form.notes}
                onChange={(e) => update('notes', e.target.value)}
                rows={3}
                className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none transition-colors resize-none"
              />
            </div>
          </div>
        </div>

        {/* Hint */}
        <p className="text-center text-xs text-slate-500">
          AI 将自动生成：StyleDNA · Prompt · 3 张效果图 · 小红书文案
        </p>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className={`w-full py-4 font-semibold rounded-lg text-lg transition-all ${
            loading
              ? 'bg-blue-500/50 text-white/70 cursor-wait'
              : 'bg-blue-500 hover:bg-blue-600 text-white hover:scale-[1.02] hover:shadow-lg hover:shadow-blue-500/25 active:scale-[0.98]'
          }`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              正在启动 Agent...
            </span>
          ) : (
            '✨ 开始生成'
          )}
        </button>
      </form>
    </div>
  )
}
