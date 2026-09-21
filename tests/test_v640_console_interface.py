from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v640_console_has_demo_mode_and_navigation_layer():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    assert "demoMode" in js
    assert "CASE-10482" in js
    assert "openCommandPalette" in js
    assert "workspace-switcher" in js
    assert "command-palette" in css
    assert "mobile-nav-toggle" in js

def test_v640_demo_keeps_server_action_boundary():
    js=(ROOT/'frontend/assets/app.js').read_text()
    assert "Aucune action externe ne sera exécutée" in js
    assert "googleapis.com" not in js
    assert "Idempotency-Key" in js

def test_v640_case_console_has_human_review_states():
    js=(ROOT/'frontend/assets/app.js').read_text()
    for value in ["IN_REVIEW","PENDING_APPROVAL","FROZEN","EVIDENCE_REQUIRED"]:
        assert value in js
    for fn in ["createDecision","freezeCase","approveCase","prepareSubmission"]:
        assert fn in js


def test_v640_all_console_pages_have_explicit_view_and_navigation_contract():
    js=(ROOT/'frontend/assets/app.js').read_text()
    required=[
        'dashboard','reviews','cases','workload','escalations','evidence',
        'approvals','submissions','alerts','audit','settings'
    ]
    for page in required:
        assert "['"+page+"'" in js or page+':async=>' in js
        assert page+':async=>' in js or page+':async()=>{' in js
    assert 'caseWorkspace' in js
    assert 'renderLogin' in js and 'renderRecovery' in js and 'renderReset' in js and 'renderVerify' in js

def test_v640_design_system_has_required_responsive_and_interaction_primitives():
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['--panel:','--line:','--muted:','--accent:','--good:','--warn:','--bad:','@media(max-width:1100px)','@media(max-width:760px)','hover','modal-backdrop','loading','.empty']:
        assert token in css

def test_v640_audit_page_is_designed_not_placeholder():
    js=(ROOT/'frontend/assets/app.js').read_text()
    assert 'Journal d’audit' in js
    assert 'audit-item' in js
    assert 'TRACEABILITY' in js

def test_v640_demo_has_each_major_domain_state():
    js=(ROOT/'frontend/assets/app.js').read_text()
    for marker in ['HIGH','CRITICAL','MEDIUM','PENDING','DELIVERED','OPEN','VERIFIED','READY_FOR_HUMAN_ACTION']:
        assert marker in js


def test_v640_page_hierarchy_and_state_system_are_explicit():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    for page in ['dashboard','reviews','cases','workload','escalations','evidence','approvals','submissions','alerts','audit','settings']:
        assert page in js
    for token in ['viewMeta','pageHead','stateCard','loading-state','Impossible de charger cette vue']:
        assert token in js
    for token in ['.page-head','.state-card','.loading-state','.loading-bar','@keyframes rd-shimmer']:
        assert token in css


def test_v640_human_gate_copy_remains_visible_in_console():
    js=(ROOT/'frontend/assets/app.js').read_text()
    for marker in ['Revue humaine requise','Aucune action externe ne sera exécutée','Aucune de ces actions n’envoie ou ne supprime automatiquement un avis Google']:
        assert marker in js


def test_v640_each_console_page_has_premium_page_header_contract():
    js=(ROOT/'frontend/assets/app.js').read_text()
    required=['dashboard','reviews','cases','workload','escalations','evidence','approvals','submissions','alerts','audit','settings']
    for page in required:
        assert "pageHead('"+page+"'" in js
    assert 'hero-actions' in js
    assert 'section-toolbar' in js


def test_v640_empty_states_are_action_oriented():
    js=(ROOT/'frontend/assets/app.js').read_text()
    for marker in ['Aucun dossier pour le moment.','Aucune escalation active.','Les nouveaux dossiers apparaîtront ici après ingestion.']:
        assert marker in js


def test_v640_accessibility_focus_and_mobile_contracts():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    assert 'aria-label="Rechercher un dossier"' in js
    assert 'focus-visible' in css
    assert '.case-row:focus-visible' in css
    assert '@media(max-width:760px)' in css


def test_v640_block1_has_complete_design_foundation_tokens():
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in [
        '--bg:','--surface:','--surface-raised:','--surface-soft:',
        '--line-subtle:','--line-strong:','--text:','--text-soft:',
        '--muted-strong:','--accent-strong:','--focus:','--shadow-sm:',
        '--shadow-md:','--shadow-lg:','--radius-sm:','--radius-md:',
        '--radius-lg:','--radius-xl:','--space-1:','--space-8:','--ease:'
    ]:
        assert token in css


