/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        midnight: {
          DEFAULT: "#101B2D",
          dark: "#0B1320",
          light: "#172740",
        },
        deep: {
          blue: "#243B60",
          hover: "#2D4B7A",
        },
        electric: {
          DEFAULT: "#3B82F6",
          light: "#60A5FA",
          dark: "#2563EB",
          subtle: "rgba(59, 130, 246, 0.12)",
        },
        teal: {
          DEFAULT: "#21C7B7",
          light: "#4FE0D2",
          dark: "#179B8F",
          subtle: "rgba(33, 199, 183, 0.12)",
        },
        soft: {
          white: "#F5F7FA",
          muted: "#CBD5E1", // Slate-300: High-contrast readable secondary text
          dim: "#94A3B8",   // Slate-400: Crisp, legible technical labels & metadata
        },
      },
      fontFamily: {
        sans: ["Manrope", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      boxShadow: {
        card: "0 10px 30px -10px rgba(11, 19, 32, 0.5)",
        "card-hover": "0 20px 40px -15px rgba(36, 59, 96, 0.35)",
        highlight: "0 0 20px -5px rgba(59, 130, 246, 0.35)",
        teal: "0 0 20px -5px rgba(33, 199, 183, 0.35)",
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
}
