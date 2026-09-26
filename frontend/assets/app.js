function modal(title,body){const old=document.getElementById('modal');if(old)old.remove();document.body.insertAdjacentHTML('beforeend',`<div id="modal" class="modal-backdrop"><div class="modal"><button class="modal-close" onclick="closeModal()">×</button><h2>${esc(title)}</h2>${body}</div></div>`)}function closeModal(){document.getElementById('modal')?.remove()}
};
window.render=render;