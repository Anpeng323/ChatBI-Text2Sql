/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#0B1220",
          800: "#131C31",
          700: "#16203A",
          600: "#24314F",
        },
        brand: {
          teal: "#14B8A6",
          blue: "#2563EB",
          purple: "#A78BFA",
          amber: "#F59E0B",
          red: "#EF4444",
        },
        txt: {
          hi: "#E2E8F0",
          mid: "#B6C2D9",
          low: "#94A3B8",
        },
      },
      fontFamily: {
        sans: [
          "PingFang SC",
          "Hiragino Sans GB",
          "Microsoft YaHei",
          "system-ui",
          "sans-serif",
        ],
      },
      boxShadow: {
        glow: "0 10px 30px rgba(29,78,216,.25)",
        panel: "0 10px 30px rgba(0,0,0,.35)",
      },
      keyframes: {
        fadeup: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "0% 50%" },
          "100%": { backgroundPosition: "100% 50%" },
        },
      },
      animation: {
        fadeup: "fadeup .25s ease-out",
        shimmer: "shimmer 3s linear infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
