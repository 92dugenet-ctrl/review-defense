import type { ReactNode } from "react";

type StatusPillProps = {
  children: ReactNode;
};

export function StatusPill({ children }: StatusPillProps) {
  return <span className="status-pill">{children}</span>;
}
