import os
import sqlite3
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()
PASSWORD = "NEST2026"

def db():
    return sqlite3.connect("chat.db")

c = db()
c.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, text TEXT)")
c.commit()
c.close()

HTML = """<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nest</title>
<style>
body{background:#0a0a0a;color:#eee;font-family:monospace;padding:10px;margin:0}
#login{display:flex;flex-direction:column;justify-content:center;height:80vh;text-align:center}
#chat{display:none;height:90vh;flex-direction:column}
#msgs{flex:1;overflow-y:auto;border:1px solid #222;padding:10px;margin-bottom:10px;background:#111}
.msg{margin:6px 0;word-wrap:break-word}
.u{color:#0ff}
input,button{padding:12px;font-size:16px;background:#1a1a1a;color:#eee;border:1px solid #333;margin:2px 0;width:100%;box-sizing:border-box}
button{background:#0ff;color:#000;font-weight:bold}
</style></head><body>
<div id="login">
<h3>🥶 Вход в Nest</h3>
<input id="pass" type="password" placeholder="Пароль">
<button onclick="check()">Войти</button>
</div>
<div id="chat">
<div id="msgs"></div>
<div style="display:flex;gap:5px">
<input id="nick" placeholder="Ник" value="anon" style="width:30%">
<input id="txt" placeholder="Сообщение..." autocomplete="off" style="width:70%">
</div>
<button onclick="s()">Отправить</button>
</div>
<script>
let ws;
function check(){
 const p=document.getElementById("pass").value;
 if(p==="NEST2026"){
  document.getElementById("login").style.display="none";
  document.getElementById("chat").style.display="flex";
  connect();
 } else { alert("Неверный пароль"); }
}
function connect(){
 ws=new WebSocket((location.protocol==="https:"?"wss://":"ws://")+location.host+"/ws");
 const m=document.getElementById("msgs");
 ws.onmessage=e=>{const d=JSON.parse(e.data);const div=document.createElement("div");div.className="msg";div.innerHTML='<span class="u">'+d.user+'</span>: '+d.text;m.appendChild(div);m.scrollTop=m.scrollHeight};
 ws.onclose=()=>{alert("Соединение потеряно. Обнови страницу.");};
}
function s(){const t=document.getElementById("txt").value;const n=document.getElementById("nick").value||"anon";if(!t||!ws)return;ws.send(JSON.stringify({user:n,text:t}));document.getElementById("txt").value=""}
document.getElementById("txt").addEventListener("keydown",e=>{if(e.key==="Enter")s()});
</script></body></html>"""

@app.get("/")
async def root():
    return HTMLResponse(HTML)

clients = set()

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        c = db()
        for r in reversed(c.execute("SELECT user,text FROM messages ORDER BY id DESC LIMIT 100").fetchall()):
            await ws.send_json({"user": r[0], "text": r[1]})
        c.close()
        while True:
            data = await ws.receive_json()
            user = (data.get("user") or "anon")[:30]
            text = (data.get("text") or "")[:500]
            if not text:
                continue
            c = db()
            c.execute("INSERT INTO messages(user,text) VALUES(?,?)", (user, text))
            c.commit()
            c.close()
            for client in list(clients):
                try:
                    await client.send_json({"user": user, "text": text})
                except:
                    clients.discard(client)
    except WebSocketDisconnect:
        clients.discard(ws)
    except Exception as e:
        print(f"ws err:{e}")
        clients.discard(ws)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Messenger on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
