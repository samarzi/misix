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
        background: "#f5f6f8",
        surface: "#ffffff",
        surfaceAlt: "#f1f3f6",
        border: "#d0d5dd",
        primary: "#2f6bff",
        primaryMuted: "#e6edff",
        text: "#111827",
        textMuted: "#5b6472",
        danger: "#c62828",
        success: "#2e7d32",
      },
      boxShadow: {
        card: "0 2px 6px rgba(15, 23, 42, 0.04)",
      },
      borderRadius: {
        xl: "14px",
      },
    },
  },
  plugins: [],
};
