/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fef2f0',
          100: '#fde4e0',
          200: '#fbc9c1',
          300: '#f9a99c',
          400: '#f67d67',
          500: '#ee6c4d',
          600: '#e04d2a',
          700: '#bc3a1d',
          800: '#9a2f1a',
          900: '#7e2a1a',
        },
      },
      animation: {
        'spin-slow': 'spin 3s linear infinite',
      },
    },
  },
  plugins: [],
}
