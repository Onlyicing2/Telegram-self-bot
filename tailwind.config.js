/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'surface':           'var(--surface)',
        'surface-container': 'var(--surface-container)',
        'surface-variant':   'var(--surface-variant)',
        'on-surface':        'var(--on-surface)',
        'on-surface-variant':'var(--on-surface-variant)',
        'outline-variant':   'var(--outline-variant)',
        'primary':           'var(--primary)',
        'on-primary':        'var(--on-primary)',
        'error':             'var(--error)',
      },
    },
  },
  plugins: [],
};
