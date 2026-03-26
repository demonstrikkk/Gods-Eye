import { divIcon } from 'leaflet';

export type VisualKey =
  | 'country'
  | 'economics'
  | 'governance'
  | 'climate'
  | 'defense'
  | 'conflict'
  | 'infrastructure'
  | 'mobility'
  | 'cyber'
  | 'news';

export type MarkerInput = {
  type?: string;
  layer?: string;
  category?: string;
  [key: string]: unknown;
};

export interface CategoryStyle {
  fill: string;
  accent: string;
  glow: string;
}

export type KeywordMap = Record<string, VisualKey>;

export interface MarkerConfig {
  baseSize?: number;
  countryBaseSize?: number;
  selectedSizeIncrement?: number;
  sizeScaleFactor?: number;
  selectionRingStyle?: string;
  glowEnabled?: boolean;
  keywordMap?: KeywordMap;
  paletteOverrides?: Partial<Record<VisualKey, Partial<CategoryStyle>>>;
  svgOverrides?: Partial<Record<VisualKey, (fill: string, accent: string) => string>>;
}

const defaultPalette: Record<VisualKey, CategoryStyle> = {
  country: { fill: '#38bdf8', accent: '#e0f2fe', glow: 'rgba(56,189,248,0.45)' },
  economics: { fill: '#10b981', accent: '#d1fae5', glow: 'rgba(16,185,129,0.42)' },
  governance: { fill: '#84cc16', accent: '#ecfccb', glow: 'rgba(132,204,22,0.42)' },
  climate: { fill: '#f59e0b', accent: '#fef3c7', glow: 'rgba(245,158,11,0.42)' },
  defense: { fill: '#ef4444', accent: '#fee2e2', glow: 'rgba(239,68,68,0.44)' },
  conflict: { fill: '#fb7185', accent: '#ffe4e6', glow: 'rgba(251,113,133,0.44)' },
  infrastructure: { fill: '#14b8a6', accent: '#ccfbf1', glow: 'rgba(20,184,166,0.42)' },
  mobility: { fill: '#d946ef', accent: '#fae8ff', glow: 'rgba(217,70,239,0.44)' },
  cyber: { fill: '#60a5fa', accent: '#dbeafe', glow: 'rgba(96,165,250,0.44)' },
  news: { fill: '#22d3ee', accent: '#cffafe', glow: 'rgba(34,211,238,0.42)' },
};

const defaultKeywordMap: KeywordMap = {
  economic: 'economics',
  govern: 'governance',
  climate: 'climate',
  defense: 'defense',
  conflict: 'conflict',
  geopolitic: 'conflict',
  infrastructure: 'infrastructure',
  mobility: 'mobility',
  aviation: 'mobility',
  cyber: 'cyber',
  news: 'news',
};

