# Logistics Platform - Full Production Architecture & PRD

## 1. Overview
A high-performance logistics platform for South India, connecting shippers with verified transporters. The system uses a dynamic pricing engine to provide instant, accurate quotes across 28 critical corridors.

## 2. Page Architecture
### Core Pages
- **Home (`/`)**: Hero section with truck matching widget.
- **Route Pages (`/routes/[city-a]-[city-b]`)**: 28 unique pages (e.g., Bangalore ↔ Chennai).
- **Cluster Pages (`/clusters/[cluster-slug]`)**: Regional logistics hubs (Western TN, Chennai Metro, etc.).
- **Blog (`/blog/[slug]`)**: SEO-optimized industry and route guides.
- **Pricing (`/pricing`)**: Interactive pricing calculator.

## 3. Dynamic Pricing Engine (DPYMA)
### Core Formula
`Final Price = (Base Cost + RDS Surcharge) * M_density * M_service * M_demand * M_tier + VAS + Fees + Insurance + GST`

### Key Multipliers
1. **Route Difficulty Score (RDS)**: Terrain, road quality, congestion, weather, tolls, accident rate, checkpoints.
2. **Urbanization Density (M_density)**: Multiplier based on city tiers (Metro, Tier 1/2/3).
3. **Deadhead / Lane Viability (M_tier)**: Probability of securing a return load on the corridor.

## 4. Technical Stack
- **Backend**: Python, Django, DRF, Celery, Redis, Channels (WebSockets).
- **Database**: PostgreSQL (Relational), Redis (Caching/Broker).
- **Servers**: Gunicorn, Nginx, Uvicorn (ASGI).
- **DevOps**: Docker, Docker Compose, GitHub Actions.

## 5. Integration Points
- **WhatsApp**: Primary CTA and quote delivery channel.
- **Sentry**: Error tracking.
- **Prometheus/Grafana**: Monitoring.

## 6. Route Coverage Matrix (Top 14 Corridors)
1. Bangalore ↔ Chennai
2. Chennai ↔ Coimbatore
3. Coimbatore ↔ Bangalore
4. Erode ↔ Bangalore
5. Thiruppur ↔ Chennai
6. Bangalore ↔ Thiruppur
7. Salem ↔ Erode
8. Salem ↔ Karur
9. Salem ↔ Bangalore
10. Erode ↔ Chennai
11. Chennai ↔ Sri City
12. Chennai ↔ Namakkal
13. Sri City ↔ Bangalore
14. Erode ↔ Thiruppur
