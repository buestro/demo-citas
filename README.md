# demo-citas

Demo of the Buestro "Citas" package: a **fictional** dental office ("Clínica Dental Mezquite") with a landing page, booking, an FAQ assistant built on Claude, and a simulated WhatsApp reminder.

- `data/consultorio.json`: single source of truth (business, hours, services, FAQ, assistant rules). The landing page, the booking seed and the assistant prompt all read it.
- `docs/diseno-demo.md`: demo design, FAQ, assistant rules and the 2-minute walkthrough script.
- `web/`: Astro landing page with the booking form (deployed on Vercel). Set `PUBLIC_API_URL` (see `web/.env.example`).
- `api/`: FastAPI booking API (deployed on Render, see `render.yaml`). It also serves the FAQ assistant and the doctor's view (`/consultorio`).

Everything in this demo is fictional. It stores no health data and no data about minors.

## Deploy (package 1.7)
1. **Render** (API): New > Blueprint from this repo. Set `ANTHROPIC_API_KEY`, `DEMO_ADMIN_KEY` and `DEMO_CORS_ORIGINS` (the Vercel URL, no trailing slash) in the dashboard. `DEMO_TRUSTED_PROXIES=1` and `DEMO_SIGNING_KEY` come from `render.yaml`.
2. **Vercel** (web): import the repo with root directory `web/` and set `PUBLIC_API_URL` to the Render URL. `web/vercel.json` adds the security headers; its CSP allows scripts only from the site itself (the scripts are bundled, never inline) and API calls to `*.onrender.com`. If the API lives on another domain, add it to `connect-src`.
3. Check the first deploy: `/api/health`, a booking from a phone, `/consultorio` with the key, and the response headers of the site.
