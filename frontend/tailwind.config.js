/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  theme: {
    extend: {
      colors: {
        sce: {
          bg: '#0f1115',
          surface: '#1a1d24',
          card: '#1f2937',
          border: '#374151',
          text: '#e5e7eb',
          muted: '#9ca3af',
          blue: '#3b82f6',
          'blue-hover': '#2563eb',
        },
      },
    },
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: [
      {
        sce: {
          primary: '#3b82f6',
          secondary: '#6b7280',
          accent: '#10b981',
          neutral: '#1f2937',
          'base-100': '#0f1115',
          'base-200': '#1a1d24',
          'base-300': '#374151',
          info: '#3b82f6',
          success: '#10b981',
          warning: '#f59e0b',
          error: '#ef4444',
        },
      },
    ],
    darkTheme: 'sce',
  },
}