def test_v640_block1_has_foundation_interactions_and_accessibility():
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in [
        'focus-visible','prefers-reduced-motion','::placeholder',
        'surface-raised','sr-only','select{','button:active',
        'box-shadow:var(--focus)'
    ]:
        assert token in css


def test_v640_block1_has_consistent_surface_and_control_primitives():
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in [
        '.card,.panel,.hero-card',
        '.primary:hover',
        '.ghost,.link-btn,.icon-btn,.command-btn',
        'transition:',
        'border-radius:var(--radius'
    ]:
        assert token in css


def test_v640_block2_navigation_has_accessible_mobile_contract():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['console-sidebar','aria-label="Navigation principale"','aria-expanded','aria-controls="console-sidebar"','navigateTo(id)','closeMobileNav()','window.addEventListener']:
        assert token in js
    for token in ['.mobile-nav-scrim','body:has(.sidebar.mobile-open)','backdrop-filter','position:sticky','z-index:10']:
        assert token in css


def test_v640_block2_navigation_has_desktop_and_mobile_surface_contract():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    assert 'data-view="${id}"' in js
    assert "onclick=\"navigateTo('\\${id}')\"" in js
    assert 'Navigation rapide' in js
    assert '⌘K' in js
    assert 'nav button.active' in css
    assert 'sidebar.mobile-open' in css
    assert '@media(max-width:760px)' in css


def test_v640_block2_navigation_preserves_keyboard_escape_behavior():
    js=(ROOT/'frontend/assets/app.js').read_text()
    assert "e.key==='Escape'" in js
    assert "e.metaKey||e.ctrlKey" in js
    assert 'openCommandPalette()' in js


def test_v640_block3_dashboard_visual_contract():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    assert 'dashboard:async=>' in js
    for token in ['.dashboard-hero','.dashboard-health','.dashboard-kpis','.kpi-card','.dashboard-grid','.pipeline-large','.pipeline-step','.priority-stack','.activity-list','.activity-item','.guardrail-list']:
        assert token in css
    for token in ['@media(max-width:1100px)','@media(max-width:760px)','@media(max-width:480px)']:
        assert token in css


def test_v640_block3_dashboard_preserves_operational_guardrails():
    js=(ROOT/'frontend/assets/app.js').read_text()
    for marker in ['Décider avec des preuves','Revue humaine requise','RLS','SHA-256','aucune action Google autonome']:
        assert marker in js
    assert "state.view='cases'" in js
    assert "state.view='approvals'" in js


def test_v640_block3_dashboard_has_operational_metrics_sources():
    js=(ROOT/'frontend/assets/app.js').read_text()
    for endpoint in ['/v1/reviews','/v1/cases','/v1/approvals','/v1/notifications/metrics']:
        assert endpoint in js


def test_v640_block4_reviews_has_inbox_filters_and_detail_affordance():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['review-overview','review-summary','review-mini-grid','reviews-panel','review-toolbar','review-list','review-card','filterReviewCards','focusReview']:
        assert token in js or token in css
    for token in ['Rechercher un avis','Filtrer par note','Filtrer par priorité','Ouvrir l’avis']:
        assert token in js


def test_v640_block4_reviews_has_responsive_visual_contract():
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['.review-overview','.review-list','.review-toolbar','.review-card','@media(max-width:900px)','@media(max-width:600px)']:
        assert token in css


def test_v640_block4_reviews_keeps_read_only_human_control_boundary():
    js=(ROOT/'frontend/assets/app.js').read_text()
    assert 'sans déclencher d’action externe automatique' in js
    assert '/v1/reviews' in js

def test_v640_block5_cases_has_management_queue_and_filters():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['case-overview','case-summary','case-mini-grid','cases-panel','case-toolbar','case-card','filterCaseCards','case-guardrail']:
        assert token in js or token in css
    for token in ['Rechercher un dossier','Filtrer les dossiers','File des dossiers','Centre des dossiers']:
        assert token in js


def test_v640_block5_cases_has_responsive_visual_contract():
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['.case-overview','.case-list','.case-row','.case-toolbar','@media(max-width:900px)','@media(max-width:600px)']:
        assert token in css


def test_v640_block5_cases_preserves_case_detail_boundary_and_human_guardrail():
    js=(ROOT/'frontend/assets/app.js').read_text()
    assert "api('/v1/cases')" in js
    assert 'openCase(' in js
    assert 'Traçabilité conservée' in js
    assert 'contrôles humains' in js

