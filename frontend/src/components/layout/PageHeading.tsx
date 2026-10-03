import type { ReactNode } from "react";

type PageHeadingProps = {
  eyebrow: string;
  title: ReactNode;
  description: ReactNode;
  className?: string;
  as?: "div" | "header";
  action?: ReactNode;
};

export function PageHeading({
  eyebrow,
  title,
  description,
  className = "page-title",
  as: HeadingTag = "div",
  action,
}: PageHeadingProps) {
  return (
    <HeadingTag className={className}>
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </HeadingTag>
  );
}
