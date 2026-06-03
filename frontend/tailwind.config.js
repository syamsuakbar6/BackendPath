/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1f2933",
        paper: "#f7f8f5",
        line: "#d8ded3",
        moss: "#516b45",
        teal: "#24746b",
        amber: "#b7791f",
        berry: "#9f3757"
      },
      boxShadow: {
        soft: "0 12px 30px rgba(31, 41, 51, 0.08)"
      }
    }
  },
  plugins: []
};
