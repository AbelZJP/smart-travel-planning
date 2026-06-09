import React, { useState } from 'react';
import type {
  PlanRequest,
  TravelMode,
  CityTransit,
  Preference,
} from '../types/plan';
import {
  TRAVEL_MODE_LABELS,
  CITY_TRANSIT_LABELS,
  PREFERENCE_LABELS,
} from '../types/plan';

interface PlanFormProps {
  onSubmit: (request: PlanRequest) => void;
  loading: boolean;
}

const TRAVEL_MODES: TravelMode[] = ['high_speed_rail', 'flight', 'self_drive', 'bus', 'train'];
const CITY_TRANSITS: CityTransit[] = ['public_transit', 'taxi', 'rental_car', 'mixed'];
const PREFERENCES: Preference[] = ['nature', 'history', 'food', 'family'];

const PlanForm: React.FC<PlanFormProps> = ({ onSubmit, loading }) => {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [budget, setBudget] = useState(3000);
  const [intercityMode, setIntercityMode] = useState<TravelMode>('high_speed_rail');
  const [cityTransit, setCityTransit] = useState<CityTransit>('mixed');
  const [days, setDays] = useState(3);
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 7);
    return d.toISOString().split('T')[0];
  });
  const [preferences, setPreferences] = useState<Preference[]>(['nature', 'history']);

  const togglePreference = (p: Preference) => {
    setPreferences((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!origin.trim() || !destination.trim()) return;
    onSubmit({
      origin: origin.trim(),
      destination: destination.trim(),
      budget,
      intercity_mode: intercityMode,
      city_transit: cityTransit,
      days,
      preferences,
      start_date: startDate,
    });
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <form
      onSubmit={handleSubmit}
      className="mx-4 p-5 bg-white rounded-card shadow-md space-y-5"
    >
      {/* Origin & Destination */}
      <div className="flex items-center gap-2">
        <div className="flex-1">
          <label className="block text-xs font-medium text-travel-muted mb-1.5">📍 出发地</label>
          <input type="text" value={origin} onChange={(e) => setOrigin(e.target.value)}
            placeholder="例如：上海"
            className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-travel-blue/30 focus:border-travel-blue transition bg-white" required />
        </div>
        <div className="pt-6 text-travel-muted">→</div>
        <div className="flex-1">
          <label className="block text-xs font-medium text-travel-muted mb-1.5">🎯 目的地</label>
          <input type="text" value={destination} onChange={(e) => setDestination(e.target.value)}
            placeholder="例如：杭州"
            className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-travel-blue/30 focus:border-travel-blue transition bg-white" required />
        </div>
      </div>

      {/* Budget */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-2">💰 总预算</label>
        <div className="flex items-center gap-3 bg-gray-50 rounded-xl px-4 py-3">
          <span className="text-xs text-travel-muted">¥500</span>
          <input type="range" min={500} max={50000} step={100} value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
            className="flex-1 accent-travel-green h-2" />
          <span className="text-xs text-travel-muted">¥50,000</span>
        </div>
        <div className="text-center mt-2">
          <span className="text-lg font-bold text-travel-blue">¥{budget.toLocaleString()}</span>
        </div>
      </div>

      {/* Intercity mode */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-2">🚗 城市间交通</label>
        <div className="flex flex-wrap gap-2">
          {TRAVEL_MODES.map((mode) => (
            <button key={mode} type="button" onClick={() => setIntercityMode(mode)}
              className={`px-4 py-2.5 text-sm rounded-full border font-medium transition active:scale-95 ${
                intercityMode === mode
                  ? 'bg-travel-blue text-white border-travel-blue shadow-md'
                  : 'bg-gray-50 text-travel-text border-gray-200 active:bg-blue-50'
              }`}>
              {TRAVEL_MODE_LABELS[mode]}
            </button>
          ))}
        </div>
      </div>

      {/* City transit */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-2">🚕 市内交通</label>
        <div className="flex flex-wrap gap-2">
          {CITY_TRANSITS.map((mode) => (
            <button key={mode} type="button" onClick={() => setCityTransit(mode)}
              className={`px-4 py-2.5 text-sm rounded-full border font-medium transition active:scale-95 ${
                cityTransit === mode
                  ? 'bg-travel-green text-white border-travel-green shadow-md'
                  : 'bg-gray-50 text-travel-text border-gray-200 active:bg-green-50'
              }`}>
              {CITY_TRANSIT_LABELS[mode]}
            </button>
          ))}
        </div>
      </div>

      {/* Date */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-1">📅 出发日期</label>
        <input type="date" value={startDate} min={today}
          onChange={(e) => setStartDate(e.target.value)}
          className="w-full min-w-0 px-3 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-travel-blue/30 focus:border-travel-blue transition bg-white" />
      </div>

      {/* Days */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-2">📆 出行天数</label>
        <div className="grid grid-cols-4 gap-2">
          {[
            { value: 1, label: '1天' },
            { value: 2, label: '2天' },
            { value: 3, label: '3天' },
            { value: 4, label: '4天' },
            { value: 5, label: '5天' },
            { value: 7, label: '7天' },
            { value: 10, label: '10天' },
            { value: 15, label: '15天' },
          ].map(({ value, label }) => (
            <button key={value} type="button" onClick={() => setDays(value)}
              className={`py-3 text-sm rounded-xl border font-medium transition active:scale-95 ${
                days === value
                  ? 'bg-travel-blue text-white border-travel-blue shadow-md'
                  : 'bg-gray-50 text-travel-text border-gray-200 hover:border-travel-blue hover:bg-blue-50'
              }`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Preferences */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-2">🏷️ 旅行偏好（可多选）</label>
        <div className="grid grid-cols-2 gap-2">
          {PREFERENCES.map((p) => (
            <button key={p} type="button" onClick={() => togglePreference(p)}
              className={`px-4 py-3 text-sm rounded-xl border font-medium transition active:scale-95 ${
                preferences.includes(p)
                  ? 'bg-travel-green text-white border-travel-green shadow-md'
                  : 'bg-gray-50 text-travel-text border-gray-200 active:bg-green-50'
              }`}>
              {PREFERENCE_LABELS[p]}
            </button>
          ))}
        </div>
      </div>

      {/* Submit */}
      <button type="submit" disabled={loading || !origin.trim() || !destination.trim()}
        className="w-full py-4 bg-gradient-to-r from-travel-blue to-travel-green text-white font-semibold text-base rounded-xl shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98]">
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="inline-block w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            规划中...
          </span>
        ) : (
          '🚀 开始规划'
        )}
      </button>
    </form>
  );
};

export default PlanForm;
