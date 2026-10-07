# NudgeWasteAI Frontend — Civic Waste Segregation & Change Platform

Production React + Vite frontend application for **NudgeWasteAI** — an AI-powered civic waste segregation and behavior-change platform built for India's statutory municipal waste categories (`Wet`, `Dry`, `Sanitary`, `Special Care`).

---

## 🏗️ Architecture

The application strictly enforces a decoupled 4-component architecture:

```
Frontend (React + Vite)
    │
    ▼ (HTTP REST API)
Backend (FastAPI)
    │
    ├──► Machine_Learning (PyTorch 4-Class Statutory Waste Classifier)
    └──► Database (PyMongo Repository Layer)
            │
            ▼
          MongoDB (nudgewaste_db)
```

> **Critical Security Rule**: The frontend communicates **exclusively** with the Backend REST API. The frontend never connects directly to MongoDB, PyMongo, PyTorch, or ML modules.

---

## 🚀 Getting Started

### Prerequisites

- **Node.js**: v18.0.0+
- **npm**: v9.0.0+
- **NudgeWasteAI Backend**: Running at `http://127.0.0.1:8000`

---

## ⚙️ Environment Configuration

Create a `.env` file inside the `frontend/` directory (or copy from `.env.example`):

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## 🛠️ Available Scripts

In the `frontend/` directory, you can run:

### `npm run dev`
Runs the application in development mode with HMR at `http://localhost:5173`.

### `npm run build`
Compiles and bundles the production-ready static assets into the `dist/` directory.

### `npm run preview`
Locally previews the production build.

---

## 🧩 Features & User Workflows

### 1. Real Authentication Flow
- **Registration**: Supports Full Name, Email, Password, and City/Municipality.
- **Initial Welcome Bonus**: Every newly registered user automatically receives **500 Swachh Credits** recorded atomically on the backend database.
- **First-Time User Isolation**: Newly created accounts start with zero historical activity (0 items segregated, 0 streak days, empty history). No fake statistics are shown.
- **Token Persistence**: JWT Bearer token is saved in `localStorage` and automatically restored on page refresh via `/api/v1/users/me`.

### 2. AI Waste Scanner Engine
- Upload or capture image files of waste items.
- Calls `/api/v1/prediction/upload` -> Backend -> PyTorch ML Classifier.
- Displays predicted statutory category (`Wet`, `Dry`, `Sanitary`, `Special Care`), model confidence %, disposal bin guidance, and positive micro-nudges.

### 3. Verified Disposal & Credit Earning
- Citizen confirms disposal into recommended statutory bin.
- Backend verifies disposal, creates MongoDB disposal document, generates nudge, and awards Swachh Credits (`+10` to `+20` credits depending on statutory category rules).
- Frontend immediately refreshes authoritative user balance.

### 4. Swachh Credits & Municipal Rewards Marketplace
- Displays real credit balance backed by MongoDB transaction ledger.
- Browse available municipal rewards (Property Tax Rebates, Metro Passes, Utility Vouchers).
- **Atomic Deduction**: Attempting redemption deducts credits on backend. If credits < cost, backend returns HTTP 400 `"Insufficient credit points"` and frontend displays clear feedback without modifying balance or creating negative balances.

---

## 📁 Directory Structure

```
frontend/
├── src/
│   ├── api/                 # Centralized API client & endpoint modules
│   │   ├── client.js
│   │   ├── authApi.js
│   │   ├── predictionApi.js
│   │   ├── disposalApi.js
│   │   ├── creditsApi.js
│   │   ├── rewardsApi.js
│   │   ├── analyticsApi.js
│   │   └── userApi.js
│   │
│   ├── components/          # Modular React UI components
│   │   ├── layout/          # Sidebar, Header, AppLayout
│   │   ├── common/          # Card, Badge, EmptyState, Modal, LoadingSpinner
│   │   ├── scanner/         # ImageUploader, PredictionResult, DisposalConfirmModal
│   │   ├── charts/          # SegregationTrendChart, WasteStreamDistributionChart
│   │   └── nudges/          # NudgeBanner
│   │
│   ├── context/             # AuthContext & ToastContext providers
│   ├── constants/           # Statutory waste category metadata & bin colors
│   ├── pages/               # Login, Register, Home, Dashboard, Scanner, etc.
│   ├── routes/              # AppRoutes & ProtectedRoute
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
│
├── .env.example
├── package.json
└── README.md
```
