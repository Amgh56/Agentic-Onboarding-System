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

export function PenIcon() {
  return (
    <svg {...props}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  );
}

export function DashboardIcon() {
  return (
    <svg {...props}>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </svg>
  );
}

export function MessagesIcon() {
  return (
    <svg {...props}>
      <path d="M21 11.5a8.4 8.4 0 0 1-12.2 7.5L3 20.5l1.6-4.9A8.4 8.4 0 1 1 21 11.5Z" />
    </svg>
  );
}

export function ApplicationsIcon() {
  return (
    <svg {...props}>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z" />
      <path d="M14 3v5h5M9 13h6M9 17h6" />
    </svg>
  );
}

export function OnboardingIcon() {
  return (
    <svg {...props}>
      <rect x="5" y="4" width="14" height="17" rx="2" />
      <path d="M9 4V3h6v1M9 13l2 2 4-4" />
    </svg>
  );
}

export function EmployeesIcon() {
  return (
    <svg {...props}>
      <circle cx="9" cy="8" r="3.2" />
      <path d="M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5M16 5a3 3 0 0 1 0 6M18 14.8c1.8.7 3 2.4 3 5.2" />
    </svg>
  );
}

export function ChartIcon() {
  return (
    <svg {...props}>
      <path d="M3 3v18h18" />
      <path d="m7 15 4-4 3 3 5-6" />
    </svg>
  );
}

export function GearIcon() {
  return (
    <svg {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z" />
    </svg>
  );
}

export function BellIcon() {
  return (
    <svg {...props}>
      <path d="M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8Z" />
      <path d="M10.3 21a1.9 1.9 0 0 0 3.4 0" />
    </svg>
  );
}

export function SparkleIcon() {
  return (
    <svg {...props} width={14} height={14}>
      <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8ZM19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8Z" />
    </svg>
  );
}
