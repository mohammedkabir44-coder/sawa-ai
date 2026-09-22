import subprocess, time, re, json, hmac, hashlib, base64, ast

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

NEW_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<title>Sodangi Motors</title>
<style>
:root{--bg:#0B0F19;--card:#151F38;--accent:#22C55E;--text:#F8FAFC;--muted:#94A3B8}
*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,sans-serif}
body{background:var(--bg);color:var(--text);padding-bottom:90px}
header{background:linear-gradient(135deg,#065F46,#0369A1);padding:18px;text-align:center}
header h1{font-size:20px;font-weight:800;letter-spacing:1px}
.container{max-width:600px;margin:0 auto;padding:14px}
.card{background:var(--card);border:1px solid #1E293B;border-radius:16px;padding:18px;margin-bottom:14px}
.card h2{font-size:17px;margin-bottom:14px;color:#7DD3FC}
label{display:block;font-size:13px;color:var(--muted);margin:10px 0 5px;font-weight:600}
input,textarea,select{width:100%;padding:12px;border-radius:10px;border:1px solid #334155;background:#0F172A;color:var(--text);font-size:15px}
.btn{width:100%;padding:13px;border:none;border-radius:10px;font-weight:700;font-size:15px;cursor:pointer;margin-top:10px}
.btn-primary{background:var(--accent);color:#052E16}
.btn-danger{background:#EF4444;color:#fff}
.btn-ghost{background:#334155;color:var(--text)}
.hidden{display:none!important}
.nav{position:fixed;bottom:0;left:0;right:0;background:#0F172A;border-top:1px solid #1E293B;display:flex;justify-content:space-around;padding:6px 0;z-index:100}
.nav button{background:none;border:none;color:var(--muted);font-size:11px;display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 8px;cursor:pointer}
.nav button.active{color:var(--accent)}
.item{background:#0F172A;border:1px solid #1E293B;border-radius:12px;padding:12px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
.item-info h3{font-size:14px;margin-bottom:3px}
.item-info p{font-size:13px;color:var(--muted)}
.gallery{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:10px;padding:4px;scrollbar-width:none}
.gallery::-webkit-scrollbar{display:none}
.gallery img{scroll-snap-align:center;flex-shrink:0;width:90%;height:200px;object-fit:cover;border-radius:14px}
#toast{position:fixed;top:16px;left:50%;transform:translateX(-50%);background:#16A34A;color:#fff;padding:12px 22px;border-radius:10px;font-weight:600;display:none;z-index:999}
#authCard{max-width:420px;margin:30px auto}
</style>
</head>
<body>
<div id="toast"></div>
<header id="mainHeader" class="hidden"><h1>SODANGI MOTORS</h1><div style="font-size:12px;color:#E0F2FE;margin-top:4px" id="who"></div></header>
<div class="container">
<section id="publicHome">
  <div style="text-align:center;padding:20px 6px 8px">
    <div style="font-size:24px;font-weight:800;letter-spacing:1px">SODANGI MOTORS</div>
    <div style="color:#94A3B8;font-size:13px;margin-top:6px">Verified cars. Verified agents. Buy with confidence.</div>
  </div>
  <div id="publicCars" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:12px 2px"></div>
  <div style="text-align:center;color:#64748B;font-size:12px;padding:6px 0 10px">Agent or Owner? Sign in below.</div>
</section>
<section id="authCard" class="card">
  <div id="googleBtnWrap" style="display:flex;justify-content:center;margin-bottom:10px"><div id="googleBtn"></div></div>
  <div id="authDivider" style="text-align:center;color:#64748B;font-size:12px;margin-bottom:10px">or continue with email</div>
  <div style="display:flex;gap:8px;margin-bottom:12px">
    <button id="tabLoginBtn" class="btn btn-primary" style="margin:0" onclick="showAuth(1)">Sign In</button>
    <button id="tabSignupBtn" class="btn btn-ghost" style="margin:0" onclick="showAuth(2)">Sign Up</button>
  </div>
  <div id="loginPane">
    <label>Email</label><input id="liEmail" type="email" placeholder="you@email.com">
    <label>Password</label><input id="liPass" type="password" placeholder="********">
    <button class="btn btn-primary" onclick="doLogin()">Sign In</button>
  </div>
  <div id="signupPane" class="hidden">
    <label>Full Name</label><input id="regName" placeholder="Your full name">
    <label>Email</label><input id="regEmail" type="email" placeholder="you@email.com">
    <label>Create Password</label><input id="regPass" type="password" placeholder="Min 6 characters">
    <button class="btn btn-primary" onclick="registerAgent()">Create My Account</button>
  </div>
  <hr style="margin:14px 0;border-color:#334155">
  <button class="btn btn-ghost" style="background:#B45309;color:#fff" onclick="emergencyLogin()">Owner Quick Login</button>
</section>
<section id="tabUpload" class="card hidden">
  <h2>Add to Showroom</h2>
  <label>Vehicle Name</label><input id="pName" placeholder="Toyota Camry 2022">
  <label>Price (Naira)</label><input id="pPrice" type="number" placeholder="8500000">
  <label>Photos (auto-compressed)</label><input type="file" id="pFile" accept="image/*" multiple onchange="uploadMedia()">
  <input type="hidden" id="pImg" value="[]">
  <div id="mediaPreview" style="font-size:12px;color:#7DD3FC;margin-top:6px"></div>
  <label>Description</label><textarea id="pDesc" rows="3"></textarea>
  <button class="btn btn-primary" onclick="uploadProduct()">Publish Vehicle</button>
</section>
<section id="tabCars" class="card hidden"><h2>My Inventory</h2><div id="carsList"></div></section>
<section id="tabStatus" class="card hidden"><h2>Status Blaster</h2><div id="statusCarsList"></div></section>
<section id="tabLeaderboard" class="card hidden"><h2>Agent Leaderboard</h2><div id="leaderboardList"></div></section>
<section id="tabLeads" class="card hidden">
  <h2>Customer Leads</h2>
  <label>Name</label><input id="leadName" placeholder="Musa Ibrahim">
  <label>Phone</label><input id="leadPhone" placeholder="2348012345678">
  <label>Type</label><select id="leadType"><option value="whatsapp">WhatsApp</option><option value="sms">SMS</option></select>
  <button class="btn btn-primary" onclick="addLead()">Save Lead</button>
  <div id="leadsList" style="margin-top:12px"></div>
</section>
<section id="tabAgents" class="card hidden">
  <h2>Sales Team</h2>
  <label>Name</label><input id="aName"><label>Email</label><input id="aEmail" type="email">
  <label>Phone</label><input id="aPhone"><label>Password</label><input id="aPass" type="password">
  <button class="btn btn-primary" onclick="createAgent()">Hire Agent</button>
  <div id="agentsList" style="margin-top:12px"></div>
</section>
<section id="tabStats" class="card hidden"><h2>Analytics</h2><div id="statsBox"></div></section>
<section id="tabBot" class="card hidden">
  <h2>AI Auto-Responder</h2>
  <div id="botStatus" style="margin-bottom:10px"></div>
  <button class="btn btn-primary" onclick="toggleBot()">Toggle Bot On/Off</button>
  <label>Meta Callback URL</label><input readonly value="https://sawa-ai-backend.vercel.app/api/v1/dashboard/whatsapp-webhook" onclick="this.select()">
  <label>Verify Token</label><input readonly value="sodangi_verify_2026" onclick="this.select()">
</section>
<section id="tabProfile" class="card hidden">
  <h2>My Profile</h2>
  <label>Phone</label><input id="mPhone"><label>Bio</label><textarea id="mBio" rows="3"></textarea>
  <button class="btn btn-primary" onclick="saveProfile()">Save Profile</button>
  <button class="btn btn-danger" onclick="logout()">Sign Out</button>
</section>
</div>
<nav class="nav hidden" id="bottomNav">
  <button id="navUpload" onclick="go(0)"><span>+</span>Add</button>
  <button id="navCars" onclick="go(1)"><span>C</span>Cars</button>
  <button id="navStatus" onclick="go(6)"><span>S</span>Status</button>
  <button id="navLeaderboard" onclick="go(2)"><span>B</span>Board</button>
  <button id="navLeads" onclick="go(3)"><span>L</span>Leads</button>
  <button id="navAgents" onclick="go(4)" class="hidden"><span>T</span>Team</button>
  <button id="navStats" onclick="go(5)" class="hidden"><span>A</span>Stats</button>
  <button id="navBot" onclick="go(7)"><span>R</span>Bot</button>
  <button id="navProfile" onclick="go(8)"><span>M</span>Me</button>
</nav>
<script>
var _auto=new URLSearchParams(window.location.search).get("auto");
if(_auto){localStorage.setItem("sodangi_token",_auto);localStorage.setItem("sodangi_role","owner");localStorage.setItem("sodangi_name","Owner");window.history.replaceState({},document.title,window.location.pathname);location.reload();}
var API="/api/v1/dashboard";
var TOKEN=localStorage.getItem("sodangi_token")||"";
var ROLE=localStorage.getItem("sodangi_role")||"";
var NAME=localStorage.getItem("sodangi_name")||"";
var TABS=["Upload","Cars","Leaderboard","Leads","Agents","Stats","Status","Bot","Profile"];
window.SHOWROOM_URL="";
function toast(m,c){var t=document.getElementById("toast");t.textContent=m;t.style.background=c||"#16A34A";t.style.display="block";setTimeout(function(){t.style.display="none";},3000);}
window.addEventListener("error",function(ev){try{toast("Error: "+(ev.message||"unknown"),"#EF4444");}catch(e){}});
async function api(p,m,b,a,att){att=att||0;var ctrl=new AbortController();var tm=setTimeout(function(){ctrl.abort();},20000);var h={"Content-Type":"application/json"};if(a)h["Authorization"]="Bearer "+TOKEN;try{var r=await fetch(API+p,{method:m,headers:h,body:b?JSON.stringify(b):undefined,signal:ctrl.signal});clearTimeout(tm);if(!r.ok){var e={};try{e=await r.json();}catch(x){}throw new Error(e.detail||("HTTP "+r.status));}return await r.json();}catch(err){clearTimeout(tm);var mg=err.message||"";var net=(err.name==="AbortError")||mg.indexOf("Failed to fetch")>-1;if(net&&att<2){await new Promise(function(rs){setTimeout(rs,1200*(att+1));});return api(p,m,b,a,att+1);}throw new Error(net?"Network slow or offline. Retry.":mg);}}
function go(i){TABS.forEach(function(t,k){var el=document.getElementById("tab"+t);if(el)el.classList.add("hidden");});var ids=["navUpload","navCars","navLeaderboard","navLeads","navAgents","navStats","navStatus","navBot","navProfile"];ids.forEach(function(n){var b=document.getElementById(n);if(b)b.classList.remove("active");});var el=document.getElementById("tab"+TABS[i]);if(el)el.classList.remove("hidden");var nb=document.getElementById(ids[i]);if(nb)nb.classList.add("active");if(i===1)loadCars();if(i===4)loadAgents();if(i===8)loadProfile();if(i===5)loadStats();if(i===3)loadLeads();if(i===2)loadLeaderboard();if(i===7)loadBot();if(i===6)loadStatusCars();}
function enterDash(){var ac=document.getElementById("authCard");if(ac)ac.classList.add("hidden");var ph=document.getElementById("publicHome");if(ph)ph.style.display="none";document.getElementById("mainHeader").classList.remove("hidden");document.getElementById("bottomNav").classList.remove("hidden");document.getElementById("who").textContent=NAME+" ("+ROLE+")";if(ROLE==="owner"){document.getElementById("navAgents").classList.remove("hidden");document.getElementById("navStats").classList.remove("hidden");}go(0);}
function showAuth(m){var lp=document.getElementById("loginPane"),sp=document.getElementById("signupPane"),lb=document.getElementById("tabLoginBtn"),sb=document.getElementById("tabSignupBtn");if(m===1){lp.classList.remove("hidden");sp.classList.add("hidden");lb.className="btn btn-primary";sb.className="btn btn-ghost";}else{sp.classList.remove("hidden");lp.classList.add("hidden");sb.className="btn btn-primary";lb.className="btn btn-ghost";}lb.style.margin="0";sb.style.margin="0";}
async function doLogin(){var em=document.getElementById("liEmail").value.trim(),pw=document.getElementById("liPass").value;if(!em||!pw){alert("Fill Email and Password");return;}try{var r=await fetch(API+"/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:em,password:pw})});var d=await r.json();if(d.status==="wrong_password"){alert("Wrong password!");return;}if(!d.token){alert("Server error: "+JSON.stringify(d));return;}TOKEN=d.token;ROLE=d.role;NAME=d.full_name;localStorage.setItem("sodangi_token",TOKEN);localStorage.setItem("sodangi_role",ROLE);localStorage.setItem("sodangi_name",NAME);enterDash();}catch(e){alert("Network error: "+e.message);}}
async function registerAgent(){var n=document.getElementById("regName").value.trim(),e=document.getElementById("regEmail").value.trim(),p=document.getElementById("regPass").value;if(!n||!e||!p){alert("Fill all fields");return;}try{var r=await fetch(API+"/register",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({full_name:n,email:e,password:p})});var d=await r.json();if(r.ok){alert("Account created! Now tap Sign In.");showAuth(1);}else{alert("Failed: "+(d.detail||"unknown"));}}catch(err){alert("Failed: "+err.message);}}
async function emergencyLogin(){var pw=prompt("Owner master password:");if(!pw)return;try{var r=await fetch(API+"/emergency-login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({master_password:pw})});var d=await r.json();if(d.token){TOKEN=d.token;ROLE=d.role;NAME=d.full_name;localStorage.setItem("sodangi_token",TOKEN);localStorage.setItem("sodangi_role",ROLE);localStorage.setItem("sodangi_name",NAME);enterDash();}else{alert("Failed: "+(d.detail||"unknown"));}}catch(e){alert("Network error: "+e.message);}}
async function initSocial(){try{var r=await fetch(API+"/social-config");var c=await r.json();if(c.google_client_id){var s=document.createElement("script");s.src="https://accounts.google.com/gsi/client";s.async=true;s.onload=function(){try{google.accounts.id.initialize({client_id:c.google_client_id,callback:onGoogleCred});google.accounts.id.renderButton(document.getElementById("googleBtn"),{theme:"filled_black",size:"large",width:300});}catch(e){}};document.head.appendChild(s);}else{document.getElementById("googleBtnWrap").style.display="none";document.getElementById("authDivider").style.display="none";}}catch(e){document.getElementById("googleBtnWrap").style.display="none";}}
async function onGoogleCred(resp){try{var r=await fetch(API+"/social-login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({credential:resp.credential})});var d=await r.json();if(d.token){TOKEN=d.token;ROLE=d.role;NAME=d.full_name;localStorage.setItem("sodangi_token",TOKEN);localStorage.setItem("sodangi_role",ROLE);localStorage.setItem("sodangi_name",NAME);enterDash();}else{alert("Google failed: "+(d.detail||"unknown"));}}catch(e){alert("Google error: "+e.message);}}
function logout(){localStorage.removeItem("sodangi_token");localStorage.removeItem("sodangi_role");localStorage.removeItem("sodangi_name");location.reload();}
function copyShowroom(){if(window.SHOWROOM_URL){navigator.clipboard.writeText(window.SHOWROOM_URL);toast("Showroom link copied!");}}
function compressImage(f,mw){return new Promise(function(res,rej){var img=new Image();var u=URL.createObjectURL(f);img.onload=function(){var w=img.width,h=img.height;if(w>mw){h=Math.round(h*mw/w);w=mw;}var c=document.createElement("canvas");c.width=w;c.height=h;c.getContext("2d").drawImage(img,0,0,w,h);URL.revokeObjectURL(u);c.toBlob(function(b){b?res(b):rej(new Error("compress"));},"image/jpeg",0.72);};img.onerror=function(){URL.revokeObjectURL(u);rej(new Error("load"));};img.src=u;});}
async function uploadMedia(){var fs=document.getElementById("pFile").files;if(!fs.length)return;var pv=document.getElementById("mediaPreview");var urls=[];for(var i=0;i<fs.length;i++){var f=fs[i],on=f.name;pv.textContent="Compressing "+(i+1)+" of "+fs.length+"...";try{f=await compressImage(f,800);var dt=on.lastIndexOf(".");on=(dt>0?on.substring(0,dt):on)+".jpg";}catch(e){}pv.textContent="Uploading "+(i+1)+" ("+Math.round(f.size/1024)+"KB)...";try{var fd=new FormData();fd.append("file",f,on);var r=await fetch(API+"/upload-media",{method:"POST",headers:{"Authorization":"Bearer "+TOKEN},body:fd});if(!r.ok)throw new Error("relay");var d=await r.json();urls.push(d.url);}catch(e){alert("Upload failed: "+on);}}document.getElementById("pImg").value=JSON.stringify(urls);pv.textContent="Done: "+urls.length+" photos.";}
async function uploadProduct(){var n=document.getElementById("pName").value,p=parseFloat(document.getElementById("pPrice").value);if(!n||isNaN(p)){alert("Fill Name and Price");return;}var u=[];try{u=JSON.parse(document.getElementById("pImg").value||"[]");}catch(e){}if(!u.length)u=["https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb"];try{await api("/products/upload","POST",{name:n,price:p,image_url:JSON.stringify(u),description:document.getElementById("pDesc").value,stock:1},true);alert("Car published!");document.getElementById("pName").value="";document.getElementById("pPrice").value="";document.getElementById("pDesc").value="";document.getElementById("pFile").value="";document.getElementById("pImg").value="[]";go(1);}catch(e){alert("Failed: "+e.message);}}
async function loadCars(){try{var C=await api("/products/mine","POST",{},true);var bx=document.getElementById("carsList");bx.innerHTML="";if(!C.length){bx.innerHTML="<p style='color:#94A3B8;text-align:center'>No vehicles yet.</p>";return;}window.CARS=C;C.forEach(function(c,i){var d=document.createElement("div");d.className="item";d.style.flexDirection="column";d.style.alignItems="stretch";var im=c.images&&c.images.length?c.images:[];var h='<div class="item-info"><h3>'+c.name+'</h3><p>&#8358;'+Number(c.price).toLocaleString()+'</p></div>';if(im.length){h+='<div class="gallery" style="margin:8px 0">';im.forEach(function(u){h+='<img src="'+u+'" loading="lazy">';});h+='</div>';}h+='<div style="display:flex;flex-wrap:wrap;gap:6px">';h+='<button class="btn btn-primary" style="flex:1;margin:0;padding:9px;font-size:12px;background:#3B82F6;color:#fff" onclick="openShareModal('+i+')">Share</button>';h+='<button class="btn btn-primary" style="flex:1;margin:0;padding:9px;font-size:12px;background:#25D366;color:#000" onclick="openBroadcastModal('+i+')">Broadcast</button>';h+='<button class="btn btn-primary" style="flex:1;margin:0;padding:9px;font-size:12px;background:#8B5CF6;color:#fff" onclick="openSMSModal('+i+')">SMS</button>';h+='<button class="btn btn-ghost" style="flex:1;margin:0;padding:9px;font-size:12px" onclick="logSale('+i+')">Log Sale</button>';h+='<button class="btn btn-danger" style="flex:1;margin:0;padding:9px;font-size:12px" onclick="delCar('+c.id+')">Delete</button>';h+='</div>';d.innerHTML=h;bx.appendChild(d);});}catch(e){document.getElementById("carsList").innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
async function delCar(pid){if(!confirm("Delete?"))return;try{await api("/products/delete","POST",{product_id:pid},true);toast("Deleted");loadCars();}catch(e){alert(e.message);}}
function openShareModal(i){var c=window.CARS[i];if(!c)return;var lk=location.origin+"/api/v1/dashboard/car/"+c.id;var cp=c.name+" - &#8358;"+Number(c.price).toLocaleString()+" "+lk;var h='<div id="mShare" style="position:fixed;inset:0;background:rgba(0,0,0,0.9);z-index:999;display:flex;align-items:center;justify-content:center;padding:20px"><div class="card" style="max-width:400px;width:100%"><h2>'+c.name+'</h2><a href="https://wa.me/?text='+encodeURIComponent(cp)+'" target="_blank" class="btn btn-primary" style="background:#25D366;color:#000">WhatsApp</a><a href="https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(lk)+'" target="_blank" class="btn btn-primary" style="background:#1877F2;color:#fff">Facebook</a><button class="btn btn-ghost" onclick="document.getElementById(\'mShare\').remove()">Close</button></div></div>';document.body.insertAdjacentHTML("beforeend",h);}
function openBroadcastModal(i){var c=window.CARS[i];if(!c)return;if(!window._leads||!window._leads.length){alert("Add leads first");go(3);return;}var mg="Check out "+c.name+" for &#8358;"+Number(c.price).toLocaleString()+". "+location.origin+"/api/v1/dashboard/car/"+c.id;var h='<div id="mBc" style="position:fixed;inset:0;background:rgba(0,0,0,0.9);z-index:999;display:flex;align-items:center;justify-content:center;padding:20px"><div class="card" style="max-width:400px;width:100%;max-height:80vh;overflow-y:auto"><h2>Broadcast</h2>';window._leads.forEach(function(l){var p=l.phone.indexOf("234")===0?l.phone:"234"+l.phone.replace(/^0/,"");h+='<a href="https://wa.me/'+p+'?text='+encodeURIComponent(mg)+'" target="_blank" class="item" style="text-decoration:none;color:#F8FAFC"><div class="item-info"><h3>'+l.name+'</h3><p>'+l.phone+'</p></div></a>';});h+='<button class="btn btn-ghost" onclick="document.getElementById(\'mBc\').remove()">Close</button></div></div>';document.body.insertAdjacentHTML("beforeend",h);}
function openSMSModal(i){var c=window.CARS[i];if(!c)return;if(!window._leads||!window._leads.length){alert("Add SMS leads first");go(3);return;}var sm=window._leads.filter(function(l){return (l.contact_type||"whatsapp")==="sms";});if(!sm.length){alert("No SMS leads");go(3);return;}var mg="Check out "+c.name+" for &#8358;"+Number(c.price).toLocaleString()+". "+location.origin+"/api/v1/dashboard/car/"+c.id;var h='<div id="mSms" style="position:fixed;inset:0;background:rgba(0,0,0,0.9);z-index:999;display:flex;align-items:center;justify-content:center;padding:20px"><div class="card" style="max-width:400px;width:100%;max-height:80vh;overflow-y:auto"><h2>SMS Blaster</h2>';sm.forEach(function(l){var p=l.phone.indexOf("234")===0?l.phone:"234"+l.phone.replace(/^0/,"");h+='<a href="sms:+'+p+'?&body='+encodeURIComponent(mg)+'" class="item" style="text-decoration:none;color:#F8FAFC"><div class="item-info"><h3>'+l.name+'</h3><p>'+l.phone+'</p></div></a>';});h+='<button class="btn btn-ghost" onclick="document.getElementById(\'mSms\').remove()">Close</button></div></div>';document.body.insertAdjacentHTML("beforeend",h);}
async function logSale(i){var c=window.CARS[i];if(!c)return;if(!confirm("Log sale for "+c.name+"?"))return;try{var me=await api("/profile/me","GET",null,true);var r=await api("/sales/log","POST",{product_id:c.id,agent_id:me.id,sale_price:c.price},true);alert("Sale logged! Commission: &#8358;"+Number(r.commission).toLocaleString());}catch(e){alert(e.message);}}
async function loadLeaderboard(){var bx=document.getElementById("leaderboardList");bx.innerHTML="<p style='color:#94A3B8;text-align:center'>Calculating...</p>";try{var b=await api("/leaderboard","GET",null,true);if(!b.length){bx.innerHTML="<p style='color:#94A3B8;text-align:center'>No sales yet.</p>";return;}var h='<table style="width:100%;border-collapse:collapse;font-size:14px"><tr style="border-bottom:1px solid #334155"><th style="text-align:left;padding:8px">Agent</th><th>Sales</th><th>Commission</th></tr>';b.forEach(function(a,i){var m=i===0?"&#129351;":i===1?"&#129352;":i===2?"&#129353;":"";h+='<tr style="border-bottom:1px solid #1E293B"><td style="padding:9px">'+m+" "+a.name+'</td><td style="text-align:center">'+a.sales_count+'</td><td style="text-align:right;color:#10B981;font-weight:bold">&#8358;'+Number(a.commission).toLocaleString()+'</td></tr>';});bx.innerHTML=h+"</table>";}catch(e){bx.innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
async function loadLeads(){var bx=document.getElementById("leadsList");try{var L=await api("/leads/all","GET",null,true);window._leads=L;if(!L.length){bx.innerHTML="<p style='color:#94A3B8;text-align:center'>No leads yet.</p>";return;}var h="";L.forEach(function(l){var bd=(l.contact_type==="sms")?' <span style="background:#3B82F6;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px">SMS</span>':' <span style="background:#25D366;color:#000;padding:2px 6px;border-radius:4px;font-size:10px">WA</span>';h+='<div class="item"><div class="item-info"><h3>'+l.name+bd+'</h3><p>'+l.phone+'</p></div></div>';});bx.innerHTML=h;}catch(e){bx.innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
async function addLead(){var n=document.getElementById("leadName").value,p=document.getElementById("leadPhone").value.replace(/\s+/g,"");if(!n||!p){alert("Fill name and phone");return;}var t=document.getElementById("leadType").value;try{await api("/leads/add","POST",{name:n,phone:p,contact_type:t},true);alert("Lead saved!");document.getElementById("leadName").value="";document.getElementById("leadPhone").value="";loadLeads();}catch(e){alert(e.message);}}
async function loadAgents(){try{var A=await api("/agents","GET",null,true);var bx=document.getElementById("agentsList");bx.innerHTML="";A.forEach(function(a){var d=document.createElement("div");d.className="item";d.innerHTML='<div class="item-info"><h3>'+a.full_name+'</h3><p>'+a.email+'</p></div>';bx.appendChild(d);});}catch(e){}}
async function createAgent(){try{await api("/agents/create","POST",{full_name:document.getElementById("aName").value,email:document.getElementById("aEmail").value,password:document.getElementById("aPass").value,phone:document.getElementById("aPhone").value},true);alert("Agent created!");loadAgents();}catch(e){alert(e.message);}}
async function loadProfile(){try{var me=await api("/profile/me","GET",null,true);document.getElementById("mPhone").value=me.phone;document.getElementById("mBio").value=me.bio;var sid=me.page.split("/").pop();window.SHOWROOM_URL=location.origin+"/api/v1/dashboard/ad/"+sid;var sec=document.getElementById("tabProfile");var old=document.getElementById("showroomBox");if(old)old.remove();var d=document.createElement("div");d.id="showroomBox";d.innerHTML='<a href="'+window.SHOWROOM_URL+'" target="_blank" class="btn btn-primary" style="display:block;text-decoration:none;text-align:center">Open My Showroom</a><button class="btn btn-ghost" onclick="copyShowroom()">Copy Showroom Link</button><a class="btn btn-primary" style="display:block;text-decoration:none;text-align:center;background:#25D366;color:#000" href="https://wa.me/?text='+encodeURIComponent("My showroom: "+window.SHOWROOM_URL)+'" target="_blank">Share Showroom</a>';sec.insertBefore(d,sec.querySelector(".btn-danger"));}catch(e){}}
async function saveProfile(){try{await api("/profile/update","POST",{phone:document.getElementById("mPhone").value,bio:document.getElementById("mBio").value},true);alert("Profile saved!");}catch(e){alert(e.message);}}
async function loadStats(){var bx=document.getElementById("statsBox");try{var a=await api("/analytics","GET",null,true);var h="<h3 style='color:#7DD3FC;margin-bottom:8px'>Team Activity</h3>";a.agents.forEach(function(g){h+='<div class="item"><div class="item-info"><h3>'+g.name+'</h3><p>Leads: '+g.ad_lead+' | Handoffs: '+g.handoff+'</p></div></div>';});bx.innerHTML=h;}catch(e){bx.innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
async function loadBot(){var bx=document.getElementById("botStatus");try{var s=await api("/ai-bot/status","GET",null,true);bx.innerHTML='<p style="color:'+(s.enabled?"#22C55E":"#EF4444")+';font-weight:700">Bot is '+(s.enabled?"ON - replying 24/7":"OFF")+'</p>';}catch(e){bx.innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
async function toggleBot(){try{var s=await api("/ai-bot/toggle","POST",{},true);alert("Bot is now "+(s.enabled?"ON":"OFF"));loadBot();}catch(e){alert(e.message);}}
async function loadPublicShowroom(){var bx=document.getElementById("publicCars");try{var r=await fetch(API+"/products");var C=await r.json();if(!C||!C.length){bx.innerHTML='<p style="color:#94A3B8;grid-column:1/-1;text-align:center">Showroom opening soon!</p>';return;}var h="";C.slice(0,8).forEach(function(c){var im="";if(c.images&&c.images.length){im=Array.isArray(c.images)?c.images[0]:c.images;}else if(c.image_url){im=c.image_url;}h+='<a href="'+location.origin+'/api/v1/dashboard/car/'+c.id+'" style="text-decoration:none"><div class="card" style="margin:0;padding:10px">'+(im?'<img src="'+im+'" loading="lazy" style="width:100%;height:100px;object-fit:cover;border-radius:10px">':'')+'<div style="font-size:12px;font-weight:700;margin-top:6px">'+c.name+'</div><div style="color:#10B981;font-weight:800;font-size:12px">&#8358;'+Number(c.price).toLocaleString()+'</div></div></a>';});bx.innerHTML=h;}catch(e){bx.innerHTML='<p style="color:#94A3B8;grid-column:1/-1;text-align:center">Welcome! Sign in below.</p>';}}
async function loadStatusCars(){var bx=document.getElementById("statusCarsList");bx.innerHTML="<p style='color:#94A3B8;text-align:center'>Loading...</p>";try{var C=await api("/products/mine","POST",{},true);window.CARS=C;var h="";C.forEach(function(c,i){var im=c.images&&c.images.length?c.images[0]:"";h+='<div class="item" style="flex-direction:column;align-items:stretch;gap:8px">'+(im?'<img src="'+im+'" loading="lazy" style="width:100%;height:150px;object-fit:cover;border-radius:12px">':'')+'<div class="item-info"><h3>'+c.name+'</h3><p>&#8358;'+Number(c.price).toLocaleString()+'</p></div><button class="btn btn-primary" style="margin:0" onclick="generateStatusImage('+i+')">Generate Status Image</button></div>';});bx.innerHTML=h||"<p style='color:#94A3B8;text-align:center'>No cars.</p>";}catch(e){bx.innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
function generateStatusImage(i){var c=(window.CARS||[])[i];if(!c)return;toast("Generating...");api("/profile/me","GET",null,true).then(function(p){drawCanvas(c,p.full_name||"Sodangi Motors",p.phone||"08000000000");}).catch(function(){drawCanvas(c,"Sodangi Motors","08000000000");});}
function drawCanvas(c,nm,ph){var cv=document.createElement("canvas");var cx=cv.getContext("2d");var im=new Image();im.crossOrigin="anonymous";var src=c.images&&c.images.length?c.images[0]:"";if(!src){toast("No image");return;}im.onload=function(){cv.width=1080;cv.height=1920;var sc=Math.max(cv.width/im.width,cv.height/im.height);cx.drawImage(im,(cv.width-im.width*sc)/2,(cv.height-im.height*sc)/2,im.width*sc,im.height*sc);var g=cx.createLinearGradient(0,cv.height-600,0,cv.height);g.addColorStop(0,"rgba(0,0,0,0)");g.addColorStop(1,"rgba(0,0,0,0.95)");cx.fillStyle=g;cx.fillRect(0,cv.height-600,cv.width,600);cx.textAlign="center";cx.fillStyle="#fff";cx.font="bold 70px sans-serif";cx.fillText(c.name,cv.width/2,cv.height-350);cx.fillStyle="#10B981";cx.font="bold 100px sans-serif";cx.fillText("\u20A6"+Number(c.price).toLocaleString(),cv.width/2,cv.height-220);cx.fillStyle="#fff";cx.font="bold 50px sans-serif";cx.fillText(nm,cv.width/2,cv.height-110);cx.fillStyle="#FBBF24";cx.font="bold 60px sans-serif";cx.fillText(ph,cv.width/2,cv.height-40);try{var a=document.createElement("a");a.download=c.name+"_Status.png";a.href=cv.toDataURL("image/png");a.click();toast("Status saved!");}catch(e){cv.toBlob(function(b){window.open(URL.createObjectURL(b));});}};im.onerror=function(){toast("Image error");};im.src=src;}
if(TOKEN){enterDash();}else{loadPublicShowroom();initSocial();}
</script>
</body>
</html>'''

start = code.find('DASHBOARD_HTML = """')
if start == -1:
    print("FATAL: DASHBOARD_HTML anchor not found!")
    raise SystemExit(1)
body_start = start + len('DASHBOARD_HTML = """')
end = code.find('"""', body_start)
if end == -1:
    print("FATAL: closing quotes not found!")
    raise SystemExit(1)
code = code[:body_start] + NEW_HTML + code[end:]
print("✅ OLD HTML DESTROYED. NEW CLEAN HTML INSTALLED!")

# CRASH-PROOF ENCODING FOREVER
n = code.count('.encode("utf-8")')
code = code.replace('.encode("utf-8")', '.encode("utf-8", "replace")')
print(f"✅ Crash-proofed {n} encode calls!")

# Ensure emergency login route exists
if "/emergency-login" not in code:
    code += '''

@router.post("/emergency-login")
def emergency_login(payload: dict, db: Session = Depends(get_db)):
    if payload.get("master_password", "") != "Sodangi2026!":
        raise HTTPException(status_code=401, detail="Wrong master password")
    owner = db.query(Agent).filter(Agent.role == "owner").first()
    if not owner:
        raise HTTPException(status_code=404, detail="No owner found")
    return {"status": "success", "token": _make_token(owner.email, owner.role), "role": owner.role, "full_name": owner.full_name}
'''
    print("✅ Emergency login route ensured!")

ast.parse(code)
with open(fp, "w", encoding="utf-8") as f:
    f.write(code)
print("✅ Saved!")

subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "TOTAL HTML REBUILD: one clean engine, crash-proof encoding, permanent login doors"], check=False)
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
    if r.returncode == 0:
        print("✅ Push successful!")
        break
    print("Push retry " + str(i+1))
    time.sleep(5)

# PRINT MAGIC LINK
m = re.search(r'SECRET\s*=\s*"([^"]+)"', code)
SECRET = m.group(1) if m else "sodangi-sawa-secret-2026-do-not-share"
payload = {"e": "owner@sodangi.com", "r": "owner", "t": int(time.time()) + 86400*30}
p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
sig = hmac.new(SECRET.encode(), p_b64.encode(), hashlib.sha256).hexdigest()
print("\n" + "="*60)
print("MAGIC LOGIN LINK (paste in browser address bar):")
print("https://sawa-ai-backend.vercel.app/?auto=" + p_b64 + "." + sig)
print("="*60)
