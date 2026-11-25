from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).parent / "app" / "static"
DOWNLOADS = ROOT / "downloads"
ART = ROOT / "art"

GAMES = {
    "orbital-drift": ("#55d6bd", "\u2726", "Orbital Drift", "Use the arrow keys to steer your craft and collect all eight beacons."),
    "signal-garden": ("#b6a0ff", "\u25c8", "Signal Garden", "Click relay tiles until the center row connects the signal from left to right. Start / reset shuffles the board."),
    "tiny-kingdoms": ("#f0bd6b", "\u2302", "Tiny Kingdoms", "Click two outposts to build a supply road. Link all three towns to complete your map."),
    "pixel-sprint": ("#ff8a80", "\u25b0", "Pixel Sprint", "Move left and right with the arrow keys. Dodge incoming blocks and see how far you can run."),
}

SCRIPTS = {
    "Orbital Drift": """const c=document.querySelector('canvas'),x=c.getContext('2d');let px=320,py=170,stars=[],running=true,score=0;function reset(){px=320;py=170;score=0;stars=Array.from({length:8},()=>[Math.random()*600+20,Math.random()*300+20]);running=true}function draw(){x.fillStyle='#10191c';x.fillRect(0,0,640,340);x.fillStyle='#55d6bd';for(const s of stars){x.beginPath();x.arc(s[0],s[1],5,0,7);x.fill()}x.fillStyle='#e8fff7';x.font='22px system-ui';x.fillText('\u2726',px-11,py+8);x.fillStyle='#a9bbb2';x.font='13px system-ui';x.fillText('Beacons collected: '+score,16,24);if(running)requestAnimationFrame(draw)}document.addEventListener('keydown',e=>{const d=12;if(e.key==='ArrowLeft')px=Math.max(12,px-d);if(e.key==='ArrowRight')px=Math.min(628,px+d);if(e.key==='ArrowUp')py=Math.max(25,py-d);if(e.key==='ArrowDown')py=Math.min(330,py+d);for(let i=stars.length-1;i>=0;i--)if(Math.hypot(px-stars[i][0],py-stars[i][1])<17){stars.splice(i,1);score++;if(!stars.length)running=false}});document.querySelector('#start').onclick=reset;reset();draw();""",
    "Signal Garden": """const c=document.querySelector('canvas'),x=c.getContext('2d');let r=Array.from({length:5},()=>Array.from({length:5},()=>Math.floor(Math.random()*4))),won=false;function draw(){x.fillStyle='#10191c';x.fillRect(0,0,640,340);for(let j=0;j<5;j++)for(let i=0;i<5;i++){let cx=140+i*90,cy=85+j*52;x.fillStyle=j===2&&r[j][i]%2===0?'#263b49':'#182126';x.fillRect(cx-24,cy-18,48,36);x.strokeStyle='#b6a0ff';x.lineWidth=4;x.beginPath();if(r[j][i]%2===0){x.moveTo(cx-16,cy);x.lineTo(cx+16,cy)}else{x.moveTo(cx,cy-12);x.lineTo(cx,cy+12)}x.stroke()}x.fillStyle='#d0c5f6';x.font='14px system-ui';x.fillText(won?'Signal connected!':'Rotate the relays to connect the center row.',125,315)}c.onclick=e=>{let b=c.getBoundingClientRect(),i=Math.floor((e.clientX-b.left)*640/b.width/90),j=Math.floor(((e.clientY-b.top)*340/b.height-59)/52);if(i>=0&&i<5&&j>=0&&j<5)r[j][i]=(r[j][i]+1)%4;won=r[2].every(v=>v%2===0);draw()};document.querySelector('#start').onclick=()=>{r=Array.from({length:5},()=>Array.from({length:5},()=>Math.floor(Math.random()*4)));won=false;draw()};draw();""",
    "Tiny Kingdoms": """const c=document.querySelector('canvas'),x=c.getContext('2d');let selected=null,links=[];const towns=[[145,105],[495,105],[320,265]];function draw(){x.fillStyle='#10191c';x.fillRect(0,0,640,340);x.strokeStyle='#f0bd6b';x.lineWidth=3;for(const [a,b] of links){x.beginPath();x.moveTo(...towns[a]);x.lineTo(...towns[b]);x.stroke()}towns.forEach((p,i)=>{x.fillStyle=selected===i?'#fff1c9':'#f0bd6b';x.beginPath();x.arc(p[0],p[1],19,0,7);x.fill();x.fillStyle='#2a2416';x.font='12px system-ui';x.fillText(''+(i+1),p[0]-4,p[1]+4)});x.fillStyle='#c6b58d';x.font='13px system-ui';x.fillText(links.length>=2?'All outposts linked!':'Select two outposts to build a supply road.',150,320)}c.onclick=e=>{let b=c.getBoundingClientRect(),mx=(e.clientX-b.left)*640/b.width,my=(e.clientY-b.top)*340/b.height,n=towns.findIndex(p=>Math.hypot(mx-p[0],my-p[1])<25);if(n<0)return;if(selected===null)selected=n;else if(selected!==n){if(!links.some(l=>l.includes(selected)&&l.includes(n)))links.push([selected,n]);selected=null}draw()};document.querySelector('#start').onclick=()=>{selected=null;links=[];draw()};draw();""",
    "Pixel Sprint": """const c=document.querySelector('canvas'),x=c.getContext('2d');let px=320,blocks=[],score=0,alive=true,last=0;function reset(){px=320;blocks=[];score=0;alive=true;last=0;requestAnimationFrame(tick)}function tick(t){if(!alive)return;if(t-last>650){blocks.push([Math.random()*600+20,-12]);last=t}x.fillStyle='#10191c';x.fillRect(0,0,640,340);x.fillStyle='#ff8a80';for(const b of blocks){b[1]+=3;x.fillRect(b[0]-8,b[1]-8,16,16)}blocks=blocks.filter(b=>b[1]<355);x.fillStyle='#f5e4df';x.fillRect(px-11,300,22,22);score++;x.fillStyle='#f3c1ba';x.font='13px system-ui';x.fillText('Distance: '+Math.floor(score/10),16,24);if(blocks.some(b=>Math.abs(b[0]-px)<20&&Math.abs(b[1]-310)<20)){alive=false;x.fillText('Run ended — press Start / reset',220,170)}if(alive)requestAnimationFrame(tick)}document.addEventListener('keydown',e=>{if(e.key==='ArrowLeft')px=Math.max(15,px-26);if(e.key==='ArrowRight')px=Math.min(625,px+26)});document.querySelector('#start').onclick=reset;reset();""",
}


