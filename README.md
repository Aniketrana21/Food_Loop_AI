# FoodLoop AI 🥗 🔄 🚚
> **Intelligent, AI-Powered Surplus Food Redistribution & Autonomous Dispatch Logistics**

FoodLoop AI is an end-to-end mission-critical platform engineered to eliminate commercial food waste at scale. By uniting surplus donors (hotels, caterers, supermarkets, bakeries) with non-profit recipients (food banks, shelters, soup kitchens) and volunteer couriers, FoodLoop AI optimizes food rescue using **Google OR-Tools** and forecasts perishable shelf life using **XGBoost**.

---

## 🏛️ System Architecture & Monorepo Layout

```
foodloop-ai/
├── frontend/             # Next.js 14 App Router + TypeScript + Tailwind CSS
├── backend/              # Python + FastAPI + SQLAlchemy + Pydantic v2
├── ml/                   # XGBoost surplus predictor + FDA shelf-life model
├── database/             # PostgreSQL / Supabase DDL schema, RLS, and seed data
├── docs/                 # Architecture, API specs, OR-Tools formulation, RAG design
├── tests/                # Pytest unit & integration test suite (100% passing)
├── infrastructure/       # Docker Compose, Dockerfiles, Vercel config, Env templates
└── README.md             # Platform overview and developer quick start
```

---

## ⚡ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 14 App Router, TypeScript, Tailwind CSS, Lucide Icons, Glassmorphism UI |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| **Database** | PostgreSQL / Supabase, PostGIS geo-indexing, pgvector, Row-Level Security (RLS) |
| **Authentication** | Supabase Auth + Role-Based Access Control (RBAC: Donor, Recipient, Driver, Admin) |
| **Machine Learning** | Python, Pandas, Scikit-learn, XGBoost (Surplus regressor & spoilage classifier) |
| **Optimization** | Google OR-Tools (Capacitated Vehicle Routing Problem with Time Windows - CVRPTW) |
| **LLM Layer** | Provider-Agnostic Engine (Google Gemini, OpenAI, or intelligent culinary fallback) |
| **RAG** | Vector similarity retrieval over FDA Food Code, Good Samaritan Act & Logistics SOPs |
| **Testing** | Pytest, TestClient, In-memory SQLite fixtures |
| **Deployment** | Vercel (Frontend), Docker Compose & Render/Railway/Cloud Run (Backend) |

---

## 🌐 Supabase Integration

FoodLoop AI is pre-configured with Supabase:
- **Project URL**: `https://cskzbogqwiqzwciuviow.supabase.co`
- **Publishable Key**: `sb_publishable_KOX8cTLR2U2fv4k3VsTxhA_EvH1QNcN`
- **Database Engine**: PostgreSQL with `uuid-ossp` and `pgcrypto` extensions
- **DDL Schema**: Located in [`database/schema.sql`](database/schema.sql)
- **Seed Data**: Located in [`database/seed.sql`](database/seed.sql)

---

## 🚀 Quick Start Guide

### 1. Backend Setup (FastAPI & ML)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app.main:app --reload --port 8000
```
- API Documentation (Swagger / OpenAPI): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 2. Machine Learning Pipeline

```bash
cd ml

# Train the XGBoost surplus forecasting & spoilage risk models
python train_surplus_model.py

# Run real-time prediction test
python predict.py
```

### 3. Frontend Setup (Next.js & Tailwind CSS)

```bash
cd frontend

# Install node dependencies
npm install

# Start Next.js development server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Running Tests

```bash
# Run complete test suite across Auth, Listings, ML, Optimizer, and RAG
python -m pytest tests/
```

---

## 🧠 Core Feature Highlights

### 1. Real-Time Bay Area Dispatch Map
- Visualizes donors (green beacons), recipient food banks (violet pins), and active volunteer vehicles.
- Real-time animated polylines trace optimized courier delivery routes.

### 2. Google OR-Tools CVRPTW Solver
- Solves Capacitated Vehicle Routing Problem with strict Expiry Time Windows (Earliest Expiry First).
- Enforces vehicle cargo capacity, pickup-before-dropoff precedence, and service time limits.

### 3. Thermodynamic Spoilage & Shelf-Life Engine
- Evaluates biological decay curves based on FDA Food Code danger zone rules (4°C-60°C).
- Automatically tags urgent listings requiring rapid courier dispatch within 4 hours.

### 4. AI Food Safety & Recipe Co-Pilot (RAG + LLM)
- **Safety Mode**: Vector search over the Bill Emerson Good Samaritan Act, FDA regulations, and transport SOPs.
- **Culinary Mode**: Commercial bulk recipe synthesizer scaling surplus ingredients into 20-200 portions.

### 5. Environmental & Social Impact Ledger
- Real-time metrics tracking: Kilograms diverted from landfill, meals served, CO₂ avoided, and water conserved.
- Corporate sustainability leaderboard for participating kitchens and supermarkets.

---

## 📄 License
MIT License. Developed for the FoodLoop AI Initiative.
