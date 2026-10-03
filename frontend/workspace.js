(()=>{"use strict";
const app=document.getElementById("app");
const S={token:localStorage.getItem("rd_token"),
  role:localStorage.getItem("rd_role"),
  userId:null,
  userEmail:null,
  view:"dashboard",
  detail:null,
  cache:{},
  caseDetails:{}};
const adminPath=()=>location.pathname.startsWith("/admin");
const roles={manager:["OWNER",
  "ADMIN"],
  operator:["OWNER",
  "ADMIN",
  "ANALYST"],
  read:["OWNER",
  "ADMIN",
  "ANALYST",
  "CLIENT",
  "VIEWER"]};
const can=(kind)=>roles[kind].includes(S.role);
const esc=x=>String(x??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const arr=x=>Array.isArray(x)?x:(x?.items||x?.data||x?.results||[]);
const fmt=x=>{if(!x)return "—";const d=new Date(x);return Number.isNaN(d.getTime())?String(x):d.toLocaleString("fr-FR")};
const field=(k,v)=>'<div class="detail-field"><small>'+esc(k)+'</small><div>'+esc(v)+'</div></div>';
const button=(label,action,cls="btn")=>'<button class="'+cls+'" data-action="'+esc(action)+'">'+esc(label)+'</button>';
async function api(url,
  opts={}){const h={"Content-Type":"application/json",
  ...(opts.headers||{})};if(S.token)h.Authorization="Bearer " +
  S.token;const r=await fetch(url,
  {...opts,
  headers:h});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d?.error?.message||d?.error?.code||"Erreur HTTP " +
  r.status);return d}
const post=(url,body={})=>api(url,{method:"POST",body:JSON.stringify(body)});
function verifyEmail(){
 const params=new URLSearchParams(location.search);
 const organizationId=params.get("organization_id")||localStorage.getItem("rd_org_id")||"";
 const token=params.get("token")||"";
 app.innerHTML=(
        '<main class="login"><section class="loginbox"><div><b style="color:#0878ee">◆</b> Rev' +
        'iew Defense</div><h1>Vérifier votre adresse email</h1><p>Confirmez votre adresse pour' +
        ' activer votre espace Review Defense.</p><div class="err" id="verify-error" role="ale' +
        'rt"></div><button class="btn primary" id="verify-submit" style="width:100%">Vérifier ' +
        'mon adresse</button><p><a href="/connexion">Retour à la connexion</a></p></section></' +
        'main>'
      );
 const submit=document.getElementById("verify-submit");
 submit.disabled=!organizationId||!token;
  if(!organizationId||!token){document.getElementById("verify-error").textContent="Lien incomplet. Ouvrez le lien de vérification reçu par email.";
   return}
    submit.onclick=async()=>{submit.disabled=true;
    const err=document.getElementById("verify-error");
    err.textContent="";
    try{await post("/v1/auth/email-verification/verify",
   {organization_id:organizationId,
   verification_token:token});localStorage.setItem("rd_org_id",
   organizationId);app.querySelector(".loginbox").innerHTML=(
        '<div><b style="color:#0878ee">◆</b> Review Defense</div><h1>Adresse vérifiée</h1><p>V' +
        'otre adresse email est confirmée. Vous pouvez maintenant vous connecter.</p><a class=' +
        '"btn primary" style="display:block;text-align:center" href="/connexion">Continuer ver' +
        's la connexion</a>'
      )}catch(e){err.textContent=e.message;submit.disabled=false}};
}

function recovery(){
  const params=new URLSearchParams(location.search),
   organizationId=params.get("organization_id")||localStorage.getItem("rd_org_id")||"",
   token=params.get("token")||"",
   resetting=Boolean(token);
  app.innerHTML='<main class="login"><section class="loginbox"><div><b style="color:#0878ee">◆</b> Review Defense</div><h1>' +
   (resetting?'Choisir un nouveau mot de passe':'Récupérer mon compte') +
   '</h1><p>' +
   (resetting?'Définissez un nouveau mot de passe.':'Indiquez votre organisation et votre adresse email. Si le compte existe, un lien sera envoyé.') +
   '</p><form id="recovery-form">' +
   (resetting?'':(
        '<div class="field"><label>Identifiant de votre organisation</label><input name="organ' +
        'ization_id" required value="'
      ) +
   esc(organizationId) +
   '"></div>') +
   '<div class="field"><label>Email</label><input name="email" type="email" required autocomplete="email"></div>' +
   (resetting?'<div class="field"><label>Nouveau mot de passe</label><input name="new_password" type="password" required minlength="12" autocomplete="new-password"></div>':'') +
   (
        '<div class="err" id="recovery-error" role="alert"></div><button class="btn primary" t' +
        'ype="submit" style="width:100%">'
      ) +
   (resetting?'Enregistrer le mot de passe':'Envoyer le lien de récupération') +
   '</button></form><p><a href="/connexion">Retour à la connexion</a></p></section></main>';
 const form=document.getElementById("recovery-form");
  form.onsubmit=async ev=>{ev.preventDefault();const button=form.querySelector('button[type="submit"]'),
   err=document.getElementById("recovery-error");button.disabled=true;err.textContent="";
  try{const data=Object.fromEntries(new FormData(form));if(resetting){await post("/v1/auth/recovery/reset",
   {organization_id:organizationId,
   recovery_token:token,
   new_password:data.new_password});app.querySelector(".loginbox").innerHTML=(
        '<div><b style="color:#0878ee">◆</b> Review Defense</div><h1>Mot de passe modifié</h1>' +
        '<p>Votre mot de passe a été mis à jour.</p><a class="btn primary" href="/connexion">S' +
        'e connecter</a>'
      )}else{localStorage.setItem("rd_org_id",
   data.organization_id);await post("/v1/auth/recovery/request",
   data);err.textContent="Si un compte correspond à ces informations, un email de récupération sera envoyé."}}
 catch(error){err.textContent=error.message}finally{if(button.isConnected)button.disabled=false}};
}
function acceptInvitation(){
  const params=new URLSearchParams(location.search),
   organizationId=params.get("organization_id")||"",
   token=params.get("token")||params.get("invitation_token")||"",
   invitedEmail=params.get("email")||"";
  app.innerHTML=(
        '<main class="login"><section class="loginbox"><div><b style="color:#0878ee">◆</b> Rev' +
        'iew Defense</div><h1>Accepter une invitation</h1><p>Confirmez votre adresse et choisi' +
        'ssez un mot de passe.</p><form id="invitation-form"><div class="field"><label>Identif' +
        'iant de l’organisation</label><input name="organization_id" required value="'
      ) +
   esc(organizationId) +
   (
        '"></div><div class="field"><label>Adresse email invitée</label><input name="email" ty' +
        'pe="email" required value="'
      ) +
   esc(invitedEmail) +
   (
        '" autocomplete="email"></div><div class="field"><label>Jeton d’invitation</label><inp' +
        'ut name="invitation_token" required value="'
      ) +
   esc(token) +
   (
        '" autocomplete="off"></div><div class="field"><label>Mot de passe</label><input name=' +
        '"password" type="password" required minlength="12" autocomplete="new-password"></div>' +
        '<div class="err" id="invitation-error" role="alert"></div><button class="btn primary"' +
        ' type="submit" style="width:100%">Accepter l’invitation</button></form><p><a href="/c' +
        'onnexion">Retour à la connexion</a></p></section></main>'
      );
 const form=document.getElementById("invitation-form");
  form.onsubmit=async ev=>{ev.preventDefault();const button=form.querySelector('button[type="submit"]'),
   err=document.getElementById("invitation-error");button.disabled=true;err.textContent="";
  try{const result=await post("/v1/organization/invitations/accept",
   Object.fromEntries(new FormData(form)));if(result.status==="verification_required"){localStorage.setItem("rd_org_id",
   organizationId);app.querySelector(".loginbox").innerHTML=(
        '<div><b style="color:#0878ee">◆</b> Review Defense</div><h1>Vérifiez votre adresse em' +
        'ail</h1><p>Une confirmation vous a été envoyée avant l’activation de votre accès.</p>' +
        '<a href="/connexion">Retour à la connexion</a>'
      );return}
  if(!result.access_token)throw Error("L’invitation a été acceptée, mais aucune session n’a été délivrée.");localStorage.setItem("rd_org_id",
   organizationId);S.token=result.access_token;S.role=result.role;localStorage.setItem("rd_token",
   S.token);localStorage.setItem("rd_role",
   S.role);location.replace(["OWNER",
   "ADMIN"].includes(S.role)?"/admin":"/client")}
 catch(error){err.textContent=error.message}finally{if(button.isConnected)button.disabled=false}};
}
function login(){
 const params=new URLSearchParams(location.search);
 let mode=params.get("auth")==="register"||location.pathname==="/inscription"?"register":"login";
 const render=()=>{
  const registering=mode==="register";
    app.innerHTML='<main class="login"><section class="loginbox"><div><b style="color:#0878ee">◆</b> Review Defense</div><h1>' +
    (registering?'Créer votre espace':'Connexion à votre espace') +
    '</h1><p>' +
    (registering?'Créez votre compte pour commencer à analyser et suivre vos avis.':'Connectez-vous pour retrouver vos avis, dossiers, preuves et actions.') +
    '</p><div class="auth-tabs"><button type="button" class="btn ' +
    (!registering?'primary':'') +
    '" id="auth-login">Connexion</button><button type="button" class="btn ' +
    (registering?'primary':'') +
    '" id="auth-register">Créer un compte</button></div><form id="auth-form">' +
    (registering?'<div class="field"><label>Nom de votre entreprise</label><input name="organization_name" required maxlength="200" autocomplete="organization"></div>':(
        '<div class="field"><label>Identifiant de votre organisation</label><input name="organ' +
        'ization_id" required value="'
      ) +
    esc(localStorage.getItem("rd_org_id")||"") +
    '"></div>') +
    (
        '<div class="field"><label>Email</label><input name="email" type="email" required auto' +
        'complete="email"></div><div class="field"><label>Mot de passe</label><input name="pas' +
        'sword" type="password" required autocomplete="'
      ) +
    (registering?'new-password':'current-password') +
    '"></div>' +
    (registering?'':'<div class="field"><label>Code MFA si demandé</label><input name="mfa_code" inputmode="numeric"></div>') +
    (
        '<div class="err" id="auth-error" role="alert"></div><button class="btn primary" style' +
        '="width:100%;text-align:center" type="submit">'
      ) +
    (registering?'Créer mon compte':'Se connecter') +
    '</button></form></section></main>';
    if(!registering)app.querySelector(".loginbox").insertAdjacentHTML("beforeend",
    '<p><a href="/reset-password">Mot de passe oublié ?</a></p>');
  document.getElementById("auth-login").onclick=()=>{mode="login";render()};
  document.getElementById("auth-register").onclick=()=>{mode="register";render()};
  document.getElementById("auth-form").onsubmit=async e=>{
      e.preventDefault();const form=e.currentTarget,
     err=document.getElementById("auth-error"),
     submit=form.querySelector('button[type="submit"]');err.textContent="";submit.disabled=true;
   try{
    const payload=Object.fromEntries(new FormData(form));
    const d=registering?await post("/v1/auth/register",payload):await post("/v1/auth/login",payload);
        if(d.status==="verification_required"){localStorage.setItem("rd_org_id",
            d.organization_id);
        mode="login";
        render();
        document.getElementById("auth-error").textContent="Un email de vérification a été demandé. Vérifiez votre boîte de réception avant de vous connecter.";
        return}
    if(d.organization_id)localStorage.setItem("rd_org_id",d.organization_id);
    if(!d.access_token)throw Error("Le compte a été créé, mais aucune session n'a été délivrée. Vérifiez la configuration de validation email.");
        S.token=d.access_token;S.role=d.role;localStorage.setItem("rd_token",
      S.token);localStorage.setItem("rd_role",
      S.role);location.replace(can("manager")?"/admin":"/client");
   }catch(x){err.textContent=x.message}
   finally{const button=form.querySelector('button[type="submit"]');if(button)button.disabled=false}
  };
 };
 render();
}
const client=[["dashboard",
  "Vue d’ensemble"],
  ["client-monitoring",
  "Mon entreprise"],
  ["reviews",
  "Avis"],
  ["cases",
  "Dossiers"],
  ["evidence",
  "Preuves"],
  ["billing",
  "Abonnement"]];
const admin=[["queue",
  "File de traitement"],
  ["escalations",
  "Escalades SLA"],
  ["approvals",
  "Approbations"],
  ["team",
  "Équipe"],
  ["notifications",
  "Notifications"],
  ["submissions",
  "Soumissions"]];
const allLabels=Object.fromEntries([...client,...admin]);
function shell(){let items=[...client];if(can("operator"))items.push(...admin.filter(x=>["queue",
  "escalations"].includes(x[0])));if(can("manager"))items.push(...admin.filter(x=>["approvals",
  "team",
  "notifications",
  "submissions"].includes(x[0])));
app.innerHTML='<div class="shell"><aside class="side"><a class="brand" href="/"><b>◆</b> Review Defense</a><nav>' +
  items.map(x=>'<button data-view="' +
  x[0] +
  '">' +
  x[1] +
  '</button>').join("") +
  '</nav><div class="role">Accès<br><strong>' +
  esc(S.role) +
  (
        '</strong></div></aside><main class="main"><header class="top"><div class="top-left"><' +
        'button class="btn menu" id="menu">☰</button><div><h1 id="page-title">Vue d’ensemble</' +
        'h1><p>Votre activité au même endroit.</p></div></div><div class="actions"><button cla' +
        'ss="btn" id="refresh">Actualiser</button><button class="btn" id="logout">Déconnexion<' +
        '/button></div></header><section class="content">'
      ) +
  items.map(x=>'<div class="view" id="view-' +
  x[0] +
  '"></div>').join("") +
  '</section></main></div><div id="modal-root"></div>';
document.querySelectorAll("[data-view]").forEach(b=>b.onclick=()=>{S.view=b.dataset.view;document.querySelector(".side").classList.remove("open");show()});
document.getElementById("logout").onclick=async()=>{try{await post("/v1/logout")}catch{}localStorage.removeItem("rd_token");
  localStorage.removeItem("rd_role");
  S.token=null;
  login()};
document.getElementById("refresh").onclick=()=>load(S.view);
document.getElementById("menu").onclick=()=>document.querySelector(".side").classList.toggle("open");
app.addEventListener("click",onAction);
show()}
function show(){document.querySelectorAll(".view").forEach(x=>x.classList.remove("active"));document.getElementById("view-" +
  S.view)?.classList.add("active");document.querySelectorAll("[data-view]").forEach(x=>x.classList.toggle("active",
  x.dataset.view===S.view));document.getElementById("page-title").textContent=allLabels[S.view]||"Espace";load(S.view)}
function table(items,
  cols,
  kind){const rows=items.map(x=>'<tr class="row-click" data-open="' +
  kind +
  '" data-id="' +
  esc(x.review_id||(x.case_id?(x.case_id +
  (x.level?"::" +
  x.level:"")):null)||x.evidence_id||x.notification_id||x.approval_id||x.member_id||x.id||"") +
  '">' +
  cols.map(c=>'<td>' +
   (c.render?c.render(x):esc(x[c.key])) +
  '</td>').join("") +
  '</tr>').join("");return '<div class="table"><table><thead><tr>' +
  cols.map(c=>'<th>' +
  c.label +
  '</th>').join("") +
  '</tr></thead><tbody>' +
  (rows||'<tr><td colspan="' +
  cols.length +
  '" class="empty">Aucune donnée à afficher.</td></tr>') +
  '</tbody></table></div>'}
function panel(title,
  body,
  actions=""){return '<section class="card panel"><div class="panel-head"><div><h2>' +
  title +
  '</h2></div><div class="actions">' +
  actions +
  '</div></div>' +
  body +
  '</section>'}
function bindList(el,
  items,
  cols,
  kind){el.innerHTML=panel(allLabels[S.view],
  '<input class="search" id="list-search" placeholder="Rechercher…">' +
  table(items,
  cols,
  kind),
  '<span>' +
  items.length +
    ' élément(s)</span>');
    const input=el.querySelector("#list-search");
    input.oninput=()=>{const q=input.value.toLowerCase();
    el.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))};
    el.querySelectorAll("[data-open]").forEach(r=>r.onclick=()=>openDetail(r.dataset.open,
  r.dataset.id))}

