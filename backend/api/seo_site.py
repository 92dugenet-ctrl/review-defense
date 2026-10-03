"""Server-rendered SEO pages for Review Defense.

V6.40 integrates the supplied SEO architecture as crawlable public routes,
including canonical URLs, sitemap, robots.txt, breadcrumbs and JSON-LD.
"""
from __future__ import annotations
import html, json, os
from urllib.parse import urljoin

SITE_MODIFIED = "2026-09-23"

_RAW = [('suppression-avis-google',
    "Suppression d'avis Google : guide complet",
    'suppression avis Google',
    'Pillar / suppression'),
    ('peut-on-supprimer-un-avis-google',
    'Peut-on supprimer un avis Google ?',
    'peut-on supprimer un avis Google',
    'Pillar / suppression'),
    ('comment-supprimer-un-avis-google',
    'Comment supprimer un avis Google ?',
    'comment supprimer un avis Google',
    'Pillar / suppression'),
    ('faux-avis-google',
    'Faux avis Google : comment les reconnaître et les signaler ?',
    'faux avis Google',
    'Faux avis'),
    ('comment-reconnaitre-un-faux-avis-google',
    'Comment reconnaître un faux avis Google ?',
    'reconnaître faux avis Google',
    'Faux avis'),
    ('comment-prouver-qu-un-avis-google-est-faux',
    'Comment prouver qu’un avis Google est faux ?',
    'prouver faux avis Google',
    'Faux avis'),
    ('comment-constituer-un-dossier-contre-un-faux-avis-google',
    'Comment constituer un dossier contre un faux avis Google ?',
    'dossier faux avis Google',
    'Faux avis'),
    ('avis-google-faux-client',
    'Avis Google d’un faux client : que faire ?',
    'avis Google faux client',
    'Cas concrets / longue traîne'),
    ('avis-google-personne-jamais-cliente',
    'Avis Google d’une personne qui n’a jamais été cliente : que faire ?',
    'avis Google personne jamais cliente',
    'Cas concrets / longue traîne'),
    ('avis-google-concurrent',
    'Avis Google publié par un concurrent : que faire ?',
    'avis Google concurrent',
    'Cas concrets / longue traîne'),
    ('avis-google-ancien-salarie',
    'Avis Google publié par un ancien salarié : que faire ?',
    'avis Google ancien salarié',
    'Cas concrets / longue traîne'),
    ('avis-google-mensonger',
    'Avis Google mensonger : que faire ?',
    'avis Google mensonger',
    'Cas concrets / longue traîne'),
    ('avis-google-accusation-mensongere',
    'Avis Google avec une accusation mensongère : que faire ?',
    'accusation mensongère avis Google',
    'Cas concrets / longue traîne'),
    ('avis-google-diffamatoire',
    'Avis Google diffamatoire : que peut-on faire ?',
    'avis Google diffamatoire',
    'Éditorial'),
    ('avis-google-insultant',
    'Avis Google insultant : comment le signaler ?',
    'avis Google insultant',
    'Cas concrets / longue traîne'),
    ('avis-google-discriminatoire',
    'Avis Google avec des propos discriminatoires : que faire ?',
    'avis Google discriminatoire',
    'Cas concrets / longue traîne'),
    ('avis-google-hors-sujet',
    'Avis Google hors sujet : que faire ?',
    'avis Google hors sujet',
    'Cas concrets / longue traîne'),
    ('avis-google-informations-personnelles',
    'Avis Google contenant des informations personnelles : que faire ?',
    'avis Google informations personnelles',
    'Cas concrets / longue traîne'),
    ('avis-google-mauvais-etablissement',
    'Avis Google publié sur le mauvais établissement : que faire ?',
    'avis Google mauvais établissement',
    'Cas concrets / longue traîne'),
    ('avis-google-fausse-identite',
    'Avis Google publié sous une fausse identité : que faire ?',
    'avis Google fausse identité',
    'Cas concrets / longue traîne'),
    ('plusieurs-faux-avis-google',
    'Plusieurs faux avis Google : que faire ?',
    'plusieurs faux avis Google',
    'Cas concrets / longue traîne'),
    ('plusieurs-comptes-google-avis-similaires',
    'Plusieurs comptes Google publient des avis similaires : que faire ?',
    'avis Google comptes similaires',
    'Cas concrets / longue traîne'),
    ('avis-google-argent-ou-avantage',
    'Avis Google en échange d’argent ou d’un avantage : que faire ?',
    'avis Google contre argent',
    'Cas concrets / longue traîne'),
    ('avis-google-contenu-promotionnel',
    'Avis Google avec contenu promotionnel : que faire ?',
    'avis Google promotionnel',
    'Cas concrets / longue traîne'),
    ('avis-google-chantage',
    'Avis Google qui fait du chantage : que faire ?',
    'chantage avis Google',
    'Cas concrets / longue traîne'),
    ('avis-google-menace',
    'Avis Google qui menace une entreprise : que faire ?',
    'menace avis Google',
    'Cas concrets / longue traîne'),
    ('avis-google-conflit-client',
    'Avis Google après un conflit client : que faire ?',
    'avis Google conflit client',
    'Cas concrets / longue traîne'),
    ('avis-google-litige',
    'Avis Google après un litige : que faire ?',
    'avis Google litige',
    'Cas concrets / longue traîne'),
    ('avis-google-ancien-client',
    'Avis Google publié par un ancien client : peut-il être supprimé ?',
    'avis Google ancien client',
    'Cas concrets / longue traîne'),
    ('signaler-un-avis-google',
    'Comment signaler un avis Google ? Guide complet',
    'signaler avis Google',
    'Signalement'),
    ('comment-signaler-un-avis-google-etape-par-etape',
    'Comment signaler un avis Google étape par étape ?',
    'signaler avis Google étape par étape',
    'Signalement'),
    ('comment-signaler-un-avis-google-google-maps',
    'Comment signaler un avis Google depuis Google Maps ?',
    'signaler avis Google Maps',
    'Signalement'),
    ('comment-signaler-un-avis-google-business-profile',
    'Comment signaler un avis Google depuis Google Business Profile ?',
    'signaler avis Google Business Profile',
    'Signalement'),
    ('comment-signaler-plusieurs-avis-google',
    'Comment signaler plusieurs avis Google ?',
    'signaler plusieurs avis Google',
    'Signalement'),
    ('comment-preparer-un-dossier-de-signalement-d-un-avis-google',
    'Comment préparer un dossier de signalement d’un avis Google ?',
    'dossier signalement avis Google',
    'Signalement'),
    ('combien-de-temps-suppression-avis-google',
    'Combien de temps faut-il pour supprimer un avis Google ?',
    'délai suppression avis Google',
    'Procédure'),
    ('comment-savoir-si-google-a-accepte-mon-signalement',
    'Comment savoir si Google a accepté mon signalement d’avis ?',
    'savoir si Google a accepté signalement avis',
    'Procédure'),
    ('comment-suivre-un-signalement-avis-google',
    'Comment suivre un signalement d’avis Google ?',
    'suivre signalement avis Google',
    'Procédure'),
    ('que-faire-si-google-ne-repond-pas-a-mon-signalement',
    'Que faire si Google ne répond pas à mon signalement d’avis ?',
    'Google ne répond pas signalement avis',
    'Procédure'),
    ('que-faire-quand-google-refuse-de-supprimer-un-avis',
    'Que faire quand Google refuse de supprimer un avis ?',
    'Google refuse supprimer avis',
    'Refus / appel'),
    ('pourquoi-mon-avis-google-reste-en-ligne',
    'Pourquoi mon avis Google reste en ligne ?',
    'pourquoi avis Google reste en ligne',
    'Refus / appel'),
    ('google-refuse-de-supprimer-mon-faux-avis-que-faire',
    'Google refuse de supprimer mon faux avis : que faire ?',
    'Google refuse faux avis',
    'Refus / appel'),
    ('comment-faire-appel-apres-refus-suppression-avis-google',
    'Comment faire appel après un refus de suppression d’un avis Google ?',
    'appel suppression avis Google',
    'Refus / appel'),
    ('comment-contester-une-decision-concernant-un-avis-google',
    'Comment contester une décision concernant un avis Google ?',
    'contester décision avis Google',
    'Refus / appel'),
    ('avis-google-signalement-ou-reponse-publique',
    'Avis Google : signalement ou réponse publique ?',
    'répondre ou signaler avis Google',
    'Éditorial'),
    ('comment-faire-supprimer-un-avis-google-qui-me-semble-faux',
    'Comment faire supprimer un avis Google qui me semble faux ?',
    'faire supprimer avis Google faux',
    'Cas concrets / longue traîne'),
    ('que-faire-si-quelqu-un-a-laisse-un-avis-sans-etre-client',
    'Que faire si quelqu’un a laissé un avis Google sans être client ?',
    'avis Google sans être client',
    'Cas concrets / longue traîne'),
    ('google-refuse-de-supprimer-mon-faux-avis',
    'Google refuse de supprimer mon faux avis : que faire ?',
    'Google refuse de supprimer mon faux avis',
    'Refus / appel'),
    ('pourquoi-mon-avis-google-reste-en-ligne-conversationnel',
    'Pourquoi mon avis Google reste en ligne ?',
    'pourquoi mon avis Google reste en ligne',
    'Refus / appel'),
    ('comment-savoir-si-un-avis-google-peut-etre-supprime',
    'Comment savoir si un avis Google peut être supprimé ?',
    'savoir si avis Google peut être supprimé',
    'Cas concrets / longue traîne'),
    ('que-faire-si-un-client-me-menace-avec-un-avis-google',
    'Que faire si un client me menace avec un avis Google ?',
    'client menace avis Google',
    'Cas concrets / longue traîne'),
    ('peut-on-supprimer-un-avis-google-diffamatoire',
    'Peut-on supprimer un avis Google diffamatoire ?',
    'supprimer avis Google diffamatoire',
    'Cas concrets / longue traîne'),
    ('comment-faire-supprimer-plusieurs-faux-avis-google',
    'Comment faire supprimer plusieurs faux avis Google ?',
    'supprimer plusieurs faux avis Google',
    'Cas concrets / longue traîne'),
    ('avis-google-menace-entreprise',
    'Avis Google qui menace une entreprise : que faire ?',
    'avis Google menace entreprise',
    'Cas concrets / longue traîne'),
    ('avis-google-propos-discriminatoires',
    'Avis Google avec propos discriminatoires : que faire ?',
    'avis Google propos discriminatoires',
    'Cas concrets / longue traîne'),
    ('avis-google-argent-avantage',
    'Avis Google en échange d’argent ou d’un avantage : que faire ?',
    'avis Google argent avantage',
    'Cas concrets / longue traîne'),
    ('faire-supprimer-avis-google',
    'Faire supprimer un avis Google | Analyse et accompagnement',
    'faire supprimer avis Google',
    'Services'),
    ('service-suppression-avis-google',
    'Service de suppression d’avis Google | Analyse et accompagnement',
    'service suppression avis Google',
    'Services'),
    ('agence-suppression-avis-google',
    'Agence de suppression d’avis Google | Analyse et accompagnement',
    'agence suppression avis Google',
    'Services'),
    ('prix-suppression-avis-google',
    'Prix suppression avis Google | Analyse et accompagnement',
    'prix suppression avis Google',
    'Services'),
    ('analyse-avis-google',
    'Analyse d’avis Google | Analyse et accompagnement',
    'analyse avis Google',
    'Services'),
    ('expert-suppression-avis-google',
    'Expert suppression d’avis Google | Analyse et accompagnement',
    'expert suppression avis Google',
    'Services')]
