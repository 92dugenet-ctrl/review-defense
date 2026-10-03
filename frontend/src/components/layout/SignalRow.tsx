import type { ReactNode } from "react";

type SignalRowProps = {
  children: ReactNode;
};

export function SignalRow({ children }: SignalRowProps) {
  return (
    <div className="signal-row">
      <span className="priority-dot" />
      <span>{children}</span>
    </div>
  );
}
