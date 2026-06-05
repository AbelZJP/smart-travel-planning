import React from 'react';
import type { TierPlan } from '../types/plan';

interface CostSummaryProps {
  plan: TierPlan;
  totalBudget: number;
  tierLabel: string;
}

const CostSummary: React.FC<CostSummaryProps> = ({ plan, totalBudget, tierLabel }) => {
  const transportCost = plan.daily_plans.reduce((sum, d) => sum + d.transport.reduce((s, t) => s + t.cost, 0), 0);
  const hotelCost = plan.daily_plans.reduce((sum, d) => sum + (d.hotel?.price || 0), 0);
  const ticketCost = plan.daily_plans.reduce((sum, d) => sum + d.attractions.reduce((s, a) => s + (a.ticket || 0), 0), 0);
  const mealsCost = plan.daily_plans.reduce((sum, d) => sum + d.meals.reduce((s, m) => s + (m.estimated_cost || 0), 0), 0);

  const usagePercent = Math.min((plan.total_cost / totalBudget) * 100, 100);
  const barColor = usagePercent > 90 ? 'bg-red-500' : usagePercent > 70 ? 'bg-yellow-500' : 'bg-travel-green';

  return (
    <div className="bg-white rounded-card shadow-md p-4">
      <h3 className="text-sm font-semibold text-travel-text mb-3">💰 {tierLabel}档费用总览</h3>
      <div className="grid grid-cols-2 gap-2 mb-3">
        {[
          { label: '交通', cost: transportCost, icon: '🚄' },
          { label: '住宿', cost: hotelCost, icon: '🏨' },
          { label: '门票', cost: ticketCost, icon: '🎫' },
          { label: '餐饮', cost: mealsCost, icon: '🍽' },
        ].map(({ label, cost, icon }) => (
          <div key={label} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
            <span className="text-lg">{icon}</span>
            <div>
              <p className="text-xs text-travel-muted">{label}</p>
              <p className="text-sm font-semibold text-travel-text">¥{cost.toLocaleString()}</p>
            </div>
          </div>
        ))}
      </div>
      <div>
        <div className="flex justify-between text-xs text-travel-muted mb-1">
          <span>总计: ¥{plan.total_cost.toLocaleString()} / 预算 ¥{totalBudget.toLocaleString()}</span>
          <span>{usagePercent.toFixed(0)}%</span>
        </div>
        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full ${barColor} rounded-full transition-all duration-500`} style={{ width: `${usagePercent}%` }} />
        </div>
      </div>
    </div>
  );
};

export default CostSummary;
