import React, { useState } from 'react';
import type { TierKey } from '../../types/chat';

const TIERS: TierKey[] = ['economy', 'comfort', 'luxury'];
const TIER_LABELS: Record<TierKey, string> = { economy: '经济', comfort: '舒适', luxury: '豪华' };
const TIER_ICONS: Record<TierKey, string> = { economy: '💰', comfort: '👍', luxury: '👑' };

const TIER_COLORS: Record<TierKey, { bg: string; text: string; border: string; tabBg: string; accent: string; ring: string }> = {
  economy: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200', tabBg: 'bg-green-100', accent: 'bg-green-500', ring: 'ring-green-300' },
  comfort: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', tabBg: 'bg-blue-100', accent: 'bg-blue-500', ring: 'ring-blue-300' },
  luxury: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', tabBg: 'bg-purple-100', accent: 'bg-purple-500', ring: 'ring-purple-300' },
};

interface TierOverview {
  label?: string;
  est_cost?: number;
  budget_usage?: number;
  hotel_level?: string;
  transit_mode?: string;
  highlight?: string;
  has_detail?: boolean;
}
interface TierDetail {
  daily_plans?: Array<Record<string, unknown>>;
  total_cost?: number;
  budget_usage?: number;
}

interface PlanCardProps {
  planData: Record<string, unknown>;
  activeTier: TierKey;
  onSelectTier: (tier: TierKey) => void;
  generatingTier?: TierKey | null;
}

