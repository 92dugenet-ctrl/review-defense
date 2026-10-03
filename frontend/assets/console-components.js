// Shared console rendering primitives.
const stateCard=(kind,
  title,
  body)=>`<div class="state-card ${esc(kind)}"><div class="state-icon">${kind==='error'?'!':kind==='empty'?'∅':'·'}</div><div><strong>${esc(title)}</strong><p>${esc(body)}</p></div></div>`;
const pageHead=(id,
  count='')=>{const m=viewMeta[id]||[id,
  ''];return `<div class="section-head page-head"><div><div class="eyebrow">${esc(m[0])}</div><h2>${esc(navItems.find(x=>x[0]===id)?.[1]||id)}</h2><p>${esc(m[1])}</p></div>${count?`<span class="pill">${esc(count)}</span>`:''}</div>`};
