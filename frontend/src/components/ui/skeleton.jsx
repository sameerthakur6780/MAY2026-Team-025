import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }) {
  return <div className={cn("animate-pulse rounded-md bg-surface-2", className)} {...props} />;
}

export { Skeleton };
