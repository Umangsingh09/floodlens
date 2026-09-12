type IconProps = { className?: string };

const common = {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

export function SatelliteIcon({ className }: IconProps) {
  return (
    <svg {...common} className={className} aria-hidden="true">
      <path d="M13 7l4 4-1.5 1.5a3 3 0 0 1-4.24 0L9.5 10.74a3 3 0 0 1 0-4.24L11 5l2 2z" />
      <path d="M8.5 12.5L3 18M15.5 5.5L18 3M5 21l1.5-1.5M18.5 9.5L21 7" />
    </svg>
  );
}

export function ClockIcon({ className }: IconProps) {
  return (
    <svg {...common} className={className} aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}

export function GridIcon({ className }: IconProps) {
  return (
    <svg {...common} className={className} aria-hidden="true">
      <rect x="3" y="3" width="7" height="7" rx="1.2" />
      <rect x="14" y="3" width="7" height="7" rx="1.2" />
      <rect x="3" y="14" width="7" height="7" rx="1.2" />
      <rect x="14" y="14" width="7" height="7" rx="1.2" />
    </svg>
  );
}

export function ChipIcon({ className }: IconProps) {
  return (
    <svg {...common} className={className} aria-hidden="true">
      <rect x="7" y="7" width="10" height="10" rx="1.5" />
      <path d="M9 3v3M15 3v3M9 18v3M15 18v3M3 9h3M3 15h3M18 9h3M18 15h3" />
    </svg>
  );
}

export function TrendIcon({ className }: IconProps) {
  return (
    <svg {...common} className={className} aria-hidden="true">
      <path d="M3 16l5-5 4 4 8-9" />
      <path d="M15 6h5v5" />
    </svg>
  );
}

export function ShieldIcon({ className }: IconProps) {
  return (
    <svg {...common} className={className} aria-hidden="true">
      <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z" />
    </svg>
  );
}
