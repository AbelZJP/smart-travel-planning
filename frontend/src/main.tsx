import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// 动态加载高德地图 JS API
const amapKey = import.meta.env.VITE_AMAP_KEY;
if (amapKey) {
  const script = document.createElement('script');
  script.src = `https://webapi.amap.com/maps?v=2.0&key=${amapKey}`;
  script.async = true;
  document.head.appendChild(script);
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
