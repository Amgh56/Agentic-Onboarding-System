const props = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round",
  strokeLinejoin: "round",
} as const;

export function OverviewIcon() {
  return (
    <svg {...props}>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </svg>
  );
}

export function JobsIcon() {
  return (
    <svg {...props}>
      <rect x="3" y="7" width="18" height="13" rx="2" />
      <path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2" />
      <path d="M3 13h18" />
    </svg>
  );
}

export function ChevronDownIcon() {
  return (
    <svg {...props} width={16} height={16}>
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

export function PlusIcon() {
  return (
    <svg {...props} width={16} height={16} strokeWidth={2.2}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function ChevronRightIcon() {
  return (
    <svg {...props} width={16} height={16} className="chevron-forward">
      <path d="m9 6 6 6-6 6" />
    </svg>
  );
}

export function ChevronLeftIcon() {
  return (
    <svg {...props} width={16} height={16} className="chevron-forward">
      <path d="m15 6-6 6 6 6" />
    </svg>
  );
}

export function UploadIcon() {
  return (
    <svg {...props} width={16} height={16}>
      <path d="M12 16V4M7 9l5-5 5 5M5 20h14" />
    </svg>
  );
}


export function CheckIcon() {
  return (
    <svg {...props} width={14} height={14} strokeWidth={3}>
      <path d="m5 12 5 5 9-10" />
    </svg>
  );
}

export function ClockIcon() {
  return (
    <svg {...props} width={14} height={14} strokeWidth={2.4}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}