_SERVICE_SLUGS={x[0] for x in _RAW[-6:]}

def _base(): return os.environ.get("REVIEW_DEFENSE_PUBLIC_URL","https://review-defense.com").rstrip("/")+"/"
def _url(p): return urljoin(_base(),p.lstrip("/"))
def _e(x): return html.escape(str(x),quote=True)
def _pages():
    out=[]; title_counts={}
    for s,t,k,c in _RAW:
        title_counts[t]=title_counts.get(t,0)+1
        occurrence=title_counts[t]
        title=t if occurrence==1 else f"{t} | Cas concret {occurrence}"
        out.append({"path":f"/{s}/","title":title,"h1":title,"keyword":k,"cluster":c,"service":s in _SERVICE_SLUGS,
                    "description":f"{title} : vérifiez les faits, identifiez le motif pertinent, préparez les éléments utiles et suivez les prochaines étapes. "+("Aucune garantie de suppression : Google prend la décision finale." if s in _SERVICE_SLUGS else "Guide pratique et points de vigilance.")})
    return out
def _related(page,pages):
    hubs={
        "Pillar / suppression":"/suppression-avis-google/",
        "Faux avis":"/faux-avis-google/",
        "Signalement":"/signaler-un-avis-google/",
        "Refus / appel":"/que-faire-quand-google-refuse-de-supprimer-un-avis/",
        "Services":"/analyse-avis-google/",
        "Cas concrets / longue traîne":"/suppression-avis-google/",
        "Éditorial":"/suppression-avis-google/",
        "Procédure":"/signaler-un-avis-google/",
    }
    preferred={
                "Pillar / suppression":["/peut-on-supprimer-un-avis-google/",
            "/comment-supprimer-un-avis-google/",
            "/faux-avis-google/",
            "/signaler-un-avis-google/"],
                "Faux avis":["/comment-reconnaitre-un-faux-avis-google/",
            "/comment-prouver-qu-un-avis-google-est-faux/",
            "/comment-constituer-un-dossier-contre-un-faux-avis-google/",
            "/signaler-un-avis-google/"],
                "Signalement":["/comment-signaler-un-avis-google-etape-par-etape/",
            "/comment-signaler-un-avis-google-google-maps/",
            "/comment-signaler-un-avis-google-business-profile/",
            "/comment-suivre-un-signalement-avis-google/"],
                "Refus / appel":["/pourquoi-mon-avis-google-reste-en-ligne/",
            "/comment-faire-appel-apres-refus-suppression-avis-google/",
            "/comment-contester-une-decision-concernant-un-avis-google/",
            "/analyse-avis-google/"],
                "Services":["/analyse-avis-google/",
            "/faire-supprimer-avis-google/",
            "/service-suppression-avis-google/",
            "/prix-suppression-avis-google/"],
    }
    by={p["path"]:p for p in pages}; out=[]
    hub=hubs.get(page["cluster"])
    if hub and hub!=page["path"] and hub in by: out.append(by[hub])
    for path in preferred.get(page["cluster"],[]):
        if len(out)>=4: break
        if path!=page["path"] and path in by and by[path] not in out: out.append(by[path])
    for p in pages:
        if len(out)>=5: break
        if p["path"]!=page["path"] and p["cluster"]==page["cluster"] and p not in out: out.append(p)
    return out[:5]
def _sections(page):
    title=page["title"]; keyword=page["keyword"]; cluster=page["cluster"]
    context={
      "Faux avis":"Examinez les indices disponibles sans transformer une suspicion en certitude : contenu, contexte de la relation, chronologie, répétitions éventuelles et éléments qui peuvent être vérifiés.",
      "Signalement":"Un signalement doit correspondre au motif réellement observable dans le contenu publié. Préparez les faits et les pièces utiles avant d’utiliser la procédure de la plateforme.",
      "Refus / appel":"Un refus ne signifie pas nécessairement que tous les éléments du dossier ont été examinés comme vous le souhaiteriez. Relisez la décision, vérifiez le motif et documentez la suite.",
      "Procédure":"La démarche doit être suivie dans l’ordre : identifier la situation, rassembler les éléments utiles, utiliser la procédure adaptée puis conserver la trace de la décision.",
      "Services":"Le service porte sur l’analyse, la qualification, la préparation et le suivi. Il ne transforme pas une hypothèse en fait établi et ne garantit pas une suppression.",
      "Cas concrets / longue traîne":"La réponse dépend des faits précis du dossier. La formulation du problème ne suffit pas à établir qu’un avis est faux, illicite ou contraire aux règles de la plateforme.",
      "Éditorial":"Deux démarches peuvent être complémentaires : répondre publiquement lorsque cela est utile et signaler lorsque le contenu semble relever d’un motif prévu par les règles.",
      "Pillar / suppression":"Un avis négatif n’est pas automatiquement supprimable. La première étape consiste à vérifier le contenu exact, son contexte et le motif pertinent avant toute démarche.",
    }.get(cluster,"Commencez par distinguer les faits observables, les éléments à vérifier et les options réellement disponibles.")
    if page["service"]:
        hs=["À quoi sert ce service ?","Ce qui est analysé","Comment le dossier est préparé","Validation et suivi","Limites du service"]
        elif cluster=="Signalement": hs=["Réponse courte",
        "Dans quels cas signaler ?",
        "Identifier le motif pertinent",
        "Préparer les éléments",
        "Effectuer et suivre le signalement",
        "Que faire après la décision ?",
        "Quand demander une analyse ?"]
        elif cluster=="Refus / appel": hs=["Réponse courte",
        "Comprendre la décision",
        "Vérifier le dossier",
        "Conserver les éléments utiles",
        "Préparer une éventuelle suite",
        "Que faire si Google ne répond pas ?",
        "Quand demander une analyse ?"]
        elif cluster=="Faux avis": hs=["Réponse courte",
        "Dans quels cas la situation peut-elle se présenter ?",
        "Quels indices vérifier ?",
        "Comment documenter les faits ?",
        "Comment signaler la situation ?",
        "Que faire si le signalement échoue ?",
        "Quand demander une analyse ?"]
        elif cluster=="Pillar / suppression": hs=["Réponse courte",
        "Dans quels cas la question se pose ?",
        "Quels éléments vérifier ?",
        "Quels éléments factuels conserver ?",
        "Quelles démarches sont possibles ?",
        "Que faire en cas de refus ou d’absence de réponse ?",
        "Quand demander une analyse professionnelle ?"]
        else: hs=["Réponse courte",
        "Dans quels cas cette situation peut-elle se présenter ?",
        "Quels éléments faut-il vérifier ?",
        "Quels éléments conserver ?",
        "Quelles démarches sont possibles ?",
        "Que faire si Google refuse ou ne répond pas ?",
        "Quand demander une analyse professionnelle ?"]
    out=[]
    for h in hs:
        if h=="Réponse courte":
            t=f"Pour « {title} », commencez par vérifier les faits et le contenu exact de l’avis. {context}"
        elif "motif" in h.lower():
            t=f"Le mot-clé « {keyword} » décrit une intention de recherche, pas une conclusion juridique ou factuelle. Le motif retenu doit correspondre à ce qui est réellement visible dans l’avis et aux règles applicables."
        elif "indices" in h.lower():
            t="Un indice isolé ne permet pas toujours de conclure. Comparez les affirmations de l’avis avec les éléments dont vous disposez et notez précisément ce qui est vérifiable, incertain ou contradictoire."
        elif "document" in h.lower() or "éléments" in h.lower() or "dossier" in h.lower():
            t="Conservez l’URL de l’avis, une capture datée, les échanges utiles, les dates et les pièces factuelles permettant de vérifier les affirmations. Évitez d’exposer des données personnelles qui ne sont pas nécessaires au dossier."
        elif "signal" in h.lower() or "démarches" in h.lower() or "options" in h.lower():
            t="Lorsque la situation semble relever d’un motif prévu par la plateforme, utilisez la procédure correspondante et gardez une trace de la demande. Le signalement déclenche un examen ; il ne garantit pas une suppression."
        elif "refus" in h.lower() or "suite" in h.lower() or "décision" in h.lower():
            t="Relisez le motif communiqué, vérifiez les éléments déjà transmis et identifiez les voies de suivi ou de contestation effectivement proposées. Une nouvelle démarche doit apporter une information pertinente, pas simplement répéter la précédente."
        elif "service" in h.lower() or "processus" in h.lower() or "prépar" in h.lower():
            t="Review Defense structure le dossier autour de l’analyse, de la qualification, des preuves, de la décision humaine et du suivi. Les étapes importantes restent explicites et traçables."
        elif "validation" in h.lower() or "suivi" in h.lower():
            t="Les étapes importantes nécessitent une validation humaine explicite. L’outil prépare les informations et conserve une trace du dossier ; il n’exécute pas automatiquement une action Google."
        else:
            t=context
        out.append((h,t))
    return out
