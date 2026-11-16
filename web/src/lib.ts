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
    days: g.days,
  }));
}

export const durationText = (min: number) => (min >= 60 && min % 60 === 0 ? `${min / 60} h` : `${min} min`);

// Simple stroke icons (24x24 viewBox) per service id.
export const serviceIcons: Record<string, string> = {
  assessment: '<circle cx="11" cy="11" r="6"/><path d="m20 20-4.200-4.200"/>',
  cleaning: '<path d="M12 3l1.800 5.200L19 10l-5.200 1.800L12 17l-1.800-5.200L5 10l5.200-1.800z"/><path d="M19 17v4M17 19h4"/>',
  filling: '<path d="M7 3c-2 0-4 1.500-4 4.500 0 2 1 3 1.500 5.500.4 2 .5 8 2.500 8 1.800 0 1.500-5 3-5s1.200 5 3 5c2 0 2.100-6 2.500-8 .5-2.500 1.500-3.500 1.500-5.500C20 4.500 18 3 16 3c-1.500 0-2.200.8-4 .8S8.500 3 7 3z"/>',
  extraction: '<path d="M7 3c-2 0-4 1.500-4 4.500 0 2 1 3 1.500 5.500.4 2 .5 8 2.500 8 1.800 0 1.500-5 3-5s1.200 5 3 5c2 0 2.100-6 2.500-8 .5-2.500 1.500-3.500 1.500-5.500C20 4.500 18 3 16 3c-1.500 0-2.200.8-4 .8S8.500 3 7 3z"/><path d="M9 9h6"/>',
  whitening: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.900 4.900l1.400 1.400M17.700 17.700l1.400 1.400M2 12h2M20 12h2M4.900 19.100l1.400-1.400M17.700 6.300l1.400-1.400"/>',
  urgent: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
};

export const stepIcons = [
  '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M8 3v4M16 3v4M3 10h18"/>',
  '<circle cx="11" cy="11" r="6"/><path d="m20 20-4.200-4.200"/>',
  '<path d="M20 6 9 17l-5-5"/>',
];

export const trustIcons = [
  '<path d="M20 6 9 17l-5-5"/>',
  '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M8 3v4M16 3v4M3 10h18"/>',
  '<path d="M21 12a8 8 0 0 1-11.600 7.100L4 20l1-4.600A8 8 0 1 1 21 12z"/>',
  '<path d="M12 3 5 6v5c0 4.500 3 8 7 10 4-2 7-5.500 7-10V6z"/>',
];
