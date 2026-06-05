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
      className="mx-4 p-5 bg-white rounded-card shadow-md space-y-4"
    >
      {/* Origin & Destination */}
      <div className="flex items-center gap-2">
        <div className="flex-1">
          <label className="block text-xs font-medium text-travel-muted mb-1">📍 出发地</label>
          <input type="text" value={origin} onChange={(e) => setOrigin(e.target.value)}
            placeholder="例如：上海"
            className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-travel-blue/30 focus:border-travel-blue transition" required />
        </div>
        <div className="pt-5 text-travel-muted">→</div>
        <div className="flex-1">
          <label className="block text-xs font-medium text-travel-muted mb-1">🎯 目的地</label>
          <input type="text" value={destination} onChange={(e) => setDestination(e.target.value)}
            placeholder="例如：杭州"
            className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-travel-blue/30 focus:border-travel-blue transition" required />
        </div>
      </div>

      {/* Budget */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-1">💰 总预算</label>
        <div className="flex items-center gap-3">
          <input type="range" min={500} max={50000} step={100} value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
            className="flex-1 accent-travel-green" />
          <span className="text-sm font-semibold text-travel-text w-20 text-right">¥{budget.toLocaleString()}</span>
        </div>
      </div>

      {/* Intercity mode */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-1">🚗 城市间交通</label>
        <div className="flex flex-wrap gap-2">
          {TRAVEL_MODES.map((mode) => (
            <button key={mode} type="button" onClick={() => setIntercityMode(mode)}
              className={`px-3 py-1.5 text-xs rounded-full border transition ${
                intercityMode === mode
                  ? 'bg-travel-blue text-white border-travel-blue'
                  : 'bg-white text-travel-text border-gray-200 hover:border-travel-blue'
              }`}>
              {TRAVEL_MODE_LABELS[mode]}
            </button>
          ))}
        </div>
      </div>

      {/* City transit */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-1">🚕 市内交通</label>
        <div className="flex flex-wrap gap-2">
          {CITY_TRANSITS.map((mode) => (
            <button key={mode} type="button" onClick={() => setCityTransit(mode)}
              className={`px-3 py-1.5 text-xs rounded-full border transition ${
                cityTransit === mode
                  ? 'bg-travel-green text-white border-travel-green'
                  : 'bg-white text-travel-text border-gray-200 hover:border-travel-green'
              }`}>
              {CITY_TRANSIT_LABELS[mode]}
            </button>
          ))}
        </div>
      </div>

      {/* Date & Days */}
      <div className="flex gap-3">
        <div className="flex-1">
          <label className="block text-xs font-medium text-travel-muted mb-1">📅 出发日期</label>
          <input type="date" value={startDate} min={today}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-travel-blue/30" />
        </div>
        <div className="flex-1">
          <label className="block text-xs font-medium text-travel-muted mb-1">📆 出行天数</label>
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5, 7, 10, 15].map((d) => (
              <button key={d} type="button" onClick={() => setDays(d)}
                className={`flex-1 py-2 text-xs rounded-lg border transition ${
                  days === d
                    ? 'bg-travel-blue text-white border-travel-blue'
                    : 'bg-white text-travel-text border-gray-200 hover:border-travel-blue'
                }`}>
                {d}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Preferences */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-1">🏷️ 旅行偏好（可多选）</label>
        <div className="flex flex-wrap gap-2">
          {PREFERENCES.map((p) => (
            <button key={p} type="button" onClick={() => togglePreference(p)}
              className={`px-3 py-1.5 text-xs rounded-full border transition ${
                preferences.includes(p)
                  ? 'bg-travel-green text-white border-travel-green'
                  : 'bg-white text-travel-text border-gray-200 hover:border-travel-green'
              }`}>
              {PREFERENCE_LABELS[p]}
            </button>
          ))}
        </div>
      </div>

      {/* Submit */}
      <button type="submit" disabled={loading || !origin.trim() || !destination.trim()}
        className="w-full py-3.5 bg-gradient-to-r from-travel-blue to-travel-green text-white font-semibold text-base rounded-xl shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98]">
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
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
