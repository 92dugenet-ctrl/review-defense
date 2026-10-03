// Shared console rendering primitives.

const stateCard = (
  kind,
  title,
  body
) => {
  const icon = (
    kind === "error"
      ? "!"
      : kind === "empty"
        ? "∅"
        : "·"
  );

  return `
    <div class="state-card ${esc(kind)}">
      <div class="state-icon">${icon}</div>
      <div>
        <strong>${esc(title)}</strong>
        <p>${esc(body)}</p>
      </div>
    </div>
  `;
};

const pageHead = (
  id,
  count = ""
) => {
  const metadata = viewMeta[id] || [
    id,
    "",
  ];

  const pageTitle = (
    navItems.find(item => item[0] === id)?.[1]
    || id
  );

  const countMarkup = count
    ? `<span class="pill">${esc(count)}</span>`
    : "";

  return `
    <div class="section-head page-head">
      <div>
        <div class="eyebrow">${esc(metadata[0])}</div>
        <h2>${esc(pageTitle)}</h2>
        <p>${esc(metadata[1])}</p>
      </div>
      ${countMarkup}
    </div>
  `;
};