const PlanCard: React.FC<PlanCardProps> = ({ planData, activeTier, onSelectTier, generatingTier = null }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [expandedDays, setExpandedDays] = useState<Record<number, boolean>>({});

  const tiers = (planData.tiers as Record<TierKey, TierOverview>) || {};
  const details = (planData.details as Record<TierKey, TierDetail>) || {};
  const budget = (planData.budget as number) || 0;

  const currentDetail = details[activeTier] || {};
  const currentOverview = tiers[activeTier] || {};
  const dailyPlans = currentDetail.daily_plans || [];
  const hasDetail = dailyPlans.length > 0;
  const totalCost = hasDetail ? (currentDetail.total_cost || 0) : (currentOverview.est_cost || 0);
  const budgetUsage = budget > 0 ? Math.min((totalCost / budget) * 100, 100) : 0;

  const toggleDay = (day: number) => setExpandedDays((p) => ({ ...p, [day]: !p[day] }));

  if (!planData.tiers) return null;

  const tierHasDetail = (t: TierKey) => !!(tiers[t]?.has_detail) || !!(details[t]?.daily_plans?.length);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* 顶部标题 + 收起按钮 */}
      <div className="px-4 pt-3 pb-2 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-base">🏆</span>
            <span className="font-bold text-sm text-gray-800">
              {hasDetail ? `${TIER_LABELS[activeTier]}档详细行程` : '三档方案速览'}
            </span>
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="text-xs text-gray-400 hover:text-gray-600 transition px-2 py-0.5 rounded hover:bg-gray-100"
          >
            {collapsed ? '▲ 展开' : '▼ 收起'}
          </button>
        </div>
      </div>

      {collapsed ? (
        <button onClick={() => setCollapsed(false)} className="w-full px-4 py-2.5 text-left text-xs text-gray-500 hover:bg-gray-50 transition">
          {TIER_LABELS[activeTier]}档 · {hasDetail ? '总价' : '预估'} ¥{totalCost.toLocaleString()} · 点击展开查看
        </button>
      ) : (
        <>
          {/* 三档概览卡片（始终显示，作为切换/生成入口） */}
          <div className="px-4 pt-2 pb-2">
            <div className="grid grid-cols-3 gap-2">
              {TIERS.map((tier) => {
                const ov = tiers[tier] || {};
                const cost = ov.est_cost || 0;
                const usage = budget > 0 ? (cost / budget) * 100 : 0;
                const color = TIER_COLORS[tier];
                const isActive = activeTier === tier;
                const isGenerating = generatingTier === tier;
                const hasD = tierHasDetail(tier);
                return (
                  <button
                    key={tier}
                    onClick={() => onSelectTier(tier)}
                    disabled={isGenerating}
                    className={`rounded-lg border p-2.5 text-center transition-all ${color.border} ${
                      isActive ? `${color.bg} ring-2 ring-offset-1 ${color.ring}` : 'bg-white hover:bg-gray-50'
                    } ${isGenerating ? 'opacity-60 cursor-wait' : 'cursor-pointer'}`}
                  >
                    <div className="text-lg mb-0.5">{TIER_ICONS[tier]}</div>
                    <div className={`text-xs font-bold ${color.text}`}>{TIER_LABELS[tier]}</div>
                    <div className="text-sm font-bold text-gray-800 mt-0.5">¥{cost.toLocaleString()}</div>
                    <div className="flex items-center gap-1 justify-center mt-1">
                      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden max-w-[60px]">
                        <div className={`h-full rounded-full ${color.accent}`} style={{ width: `${Math.min(usage, 100)}%` }} />
                      </div>
                    </div>
                    <div className="text-[10px] text-gray-400 mt-1 h-3.5">
                      {isGenerating ? '生成中…' : hasD ? '✓ 已生成' : '点击生成'}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 概要态：当前档亮点 */}
          {!hasDetail && currentOverview.highlight && (
            <div className="px-4 pb-2">
              <div className={`rounded-lg px-3 py-2 text-xs ${TIER_COLORS[activeTier].bg} ${TIER_COLORS[activeTier].text}`}>
                ✨ {currentOverview.highlight} · {currentOverview.hotel_level} · {currentOverview.transit_mode}
              </div>
              <p className="text-[10px] text-gray-400 mt-1.5 text-center">💡 点击上方任一档位卡片，生成该档详细行程</p>
            </div>
          )}

          {/* 详情态：每日行程 */}
          {hasDetail && (
            <>
              <div className="flex items-center justify-between px-4 py-2 bg-gray-50/70 border-t border-gray-100">
                <div className="flex gap-1">
                  {TIERS.map((tier) => {
                    const isActive = activeTier === tier;
                    const color = TIER_COLORS[tier];
                    return (
                      <button
                        key={tier}
                        onClick={() => onSelectTier(tier)}
                        className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                          isActive ? `${color.tabBg} ${color.text}` : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        {TIER_ICONS[tier]} {TIER_LABELS[tier]}
                      </button>
                    );
                  })}
                </div>
                <div className="text-xs text-gray-500">
                  总价 <span className="font-bold text-gray-800">¥{totalCost.toLocaleString()}</span>
                </div>
              </div>

              <div className="px-4 py-2 space-y-1.5 max-h-[340px] overflow-y-auto">
                {dailyPlans.map((day, idx) => {
                  const dayNum = (day.day as number) || idx + 1;
                  const date = day.date as string;
                  const dayCost = (day.daily_cost as number) || 0;
                  const attractions: Array<Record<string, unknown>> = (day.attractions as Array<Record<string, unknown>>) || [];
                  const isExp = expandedDays[dayNum];

                  return (
                    <div key={dayNum} className="border border-gray-100 rounded-lg overflow-hidden">
                      <button
                        onClick={() => toggleDay(dayNum)}
                        className="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-gray-50 transition"
                      >
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-gray-100 text-gray-600 flex items-center justify-center text-xs font-bold">
                            {dayNum}
                          </span>
                          <div>
                            <span className="text-sm font-semibold text-gray-800">Day {dayNum}</span>
                            {date && <span className="text-xs text-gray-400 ml-1.5">{String(date).slice(5)}</span>}
                          </div>
                          {attractions.length > 0 && (
                            <span className="text-[11px] text-gray-400">· {attractions.length} 站</span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-gray-600">¥{dayCost.toLocaleString()}</span>
                          <span className={`text-gray-400 text-xs transition-transform duration-200 ${isExp ? 'rotate-180' : ''}`}>▼</span>
                        </div>
                      </button>

                      {isExp && (
                        <div className="px-3 pb-3 space-y-1.5 text-xs border-t border-gray-50 pt-2">
                          {(day.transport as Array<Record<string, unknown>> || []).map((t, i) => (
                            <div key={`t-${i}`} className="flex items-center gap-2 text-gray-500">
                              <span>🚄</span>
                              <span>{String(t.from || '')} → {String(t.to || '')}</span>
                              <span className="ml-auto">{(t.cost as number || 0) > 0 ? `¥${t.cost}` : ''}</span>
                            </div>
                          ))}

                          {attractions.map((a, i) => (
                            <div key={`a-${i}`} className="flex items-center gap-2">
                              <span className="w-5 h-5 rounded-full bg-travel-blue text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                                {Number(a.order) || i + 1}
                              </span>
                              <span className="text-gray-700 font-medium">{String(a.name || '')}</span>
                              <span className="ml-auto text-gray-400 shrink-0">
                                {String(a.time_slot || '')}
                                {(a.ticket as number || 0) > 0 ? ` ¥${a.ticket}` : ' 免费'}
                              </span>
                            </div>
                          ))}

                          {(day.meals as Array<Record<string, unknown>> || []).map((m, i) => (
                            <div key={`m-${i}`} className="flex items-center gap-2 text-gray-500">
                              <span>🍽</span>
                              <span>{String(m.suggestion || '')}</span>
                              <span className="ml-auto">~¥{(m.estimated_cost as number || 0)}</span>
                            </div>
                          ))}

                          {Boolean(day.hotel) && (
                            <div className="flex items-center gap-2 text-gray-600 pt-1.5 mt-1 border-t border-gray-50">
                              <span>🏨</span>
                              <span className="font-medium text-gray-700">{String((day.hotel as Record<string, unknown>).name || '')}</span>
                              <span className="ml-auto text-gray-400">¥{(day.hotel as Record<string, unknown>).price as number || 0}/晚</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}

          {/* 底部预算条 */}
          {budget > 0 && (
            <div className="px-4 py-2.5 bg-gray-50 border-t border-gray-100">
              <div className="flex items-center justify-between text-xs text-gray-500 mb-1.5">
                <span>预算 ¥{budget.toLocaleString()}</span>
                <span>已用 {budgetUsage.toFixed(0)}%</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-green-400 via-blue-400 to-purple-400 transition-all"
                  style={{ width: `${Math.min(budgetUsage, 100)}%` }}
                />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default PlanCard;
