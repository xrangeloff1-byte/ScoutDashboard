// Scout iPhone Web Push: requires a VAPID public key and server-side sender.
self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
self.addEventListener('push',event=>{
 let message={title:'Scout found a lead',body:'A qualified opportunity is ready to review.',url:'./'};
 try{if(event.data)message={...message,...event.data.json()}}catch{}
 event.waitUntil(self.registration.showNotification(String(message.title).slice(0,100),{
  body:String(message.body).slice(0,220),tag:'scout-qualified-'+String(message.id||'latest').slice(0,50),
  data:{url:message.url||'./'}
 }));
});
self.addEventListener('notificationclick',event=>{
 event.notification.close();
 const url=new URL(event.notification.data?.url||'./',self.registration.scope);
 if(url.origin!==self.location.origin)return;
 event.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(async windows=>{
  for(const win of windows){if(win.url.startsWith(self.registration.scope)){await win.focus();return}}
  await clients.openWindow(url.href);
 }));
});
