/* Review Defense V6.40 — reusable UI primitives.
 * Framework-free presentation layer over the existing V6.40 frontend.
 * Authorization and sensitive actions remain server-side.
 */
(function (global) {
  const esc = (value) =>
    String(value ?? '').replace(/[&<>"']/g, (character) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    })[character]);

  const normalize = (value) =>
    String(value ?? 'UNKNOWN')
      .trim()
      .toUpperCase()
      .replace(/\s+/g, '_');

  const statusLabel = (status) =>
    normalize(status).replace(/_/g, ' ');

  const statusTone = (status) => {
    const value = normalize(status);

    if (
      ['VERIFIED', 'APPROVED', 'COMPLETED', 'READY', 'PREPARED', 'DELIVERED']
        .includes(value)
    ) {
      return 'success';
    }

    if (
      [
        'PENDING',
        'PENDING_APPROVAL',
        'TO_VERIFY',
        'EVIDENCE_REQUIRED',
        'IN_REVIEW',
        'WARNING',
        'DUE_SOON'
      ].includes(value)
    ) {
      return 'warning';
    }

    if (
      ['REJECTED', 'ERROR', 'OVERDUE', 'CRITICAL', 'BLOCKED']
        .includes(value)
    ) {
      return 'danger';
    }

    if (['FROZEN', 'LOCKED', 'READ_ONLY'].includes(value)) {
      return 'neutral';
    }

    return 'info';
  };

  const statusBadge = (status, options = {}) =>
    '<span class="rd-status rd-status--' +
    statusTone(status) +
    '" aria-label="Statut ' +
    esc(statusLabel(status)) +
    '">' +
    esc(options.label || statusLabel(status)) +
    '</span>';

  const button = (label, variant = 'secondary', attributes = '') =>
    '<button type="button" class="rd-btn rd-btn--' +
    esc(variant) +
    '" ' +
    attributes +
    '>' +
    esc(label) +
    '</button>';

  const kpiCard = (label, value, caption = '', tone = 'neutral') =>
    '<article class="rd-kpi-card rd-kpi-card--' +
    esc(tone) +
    '"><span class="rd-kpi-label">' +
    esc(label) +
    '</span><strong class="rd-kpi-value">' +
    esc(value) +
    '</strong><small class="rd-kpi-caption">' +
    esc(caption) +
    '</small></article>';

  const emptyState = (title, body = '') =>
    '<div class="rd-state rd-state--empty" role="status"><strong>' +
    esc(title) +
    '</strong>' +
    (body ? '<p>' + esc(body) + '</p>' : '') +
    '</div>';

  const errorState = (title, body = '') =>
    '<div class="rd-state rd-state--error" role="alert"><strong>' +
    esc(title) +
    '</strong>' +
    (body ? '<p>' + esc(body) + '</p>' : '') +
    '</div>';

  const loadingState = () =>
    '<div class="rd-state rd-state--loading" role="status" ' +
    'aria-live="polite"><span></span><span></span><span></span>' +
    '<strong>Chargement…</strong></div>';

  const evidenceCard = (item = {}) =>
    '<article class="rd-evidence-card"><div class="rd-evidence-head">' +
    '<div><strong>' +
    esc(item.evidence_id || item.filename || 'EVIDENCE') +
    '</strong><small>' +
    esc(item.content_type || item.evidence_type || 'Type inconnu') +
    '</small></div>' +
    statusBadge(item.status || 'TO_VERIFY') +
    '</div><div class="rd-evidence-hash"><span>SHA-256</span><code>' +
    esc(item.sha256 || 'Empreinte indisponible') +
    '</code></div></article>';

  const timeline = (events = []) =>
    '<ol class="rd-timeline">' +
    (
      events.length
        ? events.map((event) =>
            '<li><span class="rd-timeline-dot" aria-hidden="true"></span>' +
            '<div><time>' +
            esc(event.occurred_at || event.time || '') +
            '</time><strong>' +
            esc(event.kind || event.type || 'Événement') +
            '</strong><p>' +
            esc(event.result || event.description || event.actor || '') +
            '</p></div></li>'
          ).join('')
        : '<li class="rd-timeline-empty">Aucun événement enregistré.</li>'
    ) +
    '</ol>';

  const approvalGate = (item = {}) => {
    const status = normalize(item.status || 'PENDING');
    const approved = status === 'APPROVED';

    return (
      '<section class="rd-approval-gate" aria-label="Validation humaine">' +
      '<div class="rd-approval-head"><div>' +
      '<span class="rd-eyebrow">HUMAN APPROVAL GATE</span><h3>' +
      esc(item.approval_id || 'Validation') +
      '</h3></div>' +
      statusBadge(status) +
      '</div><div class="rd-approval-chain">' +
      '<span class="done">Décision</span><span class="done">Gel</span>' +
      '<span class="' +
      (approved ? 'done' : 'current') +
      '">Approbation</span><span class="locked">Action contrôlée</span>' +
      '</div><p>Une approbation autorise uniquement la progression vers ' +
      'l’étape contrôlée suivante. Aucune action Google n’est exécutée ' +
      'automatiquement.</p></section>'
    );
  };

  global.RDUI = {
    esc,
    normalize,
    statusBadge,
    button,
    kpiCard,
    emptyState,
    errorState,
    loadingState,
    evidenceCard,
    timeline,
    approvalGate
  };
})(window);
