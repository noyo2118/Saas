export type Severity = "critical" | "high" | "medium" | "low" | "info";

export const KPI_STATS = [
  { label: "Threats blocked", value: 18234902, suffix: "+" },
  { label: "Scans / day", value: 1240000, suffix: "+" },
  { label: "Detection accuracy", value: 99.7, suffix: "%" },
  { label: "Avg detection", value: 312, suffix: "ms" },
];

export const FEATURES = [
  { title: "AI Threat Detection", desc: "Multi-model neural ensemble flags zero-day attacks within milliseconds.", icon: "Brain" },
  { title: "Phishing Intelligence", desc: "Live URL fingerprinting against 4.2B malicious indicators.", icon: "Fish" },
  { title: "IP Reputation", desc: "ASN, geo, abuse history and botnet correlation in one query.", icon: "Globe2" },
  { title: "SSL & Certificate", desc: "Deep TLS inspection, chain validation, expiry & weak-cipher alerts.", icon: "Lock" },
  { title: "Blacklist Matrix", desc: "Cross-checked against 80+ commercial and public threat feeds.", icon: "Shield" },
  { title: "WHOIS Forensics", desc: "Registrar history, ownership signals and domain age scoring.", icon: "FileSearch" },
];

export const ACTIVITY: { time: string; type: string; target: string; severity: Severity }[] = [
  { time: "now",   type: "Phishing kit detected", target: "secure-paypa1-login.io",  severity: "critical" },
  { time: "1s",    type: "Malicious redirect",    target: "203.0.113.41",            severity: "high" },
  { time: "3s",    type: "C2 beacon pattern",     target: "cdn-update-host.ru",      severity: "critical" },
  { time: "7s",    type: "Suspicious WHOIS",      target: "free-crypto-airdrop.app", severity: "medium" },
  { time: "11s",   type: "Expired TLS certificate",target: "api.legacy-bank.co",     severity: "low" },
  { time: "16s",   type: "Botnet correlation",    target: "198.51.100.77",           severity: "high" },
  { time: "22s",   type: "Typo-squat domain",     target: "rnicrosoft-support.com",  severity: "medium" },
  { time: "29s",   type: "Reputation drop",       target: "ads-tracker-cdn.net",     severity: "info" },
];

export const TERMINAL_LINES = [
  "$ trustscan init --target acme-secure-portal.io",
  "[+] resolving DNS records ........................ ok",
  "[+] enumerating subdomains (217 found) ........... ok",
  "[+] tls handshake / cipher suites ................ ok",
  "[+] whois lookup .................................. ok",
  "[+] cross-referencing 84 threat feeds ............. ok",
  "[!] phishing kit signature match: evilginx2/4.0",
  "[!] suspicious form action -> http://203.0.113.41/c",
  "[+] passing context to gpt-trust-v4 ............... ok",
  "[+] generating intelligence report ................ ok",
  "$ verdict: HIGH RISK   trust score: 24/100",
];

export const THREAT_SERIES = Array.from({ length: 28 }, (_, i) => ({
  t: i,
  threats: Math.round(800 + Math.sin(i / 2.2) * 220 + Math.random() * 180),
  blocked: Math.round(700 + Math.sin(i / 2.2 + 0.5) * 200 + Math.random() * 140),
}));

export const RISK_BREAKDOWN = [
  { label: "Phishing",    value: 38 },
  { label: "Malware",     value: 27 },
  { label: "Botnet C2",   value: 18 },
  { label: "Spam",        value: 11 },
  { label: "Other",       value: 6 },
];

export const REGIONS = [
  { name: "North America", x: 22, y: 38, value: 412 },
  { name: "South America", x: 32, y: 68, value: 184 },
  { name: "Europe",        x: 52, y: 34, value: 538 },
  { name: "Africa",        x: 54, y: 60, value: 162 },
  { name: "Middle East",   x: 60, y: 44, value: 248 },
  { name: "Asia",          x: 74, y: 42, value: 612 },
  { name: "Oceania",       x: 84, y: 72, value: 96 },
];

export const PRICING = [
  {
    name: "Recon",
    price: 0,
    blurb: "For researchers and curious minds.",
    features: ["100 scans / day", "Basic AI verdict", "Community feeds", "URL & IP lookup"],
    cta: "Start free",
  },
  {
    name: "Sentinel",
    price: 49,
    blurb: "For security teams running active monitoring.",
    features: ["Unlimited scans", "Full AI explanation", "80+ premium feeds", "Webhook & API", "Threat dashboards", "Priority support"],
    cta: "Deploy Sentinel",
    featured: true,
  },
  {
    name: "Enterprise",
    price: null,
    blurb: "For governments, banks and global SOCs.",
    features: ["Dedicated tenant", "On-prem option", "SAML / SCIM", "Custom feeds & models", "24/7 incident response", "99.99% SLA"],
    cta: "Contact sales",
  },
];

export const TESTIMONIALS = [
  { quote: "TrustScan replaced three vendors in our SOC stack overnight.", name: "Maya Okafor", role: "CISO, Halcyon Bank" },
  { quote: "The AI explanations are the most lucid I've ever read in this space.", name: "Dr. Liu Wen", role: "Threat Researcher, ENISA" },
  { quote: "We catch phishing kits hours before our previous platform.", name: "Jonas Reiter", role: "Head of SecOps, Vertex Labs" },
];

export const RECENT_SCANS = [
  { target: "acme-secure-portal.io",      score: 24, verdict: "High risk",  type: "URL" },
  { target: "203.0.113.41",               score: 11, verdict: "Critical",   type: "IP" },
  { target: "cdn.assets.northwind.com",   score: 96, verdict: "Trusted",    type: "URL" },
  { target: "rnicrosoft-support.com",     score: 38, verdict: "Suspicious", type: "URL" },
  { target: "198.51.100.77",              score: 19, verdict: "Critical",   type: "IP" },
  { target: "api.payments.stripe.com",    score: 99, verdict: "Trusted",    type: "URL" },
];
