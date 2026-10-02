(()=>{const root=document.querySelector('.rd-home');if(!root)return;const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const reveal=()=>{const els=root.querySelectorAll('[data-reveal]');if(reduce){els.forEach(e=>e.classList.add('is-visible'));return}const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('is-visible');io.unobserve(e.target)}}),{threshold:.12});els.forEach(e=>io.observe(e));};reveal();
const menu=root.querySelector('.menu-toggle'),mobile=root.querySelector('.mobile-menu');if(menu){menu.addEventListener('click',()=>{const open=mobile.classList.toggle('open');menu.setAttribute('aria-expanded',String(open))});mobile.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{mobile.classList.remove('open');menu.setAttribute('aria-expanded','false')}))}
if(!reduce){const hero=root.querySelector('.hero');hero.addEventListener('pointermove',e=>{const r=hero.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;root.style.setProperty('--mx',(x*16)+'px');root.style.setProperty('--my',(y*10)+'px')});hero.addEventListener('pointerleave',()=>{root.style.setProperty('--mx','0px');root.style.setProperty('--my','0px')})}
const form=root.querySelector('.contact-form');if(form)form.addEventListener('submit',e=>{e.preventDefault();const data=new FormData(form);const subject=encodeURIComponent('Demande Review Defense — '+String(data.get('company')||'Contact'));const body=encodeURIComponent('Nom : '+String(data.get('name')||'')+'\nE-mail : '+String(data.get('email')||'')+'\nEntreprise : '+String(data.get('company')||'')+'\n\nMessage :\n'+String(data.get('message')||''));window.location.href='mailto:contact@review-defense.com?subject='+subject+'&body='+body;});const newsletter=root.querySelector('.newsletter');if(newsletter){const input=newsletter.querySelector('input[type=email]'),btn=newsletter.querySelector('button');if(btn&&input)btn.addEventListener('click',()=>{if(!input.checkValidity()){input.reportValidity();return}window.location.href='mailto:contact@review-defense.com?subject='+encodeURIComponent('Inscription aux ressources Review Defense')+'&body='+encodeURIComponent('Je souhaite recevoir les ressources à cette adresse : '+input.value);});}
root.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',e=>{const t=root.querySelector(a.getAttribute('href'));if(t){e.preventDefault();t.scrollIntoView({behavior:reduce?'auto':'smooth'})}}));
})();

/* V6.40 Premium landing micro-interactions */
(()=>{const root=document.querySelector('.rd-home');if(!root)return;
root.querySelectorAll('.hero-actions a,.public-actions a,.how-cta a').forEach(a=>{
 a.addEventListener('pointerdown',()=>a.classList.add('is-pressed'));
 ['pointerup','pointerleave'].forEach(ev=>a.addEventListener(ev,()=>a.classList.remove('is-pressed')));
});
})();
