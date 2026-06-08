import React, { useState } from 'react';
import html2canvas from 'html2canvas';

interface ExportButtonProps {
  resultRef: React.RefObject<HTMLDivElement | null>;
  onExportStart: () => void;
  onExportEnd: () => void;
}

const ExportButton: React.FC<ExportButtonProps> = ({ resultRef, onExportStart, onExportEnd }) => {
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    if (!resultRef.current) return;
    setExporting(true);

    try {
      // 1. 先切换到静态图模式
      onExportStart();

      // 2. 等 React 重渲染 + 静态图加载完成
      await new Promise((resolve) => setTimeout(resolve, 100));
      const images = resultRef.current.querySelectorAll('img');
      await Promise.all(
        Array.from(images).map(
          (img) =>
            new Promise<void>((resolve) => {
              if (img.complete) resolve();
              else {
                img.onload = () => resolve();
                img.onerror = () => resolve();
              }
            })
        )
      );
      await new Promise((resolve) => setTimeout(resolve, 300));

      // 3. 截图
      const canvas = await html2canvas(resultRef.current, {
        backgroundColor: '#F0FDF4',
        scale: 2,
        useCORS: true,
        allowTaint: true,
        logging: false,
      });

      // 4. 下载
      const link = document.createElement('a');
      link.download = `旅行规划_${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      // 5. 恢复动态地图
      onExportEnd();
      setExporting(false);
    }
  };

  return (
    <button onClick={handleExport} disabled={exporting}
      className="w-full py-3 bg-travel-text text-white font-semibold text-sm rounded-xl hover:bg-gray-800 disabled:opacity-50 transition-all active:scale-[0.98] flex items-center justify-center gap-2">
      {exporting ? (
        <>
          <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          导出中...
        </>
      ) : (
        '📥 导出长截图'
      )}
    </button>
  );
};

export default ExportButton;
