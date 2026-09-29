"""Server-rendered SEO pages, sitemap and robots for Review Defense (V6.39)."""
from __future__ import annotations
import html, json, os
from .seo_content import PAGES

BASE_URL = os.environ.get("REVIEW_DEFENSE_PUBLIC_URL", "https://review-defense.com").rstrip("/")
SERVICE_SLUGS = {"analyse-avis-google","service-suppression-avis-google","agence-suppression-avis-google","expert-suppression-avis-google","faire-supprimer-avis-google","prix-suppression-avis-google"}

def _page_map():
    return {"/" + slug + "/": (slug, title, keyword) for slug, title, keyword in PAGES}

def is_seo_path(path: str) -> bool:
    return path in _page_map()

TITLE_SUFFIXES = {
    "avis-google-argent-avantage": " | Cas concret",
    "avis-google-menace-entreprise": " | Cas concret",
    "pourquoi-mon-avis-google-reste-en-ligne-conversationnel": " | Cas concret",
    "google-refuse-de-supprimer-mon-faux-avis": " | Cas concret",
}

def _meta(slug: str, title: str) -> str:
    if slug == "suppression-avis-google":
        return "Guide complet sur la suppression d’avis Google : vérifier la situation, identifier le motif pertinent, signaler l’avis et connaître les prochaines étapes."
    if slug in SERVICE_SLUGS:
        return f"{title}. Analyse, qualification, préparation du dossier, accompagnement et suivi, sans garantie de suppression."
    return f"{title} Découvrez les vérifications à effectuer, les éléments à conserver, les options de signalement et les suites possibles. Analyse factuelle possible."

def _title_tag(slug: str, title: str) -> str:
    return title + TITLE_SUFFIXES.get(slug, " | Review Defense")

def _cluster(slug: str) -> str:
    if slug in SERVICE_SLUGS: return "Services"
    if slug == "faux-avis-google" or "faux-avis" in slug or "faux-client" in slug or "plusieurs-faux" in slug or "comptes-google" in slug: return "Faux avis"
    if "signaler" in slug or "signalement" in slug or "dossier-de-signalement" in slug: return "Signalement"
    if any(x in slug for x in ("refuse","reste-en-ligne","appel","contester","combien-de-temps")): return "Refus / appel"
    return "Suppression / cas concrets"

def _hub(slug: str):
    c=_cluster(slug)
    if c=="Faux avis": return ("faux-avis-google","Faux avis Google")
    if c=="Signalement": return ("signaler-un-avis-google","Signalement d’un avis Google")
    if c=="Refus / appel": return ("que-faire-quand-google-refuse-de-supprimer-un-avis","Refus et suites possibles")
    return ("suppression-avis-google","Suppression d’avis Google")

def _related(current_slug: str):
    c=_cluster(current_slug)
    rows=[x for x in PAGES if x[0] != current_slug and x[0] not in SERVICE_SLUGS]
    if current_slug == "analyse-avis-google": return PAGES[:6]
    filtered=[x for x in rows if _cluster(x[0])==c]
    return (filtered or rows)[:5]

