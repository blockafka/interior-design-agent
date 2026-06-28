import { useState, useRef, useEffect } from 'react'

const LAYOUTS = ['一室一厅', '两室一厅', '三室两厅', '四室两厅', '复式', '别墅']
const SPACES = ['客厅', '客餐厅', '主卧', '儿童房', '书房', '厨房', '卫生间', '全屋']
const ORIENTATIONS = ['南北通透', '东西朝向', '南向', '北向', '东向', '西向']

const GRADIENTS = [
  'from-blue-500 to-purple-500',
  'from-emerald-400 to-cyan-500',
  'from-amber-400 to-orange-500',
  'from-rose-400 to-pink-500',
  'from-violet-400 to-indigo-500',
  'from-sky-400 to-blue-500',
  'from-lime-400 to-green-500',
  'from-fuchsia-400 to-purple-500',
  'from-teal-400 to-emerald-500',
  'from-orange-400 to-red-500',
  'from-cyan-400 to-blue-500',
]

function formatCount(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

const DEFAULT_NOTES = '180㎡四室两厅，三代同堂改善住宅。客户希望有静奢老钱风的高级感，但不要酒店样板间式的冰冷；需要开放客餐厨、充足收纳、儿童活动空间，并照顾长辈日常动线。'

function AccountPicker({ accounts, selected, onSelect, onOpenChange }) {
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

  const selectedAccount = accounts.find(a => a.id === selected)
  const filtered = accounts.filter(a =>
    a.name.includes(search) || (a.sample_title || '').includes(search)
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
              {selectedAccount.name[0]}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-white">{selectedAccount.name}</div>
              <div className="text-xs text-slate-400 truncate">{formatCount(selectedAccount.total_liked)} 赞 · {formatCount(selectedAccount.total_collected)} 收藏 · {selectedAccount.post_count} 篇笔记</div>
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
                placeholder="搜索账号名称..."
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
                      onSelect(account.id)
                      toggleOpen(false)
                      setSearch('')
                    }}
                    className={`flex items-center gap-3 p-3 rounded-lg text-left transition-all ${
                      selected === account.id
                        ? 'bg-blue-500/10 border border-blue-500/30'
                        : 'hover:bg-white/5 border border-transparent'
                    }`}
                  >
                    <div className={`w-9 h-9 rounded-full bg-gradient-to-br ${account.gradient} flex items-center justify-center text-white font-bold text-sm shrink-0`}>
                      {account.name[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-white flex items-center gap-2">
                        {account.name}
                        <span className="text-[10px] text-slate-500">{account.post_count} 篇</span>
                      </div>
                      <div className="text-xs text-slate-400 truncate">{formatCount(account.total_liked)} 赞 · {formatCount(account.total_collected)} 收藏{account.sample_title ? ` · ${account.sample_title}` : ''}</div>
                    </div>
                    {selected === account.id && (
                      <span className="text-blue-400 shrink-0">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/></svg>
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 底部统计 */}
          <div className="px-3 py-2 border-t border-white/5 text-[10px] text-slate-500 flex justify-between">
            <span>已收录 {accounts.length} 个对标账号</span>
            <span>数据来自本地采集</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default function InputView({ onGenerate }) {
  const [accounts, setAccounts] = useState([])
  const [accountsLoading, setAccountsLoading] = useState(true)
  const [form, setForm] = useState({
    target_account_id: '',
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

  useEffect(() => {
    fetch('/api/accounts')
      .then(r => r.json())
      .then(data => {
        const enriched = data.map((a, i) => ({
          ...a,
          gradient: GRADIENTS[i % GRADIENTS.length],
        }))
        setAccounts(enriched)
        if (enriched.length > 0 && !form.target_account_id) {
          setForm(prev => ({ ...prev, target_account_id: enriched[0].id }))
        }
        setAccountsLoading(false)
      })
      .catch(() => setAccountsLoading(false))
  }, [])

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
          {accountsLoading ? (
            <div className="flex items-center gap-2 p-3 text-sm text-slate-400">
              <span className="w-4 h-4 border-2 border-slate-500 border-t-blue-400 rounded-full animate-spin" />
              加载账号数据...
            </div>
          ) : (
            <AccountPicker
              accounts={accounts}
              selected={form.target_account_id}
              onSelect={(id) => update('target_account_id', id)}
              onOpenChange={setPickerOpen}
            />
          )}
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
