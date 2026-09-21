"""Server-rendered SEO pages, sitemap and robots for Review Defense."""
from __future__ import annotations
import html, json, os
from urllib.parse import quote
from .seo_content import PAGES

BASE_URL = os.environ.get("REVIEW_DEFENSE_PUBLIC_URL", "https://review-defense.com").rstrip("/")
META = "Découvrez comment traiter un problème lié aux avis Google : vérifier la situation, identifier le motif pertinent, signaler l’avis et connaître les prochaines étapes. Analyse possible."

def _page_map():
    return {"/" + slug + "/": (slug, title, keyword) for slug, title, keyword in PAGES}

def is_seo_path(path: str) -> bool:
    return path in _page_map()

def _related(current_slug: str):
    rows = [x for x in PAGES if x[0] != current_slug]
    if current_slug == "analyse-avis-google":
        return rows[:6]
    if current_slug in {"suppression-avis-google","faux-avis-google"}:
        return [x for x in rows if any(k in x[0] for k in ("faux-avis","signaler","prouver","dossier"))][:5]
    if "signaler" in current_slug or "signalement" in current_slug:
        return [x for x in rows if "signaler" in x[0] or "suivre" in x[0] or "google-refuse" in x[0]][:5]
    if "refuse" in current_slug or "appel" in current_slug or "contester" in current_slug:
        return [x for x in rows if "refuse" in x[0] or "appel" in x[0] or "contester" in x[0]][:5]
    return rows[:5]

def _body(slug: str, title: str, keyword: str) -> str:
    service = slug in {"analyse-avis-google","service-suppression-avis-google","agence-suppression-avis-google","expert-suppression-avis-google","faire-supprimer-avis-google","prix-suppression-avis-google"}
    lead = ("Cette page présente le cadre d’analyse, de qualification et d’accompagnement autour des avis Google. "
            "Un avis négatif n’est pas automatiquement supprimable : les faits doivent être vérifiés et la décision finale appartient à la plateforme.")
    if service:
        lead = ("Review Defense aide à structurer l’analyse d’un avis, les éléments factuels et le dossier à examiner. "
                "Le service ne garantit pas la suppression : Google conserve la décision finale.")
    sections = [
        ("Réponse courte", lead),
        ("Quels éléments vérifier ?", "Vérifiez le contexte de l’avis, la réalité de la relation avec l’entreprise, les faits décrits, le caractère pertinent du contenu et les éventuelles informations sensibles. Séparez les faits vérifiables des impressions ou désaccords."),
        ("Quels éléments conserver ?", "Conservez l’URL de l’avis, des captures datées, les échanges utiles et les pièces factuelles disponibles. Pour un dossier complexe, reliez chaque élément à l’affirmation qu’il permet de vérifier ou de contester."),
        ("Comment agir ou signaler l’avis ?", "Lorsque le contenu semble relever d’un motif prévu par les règles de Google, utilisez le mécanisme de signalement approprié et présentez les éléments pertinents. Un signalement demande un examen ; il ne garantit pas une suppression."),
        ("Que faire en cas de refus ou d’absence de réponse ?", "Relisez le motif invoqué, vérifiez la cohérence des éléments présentés et examinez les voies de suivi ou de contestation proposées par la plateforme lorsqu’elles sont disponibles."),
        ("Quand demander une analyse professionnelle ?", "Une analyse structurée peut être utile lorsque plusieurs faits doivent être rapprochés, lorsqu’une contradiction doit être documentée ou lorsqu’un premier signalement n’a pas abouti. Review Defense conserve une validation humaine avant toute action externe."),
    ]
    out = [f'<article class="seo-article"><p class="seo-lead">{html.escape(lead)}</p>']
    for h,p in sections[1:]:
        out.append(f"<section><h2>{html.escape(h)}</h2><p>{html.escape(p)}</p></section>")
    faq = [
        ("Un avis Google peut-il être supprimé ?", "Cela dépend du contenu et des règles applicables. Un avis négatif ou contesté n’est pas automatiquement supprimable."),
        ("Comment constituer un dossier ?", "Réunissez l’URL, des captures datées, les faits vérifiables et les pièces permettant de comprendre le contexte."),
        ("Le signalement garantit-il la suppression ?", "Non. Le signalement demande un examen et Google prend la décision finale."),
        ("Faut-il répondre publiquement ?", "Une réponse peut apporter un contexte sans divulguer de données personnelles, mais elle ne remplace pas l’analyse du dossier."),
    ]
    out.append('<section class="seo-faq"><h2>Questions fréquentes</h2>')
    for q,a in faq:
        out.append(f"<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>")
    out.append("</section>")
    out.append(f'<section class="seo-cta"><h2>Besoin d’analyser votre situation ?</h2><p>Structurez les éléments utiles avant toute démarche.</p><a class="btn-primary" href="/analyse-avis-google/">Analyser mon avis →</a></section></article>')
    return "".join(out)