def _faq_items(page):
    return [
            ("Peut-on supprimer un avis dans cette situation ?",
          "Cela dépend du contenu, du contexte et du motif applicable. Un avis négatif ou contesté n’est pas automatiquement supprimable."),
            ("Quels éléments faut-il vérifier ?",
          "Le texte de l’avis, son contexte, les faits disponibles, les dates utiles et les éléments permettant de confronter les affirmations à des faits."),
            ("Comment signaler l’avis ?",
          "Lorsque le contenu semble relever d’un motif prévu par la plateforme, utilisez la procédure de signalement correspondante et conservez les éléments transmis."),
            ("Que faire si Google refuse ?",
          "Relisez le motif communiqué, vérifiez le dossier et examinez les voies de suivi ou de contestation disponibles."),
      ("La suppression est-elle garantie ?", "Non. La plateforme concernée conserve la décision finale.")
    ]

def _schema(page):
    c=_url(page["path"])
    graph=[
      {"@type":"Organization","@id":_url("/#organization"),"name":"Review Defense","url":_url("/")},
      {"@type":"WebSite","@id":_url("/#website"),"name":"Review Defense","url":_url("/"),"publisher":{"@id":_url("/#organization")}},
            {"@type":"BreadcrumbList",
          "itemListElement":[{"@type":"ListItem",
          "position":1,
          "name":"Accueil",
          "item":_url("/")},
          {"@type":"ListItem",
          "position":2,
          "name":page["cluster"]},
          {"@type":"ListItem",
          "position":3,
          "name":page["h1"],
          "item":c}]}
    ]
        graph.append({"@type":"Service" if page["service"] else "Article",
        "@id":c+"#content",
        "name":page["h1"],
        "headline":page["h1"],
        "description":page["description"],
        "url":c,
        "dateModified":SITE_MODIFIED,
        "mainEntityOfPage":{"@type":"WebPage",
        "@id":c},
        "author":{"@type":"Organization",
        "name":"Review Defense"},
        "publisher":{"@type":"Organization",
        "name":"Review Defense",
        "url":_url("/")}})
        graph.append({"@type":"FAQPage",
        "mainEntity":[{"@type":"Question",
        "name":q,
        "acceptedAnswer":{"@type":"Answer",
        "text":a}} for q,
        a in _faq_items(page)]})
    return {"@context":"https://schema.org","@graph":graph}
