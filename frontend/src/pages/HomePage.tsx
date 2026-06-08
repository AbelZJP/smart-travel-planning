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
      <PlanForm onSubmit={handleSubmit} loading={loading} />
      <footer className="mt-8 text-center text-xs text-travel-muted pb-4">
        <p>数据来源: 高德地图 API | AI 生成内容仅供参考</p>
        <p className="mt-0.5">Smart Travel Planning © 2026</p>
      </footer>
    </div>
  );
};

export default HomePage;
