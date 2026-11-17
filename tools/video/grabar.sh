#!/usr/bin/env bash
# Records the promo video of the demo against a LOCAL copy (temporary database, throwaway admin key), so the real
# admin key, the real database and the deployed demo are never touched. macOS + Google Chrome required.
# Result: tools/video/out/video-demo-citas.mp4 (vertical 540x960, ~50 s, original lo-fi music, no licenses).
# The chat scene calls the Claude API with api/.env (a few cents). Nothing is printed or stored from that key.
set -euo pipefail
cd "$(dirname "$0")"
ROOT=$(cd ../.. && pwd)
OUT=$PWD/out; mkdir -p "$OUT"; rm -f "$OUT"/*.webm
TMP=$(mktemp -d)
KEY="llave-de-prueba-solo-local-001"   # throwaway key, only valid for this local API

[ -d node_modules ] || npm install --silent
FFMPEG=$(node -e "console.log(require('ffmpeg-static'))")

# Playwright records video with its own ffmpeg build; point it to ffmpeg-static instead of downloading one.
REV=$(node -e "const b=JSON.parse(require('fs').readFileSync('node_modules/playwright-core/browsers.json','utf8')).browsers.find(x=>x.name==='ffmpeg');console.log(b.revision)")
mkdir -p "$TMP/pw/ffmpeg-$REV"
ln -s "$FFMPEG" "$TMP/pw/ffmpeg-$REV/ffmpeg-mac"
ln -s "$FFMPEG" "$TMP/pw/ffmpeg-$REV/ffmpeg-mac-arm64"

# The script owns ports 8000 (API) and 4321 (site): stop if something else is using them, and free them at the end.
for port in 8000 4321; do
  if lsof -ti "tcp:$port" >/dev/null 2>&1; then echo "El puerto $port está ocupado; ciérralo y vuelve a intentar." >&2; exit 1; fi
done
cleanup() { for port in 8000 4321; do lsof -ti "tcp:$port" 2>/dev/null | xargs kill 2>/dev/null || true; done; rm -rf "$TMP"; }
trap cleanup EXIT

# Local site (built without PUBLIC_API_URL: it talks to http://localhost:8000) and local API with a temp database.
(cd "$ROOT/web" && npm run build >/dev/null && npm run preview -- --host 127.0.0.1 --port 4321 >"$TMP/web.log" 2>&1) &
ENVFILE=(); [ -f "$ROOT/api/.env" ] && ENVFILE=(--env-file "$ROOT/api/.env")
(cd "$ROOT/api" && DEMO_DB_PATH="$TMP/video.sqlite" DEMO_ADMIN_KEY="$KEY" .venv/bin/uvicorn app.main:app --port 8000 "${ENVFILE[@]}" >"$TMP/api.log" 2>&1) &
for _ in $(seq 1 30); do curl -sf localhost:8000/api/health >/dev/null && curl -sf 127.0.0.1:4321/ >/dev/null && break; sleep 1; done

PLAYWRIGHT_BROWSERS_PATH="$TMP/pw" TEST_ADMIN_KEY="$KEY" OUT_DIR="$OUT" node grabar.js

python3 lofi.py   # writes lofi.wav (original music, synthesized)
WEBM=$(ls "$OUT"/*.webm | head -1)
"$FFMPEG" -loglevel error -y -i "$WEBM" -i lofi.wav \
  -filter_complex "[1:a]highpass=f=45,lowpass=f=4200,volume=0.9[a]" -map 0:v -map "[a]" \
  -c:v libx264 -pix_fmt yuv420p -crf 20 -preset medium -c:a aac -b:a 128k -shortest -movflags +faststart \
  "$OUT/video-demo-citas.mp4"
rm -f "$WEBM" lofi.wav
echo "Listo: $OUT/video-demo-citas.mp4"
