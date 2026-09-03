/** @type {import('tailwindcss').Config} */
const fs = require('fs');
const safelist = fs.readFileSync('./_safelist.txt','utf8').split('\n').filter(Boolean);
module.exports = {
  content: [
    "../app.py",
    "../ops_auth.py",
    "../*.py",
    "../*.html"
  ],
  safelist: safelist,
  theme: { extend: {} },
  plugins: []
}