def _topic(slug: str, title: str) -> dict[str, object]:
    t=(slug+" "+title).lower()
    if any(x in t for x in ("concurrent","ancien-salarie")):
        return {"label":"CONTEXTE À VÉRIFIER","focus":"Le contexte de l’auteur peut être un élément du dossier, mais il ne suffit pas à lui seul à qualifier l’avis. La méthode consiste à distinguer les faits établis, les indices et les hypothèses.","checks":["Documenter la relation connue avec l’entreprise","Conserver les éléments datés réellement disponibles","Séparer les faits des suppositions sur l’auteur","Éviter toute exposition inutile de données personnelles"]}
    if any(x in t for x in ("faux-client","sans-etre-client","personne-jamais-cliente")):
        return {"label":"RELATION CLIENT","focus":"L’absence apparente de relation client peut constituer un élément à examiner. Elle doit être documentée à partir des informations auxquelles l’entreprise a légitimement accès, sans transformer une absence de trace en certitude absolue.","checks":["Vérifier les systèmes internes pertinents","Définir la période et le périmètre de recherche","Conserver les éléments utiles sans données superflues","Présenter le résultat comme un constat vérifiable"]}
    if any(x in t for x in ("diffamatoire","accusation","mensonger")):
        return {"label":"ACCUSATION OU FAIT CONTESTÉ","focus":"Une accusation grave doit être traitée avec prudence. Il faut distinguer une opinion, un récit d’expérience, une affirmation factuelle et une qualification juridique. La formulation exacte de l’avis est essentielle.","checks":["Isoler les affirmations factuelles","Identifier les pièces qui les confirment ou les contredisent","Conserver les sources et dates utiles","Éviter les qualifications juridiques non vérifiées"]}
    if any(x in t for x in ("discriminatoire","insultant","menace","chantage")):
        return {"label":"CONTENU SENSIBLE","focus":"Lorsque le contenu contient des insultes, menaces, propos discriminatoires ou une pression particulière, le dossier doit rester factuel. Conservez le contexte nécessaire et limitez la diffusion des informations sensibles.","checks":["Conserver le contenu et son contexte","Identifier précisément le passage concerné","Documenter la chronologie","Séparer le signalement de l’avis des autres démarches éventuelles"]}
    if any(x in t for x in ("informations-personnelles","fausse-identite")):
        return {"label":"DONNÉES ET IDENTITÉ","focus":"Les informations personnelles ou les incohérences d’identité doivent être traitées avec retenue. Le dossier peut démontrer un problème sans publier davantage de données personnelles ni chercher à identifier publiquement l’auteur.","checks":["Identifier précisément le problème","Conserver uniquement les preuves nécessaires","Éviter toute publication de données personnelles","Décrire les incohérences observables sans spéculer"]}
    if any(x in t for x in ("mauvais-etablissement","hors-sujet")):
        return {"label":"PERTINENCE DU CONTENU","focus":"Un avis négatif n’est pas automatiquement hors sujet. Il faut montrer, à partir d’éléments concrets, pourquoi le contenu semble concerner un autre établissement, une autre activité ou un sujet sans rapport avec la fiche.","checks":["Vérifier l’établissement et son activité","Comparer les faits évoqués avec le contexte réel","Conserver les éléments de lieu ou d’activité","Ne pas confondre désaccord et hors-sujet"]}
    if any(x in t for x in ("plusieurs","comptes-google")):
        return {"label":"SCHÉMA MULTIPLE","focus":"Plusieurs avis similaires doivent être examinés comme un ensemble : dates, formulations, profils, répétitions et contexte. Un schéma peut être documenté sans affirmer un lien entre les auteurs qui n’est pas établi.","checks":["Construire une chronologie commune","Comparer les formulations et éléments répétitifs","Relier les avis uniquement par des faits observables","Conserver une preuve distincte pour chaque avis"]}
    if any(x in t for x in ("argent","avantage","promotionnel")):
        return {"label":"INCITATION","focus":"Lorsqu’un avis semble lié à une rémunération, un avantage ou une démarche promotionnelle, documentez ce qui est réellement observable : offre, message, contenu ou contexte. Ne déduisez pas un lien qui n’est pas étayé.","checks":["Conserver les éléments de sollicitation disponibles","Identifier l’avantage ou la promotion concernés","Séparer les faits des hypothèses","Préparer un dossier permettant de vérifier le motif"]}
    if any(x in t for x in ("conflit","litige")):
        return {"label":"CONFLIT OU LITIGE","focus":"Après un conflit, une chronologie neutre est particulièrement importante. Le simple fait qu’un désaccord existe ne suffit pas à déterminer si l’avis peut être signalé.","checks":["Construire une chronologie des échanges","Séparer faits vérifiables et ressentis","Conserver contrats, échanges ou documents utiles","Éviter les informations confidentielles inutiles"]}
    if any(x in t for x in ("signaler","signalement")):
        return {"label":"SIGNALEMENT","focus":"Un signalement est plus lisible lorsqu’il repose sur un motif précis et des éléments vérifiables. Le but n’est pas d’accumuler des arguments génériques, mais d’expliquer clairement le problème rencontré.","checks":["Identifier le motif pertinent","Conserver la preuve du contenu","Rédiger une explication courte et factuelle","Suivre et documenter la suite donnée"]}
    if any(x in t for x in ("refuse","reste-en-ligne","appel","contester")):
        return {"label":"REFUS ET SUITES","focus":"Un refus ou le maintien d’un avis doit être traité comme une étape supplémentaire. Conservez la décision, relisez le motif et vérifiez si une procédure de suivi ou d’appel est disponible.","checks":["Conserver la notification ou le statut","Relire le motif initial","Identifier les éléments réellement nouveaux","Documenter toute nouvelle démarche"]}
    if any(x in t for x in ("combien-de-temps","délai")):
        return {"label":"DÉLAI ET SUIVI","focus":"Le traitement d’un signalement peut dépendre de la procédure concernée et du contexte. Il est utile de distinguer la date d’envoi, le traitement de la demande et l’éventuelle suite apportée.","checks":["Noter la date du signalement","Conserver les références disponibles","Éviter les demandes identiques répétées sans raison","Prévoir une étape de suivi"]}
    return {"label":"ANALYSE","focus":"Avant toute démarche, commencez par décrire précisément ce qui pose problème. Un avis négatif, inhabituel ou contesté doit être examiné à partir de faits disponibles et du contexte.","checks":["Lire l’avis dans son intégralité","Vérifier le contexte disponible","Séparer faits et opinions","Conserver les pièces utiles"]}

