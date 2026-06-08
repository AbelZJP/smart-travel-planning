import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { PlanProvider } from './context/PlanContext';
import HomePage from './pages/HomePage';
import PlanningPage from './pages/PlanningPage';

const App: React.FC = () => {
  return (
    <PlanProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/planning" element={<PlanningPage />} />
        </Routes>
      </BrowserRouter>
    </PlanProvider>
  );
};

export default App;
