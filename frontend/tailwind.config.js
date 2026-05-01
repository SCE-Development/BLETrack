/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  theme: {
    extend: {},
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: [
      {
        sce: {
          primary: '#007bff',
          secondary: '#6c757d',
          accent: '#37cdbe',
          neutral: '#3d4451',
          'base-100': '#111827',
          'base-200': '#1f2937',
          'base-300': '#374151',
          info: '#3abff8',
          success: '#36d399',
          warning: '#fbbd23',
          error: '#f87272',
        },
      },
    ],
    darkTheme: 'sce',
  },
}
