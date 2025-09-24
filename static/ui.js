export const msg = document.getElementById('msg');
export function show(type, text){
  msg.className = 'banner ' + (type || 'error');
  msg.textContent = text;
}
export function $(id){ return document.getElementById(id); }
