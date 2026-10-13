import type { ResourceType } from "@/lib/content";

export function TypeIcon({ type }: { type: ResourceType }) {
  const common = {
    "aria-hidden": true,
    fill: "none",
    stroke: "currentColor",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    strokeWidth: 1.8,
    viewBox: "0 0 24 24",
  };

  switch (type) {
    case "Article":
      return (
        <svg {...common}>
          <path d="M5 4.5h14v15H5z" />
          <path d="M8 8h8M8 11.5h8M8 15h5" />
        </svg>
      );
    case "Video":
      return (
        <svg {...common}>
          <rect x="4" y="5" width="16" height="14" rx="2" />
          <path d="m10 9 5 3-5 3z" />
        </svg>
      );
    case "Course":
      return (
        <svg {...common}>
          <path d="m4 8 8-4 8 4-8 4-8-4Z" />
          <path d="M7 10v5c2.8 2 7.2 2 10 0v-5M20 8v5" />
        </svg>
      );
    case "Book":
      return (
        <svg {...common}>
          <path d="M5 5.5A2.5 2.5 0 0 1 7.5 3H19v16H7.5A2.5 2.5 0 0 0 5 21V5.5Z" />
          <path d="M5 5.5V21M9 7h6" />
        </svg>
      );
    case "Library":
      return (
        <svg {...common}>
          <path d="M4 20h16M6 17V7M10 17V7M14 17V7M18 17V7M5 7h14M4 4h16" />
        </svg>
      );
    case "Sample":
      return (
        <svg {...common}>
          <path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6 5.6 18.4" />
          <circle cx="12" cy="12" r="8.5" />
        </svg>
      );
    case "Tool":
      return (
        <svg {...common}>
          <path d="m14.5 6.5 3-3 3 3-3 3M4 20l9.5-9.5M13 5a5 5 0 0 0-6.4 6.4L4 14v3h3l2.6-2.6A5 5 0 0 0 15 8" />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="M12 8v8M8 12h8" />
        </svg>
      );
  }
}
