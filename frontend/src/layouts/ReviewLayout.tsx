import type { ReactNode } from "react";

export default function ReviewLayout({
  sidebar,
  main,
  aside,
}: {
  sidebar: ReactNode;
  main: ReactNode;
  aside: ReactNode;
}) {
  return (
    <div className="review-layout">
      <aside className="review-sidebar">{sidebar}</aside>
      <div className="review-main">{main}</div>
      <aside className="review-aside">{aside}</aside>
    </div>
  );
}
