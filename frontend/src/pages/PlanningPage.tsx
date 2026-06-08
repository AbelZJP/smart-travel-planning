import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePlanContext } from '../context/PlanContext';
import LoadingAnimation from '../components/LoadingAnimation';
import ProgressPanel from '../components/ProgressPanel';
import ResultPanel from '../components/ResultPanel';

const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || '';

const PlanningPage: React.FC = () => {
  const { loading, result, error, agentProgress, progressMessages, activeTier, setActiveTier } = usePlanContext();
  const navigate = useNavigate();

  // 如果没在规划中也没结果，跳回首页
  useEffect(() => {
    if (!loading && !result && !error) {
      navigate('/', { replace: true });
    }
  }, [loading, result, error, navigate]);

  return (
    <div className="max-w-lg mx-auto min-h-screen pb-10">
      {/* 顶部导航 */}
      <div className="px-6 pt-6 pb-3 flex items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="w-9 h-9 flex items-center justify-center rounded-xl bg-white shadow-sm hover:shadow transition active:scale-95"
        >
          <span className="text-lg">←</span>
        </button>
        <h1 className="text-lg font-bold text-travel-text">智能旅行规划</h1>
      </div>

      {/* 错误 */}
      {error && (
        <div className="mx-4 mt-4 p-5 bg-red-50 border border-red-200 rounded-card">
          <p className="text-sm text-red-600 mb-3">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-red-500 text-white text-sm rounded-xl"
          >
            返回重试
          </button>
        </div>
      )}

      {/* 加载中 */}
      {loading && !result && (
        <>
          <LoadingAnimation />
          <ProgressPanel agentProgress={agentProgress} messages={progressMessages} />
        </>
      )}

      {/* 结果 */}
      {result && (
        <ResultPanel
          result={result}
          activeTier={activeTier}
          onTierChange={setActiveTier}
          amapKey={AMAP_KEY}
        />
      )}
    </div>
  );
};

export default PlanningPage;
