// Console routing and interaction delegation.
function closeMobileNav(){document.querySelector('.sidebar')?.classList.remove('mobile-open');document.querySelector('.mobile-nav-toggle')?.setAttribute('aria-expanded','false')}
function toggleMobileNav(){const side=document.querySelector('.sidebar');if(!side)return;const open=side.classList.toggle('mobile-open');document.querySelector('.mobile-nav-toggle')?.setAttribute('aria-expanded',String(open))}
function navigateTo(id){state.view=id;closeMobileNav();window.reviewDefenseRender()}
document.addEventListener('click',e=>{const side=document.querySelector('.sidebar');const toggle=document.querySelector('.mobile-nav-toggle');if(window.innerWidth<=760&&side?.classList.contains('mobile-open')&&side.contains(e.target)&&e.target.closest('#nav button'))closeMobileNav();if(window.innerWidth<=760&&side?.classList.contains('mobile-open')&&!side.contains(e.target)&&toggle&&!toggle.contains(e.target))closeMobileNav()});
window.addEventListener('resize',()=>{if(window.innerWidth>760)closeMobileNav()});


document.addEventListener('click',event=>{
 const nav=event.target.closest('[data-nav]');
 if(nav){event.preventDefault();navigateTo(nav.dataset.nav);return;}
 const action=event.target.closest('[data-action]')?.dataset.action;
 if(action==='command-palette'){event.preventDefault();openCommandPalette();}
 if(action==='mobile-nav'){event.preventDefault();toggleMobileNav();}
});
