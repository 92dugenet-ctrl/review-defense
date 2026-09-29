import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

const links = [
  ["dashboard","Vue d’ensemble","⌂"],["reviews","Avis","◌"],["cases","Dossiers","◇"],["analysis","Analyse","↗"],["notifications","Notifications","◍"],["billing","Facturation","€"]
] as const;

export function AppShell(){
 const {user,logout}=useAuth(); const location=useLocation();
 const admin=["OWNER","ADMIN","admin","owner"].includes(user?.role??"");
 return <div className="app-shell">
  <aside className="app-sidebar">
   <NavLink to="/app/dashboard" className="brand"><span className="brand-mark">R</span><span>review defense</span></NavLink>
   <div className="sidebar-section"><span className="sidebar-label">Espace de travail</span>{links.map(([id,label,icon])=><NavLink key={id} to={"/app/"+id} className={({isActive})=>"side-link"+(isActive?" active":"")}><span>{icon}</span>{label}</NavLink>)}</div>
   <div className="sidebar-bottom">
    {admin&&<NavLink to="/app/admin" className={({isActive})=>"side-link"+(isActive?" active":"")}><span>✦</span>Administration</NavLink>}
    <NavLink to="/app/settings" className={({isActive})=>"side-link"+(isActive?" active":"")}><span>⚙</span>Paramètres</NavLink>
    <div className="account-chip"><div className="avatar">{(user?.email?.[0]??"U").toUpperCase()}</div><div><strong>{user?.email??"Compte"}</strong><small>{user?.role??"Utilisateur"}</small></div><button onClick={()=>void logout()} aria-label="Se déconnecter">↗</button></div>
   </div>
  </aside>
  <main className="app-main">
   <header className="app-topbar"><div><span className="topbar-context">Espace client</span><span className="topbar-path">{location.pathname.replace("/app","")||"/"}</span></div><div className="topbar-actions"><span className="live-dot">● Connecté</span><button className="icon-button" onClick={()=>void logout()} aria-label="Déconnexion">↗</button></div></header>
   <Outlet/>
  </main>
 </div>
}