def _analysis_html():
    title="Analyse d’avis Google | Review Defense"
    description="Analysez une situation liée à un avis Google, structurez les faits disponibles et préparez un dossier avec validation humaine."
    schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Organization",
                    "@id": _url("/#organization"),
                    "name": "Review Defense",
                    "url": _url("/")
                },
                {
                    "@type": "WebSite",
                    "@id": _url("/#website"),
                    "name": "Review Defense",
                    "url": _url("/"),
                    "publisher": {
                        "@id": _url("/#organization")
                    }
                },
                {
                    "@type": "Service",
                    "name": title,
                    "description": description,
                    "url": _url("/analyse-avis-google/"),
                    "provider": {
                        "@id": _url("/#organization")
                    }
                }
            ]
        },
        ensure_ascii=False,
        separators=(",", ":")
    )
    script="""<script>(function(){window.dataLayer=window.dataLayer||[];var f=document.getElementById("rd-analysis-form");if(f){var started=false;f.addEventListener("input",function(){if(!started){started=true;window.dataLayer.push({event:"analysis_start",page:location.pathname});}});f.addEventListener("submit",function(e){e.preventDefault();window.dataLayer.push({event:"analysis_submit",page:location.pathname});location.href="/app";});}})();</script>"""
    return (
        f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{_e(title)}</title><meta name="description" content="{_e(description)}">'''
        f'''<meta name="robots" content="index,follow"><link rel="canonical" href="{_e(_url("/analyse-avis-google/"))}"><meta property="og:type" content="website"><meta property="og:title" content="{_e(title)}">'''
        f'''<meta property="og:description" content="{_e(description)}"><meta property="og:url" content="{_e(_url("/analyse-avis-google/"))}"><link rel="stylesheet" href="/assets/app.css"><link rel="stylesheet" href="/assets/public.css">'''
        f'''<script type="application/ld+json">{schema}</script></head><body><div class="marketing"><header class="public-header"><a class="public-brand" href="/"><b class="brand-mark">◆</b> Review Defense</a>'''
        f'''<nav class="public-nav"><a href="/produit/">Produit</a><a href="/comment-ca-marche/">Comment ça fonctionne</a><a href="/services/">Services</a><a href="/tarifs/">Tarifs</a><a href="/ressources/">Ressources</a>'''
        f'''<a href="/contact/">Contact</a></nav><div class="public-actions"><a class="btn-secondary" href="/app">Connexion</a></div></header><main class="rd-analysis-main"><section class="rd-home-hero">'''
        f'''<div class="rd-container rd-hero-grid"><div class="rd-hero-copy"><span class="rd-eyebrow-pill">ANALYSE D’AVIS GOOGLE</span><h1>Commencez par les faits.<br><span>Préparez la suite.</span>'''
        f'''</h1><p class="rd-hero-lead">Décrivez la situation, les éléments disponibles et ce que vous souhaitez vérifier. Review Defense structure l’analyse ; les décisions importantes restent humaines.</p>'''
        f'''<div class="rd-trust-line"><span>✓ Qualification</span><span>✓ Preuves</span><span>✓ Traçabilité</span><span>✓ Validation humaine</span></div></div><div class="rd-analysis-card"><div class="rd-card-kicker">ÉTAPE 01 · ANALYSE</div>'''
        f'''<h2>Décrivez votre situation</h2><p>Ne partagez ici que les informations nécessaires à l’analyse.</p><form id="rd-analysis-form"><label>URL de l’avis Google <span>(optionnel)</span>'''
        f'''<input name="review_url" type="url" placeholder="https://www.google.com/..."></label><label>Type de situation<select name="situation"><option>Avis que je souhaite examiner</option>'''
        f'''<option>Suspicion de faux avis</option><option>Signalement refusé</option><option>Plusieurs avis à examiner</option><option>Autre situation</option></select></label><label>Résumé des faits<textarea name="summary" rows="7" required placeholder="Quels faits souhaitez-vous vérifier ?">'''
        f'''</textarea></label><button class="btn-primary rd-btn-lg" type="submit">Commencer l’analyse →</button><small>La soumission démarre le parcours Review Defense. Aucune action Google n’est exécutée automatiquement.</small>'''
        f'''</form></div></div></section><section class="rd-section rd-light"><div class="rd-container rd-value-grid"><article class="rd-value-card"><span>01</span><h2>Analyse</h2><p>Identifier les affirmations, faits et points à vérifier.</p>'''
        f'''</article><article class="rd-value-card"><span>02</span><h2>Décision</h2><p>Documenter ce qui est établi, incertain ou à confirmer.</p></article><article class="rd-value-card"><span>03</span>'''
        f'''<h2>Préparation</h2><p>Structurer les éléments utiles avant toute démarche externe.</p></article><article class="rd-value-card"><span>04</span><h2>Validation</h2><p>Une action importante reste soumise à une validation humaine explicite.</p>'''
        f'''</article></div></section><section class="rd-final-cta"><div class="rd-container"><span class="rd-eyebrow">GARDEZ LE CONTRÔLE</span><h2>L’automatisation prépare.<br><span>L’humain décide.</span>'''
        f'''</h2><p>La décision finale appartient à la plateforme concernée.</p><div class="seo-faq"><h2>Questions fréquentes</h2><details><summary>La suppression est-elle garantie ?</summary>'''
        f'''<p>Non. Review Defense prépare et structure les informations ; aucune suppression n’est garantie et la décision finale appartient à la plateforme concernée.</p></details><details><summary>Que se passe-t-il après l’analyse ?</summary>'''
        f'''<p>Le dossier peut être qualifié, documenté et soumis aux étapes de validation humaine prévues par le workflow.</p></details></div></div></section></main><footer class="public-footer">'''
        f'''<div><a class="public-brand" href="/"><b class="brand-mark">◆</b> Review Defense</a><p>Analyse, qualification et suivi des dossiers liés aux avis en ligne.</p></div><div><b>Produit</b>'''
        f'''<a href="/produit/">Fonctionnalités</a><a href="/tarifs/">Tarifs</a></div><div><b>Ressources</b><a href="/ressources/">Guides</a><a href="/analyse-avis-google/">Analyser un avis</a>'''
        f'''</div><div><b>Sécurité</b><span>Validation humaine</span><span>Traçabilité complète</span></div></footer></div>{script}</body></html>'''
    )
COMMERCIAL={
  "/":{"title":"Review Defense | Analyse et défense de votre réputation",
     "description":"Analysez vos avis Google, documentez les éléments utiles et préparez vos dossiers avec une validation humaine.",
     "eyebrow":"REPUTATION INTELLIGENCE · POUR LES ENTREPRISES",
     "h1":"Analysez vos avis Google.<br><span>Préparez vos dossiers.</span><br>Gardez le contrôle.",
     "lead":"Review Defense aide les entreprises à analyser, qualifier, documenter et suivre les situations liées aux avis Google.",
     "sections":[("Analyse structurée",
     "Examinez le contenu, le contexte et les éléments qui méritent une vérification."),
     ("Preuves documentées",
     "Reliez les éléments disponibles aux affirmations et conservez une trace claire."),
     ("Décision humaine",
     "Les étapes importantes restent soumises à une validation humaine explicite.")]},
  "/produit/":{"title":"Produit Review Defense | Analyse, preuves et traçabilité",
     "description":"Une console B2B pour analyser les avis, structurer les preuves, suivre les dossiers et conserver une traçabilité complète.",
     "eyebrow":"LE PRODUIT",
     "h1":"Une console B2B pour<br><span>des dossiers maîtrisés.</span>",
     "lead":"Une expérience opérationnelle qui rassemble analyse, preuves, dossiers, validations et suivi.",
     "sections":[("Analyse",
     "Qualifiez les éléments qui nécessitent une vérification."),
     ("Preuves",
     "Associez les éléments factuels au dossier concerné."),
     ("Workflow contrôlé",
     "Analyse → décision → gel → validation humaine → préparation contrôlée."),
     ("Audit",
     "Conservez une chronologie lisible des décisions et événements importants."),
     ("Sécurité",
     "Contrôle d’accès, MFA et garde-fous serveur.")]},
  "/comment-ca-marche/":{"title":"Comment ça fonctionne | Review Defense",
     "description":"Découvrez le workflow Review Defense : analyse, décision, gel, validation humaine et préparation contrôlée.",
     "eyebrow":"LE WORKFLOW",
     "h1":"Une chaîne de contrôle<br><span>simple à suivre.</span>",
     "lead":"L’automatisation prépare et structure. Les décisions importantes restent explicitement validées par un humain.",
     "sections":[("01 · Analyse",
     "Identifier les éléments à examiner."),
     ("02 · Décision",
     "Documenter le raisonnement et les points à vérifier."),
     ("03 · Gel",
     "Fixer le dossier avant toute étape contrôlée."),
     ("04 · Human Approval",
     "Valider explicitement la suite."),
     ("05 · Préparation contrôlée",
     "Préparer une démarche externe sans exécution automatique.")]},
  "/services/":{"title":"Services | Review Defense",
     "description":"Analyse d’avis, préparation de dossiers et accompagnement structuré pour les situations liées à votre réputation en ligne.",
     "eyebrow":"SERVICES",
     "h1":"De l’analyse au dossier<br><span>prêt à être examiné.</span>",
     "lead":"Un accompagnement structuré pour qualifier les situations, documenter les faits et suivre les démarches.",
     "sections":[("Analyse d’avis",
     "Examiner le contenu, le contexte et les éléments disponibles."),
     ("Préparation de dossier",
     "Organiser faits, preuves et chronologie."),
     ("Suivi",
     "Conserver l’historique des décisions et événements."),
     ("Validation humaine",
     "Aucune action externe importante sans validation explicite."),
     ("Limites",
     "Aucun résultat déterminé n’est garanti.")]},
  "/tarifs/":{"title":"Tarifs | Review Defense",
     "description":"Découvrez les offres Review Defense pour surveiller, analyser et structurer vos dossiers de réputation.",
     "eyebrow":"TARIFS",
     "h1":"Des offres adaptées<br><span>à votre organisation.</span>",
     "lead":"Des niveaux de service conçus pour différents volumes et organisations.",
     "sections":[("Monitoring · à partir de 29 € / mois",
     "Surveillance, alertes et tableau de bord."),
     ("Professional · à partir de 79 € / mois",
     "Analyse avancée, dossiers, preuves et suivi."),
     ("Business · à partir de 149 € / mois",
     "Multi-établissements, rôles et rapports."),
     ("Enterprise · sur devis",
     "Besoins organisationnels spécifiques.")]},
  "/ressources/":{"title":"Ressources | Review Defense",
     "description":"Guides et ressources sur les avis Google, les preuves, le signalement et le suivi des dossiers.",
     "eyebrow":"RESSOURCES",
     "h1":"Comprendre les avis Google.<br><span>Décider avec méthode.</span>",
     "lead":"Le centre de ressources relie les guides SEO aux parcours commerciaux et à l’analyse.",
     "sections":[("Faux avis",
     "Identifier les éléments à vérifier."),
     ("Signalement",
     "Comprendre les étapes et les motifs."),
     ("Refus et suites",
     "Documenter une décision et examiner les options disponibles."),
     ("Analyse professionnelle",
     "Structurer un dossier lorsque plusieurs faits doivent être rapprochés.")]},
  "/contact/":{"title":"Contact | Review Defense",
     "description":"Contactez Review Defense pour une question, une démonstration ou un accompagnement sur votre dossier.",
     "eyebrow":"CONTACT",
     "h1":"Parlons de votre<br><span>situation.</span>",
     "lead":"Une question produit, une demande de démonstration ou un besoin commercial ?",
     "sections":[("Démonstration",
     "Découvrez le produit et son workflow."),
     ("Question commerciale",
     "Échangez sur les offres et besoins spécifiques."),
     ("Dossier",
     "Présentez les éléments disponibles pour cadrer une analyse.")]},
}

def _services_html():
    styles = """
    :root{--svc-ink:#111820;
    --svc-muted:#647487;
    --svc-line:#dfe5eb;
    --svc-blue:#0878ee;
    --svc-max:1480px}
    
    .svc-page{background:#fff;
    color:var(--svc-ink);
    overflow:hidden}
    .svc-container{width:min(var(--svc-max),100%);
    margin:auto;
    padding:0 clamp(22px,4vw,64px)}
    
        .svc-hero{padding:clamp(80px,
        11vw,
        150px) 0 100px;
    background:linear-gradient(180deg,
        #fff,#f7f9fb)}
    .svc-hero-grid{display:grid;
    grid-template-columns:1.02fr .98fr;
    gap:clamp(45px,7vw,110px);
    align-items:center}
    
    .svc-eyebrow{display:inline-flex;
    align-items:center;
    gap:10px;
    color:var(--svc-blue);
    font-size:12px;
    letter-spacing:.13em;
    font-weight:800}
    .svc-eyebrow:before{content:"";
    width:28px;
    height:1px;
    background:currentColor}
    
        .svc-hero h1{font-size:clamp(56px,
        7.3vw,
        112px);
    line-height:.91;
    letter-spacing:-.065em;
    margin:22px 0 30px;
    max-width:850px}
    .svc-hero h1 span,.svc-intro h2 span,.svc-cta h2 span{color:#6d7b8b}
    
        .svc-lead{font-size:clamp(19px,
        2vw,
        25px);
    line-height:1.45;
    color:var(--svc-muted);
    max-width:720px;
    margin:0}
    .svc-hero-actions{display:flex;
    gap:14px;
    flex-wrap:wrap;
    margin-top:38px}
    .svc-hero-note{display:flex;
    gap:22px;
    flex-wrap:wrap;
    margin-top:38px;
    color:#465463;
    font-size:14px}
    
    .svc-btn{display:inline-flex;
    align-items:center;
    justify-content:center;
    border-radius:999px;
    padding:14px 22px;
    font-size:14px;
    font-weight:750;
    text-decoration:none}
    .svc-btn-primary{background:#111820;
    color:#fff}
    .svc-btn-secondary{border:1px solid #cfd7df;
    color:#111820;
    background:#fff}
    
    .svc-visual{position:relative;
    min-height:570px;
    border-radius:34px;
    background:#eef2f5;
    overflow:hidden;
    padding:30px;
    box-shadow:0 35px 80px rgba(23,44,64,.12)}
    .svc-visual:before{content:"";
    position:absolute;
    width:330px;
    height:330px;
    border-radius:50%;
    background:#dcecff;
    right:-110px;
    top:-110px}
    
    .svc-window{position:relative;
    z-index:1;
    height:100%;
    min-height:510px;
    background:#fff;
    border:1px solid #e0e6eb;
    border-radius:24px;
    box-shadow:0 22px 60px rgba(27,43,58,.13);
    overflow:hidden}
    .svc-window-top{height:54px;
    border-bottom:1px solid #e8edf1;
    display:flex;
    align-items:center;
    gap:8px;
    padding:0 18px;
    font-size:12px;
    color:#718091}
    .svc-dot{width:8px;
    height:8px;
    border-radius:50%;
    background:#d5dce2}
    .svc-window-title{margin-left:8px;
    font-weight:700;
    color:#1c2731}
    
    .svc-window-body{display:grid;
    grid-template-columns:145px 1fr;
    height:calc(100% - 54px)}
    .svc-sidebar{background:#f7f8fa;
    padding:22px 15px;
    display:flex;
    flex-direction:column;
    gap:10px;
    font-size:11px;
    color:#728091}
    .svc-sidebar strong{color:#111820;
    margin-bottom:15px;
    font-size:12px}
    .svc-sidebar .active{background:#e7f2ff;
    color:#0878ee;
    border-radius:10px;
    padding:9px}
    
    .svc-dashboard{padding:28px}
    .svc-dashboard small,.svc-art-meta{font-size:10px;
    letter-spacing:.12em;
    color:#83909c;
    font-weight:800}
    .svc-dashboard h3{font-size:28px;
    letter-spacing:-.04em;
    margin:8px 0 20px}
    .svc-kpis{display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:10px}
    .svc-kpi{background:#f6f8fa;
    border-radius:14px;
    padding:14px}
    .svc-kpi b{display:block;
    font-size:24px}
    .svc-kpi span{font-size:10px;
    color:#788694}
    
    .svc-review{margin-top:18px;
    border:1px solid #e1e6ea;
    border-radius:15px;
    padding:16px}
    .svc-review-head{display:flex;
    justify-content:space-between;
    gap:10px}
    .svc-stars{letter-spacing:2px;
    color:#f2b01e}
    .svc-badge{font-size:9px;
    border-radius:999px;
    background:#e8f3ff;
    color:#0878ee;
    padding:6px 8px;
    font-weight:800}
    .svc-review p{font-size:12px;
    line-height:1.5;
    color:#667585;
    margin:13px 0}
    
        .svc-service-list{padding:80px 0 20px}
    .svc-intro{max-width:900px;
    padding-bottom:70px}
    .svc-intro h2{font-size:clamp(43px,
        5.2vw,
        78px);
    line-height:.96;
    letter-spacing:-.06em;
    margin:20px 0}
    .svc-intro p{font-size:19px;
    line-height:1.6;
    color:var(--svc-muted);
    max-width:760px}
    
        .svc-service-row{display:grid;
    grid-template-columns:1fr 1fr;
    gap:clamp(45px,
        8vw,
        130px);
    align-items:center;
    padding:105px 0;
    border-top:1px solid var(--svc-line)}
    .svc-service-row:last-child{border-bottom:1px solid var(--svc-line)}
    
    .svc-service-row:nth-child(even) .svc-copy{order:2}
    .svc-service-row:nth-child(even) .svc-media{order:1}
    .svc-number{font-size:12px;
    color:var(--svc-blue);
    font-weight:850;
    letter-spacing:.1em}
    
        .svc-copy h3{font-size:clamp(38px,
        4.3vw,
        65px);
    line-height:.98;
    letter-spacing:-.055em;
    margin:17px 0 22px}
    .svc-copy p{font-size:18px;
    line-height:1.6;
    color:var(--svc-muted);
    max-width:620px;
    margin:0 0 18px}
    .svc-copy a{font-size:15px;
    font-weight:750;
    text-decoration:none}
    
    .svc-media{min-height:490px;
    border-radius:30px;
    background:#f4f6f8;
    position:relative;
    overflow:hidden;
    padding:30px;
    display:flex;
    align-items:center;
    justify-content:center}
    .svc-media:after{content:"";
    position:absolute;
    inset:16px;
    border:1px solid rgba(17,24,32,.06);
    border-radius:22px;
    pointer-events:none}
    
        .svc-art-card{position:relative;
    z-index:1;
    width:min(500px,
        100%);
    background:#fff;
    border:1px solid #e0e6eb;
    border-radius:22px;
    padding:24px;
    box-shadow:0 25px 60px rgba(20,40,60,.12)}
    .svc-art-card h4{margin:5px 0 18px;
    font-size:23px;
    letter-spacing:-.035em}
    
    .svc-evidence-row{display:grid;
    grid-template-columns:38px 1fr auto;
    gap:12px;
    align-items:center;
    padding:13px 0;
    border-top:1px solid #edf0f3;
    font-size:12px}
    .svc-evidence-icon{width:34px;
    height:34px;
    border-radius:10px;
    background:#eef5ff;
    display:grid;
    place-items:center;
    color:#0878ee;
    font-weight:800}
    .svc-evidence-row small{color:#8794a0}
    .svc-status{font-size:9px;
    border-radius:999px;
    padding:5px 7px;
    background:#eef7f0;
    color:#38704a;
    font-weight:800}
    
    .svc-chat{display:flex;
    flex-direction:column;
    gap:11px}
    .svc-bubble{max-width:78%;
    padding:13px 15px;
    border-radius:17px;
    background:#f1f4f7;
    font-size:12px;
    line-height:1.45}
    .svc-bubble.me{margin-left:auto;
    background:#e4f1ff}
    .svc-compose{margin-top:12px;
    border:1px solid #e0e5ea;
    border-radius:999px;
    padding:12px 15px;
    color:#8a97a4;
    font-size:11px}
    
    .svc-timeline{position:relative;
    padding-left:25px}
    .svc-timeline:before{content:"";
    position:absolute;
    left:7px;
    top:7px;
    bottom:7px;
    width:1px;
    background:#dbe2e8}
    .svc-step{position:relative;
    padding:0 0 27px 22px}
    .svc-step:before{content:"";
    position:absolute;
    left:-1px;
    top:2px;
    width:15px;
    height:15px;
    border-radius:50%;
    background:#fff;
    border:3px solid #0878ee}
    .svc-step b{display:block;
    font-size:14px}
    .svc-step span{display:block;
    margin-top:5px;
    color:#778593;
    font-size:12px;
    line-height:1.45}
    
    .svc-approval{background:#101820;
    color:#fff;
    border-radius:22px;
    padding:27px}
    .svc-approval-top{display:flex;
    justify-content:space-between;
    gap:15px;
    align-items:center}
    .svc-approval small{color:#8ea1b1;
    letter-spacing:.1em}
    .svc-approval h4{font-size:27px;
    line-height:1.05;
    margin:30px 0 10px}
    .svc-approval p{font-size:12px;
    line-height:1.55;
    color:#b9c5cf}
    .svc-approval-actions{display:flex;
    gap:8px;
    margin-top:25px}
    .svc-approval-actions span{border:1px solid #3a4854;
    border-radius:999px;
    padding:8px 11px;
    font-size:10px}
    .svc-approval-actions .selected{background:#fff;
    color:#111820;
    border-color:#fff}
    
    .svc-cta{padding:125px 0;
    background:#f4f8fb}
    .svc-cta-inner{display:grid;
    grid-template-columns:1fr auto;
    gap:50px;
    align-items:center}
    .svc-cta h2{font-size:clamp(45px,6vw,88px);
    line-height:.93;
    letter-spacing:-.06em;
    margin:0}
    .svc-cta p{font-size:18px;
    line-height:1.55;
    color:var(--svc-muted);
    max-width:720px;
    margin:25px 0 0}
    
        @media(max-width:900px){.svc-hero-grid,
        .svc-service-row,
        .svc-cta-inner{grid-template-columns:1fr}
    .svc-service-row:nth-child(even) .svc-copy,
        .svc-service-row:nth-child(even) .svc-media{order:initial}
    .svc-visual{min-height:500px}
    .svc-media{min-height:390px}
    .svc-window{min-height:440px}
    .svc-cta-inner{gap:30px}
    }
    
    @media(max-width:620px){.svc-hero{padding-top:70px}
    .svc-hero h1{font-size:52px}
    .svc-hero-actions{flex-direction:column;
    align-items:stretch}
    .svc-btn{width:100%}
    .svc-visual{padding:16px;
    min-height:390px;
    border-radius:24px}
    .svc-window{min-height:350px}
    .svc-window-body{grid-template-columns:90px 1fr}
    .svc-sidebar{font-size:9px;
    padding:15px 8px}
    .svc-dashboard{padding:18px}
    .svc-dashboard h3{font-size:21px}
    .svc-kpis{grid-template-columns:1fr}
    .svc-service-list{padding-top:60px}
    .svc-service-row{padding:75px 0}
    .svc-media{padding:18px;
    min-height:340px}
    .svc-copy h3{font-size:40px}
    .svc-cta{padding:85px 0}
    }
    
    """
    nav = (
        '<a href="/produit/">Produit</a>'
        '<a href="/comment-ca-marche/">Comment ça fonctionne</a>'
        '<a href="/services/">Services</a>'
        '<a href="/tarifs/">Tarifs</a>'
        '<a href="/ressources/">Ressources</a>'
        '<a href="/contact/">Contact</a>'
    )
    services=[
            ("01",
          "Analyse des avis",
          "Comprendre ce qui mérite d’être vérifié avant de décider quoi que ce soit.",
          "Examinez le contenu, le contexte et les signaux disponibles. L’objectif est de séparer les faits observables des éléments qui restent à confirmer.",
          "review"),
            ("02",
          "Dossier & preuves",
          "Rassembler les éléments utiles dans un dossier clair.",
          "Centralisez captures, URL, échanges, dates et pièces pertinentes. Chaque élément peut être relié à l’affirmation qu’il permet de vérifier.",
          "evidence"),
            ("03",
          "Préparation des réponses",
          "Préparer une réponse adaptée à la situation.",
          "Structurez une réponse factuelle, cohérente avec le contexte et votre ton de communication. Vous gardez la main avant toute publication.",
          "reply"),
            ("04",
          "Suivi des signalements",
          "Ne perdez plus le fil d’un dossier.",
          "Suivez les étapes, les décisions et les éléments transmis depuis une chronologie unique, avec un historique lisible.",
          "timeline"),
            ("05",
          "Validation humaine",
          "L’automatisation prépare. Vous décidez.",
          "Les actions importantes restent soumises à une validation explicite. Review Defense ne transforme pas une analyse en action externe automatique.",
          "approval"),
    ]
    visuals={
      "review":(
            '<div class="svc-art-card"><' +
            'span class="svc-art-meta">ANALYSE · AVIS #REV-88421</span><' +
            'h4>Situation à examiner</h4><' +
            'div class="svc-review-head"><' +
            'span class="svc-stars">★★★★★</span><' +
            'span class="svc-badge">À VÉRIFIER</span><' +
            '/div><' +
            'div class="svc-review"><' +
            'p>« Expérience très décevante, je n’ai jamais été client de cet établissement… »</p><' +
            '/div><' +
            'div class="svc-kpis"><' +
            'div class="svc-kpi"><' +
            'b>03</b><' +
            'span>signaux</span><' +
            '/div><' +
            'div class="svc-kpi"><' +
            'b>07</b><' +
            'span>éléments</span><' +
            '/div><' +
            'div class="svc-kpi"><' +
            'b>01</b><' +
            'span>dossier</span><' +
            '/div><' +
            '/div><' +
            '/div>'
        ),
      "evidence":(
            '<div class="svc-art-card"><' +
            'span class="svc-art-meta">DOSSIER · PREUVES</span><' +
            'h4>Éléments associés</h4><' +
            'div class="svc-evidence-row"><' +
            'div class="svc-evidence-icon">↗</div><' +
            'div><' +
            'b>URL de l’avis</b><' +
            'small> · source publique</small><' +
            '/div><' +
            'span class="svc-status">LIÉE</span><' +
            '/div><' +
            'div class="svc-evidence-row"><' +
            'div class="svc-evidence-icon">▣</div><' +
            'div><' +
            'b>Capture datée</b><' +
            'small> · 30/09/2026</small><' +
            '/div><' +
            'span class="svc-status">VÉRIFIÉE</span><' +
            '/div><' +
            'div class="svc-evidence-row"><' +
            'div class="svc-evidence-icon">✦</div><' +
            'div><' +
            'b>Échange client</b><' +
            'small> · contexte</small><' +
            '/div><' +
            'span class="svc-status">À LIRE</span><' +
            '/div><' +
            '/div>'
        ),
      "reply":(
            '<div class="svc-art-card"><' +
            'span class="svc-art-meta">RÉPONSE · BROUILLON</span><' +
            'h4>Préparation assistée</h4><' +
            'div class="svc-chat"><' +
            'div class="svc-bubble">Voici les éléments factuels disponibles dans le dossier.</div><' +
            'div class="svc-bubble me">Prépare une réponse courte, professionnelle et factuelle.</div><' +
            'div class="svc-bubble">Brouillon prêt. Vérifiez le contenu avant toute publication.</div><' +
            '/div><' +
            'div class="svc-compose">Relire le brouillon… <b style="float:right">→</b><' +
            '/div><' +
            '/div>'
        ),
      "timeline":(
            '<div class="svc-art-card"><' +
            'span class="svc-art-meta">SUIVI · CHRONOLOGIE</span><' +
            'h4>Un dossier, une vue claire</h4><' +
            'div class="svc-timeline"><' +
            'div class="svc-step"><' +
            'b>Analyse terminée</b><' +
            'span>Les éléments disponibles ont été qualifiés.</span><' +
            '/div><' +
            'div class="svc-step"><' +
            'b>Dossier complété</b><' +
            'span>Les preuves utiles ont été associées.</span><' +
            '/div><' +
            'div class="svc-step"><' +
            'b>Signalement préparé</b><' +
            'span>Le contenu et le motif ont été revus.</span><' +
            '/div><' +
            'div class="svc-step"><' +
            'b>Validation requise</b><' +
            'span>Une décision humaine reste nécessaire.</span><' +
            '/div><' +
            '/div><' +
            '/div>'
        ),
      "approval":(
            '<div class="svc-approval"><' +
            'div class="svc-approval-top"><' +
            'small>ÉTAPE CONTRÔLÉE</small><' +
            'span class="svc-badge">APPROBATION</span><' +
            '/div><' +
            'h4>Prêt pour votre validation</h4><' +
            'p>Le dossier est structuré. Aucune action externe n’est exécutée tant que vous n’avez pas validé explicitement la suite.</p><' +
            'div class="svc-approval-actions"><' +
            'span class="selected">Valider</span><' +
            'span>Modifier</span><' +
            'span>Refuser</span><' +
            '/div><' +
            '/div>'
        )
    }
    rows = "".join(
        f'<article class="svc-service-row">'
        f'<div class="svc-copy">'
        f'<span class="svc-number">{number} · SERVICE</span>'
        f'<h3>{_e(title)}</h3>'
        f'<p>{_e(description)}</p>'
        f'<p>{_e(details)}</p>'
        f'<a href="/analyse-avis-google/">Démarrer une analyse →</a>'
        f'</div>'
        f'<div class="svc-media">{visuals[visual_key]}</div>'
        f'</article>'
        for number, title, description, details, visual_key in services
    )

    schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Organization",
                    "@id": _url("/#organization"),
                    "name": "Review Defense",
                    "url": _url("/")
                },
                {
                    "@type": "WebSite",
                    "@id": _url("/#website"),
                    "name": "Review Defense",
                    "url": _url("/"),
                    "publisher": {
                        "@id": _url("/#organization")
                    }
                },
                {
                    "@type": "Service",
                    "@id": _url("/services/") + "#service",
                    "name": "Services Review Defense",
                    "description": (
                        "Analyse d’avis, préparation de dossiers, "
                        "suivi et validation humaine."
                    ),
                    "provider": {
                        "@id": _url("/#organization")
                    }
                }
            ]
        },
        ensure_ascii=False,
        separators=(",", ":")
    )
    return (
        f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Services | Review Defense</title><meta name="description" content="Analysez les avis, préparez les dossiers, structurez les réponses et suivez les démarches liées à votre réputation en ligne.">'''
        f'''<meta name="robots" content="index,follow"><link rel="canonical" href="{_e(_url("/services/"))}"><meta property="og:type" content="website"><meta property="og:title" content="Services | Review Defense">'''
        f'''<meta property="og:description" content="Analyse, preuves, réponses, suivi et validation humaine pour les situations liées aux avis en ligne."><meta property="og:url" content="{_e(_url("/services/"))}">'''
        f'''<link rel="stylesheet" href="/assets/app.css"><link rel="stylesheet" href="/assets/public.css"><link rel="stylesheet" href="/assets/seo.css"><script type="application/ld+json">{schema}</script>'''
        f'''<style>{styles}</style></head><body><div class="marketing svc-page"><header class="public-header"><a class="public-brand" href="/"><b class="brand-mark">◆</b> Review Defense</a><nav class="public-nav">{nav}</nav>'''
        f'''<div class="public-actions"><a class="btn-secondary" href="/app">Connexion</a><a class="btn-primary" href="/analyse-avis-google/">Analyser un avis →</a></div></header><main><section class="svc-hero">'''
        f'''<div class="svc-container svc-hero-grid"><div><span class="svc-eyebrow">SERVICES · REVIEW DEFENSE</span><h1>Une suite de services pour <span>défendre votre réputation.</span></h1><p class="svc-lead">De l’analyse d’un avis jusqu’au suivi d’un dossier, Review Defense rassemble les informations utiles dans une expérience claire, structurée et sous votre contrôle.</p>'''
        f'''<div class="svc-hero-actions"><a class="svc-btn svc-btn-primary" href="/analyse-avis-google/">Analyser un avis →</a><a class="svc-btn svc-btn-secondary" href="/comment-ca-marche/">Voir le fonctionnement</a>'''
        f'''</div><div class="svc-hero-note"><span>✓ Analyse structurée</span><span>✓ Preuves documentées</span><span>✓ Validation humaine</span></div></div><div class="svc-visual"><div class="svc-window">'''
        f'''<div class="svc-window-top"><span class="svc-dot"></span><span class="svc-dot"></span><span class="svc-dot"></span><span class="svc-window-title">Review Defense · Control Center</span>'''
        f'''</div><div class="svc-window-body"><aside class="svc-sidebar"><strong>REVIEW DEFENSE</strong><span class="active">Vue d’ensemble</span><span>Avis</span><span>Dossiers</span><span>Preuves</span>'''
        f'''<span>Suivi</span></aside><div class="svc-dashboard"><small>CONTROL WORKSPACE</small><h3>Votre réputation, en un seul espace.</h3><div class="svc-kpis"><div class="svc-kpi"><b>24</b>'''
        f'''<span>avis suivis</span></div><div class="svc-kpi"><b>07</b><span>dossiers actifs</span></div><div class="svc-kpi"><b>03</b><span>à valider</span></div></div><div class="svc-review">'''
        f'''<div class="svc-review-head"><span class="svc-stars">★★★★★</span><span class="svc-badge">ANALYSE</span></div><p>Un nouvel avis nécessite une vérification du contexte et des éléments disponibles.</p>'''
        f'''</div></div></div></div></div></div></section><section class="svc-service-list"><div class="svc-container"><div class="svc-intro"><span class="svc-eyebrow">LES SERVICES</span><h2>Chaque situation mérite <span>le bon niveau d’attention.</span>'''
        f'''</h2><p>Une page pensée comme une conversation : chaque bloc présente un service, son utilité et une représentation visuelle de ce que l’utilisateur retrouve dans l’espace Review Defense.</p>'''
        f'''</div>{rows}</div></section><section class="svc-cta"><div class="svc-container svc-cta-inner"><div><span class="svc-eyebrow">COMMENCER</span><h2>Commencez par un avis.<br><span>Construisez le dossier.</span>'''
        f'''</h2><p>Décrivez votre situation et les éléments disponibles. Review Defense structure l’analyse ; les décisions importantes restent humaines.</p></div><a class="svc-btn svc-btn-primary" href="/analyse-avis-google/">Analyser un avis →</a>'''
        f'''</div></section></main><footer class="public-footer"><div><a class="public-brand" href="/"><b class="brand-mark">◆</b> Review Defense</a><p>Analyse, qualification et suivi des dossiers liés aux avis en ligne.</p>'''
        f'''</div><div><b>Produit</b><a href="/produit/">Fonctionnalités</a><a href="/tarifs/">Tarifs</a></div><div><b>Ressources</b><a href="/ressources/">Guides</a><a href="/analyse-avis-google/">Analyser un avis</a>'''
        f'''</div><div><b>Sécurité</b><span>Validation humaine</span><span>Traçabilité complète</span></div></footer></div></body></html>'''
    )

