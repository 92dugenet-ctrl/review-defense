import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { ApiError, api } from "@/services/api/client";
import type { Case, NotificationItem, Review, ReviewQueueItem } from "@/types/api";

type State={reviews:Review[];cases:Case[];queue:ReviewQueueItem[];notifications:NotificationItem[]};
const date=(v?:string|null)=>{if(!v)return "—";const d=new Date(v);return Number.isNaN(d.getTime())?v:new Intl.DateTimeFormat("fr-FR",{day:"2-digit",month:"short",year:"numeric"}).format(d)};
const label=(v?:string)=>v?v.replaceAll("_"," ").toLowerCase().replace(/^./,c=>c.toUpperCase()):"Inconnu";
const priority=(v?:string)=>{const p=v?.toUpperCase();return p==="CRITICAL"||p==="HIGH"?"dashboard-priority dashboard-priority-high":p==="MEDIUM"||p==="NORMAL"?"dashboard-priority dashboard-priority-medium":"dashboard-priority dashboard-priority-low"};

export function DashboardPage(){
 const [state,setState]=useState<State>({reviews:[],cases:[],queue:[],notifications:[]}),[loading,setLoading]=useState(true),[error,setError]=useState<ApiError|null>(null);
 const load=async()=>{setLoading(true);setError(null);try{const [reviews,cases,queue,notifications]=await Promise.all([api.get<{items:Review[]}>("/v1/reviews"),api.get<{items:Case[]}>("/v1/cases"),api.get<{items:ReviewQueueItem[]}>("/v1/review-queue"),api.get<{items:NotificationItem[]}>("/v1/notifications")]);setState({reviews:reviews.items??[],cases:cases.items??[],queue:queue.items??[],notifications:notifications.items??[]})}catch(e){setError(e instanceof ApiError?e:new ApiError("Impossible de charger le tableau de bord.",0))}finally{setLoading(false)}};
 useEffect(()=>{void load()},[]);
 const average=useMemo(()=>state.reviews.length?(state.reviews.reduce((s,r)=>s+r.rating,0)/state.reviews.length).toFixed(1):"—",[state.reviews]);
 const openCases=state.cases.filter(c=>!["CLOSED","RESOLVED"].includes(c.status.toUpperCase())).length;
 const pending=state.notifications.filter(n=>!["SENT","CANCELLED","DELIVERED"].includes(n.status.toUpperCase())).length;
 const urgent=state.queue.filter(q=>["CRITICAL","HIGH"].includes(q.priority?.toUpperCase()??"")).length;
 const recent=[...state.reviews].sort((a,b)=>new Date(b.published_at??0).getTime()-new Date(a.published_at??0).getTime()).slice(0,5);
 return <section className="dashboard-page">
  <div className="dashboard-hero"><div className="dashboard-hero-copy"><span className="eyebrow">REVIEW DEFENSE · WORKSPACE</span><h1>Votre activité, en un coup d’œil.</h1><p>Analysez les avis, structurez les preuves et gardez chaque dossier sous contrôle.</p></div><div className="dashboard-hero-actions"><Button variant="secondary" onClick={()=>void load()} disabled={loading}>{loading?"Actualisation…":"Actualiser"}</Button><a className="dashboard-hero-link" href="/app/reviews">Ouvrir les avis →</a></div></div>
  {error&&<div className="dashboard-error" role="alert"><div><strong>Le tableau de bord n’a pas pu être actualisé.</strong><span>{error.message}</span></div><Button variant="secondary" onClick={()=>void load()}>Réessayer</Button></div>}
  <div className="dashboard-metrics dashboard-kpis"><article><span>Avis suivis</span><strong>{loading?"…":state.reviews.length}</strong><small>Toutes sources</small></article><article><span>Note moyenne</span><strong>{loading?"…":average}</strong><small>{state.reviews.length?"Sur 5":"Aucun avis"}</small></article><article><span>Dossiers ouverts</span><strong>{loading?"…":openCases}</strong><small>À traiter</small></article><article className="dashboard-metric-focus"><span>Priorités élevées</span><strong>{loading?"…":urgent}</strong><small>{pending} action{pending>1?"s":""} en attente</small></article></div>
  <div className="dashboard-main-grid">
   <article className="dashboard-surface dashboard-card"><div className="dashboard-section-heading"><div><span>ACTIVITÉ RÉCENTE</span><h2>Derniers avis</h2></div><a href="/app/reviews">Tout voir</a></div>
    {loading?<div className="dashboard-empty">Chargement des avis…</div>:recent.length?<div>{recent.map(r=><a className="dashboard-review-row" href={`/app/reviews/${r.review_id}`} key={r.review_id}><div className="dashboard-rating">{r.rating}<small>/5</small></div><div className="dashboard-review-content"><strong>{r.text||"Avis sans texte"}</strong><span>{r.author_display_name||"Auteur non renseigné"} · {r.source}</span></div><time>{date(r.published_at)}</time><b>→</b></a>)}</div>:<div className="dashboard-empty"><strong>Aucun avis pour le moment</strong><span>Les avis apparaîtront ici dès leur synchronisation.</span></div>}
   </article>
   <article className="dashboard-surface dashboard-card"><div className="dashboard-section-heading"><div><span>À SURVEILLER</span><h2>File prioritaire</h2></div><a href="/app/analysis">Analyse</a></div>
    {loading?<div className="dashboard-empty">Chargement…</div>:state.queue.length?<div>{state.queue.slice(0,5).map(q=><a className="dashboard-queue-row" href={`/app/cases/${q.case_id}`} key={q.case_id}><i>{String(q.priority_score??"—")}</i><div><strong>{q.case_id.slice(0,14)}</strong><span>{label(q.status)}{q.assigned_to?` · ${q.assigned_to}`:" · Non assigné"}</span></div><em className={priority(q.priority)}>{label(q.priority)}</em></a>)}</div>:<div className="dashboard-empty"><strong>File vide</strong><span>Aucun dossier prioritaire.</span></div>}
   </article>
  </div>
  <div className="dashboard-lower-grid">
   <article className="dashboard-surface dashboard-card"><div className="dashboard-section-heading"><div><span>PORTEFEUILLE</span><h2>État des dossiers</h2></div><a href="/app/cases">Dossiers →</a></div><div className="dashboard-status-list">{["OPEN","IN_REVIEW","RESOLVED","CLOSED"].map(s=><div key={s}><span>{label(s)}</span><strong>{loading?"…":state.cases.filter(c=>c.status.toUpperCase()===s).length}</strong></div>)}</div></article>
   <article className="dashboard-surface dashboard-card"><div className="dashboard-section-heading"><div><span>PROCHAINE ACTION</span><h2>Garder le contrôle</h2></div></div><div className="dashboard-next-content"><i>✓</i><div><strong>{pending?`${pending} action${pending>1?"s":""} à vérifier`:"Tout est à jour"}</strong><span>{state.notifications.length?`Dernière activité · ${date(state.notifications[0].created_at)}`:"Aucune notification récente."}</span></div><a href="/app/notifications">Voir →</a></div></article>
  </div>
 </section>
}