def render_page(path: str) -> bytes:
    row = _page_map()[path]
    slug, title, keyword = row
    canonical = BASE_URL + path
    related = _related(slug)
    crumbs = f'<a href="{BASE_URL}/">Accueil</a><span>›</span><span>{html.escape(title)}</span>'
    related_html = "".join(f'<li><a href="/{s}/">{html.escape(t)}</a></li>' for s,t,_ in related)
    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {"@type":"Organization","@id":BASE_URL+"/#organization","name":"Review Defense","url":BASE_URL+"/"},
            {"@type":"WebSite","@id":BASE_URL+"/#website","name":"Review Defense","url":BASE_URL+"/"},
            {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"Accueil","item":BASE_URL+"/"},
                {"@type":"ListItem","position":2,"name":title,"item":canonical}]},
            {"@type":"Service" if slug.endswith("avis-google") or slug in {"analyse-avis-google","service-suppression-avis-google","agence-suppression-avis-google","expert-suppression-avis-google","faire-supprimer-avis-google","prix-suppression-avis-google"} else "Article",
             "headline":title,"name":title,"description":META,"url":canonical,"inLanguage":"fr-FR"}
        ]
    }
    if slug not in {"analyse-avis-google","service-suppression-avis-google","agence-suppression-avis-google","expert-suppression-avis-google","faire-supprimer-avis-google","prix-suppression-avis-google"}:
        schema["@graph"][-1]["dateModified"]="2026-09-21"
        schema["@graph"][-1]["author"]={"@type":"Organization","name":"Review Defense"}
    doc=f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | Review Defense</title><meta name="description" content="{html.escape(META)}"><meta name="keywords" content="{html.escape(keyword)}">
<link rel="canonical" href="{html.escape(canonical)}"><meta property="og:type" content="article"><meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(META)}"><meta property="og:url" content="{html.escape(canonical)}">
<link rel="stylesheet" href="/assets/app.css"><link rel="stylesheet" href="/assets/public.css">
<script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script></head><body>
<div class="marketing"><header class="public-header"><a class="public-brand" href="/"><b class="brand-mark">◆</b> Review Defense</a><nav class="public-nav"><a href="/?page=features">Fonctionnalités</a><a href="/?page=how">Comment ça marche</a><a href="/?page=pricing">Tarifs</a><a href="/?page=resources">Ressources</a></nav><div class="public-actions"><a class="btn-secondary" href="/app">Connexion</a><a class="btn-primary" href="/analyse-avis-google/">Commencer →</a></div></header>
<main class="seo-main"><nav class="breadcrumbs">{crumbs}</nav><div class="seo-hero"><span class="eyebrow">GUIDE REVIEW DEFENSE</span><h1>{html.escape(title)}</h1><p>Mot-clé principal : <strong>{html.escape(keyword)}</strong></p></div>{_body(slug,title,keyword)}<aside class="seo-related"><h2>À lire ensuite</h2><ul>{related_html}</ul></aside></main>
<footer class="public-footer"><div><a class="public-brand" href="/"><b class="brand-mark">◆</b> Review Defense</a><p>Analyse, qualification et accompagnement autour des avis en ligne.</p></div><div><b>Produit</b><a href="/?page=features">Fonctionnalités</a><a href="/?page=pricing">Tarifs</a></div><div><b>Ressources</b><a href="/?page=resources">Guides</a><a href="/analyse-avis-google/">Analyser un avis</a></div></footer></div></body></html>'''
    return doc.encode("utf-8")

def sitemap() -> bytes:
    urls=[BASE_URL+"/",BASE_URL+"/?page=features",BASE_URL+"/?page=how",BASE_URL+"/?page=pricing",BASE_URL+"/?page=resources",BASE_URL+"/analyse-avis-google/"]
    urls += [BASE_URL+"/"+slug+"/" for slug,_,_ in PAGES if slug!="analyse-avis-google"]
    body="".join(f"<url><loc>{html.escape(u)}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>'.encode()

def robots() -> bytes:
    return f"User-agent: *\nAllow: /\nDisallow: /app\nDisallow: /v1/\nDisallow: /reset-password\nDisallow: /verify-email\nSitemap: {BASE_URL}/sitemap.xml\n".encode()
