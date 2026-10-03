import type { ReactNode } from "react";
import { Link } from "react-router-dom";

type BackLinkProps = {
  to: string;
  children: ReactNode;
};

export function BackLink({ to, children }: BackLinkProps) {
  return (
    <Link to={to} className="back-link">
      {children}
    </Link>
  );
}
