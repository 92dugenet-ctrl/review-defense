const page=document.querySelector(".services-page");
if(page){
  const reduce=window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  page.classList.add("motion-ready");

  const rows=[...document.querySelectorAll(".service-row")];
  if(reduce){
    rows.forEach(row=>row.classList.add("is-visible"));
  }else if("IntersectionObserver" in window){
    const observer=new IntersectionObserver((entries)=>{
      entries.forEach((entry)=>{
        if(entry.isIntersecting){
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },{threshold:.12,rootMargin:"0px 0px -8% 0px"});
    rows.forEach((row)=>observer.observe(row));
  }else{
    rows.forEach((row)=>row.classList.add("is-visible"));
  }

  if(!reduce && window.matchMedia("(pointer:fine)").matches){
    document.querySelectorAll(".service-art").forEach((visual)=>{
      visual.addEventListener("pointermove",(event)=>{
        const rect=visual.getBoundingClientRect();
        const x=(event.clientX-rect.left)/rect.width-.5;
        const y=(event.clientY-rect.top)/rect.height-.5;
        visual.style.transform=`translate3d(0,-5px,0) perspective(900px) rotateX(${-y*1.2}deg) rotateY(${x*1.2}deg)`;
      },{passive:true});
      visual.addEventListener("pointerleave",()=>{visual.style.transform="";});
    });
  }

  if(!reduce){
    document.querySelectorAll('a[href]').forEach((link)=>{
      const href=link.getAttribute("href");
      if(!href || link.target==="_blank" || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:") || href.startsWith("http")) return;
      link.addEventListener("click",(event)=>{
        if(event.metaKey||event.ctrlKey||event.shiftKey||event.altKey) return;
        const url=new URL(href,location.href);
        if(url.origin!==location.origin) return;
        event.preventDefault();
        page.classList.add("is-leaving");
        window.setTimeout(()=>{location.href=url.href;},180);
      });
    });
  }
}
