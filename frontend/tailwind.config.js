/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        tg: {
          bg: 'var(--tg-theme-bg-color, #0F0F0F)',
          secondary: 'var(--tg-theme-secondary-bg-color, #1C1C1E)',
          text: 'var(--tg-theme-text-color, #FFFFFF)',
          hint: 'var(--tg-theme-hint-color, #8E8E93)',
          link: 'var(--tg-theme-link-color, #0098EA)',
          button: 'var(--tg-theme-button-color, #0098EA)',
          'button-text': 'var(--tg-theme-button-text-color, #FFFFFF)',
        },
        ton: '#0098EA',
        gold: '#FFD60A',
        surface: '#1C1C1E',
        border: '#2C2C2E',
        success: '#30D158',
        danger: '#FF453A',
        warning: '#FF9F0A',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'Segoe UI', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { transform: 'translateY(20px)', opacity: '0' }, to: { transform: 'translateY(0)', opacity: '1' } },
        pulseSoft: { '0%,100%': { opacity: '1' }, '50%': { opacity: '0.6' } },
      },
    },
  },
  plugins: [],
}
