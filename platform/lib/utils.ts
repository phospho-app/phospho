import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
 
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
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

export const countObjectsPerDay = (data: Session[]): Record<string, number>  => {
  return data.reduce((counts, item) => {
    // Convert the Unix timestamp to a date string in 'YYYY-MM-DD' format
    const date = new Date(Number(item.created_at) * 1000).toISOString().split("T")[0];

    // Initialize or increment the count for each day
    counts[date] = (counts[date] || 0) + 1;

    return counts;
  }, {} as Record<string, number>);
};

// Non exaustive list of languages
export function getLanguageLabel(isoCode: string): string {
  const languageMap: Record<string, string> = {
    en: "English",
    fr: "French",
    es: "Spanish",
    sw: "Swahili",
    id: "Indonesian",
    ar: "Arabic",
    pt: "Portuguese",
    ru: "Russian",
    "zh-cn": "Chinese",
    "zh-tw": "Chinese",
    de: "German",
    it: "Italian",
    ja: "Japanese",
    ko: "Korean",
    nl: "Dutch",
    pl: "Polish",
    tr: "Turkish",
    vi: "Vietnamese",
    hi: "Hindi",
    bn: "Bengali",
    fa: "Persian",
    ur: "Urdu",
    th: "Thai",
    he: "Hebrew",
    el: "Greek",
    hu: "Hungarian",
    cs: "Czech",
    fi: "Finnish",
    sv: "Swedish",
    da: "Danish",
    no: "Norwegian",
    is: "Icelandic",
    ga: "Irish",
    lv: "Latvian",
    lt: "Lithuanian",
    et: "Estonian",
    mt: "Maltese",
    hr: "Croatian",
    sk: "Slovak",
    sl: "Slovenian",
    ro: "Romanian",
    bg: "Bulgarian",
    uk: "Ukrainian",
    mk: "Macedonian",
    sq: "Albanian",
    hy: "Armenian", 
    ka: "Georgian",
    az: "Azerbaijani",
    kk: "Kazakh",
    uz: "Uzbek",
    ky: "Kyrgyz",
    tk: "Turkmen",
    tg: "Tajik",
    mn: "Mongolian",
    ps: "Pashto",
    ks: "Kashmiri",
    sd: "Sindhi",
    ne: "Nepali",
    pa: "Punjabi",
    gu: "Gujarati",
    or: "Oriya",
    ta: "Tamil",
    te: "Telugu",
    kn: "Kannada",
    ml: "Malayalam",
    si: "Sinhala",
    lo: "Lao",
    my: "Burmese",
    km: "Khmer",
    ms: "Malay",
    tl: "Tagalog",
    jv: "Javanese",
    su: "Sundanese",
    mad: "Madurese",
    bug: "Buginese",
    ace: "Acehnese",
    tet: "Tetum",
    haw: "Hawaiian",
    to: "Tongan",
    sm: "Samoan",
    mi: "Maori",
    fij: "Fijian",
    tah: "Tahitian",
    ch: "Chamorro",
  };

  return languageMap[isoCode.toLowerCase()] || "Unknown";
}