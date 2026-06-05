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
    },
  },
  plugins: [],
};