const defaultSvgTemplates: Record<VisualKey, (fill: string, accent: string) => string> = {
  country: (fill, accent) => `
    <svg viewBox="0 0 32 32" role="img" aria-label="country marker">
      <path d="M16 3 L28 16 L16 29 L4 16 Z" fill="${fill}" stroke="${accent}" stroke-width="1.8" />
      <circle cx="16" cy="16" r="4.4" fill="${accent}" opacity="0.95" />
    </svg>
  `,
  economics: (fill, accent) => `
    <svg viewBox="0 0 32 32" role="img" aria-label="economics marker">
      <rect x="4" y="4" width="24" height="24" rx="7" fill="${fill}" stroke="${accent}" stroke-width="1.6" />
      <rect x="8" y="17" width="3.4" height="7" rx="1" fill="${accent}" />
      <rect x="14.3" y="12" width="3.4" height="12" rx="1" fill="${accent}" />
      <rect x="20.6" y="8.5" width="3.4" height="15.5" rx="1" fill="${accent}" />
    </svg>
  `,
  governance: (fill, accent) => `
    <svg viewBox="0 0 32 32" role="img" aria-label="governance marker">
      <path d="M5 12 L16 5 L27 12" fill="none" stroke="${accent}" stroke-width="2" stroke-linecap="round" />
      <rect x="6.5" y="12" width="19" height="2.2" rx="1" fill="${fill}" />
      <rect x="9" y="14.5" width="2.8" height="8.5" rx="1" fill="${accent}" />
      <rect x="14.6" y="14.5" width="2.8" height="8.5" rx="1" fill="${accent}" />
      <rect x="20.2" y="14.5" width="2.8" height="8.5" rx="1" fill="${accent}" />
      <rect x="6" y="23.5" width="20" height="2.5" rx="1.2" fill="${fill}" />
    </svg>
  `,
  climate: (fill, accent) => `
    <svg viewBox="0 0 32 32" role="img" aria-label="climate marker">
      <circle cx="16" cy="16" r="5.6" fill="${fill}" stroke="${accent}" stroke-width="1.6" />
      <g stroke="${accent}" stroke-width="2" stroke-linecap="round">
        <path d="M16 4.5 V8.2" />
        <path d="M16 23.8 V27.5" />
        <path d="M4.5 16 H8.2" />
        <path d="M23.8 16 H27.5" />
        <path d="M7.7 7.7 L10.4 10.4" />
        <path d="M21.6 21.6 L24.3 24.3" />
        <path d="M21.6 10.4 L24.3 7.7" />
        <path d="M7.7 24.3 L10.4 21.6" />
      </g>
    </svg>
  `,
  defense: (fill, accent) => `
    <svg viewBox="0 0 32 32" role="img" aria-label="defense marker">
      <path d="M16 4 L25 7.6 V14.8 C25 20.8 21.1 25.8 16 28 C10.9 25.8 7 20.8 7 14.8 V7.6 Z" fill="${fill}" stroke="${accent}" stroke-width="1.8" />
      <path d="M16 10 V21" stroke="${accent}" stroke-width="2.1" stroke-linecap="round" />
      <path d="M11.7 15.2 H20.3" stroke="${accent}" stroke-width="2.1" stroke-linecap="round" />
    </svg>
  `,
  conflict: (fill, accent) => `
    <svg viewBox="0 0 32 32" role="img" aria-label="conflict marker">
      <path d="M16 3.5 L19.2 12.8 L28.5 16 L19.2 19.2 L16 28.5 L12.8 19.2 L3.5 16 L12.8 12.8 Z" fill="${fill}" stroke="${accent}" stroke-width="1.6" />
      <path d="M10 10 L22 22" stroke="${accent}" stroke-width="2" stroke-linecap="round" />
      <path d="M22 10 L10 22" stroke="${accent}" stroke-width="2" stroke-linecap="round" />
    </svg>
  `,
  infrastructure: (fill, accent) => `
    <svg viewBox="0 0 32 32" role="img" aria-label="infrastructure marker">
      <rect x="6" y="6" width="20" height="20" rx="4" fill="${fill}" stroke="${accent}" stroke-width="1.6" />
      <path d="M10 10 H22 V22 H10 Z" fill="none" stroke="${accent}" stroke-width="1.8" stroke-dasharray="2.4 1.6" />
      <path d="M16 10 V22 M10 16 H22" stroke="${accent}" stroke-width="1.6" />
    </svg>
  `,
  mobility: (fill, accent) => `
    <svg viewBox="0 0 32 32" role="img" aria-label="mobility marker">
      <path d="M5 20 C10 11, 17 9, 27 12" fill="none" stroke="${accent}" stroke-width="2" stroke-linecap="round" />
      <path d="M19 10 L27 12 L22.4 18.2" fill="${fill}" stroke="${accent}" stroke-width="1.4" stroke-linejoin="round" />
      <circle cx="8" cy="21.5" r="2.6" fill="${fill}" stroke="${accent}" stroke-width="1.4" />
    </svg>
  `,
  cyber: (fill, accent) => `
    <svg viewBox="0 0 32 32" role="img" aria-label="cyber marker">
      <path d="M10 5 H22 L27 10 V22 L22 27 H10 L5 22 V10 Z" fill="${fill}" stroke="${accent}" stroke-width="1.6" />
      <path d="M11 16 H21" stroke="${accent}" stroke-width="1.8" stroke-linecap="round" />
      <path d="M13 11 V21" stroke="${accent}" stroke-width="1.5" stroke-linecap="round" />
      <circle cx="21.5" cy="11.5" r="1.6" fill="${accent}" />
      <circle cx="18.5" cy="20.5" r="1.6" fill="${accent}" />
    </svg>
  `,
  news: (fill, accent) => `
    <svg viewBox="0 0 32 32" role="img" aria-label="news marker">
      <rect x="5" y="7" width="22" height="18" rx="5" fill="${fill}" stroke="${accent}" stroke-width="1.6" />
      <path d="M10 14.5 H22" stroke="${accent}" stroke-width="2" stroke-linecap="round" />
      <path d="M10 19 H18" stroke="${accent}" stroke-width="2" stroke-linecap="round" />
      <circle cx="21.5" cy="19" r="2" fill="${accent}" />
    </svg>
  `,
};