def _commercial_html(path):
    if path=="/services/":
        return _services_html()
    d=COMMERCIAL[path]
    cards = "".join(
        f'<article class="rd-value-card">'
        f'<span>{index:02d}</span>'
        f'<h2>{_e(title)}</h2>'
        f'<p>{_e(description)}</p>'
        f'</article>'
        for index, (title, description) in enumerate(
            d["sections"],
            1
        )
    )

    nav = (
        '<a href="/produit/">Produit</a>'
        '<a href="/comment-ca-marche/">Comment ça fonctionne</a>'
        '<a href="/services/">Services</a>'
        '<a href="/tarifs/">Tarifs</a>'
        '<a href="/ressources/">Ressources</a>'
        '<a href="/contact/">Contact</a>'
    )

    schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Organization",
                    "@id": _url("/#organization"),
                    "name": "Review Defense",
                    "url": _url("/")
                },
                {
                    "@type": "WebSite",
                    "@id": _url("/#website"),
                    "name": "Review Defense",
                    "url": _url("/"),
                    "publisher": {
                        "@id": _url("/#organization")
                    }
                },
                {
                    "@type": "WebPage",
                    "name": d["title"],
                    "description": d["description"],
                    "url": _url(path),
                    "isPartOf": {
                        "@id": _url("/#website")
                    }
                }
            ]
        },
        ensure_ascii=False,
        separators=(",", ":")
    )

    extra=""
    if path=="/ressources/":
        links=_related({"path":path,"cluster":"Faux avis"},_pages())[:5]
        extra=(
            '<section class="rd-section rd-light"><' +
            'div class="rd-container"><' +
            'span class="rd-eyebrow">GUIDES SEO</span><' +
            'h2>Explorer les guides par situation.</h2><' +
            'div class="rd-value-grid">'
        )+''.join(f'<article class="rd-value-card"><h2>{_e(p["h1"])}</h2><a href="{_e(p["path"])}">Lire le guide →</a></article>' for p in links)+(
            '</div><' +
            '/div><' +
            '/section>'
        )
    if path=="/contact/":
        extra=(
            '<section class="rd-section rd-light"><' +
            'div class="rd-container rd-contact-grid"><' +
            'div><' +
            'span class="rd-eyebrow">CONTACT</span><' +
            'h2>Une question ?<br><' +
            'span>Une démo ?</span><' +
            '/h2><' +
            'p>Présentez votre besoin. Les demandes commerciales restent séparées des dossiers d’avis.</p><' +
            '/div><' +
            'form class="rd-contact-form" id="rd-contact-form"><' +
            'label>Nom complet<input name="name" required><' +
            '/label><' +
            'label>E-mail professionnel<input name="email" type="email" required><' +
            '/label><' +
            'label>Entreprise<input name="company"><' +
            '/label><' +
            'label>Message<textarea name="message" rows="5" required><' +
            '/textarea><' +
            'button class="btn-primary" type="submit">Envoyer le message →</button><' +
            '/form><' +
            '/div><' +
            '/section>'
        )
    return (
        f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{_e(d["title"])}</title><meta name="description" content="{_e(d["description"])}">'''
        f'''<meta name="robots" content="index,follow"><link rel="canonical" href="{_e(_url(path))}"><meta property="og:type" content="website"><meta property="og:title" content="{_e(d["title"])}">'''
        f'''<meta property="og:description" content="{_e(d["description"])}"><meta property="og:url" content="{_e(_url(path))}"><link rel="stylesheet" href="/assets/app.css"><link rel="stylesheet" href="/assets/public.css">'''
        f'''<link rel="stylesheet" href="/assets/seo.css"><script type="application/ld+json">{schema}</script></head><body><div class="marketing"><header class="public-header"><a class="public-brand" href="/">'''
        f'''<b class="brand-mark">◆</b> Review Defense</a><nav class="public-nav">{nav}</nav><div class="public-actions"><a class="btn-secondary" href="/app">Connexion</a><a class="btn-primary" href="/analyse-avis-google/">Analyser un avis →</a>'''
        f'''</div></header><main class="rd-commercial-main"><section class="rd-home-hero"><div class="rd-container rd-hero-grid"><div class="rd-hero-copy"><span class="rd-eyebrow-pill">{_e(d["eyebrow"])}</span>'''
        f'''<h1>{d["h1"]}</h1><p class="rd-hero-lead">{_e(d["lead"])}</p><div class="rd-hero-actions"><a class="btn-primary rd-btn-lg" href="/analyse-avis-google/">Analyser un avis →</a><a class="btn-secondary rd-btn-lg" href="/comment-ca-marche/">Voir comment ça fonctionne</a>'''
        f'''</div><div class="rd-trust-line"><span>✓ Analyse structurée</span><span>✓ Preuves documentées</span><span>✓ Validation humaine</span></div></div><div class="rd-product-stage"><div class="rd-product-window">'''
        f'''<div class="rd-window-top"><b>Review Defense · Control Center</b></div><div class="rd-window-body"><aside><strong>REVIEW DEFENSE</strong><span class="active">Dashboard</span><span>Avis</span>'''
        f'''<span>Analyse</span><span>Dossiers</span><span>Preuves</span><span>Audit</span></aside><div class="rd-preview-main"><div class="rd-preview-head"><div><small>CONTROL WORKSPACE</small>'''
        f'''<h3>Dossier #REV-88421</h3></div><span class="rd-mini-badge">APPROVAL REQUIRED</span></div><div class="rd-review-preview"><b>Analyse, preuves et prochaine étape</b><span>Décision humaine requise avant toute étape contrôlée</span>'''
        f'''</div><div class="rd-analysis-columns"><div><small>SIGNAUX</small><strong>03</strong><span>à examiner</span></div><div><small>PREUVES</small><strong>07</strong><span>associées</span>'''
        f'''</div><div><small>STATUT</small><strong>Gel</strong><span>validation requise</span></div></div><div class="rd-preview-chain"><span class="done">01 Analyse</span><span class="done">02 Décision</span>'''
        f'''<span class="current">03 Gel</span><span>04 Approbation</span></div></div></div></div></div></div></section><section class="rd-section rd-light"><div class="rd-container"><div class="rd-section-heading">'''
        f'''<span class="rd-eyebrow">VALEUR</span><h2>Une information claire avant<br><span>une décision importante.</span></h2><p>{_e(d["lead"])}</p></div><div class="rd-value-grid">{cards}</div>'''
        f'''</div></section><section class="rd-section"><div class="rd-container rd-split"><div class="rd-section-heading"><span class="rd-eyebrow">CONTRÔLE</span><h2>Analyse → Décision → Gel<br>'''
        f'''<span>→ Human Approval.</span></h2><p>L’automatisation prépare. L’humain décide. Les étapes importantes restent visibles et traçables.</p><a class="btn-secondary" href="/comment-ca-marche/">Découvrir le workflow →</a>'''
        f'''</div><div class="rd-workflow"><div class="rd-workflow-item done"><b>01</b><div><strong>Analyse</strong><span>Identifier les éléments à examiner.</span></div></div><div class="rd-workflow-item done">'''
        f'''<b>02</b><div><strong>Décision</strong><span>Documenter le raisonnement.</span></div></div><div class="rd-workflow-item current"><b>03</b><div><strong>Gel</strong><span>Fixer le dossier avant approbation.</span>'''
        f'''</div></div><div class="rd-workflow-item"><b>04</b><div><strong>Human Approval</strong><span>Valider explicitement la suite.</span></div></div><div class="rd-workflow-item"><b>05</b>'''
        f'''<div><strong>Préparation contrôlée</strong><span>Préparer sans exécution automatique.</span></div></div></div></div></section>{extra}<section class="rd-final-cta"><div class="rd-container">'''
        f'''<span class="rd-eyebrow">REVIEW DEFENSE</span><h2>Gardez le contrôle<br><span>de votre dossier.</span></h2><p>Commencez par une analyse structurée et préparez la suite avec des éléments vérifiables.</p>'''
        f'''<a class="btn-primary rd-btn-lg" href="/analyse-avis-google/">Analyser un avis →</a><small>La décision finale appartient toujours à la plateforme concernée.</small></div></section>'''
        f'''</main><footer class="public-footer"><div><a class="public-brand" href="/"><b class="brand-mark">◆</b> Review Defense</a><p>Analyse, qualification et suivi des dossiers liés aux avis en ligne.</p>'''
        f'''</div><div><b>Produit</b><a href="/produit/">Fonctionnalités</a><a href="/tarifs/">Tarifs</a></div><div><b>Ressources</b><a href="/ressources/">Guides</a><a href="/analyse-avis-google/">Analyser un avis</a>'''
        f'''</div><div><b>Sécurité</b><span>Validation humaine</span><span>Traçabilité complète</span></div></footer></div></body></html>'''
    )

