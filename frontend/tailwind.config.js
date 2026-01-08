/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#0F172A", // Slate 900
          foreground: "#F8FAFC", // Slate 50
        },
        secondary: {
          DEFAULT: "#F1F5F9", // Slate 100
          foreground: "#0F172A",
        },
        accent: {
          DEFAULT: "#3B82F6", // Blue 500
          foreground: "#FFFFFF",
        },
        destructive: {
          DEFAULT: "#EF4444", // Red 500
          foreground: "#FFFFFF",
        },
      },
    },
  },
  plugins: [],
}