def test_v640_block6_case_workspace_has_operational_sections():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['caseWorkspace','workspace-header','workspace-stats','workspace-main-grid','workspace-review','workspace-items','evidence-stack','matrix-grid','workspace-timeline','decision-card','workspace-guardrail']:
        assert token in js or token in css
    for token in ['Claims','Preuves liées','Matrice preuves ↔ claims','Timeline','Décision','Readiness']:
        assert token in js


def test_v640_block6_case_workspace_has_responsive_contract():
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['.workspace-main-grid','.workspace-sidebar','.workspace-bottom-grid','@media(max-width:1000px)','@media(max-width:700px)','@media(max-width:480px)']:
        assert token in css


def test_v640_block6_case_workspace_preserves_decision_freeze_approval_submission_chain():
    js=(ROOT/'frontend/assets/app.js').read_text()
    for token in ['createDecision(','freezeCase(','approveCase(','prepareSubmission(','Décision → gel → approbation → préparation de soumission']:
        assert token in js
    assert 'Aucune action Google externe automatique' in js

def test_v640_block7_sla_workload_has_operational_center():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['sla-overview','sla-hero','sla-kpis','sla-health','workload-panel','workload-list','workload-row','workload-track','sla-note']:
        assert token in js or token in css
    for token in ['SLA CONTROL CENTER','Charge & délais','Charge par analyste','Contrôle humain']:
        assert token in js


def test_v640_block7_sla_workload_has_responsive_contract():
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['.sla-overview','.workload-row','.sla-kpis','.sla-note','@media(max-width:900px)','@media(max-width:600px)']:
        assert token in css


def test_v640_block7_sla_workload_preserves_server_control_boundary():
    js=(ROOT/'frontend/assets/app.js').read_text()
    assert "api('/v1/review-queue/workload')" in js
    assert 'Les affectations et escalades restent régies par les contrôles serveur' in js

def test_v640_block8_evidence_has_integrity_registry_and_filters():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['evidence-overview','evidence-hero','evidence-kpis','evidence-registry','evidence-toolbar','evidence-list','evidence-card','hash-block','evidence-integrity-note']:
        assert token in js or token in css
    for token in ['Registre des preuves','Rechercher une preuve','Filtrer les preuves','SHA-256','Intégrité documentaire']:
        assert token in js


def test_v640_block8_evidence_has_responsive_contract():
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['.evidence-overview','.evidence-kpis','.evidence-toolbar','.hash-block','@media(max-width:900px)','@media(max-width:600px)']:
        assert token in css


def test_v640_block8_evidence_preserves_sha256_integrity_boundary():
    js=(ROOT/'frontend/assets/app.js').read_text()
    assert "api('/v1/evidence')" in js
    assert 'x.sha256' in js
    assert 'La présentation ne modifie jamais le contenu source.' in js

def test_v640_block9_approvals_has_human_gate_and_review_queue():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['approval-overview','approval-hero','approval-kpis','approvals-panel','approval-toolbar','approval-list','approval-card','approval-gate','approval-guardrail']:
        assert token in js or token in css
    for token in ['HUMAN APPROVAL GATE','Centre de validation','File de validation','Validation explicite obligatoire']:
        assert token in js


def test_v640_block9_approvals_has_responsive_contract():
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['.approval-overview','.approval-kpis','.approval-toolbar','.approval-card','@media(max-width:900px)','@media(max-width:600px)']:
        assert token in css


def test_v640_block9_approvals_preserves_human_action_boundary():
    js=(ROOT/'frontend/assets/app.js').read_text()
    assert "api('/v1/approvals')" in js
    assert 'Aucune action externe automatique' in js
    assert 'Une approbation n’exécute pas une action Google.' in js
    assert 'openApprovalCase(' in js

def test_v640_block9_approvals_exposes_decision_chain_steps():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    for token in ['approval-steps','Décision','Gel','Approbation','Soumission']:
        assert token in js
    for token in ['.approval-steps','.approval-steps .done','.approval-steps .current','.approval-steps .locked']:
        assert token in css


def test_v640_block9_approvals_does_not_add_external_action():
    js=(ROOT/'frontend/assets/app.js').read_text()
    assert 'api(\'/v1/approvals\')' in js
    assert 'openApprovalCase(' in js
    assert 'Aucune action externe automatique' in js
