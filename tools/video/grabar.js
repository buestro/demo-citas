// Records the ~50 s tour of the demo (mobile viewport, Spanish captions) as a webm. Run it through grabar.sh.
const { chromium } = require("playwright-core");
const WEB = "http://127.0.0.1:4321";
const KEY = process.env.TEST_ADMIN_KEY ?? "llave-de-prueba-solo-local-001";
const OUT = process.env.OUT_DIR ?? "out";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  const context = await browser.newContext({
    viewport: { width: 540, height: 960 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true, locale: "es-MX",
    timezoneId: "America/Mexico_City",
    recordVideo: { dir: OUT, size: { width: 540, height: 960 } },
  });
  await context.addInitScript(() => {
    window.__cap = (t) => {
      let el = document.getElementById("__cap");
      if (!el) {
        el = document.createElement("div"); el.id = "__cap";
        el.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:2147483647;padding:14px 16px;background:rgba(20,33,31,.94);color:#fff;font:700 19px/1.3 system-ui,sans-serif;text-align:center;min-height:62px;display:flex;align-items:center;justify-content:center;";
        (document.body || document.documentElement).appendChild(el);
      }
      el.textContent = t;
    };
  });
  const page = await context.newPage();
  const cap = (t) => page.evaluate((x) => window.__cap(x), t);
  const t0 = Date.now();
  const log = (m) => console.log(((Date.now() - t0) / 1000).toFixed(1) + "s", m);

  // 1. Hero
  await page.goto(WEB + "/"); await page.waitForLoadState("networkidle");
  await cap("Así se vería la página de tu consultorio"); log("hero");
  await sleep(5000);

  // 2. Servicios
  await page.locator("#servicios").scrollIntoViewIfNeeded().catch(() => {});
  await page.evaluate(() => document.querySelector("#servicios")?.scrollIntoView({ behavior: "smooth" }));
  await cap("Tus servicios, con precio y duración"); log("servicios");
  await sleep(6000);

  // 3. Agenda
  await page.evaluate(() => document.querySelector("#agendar")?.scrollIntoView({ behavior: "smooth" }));
  await cap("El paciente agenda solo: nombre y teléfono, sin datos de salud"); log("agenda");
  await sleep(1500);
  await page.locator("#days label").nth(1).click();
  await page.locator("#slots label").first().waitFor();
  await sleep(1200);
  await page.locator("#slots label").nth(3).click();
  await page.locator("input[name=name]").scrollIntoViewIfNeeded();
  await page.locator("input[name=name]").pressSequentially("Ana Pérez", { delay: 90 });
  await page.locator("input[name=phone]").pressSequentially("3312345678", { delay: 70 });
  await sleep(700);
  await page.locator("#book-submit").click();
  await page.locator("#confirm").waitFor({ state: "visible" });
  await page.evaluate(() => document.querySelector("#confirm")?.scrollIntoView({ block: "center", behavior: "smooth" }));
  await cap("¡Cita confirmada! Sin llamadas ni mensajes de ida y vuelta"); log("confirmada");
  await sleep(3500);

  // 4. Chat
  await page.locator("#chat-open").click();
  await cap("El asistente contesta a cualquier hora");  log("chat");
  await sleep(1200);
  const ask = async (q) => {
    await page.locator("#chat-input").pressSequentially(q, { delay: 55 });
    await page.keyboard.press("Enter");
    await page.waitForSelector(".msg.typing", { timeout: 6000 }).catch(() => {});
    await page.waitForSelector(".msg.typing", { state: "detached", timeout: 30000 }).catch(() => {});
    await sleep(2500);
  };
  await ask("¿Tienen estacionamiento?");
  await cap("Y no diagnostica: eso lo ve la doctora"); log("chat 2");
  await ask("Me duele una muela, ¿qué me tomo?");
  await sleep(1000);

  // 5. Recordatorio y vista de la doctora
  await page.goto(WEB + "/consultorio"); await page.waitForLoadState("networkidle");
  await cap("Tú ves tus citas del día"); log("doctora");
  await sleep(1200);
  await page.locator("#key-input").pressSequentially(KEY, { delay: 25 });
  await page.keyboard.press("Enter");
  await page.locator("#agenda-days label").nth(1).waitFor();
  await page.locator("#agenda-days label").nth(1).click();
  await page.locator(".appt", { hasText: "Ana Pérez" }).waitFor();
  await sleep(1800);
  await page.locator(".appt", { hasText: "Ana Pérez" }).click();
  await cap("Un día antes, el paciente recibe este recordatorio por WhatsApp"); log("recordatorio");
  await sleep(5500);

  // 6. Cierre
  await page.goto(WEB + "/"); await page.waitForLoadState("networkidle");
  await cap("Instalado en 7 a 10 días · $5,500 + $750 al mes · buestro.com"); log("cierre");
  await sleep(5000);

  const video = page.video();
  await context.close(); await browser.close();
  console.log("VIDEO " + (await video.path()));
})().catch((e) => { console.error("ERROR", e.message); process.exit(1); });
