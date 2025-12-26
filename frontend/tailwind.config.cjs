/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        Ink: "rgb(var(--Ink) / <alpha-value>)",
        Paper: "rgb(var(--Paper) / <alpha-value>)",
        Mint: "rgb(var(--Mint) / <alpha-value>)",
        Coral: "rgb(var(--Coral) / <alpha-value>)",
        Sun: "rgb(var(--Sun) / <alpha-value>)",
        Surf: "rgb(var(--Surf) / <alpha-value>)"
      },
      boxShadow: {
        Soft: "0 16px 40px rgba(16, 24, 40, 0.12)"
      }
    }
  },
  plugins: []
};
