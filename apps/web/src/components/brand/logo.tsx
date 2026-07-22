import { cn } from "@/lib/utils";

export function Logo({
  className,
  showWordmark = true,
}: {
  className?: string;
  showWordmark?: boolean;
}) {
  return (
    <span className={cn("flex items-center gap-2.5", className)}>
      <span className="relative grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-primary to-emerald-400 shadow-lg shadow-primary/30">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          className="h-5 w-5 text-primary-foreground"
          aria-hidden
        >
          <path
            d="M12 2.5 4 5.5v5.2c0 4.9 3.3 8.7 8 10.8 4.7-2.1 8-5.9 8-10.8V5.5L12 2.5Z"
            fill="currentColor"
            fillOpacity="0.18"
          />
          <path
            d="M12 2.5 4 5.5v5.2c0 4.9 3.3 8.7 8 10.8 4.7-2.1 8-5.9 8-10.8V5.5L12 2.5Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
          <path
            d="m8.6 12 2.3 2.3 4.5-4.6"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      {showWordmark && (
        <span className="text-lg font-bold tracking-tight">
          Secure<span className="text-primary">Naija</span>
        </span>
      )}
    </span>
  );
}