def _faq(title: str):
    return [
        ("Peut-on supprimer cet avis Google ?", "Cela dépend du contenu, du contexte et du motif applicable. Un avis négatif ou contesté n’est pas automatiquement supprimable."),
        ("Quels éléments faut-il vérifier ?", "Vérifiez le texte exact, le contexte, les dates, les faits disponibles et les éléments permettant de documenter les affirmations."),
        ("Comment signaler un avis Google ?", "Utilisez la procédure adaptée lorsque le contenu semble relever d’un motif prévu par les règles applicables et conservez les éléments transmis."),
        ("Que faire si Google refuse ?", "Conservez la décision, vérifiez le motif et examinez les possibilités de suivi ou de contestation disponibles."),
        ("La suppression est-elle garantie ?", "Non. Google ou la plateforme concernée prend la décision finale.")
    ]

def _body(slug: str, title: str, keyword: str) -> str:
    service=slug in SERVICE_SLUGS
    if service:
        sections=[
            ("Le problème","Une analyse d’avis utile commence par la situation réelle de l’entreprise : contenu de l’avis, contexte, éléments disponibles et objectif recherché. L’enjeu est de transformer une situation dispersée en dossier lisible, sans promettre un résultat que la plateforme tierce ne maîtrise pas."),
            ("Ce qui est analysé","Le contenu de l’avis, ses affirmations, le contexte commercial connu, les éléments factuels disponibles, les contradictions éventuelles et le motif de signalement qui semble pertinent. L’analyse peut également porter sur la chronologie des démarches déjà effectuées."),
            ("Le processus","Le parcours suit une logique progressive : analyse, qualification, collecte et rattachement des preuves, décision, gel du dossier, validation humaine puis préparation contrôlée. Les étapes sensibles restent explicitement sous le contrôle de l’utilisateur."),
            ("Ce qui est inclus","Selon le périmètre choisi : lecture structurée de la situation, qualification assistée, organisation des preuves, chronologie, préparation d’un dossier, suivi des démarches et analyse d’une éventuelle réponse ou d’un refus."),
            ("Limites","Aucune suppression n’est garantie. Un avis négatif n’est pas automatiquement contraire aux règles. Google ou la plateforme concernée conserve la décision finale, et Review Defense ne déclenche pas automatiquement une suppression, un signalement ou une réponse."),
        ]
    else:
        topic=_topic(slug,title)
        sections=[
            ("Réponse courte",f"Pour traiter « {title} », commencez par vérifier les faits, identifier le motif pertinent et conserver les éléments utiles. La possibilité de signaler ou de faire examiner un avis dépend du contenu et des règles applicables. Une suppression n’est jamais garantie : la plateforme concernée prend la décision finale."),
            ("Pourquoi cette situation doit-elle être vérifiée ?",str(topic["focus"])),
            ("Quels éléments faut-il examiner ?",f"Commencez par l’avis lui-même : texte, date, note, contexte apparent et éventuels éléments publics associés. Comparez ensuite avec les informations auxquelles l’entreprise a légitimement accès. {topic['checks'][0]}. {topic['checks'][1]}."),
            ("Quels éléments conserver avant d’agir ?",f"Un dossier utile est surtout un dossier lisible. Conservez l’URL de l’avis, une capture datée, les informations de contexte et les documents qui permettent de vérifier les affirmations. {topic['checks'][2]}. {topic['checks'][3]}."),
            ("Comment agir ou signaler l’avis ?","Lorsque la situation semble relever d’un motif prévu par les règles applicables, préparez une explication factuelle et utilisez la procédure de signalement adaptée. Le signalement demande un examen ; il ne constitue pas une garantie de retrait. Si une réponse publique est envisagée, elle doit rester distincte de la procédure de signalement."),
            ("Que faire si Google refuse ou ne répond pas ?","Conservez la notification, la référence et la chronologie. Relisez le motif initial et vérifiez si le dossier contient réellement des éléments qui répondent au problème. Lorsqu’une voie de suivi ou d’appel existe, préparez-la à partir d’éléments pertinents plutôt que de répéter mécaniquement la même demande."),
            ("Quand demander une analyse professionnelle ?","Une analyse structurée devient particulièrement utile lorsque plusieurs avis doivent être rapprochés, lorsque les preuves sont dispersées, lorsqu’une chronologie doit être reconstruite ou lorsqu’un premier signalement n’a pas abouti. Le rôle d’un tel accompagnement est de clarifier et préparer le dossier, pas de garantir une décision de Google."),
        ]
    faq=_faq(title)
    out=['<article class="seo-article">']
    out.append(f'<div class="seo-answer"><strong>Réponse en bref</strong><p>{html.escape(sections[0][1])}</p></div>')
    for i,(h,p) in enumerate(sections):
        if i==0: continue
        out.append(f'<section class="seo-section seo-section-{i}"><div class="seo-section-index">0{i}</div><div><h2>{html.escape(h)}</h2><p>{html.escape(p)}</p></div></section>')
    if not service:
        out.append('<section class="seo-section seo-checks"><div class="seo-section-index">08</div><div><h2>Checklist avant toute démarche</h2><div class="seo-checklist">')
        for i,c in enumerate(topic["checks"],1):
            out.append(f'<div><b>0{i}</b><span>{html.escape(str(c))}</span></div>')
        out.append('</div></div></section>')
    out.append('<section class="seo-faq"><h2>Questions fréquentes</h2>')
    for q,a in faq:
        out.append(f'<details><summary>{html.escape(q)}<span>+</span></summary><p>{html.escape(a)}</p></details>')
    out.append('</section>')
    out.append('<section class="seo-cta"><div><span>REVIEW DEFENSE · ANALYSE</span><h2>Votre avis mérite un dossier clair.</h2><p>Structurez les faits, reliez les preuves et préparez la suite avec une validation humaine avant toute démarche externe.</p></div><a class="btn-primary" href="/analyse-avis-google/">Analyser mon avis →</a></section>')
    out.append('</article>')
    return "".join(out)