export class SvgMarkerFactory {
  private config: Required<MarkerConfig>;
  private palette: Record<VisualKey, CategoryStyle>;
  private svgTemplates: Record<VisualKey, (fill: string, accent: string) => string>;
  private keywordMap: KeywordMap;
  private htmlCache = new Map<string, string>();
  private iconCache = new Map<string, ReturnType<typeof divIcon>>();

  constructor(config: MarkerConfig = {}) {
    this.config = {
      baseSize: config.baseSize ?? 30,
      countryBaseSize: config.countryBaseSize ?? 34,
      selectedSizeIncrement: config.selectedSizeIncrement ?? 6,
      sizeScaleFactor: config.sizeScaleFactor ?? 1,
      selectionRingStyle: config.selectionRingStyle ?? '',
      glowEnabled: config.glowEnabled ?? true,
      keywordMap: config.keywordMap ?? { ...defaultKeywordMap },
      paletteOverrides: config.paletteOverrides ?? {},
      svgOverrides: config.svgOverrides ?? {},
    };

    this.palette = { ...defaultPalette };
    for (const [key, overrides] of Object.entries(this.config.paletteOverrides)) {
      const visualKey = key as VisualKey;
      if (overrides && this.palette[visualKey]) {
        this.palette[visualKey] = { ...this.palette[visualKey], ...overrides };
      }
    }

    this.svgTemplates = { ...defaultSvgTemplates };
    for (const [key, templateFn] of Object.entries(this.config.svgOverrides)) {
      const visualKey = key as VisualKey;
      if (templateFn && this.svgTemplates[visualKey]) {
        this.svgTemplates[visualKey] = templateFn;
      }
    }

    this.keywordMap = Object.fromEntries(
      Object.entries(this.config.keywordMap).map(([keyword, visual]) => [keyword.toLowerCase(), visual]),
    );
  }

  public getMarkerVisual(item: MarkerInput): VisualKey {
    if (item.type === 'country') return 'country';

    const value = String(item.layer || item.category || item.type || '').toLowerCase();
    for (const [keyword, visual] of Object.entries(this.keywordMap)) {
      if (value.includes(keyword)) return visual;
    }

    return 'news';
  }

  public getMarkerSize(visual: VisualKey, selected: boolean): number {
    const base = visual === 'country' ? this.config.countryBaseSize : this.config.baseSize;
    const rawSize = selected ? base + this.config.selectedSizeIncrement : base;
    return Math.round(rawSize * this.config.sizeScaleFactor);
  }

  public getMarkerHtml(item: MarkerInput, selected = false): string {
    const visual = this.getMarkerVisual(item);
    const colors = this.palette[visual];
    const size = this.getMarkerSize(visual, selected);
    const cacheKey = `${visual}|${selected}|${size}`;

    if (this.htmlCache.has(cacheKey)) {
      return this.htmlCache.get(cacheKey)!;
    }

    const svg = this.svgTemplates[visual](colors.fill, colors.accent);
    const glowStyle = this.config.glowEnabled ? `filter: drop-shadow(0 0 10px ${colors.glow});` : '';
    const selectionHtml = selected
      ? `<span style="position:absolute;inset:-4px;border:1.6px solid ${colors.fill};border-radius:999px;box-shadow:0 0 14px ${colors.glow};${this.config.selectionRingStyle}"></span>`
      : '';

    const html = `
      <div style="
        position: relative;
        width: ${size}px;
        height: ${size}px;
        display: grid;
        place-items: center;
        border: 0;
        background: transparent;
        ${glowStyle}
        pointer-events: auto;
      ">
        ${selectionHtml}
        ${svg}
      </div>
    `;

    this.htmlCache.set(cacheKey, html);
    return html;
  }

