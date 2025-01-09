// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'space-blue': 'var(--space-blue)',
        'neon-blue': 'var(--neon-blue)',
        'neon-purple': 'var(--neon-purple)',
        'chart-blue': 'var(--chart-blue)',
        'chart-purple': 'var(--chart-purple)',
      },
    },
  },
  plugins: [],
}