# demo-citas

Demo of the Buestro "Citas" package: a **fictional** dental office ("Clínica Dental Mezquite") with a landing page, booking, an FAQ assistant built on Claude, and a simulated WhatsApp reminder.

- `data/consultorio.json`: single source of truth (business, hours, services, FAQ, assistant rules). The landing page, the booking seed and the assistant prompt all read it.
- `docs/diseno-demo.md`: demo design, FAQ, assistant rules and the 2-minute walkthrough script.
- `web/`: Astro landing page (deployed on Vercel). Coming in package 1.3.
- `api/`: FastAPI booking and assistant (deployed on Render). Coming in packages 1.4–1.6.

Everything in this demo is fictional. It stores no health data and no data about minors.
