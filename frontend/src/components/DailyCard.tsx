import React from 'react';
import type { DailyPlan } from '../types/plan';
import DailyMap from './DailyMap';

interface DailyCardProps {
  plan: DailyPlan;
  dayIndex: number;
  totalDays: number;
  exportMode: boolean;
  amapKey: string;
}

const DailyCard: React.FC<DailyCardProps> = ({ plan, dayIndex, totalDays, exportMode, amapKey }) => {
  const weatherEmoji = (w: string) => {
    if (w.includes('晴')) return '☀️';
    if (w.includes('多云')) return '⛅';
    if (w.includes('阴')) return '☁️';
    if (w.includes('雨')) return '🌧';
    if (w.includes('雪')) return '❄️';
    return '🌤';
  };

  return (
    <div className="bg-white rounded-card shadow-md overflow-hidden">
      {/* Day header */}
      <div className="px-4 py-3 bg-gradient-to-r from-travel-blue/5 to-travel-green/5 border-b border-gray-50">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-travel-text">Day {dayIndex + 1} · {plan.date}</h3>
          <span className="text-xs text-travel-muted">{dayIndex + 1}/{totalDays}</span>
        </div>
        {plan.weather && (
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/80">
              <span>{weatherEmoji(plan.weather.day_weather)}</span>
              <span className="font-medium">{plan.weather.day_weather}</span>
            </span>
            <span className="text-travel-muted">
              🌡 {plan.weather.low_temp}°C ~ {plan.weather.high_temp}°C
            </span>
            {plan.weather.wind && (
              <span className="text-travel-muted">💨 {plan.weather.wind}</span>
            )}
          </div>
        )}
        {plan.weather?.clothing_advice && (
          <div className="mt-1.5 flex items-start gap-1 text-xs text-amber-600 bg-amber-50 rounded-lg px-2.5 py-1.5">
            <span>👔</span>
            <span>{plan.weather.clothing_advice}</span>
          </div>
        )}
        {plan.weather?.travel_advice && (
          <div className="mt-1 flex items-start gap-1 text-xs text-travel-green bg-green-50 rounded-lg px-2.5 py-1.5">
            <span>💡</span>
            <span>{plan.weather.travel_advice}</span>
          </div>
        )}
      </div>

      {/* Route map */}
      {plan.route_coordinates.length > 0 && (
        <DailyMap coordinates={plan.route_coordinates} dayIndex={dayIndex} exportMode={exportMode} amapKey={amapKey} />
      )}

      {/* Timeline */}
      <div className="px-4 py-3 space-y-3">
        {plan.transport.map((t, i) => (
          <div key={`t-${i}`} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-sm">🚄</div>
              {i < plan.transport.length - 1 && <div className="w-0.5 h-full bg-blue-200 mt-1" />}
            </div>
            <div>
              <p className="text-sm font-medium text-travel-text">{t.from} → {t.to}</p>
              <p className="text-xs text-travel-muted">{t.mode} · ¥{t.cost}</p>
            </div>
          </div>
        ))}

        {plan.attractions.map((a) => (
          <div key={`a-${a.order}`} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-travel-blue text-white flex items-center justify-center text-xs font-bold">{a.order}</div>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-travel-text">{a.name}</p>
              <p className="text-xs text-travel-muted">
                {a.time_slot} · {a.duration}{a.ticket > 0 ? ` · ¥${a.ticket}` : ' · 免费'}{a.rating ? ` · ⭐${a.rating}` : ''}
              </p>
            </div>
          </div>
        ))}

        {plan.meals.map((m, i) => (
          <div key={`m-${i}`} className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center text-sm">
              {m.type === 'breakfast' ? '🥐' : m.type === 'lunch' ? '🍜' : '🍽'}
            </div>
            <div>
              <p className="text-sm font-medium text-travel-text">{m.suggestion}</p>
              <p className="text-xs text-travel-muted">
                {m.type === 'breakfast' ? '早餐' : m.type === 'lunch' ? '午餐' : '晚餐'} · 约 ¥{m.estimated_cost}
              </p>
            </div>
          </div>
        ))}

        {plan.hotel && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-sm">🏨</div>
            <div>
              <p className="text-sm font-medium text-travel-text">{plan.hotel.name}</p>
              <p className="text-xs text-travel-muted">
                ¥{plan.hotel.price}/晚{plan.hotel.rating ? ` · ⭐${plan.hotel.rating}` : ''}{plan.hotel.address ? ` · ${plan.hotel.address}` : ''}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Day cost */}
      <div className="px-4 py-2.5 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
        <span className="text-xs text-travel-muted">今日花费</span>
        <span className="text-sm font-bold text-travel-blue">¥{plan.daily_cost.toLocaleString()}</span>
      </div>
    </div>
  );
};

export default DailyCard;