  public createLeafletMarkerIcon(item: MarkerInput, selected = false): ReturnType<typeof divIcon> {
    const visual = this.getMarkerVisual(item);
    const size = this.getMarkerSize(visual, selected);
    const cacheKey = `${visual}|${selected}|${size}`;

    if (this.iconCache.has(cacheKey)) {
      return this.iconCache.get(cacheKey)!;
    }

    const icon = divIcon({
      className: 'map-svg-icon',
      html: this.getMarkerHtml(item, selected),
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
      popupAnchor: [0, -(size / 2)],
    });

    this.iconCache.set(cacheKey, icon);
    return icon;
  }

  public clearCache(): void {
    this.htmlCache.clear();
    this.iconCache.clear();
  }

  public updateConfig(config: Partial<MarkerConfig>): void {
    this.config = {
      ...this.config,
      ...config,
      keywordMap: config.keywordMap ?? this.config.keywordMap,
      paletteOverrides: config.paletteOverrides ?? this.config.paletteOverrides,
      svgOverrides: config.svgOverrides ?? this.config.svgOverrides,
    };
    this.clearCache();
  }
}

const defaultFactory = new SvgMarkerFactory();

export const getMarkerVisual = (item: MarkerInput): VisualKey => defaultFactory.getMarkerVisual(item);
export const getMarkerHtml = (item: MarkerInput, selected = false): string => defaultFactory.getMarkerHtml(item, selected);
export const createLeafletMarkerIcon = (item: MarkerInput, selected = false) => defaultFactory.createLeafletMarkerIcon(item, selected);
export { defaultFactory as markerFactory };

export const createHighlightMarkerIcon = (
  item: MarkerInput,
  highlightColor: string = '#3b82f6',
  pulseEnabled: boolean = true,
) => {
  const visual = defaultFactory.getMarkerVisual(item);
  const size = defaultFactory.getMarkerSize(visual, true) + 8;
  const colors = defaultPalette[visual];

  const pulseAnimation = pulseEnabled
    ? `
      @keyframes ai-pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.15); opacity: 0.7; }
      }
    `
    : '';

  const pulseStyle = pulseEnabled ? 'animation: ai-pulse 2s ease-in-out infinite;' : '';
  const svg = defaultSvgTemplates[visual](colors.fill, colors.accent);

  const html = `
    <style>${pulseAnimation}</style>
    <div style="
      position: relative;
      width: ${size}px;
      height: ${size}px;
      display: grid;
      place-items: center;
      ${pulseStyle}
    ">
      <span style="
        position: absolute;
        inset: -6px;
        border: 2.5px solid ${highlightColor};
        border-radius: 999px;
        box-shadow: 0 0 20px ${highlightColor}, 0 0 40px ${highlightColor}40;
        background: ${highlightColor}15;
      "></span>
      <div style="
        width: ${size - 8}px;
        height: ${size - 8}px;
        filter: drop-shadow(0 0 12px ${highlightColor});
      ">
        ${svg}
      </div>
    </div>
  `;

  return divIcon({
    className: 'ai-highlight-marker',
    html,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -(size / 2)],
  });
};

export const createRiskMarkerIcon = (riskScore: number, _countryName: string) => {
  const size = 40;

  let bgColor: string;
  let glowColor: string;
  if (riskScore >= 0.7) {
    bgColor = '#ef4444';
    glowColor = 'rgba(239, 68, 68, 0.6)';
  } else if (riskScore >= 0.4) {
    bgColor = '#f59e0b';
    glowColor = 'rgba(245, 158, 11, 0.6)';
  } else {
    bgColor = '#10b981';
    glowColor = 'rgba(16, 185, 129, 0.6)';
  }

  const html = `
    <div style="
      position: relative;
      width: ${size}px;
      height: ${size}px;
      display: flex;
      align-items: center;
      justify-content: center;
    ">
      <div style="
        width: ${size - 8}px;
        height: ${size - 8}px;
        border-radius: 50%;
        background: ${bgColor};
        box-shadow: 0 0 15px ${glowColor}, 0 0 30px ${glowColor};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        font-weight: bold;
        color: white;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
      ">
        ${Math.round(riskScore * 100)}
      </div>
    </div>
  `;

  return divIcon({
    className: 'risk-marker',
    html,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -(size / 2)],
  });
};
