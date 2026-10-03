import type { ReactNode } from "react";

type FeedbackMessageProps = {
  children: ReactNode;
  className: "empty" | "form-error" | "module-empty";
  role?: "alert" | "status";
};

export function FeedbackMessage({
  children,
  className,
  role,
}: FeedbackMessageProps) {
  return (
    <div className={className} role={role}>
      {children}
    </div>
  );
}
