import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Session {
  id: string;
  created_at: string;
  version_id: string;
  project_id: string;
  metadata: {
    flag: string;
    score: string;
    rating: string;
  };
  data: {};
}

export const countObjectsPerDay = (data: Session[]): Record<string, number> => {
  return data.reduce(
    (counts, item) => {
      // Convert the Unix timestamp to a date string in 'YYYY-MM-DD' format
      const date = new Date(Number(item.created_at) * 1000)
        .toISOString()
        .split("T")[0];

      // Initialize or increment the count for each day
      counts[date] = (counts[date] || 0) + 1;

      return counts;
    },
    {} as Record<string, number>,
  );
};

export const graphColors = [
  "#22c55e",
  "#ff7c7c",
  "#ffbb43",
  "#4a90e2",
  "#a259ff",
  "#FFDE82",
  "#CBA74E",
  "#917319",
  "#E2E3D8",
  "#68EDCB",
  "#00C4FF",
  "#9FAFA1",
  "#EB6D00",
  "#D3D663",
  "#92CF56",
  "#FA003C",
  "#9FA8DF",
  "#005400",
  "#505C8D",
];

// list of 55 languages supported by langdetect
export function getLanguageLabel(isoCode: string | null): string {
  const languageMap: Record<string, string> = {
    af: "Afrikaans",
    ar: "Arabic",
    bg: "Bulgarian",
    bn: "Bengali",
    ca: "Catalan",
    cs: "Czech",
    cy: "Welsh",
    da: "Danish",
    de: "German",
    el: "Greek",
    en: "English",
    es: "Spanish",
    et: "Estonian",
    fa: "Persian",
    fi: "Finnish",
    fr: "French",
    gu: "Gujarati",
    he: "Hebrew",
    hi: "Hindi",
    hr: "Croatian",
    hu: "Hungarian",
    id: "Indonesian",
    it: "Italian",
    ja: "Japanese",
    kn: "Kannada",
    ko: "Korean",
    lt: "Lithuanian",
    lv: "Latvian",
    mk: "Macedonian",
    ml: "Malayalam",
    mr: "Marathi",
    ne: "Nepali",
    nl: "Dutch",
    no: "Norwegian",
    pa: "Punjabi",
    pl: "Polish",
    pt: "Portuguese",
    ro: "Romanian",
    ru: "Russian",
    sk: "Slovak",
    sl: "Slovenian",
    so: "Somali",
    sq: "Albanian",
    sr: "Serbian",
    sv: "Swedish",
    sw: "Swahili",
    ta: "Tamil",
    te: "Telugu",
    th: "Thai",
    tl: "Tagalog",
    tr: "Turkish",
    uk: "Ukrainian",
    ur: "Urdu",
    vi: "Vietnamese",
    "zh-cn": "Chinese (Simplified)",
    "zh-latn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
  };
  if (!isoCode) {
    return "Unknown";
  }
  return languageMap[isoCode.toLowerCase()] || "Unknown";
}

export function generateSlug() {
  // Generate a random slug

  function getRandomItem<T>(array: T[]): T {
    return array[Math.floor(Math.random() * array.length)];
  }

  function getCompactDate() {
    const date = new Date();
    const year = date.getFullYear().toString();
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const day = date.getDate().toString().padStart(2, "0");
    return `${year}${month}${day}`;
  }

  const colors = [
    "blue",
    "green",
    "red",
    "neon",
    "azure",
    "emerald",
    "sapphire",
    "amber",
    "violet",
    "coral",
    "indigo",
    "teal",
    "scarlet",
    "jade",
    "slate",
    "ivory",
    "ruby",
    "gold",
    "silver",
    "bronze",
    "copper",
    "platinum",
    "pearl",
    "diamond",
    "topaz",
    "opal",
    "anthracite",
    "magenta",
    "turquoise",
    "lavender",
    "rose",
  ];

  const fruits = [
    "mango",
    "kiwi",
    "pineapple",
    "dragonfruit",
    "papaya",
    "lychee",
    "pomegranate",
    "guava",
    "fig",
    "passionfruit",
    "starfruit",
    "coconut",
    "jackfruit",
    "banana",
    "apple",
    "orange",
    "grapefruit",
    "lemon",
    "lime",
    "strawberry",
    "soursop",
    "beaujaulais",
    "cantaloupe",
    "watermelon",
    "honeydew",
    "cucumber",
    "tomato",
    "potato",
    "carrot",
    "beet",
  ];

  const color = getRandomItem(colors);
  const fruit = getRandomItem(fruits);
  const date = getCompactDate();
  return `${date}-${color}-${fruit}`;
}
