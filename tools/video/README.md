# Video promocional de la demo

Regraba el video cuando cambie la demo. Todo corre en local (base temporal y llave de prueba), así que no toca la
demo publicada, la base real ni la llave de administración.

```bash
cd tools/video && ./grabar.sh      # resultado: tools/video/out/video-demo-citas.mp4
```

Requisitos: macOS, Google Chrome, Node 22+, Python 3 y el entorno de la API (`api/.venv`). La escena del chat usa
`api/.env` (cuesta unos centavos); si no existe, el chat responde que no está disponible.

- `grabar.js`: guion de la grabación (Playwright con Chrome, 540×960, subtítulos en pantalla). Los textos están en
  el propio archivo.
- `lofi.py`: música original sintetizada (piano eléctrico, ritmo con swing, vinilo). Sin muestras ni licencias.
- `grabar.sh`: levanta el sitio y la API locales, graba, genera la música y mezcla todo con `ffmpeg-static`.

Si cambias los textos o el orden de la demo, ajusta `grabar.js` (selectores de la reserva, del chat y de `/consultorio`).
