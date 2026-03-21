/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        background: '#09090b',
        panel:      '#18181b',
        border:     '#27272a',
        primary: {
          light:   '#60a5fa',
          DEFAULT: '#3b82f6',
          dark:    '#2563eb',
        },
        success: '#10b981',
        warning: '#f59e0b',
        danger:  '#ef4444',
        text: {
          main:  '#f4f4f5',
          muted: '#a1a1aa',
        },
      },
      boxShadow: {
        glass: '0 4px 30px rgba(0, 0, 0, 0.6)',
        glow:  '0 0 20px rgba(59, 130, 246, 0.35)',
        'glow-red': '0 0 20px rgba(239, 68, 68, 0.35)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
