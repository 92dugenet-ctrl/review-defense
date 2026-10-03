import type { ReactNode } from "react";
import { Link } from "react-router-dom";

type PublicActionLinkProps = {
  to: string;
  children: ReactNode;
  className?: string;
};

/**
 * Shared internal navigation link styled as a public-page call to action.
 * The destination remains a router path so navigation stays client-side.
 */
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
