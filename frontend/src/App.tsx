import React from 'react';
import Header from './components/Header';
import PlanForm from './components/PlanForm';
import ProgressPanel from './components/ProgressPanel';
import ResultPanel from './components/ResultPanel';
import { usePlan } from './hooks/usePlan';

const AMAP_KEY = 'YOUR_AMAP_KEY';

const App: React.FC = () => {
  const {
    loading,
    result,
    activeTier,
    setActiveTier,
    error,
    agentProgress,
    progressMessages,
    startPlanning,
  } = usePlan();

  return (
    <div className="max-w-lg mx-auto min-h-screen pb-10">
      <Header />
      <PlanForm onSubmit={startPlanning} loading={loading} />

      {error && (
        <div className="mx-4 mt-4 p-4 bg-red-50 border border-red-200 rounded-card">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {loading && !result && (
        <ProgressPanel agentProgress={agentProgress} messages={progressMessages} />
      )}

      {result && (
        <ResultPanel result={result} activeTier={activeTier}
          onTierChange={setActiveTier} amapKey={AMAP_KEY} />
      )}

      <footer className="mt-8 text-center text-xs text-travel-muted pb-4">
        <p>数据来源: 高德地图 API | AI 生成内容仅供参考</p>
        <p className="mt-0.5">Smart Travel Planning © 2026</p>
      </footer>
    </div>
  );
};

export default App;
