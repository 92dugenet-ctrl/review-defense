/* Review Defense V6.40 — reusable UI primitives.
 * Framework-free presentation layer over the existing V6.40 frontend.
 * Authorization and sensitive actions remain server-side.
 */
(function(global){
  const esc=(s)=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const normalize=(s)=>String(s??'UNKNOWN').trim().toUpperCase().replace(/\s+/g,'_');
  const statusLabel=(s)=>normalize(s).replace(/_/g,' ');
  const statusTone=(s)=>{
    const v=normalize(s);
    if(['VERIFIED','APPROVED','COMPLETED','READY','PREPARED','DELIVERED'].includes(v))return 'success';
    if(['PENDING','PENDING_APPROVAL','TO_VERIFY','EVIDENCE_REQUIRED','IN_REVIEW','WARNING','DUE_SOON'].includes(v))return 'warning';
    if(['REJECTED','ERROR','OVERDUE','CRITICAL','BLOCKED'].includes(v))return 'danger';
    if(['FROZEN','LOCKED','READ_ONLY'].includes(v))return 'neutral';
    return 'info';
  };
  const statusBadge=(status,opts={})=>'<span class="rd-status rd-status--'+statusTone(status)+'" aria-label="Statut '+esc(statusLabel(status))+'">'+esc(opts.label||statusLabel(status))+'</span>';
  const button=(label,variant='secondary',attrs='')=>'<button type="button" class="rd-btn rd-btn--'+esc(variant)+'" '+attrs+'>'+esc(label)+'</button>';
  const kpiCard=(label,value,caption='',tone='neutral')=>'<article class="rd-kpi-card rd-kpi-card--'+esc(tone)+'"><span class="rd-kpi-label">'+esc(label)+'</span><strong class="rd-kpi-value">'+esc(value)+'</strong><small class="rd-kpi-caption">'+esc(caption)+'</small></article>';
  const emptyState=(title,body='')=>'<div class="rd-state rd-state--empty" role="status"><strong>'+esc(title)+'</strong>'+(body?'<p>'+esc(body)+'</p>':'')+'</div>';
  const errorState=(title,body='')=>'<div class="rd-state rd-state--error" role="alert"><strong>'+esc(title)+'</strong>'+(body?'<p>'+esc(body)+'</p>':'')+'</div>';
  const loadingState=()=>'<div class="rd-state rd-state--loading" role="status" aria-live="polite"><span></span><span></span><span></span><strong>Chargement…</strong></div>';
  const evidenceCard=(item={})=>'<article class="rd-evidence-card"><div class="rd-evidence-head"><div><strong>'+esc(item.evidence_id||item.filename||'EVIDENCE')+'</strong><small>'+esc(item.content_type||item.evidence_type||'Type inconnu')+'</small></div>'+statusBadge(item.status||'TO_VERIFY')+'</div><div class="rd-evidence-hash"><span>SHA-256</span><code>'+esc(item.sha256||'Empreinte indisponible')+'</code></div></article>';
  const timeline=(events=[])=>'<ol class="rd-timeline">'+(events.length?events.map(e=>'<li><span class="rd-timeline-dot" aria-hidden="true"></span><div><time>'+esc(e.occurred_at||e.time||'')+'</time><strong>'+esc(e.kind||e.type||'Événement')+'</strong><p>'+esc(e.result||e.description||e.actor||'')+'</p></div></li>').join(''):'<li class="rd-timeline-empty">Aucun événement enregistré.</li>')+'</ol>';
  const approvalGate=(item={})=>{
    const s=normalize(item.status||'PENDING'); const approved=s==='APPROVED';
    return '<section class="rd-approval-gate" aria-label="Validation humaine"><div class="rd-approval-head"><div><span class="rd-eyebrow">HUMAN APPROVAL GATE</span><h3>'+esc(item.approval_id||'Validation')+'</h3></div>'+statusBadge(s)+'</div><div class="rd-approval-chain"><span class="done">Décision</span><span class="done">Gel</span><span class="'+(approved?'done':'current')+'">Approbation</span><span class="locked">Action contrôlée</span></div><p>Une approbation autorise uniquement la progression vers l’étape contrôlée suivante. Aucune action Google n’est exécutée automatiquement.</p></section>';
  };
  global.RDUI={esc,normalize,statusBadge,button,kpiCard,emptyState,errorState,loadingState,evidenceCard,timeline,approvalGate};
})(window);
