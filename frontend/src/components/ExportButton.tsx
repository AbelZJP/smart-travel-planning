import React, { useState } from 'react';
import html2canvas from 'html2canvas';

interface ExportButtonProps {
  resultRef: React.RefObject<HTMLDivElement | null>;
}

const ExportButton: React.FC<ExportButtonProps> = ({ resultRef }) => {
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    if (!resultRef.current) return;
    setExporting(true);
    try {
      const mapContainers = resultRef.current.querySelectorAll('[data-map-container]');
      mapContainers.forEach((el) => {
        el.setAttribute('data-export-mode', 'true');
        el.dispatchEvent(new CustomEvent('exportModeChange', { bubbles: true }));
      });

      await new Promise((resolve) => setTimeout(resolve, 800));

      const canvas = await html2canvas(resultRef.current, {
        backgroundColor: '#F0FDF4',
        scale: 2,
        useCORS: true,
        allowTaint: true,
        logging: false,
      });

      const link = document.createElement('a');
      link.download = `旅行规划_${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();

      mapContainers.forEach((el) => {
        el.removeAttribute('data-export-mode');
        el.dispatchEvent(new CustomEvent('exportModeChange', { bubbles: true }));
      });
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
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