function renderTeam(el,items){
  const body='<p>Gérez les membres et leurs droits d’accès. Les changements de rôle sont appliqués côté serveur.</p>' +
   table(items,
   [{label:"Membre",
   render:x=>esc(x.email||x.user_id)},
   {label:"Rôle",
   render:x=>esc(x.role)},
   {label:"Identifiant",
   render:x=>esc(x.user_id)}],
   "team");
 el.innerHTML=panel("Équipe",body,button("Inviter un membre","invite-member","btn primary"));
 el.querySelectorAll("[data-open]").forEach(r=>r.onclick=()=>openDetail("team",r.dataset.id));
}
function renderEscalations(el,items){
  const body='<p>Suivi des alertes d’échéance. La prise en compte et la résolution sont enregistrées côté serveur.</p>' +
   table(items,
   [{label:"Dossier",
   render:x=>esc(x.case_id)},
   {label:"Niveau",
   render:x=>esc(x.level)},
   {label:"État",
   render:x=>esc(x.status)},
   {label:"Assigné",
   render:x=>esc(x.assigned_to||"—")},
   {label:"Temps restant",
   render:x=>esc(x.sla?.remaining_seconds!=null?Math.round(x.sla.remaining_seconds/60) +
   " min":"—")}],
   "escalations");
 el.innerHTML=panel("Escalades SLA",body);
 el.querySelectorAll("[data-open]").forEach(r=>r.onclick=()=>openDetail("escalations",r.dataset.id));
}

