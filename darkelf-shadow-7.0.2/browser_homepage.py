

HOMEPAGE = """ <!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Darkelf Browser</title>
<meta name="referrer" content="no-referrer">

<meta http-equiv="Content-Security-Policy"
content="
default-src 'self' data:;
style-src 'unsafe-inline';
script-src 'unsafe-inline';
img-src data:;
base-uri 'none';
object-src 'none';
frame-src 'none';
">

<style>
:root{
  --bg:#0a0b10;

  /* injected by Python */
  --bg1:BG1;
  --bg2:BG2;
  --bg3:BG3;

  --accent:ACCENT_COLOR;

  --text:#eef2f6;
  --muted:#d7dee8;
}

*{ box-sizing:border-box; }

html,body{
  height:100%;
  margin:0;
  overflow:hidden;
}

body{
  font-family:
    ui-sans-serif,
    system-ui,
    -apple-system,
    Segoe UI,
    Roboto,
    Helvetica,
    Arial;

background:
radial-gradient(
    1200px 700px at 20% -10%,
    var(--bg1),
    transparent 65%
),
radial-gradient(
    1100px 700px at 120% 5%,
    var(--bg2),
    transparent 65%
),
radial-gradient(
    900px 700px at 50% 120%,
    var(--bg3),
    transparent 70%
),
var(--bg);

  display:flex;
  flex-direction:column;
  justify-content:center;
  align-items:center;
  color:var(--text);

  opacity:0;
  animation:bootFade 1.15s ease forwards;
}

@keyframes bootFade{
  from{ opacity:0; transform:scale(.985); }
  to{ opacity:1; transform:scale(1); }
}

.particles{
  position:fixed;
  inset:0;
  pointer-events:none;
  background-image:radial-gradient(color-mix(in srgb, var(--accent) 70%, transparent) 1px, transparent 1px);
  background-size:86px 86px;
  opacity:.18;
  animation:particleMove 60s linear infinite;
}

@keyframes particleMove{
  from{ transform:translateY(0); }
  to{ transform:translateY(-200px); }
}

.brand{
  display:flex;
  align-items:center;
  gap:14px;
  font-weight:800;
  font-size:3.75rem;
  line-height:1;
  animation:brandRise 1s ease forwards;
}

@keyframes brandRise{
  from{
    opacity:0;
    transform:translateY(34px);
  }
  to{
    opacity:1;
    transform:translateY(0);
  }
}

.brand svg{
  width:42px;
  height:42px;
  flex:0 0 auto;
  stroke:var(--accent);
  stroke-width:2;
  margin-top:4px;
  filter:
    drop-shadow(0 0 8px color-mix(in srgb, var(--accent) 75%, transparent))
    drop-shadow(0 0 18px color-mix(in srgb, var(--accent) 45%, transparent));
  animation:circlePulse 3s ease-in-out infinite;
}

@keyframes circlePulse{
  0%{
    transform:scale(1);
    filter:
      drop-shadow(0 0 7px color-mix(in srgb, var(--accent) 70%, transparent))
      drop-shadow(0 0 16px color-mix(in srgb, var(--accent) 40%, transparent));
  }
  50%{
    transform:scale(1.03);
    filter:
      drop-shadow(0 0 12px color-mix(in srgb, var(--accent) 90%, transparent))
      drop-shadow(0 0 26px color-mix(in srgb, var(--accent) 60%, transparent));
  }
  100%{
    transform:scale(1);
    filter:
      drop-shadow(0 0 7px color-mix(in srgb, var(--accent) 70%, transparent))
      drop-shadow(0 0 16px color-mix(in srgb, var(--accent) 40%, transparent));
  }
}

.brand span{
  color:var(--accent);
  letter-spacing:-.02em;
  text-shadow:
    0 0 10px color-mix(in srgb, var(--accent) 85%, transparent),
    0 0 24px color-mix(in srgb, var(--accent) 50%, transparent),
    0 0 44px color-mix(in srgb, var(--accent) 30%, transparent);
  animation:titlePulse 3s ease-in-out infinite;
}

@keyframes titlePulse{
  0%{
    text-shadow:
      0 0 10px color-mix(in srgb, var(--accent) 85%, transparent),
      0 0 24px color-mix(in srgb, var(--accent) 50%, transparent),
      0 0 44px color-mix(in srgb, var(--accent) 30%, transparent);
  }
  50%{
    text-shadow:
      0 0 16px color-mix(in srgb, var(--accent) 100%, transparent),
      0 0 34px color-mix(in srgb, var(--accent) 65%, transparent),
      0 0 58px color-mix(in srgb, var(--accent) 38%, transparent);
  }
  100%{
    text-shadow:
      0 0 10px color-mix(in srgb, var(--accent) 85%, transparent),
      0 0 24px color-mix(in srgb, var(--accent) 50%, transparent),
      0 0 44px color-mix(in srgb, var(--accent) 30%, transparent);
  }
}

.tagline{
margin-top:18px;
font-size:1.1rem;
letter-spacing:.25em;
text-transform:uppercase;
color:#cfd8e3;

text-align:center;
width:100%;
}

@keyframes taglineFade{
  0%{ opacity:0; transform:translateY(8px); }
  100%{ opacity:1; transform:translateY(0); }
}

/* ---------- DuckDuckGo Search ---------- */

.search-box{
    margin-top:34px;
    width:min(620px, 82vw);
    animation:taglineFade .8s ease forwards;
}

.search-box form{
    width:100%;
}

.search-box input{

    width:100%;
    height:54px;

    background:rgba(255,255,255,.055);

    border:1px solid color-mix(in srgb, var(--accent) 35%, #3b4252);

    border-radius:16px;

    color:white;

    font-size:16px;

    padding:0 22px;

    outline:none;

    transition:.22s;
}

.search-box input::placeholder{
    color:#8f9bab;
}

.search-box input:hover{
    border-color:color-mix(in srgb, var(--accent) 60%, white);
}

.search-box input:focus{

    border-color:var(--accent);

    background:rgba(255,255,255,.08);

    box-shadow:
        0 0 0 1px var(--accent),
        0 0 24px color-mix(in srgb, var(--accent) 35%, transparent);
}

/* ---------- MiniAI Status ---------- */

.ai-status{
  position:absolute;
  bottom:42px;
  font-size:.95rem;
  font-weight:700;
  letter-spacing:.28em;
  color:var(--accent);
  opacity:.78;
  text-shadow:
    0 0 8px color-mix(in srgb, var(--accent) 85%, transparent),
    0 0 18px color-mix(in srgb, var(--accent) 35%, transparent);
  animation:miniPulse 3s ease-in-out infinite;
}

@keyframes miniPulse{
  0%{
    opacity:.68;
    text-shadow:
      0 0 8px color-mix(in srgb, var(--accent) 85%, transparent),
      0 0 18px color-mix(in srgb, var(--accent) 35%, transparent);
  }
  50%{
    opacity:.95;
    text-shadow:
      0 0 12px color-mix(in srgb, var(--accent) 100%, transparent),
      0 0 26px color-mix(in srgb, var(--accent) 50%, transparent);
  }
  100%{
    opacity:.68;
    text-shadow:
      0 0 8px color-mix(in srgb, var(--accent) 85%, transparent),
      0 0 18px color-mix(in srgb, var(--accent) 35%, transparent);
  }
}
</style>
</head>

<body>
  <div class="particles"></div>

  <div class="brand">
    <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <ellipse cx="16" cy="16" rx="13" ry="14"/>
    </svg>
    <span>Darkelf Browser</span>
  </div>

  <div class="search-box">
      <form method="GET" action="https://duckduckgo.com/lite/">
          <input
              name="q"
              autofocus
              autocomplete="off"
              spellcheck="false"
              placeholder="Search privately, or type a URL in the bar above">
      </form>
  </div>

  <div class="ai-status">
      Darkelf MiniAI Sentinel
  </div>
</body>
</html>
"""
