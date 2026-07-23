import { cn } from "@/lib/utils";

/**
 * No_Gree AI brand lockup. The mark is the shield logo on a dark tile;
 * the wordmark uses the brand green ("No_") + red ("Gree") + an "AI" chip.
 */
export function Logo({
  className,
  showWordmark = true,
  size = 36,
}: {
  className?: string;
  showWordmark?: boolean;
  size?: number;
}) {
  return (
    <span className={cn("flex items-center gap-2.5", className)}>
      <span
        className="relative grid shrink-0 place-items-center overflow-hidden rounded-xl bg-black shadow-md-brand"
        style={{ width: size, height: size }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/logo.jpg"
          alt="No_Gree AI"
          className="h-full w-full object-cover"
        />
      </span>
      {showWordmark && (
        <span className="font-display text-lg font-bold leading-none tracking-tight">
          <span style={{ color: "var(--neon-green)" }}>No_</span>
          <span style={{ color: "var(--neon-red)" }}>Gree</span>
          <span className="ml-1.5 inline-flex items-center rounded-[5px] border border-white/15 bg-neutral-900 px-1.5 py-0.5 text-[0.62em] font-bold text-white">
            AI
          </span>
        </span>
      )}
    </span>
  );
}
