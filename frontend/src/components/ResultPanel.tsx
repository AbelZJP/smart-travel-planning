import React, { useRef, useState, useCallback } from 'react';
import type { PlanResult, TierKey } from '../types/plan';
import { TIER_LABELS } from '../types/plan';
import DailyCard from './DailyCard';
import CostSummary from './CostSummary';
import ExportButton from './ExportButton';

interface ResultPanelProps {
  result: PlanResult;
  activeTier: TierKey;
  onTierChange: (tier: TierKey) => void;
  amapKey: string;
}

const TIERS: TierKey[] = ['economy', 'comfort', 'luxury'];

const ResultPanel: React.FC<ResultPanelProps> = ({ result, activeTier, onTierChange, amapKey }) => {
  const resultRef = useRef<HTMLDivElement>(null);
  const [exportMode, setExportMode] = useState(false);
  const plan = result.plans[activeTier];
  const totalBudget = result.input.budget;

  const handleExportStart = useCallback(() => setExportMode(true), []);
  const handleExportEnd = useCallback(() => setExportMode(false), []);

  return (
    <div className="mx-4 mt-4 space-y-4" ref={resultRef}>
      {/* Tier Tabs */}
      <div className="flex bg-white rounded-card p-1 shadow-md">
        {TIERS.map((tier) => (
          <button key={tier} onClick={() => onTierChange(tier)}
            className={`flex-1 py-2.5 text-sm font-medium rounded-xl transition-all ${
              activeTier === tier
                ? 'bg-gradient-to-r from-travel-blue to-travel-green text-white shadow-md'
                : 'text-travel-muted hover:text-travel-text'
            }`}>
            {TIER_LABELS[tier]}
            {result.plans[tier]?.total_cost > 0 && (
              <span className="block text-xs opacity-80">¥{result.plans[tier].total_cost.toLocaleString()}</span>
            )}
          </button>
        ))}
      </div>

      {/* Daily plans */}
      <div className="space-y-3">
        {plan.daily_plans.map((dayPlan, idx) => (
          <DailyCard key={`${activeTier}-day-${idx}`} plan={dayPlan} dayIndex={idx}
            totalDays={plan.daily_plans.length} exportMode={exportMode} amapKey={amapKey} />
        ))}
      </div>

      {/* Cost summary */}
      {plan.daily_plans.length > 0 && (
        <CostSummary plan={plan} totalBudget={totalBudget} tierLabel={TIER_LABELS[activeTier]} />
      )}

      {/* Export */}
      <ExportButton
        resultRef={resultRef}
        onExportStart={handleExportStart}
        onExportEnd={handleExportEnd}
      />
    </div>
  );
};

export default ResultPanel;