def create_game_html(title, color, symbol, instructions):
    script = SCRIPTS[title]
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} — Pixel Vault Demo</title><style>body{{margin:0;background:#0b1014;color:#e8efed;font:16px system-ui;display:grid;min-height:100vh;place-items:center}}main{{width:min(700px,90vw);text-align:center}}h1{{color:{color};font-size:clamp(34px,8vw,70px);margin:10px}}p{{color:#9baaa3;line-height:1.6}}canvas{{width:100%;max-width:640px;background:#111a1d;border:1px solid #31413f;border-radius:12px;cursor:pointer}}button{{margin:12px;padding:10px 16px;background:{color};border:0;border-radius:6px;cursor:pointer}}small{{color:#65736d}}</style><main><small>ORIGINAL OFFLINE DEMO · PIXEL VAULT</small><h1>{symbol} {title}</h1><p>{instructions}</p><canvas id="game" width="640" height="340" aria-label="{title} game"></canvas><p><button id="start">Start / reset</button></p></main><script>{script}</script></html>'''


def main():
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    for slug, (color, symbol, title, instructions) in GAMES.items():
        html = create_game_html(title, color, symbol, instructions)
        with ZipFile(DOWNLOADS / f"{slug}.zip", "w", ZIP_DEFLATED) as archive:
            archive.writestr(f"{slug}/index.html", html)
            archive.writestr(f"{slug}/README.txt", f"{title} is an original, offline educational sample.\nUnpack this ZIP and open index.html in a modern browser.\n")
        art = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 420"><defs><radialGradient id="g"><stop stop-color="{color}" stop-opacity=".55"/><stop offset="1" stop-color="#10171a" stop-opacity="0"/></radialGradient><pattern id="p" width="38" height="38" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#e9fff8" opacity=".36"/></pattern></defs><rect width="800" height="420" fill="#11191c"/><rect width="800" height="420" fill="url(#g)"/><rect width="800" height="420" fill="url(#p)"/><circle cx="400" cy="214" r="105" fill="none" stroke="{color}" stroke-opacity=".25"/><circle cx="400" cy="214" r="66" fill="{color}" fill-opacity=".09" stroke="{color}" stroke-opacity=".52"/><text x="400" y="245" text-anchor="middle" font-size="94" fill="{color}" font-family="sans-serif">{symbol}</text><path d="M0 350 Q190 300 400 350 T800 340" fill="none" stroke="{color}" stroke-opacity=".2"/></svg>'''
        (ART / f"{slug}.svg").write_text(art, encoding="utf-8")
    print(f"Built {len(GAMES)} original offline game packages and matching artwork.")


if __name__ == "__main__":
    main()