def render(path):
    if path=="/analyse-avis-google/":
        return 200,{"Content-Type":"text/html; charset=utf-8","Cache-Control":"public, max-age=300"},_analysis_html().encode()
    if path in COMMERCIAL:
        return 200,{"Content-Type":"text/html; charset=utf-8","Cache-Control":"public, max-age=300"},_commercial_html(path).encode()
    pages=_pages()
    if path=="/robots.txt":
                return 200,{"Content-Type":"text/plain; charset=utf-8",
            "Cache-Control":"public, max-age=3600"},f"User-agent: *\nAllow: /\nDisallow: /app\nDisallow: /v1/\nDisallow: /reset-password\nDisallow: /verify-email\nDisallow: /accept-invitation\nSitemap: {_url('/sitemap.xml')}\n".encode()
    if path=="/sitemap.xml":
        paths=list(dict.fromkeys(["/"]+[x for x in COMMERCIAL if x!="/"]+[p["path"] for p in pages]))
        body='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f"<url><loc>{_e(_url(path))}</loc><lastmod>{SITE_MODIFIED}</lastmod></url>" for path in paths)+"</urlset>"
        return 200,{"Content-Type":"application/xml; charset=utf-8","Cache-Control":"public, max-age=3600"},body.encode()
    page=next((p for p in pages if p["path"]==path),None)
    if not page: return None
    sections=''.join(f'<section><h2>{_e(h)}</h2><p>{_e(t)}</p></section>' for h,t in _sections(page))
    faq=''.join(f'<details><summary>{_e(q)}</summary><p>{_e(a)}</p></details>' for q,a in _faq_items(page))
    related=''.join(f'<li><a href="{_e(p["path"])}">{_e(p["h1"])}</a></li>' for p in _related(page,pages))
    c=_url(page["path"]); schema=json.dumps(_schema(page),ensure_ascii=False,separators=(",",":"))
    title_counts={}
    for item in pages: title_counts[item["title"]]=title_counts.get(item["title"],0)+1
    display_title=page["title"] if title_counts.get(page["title"],0)==1 else page["title"]+" — "+page["cluster"]+" | Review Defense"
    cta_label="Demander l'analyse" if page["service"] else "Analyser mon avis"
    script="""<script>(function(){window.dataLayer=window.dataLayer||[];document.addEventListener("click",function(e){var x=e.target.closest("[data-rd-track]");if(x){window.dataLayer.push(["click",x.getAttribute("data-rd-track"),location.pathname]);}});})();</script>"""
    body=(
        f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{_e(display_title)}</title>"""
        f"""<meta name="description" content="{_e(page["description"])}"><meta name="robots" content="index,follow"><link rel="canonical" href="{_e(c)}"><meta property="og:type" content="article">"""
        f"""<meta property="og:title" content="{_e(display_title)}"><meta property="og:description" content="{_e(page["description"])}"><meta property="og:url" content="{_e(c)}">"""
        f"""<link rel="stylesheet" href="/assets/app.css"><link rel="stylesheet" href="/assets/public.css"><script type="application/ld+json">{schema}</script></head><body>"""
        f"""<div class="marketing"><header class="public-header"><a class="public-brand" href="/"><b class="brand-mark">◆</b> Review Defense</a><nav class="public-nav"><a href="/produit/">Produit</a>"""
        f"""<a href="/comment-ca-marche/">Comment ça fonctionne</a><a href="/services/">Services</a><a href="/tarifs/">Tarifs</a><a href="/ressources/">Ressources</a><a href="/contact/">Contact</a>"""
        f"""</nav><div class="public-actions"><a class="btn-secondary" href="/app">Connexion</a><a class="btn-primary" href="/analyse-avis-google/">Analyser un avis →</a></div>"""
        f"""</header><main class="seo-main"><div class="seo-breadcrumb"><a href="/">Accueil</a> <span>›</span> <span>{_e(page["cluster"])}</span> <span>›</span> <span>{_e(page["h1"])}</span>"""
        f"""</div><article class="seo-article"><span class="eyebrow">{_e(page["cluster"]).upper()}</span><h1>{_e(page["h1"])}</h1><p class="seo-lead">Guide pratique sur <strong>{_e(page["keyword"])}</strong> : vérification des faits, qualification du problème, éléments à conserver et prochaines étapes.</p>"""
        f"""<div class="seo-content">{sections}</div><section class="seo-disclaimer"><strong>À retenir :</strong> un avis négatif ou contesté n’est pas automatiquement supprimable. Le signalement doit correspondre aux faits observables ; aucune suppression n’est garantie et la décision finale appartient à la plateforme.</section>"""
        f"""<section class="seo-faq"><h2>Questions fréquentes</h2>{faq}</section><section class="seo-related"><h2>À lire également</h2><ul>{related}</ul><p><a href="/signaler-un-avis-google/">Comment signaler un avis Google</a> · <a href="/analyse-avis-google/">Analyser votre avis Google</a>"""
        f"""</p></section><section class="seo-cta"><h2>Besoin d’analyser votre avis ?</h2><p>Structurez votre dossier avec Review Defense et gardez une validation humaine sur les étapes importantes.</p>"""
        f"""<a class="btn-primary" href="/analyse-avis-google/">{cta_label} →</a></section></article></main><footer class="public-footer"><div><a class="public-brand" href="/">"""
        f"""<b class="brand-mark">◆</b> Review Defense</a><p>Analyse, qualification et suivi des dossiers liés aux avis en ligne.</p></div><div><b>Produit</b><a href="/produit/">Fonctionnalités</a>"""
        f"""<a href="/tarifs/">Tarifs</a></div><div><b>Ressources</b><a href="/ressources/">Guides</a><a href="/analyse-avis-google/">Analyser un avis</a></div><div><b>Sécurité</b>"""
        f"""<span>Validation humaine</span><span>Traçabilité complète</span></div></footer></div>{script}</body></html>"""
    )
    return 200,{"Content-Type":"text/html; charset=utf-8","Cache-Control":"public, max-age=300"},body.encode()

def is_seo_path(path):
    return path in {"/robots.txt","/sitemap.xml"} or path in COMMERCIAL or any(p["path"]==path for p in _pages())