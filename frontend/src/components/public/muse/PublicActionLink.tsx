import type { ReactNode } from "react";
import { Link } from "react-router-dom";

type PublicActionLinkProps = {
  to: string;
  children: ReactNode;
  className?: string;
};

export function PublicActionLink({
  to,
  children,
  className = "muse-pill muse-blue",
}: PublicActionLinkProps) {
  return (
    <Link className={className} to={to}>
      {children}
    </Link>
  );
}
