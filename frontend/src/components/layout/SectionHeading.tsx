import type { ReactNode } from "react";

type SectionHeadingProps = {
  eyebrow: string;
  title: string;
  action?: ReactNode;
};

export function SectionHeading({
  eyebrow,
  title,
  action,
}: SectionHeadingProps) {
  return (
    <div className="dashboard-section-heading">
      <div>
        <span>{eyebrow}</span>
        <h2>{title}</h2>
      </div>
      {action}
    </div>
  );
}
