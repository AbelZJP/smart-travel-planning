import React, { useEffect, useRef, useState } from 'react';
import type { RouteCoordinate } from '../types/plan';

interface DailyMapProps {
  coordinates: RouteCoordinate[];
  dayIndex: number;
  exportMode: boolean;
  amapKey: string;
}

declare global {
  interface Window {
    AMap: any;
  }
}

const DailyMap: React.FC<DailyMapProps> = ({ coordinates, dayIndex, exportMode, amapKey }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const [staticMapUrl, setStaticMapUrl] = useState<string>('');

  useEffect(() => {
    if (exportMode) {
      buildStaticMap();
      return;
    }
    if (!coordinates.length || !containerRef.current) return;
    initDynamicMap();

    return () => {
      if (mapRef.current) {
        mapRef.current.destroy();
        mapRef.current = null;
      }
    };
  }, [coordinates, exportMode, dayIndex]);

  const initDynamicMap = () => {
    const AMap = window.AMap;
    if (!AMap || !containerRef.current) return;

    const map = new AMap.Map(containerRef.current, {
      zoom: 12,
      center: [coordinates[0].lng, coordinates[0].lat],
      resizeEnable: false,
      dragEnable: false,
      zoomEnable: false,
      scrollWheel: false,
      doubleClickZoom: false,
      touchZoom: false,
    });
    mapRef.current = map;

    coordinates.forEach((coord) => {
      const isHotel = coord.type === 'hotel';
      const content = isHotel
        ? `<div style="background:#FF6B6B;color:#fff;width:28px;height:28px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:16px;box-shadow:0 2px 6px rgba(0,0,0,.3);">🏨</div>`
        : `<div style="background:#3B82F6;color:#fff;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:bold;box-shadow:0 2px 6px rgba(0,0,0,.3);">${coord.order}</div>`;

      new AMap.Marker({
        position: [coord.lng, coord.lat],
        content,
        offset: new AMap.Pixel(isHotel ? -14 : -12, isHotel ? -14 : -12),
        map,
      });
    });

    if (coordinates.length >= 2) {
      const path = coordinates.map((c) => [c.lng, c.lat]);
      new AMap.Polyline({
        path,
        strokeColor: '#3B82F6',
        strokeWeight: 3,
        strokeOpacity: 0.7,
        strokeStyle: 'dashed',
        showDir: true,
        map,
      });
    }

    map.setFitView(null, false, [60, 40, 40, 40]);
  };

  const buildStaticMap = () => {
    if (!coordinates.length) return;
    const base = 'https://restapi.amap.com/v3/staticmap';
    const markers = coordinates
      .map((c) => {
        const style = c.type === 'hotel' ? 'mid,0xFF6B6B,A' : `mid,0x3B82F6,${c.order}`;
        return `markers=${style}:${c.lng},${c.lat}`;
      })
      .join('&');
    const points = coordinates.map((c) => `${c.lng},${c.lat}`).join(';');
    const path = `path=0x3B82F6,2,0:${points}`;
    const url = `${base}?key=${amapKey}&size=800*200&scale=2&zoom=12&${markers}&${path}`;
    setStaticMapUrl(url);
  };

  if (exportMode && staticMapUrl) {
    return (
      <div className="w-full h-[120px] rounded-lg overflow-hidden bg-gray-100 mt-2">
        <img src={staticMapUrl} alt={`Day ${dayIndex + 1} route map`} className="w-full h-full object-cover" />
      </div>
    );
  }

  return (
    <div className="w-full h-[180px] rounded-lg overflow-hidden bg-gray-100 mt-2">
      {coordinates.length > 0 ? (
        <div ref={containerRef} className="w-full h-full" />
      ) : (
        <div className="w-full h-full flex items-center justify-center text-travel-muted text-xs">暂无路线数据</div>
      )}
    </div>
  );
};

export default DailyMap;
