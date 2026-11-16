import data from "../../data/consultorio.json";

export const site = data;

const money = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });
export const formatMoney = (n: number) => money.format(n);

export const whatsappUrl =
  `https://wa.me/${data.contact.whatsapp}?text=${encodeURIComponent(data.contact.whatsapp_message)}`;

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
export const rangesText = (ranges: string[][]) =>
  ranges.length ? ranges.map(([a, b]) => `${a}–${b}`).join(" y ") : "Cerrado";

// Groups consecutive days with the same hours: "Lunes a viernes: 10:00–14:00 y 16:00–20:00".
export function hoursSummary() {
  const groups: { days: string[]; text: string }[] = [];
  for (const h of data.hours) {
    const text = rangesText(h.ranges);
    const last = groups[groups.length - 1];
    if (last && last.text === text) last.days.push(h.day);
    else groups.push({ days: [h.day], text });
  }
  return groups.map((g) => ({
    label: g.days.length > 1 ? `${cap(g.days[0])} a ${g.days[g.days.length - 1]}` : cap(g.days[0]),
    text: g.text,
  }));
}

export const durationText = (min: number) => (min >= 60 && min % 60 === 0 ? `${min / 60} h` : `${min} min`);
