import type { ReactNode } from "react";

type DetailMetaProps = {
  children: ReactNode;
};

export function DetailMeta({ children }: DetailMetaProps) {
  return <div className="detail-meta">{children}</div>;
}
