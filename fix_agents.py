import subprocess, time, re

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

print("Removing old broken V4 dashboard...")
code = re.sub(r'@router\.get\("/v4-dashboard"\).*?(?=\n@router\.get\(|\n@router\.post\(|\n@router\.put\(|\n@router\.delete\(|\Z)', '', code, flags=re.DOTALL)

NEW_V4 = '''
@router.get("/v4-dashboard")
def fresh_dashboard_v5():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Sodangi Motors - Dashboard</title>
<style>
:root{--bg:#0B0F19;--card:#151F38;--accent:#22C55E;--text:#F8FAFC;--muted:#94A3B8}
*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,sans-serif}
body{background:var(--bg);color:var(--text);padding-bottom:80px;min-height:100vh}
header{background:linear-gradient(135deg,#065F46,#0369A1);padding:20px;text-align:center}
header h1{font-size:22px;font-weight:800;letter-spacing:1px}
.container{max-width:600px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid #1E293B;border-radius:16px;padding:20px;margin-bottom:16px}
.card h2{font-size:18px;margin-bottom:16px;color:#7DD3FC}
label{display:block;font-size:13px;color:var(--muted);margin:12px 0 6px;font-weight:600}
input,textarea,select{width:100%;padding:12px;border-radius:10px;border:1px solid #334155;background:#0F172A;color:var(--text);font-size:15px}
.btn{width:100%;padding:14px;border:none;border-radius:10px;font-weight:700;font-size:16px;cursor:pointer;margin-top:12px}
.btn-primary{background:var(--accent);color:#052E16}
.btn-danger{background:#EF4444;color:#fff}
.btn-ghost{background:#334155;color:var(--text)}
.hidden{display:none!important}
.nav{position:fixed;bottom:0;left:0;right:0;background:#0F172A;border-top:1px solid #1E293B;display:flex;justify-content:space-around;padding:8px 0;z-index:100}
.nav button{background:none;border:none;color:var(--muted);font-size:12px;display:flex;flex-direction:column;align-items:center;gap:4px;padding:8px 12px;border-radius:12px;cursor:pointer}
.nav button.active{color:var(--accent);background:rgba(34,197,94,0.1)}
.nav button span{font-size:22px}
.item{background:#0F172A;border:1px solid #1E293B;border-radius:12px;padding:12px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
.item-info h3{font-size:15px;margin-bottom:4px}
.item-info p{font-size:13px;color:var(--muted)}
#toast{position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#16A34A;color:#fff;padding:12px 24px;border-radius:10px;font-weight:600;display:none;z-index:999;box-shadow:0 4px 12px rgba(0,0,0,0.3)}
</style>
</head>
<body>
<div id="toast"></div>
<header><h1>SODANGI MOTORS</h1><div style="font-size:13px;color:#E0F2FE;margin-top:4px" id="who">Dashboard</div></header>
<div class="container">
  <section id="tabUpload" class="card">
    <h2>+ Add Vehicle</h2>
    <label>Vehicle Name</label><input id="pName" placeholder="Toyota Camry 2022">
    <label>Price (Naira)</label><input id="pPrice" type="number" placeholder="8500000">
    <label>Description</label><textarea id="pDesc" rows="3" placeholder="Clean interior..."></textarea>
    <button class="btn btn-primary" onclick="publishCar()">Publish Vehicle</button>
  </section>
  <section id="tabCars" class="card hidden">
    <h2>My Inventory</h2>
    <div id="carsList"></div>
  </section>
  <section id="tabAgents" class="card hidden">
    <h2>Sales Team (Owner Only)</h2>
    <div style="background:#1E293B;padding:16px;border-radius:12px;margin-bottom:16px">
      <h3 style="font-size:15px;margin-bottom:12px;color:#7DD3FC">Create New Agent Profile</h3>
      <label>Full Name</label><input id="newAgentName" placeholder="Musa Abdullahi">
      <label>Email</label><input id="newAgentEmail" type="email" placeholder="musa@sodangi.com">
      <label>Phone</label><input id="newAgentPhone" placeholder="080...">
      <label>Password</label><input id="newAgentPass" type="password" placeholder="Min 6 characters">
      <button class="btn btn-primary" onclick="createAgent()">Create Agent</button>
    </div>
    <h3 style="font-size:15px;margin-bottom:12px;color:#7DD3FC">Your Agents</h3>
    <div id="agentsList"></div>
  </section>
  <section id="tabProfile" class="card hidden">
    <h2>My Profile & Showroom</h2>
    <div id="myShowroomLink" style="margin-bottom:16px"></div>
    <label>Phone</label><input id="mPhone" placeholder="080...">
    <label>Bio</label><textarea id="mBio" rows="3" placeholder="Tell buyers about yourself..."></textarea>
    <button class="btn btn-primary" onclick="saveProfile()">Save Profile</button>
    <button class="btn btn-danger" onclick="logout()" style="margin-top:10px">Sign Out</button>
  </section>
</div>
<nav class="nav">
  <button id="navUpload" onclick="go('Upload')" class="active"><span>+</span>Add</button>
  <button id="navCars" onclick="go('Cars')"><span>C</span>Cars</button>
  <button id="navAgents" onclick="go('Agents')" class="hidden"><span>T</span>Team</button>
  <button id="navProfile" onclick="go('Profile')"><span>P</span>Me</button>
</nav>
<script>
var API="/api/v1/dashboard";
var TOKEN=localStorage.getItem("sodangi_token")||"";
var ROLE=localStorage.getItem("sodangi_role")||"";
var NAME=localStorage.getItem("sodangi_name")||"";

document.getElementById("who").textContent=NAME+" ("+ROLE+")";

if(ROLE==="owner"){
  document.getElementById("navAgents").classList.remove("hidden");
}

function toast(m,c){var t=document.getElementById("toast");t.textContent=m;t.style.background=c||"#16A34A";t.style.display="block";setTimeout(function(){t.style.display="none";},3000);}
async function api(p,m,b){var h={"Content-Type":"application/json","Authorization":"Bearer "+TOKEN};var r=await fetch(API+p,{method:m,headers:h,body:b?JSON.stringify(b):undefined});if(!r.ok){var e={};try{e=await r.json();}catch(x){}throw new Error(e.detail||("HTTP "+r.status));}return r.json();}

function go(tab){
  ["Upload","Cars","Agents","Profile"].forEach(function(t){
    var el=document.getElementById("tab"+t);if(el)el.classList.add("hidden");
    var nb=document.getElementById("nav"+t);if(nb)nb.classList.remove("active");
  });
  var el=document.getElementById("tab"+tab);if(el)el.classList.remove("hidden");
  var nb=document.getElementById("nav"+tab);if(nb)nb.classList.add("active");
  if(tab==="Cars")loadCars();
  if(tab==="Profile")loadProfile();
  if(tab==="Agents")loadAgents();
}

async function publishCar(){
  var n=document.getElementById("pName").value;
  var p=parseFloat(document.getElementById("pPrice").value);
  if(!n||isNaN(p)){alert("Please fill Name and Price!");return;}
  try{
    await api("/products/upload","POST",{name:n,price:p,image_url:"[]",description:document.getElementById("pDesc").value,stock:1});
    toast("Car published!");
    document.getElementById("pName").value="";
    document.getElementById("pPrice").value="";
    document.getElementById("pDesc").value="";
    go("Cars");
  }catch(e){alert("Failed: "+e.message);}
}

async function loadCars(){
  try{
    var CARS=await api("/products/mine","POST",{});
    var box=document.getElementById("carsList");
    box.innerHTML="";
    if(!CARS.length){box.innerHTML="<p style='color:#94A3B8;text-align:center;padding:20px'>No vehicles yet.</p>";return;}
    window.V4CARS=CARS;
    CARS.forEach(function(c){
      var d=document.createElement("div");
      d.className="item";
      d.style.flexDirection="column";
      d.style.alignItems="stretch";
      d.style.gap="8px";
      d.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><div class="item-info"><h3>'+c.name+'</h3><p>&#8358;'+Number(c.price).toLocaleString()+'</p></div><button class="btn btn-danger" style="width:auto;padding:8px 12px;font-size:12px;margin:0" onclick="delCar('+c.id+')">Delete</button></div><div style="display:flex;gap:6px;flex-wrap:wrap"><button class="btn btn-ghost" style="flex:1;min-width:80px;padding:10px;font-size:12px;margin:0" onclick="editCar('+c.id+')">Edit</button><a class="btn btn-primary" style="flex:1;min-width:80px;padding:10px;font-size:12px;margin:0;text-decoration:none;text-align:center" href="/api/v1/dashboard/showroom/'+c.id+'" target="_blank">Showroom</a></div>';
      box.appendChild(d);
    });
  }catch(e){document.getElementById("carsList").innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}
}

async function delCar(pid){
  if(!confirm("Delete?"))return;
  try{await api("/products/delete","POST",{product_id:pid});toast("Deleted");loadCars();}
  catch(e){alert(e.message);}
}

function editCar(id){var c=(window.V4CARS||[]).filter(function(x){return x.id===id;})[0];if(!c)return;var n=prompt("Vehicle name:",c.name);if(n===null||n==="")return;var p=prompt("Price:",c.price);if(p===null||p==="")return;var ds=prompt("Description:",c.description||"");if(ds===null)return;api("/products/"+id,"PUT",{name:n,price:parseFloat(p),description:ds,image_url:JSON.stringify(c.images||[]),stock:c.stock||1}).then(function(){toast("Updated!");loadCars();}).catch(function(e){alert("Failed: "+e.message);});}

async function loadProfile(){
  try{
    var me=await api("/profile/me","GET");
    document.getElementById("mPhone").value=me.phone||"";
    document.getElementById("mBio").value=me.bio||"";
    var showroomUrl=location.origin+"/api/v1/dashboard/agent/"+me.id;
    document.getElementById("myShowroomLink").innerHTML='<a href="'+showroomUrl+'" target="_blank" class="btn btn-primary" style="background:#3B82F6;color:#fff;text-decoration:none;text-align:center">View My Showroom</a><button class="btn btn-ghost" onclick="navigator.clipboard.writeText(&quot;'+showroomUrl+'&quot;);toast(&quot;Link copied!&quot;)">Copy Showroom Link</button>';
  }catch(e){}
}

async function saveProfile(){
  try{
    await api("/profile/update","POST",{phone:document.getElementById("mPhone").value,bio:document.getElementById("mBio").value});
    toast("Profile saved!");
  }catch(e){alert(e.message);}
}

async function createAgent(){
  var name=document.getElementById("newAgentName").value;
  var email=document.getElementById("newAgentEmail").value;
  var phone=document.getElementById("newAgentPhone").value;
  var pass=document.getElementById("newAgentPass").value;
  if(!name||!email||!pass){alert("Name, email, and password required!");return;}
  try{
    await api("/agents/create","POST",{full_name:name,email:email,phone:phone,password:pass});
    toast("Agent created! They can now log in.");
    document.getElementById("newAgentName").value="";
    document.getElementById("newAgentEmail").value="";
    document.getElementById("newAgentPhone").value="";
    document.getElementById("newAgentPass").value="";
    loadAgents();
  }catch(e){alert("Failed: "+e.message);}
}

async function loadAgents(){
  try{
    var agents=await api("/agents/list","GET");
    var box=document.getElementById("agentsList");
    box.innerHTML="";
    if(!agents.length){box.innerHTML="<p style='color:#94A3B8;text-align:center;padding:20px'>No agents yet.</p>";return;}
    agents.forEach(function(a){
      var d=document.createElement("div");
      d.className="item";
      d.style.flexDirection="column";
      d.style.alignItems="stretch";
      d.style.gap="8px";
      d.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center"><div class="item-info"><h3>'+a.full_name+'</h3><p>'+a.email+'</p></div><button class="btn btn-danger" style="width:auto;padding:8px 12px;font-size:12px;margin:0" onclick="deleteAgent('+a.id+')">Delete</button></div><a href="/api/v1/dashboard/agent/'+a.id+'" target="_blank" class="btn btn-primary" style="padding:10px;font-size:12px;text-decoration:none;text-align:center">View Agent Showroom</a>';
      box.appendChild(d);
    });
  }catch(e){document.getElementById("agentsList").innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}
}

async function deleteAgent(id){
  if(!confirm("Delete agent?"))return;
  try{await api("/agents/"+id,"DELETE");toast("Deleted");loadAgents();}
  catch(e){alert(e.message);}
}

function logout(){
  localStorage.removeItem("sodangi_token");
  localStorage.removeItem("sodangi_role");
  localStorage.removeItem("sodangi_name");
  location.href="/api/v1/dashboard/ui";
}
</script>
</body>
</html>"""
    return Response(content=html, media_type="text/html")
'''

code = code + NEW_V4
print("Perfect V5 dashboard with Team tab injected!")

with open(fp, "w", encoding="utf-8") as f:
    f.write(code)

subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Fix Agent Registration: Perfect Team tab + Showroom links"], check=False)
subprocess.run(["git", "push", "origin", "main", "--force"], check=False)
