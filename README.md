# CHARTIX Final Project

## What this includes

- Node.js Express backend
- Python `yfinance` data engine
- Firebase Auth-ready login screen
- Firestore-ready user watchlist
- Google Ad Space placeholders
- Required cookie / disclaimer consent panel
- English UI
- Yahoo-style price header with after-hours support
- RSI, MACD, Bollinger, SMA20/SMA50/SMA200
- AI technical analysis disclaimer
- 15 second memory cache

## Install

```powershell
cd "C:\Users\GİRAY\OneDrive\Masaüstü\Chartix"
npm.cmd install
py -m pip install -r requirements.txt
npm.cmd start
```

Open:

```text
http://localhost:3000
```

## Firebase setup

1. Go to Firebase Console.
2. Create a project.
3. Add a Web App.
4. Copy your `firebaseConfig`.
5. Paste it into `public/js/firebase-config.js`.
6. Enable Authentication:
   - Email/Password
   - Google
7. Create Firestore Database.
8. Add rules from `firebase/firestore.rules`.

## Important

`yfinance` is not an official API. It is common for personal projects, but availability may change.