async function clientMonitoring(el){
  const [profileResult,
   documentResult,
   googleResult]=await Promise.all([api("/v1/client/profile"),
   api("/v1/client/documents"),
   api("/v1/integrations/google/locations")]);
  const profile=profileResult.profile||{},
   documents=documentResult.items||[],
   locations=googleResult.items||[],
   connections=googleResult.connections||[];
 const editable=["OWNER","ADMIN","CLIENT"].includes(S.role);
  const fields=[["legal_name",
   "Raison sociale"],
   ["website",
   "Site web"],
   ["phone",
   "Téléphone"],
   ["address",
   "Adresse"],
   ["city",
   "Ville"],
   ["postal_code",
   "Code postal"],
   ["country",
   "Pays"],
   ["sector",
   "Secteur"],
   ["employee_count",
   "Effectif"]];
  const inputs=fields.map(([name,
   label])=>'<div class="field"><label>' +
   label +
   '</label><input name="' +
   name +
   '" value="' +
   esc(profile[name]||"") +
   '" maxlength="500" ' +
   (name==="website"?'type="url"':'type="text"') +
   ' ' +
   (!editable?'disabled':'') +
   '></div>').join("");
  const description='<div class="field"><label>Description</label><textarea name="description" rows="4" maxlength="2000" ' +
   (!editable?'disabled':'') +
   '>' +
   esc(profile.description||"") +
   '</textarea></div>';
 const notice=new URLSearchParams(location.search).get("google")==="connected"?'<div class="notice">Compte Google connecté. Sélectionnez une fiche pour synchroniser ses avis.</div>':new URLSearchParams(location.search).get("google")==="denied"?'<div class="notice">La connexion Google a été annulée.</div>':'';
  const googleErrors=(googleResult.errors||[]).map(x=>'<div class="notice">' +
   esc(x.message||"Connexion Google indisponible") +
   '</div>').join("");
  const googleRows=locations.map(x=>'<div class="detail-section"><div class="detail-grid"><div>' +
   field("Établissement",
   x.location_name||x.location_id) +
   '</div><div>' +
   field("Compte",
   x.account_name||x.account_id) +
   '</div></div><button type="button" class="btn ' +
   (x.selected?'primary':'') +
   '" data-google-select="1" data-connection="' +
   esc(x.connection_id) +
   '" data-account="' +
   esc(x.account_id) +
   '" data-location="' +
   esc(x.location_id) +
   '" ' +
   (!editable?'disabled':'') +
   '>' +
   (x.selected?'Établissement sélectionné':'Sélectionner cet établissement') +
   '</button></div>').join("");
  const documentRows=documents.map(d=>'<tr><td>' +
   esc(d.filename) +
   '</td><td>' +
   esc(d.category||"GENERAL") +
   '</td><td>' +
   formatClientBytes(d.size_bytes) +
   '</td><td>' +
   esc(fmt(d.created_at)) +
   '</td><td><button type="button" class="btn" data-document-download="' +
   esc(d.document_id) +
   '">Télécharger</button></td></tr>').join("");
  el.innerHTML=(
        '<div class="client-hub-grid"><section class="card panel"><div class="panel-head"><div' +
        '><h2>Profil de l’entreprise</h2><p>Informations de votre organisation, partagées dans' +
        ' cet espace.</p></div></div><form id="client-profile-form"><div class="detail-grid">'
      ) +
   inputs +
   '</div>' +
   description +
   '<button class="btn primary" type="submit" ' +
   (!editable?'disabled':'') +
   (
        '>Enregistrer le profil</button></form></section><section class="card panel"><div clas' +
        's="panel-head"><div><h2>Google Business Profile</h2><p>Connexion et synchronisation e' +
        'n lecture seule. Aucune réponse ni modification ne sera envoyée à Google.</p></div><s' +
        'pan class="pill">'
      ) +
   connections.length +
   ' connexion(s)</span></div>' +
   notice +
   '<button id="client-google-connect" class="btn primary" type="button" ' +
   (!editable?'disabled':'') +
   '>Connecter un compte Google</button>' +
   googleErrors +
   (googleRows||'<p class="muted">Aucun établissement disponible. Connectez votre compte Google pour afficher ses fiches.</p>') +
   (
        '</section><section class="card panel"><div class="panel-head"><div><h2>Documents de l' +
        '’organisation</h2><p>PDF, images et fichiers texte, 25 Mo maximum par document.</p></' +
        'div><span class="pill">'
      ) +
   documents.length +
   ' document(s)</span></div>' +
   (editable?'<div class="field"><label>Ajouter des documents</label><input id="client-document-input" type="file" multiple accept="application/pdf,image/jpeg,image/png,image/webp,text/plain,text/csv"></div>':'') +
   (
        '<div id="client-document-status" class="muted" aria-live="polite"></div><div class="t' +
        'able"><table><thead><tr><th>Nom</th><th>Catégorie</th><th>Taille</th><th>Ajouté le</t' +
        'h><th></th></tr></thead><tbody>'
      ) +
   (documentRows||'<tr><td colspan="5" class="empty">Aucun document déposé.</td></tr>') +
   '</tbody></table></div></section></div>';
 const form=el.querySelector("#client-profile-form");
  if(form)form.onsubmit=async ev=>{ev.preventDefault();try{await post("/v1/client/profile",
      Object.fromEntries(new FormData(form)));
     el.querySelector("#client-document-status").textContent="Profil enregistré.";
     await clientMonitoring(el)}catch(err){el.querySelector("#client-document-status").textContent=err.message}};
 const connect=el.querySelector("#client-google-connect");
  if(connect)connect.onclick=async()=>{connect.disabled=true;try{const result=await post("/v1/integrations/google/start",
      {});
     if(!result.authorization_url)throw Error("URL Google indisponible");
     location.href=result.authorization_url}catch(err){connect.disabled=false;
     el.querySelector("#client-document-status").textContent=err.message}};
  el.querySelectorAll("[data-google-select]").forEach(button=>button.onclick=async()=>{button.disabled=true;try{const result=await post("/v1/integrations/google/select-location",
   {connection_id:button.dataset.connection,
   account_id:button.dataset.account,
   location_id:button.dataset.location});el.querySelector("#client-document-status").textContent=(result.reviews_synced||0) +
      " avis synchronisés.";
     await clientMonitoring(el)}catch(err){button.disabled=false;
     el.querySelector("#client-document-status").textContent=err.message}});
 const upload=el.querySelector("#client-document-input");
    if(upload)upload.onchange=async()=>{const status=el.querySelector("#client-document-status");
    for(const file of upload.files||[]){try{if(file.size>25*1024*1024)throw Error("Chaque document doit faire 25 Mo maximum.");
    status.textContent="Téléversement de " +
   file.name +
   "…";const encoded=await new Promise((resolve,
      reject)=>{const reader=new FileReader();
     reader.onload=()=>resolve(String(reader.result).split(",")[1]||"");
     reader.onerror=()=>reject(Error("Lecture du fichier impossible"));
     reader.readAsDataURL(file)});
     await post("/v1/client/documents",
   {filename:file.name,
   content_type:file.type||"application/octet-stream",
   content_base64:encoded,
   category:"GENERAL"});status.textContent="Document ajouté : " +
   file.name}catch(err){status.textContent=err.message;return}}await clientMonitoring(el)};
  el.querySelectorAll("[data-document-download]").forEach(button=>button.onclick=async()=>{try{const headers={Authorization:"Bearer " +
   S.token};const response=await fetch("/v1/client/documents/" +
   encodeURIComponent(button.dataset.documentDownload) +
   "/download",
   {headers});if(!response.ok){const data=await response.json().catch(()=>({}));throw Error(data?.error?.message||"Téléchargement impossible")}const blob=await response.blob();const disposition=response.headers.get("Content-Disposition")||"";const filename=disposition.match(/filename="([^"] +
   )"/)?.[1]||"document";const url=URL.createObjectURL(blob);const link=document.createElement("a(
        ");link.href=url;link.download=filename;document.body.appendChild(link);link.click();l" +
        "ink.remove();setTimeout(()=>URL.revokeObjectURL(url),30000)}catch(err){el.querySelect" +
        "or("
      )#client-document-status").textContent=err.message}});
}
function formatClientBytes(value){const n=Number(value||0);if(n<1024)return n +
  " o";if(n<1048576)return (n/1024).toFixed(1) +
  " Ko";return (n/1048576).toFixed(1) +
  " Mo"}
async function load(v){const el=document.getElementById("view-" +
  v);if(!el)return;el.innerHTML='<div class="card">Chargement…</div>';try{
if(v==="dashboard")return await dashboard(el);
if(v==="billing")return await billing(el);
if(v==="client-monitoring")return await clientMonitoring(el);
const urls={reviews:"/v1/reviews",
  cases:"/v1/cases",
  evidence:"/v1/evidence",
  queue:"/v1/review-queue",
  escalations:"/v1/escalations",
  approvals:"/v1/approvals",
  team:"/v1/organization/members",
  notifications:"/v1/notifications",
  submissions:"/v1/submissions"};
const data=arr(await api(urls[v]));S.cache[v]=data;
const cols={
reviews:[{label:"Avis",
  render:x=>esc(x.author_display_name||x.review_id)},
  {label:"Note",
  render:x=>esc(x.rating) +
  "/5"},
  {label:"Date",
  render:x=>esc(fmt(x.published_at))}],
cases:[{label:"Dossier",
  render:x=>esc(x.case_id)},
  {label:"Avis associé",
  render:x=>esc(x.review_id)},
  {label:"Statut",
  render:x=>'<span class="pill">' +
  esc(x.status) +
  '</span>'},
  {label:"Créé le",
  render:x=>esc(fmt(x.created_at))}],
evidence:[{label:"Fichier",
  render:x=>esc(x.filename)},
  {label:"Dossier",
  render:x=>esc(x.case_id)},
  {label:"Intégrité",
  render:x=>'<span class="pill">' +
  esc(x.status|| (x.verified?"VERIFIED":"PENDING")) +
  '</span>'}],
queue:[{label:"Dossier",
  render:x=>esc(x.case_id)},
  {label:"Priorité",
  render:x=>esc(x.priority)},
  {label:"Score",
  render:x=>esc(x.priority_score)},
  {label:"Assigné",
  render:x=>esc(x.assigned_to||"Non assigné")},
  {label:"SLA",
  render:x=>esc(x.sla?.status||"—")}],
escalations:[{label:"Dossier",
  render:x=>esc(x.case_id)},
  {label:"Niveau",
  render:x=>esc(x.level)},
  {label:"État",
  render:x=>esc(x.status)},
  {label:"Assigné",
  render:x=>esc(x.assigned_to||"Non assigné")},
  {label:"Échéance",
  render:x=>esc(fmt(x.due_at||x.created_at))}],
approvals:[{label:"Approbation",
  render:x=>esc(x.approval_id||x.decision_id)},
  {label:"Dossier",
  render:x=>esc(x.case_id)},
  {label:"Statut",
  render:x=>esc(x.status||x.state)}],
team:[{label:"Membre",
  render:x=>esc(x.email||x.name||x.user_id)},
  {label:"Rôle",
  render:x=>esc(x.role)},
  {label:"Statut",
  render:x=>esc(x.status||"Actif")}],
notifications:[{label:"Notification",
  render:x=>esc(x.subject||x.notification_id)},
  {label:"Canal",
  render:x=>esc(x.channel)},
  {label:"Statut",
  render:x=>esc(x.status)},
  {label:"Créée le",
  render:x=>esc(fmt(x.created_at))}],
submissions:[{label:"Soumission",
  render:x=>esc(x.submission_id||x.case_id)},
  {label:"Dossier",
  render:x=>esc(x.case_id)},
  {label:"Statut",
  render:x=>esc(x.status)}]
};
if(v==="team")return renderTeam(el,
  data);if(v==="escalations")return renderEscalations(el,
  data);bindList(el,
  data,
  cols[v]||[{label:"Élément",
  key:"id"}],
  v);
}catch(e){el.innerHTML=panel(allLabels[v]||v,'<div class="notice">'+esc(e.message)+'</div>')}}
async function dashboard(el){
 const jobs=[api("/v1/reviews"),api("/v1/cases")];
 if(can("operator"))jobs.push(api("/v1/notifications").catch(()=>({items:[]})));
 if(can("manager"))jobs.push(api("/v1/approvals").catch(()=>({items:[]})));
 const rs=await Promise.allSettled(jobs);
 const values=rs.map(x=>x.status==="fulfilled"?arr(x.value):[]);
 const reviews=values[0]||[],cases=values[1]||[],notifications=values[2]||[],approvals=values[can("operator")?3:2]||[];
  const stats=[["Avis suivis",
   reviews.length,
   "Avis enregistrés dans votre organisation"],
   ["Dossiers",
   cases.length,
   "Dossiers accessibles selon vos droits"]];
 if(can("operator"))stats.push(["Notifications",notifications.length,"Éléments de suivi et d’alerte"]);
  if(can("manager"))stats.push(["À valider",
   approvals.filter(x=>!["APPROVED",
   "REJECTED",
   "COMPLETED"].includes(String(x.status||x.state||"").toUpperCase())).length,
   "Approbations encore ouvertes"]);
  const shortcuts=[["reviews",
   "Consulter les avis",
   "Retrouver les avis et leurs informations."],
   ["cases",
   "Ouvrir les dossiers",
   "Suivre les dossiers, preuves et décisions."],
   ["evidence",
   "Voir les preuves",
   "Contrôler les pièces et leur intégrité."]];
 if(can("operator"))shortcuts.push(["queue","File de traitement","Voir les dossiers à prendre en charge."]);
 if(can("manager"))shortcuts.push(["approvals","Approbations","Examiner les validations en attente."]);
  el.innerHTML='<div class="cards">' +
   stats.map(x=>'<div class="card k"><small>' +
   esc(x[0]) +
   '</small><strong>' +
   x[1] +
   '</strong><span>' +
   esc(x[2]) +
   '</span></div>').join("") +
   '</div>'+
  panel("Votre parcours Review Defense",
   (
        '<p>Retrouvez les principales étapes du traitement. Les actions restent soumises aux a' +
        'utorisations de votre compte et aux validations prévues.</p><div class="steps"><span>' +
        '<b>01</b> Analyse</span><span><b>02</b> Dossier</span><span><b>03</b> Preuves</span><' +
        'span><b>04</b> Validation humaine</span><span><b>05</b> Suivi</span></div>'
      ))+
  panel("Accès rapides",
   '<div class="service-strip">' +
   shortcuts.map(x=>'<button type="button" class="dashboard-shortcut" data-dashboard-view="' +
   x[0] +
   '"><b>' +
   esc(x[1]) +
   '</b><span>' +
   esc(x[2]) +
   '</span><i aria-hidden="true">→</i></button>').join("") +
   '</div>')+
  panel("Dossiers récents",
   cases.length?table(cases.slice(0,
   5),
   [{label:"Dossier",
   render:x=>esc(x.case_id)},
   {label:"Avis associé",
   render:x=>esc(x.review_id)},
   {label:"Statut",
   render:x=>'<span class="pill">' +
   esc(x.status) +
   '</span>'},
   {label:"Créé le",
   render:x=>esc(fmt(x.created_at))}],
   "cases"):'<div class="empty">Aucun dossier pour le moment. Créez un dossier depuis la fiche d’un avis.</div>');
 el.querySelectorAll("[data-dashboard-view]").forEach(b=>b.onclick=()=>{S.view=b.dataset.dashboardView;show()});
 el.querySelectorAll('[data-open="cases"]').forEach(row=>row.onclick=()=>openDetail("cases",row.dataset.id));
}
async function billing(el){const items=arr(await api("/v1/billing/catalog"));el.innerHTML=panel("Catalogue des offres",
  '<p>Les informations tarifaires sont chargées depuis le backend.</p>' +
  table(items,
  [{label:"Offre",
  render:x=>esc(x.name_fr||x.offer_id)},
  {label:"Type",
  render:x=>esc(x.kind)},
  {label:"Prix",
  render:x=>esc(x.amount!=null?x.amount +
  " " +
  (x.currency||"EUR"):"Sur devis")}],
  "billing"))}
async function openDetail(kind,
    id){if(!id)return;
    const root=document.getElementById("modal-root");
    root.innerHTML='<div class="overlay"><section class="card drawer">Chargement de la fiche…</section></div>';
    try{let data={},
  title=kind; if(kind==="reviews"){data=await api("/v1/reviews/" +
  encodeURIComponent(id));title="Fiche avis"}
if(kind==="cases"){const base="/v1/cases/" +
  encodeURIComponent(id);const results=await Promise.allSettled([api(base),
  api(base +
  "/workspace"),
  api(base +
  "/history"),
  api(base +
  "/sla"),
  api(base +
  "/review-checklist"),
  api(base +
  "/evidence-matrix"),
  api(base +
  "/contradictions")]);data={};["detail",
  "workspace",
  "history",
  "sla",
  "checklist",
  "matrix",
  "contradictions"].forEach((k,
  i)=>{if(results[i].status==="fulfilled")data[k]=results[i].value;else data[k +
  "_error"]=results[i].reason.message});title="Dossier " +
  id}
if(kind==="evidence"){data=await api("/v1/evidence/"+encodeURIComponent(id));title="Preuve"}
if(kind==="queue"){const q=(S.cache.queue||[]).find(x=>x.case_id===id);data={queue:q};title="File de traitement"}
if(kind==="approvals"){data=(S.cache.approvals||[]).find(x=>(x.approval_id||x.decision_id)===id)||{};title="Approbation"}
if(kind==="notifications"){data=(S.cache.notifications||[]).find(x=>(x.notification_id||x.id)===id)||{};title="Notification"}
if(kind==="team"){data=(S.cache.team||[]).find(x=>(x.member_id||x.user_id)===id)||{};title="Membre"}
if(kind==="escalations"){const parts=id.split("::");
  data=(S.cache.escalations||[]).find(x=>x.case_id===parts[0]&&(!parts[1]||x.level===parts[1]))||{};
  title="Escalade SLA"}
renderDetail(root,kind,id,title,data)
}catch(e){root.innerHTML=(
        '<div class="overlay"><section class="card drawer"><button class="btn close" data-acti' +
        'on="close">×</button><div class="notice">'
      ) +
  esc(e.message) +
  '</div></section></div>'}}
function jsonBlock(x){return '<pre class="data-fallback">'+esc(JSON.stringify(x,null,2))+'</pre>'}
function objectRows(x){if(!x||typeof x!=="object")return [];return Array.isArray(x)?x:Object.entries(x).map(([key,
  value])=>({key,
  value}))}
function valueText(x){if(x==null||x==="")return "—";if(typeof x==="object")return JSON.stringify(x);return String(x)}
function recordList(rows,
  emptyLabel){if(!Array.isArray(rows)||!rows.length)return '<div class="empty-inline">' +
  esc(emptyLabel) +
  '</div>';return '<div class="record-list">' +
  rows.map((x,
  i)=>'<article class="record-item"><div class="record-index">' +
  (i +
  1) +
  '</div><div class="record-content"><b>' +
  esc(x.title||x.label||x.key||x.type||("Élément " +
  (i +
  1))) +
  '</b><p>' +
  esc(x.description||x.text||x.value||x.message||x.detail||"") +
  '</p><small>' +
  esc(x.status||x.state||x.category||x.source||"") +
  '</small></div></article>').join("") +
  '</div>'}
function evidenceList(rows){if(!Array.isArray(rows)||!rows.length)return '<div class="empty-inline">Aucune preuve ajoutée à ce dossier.</div>';
  return '<div class="evidence-list">' +
  rows.map(x=>'<article class="evidence-item"><div><b>' +
  esc(x.filename||x.name||x.evidence_id||"Pièce") +
  '</b><small>' +
  esc(x.content_type||x.kind||"Fichier") +
  " · " +
  esc(x.size_bytes!=null?x.size_bytes +
  " octets":"Taille non renseignée") +
  '</small></div><span class="pill">' +
  esc(x.status||(x.verified?"Vérifiée":"À vérifier")) +
  '</span></article>').join("") +
  '</div>'}
function historyList(rows){if(!Array.isArray(rows)||!rows.length)return '<div class="empty-inline">Aucun événement d’historique disponible.</div>';
  return '<div class="history-list">' +
  rows.map(x=>'<article class="history-item"><span class="history-dot"></span><div><b>' +
  esc(x.title||x.action||x.event_type||x.event||"Événement") +
  '</b><p>' +
  esc(x.description||x.message||x.rationale||x.actor_email||x.actor_id||"") +
  '</p><small>' +
  esc(fmt(x.created_at||x.timestamp||x.occurred_at)) +
  '</small></div></article>').join("") +
  '</div>'}
function keyValueList(x){const rows=objectRows(x);
  if(!rows.length)return '<div class="empty-inline">Aucune donnée disponible.</div>';
  return '<div class="key-value-list">' +
  rows.map(r=>'<div><span>' +
  esc(r.key||r.label) +
  '</span><b>' +
  esc(valueText(r.value)) +
  '</b></div>').join("") +
  '</div>'}
function factsMarkup(rows,
  evidenceRows,
  caseId){if(!rows.length)return '<p class="muted">Aucun fait extrait pour le moment.</p>';return (
        '<div class="table"><table><thead><tr><th>Fait</th><th>Valeur proposée</th><th>Source<' +
        '/th><th>État</th><th></th></tr></thead><tbody>'
      ) +
  rows.map(x=>{const evidence=(evidenceRows||[]).find(e=>e.evidence_id===x.evidence_id);return '<tr><td>' +
  esc(x.key) +
  '</td><td>' +
  esc(x.value) +
  '</td><td>' +
  esc(x.source_location||x.evidence_id) +
  '</td><td>' +
  (x.verified?'<span class="pill">Vérifié</span>':'<span class="pill">À vérifier</span>') +
  '</td><td>' +
  (!x.verified&&(evidence?.verified||evidence?.status==="VERIFIED")?button("Vérifier",
  "verify-fact:" +
  x.evidence_id +
  ":" +
  caseId +
  ":" +
  x.fact_id):"") +
  ( !(evidence?.verified||evidence?.status==="VERIFIED")?'<small>Vérifier d’abord la preuve</small>':"") +
  '</td></tr>'}).join("") +
    '</tbody></table></div>'}function contradictionsMarkup(rows){if(!rows.length)return '<p class="muted">Aucune contradiction enregistrée. Une analyse peut être lancée par un administrateur.</p>';
    return '<div class="table"><table><thead><tr><th>Description</th><th>Éléments</th><th>Statut</th></tr></thead><tbody>' +
  rows.map(x=>'<tr><td>' +
  esc(x.description) +
  '</td><td>' +
  esc((x.evidence_ids||[]).join(", ")) +
  '</td><td>' +
  esc(x.disposition?.status||"À examiner") +
  '</td></tr>').join("") +
  '</tbody></table></div>'}function renderDetail(root,
  kind,
  id,
  title,
  d){let body="",
  actions="";
if(kind==="reviews"){const r=d.review||{};body='<div class="detail-grid">' +
  field("Identifiant",
  r.review_id) +
  field("Auteur",
  r.author_display_name) +
  field("Note",
  r.rating +
  "/5") +
  field("Publié le",
  fmt(r.published_at)) +
  field("Source",
  r.source) +
  field("Langue",
  r.language) +
  '</div><h3>Texte de l’avis</h3><p>' +
  esc(r.text) +
  '</p><h3>Réclamations / affirmations détectées</h3>' +
  jsonBlock(d.claims||[]) +
   '<h3>Signaux de politique</h3>' +
  jsonBlock(d.policy_signals||[]);if(["CLIENT",
  "OWNER",
  "ADMIN",
  "ANALYST"].includes(S.role))actions+=button("Créer un dossier",
  "create-case:" +
  id,
  "btn primary")}
else if(kind==="cases"){const c=d.detail?.case||{},w=d.workspace?.workspace||{};S.cache.caseDetails[id]=c;
  const claims=d.detail?.claims||[],
   signals=d.detail?.policy_signals||[],
   evidence=w.evidence||[],
   facts=d.workspace?.fact_suggestions||[],
   history=d.history?.items||[],
   approvalRows=d.workspace?.approvals||[];
 const decision=d.workspace?.decision||{},sla=d.sla?.sla||d.sla||{};
  body='<div class="case-summary"><div class="case-summary-main"><small>DOSSIER</small><b>' +
   esc(c.case_id||id) +
   '</b><span class="pill">' +
   esc(c.status||"Statut inconnu") +
   '</span></div><div class="case-summary-meta">' +
   field("Avis associé",
   c.review_id) +
   field("Assigné à",
   c.assigned_to) +
   field("Créé le",
   fmt(c.created_at)) +
   field("État SLA",
   sla.status||"—") +
   '</div></div>'+
  '<section class="detail-section"><h3>Avis associé</h3><blockquote class="review-quote">' +
   esc(d.detail?.review?.text||w.review?.text||"Texte de l’avis indisponible.") +
   '</blockquote><div class="detail-grid compact">' +
   field("Auteur",
   d.detail?.review?.author_display_name||w.review?.author_display_name) +
   field("Note",
   (d.detail?.review?.rating??w.review?.rating)!=null?(d.detail?.review?.rating??w.review?.rating) +
   "/5":"—") +
   field("Source",
   d.detail?.review?.source||w.review?.source) +
   field("Publié le",
   fmt(d.detail?.review?.published_at||w.review?.published_at)) +
   '</div></section>'+
  (
        '<section class="detail-section"><h3>Analyse de l’avis</h3><div class="detail-subsecti' +
        'on"><b>Affirmations identifiées</b>'
      ) +
   recordList(claims,
   "Aucune affirmation structurée disponible.") +
   '</div><div class="detail-subsection"><b>Signaux de politique</b>' +
   recordList(signals,
   "Aucun signal structuré disponible.") +
   '</div></section>'+
  '<section class="detail-section"><h3>Préparation du dossier</h3>' +
   keyValueList(d.checklist?.items||d.checklist) +
   '</section>'+
 '<section class="detail-section"><h3>Preuves et pièces jointes</h3>'+evidenceList(evidence)+'</section>'+
 '<section class="detail-section"><h3>Matrice des preuves</h3>'+keyValueList(d.matrix?.matrix||d.matrix)+'</section>'+
 '<section class="detail-section"><h3>Faits extraits à vérifier</h3>'+factsMarkup(facts,evidence,id)+'</section>'+
  '<section class="detail-section"><h3>Contradictions détectées</h3>' +
   contradictionsMarkup(d.contradictions?.contradictions||[]) +
   '</section>'+
  '<section class="detail-section"><h3>Décision et approbations</h3>' +
   keyValueList({decision,
   approvals:approvalRows,
   snapshot:d.workspace?.snapshot||"Aucun instantané"}) +
   '</section>'+
 '<section class="detail-section"><h3>Chronologie du dossier</h3>'+historyList(history)+'</section>'+
  (d.history_error||d.checklist_error||d.matrix_error?'<div class="notice">Certaines informations complémentaires n’ont pas pu être chargées : ' +
   esc([d.history_error,
   d.checklist_error,
   d.matrix_error].filter(Boolean).join(" · ")) +
   '</div>':"");

if(can("operator")){actions+=button("Ajouter une preuve",
  "upload-evidence:" +
  id,
    "btn primary");
    if(!c.assigned_to||c.assigned_to===S.userId||can("manager"))actions+=button(c.assigned_to?"Libérer l’affectation":"Prendre en charge",
  "claim-case:" +
  id);actions+=button("Vérifier checklist",
  "checklist:" +
  id);}
if(can("manager")){actions+=button("Extraire les faits",
  "extract-facts:" +
  id);actions+=button("Analyser les contradictions",
  "analyze-contradictions:" +
  id);actions+=button("Créer une décision",
  "decision:" +
  id);if(c.decision_id)actions+=button("Geler la décision",
  "freeze:" +
  id);actions+=button("Mettre en pause SLA",
  "pause-sla:" +
  id);actions+=button("Reprendre SLA",
  "resume-sla:" +
  id);actions+=button("Approuver",
  "approve:" +
  id);actions+=button("Préparer la soumission",
  "submit:" +
  id)}}
else if(kind==="team"){const m=d||{};body='<div class="detail-grid">' +
  field("Identifiant",
  m.user_id) +
  field("Email",
  m.email) +
  field("Rôle",
  m.role) +
    '</div><p>Un changement de rôle invalide les sessions existantes du membre.</p>';
    if(can("manager")&&m.user_id!==undefined)actions+=button("Modifier le rôle",
  "edit-role:" +
  m.user_id,
  "btn primary")}
else if(kind==="notifications"){const n=d||{};body='<div class="detail-grid">' +
  field("Sujet",
  n.subject) +
  field("Canal",
  n.channel) +
  field("Statut",
  n.status) +
  field("Créée le",
  fmt(n.created_at)) +
  field("Destinataire",
  n.target) +
  '</div><h3>Contenu</h3><p>' +
  esc(n.body) +
  '</p>';if(can("manager")&&!["SENT",
  "CANCELLED",
  "DELIVERED"].includes(n.status)){actions+=button("Envoyer maintenant",
  "deliver-notification:" +
  id,
  "btn primary");actions+=button("Annuler",
  "cancel-notification:" +
  id)}}
else if(kind==="escalations"){const x=d||{};body='<div class="detail-grid">' +
  field("Dossier",
  x.case_id) +
  field("Niveau",
  x.level) +
  field("État",
  x.status) +
  field("Assigné",
  x.assigned_to) +
  field("Priorité SLA",
  x.sla?.priority) +
  field("Temps restant (s)",
  x.sla?.remaining_seconds) +
  '</div>';if(can("operator")&&x.status!=="RESOLVED"){actions+=button("Prendre en compte",
  "ack-escalation:" +
  x.case_id +
  ":" +
  x.level);actions+=button("Résoudre",
  "resolve-escalation:" +
  x.case_id +
  ":" +
  x.level)}if(can("manager")&&x.status!=="RESOLVED")actions+=button("Créer une notification",
  "notify-escalation:" +
  encodeURIComponent(x.case_id) +
  "~" +
  x.level,
  "btn primary") }
else if(kind==="evidence"){const e=d.evidence||{};body='<div class="detail-grid">' +
  field("Fichier",
  e.filename) +
  field("Dossier",
  e.case_id) +
  field("Type",
  e.content_type) +
  field("Taille",
  e.size_bytes +
  " octets") +
  field("SHA-256",
  e.sha256) +
  field("État",
  e.status) +
  '</div><p>La vérification contrôle l’intégrité du fichier côté serveur.</p>';body+='<p>' +
  button("Télécharger la preuve",
  "download-evidence:" +
  id) +
  '</p>';if(can("operator")&&!e.verified)actions+=button("Vérifier l’intégrité",
  "verify-evidence:" +
  id,
  "btn primary")}
else body=jsonBlock(d);
root.innerHTML='<div class="overlay"><section class="card drawer"><button class="btn close" data-action="close">×</button><h2>' +
  esc(title) +
  (
        '</h2><p class="muted">Données et opérations issues du backend Review Defense.</p><div' +
        ' class="actions" style="flex-wrap:wrap;margin:14px 0">'
      ) +
  actions +
  '</div>' +
  body +
  '</section></div>'}
function modal(title,
    form){const root=document.getElementById("modal-root");
    root.innerHTML='<div class="overlay"><section class="card drawer"><button class="btn close" data-action="close">×</button><h2>' +
  esc(title) +
  '</h2>' +
  form +
  '</section></div>'}
async function onAction(e){const b=e.target.closest("[data-action]");
  if(!b)return;
  const action=b.dataset.action;
  if(action==="close"){document.getElementById("modal-root").innerHTML="";
  return}
const [op,id]=action.split(":");try{
if(op==="invite-member"){modal("Inviter un membre",
  (
        '<form id="invite-form"><div class="field"><label>Adresse email</label><input name="em' +
        'ail" type="email" required></div><div class="field"><label>Rôle</label><select name="' +
        'role"><option value="CLIENT">Client</option><option value="ANALYST">Analyste</option>' +
        '<option value="VIEWER">Lecture seule</option><option value="ADMIN">Administrateur</op' +
        'tion></select></div><button class="btn primary">Créer l’invitation</button><p class="' +
        'notice">Le backend crée un jeton à usage unique. Cette action n’envoie pas d’email.</' +
        'p></form>'
      ));document.getElementById("invite-form").onsubmit=async ev=>{ev.preventDefault();const result=await post("/v1/organization/invitations",
  Object.fromEntries(new FormData(ev.currentTarget)));S.lastInvitationToken=result.invitation_token;modal("Invitation créée",
  (
        '<p>Copiez et transmettez ce jeton à la personne invitée. Il ne sera affiché qu’une fo' +
        'is.</p><pre style="white-space:pre-wrap;overflow-wrap:anywhere">'
      ) +
  esc(result.invitation_token) +
  '</pre><p class="muted">Expiration : ' +
  esc(fmt(result.expires_at)) +
    '</p><button class="btn primary" data-action="copy-token">Copier le jeton</button>');
    S.cache.team=arr(await api("/v1/organization/members"));
    };
    return}
if(op==="copy-token"){await navigator.clipboard.writeText(S.lastInvitationToken||"");b.textContent="Copié";return}
if(op==="edit-role"){const member=(S.cache.team||[]).find(x=>x.user_id===id);if(!member)return;modal("Modifier le rôle",
  '<form id="role-form"><div class="field"><label>Membre</label><input value="' +
  esc(member.email) +
  (
        '" disabled></div><div class="field"><label>Nouveau rôle</label><select name="role"><o' +
        'ption value="CLIENT">Client</option><option value="ANALYST">Analyste</option><option ' +
        'value="VIEWER">Lecture seule</option><option value="ADMIN">Administrateur</option><op' +
        'tion value="OWNER">Propriétaire</option></select></div><button class="btn primary">En' +
        'registrer</button></form>'
            ));
        if(S.role!=="OWNER")document.querySelector("#role-form [value=OWNER]")?.remove();
        document.querySelector("#role-form [name=role]").value=member.role;
        document.getElementById("role-form").onsubmit=async ev=>{ev.preventDefault();
        await post("/v1/organization/members/" +
  encodeURIComponent(id) +
  "/role",
    Object.fromEntries(new FormData(ev.currentTarget)));
    S.cache.team=arr(await api("/v1/organization/members"));
    await load("team");
    document.getElementById("modal-root").innerHTML="";
    };
    return}
if(op==="notify-escalation"){const [caseId,
  level]=id.split("~");modal("Créer une notification d’escalade",
  (
        '<form id="notify-form"><div class="field"><label>Canal</label><select name="channel">' +
        '<option value="IN_APP">Dans l’application</option><option value="EMAIL">Email</option' +
        '><option value="WEBHOOK">Webhook</option></select></div><div class="field"><label>Des' +
        'tinataire</label><input id="notify-target" name="target" required value="'
      ) +
  esc(S.userId) +
  (
        '" placeholder="Identifiant du membre"></div><small id="notify-target-help" class="mut' +
        'ed">Pour IN_APP, indiquez l’identifiant du membre destinataire.</small><div class="fi' +
        'eld"><label>Objet</label><input name="subject" required value="'
      ) +
  esc("Escalade SLA " +
  level +
  " — " +
  caseId) +
  '"></div><div class="field"><label>Message</label><textarea name="body" required rows="5">' +
  esc("Une escalade SLA de niveau " +
  level +
  " concerne le dossier " +
  caseId +
  ".") +
  (
        '</textarea></div><button class="btn primary">Mettre en file d’envoi</button><p class=' +
        '"notice">La notification est créée selon la politique de l’organisation. Aucun envoi ' +
        'externe n’est déclenché par cette étape.</p></form>'
      ));document.getElementById("notify-form").elements.channel.onchange=ev=>{const target=document.getElementById("notify-target"),
  help=document.getElementById("notify-target-help"),
    channel=ev.target.value;
    if(channel==="EMAIL"){if(!target.value||target.value===S.userId)target.value=S.userEmail||"";
    target.placeholder="destinataire@entreprise.fr";
    help.textContent="Adresse email destinataire. L’envoi nécessite une configuration SMTP et une politique autorisant l’email."}else if(channel==="WEBHOOK"){if(target.value===S.userId||target.value===S.userEmail)target.value="";
    target.placeholder="https://exemple.fr/webhook";
    help.textContent="URL HTTPS publique. Les adresses privées et locales sont refusées par le serveur."}else{if(!target.value||target.value===S.userEmail)target.value=S.userId||"";
    target.placeholder="Identifiant du membre";
    help.textContent="Identifiant du membre destinataire dans l’organisation."}};
    document.getElementById("notify-form").onsubmit=async ev=>{ev.preventDefault();
    const payload=Object.fromEntries(new FormData(ev.currentTarget));
    payload.level=level;
    const result=await post("/v1/escalations/" +
  encodeURIComponent(decodeURIComponent(caseId)) +
  "/notify",
  payload);S.cache.notifications=arr(await api("/v1/notifications"));modal("Notification créée",
  '<p>La notification a été mise en file côté serveur.</p>' +
  jsonBlock(result.notification));};return}
if(op==="ack-escalation"||op==="resolve-escalation"){const parts=action.split(":");const caseId=parts[1],
  level=parts[2];await post("/v1/escalations/" +
  encodeURIComponent(caseId) +
  "/" +
  (op==="ack-escalation"?"acknowledge":"resolve"),
  {level});S.cache.escalations=arr(await api("/v1/escalations"));return openDetail("escalations",
  caseId +
  "::" +
  level)}
if(op==="deliver-notification"||op==="cancel-notification"){await post("/v1/notifications/" +
  encodeURIComponent(id) +
  "/" +
  (op==="deliver-notification"?"deliver":"cancel"));S.cache.notifications=arr(await api("/v1/notifications"));return openDetail("notifications",
  id)}
if(op==="create-case"){await post("/v1/cases",
  {review_id:id});document.getElementById("modal-root").innerHTML="";S.view="cases";show();return}
if(op==="download-evidence"){const file=await api("/v1/evidence/" +
  encodeURIComponent(id) +
    "/content");
    const binary=atob(file.content_base64);
    const bytes=new Uint8Array(binary.length);
    for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
    const blob=new Blob([bytes],
    {type:file.content_type||"application/octet-stream"});
    const url=URL.createObjectURL(blob);
    const link=document.createElement("a");
    link.href=url;
    link.download=file.filename||"preuve";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    return}
if(op==="verify-evidence"){await post("/v1/evidence/" +
  encodeURIComponent(id) +
  "/verify");return openDetail("evidence",
  id)}
if(op==="extract-facts"){await post("/v1/cases/"+id+"/extract-facts",{});return openDetail("cases",id)}
if(op==="analyze-contradictions"){await post("/v1/cases/"+id+"/contradictions",{});return openDetail("cases",id)}
if(op==="verify-fact"){const parts=action.split(":");const evidenceId=parts[1],
  caseId=parts[2],
  factId=parts[3];await post("/v1/evidence/" +
  encodeURIComponent(evidenceId) +
  "/facts/verify",
  {fact_ids:[factId]});return openDetail("cases",
  caseId)}
if(op==="disposition"){const parts=action.split(":");const caseId=parts[1],
  contradictionId=parts[2];modal("Qualifier la contradiction",
  (
        '<form id="disposition-form"><div class="field"><label>Qualification</label><select na' +
        'me="status" required><option value="CONFIRMED">Confirmée</option><option value="DISMI' +
        'SSED">Écartée</option><option value="NEEDS_REVIEW">À approfondir</option></select></d' +
        'iv><div class="field"><label>Justification</label><textarea name="rationale" required' +
        ' rows="4"></textarea></div><button class="btn primary">Enregistrer</button></form>'
      ));document.getElementById("disposition-form").onsubmit=async ev=>{ev.preventDefault();await post("/v1/cases/" +
  caseId +
  "/contradictions/" +
  contradictionId +
  "/disposition",
  Object.fromEntries(new FormData(ev.currentTarget)));await openDetail("cases",
  caseId)};return}
if(op==="claim-case"){const row=(S.cache.queue||[]).find(x=>x.case_id===id);
  const assignedTo=S.cache.caseDetails?.[id]?.assigned_to??row?.assigned_to;
  if(assignedTo&&assignedTo!==S.userId&&!can("manager"))throw Error("Ce dossier est attribué à un autre membre.");
  await post("/v1/review-queue/" +
  encodeURIComponent(id) +
  (assignedTo?"/unclaim":"/claim"));return openDetail("cases",
  id)}
if(op==="upload-evidence"){modal("Ajouter une preuve",
  (
        '<form id="evidence-form"><div class="field"><label>Fichier</label><input type="file" ' +
        'name="file" required></div><button class="btn primary">Envoyer la preuve</button><p c' +
        'lass="notice">Le fichier est transmis au serveur via le endpoint sécurisé de dépôt.</' +
        'p></form>'
            ));
        document.getElementById("evidence-form").onsubmit=async ev=>{ev.preventDefault();
        const file=ev.currentTarget.elements.file.files[0];
        const b64=await new Promise((resolve,
    reject)=>{const reader=new FileReader();
    reader.onload=()=>resolve(String(reader.result).split(",")[1]);
    reader.onerror=reject;
    reader.readAsDataURL(file)});
    await post("/v1/evidence",
  {case_id:id,
  filename:file.name,
  content_type:file.type||"application/octet-stream",
  content_base64:b64});await openDetail("cases",
  id)};return}
if(op==="decision"){modal("Créer une décision",
  (
        '<form id="decision-form"><div class="field"><label>Type</label><select name="kind"><o' +
        'ption value="HUMAN_REVIEW">Examen humain</option><option value="NO_ACTION">Aucune act' +
        'ion</option></select></div><div class="field"><label>Motif obligatoire</label><textar' +
        'ea name="rationale" required rows="5"></textarea></div><button class="btn primary">En' +
        'registrer la décision</button></form>'
      ));document.getElementById("decision-form").onsubmit=async ev=>{ev.preventDefault();await post("/v1/cases/" +
  id +
  "/decision",
  Object.fromEntries(new FormData(ev.currentTarget)));await openDetail("cases",
  id)};return}
if(op==="freeze"){if(!confirm("Geler la décision et créer son instantané ?"))return;await post("/v1/cases/" +
  id +
  "/freeze");return openDetail("cases",
  id)}
if(op==="approve"){if(!confirm("Confirmer l’approbation de la décision gelée ?"))return;await post("/v1/cases/" +
  id +
  "/approve");return openDetail("cases",
  id)}
if(op==="submit"){if(!confirm("Préparer la soumission ? Cette action sera enregistrée côté serveur."))return;await post("/v1/cases/" +
  id +
  "/submit",
  {});return openDetail("cases",
  id)}
if(op==="pause-sla"||op==="resume-sla"){if(op==="pause-sla"){modal("Mettre en pause le SLA",
  (
        '<form id="sla-form"><div class="field"><label>Motif obligatoire</label><textarea name' +
        '="reason" required maxlength="500" rows="4"></textarea></div><button class="btn prima' +
        'ry">Confirmer la pause</button></form>'
      ));document.getElementById("sla-form").onsubmit=async ev=>{ev.preventDefault();await post("/v1/cases/" +
  id +
  "/pause-sla",
  Object.fromEntries(new FormData(ev.currentTarget)));await openDetail("cases",
  id)}}else{if(!confirm("Reprendre le SLA ?"))return;await post("/v1/cases/" +
  id +
  "/resume-sla");await openDetail("cases",
  id)}return}
if(op==="checklist"){const d=await api("/v1/cases/" +
  id +
  "/review-checklist");const rows=arr(d).length?arr(d):d.items||[];modal("Checklist du dossier",
  '<form id="checklist-form">' +
  rows.map(x=>'<label style="display:block;padding:10px;border-bottom:1px solid #eee"><input type="checkbox" data-code="' +
  esc(x.code) +
  '" ' +
  (x.completed?"checked":"") +
  '> ' +
  esc(x.label||x.code) +
  '</label>').join("") +
    '<button class="btn primary">Enregistrer les éléments cochés</button></form>');
    document.getElementById("checklist-form").onsubmit=async ev=>{ev.preventDefault();
    for(const input of ev.currentTarget.querySelectorAll("[data-code]"))await post("/v1/cases/" +
  id +
  "/review-checklist",
  {code:input.dataset.code,
  completed:input.checked});await openDetail("cases",
  id)};return}
}catch(err){modal("Action non effectuée",'<div class="notice">'+esc(err.message)+'</div>')}}
async function start(){if(location.pathname==="/verify-email")return verifyEmail();
  if(location.pathname==="/reset-password")return recovery();
  if(location.pathname==="/accept-invitation")return acceptInvitation();
  if(!S.token){if(["/client",
  "/client/",
  "/admin",
  "/admin/"].includes(location.pathname)){location.replace("/connexion?next=" +
  encodeURIComponent(location.pathname +
    location.search));
    return}return login()}try{const me=await api("/v1/me");
    S.userId=me.user_id||null;
    S.userEmail=me.email||null;
    S.role=me.role||S.role;
    localStorage.setItem("rd_role",
    S.role);
    const requestedView=new URLSearchParams(location.search).get("page");
    if(requestedView&&allLabels[requestedView])S.view=requestedView;
    const query=location.search||"";
    if(adminPath()&&!can("manager")){location.replace("/client" +
  query);return}if(!adminPath()&&can("manager")){location.replace("/admin" +
  query);return}shell()}catch(e){localStorage.removeItem("rd_token");localStorage.removeItem("rd_role");S.token=null;login()}}
start();
})();