def _article_visual(slug: str) -> str:
    if slug in SERVICE_SLUGS: return "/assets/resource-report.svg"
    if any(x in slug for x in ("faux","client","concurrent","salarie","fausse-identite","plusieurs")): return "/assets/resource-fake-review.svg"
    if any(x in slug for x in ("signaler","signalement","dossier")): return "/assets/resource-evidence.svg"
    if any(x in slug for x in ("refuse","reste-en-ligne","appel","contester")): return "/assets/resource-refused.svg"
    if "analyse" in slug: return "/assets/resource-ai.svg"
    return "/assets/resource-google.svg"

def render_page(path: str) -> bytes:
    slug,title,keyword=_page_map()[path]
    meta=_meta(slug,title)
    canonical=BASE_URL+path
    hub_slug,hub_title=_hub(slug)
    related=_related(slug)
    related_html="".join(f'<li><a href="/{html.escape(s)}/">{html.escape(t)}</a></li>' for s,t,_ in related)
    faq=_faq(title)
    schema_graph=[
        {"@type":"Organization","@id":BASE_URL+"/#organization","name":"Review Defense","url":BASE_URL+"/"},
        {"@type":"WebSite","@id":BASE_URL+"/#website","name":"Review Defense","url":BASE_URL+"/","inLanguage":"fr-FR"},
        {"@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":"Accueil","item":BASE_URL+"/"},
            {"@type":"ListItem","position":2,"name":hub_title,"item":BASE_URL+"/"+hub_slug+"/"},
            {"@type":"ListItem","position":3,"name":title,"item":canonical}]},
        {"@type":"Service" if slug in SERVICE_SLUGS else "Article","headline":title,"name":title,"description":meta,"url":canonical,"inLanguage":"fr-FR","author":{"@type":"Organization","name":"Review Defense"}}
    ]
    if slug in SERVICE_SLUGS:
        schema_graph[-1]["provider"]={"@type":"Organization","name":"Review Defense"}
    else:
        schema_graph[-1]["dateModified"]="2026-09-21"
    schema_graph.append({"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]})
    schema={"@context":"https://schema.org","@graph":schema_graph}
    doc=f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(_title_tag(slug,title))}</title><meta name="description" content="{html.escape(meta)}">
<link rel="canonical" href="{html.escape(canonical)}"><meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="article"><meta property="og:title" content="{html.escape(_title_tag(slug,title))}"><meta property="og:description" content="{html.escape(meta)}"><meta property="og:url" content="{html.escape(canonical)}">
<link rel="stylesheet" href="/assets/app.css"><link rel="stylesheet" href="/assets/public.css?v=6500"><link rel="stylesheet" href="/assets/seo.css?v=6500">
<script type="application/ld+json">{json.dumps(schema,ensure_ascii=False,separators=(",",":"))}</script></head><body>
<div class="marketing"><header class="public-header"><div class="rd-nav-inner"><a class="public-brand" href="/"><b class="brand-mark">RD</b><span>Review Defense</span></a><nav class="public-nav"><a href="/produit/">Produit</a><a href="/comment-ca-marche/">Comment ça marche</a><a href="/services/">Services</a><a href="/tarifs/">Tarifs</a><a href="/ressources/">Ressources</a></nav><div class="public-actions"><a class="btn-secondary" href="/app">Connexion</a><a class="btn-primary" href="/analyse-avis-google/">Analyser un avis <span>→</span></a></div></div></header>
<main class="seo-main"><nav class="breadcrumbs"><a href="/">Accueil</a><span>›</span><a href="/{hub_slug}/">{html.escape(hub_title)}</a><span>›</span><span>{html.escape(title)}</span></nav><header class="seo-hero"><div class="seo-hero-copy"><span>{html.escape(_cluster(slug).upper())}</span><h1>{html.escape(title)}</h1><p>{html.escape(meta)}</p><div class="seo-keyword">Sujet : {html.escape(keyword)}</div></div><div class="seo-hero-visual" style="background-image:url('{_article_visual(slug)}')" aria-hidden="true"></div></header>{_body(slug,title,keyword)}<aside class="seo-related"><h2>À lire ensuite</h2><ul>{related_html}</ul></aside></main>
<footer class="public-footer"><div><a class="public-brand" href="/"><b class="brand-mark">◆</b> Review Defense</a><p>Analyse, qualification et accompagnement autour des avis en ligne.</p></div><div><b>Produit</b><a href="/produit/">Fonctionnalités</a><a href="/tarifs/">Tarifs</a></div><div><b>Ressources</b><a href="/ressources/">Guides</a><a href="/analyse-avis-google/">Analyser un avis</a></div></footer></div></body></html>'''
    return doc.encode("utf-8")

def sitemap() -> bytes:
    urls=[BASE_URL+"/",BASE_URL+"/produit/",BASE_URL+"/comment-ca-marche/",BASE_URL+"/services/",BASE_URL+"/tarifs/",BASE_URL+"/ressources/",BASE_URL+"/contact/",BASE_URL+"/analyse-avis-google/"]+[BASE_URL+"/"+slug+"/" for slug,_,_ in PAGES if slug!="analyse-avis-google"]
    body="".join(f"<url><loc>{html.escape(u)}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>'.encode()

def robots() -> bytes:
    return f"User-agent: *\nAllow: /\nDisallow: /app\nDisallow: /v1/\nDisallow: /reset-password\nDisallow: /verify-email\nDisallow: /accept-invitation\nSitemap: {BASE_URL}/sitemap.xml\n".encode()
