import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import PlanForm from '../components/PlanForm';
import { usePlanContext } from '../context/PlanContext';
import type { PlanRequest } from '../types/plan';

const HomePage: React.FC = () => {
  const { startPlanning, loading } = usePlanContext();
  const navigate = useNavigate();

  const handleSubmit = (request: PlanRequest) => {
    startPlanning(request);
    navigate('/planning');
  };

  return (
    <div className="max-w-lg mx-auto min-h-screen pb-10">
      <Header />

      {/* AI 对话入口 */}
      <div className="mx-4 mb-4">
        <button
          onClick={() => navigate('/chat')}
          className="w-full py-4 bg-gradient-to-r from-travel-blue to-travel-green text-white font-semibold text-base rounded-xl shadow-md hover:shadow-lg transition-all active:scale-[0.98] flex items-center justify-center gap-2"
        >
          <span className="text-xl">💬</span>
          AI 对话规划（全新）
        </button>
        <p className="text-center text-xs text-travel-muted mt-1.5">
          跟 AI 对话，边聊边规划，随时调整
        </p>
      </div>

      {/* 分割线 */}
      <div className="mx-4 mb-4 flex items-center gap-3">
        <div className="flex-1 h-px bg-gray-200" />
        <span className="text-xs text-travel-muted">或快速填表</span>
        <div className="flex-1 h-px bg-gray-200" />
      </div>

      <PlanForm onSubmit={handleSubmit} loading={loading} />
      <footer className="mt-8 text-center text-xs text-travel-muted pb-4">
        <p>数据来源: 高德地图 API | AI 生成内容仅供参考</p>
        <p className="mt-0.5">Smart Travel Planning © 2026</p>
      </footer>
    </div>
  );
};

export default HomePage;
