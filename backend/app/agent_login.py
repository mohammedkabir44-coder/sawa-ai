
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/agent-login")
def agent_login_page():
    html = r'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agent Login</title>
<style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;box-sizing:border-box}
.box{background:#1E293B;padding:30px;border-radius:16px;width:100%;max-width:400px;border:1px solid #334155}
h2{color:#10B981;margin-top:0;text-align:center}
label{display:block;margin-top:16px;font-size:14px;color:#94A3B8}
input{width:100%;padding:14px;border-radius:10px;border:1px solid #334155;background:#0F172A;color:#fff;font-size:16px;box-sizing:border-box;margin-top:6px}
.btn{width:100%;padding:16px;margin-top:24px;background:#10B981;color:#052E16;border:none;border-radius:10px;font-weight:800;font-size:16px;cursor:pointer}
.err{color:#EF4444;text-align:center;margin-top:12px;font-size:14px}</style></head>
<body><div class="box"><h2>👤 Agent Portal Login</h2>
<label>Email / Username</label><input id="email" type="text" placeholder="agent@sodangi.com">
<label>Password</label><input id="pass" type="password" placeholder="••••••••">
<button class="btn" onclick="login()">Sign In</button>
<p class="err" id="err"></p>
<p style="text-align:center;margin-top:20px;font-size:13px;color:#64748B">Only Admin can create new profiles.</p>
</div>
<script>
async function login(){
  var e=document.getElementById("email").value;
  var p=document.getElementById("pass").value;
  document.getElementById("err").innerText="Signing in...";
  try{
    var fd=new FormData(); fd.append("username",e); fd.append("password",p);
    var r=await fetch("/api/v1/auth/login",{method:"POST",body:fd});
    var d=await r.json();
    if(d.access_token){
      localStorage.setItem("sodangi_token", d.access_token);
      localStorage.setItem("sodangi_role", d.role||"agent");
      localStorage.setItem("sodangi_name", d.full_name||e);
      location.href="/agent-dashboard";
    } else { document.getElementById("err").innerText="Login failed: "+(d.detail||"Check credentials"); }
  }catch(ex){ document.getElementById("err").innerText="Error: "+ex.message; }
}
</script></body></html>'''
    return HTMLResponse(content=html)
