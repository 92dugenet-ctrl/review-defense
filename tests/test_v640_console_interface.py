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
