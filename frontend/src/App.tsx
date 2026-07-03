import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { PlanProvider } from './context/PlanContext';
import HomePage from './pages/HomePage';
import PlanningPage from './pages/PlanningPage';
import ChatPage from './pages/ChatPage';

const App: React.FC = () => {
  return (
    <PlanProvider>
      <BrowserRouter basename="/travel">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/planning" element={<PlanningPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/chat/:threadId" element={<ChatPage />} />
          <Route path="/chat/new" element={<ChatPage />} />
        </Routes>
      </BrowserRouter>
    </PlanProvider>
  );
};

export default App;
