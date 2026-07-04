/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        travel: {
          blue: '#3B82F6',
          green: '#10B981',
          light: '#F0FDF4',
          card: '#FFFFFF',
          text: '#1F2937',
          muted: '#6B7280',
          accent: '#F59E0B',
        },
      },
      borderRadius: {
        card: '16px',
      },
      keyframes: {
        breathing: {
          '0%, 100%': {
            transform: 'scale(1)',
            boxShadow:
              '0 4px 14px rgba(59, 130, 246, 0.25), 0 0 0 0 rgba(16, 185, 129, 0.25)',
          },
          '50%': {
            transform: 'scale(1.015)',
            boxShadow:
              '0 10px 28px rgba(59, 130, 246, 0.45), 0 0 0 8px rgba(16, 185, 129, 0)',
          },
        },
      },
      animation: {
        breathing: 'breathing 1.6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
