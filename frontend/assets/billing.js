// Billing and PayPal integration isolated from the console shell.
const PAYPAL_HOSTED_CLIENT_ID='BAAftx79q4rSHY7vc2aYy_hgx3KB6GB15k__TBghUQyd1_ixXSqv71UHw1RXZvkR4cli25WsSirUKWt7zs';
const PAYPAL_SUBSCRIPTION_CLIENT_ID='BAADwFz5aRpmMnNRVADMoONwkWyHzC3Y-l75vTda13-4tfwv2gSa4TdAq_jguOBTz2kBqsU1ARHCQ7nz6k';

function selectClientBillingOffer(type,name,price,offerId){try{localStorage.setItem('rd_selected_offer',JSON.stringify({type,name,price,offer_id:offerId||null,selected_at:new Date().toISOString()}))}catch(_){}if(offerId)showBillingPayment()}

function selectedBillingOffer(){try{return JSON.parse(localStorage.getItem('rd_selected_offer')||'null')}catch(_){return null}}

async function loadPayPalSdk(clientId,components,locale,extra=''){
 const key=clientId+'|'+components+'|'+locale;
 if(window.__rdPayPalSdkKey===key&&window.paypal)return window.paypal;
 const src='https://www.paypal.com/sdk/js?client-id='+encodeURIComponent(clientId)+'&components='+components+'&currency=EUR&locale='+locale+extra;
 await new Promise((resolve,reject)=>{
  const old=document.querySelector('script[data-review-defense-paypal]');
  if(old)old.remove();
  const el=document.createElement('script');el.src=src;el.async=true;el.dataset.reviewDefensePaypal='1';
  el.onload=resolve;el.onerror=()=>reject(new Error(locale==='en_GB'?'Unable to load PayPal.':'Impossible de charger PayPal.'));
  document.head.appendChild(el);
 });
 if(!window.paypal)throw new Error(locale==='en_GB'?'PayPal is unavailable.':'PayPal est indisponible.');
 window.__rdPayPalSdkKey=key;
 return window.paypal;
}

async function loadBillingCatalog(){return api('/v1/billing/catalog')}

async function renderHostedButton(buttonId,en){
 const hostId='paypal-hosted-'+String(buttonId).replace(/[^a-zA-Z0-9_-]/g,'');
 const box=document.getElementById('paypal-button-container');
 if(!box)throw new Error(en?'PayPal checkout container is missing.':'Conteneur de paiement PayPal introuvable.');
 box.innerHTML='<div id="'+hostId+'"></div>';
 const pp=await loadPayPalSdk(PAYPAL_HOSTED_CLIENT_ID,'hosted-buttons',en?'en_GB':'fr_FR');
 if(!pp.HostedButtons)throw new Error(en?'Hosted PayPal buttons are unavailable.':'Les boutons PayPal hébergés sont indisponibles.');
 pp.HostedButtons({hostedButtonId:buttonId}).render('#'+hostId);
}

async function renderSubscriptionButton(offerId,en){
 const cfg=await api('/v1/paypal/subscription/config?offer_id='+encodeURIComponent(offerId));
 const pp=await loadPayPalSdk(PAYPAL_SUBSCRIPTION_CLIENT_ID,'buttons',en?'en_GB':'fr_FR','&vault=true&intent=subscription');
 pp.Buttons({
  style:{layout:'vertical',label:'subscribe'},
  createSubscription:(data,actions)=>actions.subscription.create({plan_id:cfg.plan_id}),
  onApprove:async data=>{
   await api('/v1/paypal/subscription/confirm',{method:'POST',body:JSON.stringify({offer_id:offerId,subscription_id:data.subscriptionID})});
   toast(en?'Subscription confirmed':'Abonnement confirmé','success');
   closeModal();await window.reviewDefenseRender();
  },
  onCancel:()=>toast(en?'Payment cancelled':'Paiement annulé','error'),
  onError:e=>toast(e?.message||(en?'PayPal payment error':'Erreur de paiement PayPal'),'error')
 }).render('#paypal-button-container');
}

async function showBillingPayment(){
 const selected=selectedBillingOffer();
 const offerId=selected?.offer_id||'monitoring_professional';
 const en=window.ReviewDefenseI18n?.getLanguage?.()==='en';
 let catalog;
 try{catalog=await loadBillingCatalog()}catch(e){toast(e.message||'Catalogue indisponible','error');return}
 const offer=(catalog.items||[]).find(x=>x.offer_id===offerId);
 if(!offer){toast(en?'This offer is unavailable.':'Cette offre est indisponible.','error');return}
 const subscription=offer.kind==='subscription';
 const configured=subscription?Boolean(offer.paypal_plan_id):Boolean(offer.paypal_hosted_button_id);
 if(!configured){toast(en?'This payment is not configured yet.':'Ce paiement n’est pas encore configuré.','error');return}
 const title=en?'PayPal payment':'Paiement PayPal';
 const label=en?(offer.name_en||offer.offer_id):(offer.name_fr||offer.offer_id);
 const price=offer.amount===null?(en?'Custom quote':'Sur devis'):(offer.amount+' €'+(subscription?' / month':''));
 modal(title,'<div class="stack"><div class="billing-checkout-summary"><strong>'+esc(label)+'</strong><span>'+esc(price)+'</span></div><p>'+esc(en?'Secure checkout powered directly by PayPal.':'Paiement sécurisé directement via PayPal.')+'</p><div id="paypal-button-container"></div><p class="human-note">'+esc(en?'Payment does not trigger external Google action.':'Le paiement ne déclenche aucune action externe Google.')+'</p></div>');
 try{
  if(subscription)await renderSubscriptionButton(offerId,en);
  else await renderHostedButton(offer.paypal_hosted_button_id,en);
 }catch(e){
  const msg=e?.message||'PayPal error';
  toast(msg,'error');
  const box=document.getElementById('paypal-button-container');
  if(box)box.insertAdjacentHTML('beforeend','<div class="error-state" style="margin-top:12px">'+esc(msg)+'</div>');
 }
}

async function openBillingPlanSelector(){
 const en=window.ReviewDefenseI18n?.getLanguage?.()==='en';
 try{
  const catalog=await loadBillingCatalog();
  const items=(catalog.items||[]).filter(x=>x.kind==='subscription');
  const html='<div class="billing-selector">'+items.map(x=>'<article class="billing-option"><div><strong>'+esc(en?x.name_en:x.name_fr)+'</strong><span>'+esc(x.offer_id)+'</span></div><div><b>'+esc(x.amount||'—')+' €</b></div><button class="primary billing-offer-btn" data-billing-offer="subscription" data-billing-name="'+esc(en?x.name_en:x.name_fr)+'" data-billing-price="'+esc(x.amount||'')+'" data-billing-id="'+esc(x.offer_id)+'">'+(en?'Choose':'Choisir')+'</button></article>').join('')+'</div>';
  modal(en?'Choose a plan':'Choisir une formule',html)
 }catch(e){toast(e.message||'Catalogue indisponible','error')}
}