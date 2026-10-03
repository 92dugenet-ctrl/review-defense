import{useEffect,useState}from"react";import{useParams}from"react-router-dom";import{api}from"@/services/api/client";
import { PageHeading } from "@/components/layout/PageHeading";
import { BackLink } from "@/components/layout/BackLink";
import { StatusPill } from "@/components/layout/StatusPill";
import { FeedbackMessage } from "@/components/layout/FeedbackMessage";
import { DetailMeta } from "@/components/layout/DetailMeta";
import { SignalRow } from "@/components/layout/SignalRow";
type Evidence={evidence_id:string;filename:string;evidence_type:string;status:string};
type Workspace={state:string;priority:string;review:{author_display_name?:string|null;text?:string;rating?:number;source?:string};evidence:Evidence[];evidence_coverage?:number;claims?:{claim_id:string;text:string;claim_type:string;status:string}[];policies?:{code:string;status:string;justification?:string}[];contradictions?:{contradiction_id:string;description:string;requires_human_review:boolean}[]};
type WorkspaceResponse={workspace:Workspace;evidence_tasks:{task_id:string;evidence_requirement:string;priority:string;status:string}[];requires_human_review:boolean};
export function CaseDetailPage(){
const{id}=useParams(),[data,setData]=useState<WorkspaceResponse|null>(null),[error,setError]=useState("");
useEffect(()=>{let active=true;if(id)api.get<WorkspaceResponse>("/v1/cases/"+id+"/workspace").then(x=>{if(active)setData(x)}).catch(e=>{if(active)setError(e instanceof Error?e.message:"Impossible de charger le dossier")});return()=>{active=false}},[id]);
if(error)return <section className="workspace"><BackLink to="/app/cases">← Tous les dossiers</BackLink><FeedbackMessage className="form-error" role="alert">{error}</FeedbackMessage></section>;
if(!data)return <section className="workspace"><FeedbackMessage className="empty">Chargement du dossier…</FeedbackMessage></section>;
const w=data.workspace,review=w.review,evidence=w.evidence??[],tasks=data.evidence_tasks??[];
return <section className="workspace"><Link to="/app/cases" className="back-link">← Tous les dossiers</Link><PageHeading eyebrow="DOSSIER" title={id ?? "Dossier"} description="Workspace de décision et de preuves." action={<StatusPill>{w.state??"OPEN"}</StatusPill>} /><div className="content-grid"><article className="panel"><span className="eyebrow">AVIS</span><h2>{review.author_display_name??"Avis sélectionné"}</h2><blockquote>{review.text??"Aucun texte disponible."}</blockquote><DetailMeta><span>Note</span><b>{review.rating??"—"}</b><span>Source</span><b>{review.source??"—"}</b><span>Priorité</span><b>{w.priority??"—"}</b></DetailMeta></article><article className="panel"><span className="eyebrow">PREUVES</span><h2>Éléments du dossier</h2>{evidence.map(x=><SignalRow key={x.evidence_id}>{x.filename} · {x.status}</SignalRow>)}{!evidence.length&&<FeedbackMessage className="empty">Aucune preuve enregistrée.</FeedbackMessage>}<div className="panel-head"><h3>Éléments à réunir</h3></div>{tasks.map(x=><SignalRow key={x.task_id}>{x.evidence_requirement} · {x.status}</SignalRow>)}{!tasks.length&&<FeedbackMessage className="empty">Aucun élément manquant identifié.</FeedbackMessage>}<p>Couverture des preuves : {Math.round((w.evidence_coverage??0)*100)}%</p></article></div></section>;
}