"""Server-rendered SEO pages, sitemap and robots for Review Defense (V6.39)."""
from __future__ import annotations
import html, json, os
from .seo_content import PAGES

BASE_URL = os.environ.get("REVIEW_DEFENSE_PUBLIC_URL", "https://review-defense.com").rstrip("/")
SERVICE_SLUGS = {"analyse-avis-google","service-suppression-avis-google","agence-suppression-avis-google","expert-suppression-avis-google","faire-supprimer-avis-google","prix-suppression-avis-google"}

def _page_map():
    return {"/" + slug + "/": (slug, title, keyword) for slug, title, keyword in PAGES}

def is_seo_path(path: str) -> bool:
    return path in _page_map() or path in {"/","/produit/","/comment-ca-marche/","/services/","/tarifs/","/ressources/","/contact/","/analyse-avis-google/"}

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

def _faq(title: str):
    return [
        ("Peut-on supprimer cet avis Google ?", "Cela dépend du contenu, du contexte et du motif applicable. Un avis négatif ou contesté n’est pas automatiquement supprimable."),
        ("Quels éléments faut-il vérifier ?", "Le texte de l’avis, son contexte, les faits disponibles et les éléments permettant de documenter les affirmations."),
        ("Comment signaler un avis Google ?", "Utilisez la procédure adaptée lorsque le contenu semble relever d’un motif prévu par les règles applicables et conservez les éléments transmis."),
        ("Que faire si Google refuse ?", "Conservez la décision, vérifiez le motif et examinez les possibilités de suivi ou de contestation disponibles."),
        ("La suppression est-elle garantie ?", "Non. Google prend la décision finale."),
    ]

def _body(slug: str, title: str, keyword: str) -> str:
    service=slug in SERVICE_SLUGS
    if service:
        sections=[
            ("Le problème","Un service d’analyse d’avis doit distinguer les faits vérifiables des impressions, documenter le contexte et préparer les éléments utiles avant toute démarche."),
            ("Ce qui est analysé","Le contexte de l’avis, ses affirmations, les éléments de preuve disponibles, les contradictions éventuelles et le motif de signalement pertinent."),
            ("Le processus","Analyse → qualification → préparation des éléments → accompagnement du signalement → suivi. Les décisions importantes restent soumises à une validation humaine."),
            ("Ce qui est inclus","Un dossier structuré, des éléments traçables et un suivi du traitement. Le périmètre exact dépend de la situation et des preuves disponibles."),
            ("Limites","Aucune suppression n’est garantie. Google conserve la décision finale et un avis défavorable n’est pas automatiquement supprimable."),
        ]
    else:
        sections=[
            ("Réponse courte",f"Pour traiter « {title} », commencez par vérifier les faits, identifier le motif pertinent et conserver les éléments utiles. Ne qualifiez pas un avis de faux ou de supprimable sans éléments permettant de l’étayer."),
            ("Quels éléments vérifier ?","Vérifiez le contenu exact de l’avis, son contexte, la relation commerciale connue, les dates utiles et tout élément permettant de confronter les affirmations à des faits."),
            ("Quels éléments conserver ?","Conservez l’URL de l’avis, des captures datées, les échanges utiles et les pièces factuelles disponibles. Reliez si possible chaque élément à l’affirmation qu’il permet de vérifier."),
            ("Comment agir ou signaler l’avis ?","Lorsque le contenu semble relever d’un motif applicable, utilisez la procédure adaptée. Un signalement demande un examen et ne garantit pas une suppression."),
            ("Que faire en cas de refus ou d’absence de réponse ?","Relisez le motif invoqué, vérifiez la cohérence du dossier et examinez les voies de suivi ou de contestation proposées lorsqu’elles sont disponibles."),
            ("Quand demander une analyse professionnelle ?","Une analyse structurée peut être utile lorsque plusieurs faits doivent être rapprochés, lorsqu’une contradiction doit être documentée ou lorsqu’un premier signalement n’a pas abouti."),
        ]
    out=[f'<article class="seo-article"><p class="seo-lead">{html.escape(_meta(slug,title))}</p>']
    for h,p in sections:
        out.append(f'<section><h2>{html.escape(h)}</h2><p>{html.escape(p)}</p></section>')
    faq=_faq(title)
    out.append('<section class="seo-faq"><h2>Questions fréquentes</h2>')
    for q,a in faq:
        out.append(f'<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>')
    out.append('</section>')
    out.append(f'<section class="seo-cta"><h2>Besoin d’analyser votre situation ?</h2><p>Structurez les éléments utiles avant toute démarche et gardez la décision finale sous contrôle humain.</p><a class="btn-primary" href="/analyse-avis-google/">Analyser mon avis →</a></section></article>')
    return "".join(out)

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
<link rel="stylesheet" href="/assets/app.css"><link rel="stylesheet" href="/assets/public.css"><link rel="stylesheet" href="/assets/seo.css">
<script type="application/ld+json">{json.dumps(schema,ensure_ascii=False,separators=(",",":"))}</script></head><body>
<div class="marketing"><header class="public-header"><a class="public-brand" href="/"><b class="brand-mark">◆</b> Review Defense</a><nav class="public-nav"><a href="/produit/">Produit</a><a href="/comment-ca-marche/">Comment ça fonctionne</a><a href="/services/">Services</a><a href="/tarifs/">Tarifs</a><a href="/ressources/">Ressources</a><a href="/contact/">Contact</a></nav><div class="public-actions"><a class="btn-secondary" href="/app">Connexion</a><a class="btn-primary" href="/analyse-avis-google/">Analyser un avis →</a></div></header>
<main class="seo-main"><nav class="breadcrumbs"><a href="/">Accueil</a><span>›</span><a href="/{hub_slug}/">{html.escape(hub_title)}</a><span>›</span><span>{html.escape(title)}</span></nav><header class="seo-hero"><span>{html.escape(_cluster(slug).upper())}</span><h1>{html.escape(title)}</h1><p>{html.escape(meta)}</p><div class="seo-keyword">Sujet : {html.escape(keyword)}</div></header>{_body(slug,title,keyword)}<aside class="seo-related"><h2>À lire ensuite</h2><ul>{related_html}</ul></aside></main>
<footer class="public-footer"><div><a class="public-brand" href="/"><b class="brand-mark">◆</b> Review Defense</a><p>Analyse, qualification et accompagnement autour des avis en ligne.</p></div><div><b>Produit</b><a href="/?page=features">Fonctionnalités</a><a href="/?page=pricing">Tarifs</a></div><div><b>Ressources</b><a href="/?page=resources">Guides</a><a href="/analyse-avis-google/">Analyser un avis</a></div></footer></div></body></html>'''
    return doc.encode("utf-8")

def sitemap() -> bytes:
    urls=[BASE_URL+"/",BASE_URL+"/produit/",BASE_URL+"/comment-ca-marche/",BASE_URL+"/services/",BASE_URL+"/tarifs/",BASE_URL+"/ressources/",BASE_URL+"/contact/",BASE_URL+"/analyse-avis-google/"]+[BASE_URL+"/"+slug+"/" for slug,_,_ in PAGES if slug!="analyse-avis-google"]
    body="".join(f"<url><loc>{html.escape(u)}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>'.encode()

def robots() -> bytes:
    return f"User-agent: *\nAllow: /\nDisallow: /app\nDisallow: /v1/\nDisallow: /reset-password\nDisallow: /verify-email\nSitemap: {BASE_URL}/sitemap.xml\n".encode()
