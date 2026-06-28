import { useState } from 'react'

const LAYOUTS = ['一室一厅', '两室一厅', '三室两厅', '四室两厅', '复式', '别墅']
const SPACES = ['客厅', '客餐厅', '主卧', '儿童房', '书房', '厨房', '卫生间', '全屋']
const ORIENTATIONS = ['南北通透', '东西朝向', '南向', '北向', '东向', '西向']

const DEFAULT_NOTES = '180㎡四室两厅，三代同堂改善住宅。客户希望有静奢老钱风的高级感，但不要酒店样板间式的冰冷；需要开放客餐厨、充足收纳、儿童活动空间，并照顾长辈日常动线。'

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

  const update = (key, value) => setForm(prev => ({ ...prev, [key]: value }))

  const handleSubmit = (e) => {
    e.preventDefault()
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

      <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl mx-auto">
        {/* Step 1 */}
        <div className="bg-[#1e1e2e] rounded-xl p-6 border border-white/5">
          <h2 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs flex items-center justify-center font-bold">1</span>
            对标账号
          </h2>
          <div className="flex items-center gap-4 p-4 rounded-lg bg-white/5 border border-blue-500/30">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-lg">
              厚
            </div>
            <div className="flex-1">
              <div className="font-medium text-white">厚来设计</div>
              <div className="text-xs text-slate-400 mt-1">
                1284 赞 · 1210 收藏 · 静奢老钱风 · 北京高端私宅
              </div>
            </div>
            <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full">已选</span>
          </div>
        </div>

        {/* Step 2 */}
        <div className="bg-[#1e1e2e] rounded-xl p-6 border border-white/5">
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

        {/* Submit */}
        <button
          type="submit"
          className="w-full py-4 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-lg text-lg transition-all hover:scale-[1.02] hover:shadow-lg hover:shadow-blue-500/25 active:scale-[0.98]"
        >
          ✨ 开始生成
        </button>
      </form>
    </div>
  )
}
