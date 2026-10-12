import typography from '@tailwindcss/typography';

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        sap: {
          blue: '#005A9E',
          accent: '#0A6ED1',
          navy: '#0A1B2A',
          darkBlue: '#0A1B2A',
          gold: '#E3A008',
          bgLight: '#F5F7FA',
          bgDark: '#0E131F',
          cardLight: '#FFFFFF',
          cardDark: '#161C2E',
          borderLight: '#E2E8F0',
          borderDark: '#2D3748',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [
    typography,
  ],
};
