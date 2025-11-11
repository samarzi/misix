/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
      colors: {
        background: "#05060d",
        backgroundMuted: "#0c1020",
        surface: "rgba(17, 22, 40, 0.65)",
        surfaceAlt: "rgba(14, 19, 34, 0.85)",
        surfaceGlass: "rgba(79, 97, 255, 0.08)",
        border: "rgba(126, 140, 179, 0.18)",
        borderStrong: "rgba(126, 140, 179, 0.35)",
        primary: "#5a6dff",
        primaryMuted: "rgba(90, 109, 255, 0.18)",
        primaryGlow: "rgba(90, 109, 255, 0.35)",
        accent: "#8a7dff",
        accent2: "#4ed2f0",
        text: "#f5f8ff",
        textSecondary: "#c2c7dd",
        textMuted: "#7a86a8",
        danger: "#ff6b6b",
        success: "#4ade80",
      },
      boxShadow: {
        card: "0 16px 60px rgba(10, 16, 40, 0.45)",
        glow: "0 0 35px rgba(90, 109, 255, 0.45)",
      },
      borderRadius: {
        xl: "14px",
      },
      backgroundImage: {
        'radial-overlay': "radial-gradient(circle at 20% 20%, rgba(90,109,255,0.18), transparent 55%), radial-gradient(circle at 80% 10%, rgba(78,210,240,0.12), transparent 55%), radial-gradient(circle at 50% 80%, rgba(119,79,255,0.15), transparent 60%)",
      },
      keyframes: {
        'float-slow': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        'pulse-border': {
          '0%,100%': { boxShadow: '0 0 0 0 rgba(90,109,255,0.35)' },
          '70%': { boxShadow: '0 0 0 12px rgba(90,109,255,0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0%' },
          '100%': { backgroundPosition: '200% 0%' },
        },
      },
      animation: {
        'float-slow': 'float-slow 8s ease-in-out infinite',
        'pulse-border': 'pulse-border 3.5s ease-in-out infinite',
        shimmer: 'shimmer 3s linear infinite',
      },
      transitionTimingFunction: {
        'out-soft': 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
      transitionDuration: {
        350: '350ms',
        450: '450ms',
      },
    },
  },
  plugins: [],
};
