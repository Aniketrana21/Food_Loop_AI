# FoodLoop AI - Architectural Blueprint & System Design

FoodLoop AI is an end-to-end intelligent platform engineered to eliminate food waste at scale by pairing surplus donors (hotels, caterers, supermarkets, restaurants) with non-profit recipients (food banks, shelters, community kitchens) and deploying volunteer couriers via automated multi-stop route optimization.

---

## 1. High-Level System Architecture

```mermaid
graph TD
    subgraph Client Layer
        A1[Next.js App Router]
        A2[Tailwind CSS & shadcn/ui]
        A3[Interactive Dispatch Map Canvas]
        A4[AI Culinary & Safety Co-Pilot]
    end

    subgraph API Gateway & Backend
        B1[FastAPI Microservices]
        B2[Supabase Auth & RBAC Middleware]
        B3[SQLAlchemy ORM Engine]
    end

    subgraph Intelligence & Optimization Layer
        C1[XGBoost Surplus Predictor]
        C2[Thermodynamic Shelf-Life Engine]
        C3[Google OR-Tools CVRPTW Solver]
        C4[Provider-Agnostic LLM Layer]
        C5[RAG Semantic Vector Knowledge Base]
    end

    subgraph Data & Storage Layer
        D1[(PostgreSQL / Supabase)]
        D2[PostGIS & pgvector]
        D3[Supabase Storage Buckets]
    end

    Client Layer -->|REST API & WebSockets| B1
    B1 --> B2
    B2 --> B3
    B1 --> C1
    B1 --> C2
    B1 --> C3
    B1 --> C4
    B1 --> C5
    B3 --> D1
    C5 --> D2
```

---

## 2. Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    PROFILES ||--o{ FOOD_LISTINGS : creates
    PROFILES ||--o{ RESCUE_CLAIMS : requests
    PROFILES ||--o{ DELIVERIES : drives
    FOOD_LISTINGS ||--o{ RESCUE_CLAIMS : fulfills
    RESCUE_CLAIMS ||--o{ DELIVERIES : dispatches
    FOOD_LISTINGS ||--o{ IMPACT_METRICS : records

    PROFILES {
        uuid id PK
        string email
        string full_name
        string role
        string organization_name
        float latitude
        float longitude
        float capacity_kg
    }

    FOOD_LISTINGS {
        uuid id PK
        uuid donor_id FK
        string title
        string category
        float quantity_kg
        int portions
        string storage_temp
        timestamp expiry_at
        float estimated_shelf_life_hours
        string status
    }

    RESCUE_CLAIMS {
        uuid id PK
        uuid listing_id FK
        uuid recipient_id FK
        int claimed_portions
        float claimed_quantity_kg
        string status
    }

    DELIVERIES {
        uuid id PK
        uuid claim_id FK
        uuid driver_id FK
        int stop_sequence
        string status
        timestamp pickup_eta
        timestamp dropoff_eta
        float temperature_log_c
    }

    IMPACT_METRICS {
        uuid id PK
        uuid listing_id FK
        float co2_kg_saved
        int meals_provided
        float water_liters_saved
        float financial_value_usd
    }
```

---

## 3. End-to-End Rescue Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    actor Donor as Donor (Hotel/Bakery)
    participant API as FastAPI Backend
    participant ML as XGBoost & Shelf-Life Model
    actor Recipient as Food Bank / Shelter
    participant Solver as OR-Tools CVRPTW Solver
    actor Driver as Volunteer Courier

    Donor->>API: Post Surplus Food (e.g. 35kg Cooked Pasta)
    API->>ML: Estimate Remaining Safe Shelf-Life
    ML-->>API: 4.2 Safe Hours Remaining (FDA Danger Zone Rule)
    API->>Recipient: Broadcast Urgent Rescue Listing
    Recipient->>API: Claim 35kg for Evening Service
    API->>Solver: Trigger Automated Dispatch Optimization
    Solver-->>API: Multi-Stop Schedule (Pickup -> Dropoff)
    API->>Driver: Assign Turn-by-Turn Route Notification
    Driver->>API: Check-in at Donor & Log Cambro Temp (62°C)
    Driver->>Recipient: Deliver Food & Capture Digital Signature
    API->>API: Record Carbon & Meals Saved in Impact Ledger
```

---

## 4. Key Architectural Decisions

1. **Provider-Agnostic LLM Layer**: Decoupled with an abstract base class pattern. Works identically on Google Gemini (`gemini-1.5-flash`), OpenAI (`gpt-4o-mini`), or intelligent zero-dependency heuristic fallback.
2. **Resilient Solver Architecture**: Features both Google OR-Tools constraint programming and a high-performance heuristic solver (Earliest Expiry First + Capacity Clustering) ensuring zero downtime regardless of host OS C++ binary support.
3. **Database Dual-Compatibility**: Models designed to work both with Supabase PostgreSQL (with PostGIS and pgvector) and local SQLite instances during edge deployments or local testing.
