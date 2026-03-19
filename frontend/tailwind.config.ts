import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary-blue': 'var(--primary-blue)',
        'secondary-blue': 'var(--secondary-blue)',
        'blue-bg': 'var(--blue-bg)',
        'eel': 'var(--eel)',
        'gray': 'var(--gray)',
        'light-gray': 'var(--light-gray)',
        'background': 'var(--background)',
        'white': 'var(--white)',
        'error-red': 'var(--error-red)',
        'kakao-yellow': 'var(--kakao-yellow)',
      }
    },
  },
  plugins: [],
} satisfies Config
