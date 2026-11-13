#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador do painel PinkPapa (G3 Health Service) — rastreio de cancer de colo do utero
por teste DNA-HPV com autocoleta (produto PinkPapa / PinkLab).
HTML self-contained: 5.570 municipios + 27 estados (IBGE Censo 2022, mulheres 25-64),
funil/ROI ao vivo, comparativo de custo, ranking, e gerador de PROPOSTA PDF hi-tech (PNSB).
Publica no GitHub Pages g3healthservice/dashboard-pinkpapa.
"""
import json, datetime, pathlib

BASE = pathlib.Path(__file__).resolve().parent
DADOS = json.load(open(BASE/"dados/municipios_pinkpapa.json", encoding="utf-8"))
_pate_path = BASE/"dados/pate_saldo_202607.json"
PATE = json.load(open(_pate_path, encoding="utf-8")) if _pate_path.exists() else {}
PATE_COMP = "07/2026 · competência 2025-01 a 2026-07 (NT 33/2026 · PATE)"
BUILD = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# endpoint do Apps Script (envio real de e-mail com anexo). Vazio = fallback mailto.
EP = BASE/"mail_endpoint.txt"
MAIL_ENDPOINT = EP.read_text(encoding="utf-8").strip() if EP.exists() else ""
# token (deve bater com TOKEN no AppsScript_EnvioProposta.gs)
TK = BASE/"mail_token.txt"
MAIL_TOKEN = TK.read_text(encoding="utf-8").strip() if TK.exists() else ""

CAPITAIS = {
 'AC':'Rio Branco','AL':'Maceió','AP':'Macapá','AM':'Manaus','BA':'Salvador','CE':'Fortaleza',
 'DF':'Brasília','ES':'Vitória','GO':'Goiânia','MA':'São Luís','MT':'Cuiabá','MS':'Campo Grande',
 'MG':'Belo Horizonte','PA':'Belém','PB':'João Pessoa','PR':'Curitiba','PE':'Recife','PI':'Teresina',
 'RJ':'Rio de Janeiro','RN':'Natal','RS':'Porto Alegre','RO':'Porto Velho','RR':'Boa Vista',
 'SC':'Florianópolis','SP':'São Paulo','SE':'Aracaju','TO':'Palmas'}
UF_NOMES = {
 'AC':'Acre','AL':'Alagoas','AP':'Amapá','AM':'Amazonas','BA':'Bahia','CE':'Ceará','DF':'Distrito Federal',
 'ES':'Espírito Santo','GO':'Goiás','MA':'Maranhão','MT':'Mato Grosso','MS':'Mato Grosso do Sul',
 'MG':'Minas Gerais','PA':'Pará','PB':'Paraíba','PR':'Paraná','PE':'Pernambuco','PI':'Piauí',
 'RJ':'Rio de Janeiro','RN':'Rio Grande do Norte','RS':'Rio Grande do Sul','RO':'Rondônia','RR':'Roraima',
 'SC':'Santa Catarina','SP':'São Paulo','SE':'Sergipe','TO':'Tocantins'}

muns = [[d['nome'], d['uf'], d['pop'] or 0, d['m2564'] or 0, (str(d.get('ibge') or ''))[:6]] for d in DADOS if d['m2564']]
muns.sort(key=lambda x:-x[3])
uf_stats = {}
for nome,uf,pop,m,ib in muns:
    s = uf_stats.setdefault(uf, {'pop':0,'m':0,'capital':None,'n':0})
    s['pop']+=pop; s['m']+=m; s['n']+=1
for nome,uf,pop,m,ib in muns:
    if CAPITAIS.get(uf)==nome:
        uf_stats[uf]['capital']=[nome,uf,pop,m]
# "Estado de/do/da X" — artigo correto por UF (DF não é Estado)
UF_ARTIGO = {
 'AC':'do Acre','AL':'de Alagoas','AP':'do Amapá','AM':'do Amazonas','BA':'da Bahia','CE':'do Ceará',
 'DF':'','ES':'do Espírito Santo','GO':'de Goiás','MA':'do Maranhão','MT':'de Mato Grosso',
 'MS':'de Mato Grosso do Sul','MG':'de Minas Gerais','PA':'do Pará','PB':'da Paraíba','PR':'do Paraná',
 'PE':'de Pernambuco','PI':'do Piauí','RJ':'do Rio de Janeiro','RN':'do Rio Grande do Norte',
 'RS':'do Rio Grande do Sul','RO':'de Rondônia','RR':'de Roraima','SC':'de Santa Catarina',
 'SP':'de São Paulo','SE':'de Sergipe','TO':'do Tocantins'}
for uf,s in uf_stats.items():
    s['nome'] = UF_NOMES.get(uf,uf)
    # rótulo pronto: "Estado da Bahia" / "Distrito Federal"
    s['label'] = 'Distrito Federal' if uf=='DF' else 'Estado '+UF_ARTIGO.get(uf,'de '+s['nome'])
    s['orgao'] = ('Secretaria de Saúde do Distrito Federal' if uf=='DF'
                  else 'Secretaria Estadual de Saúde '+UF_ARTIGO.get(uf,'de '+s['nome']))
TOT_M = sum(x[3] for x in muns); TOT_POP = sum(x[2] for x in muns)

DATA_JS   = json.dumps(muns, ensure_ascii=False, separators=(',',':'))
UFSTATS_JS= json.dumps(uf_stats, ensure_ascii=False, separators=(',',':'))
PATE_JS   = json.dumps(PATE, ensure_ascii=False, separators=(',',':'))
PATEUF_JS = json.dumps({v['uf']:k for k,v in PATE.items() if v.get('tipo')=='ESTADUAL'}, ensure_ascii=False, separators=(',',':'))

# Cobertura real de rastreio por município (SISCAN, triênio). COB[ibge6]=[pct,fonte,comp,fallback]
COB = {(str(d.get('ibge') or ''))[:6]: [round((d.get('cobSiscan') or 0)*100), d.get('cobFonte') or '',
        d.get('cobComp') or '', d.get('cobFallback') or ''] for d in DADOS if d.get('cobSiscan') is not None}
_ufn={}; _ufd={}
for d in DADOS:
    c=d.get('cobSiscan'); m=d.get('m2564') or 0
    if c is not None and m>0: _ufn[d['uf']]=_ufn.get(d['uf'],0)+c*m; _ufd[d['uf']]=_ufd.get(d['uf'],0)+m
COB_UF = {uf: round(_ufn[uf]/_ufd[uf]*100) for uf in _ufn if _ufd[uf]>0}
COB_JS = json.dumps(COB, ensure_ascii=False, separators=(',',':'))
COBUF_JS = json.dumps(COB_UF, ensure_ascii=False, separators=(',',':'))

def vend(name):
    return open(BASE/"vendor"/name, encoding="utf-8").read().replace('</script','<\\/script')
CHART = vend("chart.umd.js"); JSPDF = vend("jspdf.umd.min.js"); AUTOTABLE = vend("jspdf.autotable.min.js")

TOTM_BR = f"{TOT_M:,}".replace(",",".")

HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>PinkPapa · Painel de Rastreio de Câncer de Colo do Útero (DNA-HPV) — G3 Health Service</title>
<meta name="description" content="Painel de apoio à decisão para secretarias de saúde: dimensiona a população-alvo (mulheres 25–64), o custo-benefício e as metas do rastreio de câncer de colo do útero por teste DNA-HPV (PinkPapa), por município e por estado.">
<!-- cartão de compartilhamento (WhatsApp, e-mail, redes) -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="G3 Health Service · PinkPapa">
<meta property="og:title" content="Rastreio de câncer de colo do útero por teste DNA-HPV — PinkPapa">
<meta property="og:description" content="Painel por município e por estado: população-alvo (mulheres 25–64), custo-benefício frente ao tratamento oncológico e metas oficiais de rastreio. G3 Health Service.">
<meta property="og:url" content="https://g3healthservice.github.io/rastreio-colo-utero-pinkpapa/">
<meta property="og:image" content="https://g3healthservice.github.io/rastreio-colo-utero-pinkpapa/og.png">
<meta property="og:image:width" content="1600">
<meta property="og:image:height" content="840">
<meta property="og:locale" content="pt_BR">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Rastreio de câncer de colo do útero por teste DNA-HPV — PinkPapa">
<meta name="twitter:description" content="Painel por município e por estado: população-alvo, custo-benefício e metas de rastreio. G3 Health Service.">
<meta name="twitter:image" content="https://g3healthservice.github.io/rastreio-colo-utero-pinkpapa/og.png">
<style>
:root{--pink:#E6007E;--pink2:#FF4DA6;--wine:#7C1D4F;--green:#12A97A;--red:#C81E5B;
 --ink:#2A1622;--muted:#7a6b73;--bg:#fff;--soft:#fff2f8;--line:#f1d9e6;--card:#fff;}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.5}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
a{color:var(--pink)} h1,h2,h3{margin:0}
.hero{background:linear-gradient(135deg,#E6007E 0%,#B4126A 55%,#7C1D4F 100%);color:#fff;padding:46px 0 40px}
.hero .brand{font-weight:800;letter-spacing:.5px;font-size:14px;opacity:.9;text-transform:uppercase}
.hero h1{font-size:30px;margin:10px 0 6px;font-weight:800;line-height:1.15}
.hero p{font-size:15px;opacity:.95;max-width:760px}
.hero .kpis{display:flex;flex-wrap:wrap;gap:14px;margin-top:22px}
.hero .kpi{background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.22);border-radius:14px;padding:12px 16px;min-width:150px}
.hero .kpi b{display:block;font-size:22px;font-weight:800}
.hero .kpi span{font-size:12px;opacity:.9}
section{padding:38px 0;border-bottom:1px solid var(--line)}
section.alt{background:var(--soft)}
.h{color:var(--pink);font-weight:800;font-size:13px;letter-spacing:1px;text-transform:uppercase}
.title{font-size:23px;font-weight:800;margin:6px 0 18px;line-height:1.2}
.lead{color:var(--muted);max-width:820px;margin:-8px 0 18px;font-size:15px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}
.card .num{font-size:27px;font-weight:800;color:var(--wine)}
.card .num.pink{color:var(--pink)}.card .num.green{color:var(--green)}.card .num.red{color:var(--red)}
.card .lbl{font-size:13.5px;margin-top:4px}
.card .src{font-size:11px;color:var(--muted);margin-top:8px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;margin-top:6px}
.selrow{display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end}
.selrow .fld{flex:1;min-width:200px}
label{font-size:12.5px;color:var(--muted);font-weight:600;display:block;margin-bottom:4px}
input[type=text],input[type=number],select{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:10px;font-size:14px;background:#fff;color:var(--ink)}
.tabs{display:flex;gap:8px;margin-bottom:14px}
.tab{padding:9px 18px;border-radius:999px;border:1px solid var(--line);background:#fff;color:var(--muted);font-weight:700;font-size:13.5px;cursor:pointer}
.tab.on{background:var(--pink);color:#fff;border-color:var(--pink)}
.muni-hero{display:flex;flex-wrap:wrap;gap:16px;align-items:baseline;margin:16px 0 4px}
.muni-hero .mn{font-size:24px;font-weight:800}
.muni-hero .mt{color:var(--muted);font-size:14px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:14px}
@media(max-width:820px){.grid2{grid-template-columns:1fr}}
.ctl{display:flex;align-items:center;gap:10px;margin:9px 0}
.ctl label{flex:1;margin:0}
.ctl input[type=range]{flex:1.4;accent-color:var(--pink)}
.ctl .rangeval{width:56px;text-align:right;font-weight:700;color:var(--wine);font-size:13px}
.ctl input[type=number]{width:96px}
.driver{background:linear-gradient(135deg,#fff2f8,#ffe1f1);border:2px solid var(--pink);border-radius:14px;padding:14px 16px;margin-bottom:16px;box-shadow:0 3px 14px rgba(230,0,126,.14)}
.driver h4{margin:0 0 2px;color:var(--wine);font-size:14.5px;display:flex;align-items:center;gap:6px;font-weight:800}
.driver .hint{font-size:11.5px;color:var(--muted);margin:0 0 12px;line-height:1.35}
.driver .ctl{margin:6px 0}.driver .ctl label{font-weight:700;color:var(--ink)}
.driver .ctl input[type=range]{flex:1.4;height:6px}
.driver .ctl .rangeval{width:52px;font-size:16px;color:var(--pink)}
.driver .vfield{display:flex;align-items:center;gap:10px;margin-top:10px;padding-top:10px;border-top:1px dashed var(--pink2)}
.driver .vfield label{flex:1;margin:0;font-weight:700;color:var(--ink);line-height:1.25}
.driver .vfield .pre{color:var(--wine);font-weight:800}
.driver .vfield input{width:150px;font-weight:800;font-size:15px;border:2px solid var(--pink);border-radius:8px;padding:7px 9px;text-align:right;color:var(--wine)}
.premlabel{font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin:4px 0 2px}
.step{display:flex;align-items:flex-start;gap:10px;margin:9px 0}
.step .lbl{width:230px;font-size:12.5px;display:flex;flex-direction:column}
.step .lbl .sub{font-size:10.5px;color:#9A6A86;font-weight:400;line-height:1.25;margin-top:2px}
.step .bar-track{flex:1;background:#f6e6ef;border-radius:8px;height:16px;overflow:hidden;margin-top:2px}
.step .bar-fill{height:100%;background:linear-gradient(90deg,var(--pink),var(--pink2));border-radius:8px}
.step .val{width:92px;text-align:right;font-weight:700;font-size:13px;color:var(--wine);margin-top:1px}
.funnel-head{background:#fff0f7;border:1px solid #f3cfe3;border-radius:10px;padding:10px 12px;font-size:13px;color:var(--wine);margin-bottom:10px;line-height:1.45}
.roi{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px}
.roi .b{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px;text-align:center}
.roi .b b{display:block;font-size:22px;font-weight:800;color:var(--wine)}
.roi .b.green b{color:var(--green)}.roi .b span{font-size:11.5px;color:var(--muted)}
.callout{background:#fff6fb;border:1px solid var(--line);border-left:4px solid var(--pink);border-radius:10px;padding:12px 14px;font-size:13px;margin-top:12px}
.btnrow{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px;align-items:center}
.btn{background:var(--pink);color:#fff;border:none;border-radius:10px;padding:11px 18px;font-size:14px;font-weight:700;cursor:pointer}
.btn.sec{background:#fff;color:var(--pink);border:1px solid var(--pink)}
.btn:disabled{opacity:.5;cursor:wait}
.btn:hover{filter:brightness(1.05)}
#mailStatus{font-size:13px;font-weight:600}
table.cmp{width:100%;border-collapse:collapse;margin-top:10px;font-size:13.5px}
table.cmp th,table.cmp td{border:1px solid var(--line);padding:10px 12px;text-align:left}
table.cmp th{background:#fbe7f2;color:var(--wine)}
table.cmp td.pp{background:#fff2f8;font-weight:600}
.rank{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:8px}
.rank th,.rank td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:right}
.rank th:first-child,.rank td:first-child,.rank th:nth-child(2),.rank td:nth-child(2){text-align:left}
.rank th{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase}
.rank tr{cursor:pointer}.rank tr:hover td{background:var(--soft)}
#rankWrap.scroll{max-height:440px;overflow-y:auto;border:1px solid var(--line);border-radius:12px}
#rankWrap.scroll .rank th{position:sticky;top:0;background:#fbe7f2;z-index:1}
#rankWrap.scroll .rank th,#rankWrap.scroll .rank td{padding-left:12px;padding-right:12px}
.pill{display:inline-block;background:#fbe7f2;color:var(--wine);border-radius:999px;padding:3px 10px;font-size:12px;font-weight:700;margin:2px 4px 2px 0}
.foot{padding:26px 0;color:var(--muted);font-size:12.5px}
.foot b{color:var(--ink)}
.tag{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:4px 12px;font-size:12px;margin-top:14px}
.note{font-size:11.5px;color:var(--muted);margin-top:6px}
.src2{font-size:11px;color:var(--muted)}
.abas{position:sticky;top:0;z-index:50;background:#fff;border-bottom:1px solid var(--line);box-shadow:0 2px 10px rgba(0,0,0,.05)}
.abas .wrap{display:flex;flex-wrap:wrap;align-items:center;gap:0 4px;padding-top:6px;padding-bottom:0}
@media(max-width:640px){.abas .wrap{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:thin}.aba.destaque{order:-1;margin-left:0}.aba .longo{display:none}}
.aba{flex:0 0 auto;background:none;border:none;border-bottom:3px solid transparent;padding:9px 12px;font:inherit;font-size:13.5px;font-weight:600;color:var(--muted);cursor:pointer;white-space:nowrap}
.aba:hover{color:var(--wine)}
.aba.on{color:var(--pink);border-bottom-color:var(--pink)}
.aba.destaque{background:var(--pink);color:#fff;border:none;border-radius:999px;margin:3px 6px;padding:6px 16px;font-weight:800;box-shadow:0 2px 8px rgba(230,0,126,.35)}
.aba.destaque:hover{color:#fff;filter:brightness(1.08)}
.aba.destaque.on{color:#fff;box-shadow:0 0 0 3px #ffc9e4,0 2px 8px rgba(230,0,126,.35)}
.cta{margin-top:18px;background:#fff;color:var(--pink);border:none;border-radius:12px;padding:13px 22px;font:inherit;font-size:16px;font-weight:800;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.18)}
.cta:hover{filter:brightness(.97)}
.oculta{display:none!important}
@media print{.abas{display:none}.oculta{display:block!important}}
</style>
</head>
<body>

<nav class="abas" aria-label="Seções do painel"><div class="wrap" role="tablist">
  <button class="aba on" role="tab" onclick="abrir(0)">Capa</button>
  <button class="aba" role="tab" onclick="abrir(1)">01 · O problema</button>
  <button class="aba" role="tab" onclick="abrir(2)">02 · A solução<span class="longo"> e seu enquadramento oficial</span></button>
  <button class="aba destaque" role="tab" onclick="abrir(3)">🎯 03 · Dimensionamento</button>
  <button class="aba" role="tab" onclick="abrir(4)">04 · Custo-benefício</button>
  <button class="aba" role="tab" onclick="abrir(5)">05 · Metas e cobertura</button>
  <button class="aba" role="tab" onclick="abrir(6)">06 · Ranking</button>
  <button class="aba" role="tab" onclick="abrir(7)">07 · Metodologia</button>
</div></nav>

<div class="hero"><div class="wrap">
  <div class="brand">G3 Health Service · PinkPapa (PinkLab)</div>
  <h1>Rastreio de câncer de colo do útero por teste DNA-HPV com autocoleta</h1>
  <p>Painel de apoio à decisão para secretarias municipais e estaduais de saúde: dimensiona a população-alvo (mulheres de 25 a 64 anos), o custo-benefício frente ao tratamento oncológico e o alinhamento às metas oficiais — por município ou por estado.</p>
  <div class="kpis">
    <div class="kpi"><b>__TOTM__</b><span>mulheres de 25 a 64 anos no Brasil (Censo 2022) — população-alvo</span></div>
    <div class="kpi"><b>17.010</b><span>casos novos/ano de câncer de colo do útero (INCA)</span></div>
    <div class="kpi"><b>7.143</b><span>óbitos em 2023 — 1 mulher a cada ~90 min</span></div>
    <div class="kpi"><b>R$ 590</b><span>custo do kit × dezenas de milhares no tratamento tardio</span></div>
  </div>
  <div class="tag">Autoteste DNA-HPV homologado ANVISA · SIGTAP 0202100251 · Incorporado ao SUS (Portaria SECTICS/MS nº 3/2024)</div>
  <div><button class="cta" onclick="abrir(3)">🎯 Dimensionar meu município ou estado →</button></div>
</div></div>

<section><div class="wrap">
  <div class="h">01 · O problema</div>
  <h3 class="title">Câncer de colo do útero: quase 100% evitável, mas ainda mata milhares por rastreio tardio</h3>
  <div class="cards">
    <div class="card"><div class="num red">17.010</div><div class="lbl">casos novos por ano (taxa 15,38/100 mil mulheres)</div><div class="src">INCA — Estimativa 2023–2025</div></div>
    <div class="card"><div class="num red">7.143</div><div class="lbl">óbitos em 2023, +8,3% desde 2019 — 3º câncer mais frequente entre brasileiras</div><div class="src">Observatório de Oncologia (SIM/SUS)</div></div>
    <div class="card"><div class="num">1 em 7</div><div class="lbl">mulheres com citologia normal e HPV-16+ tinham lesão de alto grau <b>não detectada</b> pelo Papanicolau</div><div class="src">Estudo ATHENA</div></div>
    <div class="card"><div class="num">4 a 6 meses</div><div class="lbl">de espera no agendamento; rastreio ainda oportunístico</div><div class="src">Diretrizes MS / PinkLab</div></div>
  </div>
  <div class="callout">O HPV é a infecção sexualmente transmissível mais prevalente do mundo e o <b>principal causador do câncer de colo do útero</b>. A citologia (Papanicolau) tem sensibilidade de apenas 55–70% para lesões de alto grau (NIC2+); o teste de DNA-HPV chega a 90–95%, com valor preditivo negativo de 98–99% — o que permite espaçar o rastreio para 5 anos após resultado negativo.</div>
</div></section>

<section class="alt"><div class="wrap">
  <div class="h">02 · A solução e seu enquadramento oficial</div>
  <h3 class="title">PinkPapa: autocoleta de DNA-HPV, alinhada às novas diretrizes do Ministério da Saúde</h3>
  <div class="grid2">
    <div class="panel">
      <b style="color:var(--wine)">Como funciona</b>
      <p style="font-size:14px">Autoteste de HPV homologado pela ANVISA. A mulher faz a <b>autocoleta</b> em UBS, UPA, centros comunitários ou hospitais — sem mesa ginecológica, sem espéculo, sem constrangimento. Detecta <b>28 tipos de HPV</b> (19 de alto risco oncogênico + 9 de baixo risco), informando o tipo viral. Acompanhamento por IA por até 5 anos.</p>
      <div><span class="pill">Alto risco: 16, 18, 31, 33, 35, 39, 45, 51, 52, 56, 58, 59, 66, 68…</span>
      <span class="pill">Antecipa o diagnóstico em até 10 anos</span>
      <span class="pill">Aceitação ~100% (não invasivo)</span></div>
    </div>
    <div class="panel">
      <b style="color:var(--wine)">Nome técnico e enquadramento (o que buscar no edital)</b>
      <table class="cmp" style="margin-top:8px">
        <tr><th>Campo</th><th>Valor oficial</th></tr>
        <tr><td>Procedimento SIGTAP</td><td class="pp">0202100251 — Exame molecular de detecção de HPV</td></tr>
        <tr><td>Descrição técnica</td><td>Análise molecular de material cérvico-vaginal por amplificação de ácido nucleico (PCR) com genotipagem parcial ou estendida</td></tr>
        <tr><td>Faixa etária</td><td>25 a 64 anos (300–779 meses)</td></tr>
        <tr><td>Financiamento no SUS</td><td>Média e Alta Complexidade (MAC) — fonte do projeto selecionável na proposta (MAC, PAP, emenda, crédito, doação)</td></tr>
        <tr><td>Incorporação</td><td>Portaria SECTICS/MS nº 3, de 07/03/2024 (CONITEC)</td></tr>
        <tr><td>Diretriz</td><td>Rastreamento organizado — DNA-HPV substitui o Papanicolau (MS/INCA, 2024)</td></tr>
      </table>
      <div class="note">Para compra de insumo/kit, o item é catalogado como material de detecção de DNA-HPV (CATMAT/BPS); o procedimento/serviço é o SIGTAP 0202100251.</div>
    </div>
  </div>
</div></section>

<section><div class="wrap">
  <div class="h">03 · Dimensionamento</div>
  <h3 class="title">Perfil por município ou por estado</h3>
  <p class="lead">Todos os números partem da população feminina de 25 a 64 anos do Censo 2022 (IBGE). Premissas ajustáveis; valores-padrão documentados na metodologia.</p>
  <div class="panel">
    <div class="tabs">
      <div class="tab on" id="tab-mun" onclick="setEscopo('mun')">🏙️ Município</div>
      <div class="tab" id="tab-uf" onclick="setEscopo('uf')">🗺️ Estado (UF)</div>
    </div>
    <div class="selrow" id="row-mun">
      <div class="fld">
        <label>Município (digite para buscar — sem precisar de acento)</label>
        <input type="text" id="busca" placeholder="Ex.: sao paulo, salvador, campinas…" autocomplete="off" oninput="onBusca()">
        <div id="sug" style="position:relative"></div>
      </div>
    </div>
    <div class="selrow" id="row-uf" style="display:none">
      <div class="fld" style="max-width:380px">
        <label>Estado — a proposta será dirigida à Secretaria Estadual de Saúde</label>
        <select id="seluf" onchange="pickUF(this.value)"><option value="">Selecione o estado…</option></select>
      </div>
    </div>

    <div id="muniBox" style="display:none">
      <div class="muni-hero"><div class="mn" id="mn"></div><div class="mt" id="mt"></div><div class="mt" id="mcov" style="margin-top:6px;font-size:12px;line-height:1.4"></div></div>
      <div class="grid2">
        <div>
          <div class="driver">
            <h4>🎯 Defina o tamanho da proposta</h4>
            <p class="hint">Use a <b>cobertura-meta</b> ou digite direto o <b>valor-alvo em R$</b> — os dois andam juntos e <b>recalculam automaticamente</b> testes, custo, lesões, casos e mortes evitados logo abaixo.</p>
            <div class="ctl"><label>Cobertura-meta de rastreio (OMS: 70%)</label><input type="range" id="in-cov-meta" min="1" max="100" step="0.1" value="70" oninput="calc()"><span class="rangeval" id="v-cov-meta">70%</span></div>
            <div class="vfield"><label>Valor-alvo da proposta<br><span class="hint" style="margin:0">ajusta a meta para caber neste orçamento</span></label><span class="pre">R$</span><input type="text" inputmode="decimal" id="in-valor-alvo" placeholder="0,00" oninput="fromValor()" onblur="fmtValor()"></div>
          </div>
          <div class="premlabel">Premissas do cenário (ajustáveis)</div>
          <div class="ctl"><label>Cobertura atual de rastreio (SISCAN — ajustável)</label><input type="range" id="in-cov-atual" min="1" max="100" value="40" oninput="calc()"><span class="rangeval" id="v-cov-atual">40%</span></div>
          <div class="ctl"><label>Adesão ao convite</label><input type="range" id="in-adesao" min="1" max="100" value="80" oninput="calc()"><span class="rangeval" id="v-adesao">80%</span></div>
          <div class="ctl"><label>Prevalência de HPV de alto risco</label><input type="range" id="in-prev" min="1" max="30" value="10" oninput="calc()"><span class="rangeval" id="v-prev">10%</span></div>
          <div class="ctl"><label>Lesões alto grau (NIC2+) entre HPV+</label><input type="range" id="in-lesao" min="1" max="40" value="12" oninput="calc()"><span class="rangeval" id="v-lesao">12%</span></div>
          <div class="ctl"><label>Progressão a câncer se não tratada</label><input type="range" id="in-prog" min="1" max="40" value="15" oninput="calc()"><span class="rangeval" id="v-prog">15%</span></div>
          <div class="ctl"><label>Preço do kit PinkPapa (R$)</label><input type="number" id="in-preco" value="590" min="1" oninput="calc()"></div>
          <div class="ctl"><label>Prazo de execução (meses)</label><input type="number" id="in-prazo" value="12" min="1" max="60" oninput="calc()"></div>
        </div>
        <div>
          <div id="funnel-head" class="funnel-head"></div>
          <div id="funnel-box"></div>
          <div class="roi">
            <div class="b"><b id="roi-custo">—</b><span>Investimento no rastreio</span></div>
            <div class="b green"><b id="roi-cpm">—</b><span>Custo por morte evitada</span></div>
            <div class="b green"><b id="roi-soc">—</b><span>Retorno socioeconômico</span></div>
          </div>
          <div class="callout" style="margin-top:12px" id="resumo"></div>
        </div>
      </div>
      <div class="callout"><b>Premissa importante:</b> "casos suspeitos/lesões" não são câncer confirmado. O funil aplica etapas de confirmação e progressão ajustáveis (história natural do HPV) antes de estimar casos e mortes evitados — para não superestimar o retorno. Ajuste os controles à realidade epidemiológica local.</div>

      <div id="pate-box" style="margin-top:14px"></div>

      <div class="selrow" style="margin-top:16px">
        <div class="fld"><label>Destinatário / autoridade (entra na proposta)</label><input type="text" id="in-dest-nome" placeholder="Ex.: Sr. Nicolau — Secretário de Saúde"></div>
        <div class="fld" style="max-width:280px"><label>E-mail do destinatário</label><input type="text" id="in-dest-email" placeholder="nome@municipio.gov.br"></div>
        <div class="fld" style="max-width:280px"><label>Fonte de recurso (entra na proposta)</label>
          <select id="in-fonte" onchange="calc()">
            <option value="MAC">MAC — Média e Alta Complexidade</option>
            <option value="PAP">PAP — Piso da Atenção Primária</option>
            <option value="EMENDA">Emenda parlamentar</option>
            <option value="CREDITO">Crédito / financiamento</option>
            <option value="DOACAO">Doação / patrocínio</option>
            <option value="PROPRIO">Recurso próprio do município</option>
            <option value="OUTRO">Outra fonte (definir no plano)</option>
          </select></div>
        <div class="fld" style="max-width:360px"><label>Rota jurídica (define as peças e a estrutura das partes)</label>
          <select id="in-instrumento" onchange="calc()">
            <option value="MROSC">Parceria com OSC (MROSC) — Lei 13.019/2014</option>
            <option value="CREDENCIAMENTO">Credenciamento — Lei 14.133/2021 (arts. 79 e 74, IV)</option>
          </select></div>
      </div>
      <div class="selrow" style="margin-top:8px">
        <div class="fld"><label>Executante / proponente</label><input type="text" id="in-prop-nome" value="PinkPapa · PinkLab"></div>
        <div class="fld"><label>Contato — e-mail (opcional)</label><input type="text" id="in-prop-email" placeholder="contato@pinkpapa.com.br"></div>
        <div class="fld" style="max-width:200px"><label>Contato — telefone (opcional)</label><input type="text" id="in-prop-tel" placeholder=""></div>
      </div>
      <div class="btnrow">
        <button class="btn" onclick="baixarApresentacao()">🎯 Apresentação (projeto técnico) — pronta para enviar ao gestor</button>
        <button class="btn" onclick="baixarPacote()">📦 Baixar pacote completo (proposta + proposta técnica + nota técnica)</button>
        <button class="btn sec" onclick="baixarPDF()">📄 Só a proposta (PNSB)</button>
        <button class="btn sec" onclick="baixarPropTec()">📑 Só a proposta técnica</button>
        <button class="btn sec" onclick="baixarNotaTec()">🧾 Só a nota técnica</button>
        <button class="btn sec" id="btnMail" onclick="enviarEmail()">✉️ Enviar proposta por e-mail</button>
        <span id="mailStatus"></span>
      </div>
      <div class="btnrow" style="margin-top:6px">
        <span class="note" style="width:100%;margin-bottom:2px">Peças de instrução, conforme a rota jurídica selecionada acima (geradas com os dados do município):</span>
        <button class="btn sec" onclick="baixarETP()">📘 ETP (serve às duas rotas)</button>
        <button class="btn sec" onclick="baixarNotaTec()">🧾 Nota Técnica (serve às duas rotas)</button>
        <button class="btn sec" id="btnInstr" onclick="baixarInstrumento()">📗 Minuta do instrumento</button>
        <button class="btn sec" id="btnPeca" onclick="baixarPeca()">📙 Plano / Termo de Referência</button>
        <a class="btn sec" href="projeto-ribeirao-preto.html" target="_blank" rel="noopener" style="text-decoration:none">📑 Apresentação do projeto (modelo · Ribeirão Preto)</a>
        <span class="note" style="width:100%;margin-top:4px">A rota <b>MROSC</b> gera Termo de Colaboração + Plano de Trabalho; a rota <b>Credenciamento</b> gera Edital de credenciamento + Termo de Referência.</span>
        <span class="note" style="width:100%;margin-top:4px">Modelos editáveis (.docx) — comuns: <a href="modelos/ETP_RastreioColoUtero_DNA-HPV.docx">ETP</a> · <a href="modelos/NotaTecnica_RastreioColoUtero_DNA-HPV.docx">Nota Técnica</a> · MROSC: <a href="modelos/MROSC_TermoColaboracao_RastreioColoUtero.docx">Termo de Colaboração</a> · <a href="modelos/MROSC_PlanoDeTrabalho_RastreioColoUtero.docx">Plano de Trabalho</a> · Credenciamento: <a href="modelos/Credenciamento_Edital_RastreioColoUtero.docx">Edital</a> · <a href="modelos/Credenciamento_TermoReferencia_RastreioColoUtero.docx">Termo de Referência</a></span>
      </div>
      <div class="note" id="mailNote"></div>
    </div>
  </div>
</div></section>

<section class="alt"><div class="wrap">
  <div class="h">04 · Custo-benefício</div>
  <h3 class="title">R$ 590 na prevenção × dezenas de milhares no tratamento tardio</h3>
  <p class="lead">O valor por exame do PinkPapa cruzado com o custo real dos procedimentos do SUS. Fontes: Observatório de Oncologia (APAC/SIA-SIH) e Tabela SIGTAP.</p>
  <table class="cmp">
    <tr><th>Item</th><th>PinkPapa (DNA-HPV, autocoleta)</th><th>Papanicolau (citologia)</th><th>Tratamento do câncer (tardio)</th></tr>
    <tr><td>Custo unitário</td><td class="pp">R$ 590 / mulher</td><td>R$ 14,37 / exame (SIGTAP)</td><td>R$ 10.000 / paciente / ano</td></tr>
    <tr><td>Sensibilidade (NIC2+)</td><td class="pp">90–95%</td><td>55–70%</td><td>—</td></tr>
    <tr><td>Intervalo</td><td class="pp">5 anos (após negativo)</td><td>3 anos (2 normais)</td><td>—</td></tr>
    <tr><td>Coleta</td><td class="pp">Autocoleta (sem profissional/estrutura)</td><td>Requer médico/enfermeiro + estrutura</td><td>—</td></tr>
    <tr><td>Procedimentos típicos</td><td class="pp">1 teste + acompanhamento IA</td><td>Exame + consulta + repetições</td><td>Cirurgia + radioterapia (R$ 4.038/APAC) + braquiterapia (R$ 3.936/APAC) + quimioterapia + internações (R$ 2.183)</td></tr>
  </table>
  <div class="cards" style="margin-top:16px">
    <div class="card"><div class="num pink">≈ 17×</div><div class="lbl">um tratamento oncológico anual equivale a ~17 kits PinkPapa</div><div class="src">R$ 10 mil ÷ R$ 590</div></div>
    <div class="card"><div class="num green">−30%</div><div class="lbl">de redução estimada de custos do SUS no longo prazo com rastreio por DNA-HPV</div><div class="src">CONITEC</div></div>
    <div class="card"><div class="num">R$ 184 mi</div><div class="lbl">impacto incremental em 5 anos da incorporação — compensado pela queda em tratamentos tardios</div><div class="src">CONITEC (2024)</div></div>
    <div class="card"><div class="num red">64%</div><div class="lbl">das pacientes em radioterapia se tratam fora do município</div><div class="src">Observatório de Oncologia</div></div>
  </div>
</div></section>

<section><div class="wrap">
  <div class="h">05 · Metas e cobertura</div>
  <h3 class="title">Alinhamento às metas oficiais de eliminação</h3>
  <div class="cards">
    <div class="card"><div class="num pink">90-70-90</div><div class="lbl">Meta OMS até 2030: <b>90%</b> vacinadas, <b>70%</b> rastreadas com teste de alta performance, <b>90%</b> tratadas</div><div class="src">OMS/ONU (194 países, 2020)</div></div>
    <div class="card"><div class="num">≥ 40%</div><div class="lbl">meta de cobertura do exame de rastreio (Previne Brasil)</div><div class="src">Ministério da Saúde</div></div>
    <div class="card"><div class="num red">em queda</div><div class="lbl">cobertura de citologia nas capitais no menor valor da série histórica (2023)</div><div class="src">SISCAN / INCA</div></div>
    <div class="card"><div class="num green">-97%</div><div class="lbl">de redução possível na incidência atingindo as metas 90-70-90</div><div class="src">OMS / SBOC</div></div>
  </div>
  <div class="callout">Estratégia de eliminação = <b>Vacinação + Rastreio + Tratamento</b>. O PinkPapa atua no pilar do <b>rastreio</b>, com o teste de alta performance (DNA-HPV) recomendado pela OMS para atingir a meta de 70% — e a autocoleta é o vetor para alcançar as mulheres que nunca se rastrearam.</div>
</div></section>

<section class="alt"><div class="wrap">
  <div class="h">06 · Ranking de oportunidade</div>
  <h3 class="title">Por população-alvo (mulheres 25–64 anos)</h3>
  <div class="tabs">
    <div class="tab on" id="rtab-mun" onclick="setRank('mun')">Municípios</div>
    <div class="tab" id="rtab-uf" onclick="setRank('uf')">Estados</div>
  </div>
  <p class="lead">Clique em uma linha para carregá-la na aba 03 · Dimensionamento. Para um município específico, use a busca daquela aba.</p>
  <div id="rankWrap"><table class="rank"><thead id="rankHead"></thead><tbody id="rankBody"></tbody></table></div>
  <div class="btnrow"><button class="btn sec" id="btnRankMore" onclick="toggleRank()">Ver ranking completo ▾</button><span class="note" id="rankCount"></span></div>
</div></section>

<section><div class="wrap">
  <div class="h">07 · Metodologia e fontes</div>
  <h3 class="title">Como os números são calculados</h3>
  <div class="grid2">
    <div class="panel"><b style="color:var(--wine)">Modelo do funil</b>
      <ol style="font-size:13.5px;padding-left:18px">
        <li>População-alvo = mulheres de 25 a 64 anos (IBGE, Censo 2022, SIDRA 9514) — do município ou somadas no estado.</li>
        <li>Mulheres convocadas (busca ativa) = alvo × (cobertura-meta − cobertura atual).</li>
        <li>Mulheres atendidas (testadas) = convocadas × adesão ao convite.</li>
        <li>HPV alto risco+ = testes × prevalência.</li>
        <li>Lesões NIC2+ = HPV+ × % de lesão; das quais a citologia perderia (95%−60%).</li>
        <li>Casos de câncer evitados = lesões × progressão evitada pelo tratamento precoce.</li>
        <li>Mortes evitadas = casos × letalidade evitável (40%).</li>
      </ol>
    </div>
    <div class="panel"><b style="color:var(--wine)">Fontes oficiais</b>
      <ul class="src2" style="padding-left:18px;line-height:1.7">
        <li>IBGE — Censo 2022 (SIDRA 9514/4709).</li>
        <li>INCA — Estimativa de Incidência 2023–2025.</li>
        <li>Observatório de Oncologia — custos APAC/SIA-SIH.</li>
        <li>SIGTAP — procedimentos 0202100251 e 0203010086.</li>
        <li>CONITEC/MS — Portaria SECTICS nº 3/2024.</li>
        <li>OMS/ONU — estratégia 90-70-90.</li>
      </ul>
      <div class="note">Ferramenta de apoio à decisão e prospecção. Não substitui avaliação epidemiológica local nem diagnóstico médico.</div>
    </div>
  </div>
</div></section>

<div class="wrap foot">
  <b>G3 Health Service</b> · Painel PinkPapa (PinkLab) — rastreio de câncer de colo do útero por DNA-HPV.<br>
  Contato: g3.healthservice@proton.me · Build __BUILD__ · Dados: IBGE Censo 2022, INCA, Observatório de Oncologia, CONITEC, OMS.
</div>

<script>
// Abas: capa (hero) + uma por <section>; #aba-N na URL abre direto e permite compartilhar o link da aba
const ABAS=[document.querySelector('.hero'),...document.querySelectorAll('body>section')];
function abrir(n,semHash){
  n=Math.max(0,Math.min(ABAS.length-1,n|0));
  ABAS.forEach((el,i)=>el.classList.toggle('oculta',i!==n));
  document.querySelectorAll('.aba').forEach((b,i)=>{b.classList.toggle('on',i===n);b.setAttribute('aria-selected',i===n)});
  document.querySelectorAll('.aba')[n].scrollIntoView({block:'nearest',inline:'nearest'});
  if(!semHash)history.replaceState(null,'','#aba-'+n);
  window.scrollTo(0,0);
}
abrir(+(location.hash.match(/^#aba-(\d+)$/)||[])[1]||0,true);
</script>
<script>__CHART__</script>
<script>__JSPDF__</script>
<script>__AUTOTABLE__</script>
<script>
const MUNICIPIOS = __DATA__;    // [nome, uf, pop, m2564, ibge6]
const UF_STATS   = __UFSTATS__; // {uf:{pop,m,n,capital,nome}}
const PATE       = __PATE__;    // {codIbge6:{...saldo-gestor PATE...}}
const COB        = __COB__;     // {ibge6:[pct, fonte, competencia, fallback]} — cobertura real SISCAN
const COB_UF     = __COBUF__;   // {uf:pct} — cobertura ponderada por pop da UF
const PATE_UF    = __PATEUF__;  // {uf:codIbge6 estadual}
const PATE_COMP  = "__PATECOMP__";
const MAIL_ENDPOINT = "__MAIL_ENDPOINT__";
const MAIL_TOKEN = "__MAIL_TOKEN__";
const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();
let selected = null, lastCalc = null, escopo = 'mun';

const fmt = n => Math.round(n).toLocaleString('pt-BR');
const fmtMoney = n => 'R$ '+Math.round(n).toLocaleString('pt-BR');
const fmtPct = n => (n*100).toFixed(0).replace('.',',')+'%';

/* ---------- escopo município / estado ---------- */
function setEscopo(e){
  escopo = e;
  document.getElementById('tab-mun').classList.toggle('on', e==='mun');
  document.getElementById('tab-uf').classList.toggle('on', e==='uf');
  document.getElementById('row-mun').style.display = e==='mun'?'flex':'none';
  document.getElementById('row-uf').style.display  = e==='uf'?'flex':'none';
  document.getElementById('muniBox').style.display='none';
  selected=null; lastCalc=null;
}
function onBusca(){
  const q = norm(document.getElementById('busca').value.trim());
  const sug = document.getElementById('sug');
  if(q.length<2){ sug.innerHTML=''; return; }
  const hits = MUNICIPIOS.filter(m=>norm(m[0]).includes(q)).slice(0,8);
  sug.innerHTML = '<div style="position:absolute;z-index:9;background:#fff;border:1px solid var(--line);border-radius:10px;width:100%;box-shadow:0 8px 24px rgba(124,29,79,.12);overflow:hidden">'+
    hits.map(m=>`<div style="padding:9px 12px;cursor:pointer;font-size:14px" onmousedown="pick('${m[0].replace(/'/g,"\\'")}','${m[1]}')">${m[0]} <span style="color:var(--muted)">/ ${m[1]} · ${m[3].toLocaleString('pt-BR')} mulheres 25-64</span></div>`).join('')+'</div>';
}
function pick(nome,uf){
  escopo='mun'; setEscopoTabs('mun');
  selected = MUNICIPIOS.find(m=>m[0]===nome && m[1]===uf);
  selected = [selected[0],selected[1],selected[2],selected[3],false,selected[4]];
  document.getElementById('busca').value = nome+' / '+uf;
  document.getElementById('sug').innerHTML='';
  show();
}
function pickUF(uf){
  if(!uf) return;
  escopo='uf'; setEscopoTabs('uf');
  const s = UF_STATS[uf];
  selected = [s.label, uf, s.pop, s.m, true, (PATE_UF[uf]||'')];
  document.getElementById('seluf').value = uf;
  show();
}
function setEscopoTabs(e){
  document.getElementById('tab-mun').classList.toggle('on', e==='mun');
  document.getElementById('tab-uf').classList.toggle('on', e==='uf');
  document.getElementById('row-mun').style.display = e==='mun'?'flex':'none';
  document.getElementById('row-uf').style.display  = e==='uf'?'flex':'none';
}
function show(){
  if(!selected) return;
  document.getElementById('muniBox').style.display='block';
  const isUF = selected[4];
  document.getElementById('mn').textContent = isUF ? selected[0] : selected[0]+' / '+selected[1];
  const extra = isUF ? ' · '+UF_STATS[selected[1]].n+' municípios' : '';
  document.getElementById('mt').textContent = selected[3].toLocaleString('pt-BR')+' mulheres de 25 a 64 anos · '+selected[2].toLocaleString('pt-BR')+' habitantes (Censo 2022)'+extra;
  // cobertura real: preenche o slider "Cobertura atual" com o dado por município (SISCAN, triênio)
  const cb = isUF ? (COB_UF[selected[1]]!=null?[COB_UF[selected[1]],'SISCAN (média da UF)','2022-2024','uf']:null) : COB[selected[5]];
  const covEl = document.getElementById('in-cov-atual');
  if(cb){ covEl.value = cb[0]; }
  document.getElementById('v-cov-atual').textContent = covEl.value+'%';
  const fbTxt = cb && cb[3] ? ' · <i>estimada por média '+(cb[3]==='uf'?'da UF':'nacional')+' (SISCAN local indisponível/implausível)</i>' : '';
  document.getElementById('mcov').innerHTML = cb
    ? 'Cobertura atual preenchida com dado real: <b>'+cb[0]+'%</b> — '+(cb[1]||'SISCAN')+', triênio '+(cb[2]||'2022-2024')+' (mulheres únicas rastreadas 25–64 ÷ população 25–64)'+fbTxt+'. &nbsp;·&nbsp; <b>Previne/APS</b> (coleta de citopatológico na APS): indicador por município exige acesso restrito ao SISAB — não disponível publicamente.'
    : 'Cobertura atual: ajuste manual (sem dado SISCAN para este recorte).';
  calc();
}

/* ---------- núcleo do cálculo ---------- */
const CUSTO_PRECOCE=1500, CUSTO_TARDIO=30000, VALOR_MORTE=1000000;
const SENS_DNA=0.95, SENS_CITO=0.60, LETALIDADE_EVIT=0.40;
const val = id => document.getElementById('in-'+id).value;

const FONTES={MAC:'Média e Alta Complexidade (MAC)',PAP:'Piso da Atenção Primária (PAP)',EMENDA:'emenda parlamentar',CREDITO:'crédito / financiamento',DOACAO:'doação / patrocínio',PROPRIO:'recurso próprio do município',OUTRO:'fonte a definir no plano de trabalho'};
function fonteSel(){const el=document.getElementById('in-fonte');const k=el?el.value:'MAC';return{key:k,label:FONTES[k]||k};}
const INSTRUMENTOS={
  MROSC:{key:'MROSC', lei:'Lei nº 13.019/2014',
    label:'Parceria com OSC — MROSC (Lei nº 13.019/2014)',
    base:'Parceria com Organização da Sociedade Civil por Termo de Colaboração, precedida de chamamento público (art. 24) ou de sua dispensa/inexigibilidade justificada (arts. 30–31), com Plano de Trabalho (art. 22) e prestação de contas (arts. 63–72).',
    baseLegalETP:'Lei nº 13.019/2014 (MROSC) — regime jurídico das parcerias com organizações da sociedade civil, instrumentalizadas por Termo de Colaboração, precedido de chamamento público (art. 24) ou de sua dispensa/inexigibilidade justificada (arts. 30 e 31);',
    conc:'legalmente enquadrável na Lei nº 13.019/2014 (parceria com organização da sociedade civil, por Termo de Colaboração)',
    prox:'do Plano de Trabalho, do instrumento de parceria (Termo de Colaboração) e da pesquisa de preços',
    pecas:[['termo','📗 Minuta de Termo de Colaboração'],['plano','📙 Plano de Trabalho']],
    docs:['Chamamento público (edital) ou justificativa de dispensa/inexigibilidade (arts. 30–31)','Plano de Trabalho (art. 22): metas, cronograma e memória de cálculo','Comprovação da OSC: CNPJ, estatuto e objeto social compatível','Certidões de regularidade (fiscal, trabalhista, FGTS) e consulta CEPIM/CADIN','Declarações dos arts. 33 e 34 (capacidade técnica e operacional)','Designação do gestor da parceria e da comissão de monitoramento e avaliação','Conta bancária específica e movimentação eletrônica dos recursos','Prestação de contas e relatório de execução do objeto (arts. 63–72)']},
  CREDENCIAMENTO:{key:'CREDENCIAMENTO', lei:'Lei nº 14.133/2021',
    label:'Credenciamento — Lei nº 14.133/2021 (arts. 79 e 74, IV)',
    base:'Contratação por credenciamento (art. 79), com chamamento público permanente, preços fixados pela Administração e inexigibilidade de licitação por inviabilidade de competição (art. 74, IV), precedida de Estudo Técnico Preliminar (ETP), Termo de Referência (TR) e pesquisa de preços (IN SEGES/ME nº 65/2021).',
    baseLegalETP:'Lei nº 14.133/2021 — contratação por credenciamento (art. 79), com inexigibilidade de licitação por inviabilidade de competição (art. 74, IV); planejamento (art. 18) e pesquisa de preços (art. 23);',
    conc:'legalmente enquadrável na Lei nº 14.133/2021 (credenciamento, com inexigibilidade de licitação por inviabilidade de competição — arts. 79 e 74, IV)',
    prox:'do Termo de Referência, do edital de credenciamento e da pesquisa de preços',
    pecas:[['edital','📗 Edital/Minuta de credenciamento'],['tr','📙 Termo de Referência']],
    docs:['Estudo Técnico Preliminar (ETP) e Termo de Referência (TR)','Edital de chamamento público permanente para credenciamento (art. 79)','Justificativa da inviabilidade de competição e da inexigibilidade (art. 74, IV)','Tabela de preços fixada pela Administração, ancorada em pesquisa de mercado (IN SEGES/ME nº 65/2021)','Requisitos técnicos, sanitários e de habilitação dos credenciados','Critério impessoal de distribuição das demandas entre credenciados','Termo de credenciamento, fiscalização e medição por laudo liberado']},
};
function instrSel(){const el=document.getElementById('in-instrumento');const k=el?el.value:'MROSC';return Object.assign({key:k},INSTRUMENTOS[k]||INSTRUMENTOS.MROSC);}
function atualizarBotoesRota(){const s=instrSel();const bi=document.getElementById('btnInstr'),bp=document.getElementById('btnPeca');
  if(bi)bi.textContent=s.pecas[0][1]; if(bp)bp.textContent=s.pecas[1][1];}
// valor-alvo (R$) -> cobertura-meta: inverte custoPrograma = popAlvo*(covM-covA)*ades*preco
function fromValor(){
  // máscara R$ pt-BR: agrupa milhares com ponto enquanto digita e mantém a vírgula dos centavos
  const vinp=document.getElementById('in-valor-alvo');
  const temVirg=vinp.value.includes(',');
  let [int,dec]=vinp.value.replace(/[^\d,]/g,'').split(',');
  dec=(dec||'').slice(0,2);
  vinp.value=(int?(+int).toLocaleString('pt-BR'):(temVirg?'0':''))+(temVirg?','+dec:'');
  const valor=parseFloat((int||'0')+'.'+(dec||'0'))||0;
  if(!selected) return;
  const popAlvo=selected[3];
  const covA=+val('cov-atual')/100, ades=+val('adesao')/100, preco=+val('preco')||0;
  if(valor<=0||preco<=0||ades<=0||popAlvo<=0){ calc(); return; }
  const adicionais=(valor/preco)/ades;
  const covM=Math.min(1, Math.max(covA, covA + adicionais/popAlvo));
  document.getElementById('in-cov-meta').value=Math.max(1,(covM*100).toFixed(1));
  calc();
}
function fmtValor(){ // ao sair do campo, normaliza para 2 casas (R$ 4.011.245,00)
  const vinp=document.getElementById('in-valor-alvo');
  const valor=parseFloat(vinp.value.replace(/\./g,'').replace(',','.'))||0;
  vinp.value=valor?valor.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2}):'';
}
function calc(){
  if(!selected) return;
  ['cov-atual','cov-meta','adesao','prev','lesao','prog'].forEach(id=>{
    const el=document.getElementById('v-'+id); if(el) el.textContent=Math.round(+val(id))+'%'; });
  const popAlvo=selected[3];
  const covA=+val('cov-atual')/100, covM=+val('cov-meta')/100, ades=+val('adesao')/100;
  const prev=+val('prev')/100, pLes=+val('lesao')/100, pProg=+val('prog')/100;
  const preco=+val('preco')||0, prazo=+val('prazo')||12;

  const adicionais = popAlvo*Math.max(0,covM-covA);
  const testes = adicionais*ades;
  const hpvPos = testes*prev;
  const lesoes = hpvPos*pLes;
  const lesoesCitoPerde = lesoes*(SENS_DNA-SENS_CITO);
  const casosEvit = lesoes*pProg;
  const mortesEvit = casosEvit*LETALIDADE_EVIT;

  const custoPrograma = testes*preco;
  const custoEvitado = casosEvit*(CUSTO_TARDIO-CUSTO_PRECOCE);
  const valorSocial = mortesEvit*VALOR_MORTE;
  const roiSoc = custoPrograma>0 ? (custoEvitado+valorSocial-custoPrograma)/custoPrograma : 0;
  const custoPorMorte = mortesEvit>0 ? custoPrograma/mortesEvit : 0;
  const custoPorCaso = casosEvit>0 ? custoPrograma/casosEvit : 0;
  const testesMes = prazo>0 ? testes/prazo : 0;

  const steps = [
    ['População-alvo (25–64 anos)', popAlvo, popAlvo, 'mulheres do município na faixa do rastreio (IBGE 2022)'],
    ['Mulheres convocadas (busca ativa)', adicionais, popAlvo, 'ainda sem rastreio — para subir de '+(covA*100).toFixed(0)+'% a '+(covM*100).toFixed(0)+'% de cobertura'],
    ['Mulheres atendidas (testadas)', testes, popAlvo, 'das convocadas que aderem ('+(ades*100).toFixed(0)+'%) — estas realizam a autocoleta'],
    ['HPV de alto risco positivos', hpvPos, popAlvo, 'das testadas ('+(prev*100).toFixed(0)+'%) — seguem p/ colposcopia'],
    ['Lesões NIC2+ detectadas', lesoes, popAlvo, 'das HPV+ ('+(pLes*100).toFixed(0)+'%) — '+fmt(lesoesCitoPerde)+' que o Papanicolau perderia'],
    ['Casos de câncer evitados', casosEvit, popAlvo, 'por tratamento precoce da lesão'],
    ['Mortes potencialmente evitadas', mortesEvit, popAlvo, 'letalidade evitável do câncer invasivo'],
  ];
  // barra proporcional à etapa ANTERIOR (funil de conversão) — torna visíveis as etapas pequenas
  const base=[popAlvo,adicionais,testes,hpvPos,lesoes,casosEvit,mortesEvit];
  document.getElementById('funnel-box').innerHTML = steps.map((s,i)=>{
    const prev = i===0 ? s[1] : base[i-1];
    const pct = prev>0 ? Math.max(2,Math.min(100,(s[1]/prev)*100)) : 2;
    const conv = (i>0 && prev>0) ? ' · '+((s[1]/prev)*100).toFixed(s[1]/prev<0.1?1:0)+'% da etapa anterior' : '';
    return `<div class="step"><div class="lbl">${s[0]}<span class="sub">${s[3]}${conv}</span></div><div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div><div class="val">${fmt(s[1])}</div></div>`;}).join('');
  document.getElementById('funnel-head').innerHTML =
    'Neste cenário, o programa <b>convoca '+fmt(adicionais)+'</b> mulheres ainda sem rastreio e <b>atende (testa) '+fmt(testes)+'</b> — em '+prazo+' '+(prazo==1?'mês':'meses')+' ('+fmt(Math.round(testesMes))+' testes/mês). '+
    'Dessas, ~<b>'+fmt(hpvPos)+'</b> dão HPV+ de alto risco e ~<b>'+fmt(lesoes)+'</b> têm lesão de alto grau a tratar.';
  const vinp=document.getElementById('in-valor-alvo'); if(vinp && document.activeElement!==vinp) vinp.value=custoPrograma.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
  document.getElementById('roi-custo').textContent=fmtMoney(custoPrograma);
  document.getElementById('roi-cpm').textContent = mortesEvit>0?fmtMoney(custoPorMorte):'—';
  document.getElementById('roi-soc').textContent = (roiSoc>=0?'+':'')+fmtPct(roiSoc);
  const alvoNome = selected[4] ? selected[0] : selected[0];
  document.getElementById('resumo').innerHTML =
    `Para levar <b>${alvoNome}</b> de ${(covA*100).toFixed(0)}% a ${(covM*100).toFixed(0)}% de cobertura, seriam <b>${fmt(testes)}</b> testes DNA-HPV (<b>${fmtMoney(custoPrograma)}</b>), `+
    `detectando ~<b>${fmt(lesoes)}</b> lesões de alto grau — sendo <b>${fmt(lesoesCitoPerde)}</b> que o Papanicolau perderia. `+
    `Estimativa: <b>${fmt(casosEvit)}</b> cânceres e <b>${fmt(mortesEvit)}</b> mortes evitados; retorno socioeconômico de <b>${(roiSoc*100).toFixed(0)}%</b>. `+
    `Frente ao Papanicolau (não somado a ele), o DNA-HPV é custo-efetivo e reduz gastos no longo prazo (CONITEC: −30%).`;

  lastCalc = {muni:selected, steps, fonteLabel:fonteSel().label, instr:instrSel(), ades, prev, pLes, pProg, covA, covM, hpvPos, adicionais,
    custoPrograma, custoEvitado, valorSocial, roiSoc, custoPorMorte, custoPorCaso,
    lesoes, lesoesCitoPerde, testes, casosEvit, mortesEvit, preco, prazo, testesMes, isUF:selected[4],
    premissas:[['Cobertura atual',(covA*100).toFixed(0)+'%'],['Cobertura-meta',(covM*100).toFixed(0)+'%'],
      ['Adesão ao convite',(ades*100).toFixed(0)+'%'],['Prevalência HPV alto risco',(prev*100).toFixed(0)+'%'],
      ['Lesões NIC2+ entre HPV+',(pLes*100).toFixed(0)+'%'],['Progressão a câncer evitada',(pProg*100).toFixed(0)+'%'],
      ['Preço unitário do kit','R$ '+preco.toLocaleString('pt-BR')],['Prazo de execução',prazo+' meses']]};
  renderPate();   // depois de lastCalc: a reconciliação SUS 360 usa o custo deste cenário
  atualizarBotoesRota();
}

/* ---------- rankings ---------- */
let rankMode='mun';
let rankExpanded=false;
const RANK_TOP=10, RANK_MAX_MUN=200;
function setRank(m){
  rankMode=m;
  document.getElementById('rtab-mun').classList.toggle('on',m==='mun');
  document.getElementById('rtab-uf').classList.toggle('on',m==='uf');
  renderRank();
}
function toggleRank(){
  rankExpanded=!rankExpanded;
  document.getElementById('rankWrap').classList.toggle('scroll',rankExpanded);
  document.getElementById('btnRankMore').textContent = rankExpanded?'Ver menos ▴':'Ver ranking completo ▾';
  renderRank();
}
function renderRank(){
  const head=document.getElementById('rankHead'), body=document.getElementById('rankBody');
  if(rankMode==='mun'){
    const total=MUNICIPIOS.length, n=rankExpanded?RANK_MAX_MUN:RANK_TOP;
    head.innerHTML='<tr><th>#</th><th>Município</th><th>UF</th><th>Mulheres 25–64</th><th>População</th><th>% alvo</th></tr>';
    body.innerHTML=MUNICIPIOS.slice(0,n).map((m,i)=>
      `<tr onclick="pick('${m[0].replace(/'/g,"\\'")}','${m[1]}');abrir(3)"><td>${i+1}</td><td>${m[0]}</td><td>${m[1]}</td><td>${m[3].toLocaleString('pt-BR')}</td><td>${m[2].toLocaleString('pt-BR')}</td><td>${(100*m[3]/m[2]).toFixed(1)}%</td></tr>`).join('');
    document.getElementById('rankCount').textContent = rankExpanded
      ? 'Mostrando os '+Math.min(n,total)+' maiores de '+total.toLocaleString('pt-BR')+' municípios — use a busca acima para os demais.'
      : 'Mostrando o Top 10 de '+total.toLocaleString('pt-BR')+' municípios.';
  } else {
    const ufs=Object.entries(UF_STATS).sort((a,b)=>b[1].m-a[1].m);
    const n=rankExpanded?ufs.length:RANK_TOP;
    head.innerHTML='<tr><th>#</th><th>Estado</th><th>UF</th><th>Mulheres 25–64</th><th>População</th><th>Municípios</th></tr>';
    body.innerHTML=ufs.slice(0,n).map(([uf,s],i)=>
      `<tr onclick="pickUF('${uf}');abrir(3)"><td>${i+1}</td><td>${s.nome}</td><td>${uf}</td><td>${s.m.toLocaleString('pt-BR')}</td><td>${s.pop.toLocaleString('pt-BR')}</td><td>${s.n}</td></tr>`).join('');
    document.getElementById('rankCount').textContent = rankExpanded
      ? 'Mostrando todos os 27 estados.' : 'Mostrando o Top 10 de 27 estados.';
    document.getElementById('btnRankMore').style.display = 'inline-block';
  }
}
function initUF(){
  const ufs=Object.entries(UF_STATS).sort((a,b)=>a[1].nome.localeCompare(b[1].nome));
  document.getElementById('seluf').innerHTML='<option value="">Selecione o estado…</option>'+
    ufs.map(([uf,s])=>`<option value="${uf}">${s.nome} (${uf}) — ${s.m.toLocaleString('pt-BR')} mulheres 25-64</option>`).join('');
}

/* ================= PROPOSTA PDF (hi-tech) ================= */
const MESES=['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'];
const dataExtenso = d => d.getDate()+' de '+MESES[d.getMonth()]+' de '+d.getFullYear();
const C_PINK=[230,0,126], C_WINE=[124,29,79], C_DARK=[36,12,26], C_GREEN=[18,169,122], C_GREY=[120,110,116];

const valueLabelPlugin={id:'vl',afterDatasetsDraw(c){const{ctx}=c;c.data.datasets.forEach((ds,di)=>{c.getDatasetMeta(di).data.forEach((bar,i)=>{ctx.save();ctx.fillStyle='#2A1622';ctx.font='bold 13px Arial';ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(Math.round(ds.data[i]).toLocaleString('pt-BR'),bar.x+8,bar.y);ctx.restore();});});}};
function chartImg(config,w,h){
  const cv=document.createElement('canvas');cv.width=w;cv.height=h;
  config.plugins=(config.plugins||[]).concat([valueLabelPlugin]);
  const ch=new Chart(cv.getContext('2d'),config);const img=ch.toBase64Image('image/png',1.0);ch.destroy();return img;
}
/* estilo limpo: sem grid vertical pesado, fonte maior, barras arredondadas */
const baseOpts = (titulo)=>({responsive:false,animation:false,indexAxis:'y',
  layout:{padding:{right:90,left:4,top:4,bottom:4}},
  plugins:{legend:{display:false},title:{display:true,text:titulo,font:{size:14,weight:'bold'},color:'#7C1D4F',padding:{bottom:12}}},
  scales:{x:{display:false,grid:{display:false}},y:{grid:{display:false},border:{display:false},ticks:{font:{size:12},color:'#2A1622'}}}});

function imgRegional(m){
  const uf=m[1],s=UF_STATS[uf],cap=s.capital,labels=[],data=[],bg=[];
  if(m[4]){ // estado: compara com capital e Brasil
    labels.push(s.nome);data.push(m[3]);bg.push('#E6007E');
    if(cap){labels.push('Capital ('+cap[0]+')');data.push(cap[3]);bg.push('#7C1D4F');}
  } else {
    labels.push(m[0]);data.push(m[3]);bg.push('#E6007E');
    if(cap&&cap[0]!==m[0]){labels.push('Capital ('+cap[0]+')');data.push(cap[3]);bg.push('#B4126A');}
    labels.push('Total '+uf);data.push(s.m);bg.push('#7C1D4F');
  }
  return chartImg({type:'bar',data:{labels,datasets:[{data,backgroundColor:bg,borderRadius:6,barThickness:26}]},
    options:baseOpts('Mulheres 25–64 anos — comparação regional (Censo 2022)')},760,210);
}
function imgFunil(steps){
  const a=steps.slice(0,3),d=steps.slice(3);
  const i1=chartImg({type:'bar',data:{labels:a.map(s=>s[0]),datasets:[{data:a.map(s=>Math.round(s[1])),backgroundColor:['#E6007E','#F0398B','#FF4DA6'],borderRadius:6,barThickness:26}]},
    options:baseOpts('Alcance do programa')},760,190);
  const i2=chartImg({type:'bar',data:{labels:d.map(s=>s[0]),datasets:[{data:d.map(s=>Math.round(s[1])),backgroundColor:['#7C1D4F','#9B2A63','#B4126A','#C81E5B'],borderRadius:6,barThickness:24}]},
    options:baseOpts('Resultados de detecção estimados')},760,230);
  return [i1,i2];
}
function imgCusto(c){
  return chartImg({type:'bar',
    data:{labels:['PinkPapa (kit)','Papanicolau','Tratamento/ano'],datasets:[{data:[c.preco,14.37,10000],backgroundColor:['#E6007E','#C9B2BF','#C81E5B'],borderRadius:6,barThickness:26}]},
    options:Object.assign(baseOpts('Custo unitário comparado (R$, escala log)'),{scales:{x:{type:'logarithmic',display:false,grid:{display:false}},y:{grid:{display:false},border:{display:false},ticks:{font:{size:12},color:'#2A1622'}}}})},760,180);
}

function pnsb(c){
  const m=c.muni,uf=m[1],passo=l=>c.steps.find(s=>s[0]===l)[1];
  const alvo = m[4] ? m[0] : m[0]+'/'+uf;
  const covA=c.premissas[0][1], covM=c.premissas[1][1];
  const ente = m[4] ? 'o estado' : 'o município';
  return {
    problema:'O câncer de colo do útero é o 3º mais frequente entre as brasileiras e a 1ª causa de morte por câncer na América Latina: 17.010 casos novos e mais de 7.100 óbitos por ano no Brasil (INCA; Observatório de Oncologia) — uma mulher a cada 90 minutos. É causado pelo HPV e quase 100% evitável com rastreio de qualidade, mas a citologia (Papanicolau) detecta apenas 55–70% das lesões de alto grau e a cobertura está em queda. Em '+alvo+', a cobertura estimada hoje é de '+covA+', para uma população-alvo de '+m[3].toLocaleString('pt-BR')+' mulheres de 25 a 64 anos (Censo 2022, IBGE).',
    necessidade:'Para levar '+alvo+' à cobertura-meta de '+covM+' (patamar da meta de 70% da OMS), é preciso incluir mais '+fmt(passo('Mulheres convocadas (busca ativa)'))+' mulheres no rastreio — cerca de '+fmt(c.testes)+' testes, considerando a adesão estimada, executados em '+c.prazo+' meses ('+fmt(c.testesMes)+' testes/mês). O rastreio oportunístico atual e a espera de 4 a 6 meses por consulta deixam muitas mulheres sem qualquer exame.',
    solucao:'O PinkPapa é um autoteste de DNA-HPV homologado pela ANVISA, correspondente ao procedimento SIGTAP 0202100251 (Exame molecular de detecção de HPV), incorporado ao SUS pela Portaria SECTICS/MS nº 3/2024 e custeável por '+(c.fonteLabel||'Média e Alta Complexidade (MAC)')+'. A autocoleta é feita pela própria mulher em UBS, UPA, centros comunitários ou hospitais — sem espéculo, sem mesa ginecológica, sem constrangimento, com aceitação próxima de 100%. Detecta 28 tipos de HPV (19 de alto risco), com sensibilidade de 90–95% (contra 55–70% do Papanicolau), antecipa o diagnóstico em até 10 anos e permite espaçar o rastreio para 5 anos após resultado negativo, com acompanhamento por inteligência artificial por 5 anos.',
    beneficio:'Com as premissas simuladas, o investimento é de '+fmtMoney(c.custoPrograma)+', detectando ~'+fmt(c.lesoes)+' lesões de alto grau (das quais ~'+fmt(c.lesoesCitoPerde)+' que o Papanicolau perderia), evitando '+fmt(c.casosEvit)+' casos de câncer e '+fmt(c.mortesEvit)+' mortes — a um custo de '+fmtMoney(c.custoPorMorte)+' por morte evitada e retorno socioeconômico de '+(c.roiSoc*100).toFixed(0)+'%. Substituindo (e não somando-se a) o Papanicolau, o DNA-HPV é custo-efetivo e reduz o gasto do SUS no longo prazo (estimativa CONITEC: -30%), alinhando '+ente+' às metas 90-70-90 da OMS e ao indicador de cobertura do Previne Brasil.'
  };
}

function montarPDF(){
  if(!lastCalc){alert('Selecione um município ou estado primeiro.');return null;}
  const c=lastCalc,m=c.muni,uf=m[1],{jsPDF}=window.jspdf;
  const doc=new jsPDF({unit:'pt',format:'a4'});
  const W=doc.internal.pageSize.getWidth(),H=doc.internal.pageSize.getHeight(),M=44;
  const isUF=m[4];
  const alvo = isUF ? m[0] : m[0]+'/'+uf;
  const orgao = isUF ? UF_STATS[uf].orgao : ('Secretaria Municipal de Saúde de '+m[0]+'/'+uf);
  const dest=document.getElementById('in-dest-nome').value.trim();
  const pNome=document.getElementById('in-prop-nome').value.trim()||'PinkPapa · PinkLab';
  const pMail=document.getElementById('in-prop-email').value.trim();
  const pTel =document.getElementById('in-prop-tel').value.trim();
  const hoje=new Date();
  const ref='PINKPAPA-'+uf+'-'+(isUF?'UF':'MUN')+'-'+hoje.getFullYear()+String(hoje.getMonth()+1).padStart(2,'0')+String(hoje.getDate()).padStart(2,'0');
  let y=0;

  /* gradiente simulado por faixas finas (jsPDF não tem gradiente nativo) */
  function gradiente(x,yy,w,h,c1,c2){
    const N=90;
    for(let i=0;i<N;i++){
      const t=i/(N-1);
      doc.setFillColor(Math.round(c1[0]+(c2[0]-c1[0])*t),Math.round(c1[1]+(c2[1]-c1[1])*t),Math.round(c1[2]+(c2[2]-c1[2])*t));
      doc.rect(x, yy+(h/N)*i, w, h/N+0.7, 'F');
    }
  }
  function barraTopo(){
    doc.setFillColor(...C_PINK);doc.rect(0,0,W,24,'F');
    doc.setTextColor(255);doc.setFont('helvetica','bold');doc.setFontSize(10);doc.text((pNome||'PROPONENTE').toUpperCase(),M,16);
    doc.setFont('helvetica','normal');doc.setFontSize(7.5);
    doc.text('Rastreio de câncer de colo do útero por DNA-HPV (autocoleta)',W-M,16,{align:'right'});
  }
  function header(sub){
    barraTopo();
    doc.setTextColor(...C_WINE);doc.setFont('helvetica','bold');doc.setFontSize(13);doc.text('Proposta — '+alvo,M,46);
    doc.setTextColor(...C_GREY);doc.setFont('helvetica','normal');doc.setFontSize(9);doc.text(sub+' · Ref. '+ref,M,60);
    doc.setDrawColor(240,215,230);doc.line(M,68,W-M,68);
    return 84;
  }
  /* rodapé em 2 linhas — numa linha só, contato e fontes se sobrepõem */
  function rodape(){
    const p=doc.internal.getNumberOfPages();
    for(let i=2;i<=p;i++){doc.setPage(i);
      doc.setDrawColor(240,215,230);doc.line(M,H-40,W-M,H-40);
      doc.setFontSize(7.3);doc.setTextColor(150);
      doc.text(pNome+(pMail?' · '+pMail:'')+(pTel?' · '+pTel:''),M,H-28);
      doc.text(i+'/'+p,W-M,H-28,{align:'right'});
      doc.setFontSize(6.8);doc.setTextColor(170);
      doc.text('Fontes: IBGE (Censo 2022), INCA, Obs. de Oncologia, CONITEC/MS, OMS · Apoio à decisão; não substitui diagnóstico médico',M,H-17);}
  }
  /* KPI card */
  function kpi(x,yy,w,h,valor,rot,cor){
    doc.setFillColor(255,255,255);doc.setDrawColor(240,215,230);doc.roundedRect(x,yy,w,h,6,6,'FD');
    doc.setFillColor(...cor);doc.rect(x,yy,3.5,h,'F');
    doc.setTextColor(...cor);doc.setFont('helvetica','bold');doc.setFontSize(15);doc.text(valor,x+12,yy+22);
    doc.setTextColor(...C_GREY);doc.setFont('helvetica','normal');doc.setFontSize(7.8);
    doc.text(doc.splitTextToSize(rot,w-18),x+12,yy+34);
  }

  /* ======== PÁGINA 1 — CAPA hi-tech ======== */
  gradiente(0,0,W,H,[243,110,170],[150,28,96]);
  // grid decorativo
  doc.setDrawColor(255,255,255);doc.setLineWidth(0.3);
  for(let i=1;i<7;i++){doc.setGState(new doc.GState({opacity:0.07}));doc.line(0,H*i/7,W,H*i/7);doc.line(W*i/7,0,W*i/7,H);}
  doc.setGState(new doc.GState({opacity:1}));doc.setLineWidth(1);

  doc.setTextColor(255);doc.setFont('helvetica','bold');doc.setFontSize(11);
  doc.text((pNome||'PROPONENTE').toUpperCase(),M,64);
  doc.setFont('helvetica','normal');doc.setFontSize(8.5);doc.setTextColor(255,220,238);
  doc.text('Executante técnico — rastreio por DNA-HPV com autocoleta',M,78);

  // título: posiciona o subtítulo DEPOIS das linhas reais do título (senão sobrepõe)
  doc.setTextColor(255);doc.setFont('helvetica','bold');doc.setFontSize(30);
  const tLines=doc.splitTextToSize('PROPOSTA TÉCNICA E COMERCIAL',W-2*M-30);
  let ty=172;
  doc.text(tLines,M,ty); ty += tLines.length*33;
  doc.setFont('helvetica','normal');doc.setFontSize(12.5);doc.setTextColor(255,210,234);
  const sLines=doc.splitTextToSize('Programa de rastreio de câncer de colo do útero por teste de DNA-HPV com autocoleta',W-2*M-30);
  doc.text(sLines,M,ty+6);

  // faixa do alvo
  doc.setFillColor(255,255,255);doc.setGState(new doc.GState({opacity:0.12}));
  doc.roundedRect(M,258,W-2*M,62,8,8,'F');doc.setGState(new doc.GState({opacity:1}));
  doc.setTextColor(255,190,225);doc.setFont('helvetica','bold');doc.setFontSize(8);
  doc.text(isUF?'ENTE FEDERATIVO (ESTADUAL)':'MUNICÍPIO',M+16,278);
  doc.setTextColor(255);doc.setFontSize(20);doc.text(alvo,M+16,302);
  doc.setFont('helvetica','normal');doc.setFontSize(9);doc.setTextColor(255,210,234);
  doc.text(fmt(m[3])+' mulheres de 25 a 64 anos (população-alvo)',W-M-16,302,{align:'right'});

  // VALOR DO PROJETO — destaque grande
  doc.setFillColor(255,255,255);
  doc.roundedRect(M,340,W-2*M,104,10,10,'F');
  doc.setFillColor(...C_PINK);doc.rect(M,340,6,104,'F');
  doc.setTextColor(...C_GREY);doc.setFont('helvetica','bold');doc.setFontSize(8);
  doc.text('VALOR TOTAL DO PROJETO (AQUISIÇÃO DOS TESTES)',M+20,364);
  doc.setTextColor(...C_PINK);doc.setFont('helvetica','bold');doc.setFontSize(30);
  doc.text(fmtMoney(c.custoPrograma),M+20,398);
  doc.setTextColor(...C_WINE);doc.setFont('helvetica','normal');doc.setFontSize(9.5);
  doc.text(fmt(c.testes)+' testes × '+fmtMoney(c.preco)+' por kit  ·  execução em '+c.prazo+' meses ('+fmt(c.testesMes)+'/mês)',M+20,420);
  doc.setFontSize(8);doc.setTextColor(...C_GREY);
  doc.text('Fonte de recurso: '+(c.fonteLabel||'Média e Alta Complexidade (MAC)')+' · procedimento SIGTAP 0202100251',M+20,436);

  // KPIs da capa
  const kw=(W-2*M-24)/3;
  doc.setGState(new doc.GState({opacity:1}));
  kpi(M,468,kw,58,fmt(c.casosEvit),'casos de câncer potencialmente evitados',C_PINK);
  kpi(M+kw+12,468,kw,58,fmt(c.mortesEvit),'mortes potencialmente evitadas',C_WINE);
  kpi(M+2*(kw+12),468,kw,58,(c.roiSoc*100).toFixed(0)+'%','retorno socioeconômico estimado',C_GREEN);

  // destinatário + proponente
  doc.setDrawColor(255,255,255);doc.setGState(new doc.GState({opacity:0.25}));
  doc.line(M,566,W-M,566);doc.setGState(new doc.GState({opacity:1}));
  doc.setTextColor(255,190,225);doc.setFont('helvetica','bold');doc.setFontSize(8);
  doc.text('DESTINATÁRIO',M,588);
  doc.text('PROPONENTE',W/2+10,588);
  doc.setTextColor(255);doc.setFont('helvetica','normal');doc.setFontSize(10);
  doc.text(doc.splitTextToSize(dest||orgao,W/2-M-20),M,604);
  doc.text(doc.splitTextToSize(orgao,W/2-M-20),M,dest?620:620);
  doc.setFont('helvetica','bold');doc.text(doc.splitTextToSize(pNome,W/2-M-20),W/2+10,604);
  doc.setFont('helvetica','normal');doc.setFontSize(9);
  doc.text('Executante técnico',W/2+10,618);
  let py=631; if(pMail){doc.text(pMail,W/2+10,py);py+=13;} if(pTel){doc.text(pTel,W/2+10,py);}

  doc.setFontSize(8);doc.setTextColor(255,190,225);
  doc.text('Ref. '+ref,M,H-56);
  doc.text('Brasília/DF, '+dataExtenso(hoje),W-M,H-56,{align:'right'});
  doc.setFontSize(7.5);doc.setTextColor(255,170,215);
  doc.text('Documento gerado com dados oficiais: IBGE (Censo 2022), INCA, Observatório de Oncologia, CONITEC/MS, OMS.',M,H-38);

  /* ======== PÁGINA 2 — PNSB ======== */
  doc.addPage();y=header('Problema · Necessidade · Solução · Benefício (PNSB)');
  const P=pnsb(c);
  function bloco(tit,txt,cor){
    const lines=doc.splitTextToSize(txt,W-2*M-22);
    const h=lines.length*11.5+30;
    doc.setFillColor(252,244,248);doc.roundedRect(M,y,W-2*M,h,6,6,'F');
    doc.setFillColor(...cor);doc.rect(M,y,4,h,'F');
    doc.setTextColor(...cor);doc.setFont('helvetica','bold');doc.setFontSize(10.5);doc.text(tit,M+14,y+18);
    doc.setTextColor(55,42,50);doc.setFont('helvetica','normal');doc.setFontSize(9.2);
    doc.text(lines,M+14,y+32);
    y+=h+12;
  }
  bloco('PROBLEMA',P.problema,[200,30,91]);
  bloco('NECESSIDADE',P.necessidade,C_WINE);
  bloco('SOLUÇÃO',P.solucao,C_PINK);
  bloco('BENEFÍCIO',P.beneficio,C_GREEN);

  /* ======== PÁGINA 3 — EXECUÇÃO (destaque) ======== */
  doc.addPage();y=header('Plano de execução');
  doc.setFillColor(...C_DARK);doc.roundedRect(M,y,W-2*M,52,8,8,'F');
  doc.setTextColor(255);doc.setFont('helvetica','bold');doc.setFontSize(13);
  doc.text('EXECUÇÃO DO PROGRAMA',M+16,y+22);
  doc.setFont('helvetica','normal');doc.setFontSize(9);doc.setTextColor(255,190,225);
  doc.text(fmt(c.testes)+' testes em '+c.prazo+' meses  ·  '+fmt(c.testesMes)+' testes/mês  ·  autocoleta em UBS, UPA, centros comunitários e hospitais',M+16,y+40);
  y+=68;

  doc.autoTable({startY:y,
    head:[['Fase','Atividades','Prazo','Responsável']],
    body:[
      ['1. Planejamento','Pactuação com a Secretaria, definição das unidades de coleta (UBS/UPA/centros comunitários), meta por unidade e cadastro no SISCAN (acesso: siscan.saude.gov.br/login.jsf).','Mês 1','Executante + Secretaria'],
      ['2. Capacitação','Treinamento das equipes da Atenção Primária (ACS/enfermagem) para orientar a autocoleta e registrar o procedimento SIGTAP 0202100251.','Mês 1–2','Executante + laboratório'],
      ['3. Convocação','Busca ativa das mulheres de 25 a 64 anos, priorizando as que nunca se rastrearam; campanha local e agendamento.','Mês 2 em diante','Secretaria + ACS'],
      ['4. Autocoleta','Entrega e retirada do coletor; a mulher realiza a autocoleta sem espéculo e sem constrangimento. Sem necessidade de mesa ginecológica.','Contínuo','Unidades de saúde'],
      ['5. Análise laboratorial','Processamento por PCR com genotipagem (28 tipos de HPV, 19 de alto risco) e emissão de laudo.','Contínuo','Laboratório'],
      ['6. Encaminhamento','Mulheres HPV+ de alto risco encaminhadas à colposcopia/tratamento da lesão precursora (CAF/EZT), fechando a linha de cuidado.','Contínuo','Secretaria'],
      ['7. Monitoramento por IA','Acompanhamento por inteligência artificial por até 5 anos, com painel de cobertura e indicadores (Previne Brasil / metas 90-70-90).','5 anos','Executante + laboratório'],
    ],
    theme:'grid',headStyles:{fillColor:C_PINK,fontSize:9},styles:{fontSize:8.4,cellPadding:5,lineColor:[240,215,230]},
    columnStyles:{0:{cellWidth:80,fontStyle:'bold',textColor:C_WINE},2:{cellWidth:66},3:{cellWidth:88}},margin:{left:M,right:M},
    didDrawCell:function(d){ if(d.section==='body'&&d.row.index===0&&d.column.index===1){ doc.link(d.cell.x,d.cell.y,d.cell.width,d.cell.height,{url:'https://siscan.saude.gov.br/login.jsf'}); } }});
  y=doc.lastAutoTable.finalY+16;

  /* ---- Cronograma (Gantt vetorial), escalado ao prazo de execução ---- */
  (function(){
    const gx=M, gw=W-2*M, Lp=150, tl=gx+Lp, tw=gw-Lp;
    const nm=Math.max(1,Math.min(60,c.prazo)), colW=tw/nm;
    const mx=(mth)=>tl+colW*mth;
    doc.setTextColor(...C_WINE);doc.setFont('helvetica','bold');doc.setFontSize(10.5);
    doc.text('Cronograma de execução',gx,y);
    doc.setFont('helvetica','normal');doc.setFontSize(7);doc.setTextColor(...C_GREY);
    doc.text('barras ajustadas a '+nm+' meses',W-M,y,{align:'right'});
    let hy=y+12;
    const step = nm<=12?1:(nm<=24?2:4);
    for(let i=1;i<=nm;i++){ if(i===1||i%step===0||i===nm){ doc.text('M'+i, mx(i-0.5), hy, {align:'center'}); } }
    const top=hy+6, rowH=16, barH=10;
    doc.setDrawColor(240,215,230);doc.setLineWidth(0.4);
    for(let i=0;i<=nm;i++){ doc.line(mx(i),top,mx(i),top+7*rowH); }
    const cap=v=>Math.min(nm,v);
    const fases=[
      ['1 · Planejamento',C_PINK,0,cap(1),false],
      ['2 · Capacitação',[240,57,139],0,cap(2),false],
      ['3 · Convocação',[180,18,106],cap(1),nm,false],
      ['4 · Autocoleta',[155,42,99],cap(1),nm,false],
      ['5 · Análise laboratorial',C_WINE,cap(2),nm,false],
      ['6 · Encaminhamento',[200,30,91],cap(2),nm,false],
      ['7 · Monitoramento IA',C_GREEN,0,nm,true],
    ];
    fases.forEach((f,i)=>{
      const ry=top+i*rowH;
      doc.setTextColor(42,22,34);doc.setFont('helvetica','bold');doc.setFontSize(7.6);
      doc.text(f[0],gx,ry+rowH/2+2.5);
      const bx=mx(f[2]), bw=Math.max(3,mx(f[3])-mx(f[2])), by=ry+(rowH-barH)/2;
      doc.setFillColor(...f[1]);doc.roundedRect(bx,by,bw,barH,2,2,'F');
      if(f[4]){ const ax=mx(f[3]); doc.triangle(ax,by,ax,by+barH,ax+7,by+barH/2,'F'); }
    });
    // marco de início (linha tracejada)
    doc.setDrawColor(42,22,34);doc.setLineWidth(0.8);
    for(let dy=top; dy<top+7*rowH; dy+=4){ doc.line(tl,dy,tl,Math.min(dy+2,top+7*rowH)); }
    doc.setLineWidth(1);
    doc.setFont('helvetica','italic');doc.setFontSize(6.8);doc.setTextColor(...C_GREEN);
    doc.text('» o monitoramento por IA segue por 5 anos',W-M,top+7*rowH+9,{align:'right'});
    y=top+7*rowH+18;
  })();

  doc.setFillColor(252,244,248);doc.roundedRect(M,y,W-2*M,58,6,6,'F');
  doc.setFillColor(...C_GREEN);doc.rect(M,y,4,58,'F');
  doc.setTextColor(...C_GREEN);doc.setFont('helvetica','bold');doc.setFontSize(10);
  doc.text('ONDE A AUTOCOLETA ACONTECE',M+14,y+18);
  doc.setTextColor(55,42,50);doc.setFont('helvetica','normal');doc.setFontSize(9);
  doc.text(doc.splitTextToSize('UBS · UPA · Centros comunitários · Hospitais · Ações itinerantes. O PinkPapa elimina a necessidade de mesa ginecológica, espéculo, foco de luz e da presença de vários profissionais — o que permite escalar o rastreio sem ampliar a estrutura física instalada.',W-2*M-24),M+14,y+34);

  /* ======== PÁGINA 4 — DIMENSIONAMENTO / GRÁFICOS ======== */
  doc.addPage();y=header('Dimensionamento e alcance');
  const wImg=W-2*M;
  doc.addImage(imgRegional(m),'PNG',M,y,wImg,wImg*210/760);y+=wImg*210/760+6;
  const[i1,i2]=imgFunil(c.steps);
  doc.addImage(i1,'PNG',M,y,wImg,wImg*190/760);y+=wImg*190/760+6;
  doc.addImage(i2,'PNG',M,y,wImg,wImg*230/760);y+=wImg*230/760+6;
  doc.addImage(imgCusto(c),'PNG',M,y,wImg,wImg*180/760);

  /* ======== PÁGINA 5 — INVESTIMENTO ======== */
  doc.addPage();y=header('Investimento e custo-benefício');
  // caixa do valor
  gradiente(M,y,W-2*M,76,[243,110,170],[150,28,96]);
  doc.setTextColor(255,190,225);doc.setFont('helvetica','bold');doc.setFontSize(8);
  doc.text('VALOR TOTAL DA CONTRATAÇÃO / AQUISIÇÃO',M+16,y+22);
  doc.setTextColor(255);doc.setFontSize(26);doc.text(fmtMoney(c.custoPrograma),M+16,y+52);
  doc.setFont('helvetica','normal');doc.setFontSize(9);doc.setTextColor(255,215,238);
  doc.text(fmt(c.testes)+' kits × '+fmtMoney(c.preco),W-M-16,y+38,{align:'right'});
  doc.text('Execução: '+c.prazo+' meses',W-M-16,y+54,{align:'right'});
  y+=92;

  doc.autoTable({startY:y,head:[['Composição do investimento','Quantidade','Unitário','Total']],
    body:[
      ['Kit PinkPapa (autoteste DNA-HPV) — SIGTAP 0202100251',fmt(c.testes),fmtMoney(c.preco),fmtMoney(c.custoPrograma)],
      ['Capacitação das equipes, logística e monitoramento por IA (5 anos)','—','incluso','incluso'],
    ],theme:'grid',headStyles:{fillColor:C_PINK,fontSize:9},styles:{fontSize:8.6,cellPadding:5,lineColor:[240,215,230]},
    columnStyles:{1:{halign:'right'},2:{halign:'right'},3:{halign:'right',fontStyle:'bold',textColor:C_PINK}},margin:{left:M,right:M}});
  y=doc.lastAutoTable.finalY+12;

  doc.autoTable({startY:y,head:[['Retorno estimado para o SUS','Valor']],
    body:[
      ['Custo de tratamento evitado',fmtMoney(c.custoEvitado)],
      ['Custo por câncer evitado',c.custoPorCaso>0?fmtMoney(c.custoPorCaso):'—'],
      ['Custo por morte evitada',c.custoPorMorte>0?fmtMoney(c.custoPorMorte):'—'],
      ['Valor social (mortes evitadas)',fmtMoney(c.valorSocial)],
      ['Retorno socioeconômico',(c.roiSoc*100).toFixed(0)+'%'],
      ['Comparativo — Papanicolau (SIGTAP)','R$ 14,37 / exame (sensibilidade 55–70%)'],
      ['Comparativo — tratamento oncológico','R$ 10.000 / paciente / ano'],
      ['Projeção CONITEC','-30% de custo no longo prazo (substituindo a citologia)'],
    ],theme:'grid',headStyles:{fillColor:C_GREEN,fontSize:9},styles:{fontSize:8.6,cellPadding:5,lineColor:[240,215,230]},
    columnStyles:{1:{halign:'right'}},margin:{left:M,right:M}});
  y=doc.lastAutoTable.finalY+12;

  doc.autoTable({startY:y,head:[['Premissas utilizadas','Valor']],body:c.premissas,
    theme:'grid',headStyles:{fillColor:C_WINE,fontSize:9},styles:{fontSize:8.4,cellPadding:4,lineColor:[240,215,230]},
    columnStyles:{1:{halign:'right'}},margin:{left:M,right:M}});

  const _r=reconFrom(c);
  if(_r){
    const sit=_r.semSaldo?'Sem saldo a comprovar — orçar por MAC/emenda (enquadrável no Mutirão das Mulheres)'
      :_r.saldoLimita?'Saldo é o teto — ação de ~'+fmt(_r.acaoTestadas)+' mulheres ('+(_r.covA*100).toFixed(0)+'%→~'+(_r.covB*100).toFixed(0)+'%); complemento p/ '+(_r.covM*100).toFixed(0)+'%: '+fmtMoney(_r.falta)
      :'Demanda é o teto — saldo cobre a meta de '+(_r.covM*100).toFixed(0)+'% com folga de '+fmtMoney(_r.folga)+' (seguimento/próx. ciclo)';
    doc.autoTable({startY:doc.lastAutoTable.finalY+12,head:[['Viabilidade orçamentária — SUS 360 (PATE)','Valor']],
      body:[
        ['Saldo a comprovar (recurso já antecipado ao fundo)',fmtMoney(_r.envelope)],
        ['Custo por mulher rastreada',fmtMoney(_r.custoTestada)+' / teste · '+fmtMoney(_r.custoConvocada)+' / convocada'],
        ['Ação que cabe no saldo',_r.semSaldo?'—':fmt(_r.acaoTestadas)+' mulheres · +'+_r.ptsAcao.toFixed(0)+' pts de cobertura'],
        ...(_r.saldoEmendas>0?[['Emendas parlamentares no saldo',fmtMoney(_r.saldoEmendas)]]:[]),
        ['Dimensionamento pela fonte',sit],
      ],theme:'grid',headStyles:{fillColor:C_WINE,fontSize:9},styles:{fontSize:8.4,cellPadding:4,lineColor:[240,215,230]},
      columnStyles:{1:{halign:'right'}},margin:{left:M,right:M}});
    if(_r.saldoEmendas>0){ y=doc.lastAutoTable.finalY+10; doc.setFontSize(8);doc.setTextColor(120);
      doc.text('Emendas no saldo — consultar nº, autor e andamento (Portal da Transparência, gestor na Busca Livre):',M,y);
      doc.setTextColor(0,0,255); doc.textWithLink(_r.emendaURL,M,y+11,{url:_r.emendaURL}); doc.setTextColor(60); }
  }
  y=doc.lastAutoTable.finalY+30;

  if(y>H-120) { doc.addPage(); y=header('Aceite'); y+=10; }
  doc.setDrawColor(190,170,182);
  doc.line(M,y+26,M+210,y+26);doc.line(W-M-210,y+26,W-M,y+26);
  doc.setFontSize(9);doc.setTextColor(60);
  doc.setFont('helvetica','bold');doc.text(pNome,M,y+40);
  doc.setFont('helvetica','normal');doc.setFontSize(8);doc.setTextColor(120);
  doc.text('Executante técnico'+(pTel?' · '+pTel:''),M,y+52);
  doc.setFont('helvetica','bold');doc.setFontSize(9);doc.setTextColor(60);
  doc.text(doc.splitTextToSize(dest||orgao,210),W-M-210,y+40);
  doc.setFont('helvetica','normal');doc.setFontSize(8);doc.setTextColor(120);
  doc.text('Contratante',W-M-210,y+52);
  doc.setFontSize(8);doc.setTextColor(120);
  doc.text('Local e data: ____________________________________, '+dataExtenso(hoje),M,y+80);

  rodape();
  return {doc,ref,alvo};
}

function nomeArq(){ return 'Proposta_PinkPapa_'+(selected?selected[0].replace(/[^\w]/g,'_'):'')+'.pdf'; }
function renderPate(){
  const box=document.getElementById('pate-box'); if(!box||!selected) return;
  const isUF=selected[4];
  const key = isUF ? (PATE_UF[selected[1]]||'') : (selected[5]||'');
  const d = key ? PATE[key] : null;
  const ente = isUF ? 'o estado' : 'o município';
  if(!d){
    box.innerHTML='<div class="callout"><b>🏛️ Agora Tem Especialistas (PATE) — SUS 360:</b> '+selected[0]+' não aparece como gestor com recurso próprio de especializada nesta competência ('+PATE_COMP+'). A atenção especializada pode ser executada pela gestão estadual — nesse caso, o seguimento das HPV+ é pactuado na CIR/PPI.</div>';
    return;
  }
  const brl=v=>fmtMoney(v||0);
  const rep=d.repasses||0, prod=d.producao||0, saldo=d.saldo||0, pct=d.pctExecutado||0;
  const repAmb=d.repAmbulatorial||0, prodAmb=d.prodAmbulatorial||0, mm=d.mutiraoMulheres||0;
  let tag,cor;
  if(saldo>0 && pct<50){ tag='Alto potencial — recurso antecipado com execução baixa ('+pct.toFixed(0)+'%)'; cor='#C81E5B'; }
  else if(saldo>0){ tag='Potencial — ainda há recurso a comprovar com produção ('+pct.toFixed(0)+'% executado)'; cor='#B4126A'; }
  else { tag='Execução em dia — recurso antecipado já consumido'; cor='#12A97A'; }
  const linha=(r,v,hint)=>`<tr><td style="padding:4px 10px;border-top:1px solid #f6e6ef">${r}${hint?'<br><span style="color:#9A6A86;font-size:11px">'+hint+'</span>':''}</td><td style="padding:4px 10px;border-top:1px solid #f6e6ef;text-align:right;font-weight:700;color:var(--wine);white-space:nowrap">${v}</td></tr>`;
  // ---- Dimensionamento da ação pelo saldo SUS 360 (encaixe dinheiro × demanda) — fonte única: reconFrom ----
  const R = lastCalc ? reconFrom(lastCalc) : null;
  let dimTag,dimCor,dimTxt;
  if(!R){ dimTag=''; }
  else if(R.semSaldo){ dimCor='#B4126A'; dimTag='Sem saldo a comprovar nesta competência';
    dimTxt='O recurso antecipado já foi consumido (ou não há antecipação). Orce a ação por <b>MAC</b> (produção nova do rastreio) e/ou <b>emenda</b>; a produção pode ser enquadrada no <b>Mutirão das Mulheres</b>'+(R.mm>0?' (o gestor já tem valor nessa rubrica).':'.');
  } else if(R.saldoLimita){ dimCor='#C81E5B'; dimTag='A ação cabe em ~'+fmt(R.acaoTestadas)+' mulheres ('+(R.covA*100).toFixed(0)+'% → ~'+(R.covB*100).toFixed(0)+'%)';
    dimTxt='O saldo a comprovar (<b>'+fmtMoney(R.envelope)+'</b>) financia uma ação de <b>~'+fmt(R.acaoTestadas)+' mulheres rastreadas</b> (convocando ~'+fmt(R.acaoConvocadas)+'), elevando a cobertura de '+(R.covA*100).toFixed(0)+'% para <b>~'+(R.covB*100).toFixed(0)+'%</b> — a ação executável com o recurso já no fundo. Para a meta de '+(R.covM*100).toFixed(0)+'% o complemento de <b>'+fmtMoney(R.falta)+'</b> entra por <b>MAC</b>, <b>emenda</b> ou <b>Mutirão das Mulheres</b> nos próximos ciclos.';
  } else { dimCor='#12A97A'; dimTag='O saldo cobre a meta de '+(R.covM*100).toFixed(0)+'% com folga de '+fmtMoney(R.folga);
    dimTxt='A ação até a meta de '+(R.covM*100).toFixed(0)+'% custa <b>'+fmtMoney(R.custoMeta)+'</b> e rastreia <b>~'+fmt(R.acaoTestadas)+' mulheres</b>; o saldo a comprovar (<b>'+fmtMoney(R.envelope)+'</b>) cobre a ação com <b>folga de '+fmtMoney(R.folga)+'</b>, que comporta o seguimento das HPV+ e o próximo ciclo. O mutirão converte esse recurso parado em produção, cumprindo o encontro de contas do PATE e evitando a glosa.';
  }
  // KPI tiles e barra de execução — destaca os 3 números que decidem (saldo, execução, ação que cabe)
  const execPct = Math.max(0, Math.min(100, pct));
  const execCor = pct>=100 ? 'var(--green)' : 'var(--pink)';
  const tile=(label,val,sub,accent,extra)=>`<div style="flex:1 1 150px;background:#fff;border:1px solid #f3cfe3;border-radius:11px;padding:11px 13px">
    <div style="font-size:10.5px;color:#9A6A86;font-weight:700;text-transform:uppercase;letter-spacing:.4px">${label}</div>
    <div style="font-size:23px;font-weight:800;color:${accent||'var(--wine)'};line-height:1.12;margin-top:4px">${val}</div>
    ${extra||''}
    <div style="font-size:11px;color:#9A6A86;margin-top:4px;line-height:1.35">${sub}</div></div>`;
  const execBar=`<div style="height:8px;background:#f6e6ef;border-radius:5px;overflow:hidden;margin-top:6px"><div style="height:100%;width:${execPct}%;background:linear-gradient(90deg,var(--wine),var(--pink))"></div></div>`;
  const acaoTile = R&&!R.semSaldo
    ? tile('Ação que cabe no saldo', '<b>'+fmt(R.acaoTestadas)+'</b> mulheres', 'cobertura '+(R.covA*100).toFixed(0)+'% → ~'+(R.covB*100).toFixed(0)+'% (+'+R.ptsAcao.toFixed(0)+' pts) · '+(R.saldoLimita?'saldo é o teto':'saldo sobra '+fmtMoney(R.folga)), 'var(--pink)')
    : tile('Como orçar a ação', 'MAC / emenda', 'sem saldo a comprovar nesta competência — enquadrável no Mutirão das Mulheres', 'var(--pink)');
  box.innerHTML = `
  <div style="border:1px solid #f3cfe3;border-radius:12px;overflow:hidden">
    <div style="background:linear-gradient(90deg,var(--wine),var(--pink));color:#fff;padding:10px 14px;font-weight:700;font-size:13.5px">
      🏛️ Viabilidade orçamentária — Programa Agora Tem Especialistas (SUS 360)
      <span style="font-weight:400;font-size:11px;opacity:.92"> · ${PATE_COMP}</span></div>
    <div style="padding:8px 14px;background:${cor}14;border-bottom:1px solid #f3cfe3;color:${cor};font-weight:700;font-size:13px">${tag}</div>
    <div style="display:flex;flex-wrap:wrap;gap:10px;padding:12px 14px;background:#fff7fb">
      ${tile('Saldo a comprovar', brl(saldo), '<b>não é caixa:</b> recurso já no fundo que ainda falta comprovar com serviço prestado — sem produção, há glosa', 'var(--wine)')}
      ${tile('Execução comprovada', pct.toFixed(0)+'%', brl(prod)+' de '+brl(rep)+' já aprovados em SIA/SIH', execCor, execBar)}
      ${acaoTile}
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:12.5px">
      ${linha('Componente ambulatorial (OCI)', brl(repAmb)+' repassado → '+brl(prodAmb)+' produzido', 'é onde entra o seguimento das HPV+ (colposcopia, biópsia, EZT) — gap a preencher')}
      ${linha('Mutirão das Mulheres', brl(mm), mm>0?'o gestor já tem valor nesta rubrica (adesão comprovada)':'ainda sem valor — oportunidade de enquadramento da produção')}
      ${R&&R.saldoEmendas>0?linha('Emendas parlamentares no saldo', brl(R.saldoEmendas), 'parcela do saldo oriunda de emendas — o SUS 360 não traz o nº da emenda; consulte-as na fonte oficial abaixo'):''}
      ${R?linha('Custo por mulher rastreada', fmtMoney(R.custoTestada)+' / teste · '+fmtMoney(R.custoConvocada)+' / convocada', 'preço do kit por mulher testada · diluído pela adesão por mulher convocada'):''}
    </table>
    ${dimTag?`<div style="padding:9px 14px;background:${dimCor}14;border-top:1px solid #f3cfe3;color:${dimCor};font-weight:700;font-size:12.5px">⚖️ Dimensionamento pela fonte — ${dimTag}</div>
    <div style="padding:9px 14px;background:#fff;font-size:12px;color:var(--wine);line-height:1.55;border-top:1px solid #f6e6ef">${dimTxt}</div>`:''}
    <div style="padding:10px 14px;background:#fff0f7;font-size:12px;color:var(--wine);line-height:1.55">
      <b>Como usar (sequência):</b> 1) o rastreio por DNA-HPV é pago por <b>MAC</b> (SIGTAP 0202100251); 2) os positivos geram <b>seguimento</b> (colposcopia, biópsia, EZT) = <b>produção ambulatorial OCI</b>; 3) essa produção <b>consome o saldo acima</b> e cumpre o encontro de contas do PATE (NT 33/2026); 4) pode ser contabilizada no <b>Mutirão das Mulheres</b>. Em resumo: o mutirão PinkPapa é o meio de ${ente} executar recurso federal já antecipado — evitando a glosa por não-produção.
    </div>
    <a href="https://sus360.saude.gov.br/painel/saldo-gestor/${selected[1]}/${key}" target="_blank" rel="noopener"
       style="display:block;padding:10px 14px;background:#fff;border-top:1px solid #f3cfe3;font-size:12px;font-weight:700;text-decoration:none">
      🔗 Conferir estes números na fonte oficial — painel Saldo do Gestor (SUS 360) ↗
      <span style="font-weight:400;color:#9A6A86"> · ${selected[0]} · competência ${PATE_COMP}</span>
    </a>
    ${R&&R.saldoEmendas>0?`<a href="${R.emendaURL}" target="_blank" rel="noopener"
       style="display:block;padding:10px 14px;background:#fff;border-top:1px solid #f3cfe3;font-size:12px;font-weight:700;text-decoration:none">
      🔎 Ver as emendas parlamentares deste gestor — Portal da Transparência ↗
      <span style="font-weight:400;color:#9A6A86"> · ${selected[0]} já preenchido na Busca Livre — clique “Consultar” para ver nº, autor e andamento</span>
    </a>`:''}
  </div>`;
}
function baixarPDF(){const r=montarPDF();if(r) r.doc.save(nomeArq());}

/* ===== Apresentação / Projeto Técnico em HTML — mesmo design das propostas TEAlliance (inclusao-tea/docs.js) ===== */
/* Motor compartilhado (idêntico no PinkPapa e no RosalindTest): deckHTML(S) monta capa + sumário + seções + manifesto.
   Cada página é A4 e o conteúdo se distribui na altura toda (.fill), para não sobrar meia página vazia.
   O arquivo baixado abre no navegador; o botão "Salvar em PDF" imprime 1 página A4 por seção. */
const DK_IMG={carreta:'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAASABIAAD/4QBARXhpZgAATU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAC0KADAAQAAAABAAAB3wAAAAD/7QA4UGhvdG9zaG9wIDMuMAA4QklNBAQAAAAAAAA4QklNBCUAAAAAABDUHYzZjwCyBOmACZjs+EJ+/+IB2ElDQ19QUk9GSUxFAAEBAAAByAAAAAAEMAAAbW50clJHQiBYWVogB+AAAQABAAAAAAAAYWNzcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPbWAAEAAAAA0y0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJZGVzYwAAAPAAAAAkclhZWgAAARQAAAAUZ1hZWgAAASgAAAAUYlhZWgAAATwAAAAUd3RwdAAAAVAAAAAUclRSQwAAAWQAAAAoZ1RSQwAAAWQAAAAoYlRSQwAAAWQAAAAoY3BydAAAAYwAAAA8bWx1YwAAAAAAAAABAAAADGVuVVMAAAAIAAAAHABzAFIARwBCWFlaIAAAAAAAAG+iAAA49QAAA5BYWVogAAAAAAAAYpkAALeFAAAY2lhZWiAAAAAAAAAkoAAAD4QAALbPWFlaIAAAAAAAAPbWAAEAAAAA0y1wYXJhAAAAAAAEAAAAAmZmAADypwAADVkAABPQAAAKWwAAAAAAAAAAbWx1YwAAAAAAAAABAAAADGVuVVMAAAAgAAAAHABHAG8AbwBnAGwAZQAgAEkAbgBjAC4AIAAyADAAMQA2/8AAEQgB3wLQAwEiAAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2drh4uPk5ebn6Onq8fLz9PX29/j5+v/EAB8BAAMBAQEBAQEBAQEAAAAAAAABAgMEBQYHCAkKC//EALURAAIBAgQEAwQHBQQEAAECdwABAgMRBAUhMQYSQVEHYXETIjKBCBRCkaGxwQkjM1LwFWJy0QoWJDThJfEXGBkaJicoKSo1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoKDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uLj5OXm5+jp6vLz9PX29/j5+v/bAEMAAwMDAwMDBgMDBggGBgYICwgICAgLDQsLCwsLDRANDQ0NDQ0QEBAQEBAQEBMTExMTExcXFxcXGhoaGhoaGhoaGv/bAEMBBAQEBgYGCwYGCxsSDxIbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbG//dAAQALf/aAAwDAQACEQMRAD8A/Q2in4FLwK9254uw0KTRtxTxzS4pXEyMDmn0oFO4ouCGUU/ijilcLDcUoGKMHtTgD3pNjEop3FHFK4DaNtO4paLjuIBiloopCCiijBoGkFFGDRg0rj5QoxmjBpRRcEgApaWjFJlCUU/ijigBuKXFLRQBFI7QxmZVLlRnC9Tj0x3r8rf2ktN8M2msyaj4XDrBcOXMgP7p2cZIjx93aSdw9a/VgHHNfOPxu+B8nxO0ySHTpkimLB4Vf5UjYDk8ZzuPXiuTF0faRSsXF2Pyq8Nanp2mXpXU901m4IlhjYoXYD5SSCCcGu0s9Hsta8N/23FK8knmyRzRqT+7UY2e5AX619O6H+xNq8cBuNT1OGO4Q/KqhmRhjucAj8q971rwBpXhL4Xt4fsbK1TVpLbDONqfaZAG3L5pAOTkDnnmuSphJOLuDlfY/M97230uCXTGdgdhVkBO1vRmB6kdqreGYdP1976w1e8ezEcQkt1Q8O+cc8HgenvXW3/gO9n09ddvFeyadSUMo+Ubj8gAXLbcc5IAIp0b6J4c0BrNYws0rhpZ9wYFlBACjqBya+XrV5KLptvmO2KjH3pbHOTaXqFzp6Wl1cyyyEOsNvCcgsAMbgAfvAj+XatoQ+GdP0e1EjN/aQjCPCchST0JB6HpWXJqsYdb1OU24DHqxHdfX8Kz5tVgt5Ou6RScbeSp/DmuarOrVSUmRGskrJFG/wBc8wlZ4A4GAzRj17EisxrRHw9oqyb+RjB2ex7Zroo9OjtdPe8nLq0pGY25zjkcUkcyEAxEIq9TjAyacJW0ijmfYzdn2a1wGEQfIYAYLfXHb0rlZ4xGQqcuQSWbsPSt+61GwuHEW/e5G3cOmfxrm7x9j5ZckH1zmuqjD3ioLUgjjKnKncMYPGc1FHcX1s/+jO6t2ZSR/KkaWXGI8gVctYvKt/OkbIIOM/pivRTcVqdCajqz6btdV8Hx/CuSXTBFLeOE8yCTG6OX+MKBghSN2T04FeLDTrm4KyzBoyBl0Kn7rH5Svtwap+H7owtOtvcrau8TKiujMshx93Kg4J6DPrV3WZ4gkE13aSI6DayN8qkdQwz6nPatcTVjVUeZakRinshlvpGmXmrNHcT+TbBSqzSfdVhn72PftXPXj3FzeSJbuZJC4QbQfm7A/Q1vaF4Y1vWJo4NJtnkhnYOTJwMD7zZPUcfw5r2az+A/iS6tpLRHtYLmZl4lXDL83AikIAZT1YqcgDkVrQwnMvdNLKO7PM9e8Gan4CisZNatmRdRjMoWbAWREII2bcH5T1I9RWprXxD1jxDa2lrq7TR6fbRLBCDI7RonTHJIPtnNZWv+BPiT4RFxa6rbvsTCOWcE45xtyQSPXGcd61/h/wCC9WuIG12V/wB5aOJYrMkN5mwCTLjOAmCME8HkdQaeIjNRaWi6lU4xfU80iuzY3K+WqyKkhZFkAIYZ6MvQ/lWzrs19rNhFq2qzHKYj8xjk9yFUHkAf1r36T4w+KNIt/O1K30l9jhFt/JVt2T67SMgVyt98QfiHb6/J4yl02zeOe3EMMBjjMaxs6jcEGcMWIHQGvHpJ1J80UdPJTX2jzDw3raWOtW2o3cqb4UBTcBh8E5BzwW6DLVteP59Tvb5Lm42STXYX5YwNzYUY4XjgDHAq7ql1qOp3Mh1exsbH7QSjkgII2xzlVUkdeuK8+vLfVvDbQK88ATeRHLFIH2spOM7SWHT0rthUcrqJE1G6aZP4dsYZLgT3cjJbgbcxjcTL1VcAEjODXoek2l/4i8QwQahaGCAgwRlIgm4pgg4AHQH5ifbNXfh18XrDw9oV34U8Q6INXt5ctBcwJ+8ikypzll5GEz16Zrr9W+Pmk3Fja2OmpdrsR43URhGGcYCsrE4GORxzRXwso+9HUlS1szm7+08OXfhd9O80Lq7zqGly8jlGKkvuyVUAkkYwRXnOreI4LmWOaYn7dgw3aZJRiB/rVxxkn72K1NL8WeGYNd+0adpM16p5S327idoyzEAN6E98VgeIovEHiK6a7tNONqIczbN6+ZjBJPJDHAGSMU3HmtCcbIqDt1M+LUbJoHsdkUQeUHz2XJUbegPUdOlMF5MsSRzO8lmH3NFvYLz94jaRgmsNZv7VRrm8Jkl8wbsY3FQuBwSORj1rU05Aulz3JliJjJXySfn5xzjGD19a1jRUN9UVc2dKkdb6XUZttu8O8x4cI3IO1RyO2eetYVnPBHfTTyRLcblLBZAW+cnqB3wPqOaypDfPhJR0+6PrxivVPC/wn1HUNNOtX0yW0DKxGDvfqAMKvTJ9TWLjLnephLc8su7zUfLTTmlknhCDbHyypnkhR0H4VPoWoMiy2TkMCvyKwz83+z6H3rv9L8M3NlfeTBvkZQwJKkElR8wAPtxXLah4fk0i0j1iIvHeecskceOdo+YNkHr0461KqRmnGX3lJ6anqHgf4ZrrLTt4ssbhY4UYoy7l3McbVU9MjrXnOreH9f8AA2rSOyGO1uQUBbDEp/d3dyM4OO9fSvhv4orrXhZNUeZIrxD5bwkMSTjOVUKc59favK/GniIeJo4LK5t0iETuybQMEtjcSe3IroSjTjy7iTseKSN5xZoTkqSQQe34VoXLILaO6AxvHzZ6VXNothqjQ4IRwQD0BBqnKZzOtqASozwOeT06UpxUtnoayV0PuJjaxyXMOCMDnp+XrVCyummTDYLHJyRzU8tpdSzJaTxugLAMcdq6f/hGLKJ1mtXMbYwUcdqTrU6K16mDmoaM5NGfB8zJAGBUKxW7n52PPYf5zXSSaTafaRvciPHPrn/Cn32hwoEjtXU7j17isHiIyE6qvuc/F9miJaToBgDvT1uIXuFfaNqnp61VltJoJWjdS23qwGf5VSEqiRQOBkZ+lbxTmUm5bMvXc4eUbBjHqB0qsEypY5OfU112sW1q4t5bZSV2lfMP8XQ4HfjNc/5HlZFXZW0NFAzgADlakXIYGpNuX6VdjtZfLDkbVLYyeK0nHS47EKyOZVLgegPSrE9lJffPu8uL+Lkc4p7zWlgPIb94w4B7fWsuTULz7SJHbco4C9sfSuenGV7xMoxs7jnvLSyUx6egLdCxGf51ls81w3mTsWPvVmZIy2+IjB5I9PaoVQk4HU13RVka3ubXhm5+x6/Zz9MTKPzOP616/wCL4CGimI65H8q8LgcwzpMeqMG49jmvoXxIBc6Yl0v94HP1FZVnrcuB5lIi7a4yf5Z2X0P9a7m4XHvXNy6ZNNctKCqIT1bv9B1P4VMJIqUb7F3SZPP0y6tT/DhgPzzWYtm0pDAGNemT3+g6mt21sXt4ytpld/DO3GR7DqK1IbZYMufmY9Wbr+dZVMVGOiOqjgJz1lojGtNLAYyBdp/vNyfwB4FaywxRjA79T1J/E1cwDyRion9MDNcFStKb1PXp4aFNe6h3AUFfpUBldeF7UvbPYVB5i7tifMx7DrU7o00WrP/Q/RPaKXaKdijFe1c8UaBig07FKBSuAwHJxT8CloouAmBRgUtFK4CUtFFA7MKKKKAswopcUYpJlNCUUuKWi4WEApaWlxRcY2inYpaVwGUU+ii4DR1p1FLSuISilxRijUaXcSlApRS4oKEwKUCoJ7iO3MfmdJGCZ9CeBmvPvE3xBsvDN3cw3UkTLFCsqjPzZLICCB2wxOfalKSSuwPSiB0r5p/aMl1qHwtJBF5P2dz5kcu4rNE6jkADIIPBzxj3qTxF+0h4U03TpZ9LZZ5oZQu1g2yRdoJ2tgDqeue2K+J/iX8Rv+FjeJZfEcc8sNsgEaQ+YxQ8fMNvA9icc15uNxlKNNpyKSscTpF/qZtplvJiwU7WeRi23b0G3oMYxxXA+I79YZlt32ujZJxnII/L1rb1bW4xYSPZWywwlwxKA7c5yM5z19K4XVZJtQvh5a7gyjhR05r5ClGU6jm9intqV7rVG+zxw2u4iI5GexNMt1mimSaVt8sxGUHHB6kn/CurtdNjtLQRFt5PzFdoP4HvWPc3kNsTJPhyTlW24/p2rpjJaxjEd0kP1m8klk86RmjToqqc4/OsW9v5JYfL3ggKBxkE9cE+9UbmX7bdmUKctjA9aeLC6eUo67AFz9a1hThBpyHBJO5BbK7lVB6/pWobFgzSyNkCstj5BMSdeKvxTy7/AJ87V/hrWrr70TWSvqiGW13A7OB6GpHilvCkStgrhVB4FLPczvLhwdv8PFblhpuoFRO1qJbdwfndSUxjnkYwcdOc0Qbt7w4x7nQ2Gj6hYSpbNJErXEavEmNxdiRhc44IJznPaum0rwTf6jo2oeK9TkWZrK4it1tnYkkurkkgAcDb2PeuOnsJIjFZ2biZVG5ZFbGTjnAzwR+dVv8AhLda0KZrvTCYHkwrqAGDbOh+YHnrVKrSb5baju4nr9j8Tr3wTcf8I7okUL2cCDKzxnd5uPn2P1UMeMEEU3xB8ddV1y1axtLVIYdzMuCxaIHO4I+Qe/BI49DXms2uDxa95ceIZJLa6kTMQwMSNycN8vr6EdazdH8G6vqNy/8AZSsyxRyS8c7ggyemO3NaU6lSleMZNik76s37/wCJOvXUkn2mf7cHQIhuAcrzkgFcckcEkGs62uNV12K4vLCQWEaKkX2cM+ZSAcKjgYB/3iBzRo+kQ2U0l/r9t59rAg82MsUK72+Vhjk9CMf4V98fDb4I+BvFfw0GqeHpbqzGoo8j28nl3Eb8sFbZNG23A4DLtPHXNdtGk60eWbI5lHVHwLe2k1/ZJqsCgW42+Zk/OH4XkE9c8ccVrL4ztLHR7zRfs7SR3Plr5jMS0TRuH+Q9DkDkcdq2X+GXj0eItQ0mZG1MWJaW88l1DPGnL7XBZS4XJwATx0r6YudK+Fnjb4fWJ8J29nZ2em3qLJ9oA815Xhk3efko+1QmRnAJ6dCKwp5Y4ybjKxbnsfFdyX1rWIYX86K3uhuEj4Z2XOCQM4BJ4GT2r13wl4G8OXd+ujWtq8sM0ZSY3I8wiQHPyOrIFbjGcEVkXep2txqc9hZmJfOnEKMijCQwHCsu7PEhLN16Yr2bTtZ0bwn4Q1WPwnLLfI0kYh83IdHyNzrwCctkDHr1rh+ryvbmsl+Zbq8qsjwPwxp/iq08dDTfh1aos8hKi2utskLkBg24kAr8pOMH8a+lPg34R0XUPiHc6Z8SreDS9Vt4thtNn7qcSMWMkT5YZGAMHFeifArULbXtC1O4msIZlKMRcCIxyeYmMDzjwm3OR0PNfKPxy8WX2reI4dH1+6e8l0tGSCUMN0UcjFuXjAO5OFyTyK9PCqUaSrVtzJ1G/cPUrL4UeIfA/wAQbrx58PobSfSLVpJ4lvSNxi2EuoVc8KCcE8kDpmvLfiX448Ea34MsbvSoJYNZdi0qxkeSqt13nAbd6AZFeNv4z16G1XTjdPIqB1EyO24o2VZSQc7SpIxnoa5yU2EoTyUaKMAeZvbcNw7+vPpU1qifuxRUaXdle7jur9W1ZYtiJgSNHxkfyzxWxpWgwaui30F8lnbSzNGBMC7qqgEsdoAPoMYzjtWcutXptpYIJJVtmYebEpIVgBgEjpWbbtLNIlhv2REnacgBd3f8+tZxlLl1OhaIuXltexEyOfNhLlY5F43AHhsZyM9cV7x8I/iFYWlo3hjWXclmzAWUEDuVOOffmvnu7tFtLzyS/KEghGyOO4OSOtHmiZfOiJjmU9VOD9ciqhNXEvePtO8vrqHU5gun74UwVlRly24ZbCkDp061yFpa+HJbNbvU1YzBQxjY9MEY9f514nofxJ8TaVGNOmkEkPGTISWHrtOeK2ZvEP25Fmm+WQjIHPSipKOl0KVloyXXJ2s9X+0aDDtikJLJnAX1H0rlL3VB52BGwfJIyRjJ6/ypms6tcsFUN5aEHKocfmawxMl6Et4gU2dGLZP61yS59WtEYSlLoaV1eW9xtSZGSRO456f0qxZ2TG7kuwD04Ax1pbd3mUW9wgwFyZO4pmqX727i1sJCNq4AB556kmudVGl7NdSFVajyl1rq1S/Vp1DEKcnkkNx+FUbnUWN4gmyEAIDDrnnr+Nc7b6isAdJhukz95uazrq5kkYMv3eg5q44dydpEKLe518s8EUy28sgYyLwQPXtUYv47PEOA+DyepH+c1xolBURyDa3UHNT20N/Gwmj43cDPOar2EUrMPZdzqdQ1OTyynlqsL91HP0OayVjtYlASLcD3J6/pVyG6V4BHKwQA/dbGauxaRI42riRWBGDxj3FKL5BwfLuWbgNPo8flISyNjPGACOn14rmpopN+WGPauuSEw6abR3JIOT+HT+dc/OoB7n8MV2UpqWx6MJ8y0IYFsIRvlzJKTwg9aS4Sf7104U9kHPH4YAqncXslsRHEoTcOW/i/PtVWy2y3iFs5Y4/StJxbFJ9BxEV3uXOCorKEfOBW09nGrsxbDBsbe/1+lQXsZhYoAAvXC9PzrSlFxM0rGeAO1WreMzgwquT1GOtV92FzV7TlunkJthx3bsPx7VdRtR0NIrUij0+a5dYoRkuQOOxJxz+Ne4FZZfDywzDDRx4YH1U//Xrg7K4bT8tpWfMdAsjk5Bbgswz3z713umz3F1o8n2mRppGJ3O3U5HeuSVVSsupvGjNRcnscG7diM06zgjkcu3VTxT5UwzKexNR2mPNK1nV+F2OrCWVRXLrNk4pM+tWCVAyarEBj8oJPoK89JnuaIYzu3C8VGdwHPJrWh0yZo/Ou2EEXcnjisu51zTrBWTTUEshP+sfnFbwoSe5x1sbCOi1Llvpkl1ua4cQogySajOu6HpDFNNiNxKDje/AzXH3mqXl8265kJ/2Rwv5CqALO22Mbq7KdFR3PLqYmcz//0f0Yoo5o5r2DxQoo5o5pFW0CijFLgUMEhMGjBp1FK4+Ubg0oFLSgZp3GJxRxTsCjApAJg0YNOooAQCl4oo5pXEFFHNLRcpCUU7FGKLEpCYpQKWiixXKJxS4pcUuKdwSG4NGDT+aOaVxiAUuKUUEHrSuB4T8WPF7aTJLpYQyAW4YIhAdi2chScdvevzb8TeJX1rVX1C5vGTCERwB9wQcAIDkA4HWvq79pXwb4rl1lfEpIlteBCEyqxDkZkOSTzycCvi248AarppfUb4qjq4GxiM4bkOMHoOODzzXg46pNzaeyLSCKy1DVtKnWNZWVZFRXIO0EgtgsMgZweM9qnjhjsPD6wzkrLEGBXHDY6nJ7Zz9ay9R8ST2Ucmh2EzRQXMivKTzkoOCAK01A8SQC6C+TbqxjUk5L7eCxHQZ+teBio81nHZmia1bKOh+ItTu9Fm0ZUVoGkVnAUHnP0561FceRppdmU7y2PlHJGKxbDWrnw+ssdntB3gNkZO3OOK0P7Vh16eS2eVbZequwJzgHPTpnp3rN0Wpc0dmS3KSVzkri8nmmaVJCnUbf9mqxjLTfbAA6oOBnoTV/+zVkuTboSCuCfcetbktpb2NqUABdeuO34d61nWjH3VuFjmDIkLDzIipHOR3FXLPUY4g0rASuxITfg4H40y9lgkYNCwJC42jPX0q5DZwW9slyoVxIMFs9CMEgDGcjP0qn8PNJGkYpakKpaPMrhQcKGZj3bFJqT28Wx15J54HJP9KY725cxW5wQoAJ9afa6ptcW32P7TMmCpzhRjru4PH41L5m00ayZRayuX/0uP5dxwUIOWB//VXrHw28ajwFfCLxDp76jpUvz/Z26RFh80iKw25A5PIqfQtQsLrQLnUtXtRGxfyVVMBN+Mjk5PAHpU9gia1MblNIe9s4lQTTtMqFOgyybTkewIyK3wlep7VQE4q12zu/iR4n+GnjY+V4B0f7G8S5S4wsJbuwEYPzcAnJ+tcFpQ0rxKHsb82tqLS3LQRS7VLyhgDvcgdRkjk1197BG9yNH8PSRJckbVtvKKwScj5BKWHUZ7DjNeX+NdTaUWWk3enxWVxCz+dcRg4fnAVTkgquD6nNdlWEnUcqiE3BRtE7rxFqEA0XT9M1JodURoS9jcQgM0C5O6CVSAcqQcZzwRXERXMmmalLDotxIkUmAdpIXGOQwzyMZGMUms+FtV0+3t73QpJL2xMH2yRTtDRjneSAeRhc/TsKyL/SNQs7WDVncvayygSmLAYK4JUAlsEkc4x9TWleNaUlKmrGcm7JIZe6hfT3P2WS6NyVO6RSSM9h19O1et/Dz4t6l8O3/wCEdlu55dOuI2lECyzQiKViSQGjBJzx04r57S7gN+VdXSHPEgUGUjsSm7H61oWlyZtXit7bcztJsQzL5QIJADty2B6jn60sPKrCbm2JJrc9C1PxNf2lwdIeZDCIvOKWcmV8x1zh3+XOM/MOcn1rz3U9V1nWtQXW5I5ZizjfIQSrmPB2ttBBIHr61TgghjHmyBpWYFXjPHzHjg+x5/CvT/hnra+CdYk1SylVmeF441c4CsME5GG+8OOPSuiOKjJ++zSM4pXSOZj1vVPF2tNPodtsuVO5ioHyqoA4CjouOwz7V7TrHgDxD4AbTLbWfOvv7TVXZrXzRgSDO92IUqRnhe/tXjPiu/m8Q6ufENnALHUGkLyvCcRsAF2kL13HBJ55z0FdT4w+MXiXxpDZzTyC0ntohG7RZ2uVG1WwckEAdMnms1Ww6vO92Zyd1ofQvin42aN4Ps0tbe0mgtZA0ctvHiPeAMx7RkFSHALFRyBgmvhnW9dk1/xBd66Q0pmYsQxywBPyjPVsDArdubuy1dFtrt3kAOWYjkkdgc8Z+lULERaZNLPYDIf5dp5YAdugrCrjfa35h00lr1MeTR7+COOa6jMI3fxcH1yRU2sSw3bC6061VYowNzRnIJ9cEAjP0r0PxT42j1jQYoL2BYrg53BRxnGAxOevt+teXraSiBhEwDFdxOeMd6zpPW61OpWLUWri30qeGNCWnwpYDAx3B9+lc7EBJLGJG2KzhSTyAD3x7VowIkMf7nDsQRhunP06V6H4W8PeGtb8FXkJkZNX8xlAcgKqjDKRnHXoa66aT2KucRd6Nb2vLhpXU42pgnH0BzzTZLVZLYXEMRiaM7CHyp9eS2Oxr0j/AIT7TlsrC7sNPhW7tQFlxn5yF2liT0zzxzXnevapeeJLuW/uysWcERp0H+NRJJbsza1Lq21tPLFdvxEcFyoyffHSp9T1ixEQtrVCgU5HPb0z1zXMaRdXL2U2nqpI/hYfw06PRp7u4EMkoAJ5PNa/u78smVLlb1ZFuN1ISMtuqaDTZ5ImuABgMV69/SureCx0XbGf3jFCOPWudEt1clhKBHEh4UfzrKtaz1M5WtuMZktkwjEt1OOlYqXDiUlGwSME5/QUs0xZjjgUyJYd4VRyayhTsrszjG2rEdVGHJOScEfSrTlLpkjjcA56nharvzKyRgtjj/69b1jpEhuIyxKqeoOMfnVSmorUJNJEMdlaxyj7ZIDznYgJJ/HAreeCyJ8qFGiY8gMcfzNF3EiyxyoucZ/LinXd/aXT/YZPlJUEEjOD65yK5G3PUxbb1Mxo7GIgybC0fKhfmbjnt1P41nTXd9Ndq0ZIjBJXsR68da1rf7NDcskagSZyuDnIPNLeTRYZG4mjHXrkH6VV9dgS6mlYXS+UwbcoPUnoT61QulDSHYO/GOlQaBdHe0Uw37v4T689K0jEhYgHJyeK6KEORtnbQVrnM6vb8LLngVUgiMQSQ/Lznpgmt3VbWaSIADG05P0rD2XV4TFb/OEHXt19TXoUpJo0er0L2rtBDfO6gsXbOexHbFUp0url/JTLYHXsPxPArdntIrqSOVQXkREUqOFyAM5P19BWgbPzWzMQTnO0DCj6DrWE8VGK03OqjgpzObttJQnLgSMPwUfietbEMC/cb5tvYfdH4VeaHjaBxSqEjAAFcVSvKZ61HBwh6iiPHJrsPDBV1miPPTj65FcezgLk10PhabOoNEnVkP6EVnTfvF4pJ0mjI1OLy7ySM8EMeP1rGifyZ93XrXReI0eDUpMnJOD+lctKzcspwRXZa6szx4VeSzRv7YxH593KIk9+tU5vFVlZoY9LjLsesjDGPwOc1xVybyRi8xL1SBkaQIBiiFGCKq4mc92al3qN3fSeZeSlyexPA/CoEEkhIiBJNXrXTdxDyc10ttaKvQYq5StojGMe5hW2jSyfNOevaujttNihTCLWhDHg4xmtEKIk85wSBzgDJrN3e5eiZ//S/RqilwaMGvWPJEopcGjBoAKXFAFLRcAooopXHYKKKdigXKNop3FFFg5RMUYp2DTsUaFDKWncUcUXAbRTwBmlwKLgMxRinYNOxSuAynClxSgUrgNPSkqTAowKEAmDRg0pyBk8D3rLuNb0i1/19zEp9NwJ/IHNS2h2ZqClrlj4y8PBtonJ/wCANj88YqxbeJ9NvVzaEv2PGP50uZFKEmeJ/tG6X4h1DwxGNEgmuQpyyRM4BIOQHVCNw6cV+efiu28QypdQa5OsN1bsRclgAN4BIUe/GAK/ST4mfGPS/BZisnuFhlbmVcEyKh6bMA5Y9gDXwV8RPHF74iefXBDJOCSiQXEeXDlSvmscEbsZIOT1rysfKnNbj9lI+cEsbtbuEuDKZDxkZA9zXptvfeGvDupPpFzc/abRjl2Cj5HYYk2BeMDHFchaab4h1u4SS1bzFLKjMnAUtnaCeAM4Nel+NfgT4w8IaNba7qNoI3iZjMWlUu4DHaFjDEnA6sBj3ryeS8OWo7G0aTseXtaabrOoyxaUpKyl2UStgqozjJGOen410Q8I2kOjR39xG0TxzGKRc/eG3Oazb6+0eezv4YtLBvri4WS0uYySsa5+aIL0O4E9q07a01WDw0sOoAh4ixjVuWCkDP05FcmIqKglaV7j5EkZf2Wwsk3W+7zSODJyME8A/hXPX1yzhvLUq5YlmbkZY9uBxzWLNeXBuCpYtgcgnI6VZtrK5ukM85KJnJBPTPoKyVL7UmZCppEXmicy5ROWKYyM/nVm+it7aHbaSFwCGDcA88kGu+uPCWoWNvFHKq4YFiUZduf4RkHGawYtAvL67NnZxPJIFLScEBcHB5PB/ColValyy6GkVc4uPe0ZUdc7v611XhmKNFe5uyIY5RhpGOMj0PtnFaOpeEL3QIAL5WimlIMXIKFTjJ3LkdM8Zq/e6Rd+IriNLSSOKC2wszjCogHCt2znnOMmlOtGS1ejKXdkWqaz4dj08WFvMTJyVRFAjGP4jnOSfU812HwwOj38V5e+ILue1sI0DSLE2GlkH+r4xtYBsfKQRirsfwm8Hz2sV1eaiyvOrLBcAHy3kXkg5HuMcc15YdYm0TS59EmVSVnJyPvblbBP44xW+CrUk+aF20XV+Gx3/jXx1ZaprwaFD9iQ4to0C25Rwcb2MaqW4JB9ia5vWl1/xHp9u8vkC2iDshUjcuCAQM54Oc+5Ga881i685lY4B42j/wDVSWd5qLSG2thg8Nvx8y4yOD1712wxEpJzmc6lY9QtbHU/Bl1b6veyyalp13bNFIlvKVABDLtcrnAJPI4zzXJeKBoEGmRWPh+6vJGV8yRSvmMEA4KjHGD+lZUmtyqDazu8gRjncxIyeT1PrWPLq9sATOn73JPyjgelarFTa5IxJlJvVG5otwqW3marEqeS2Y5VGHOR0J7jjjPvWndo2tMLtJDuxt3MBnH4Yrz9rozFWunbYDkLyf0rSu9Z1SeMJaSGONRgY4PFclelWk7pk8rZ0d9p5slWVJgM8nfjPTNcjLqMtsPLsiM/eL9/oKrrBc3cjC4mZ5Dz8xJ5NXYtNaT5ZWIyPlz1YD0AqqdNQT5ncpQtuVpfEVzPDiZDvHR1OOfUjoaQ36zoOSzv7YCmllso4xtjIOOuO31qqJlG7zFJyPlxxj8K1UIWXKilDqaGmXMZLtcyGNOCCvQn3rbjjDo13psm+Rhg8Z7nkj1rmLK2adgiDgn+dac0cunssSl13HIKkgZH0rCrD3tBNWZox30NxDsvY1YhSBjuemT71RmEUsMmm28O6ad08ogkEbf4ffNLDp81x+9jY+azgD2J6fmeK9z8MSeE/B4XUbia01HUSpxGy5EDAcncyjkdMDOa1owalZbGsNGZXwy8JeDl0SbxF4xXJjmMao7FEXaATu6ZJPQe1eYeMLnT/wDhJbi58ORmC3k/gA4AIwSoOSPUZJro/F3ie91/Umu8hiowCqhQB6LwMVxNvZyXUjTXRIHTHXA967qtWFNWNXJJbmJ9lmlu/s9uxUSMB14PvW+3hW7DYtm8w9wwwD681oPqWkafCq2yDzFJO7HK4/rXP3fiO/vZCIHZV9Acc1wyqzm7wVjCVRt3Rt2WizW7mHhUB5C9D7Z6nHTNLc2ElvH5kDZ5yQQOPoetYR8SX8MRgK5YDBz1+tQm8urvEplJzjcu48Vl7Kq3zS2M5Rk9WOuLwLln5bOPrWQbt2Ys2TxXZsLQJtAV8nHrVK4ksW327RruT0A5HXIrenUjs0FOWtmjAkjiZTkAkjtU2mWUUk6R4zuOD2xxT5mh/tKFsFFLrlWyBjI6mty6XT7JpJNOlLLL93qCo7iuqr7qujrdkrmmiabDMLbT41zgLIxGcn8ay/7Uha5kt5CsSJ8yZ7kcYrPh1KGwiCw4LsSTu/TrWR58LN5s+XY5B9fb8K5I0ZbyOb2Tb1LE+p75z8zCPBHB7en0qoXSZTMM8etSxCIgrNja65GegxzUMSq0D+xFdsaCR0xopFWOd0kLxkhweG9qnE0hnG3HTBHX+dVVKJ8znv0q1vJYSxHGetFSNnexE4nU6Iv2eU3G0EqOp6DvxViaUXjyXUDjOSTgAYqt4cuvLu2trlDNHN1UDJ3DuPwrRZLXzS0YMauepBGa5Jtp3TFyztoRrasYfM3NIGxxnGfr7UsOm7FKEKqHnYvA/HufxNVIbpjJ9nQ5AzxW/GqIMHj2NYupJK1z2cqpxknzLUqxQBMoV2genAqVv3Y7HNSsQW+Wq8iSSHZEpZvQcmou2z3bWRVdjnnpUe8E7VGa3IdGaJftWsSLbxejEAmqV54o0+wU2uiRBjjmVh/jzW8aLZxVcZGOxINKlQedqLeTF1561b0jWtIi1eGysEz5hKtKeuMHgV53eX1zeyeZeSGRj/e/wqzo4lj1O3uEU4SVSfz5roVKKWp5lTEymej+K7ZftKSISAQR+VcJcJ5ZIcZz6V6j4uUPDFOvJ/xANcFMmeMVojA5xXgkJUcHvmq4t0W4Rl711a6JbXUPmFcE9SKsW3h2wtXDu5kYcgdhSv0HYjtrcsQR0rdjtkjGXGaekfQKuAKtiLby9JsoYkSAZAp00giUEck9qnGCCEGKiyictgCpbJaP/9P9HaKXFLivV1PI1G0U4UtA0mNFLgUtLigobgUYp2KcFougI8U7ApxoAzRcBuBRgU/FLtpXATApwUU6ilcBu0UbRTqKLgN2ilwKWikAmBS0UUAFFNdkjQyyEKqjJJryvXvFl1eubXS2MUIOC4+8/wBD2H+c1EpqO5cablsdprHinR9EX/TJCzdkjG5j/Qfia4W9+IN/cHZp8Kwr/ec7m/IdK8e8ReIdJ8OEQXp2qH+aSR8sAe+WySfxryzX/jlZWsTR+GLVbmVRhXnYqn1wBn9a55VZHTGikfQkmoazqF4zX1w7gjhc8flUXlW9ufPkKKehLMB/OvhjUvjP8Xry5X9ykCPkILWPg+vzNuJqg2peMNdDS3styWA+YO7D9OlZufc15D7f1XxX4FgYLqupWyBG3YDFjn/gINJF8bfhfprYW/38AfuopD0+oFfB7+ADd/6XLuikLcsBlDntj19wfwrWsfBkFpcPZz3G2VV3iPIyV4529e/rUSrdClSR9UeMvin8GPGBDaj9ukeNcJshUZPbJZvwr4f8QX8d1rDixfZYSTlmDja3lhssAATjIyBX0DoPhrwveeBbvWIwHuYHkwrkq+EUH5VJP54NeHeItO0bVtR32YeMp95Wx6cnoK8bH1FGUWTOyPp/w/r/AOz7pehJaQR6lc3DAMhkEfy7TnGQR6ntXiPxW+Li6xfeTpKzWtsqmNIpX8wnJOSSAAASenNeatHFp2z7LIUYE5yc5J71z1/Ym/nkku5Cir1b6dua851nUnZ7GM63NoiKwurq6u1nlwoRgC3OFHeu3juEkuJY0b5512qf4QBzXlUmrpbo8AXKAEbVONxHcnk+9XrMXN4sd7HKVAO2NF7seufoKjEYVu0nojLVG+dAiFxLcXQKQIAWK4JPuPrVK51Vrq3jitYgjRIFLDJ3bRj068V3N0lmtoLe8kcJtQMeBltoJwMds1qeFvDOhxaraJFcrNcXDhhGwG3kZAIzzmuRV0k3LoWoPoP8P+GIn8NxaxqN3gzOUSNUZscZ56c+lelvJpeh28CzyKUeIAFAfMckD5G4wD6c9KfBYTWFtP4eIEzQB3iRVwVk2EAnHXAJPb9Kx9O0m28iwsddLpN5jXJ3/dkdWGBngjg44NcEq6qvc3graHPeMtE8P3q2upaFb3EPncBXYbS23pjsfXt6VX03xTpHhoxaxqduWxG0XkqBhnIHU5PAx6VkeKdcvIWmjgdhHHKXjHUYzgbT7LxmvHNWvbi6nZjMXHZD2z/WuzD0HVVpMmTszsNX8W6tqjy22kyBInfzdn90j0zjFcs+j6hqVtca9JmTa26RlI4JPXBIz+FYluzwsZISWdxgqRnitq1nuoLFogWQEkYDHDZ9RXqqk6MfcE5aalGeWFEBK72Y/Ken86rm4ubWdp7foV24P50+clyHA5XofSpTrrRIYY4Y3JQp8wyRk5yOnPoa6KcNTFtMy2aOQCV85JycY65oNqs5AORI7AAY4+bpyTUmk6ZLfXXlo6RyAkjzDgYXk8njpWlZ3H9nSLdArcvtGwPhghyPvD+IY4wa7401FXY0h2q+F9f0KdF1CzeLcm6NSVfcPVdhOR9K5udZN+2RSjDJ2sCDnPPBrqk8R61Dew6mt48kloP3QkJdYxn7qq5YY9q7nUdZh8eaaoNpaTajMu+S4XMU4kGcqEVghGMHhR1qpSi9VsdCimrnlaXptzuQglsc+9WtTv7OeZb+1TyDja6joT6j0zSyeHFiYiaXBJ+X0P4/SqrabJAysm1wD35wf61lB0k3ysiMoJ2RXW6aTCwD1DZ75Oas2OnrcXklmrFyqsVZBnJUZ7kcVb+y5t2kljf1V1+Xae4IxyPxq5YGGxhk+V+R8oBKnn3HPPfmlOvTirJBKrFEFqupJEdQiUFDg5z/AHTnBH41t6PqFrI5k1q1+1QjdtQNs2sxBLA4P5VbgudFNv5NvlAMfISdrE9RzVXUUj4W1GR/cFee8Q+bRGDrK+xi6ii22oMmltI8AI2GUbXI6/NtJGR9apBtUZgpj5J6+lXWF3AxedXQDJ69c96U6r9ni8yBSTnuT+da8/RIV+bSwz7Hd3d2tlbrk993AzVz7NrCxm3i2bgcYHc+pz2p+n658xmnVQQPv9/wqrqWtLdhI7T5NxG45659alqT91xC2lrGXqGg3tuGku5o9x5IGT/So7a1tNPhR5HEhYljjjGOO9Ovrq8kGBNvIHzcDp6UfYIpbKK63lt+cg9iO1dFOFRxtLY1jGTWpl310rys9uMA8Anviq9jMtu5LqWBBwPenzRAcVr2Gjz38ipEMK3Bc9B+NdsYwjGx0qCtYkjEKWyy2w5HJzzzVaGyu52W9nCxoD94nlsegrY1O1stJSMWMpuBu2ynA25PTB/Cub1UTRsG3MVXkKT8ozz0o9nF6pD5I72Ottw16RPIAixsAgHUkGubvZZpLtnlADE84rbec2dusGd2cMccHHfHXj0rOjidrA6lIPl3lRx3xn8e9clpOTSOVpuTsYjwC6kKA4C8596iFpOqM3B2DOfbNWbTmRy3HGfzzVmaKdm+zoDjaTx6KCT/ACrupwtozpjC2xnW/ltbNkZYN17Vat0Vlceq5qppixyRzRE7SORmrdpE7vtyQAMGnJ8uprCLbSRQjsXeQCUkA9hyf8K2206TyRFEoUfXJ/E1oQ2iofl6d/X8TWmscSLjFcVas5bHowwMbe8c9bF9NaO4AO5G+at+9s5Gk3BuOCPTBGRg/jUJhT5hJ8ysRwa7DW9OgtNHhmthncFYjPPIHA9qyp6s5q2H5LdjiSghbeByOtaUVxkbh3qiylgQ/wCVZU2o3VkoS3QZ/vnnFaPDqRph6yo3sjrTGip5t1IIUH4k/hVCXxZb2imDSY+f+er9fwFcDPdzXEhe4dmY+tTQQSTY28VrGjGKIq4mdTqWrq/u76XzLqRpD2z2pkVncXDfIMDuTWpaaco5YZPvXSWlkAlUn2MorqY1ro8a4Z/mNdDDZCMhkGMHNaMFsAtXSqgVm13GbmsxpPo0br1CBj+AxXnkh2oSe1eixhrrSgmM4VlrzyOJrmdLbHU5Y+3X9aqImTWYnkhEZOFPOK01WKHaszbQ3etSG0WNN54AqnqGp2FpEwnCkf7XP6VLeugIlDGOMPHhh+WR7VVuL6GMA5znv6D+dchea9d3MRaxjXavAPb8KpW93sge6uZdxHAHbIPSs5yaVzOdRRN668R7HdbNN+xcknjn8a4yfV9WvpBJL8kZHGDVuW9RpUIC4bOcfhThEkqFMHBzgAYA+lOMrfEieeUtkf/U/SDBp2KXmngcV6jZ5SQzFGKkwKMClcZHil2mn4paLgR7TTsGnUUrgNxQBTqKdwExS0Uc0gCilwKMCgBMUYNOopXAbg0uKdQBRcdhOKOKdgUYFFwscD45vmSCDS4jgzsXf/dQZ/LJFfD3xV+N50a9bQfBBEk6ZWa527lRumI88EjucEZr2X9rHxTc+HdDsbLTW23OoM8YYHBWNdrP+fAr5Y+G+lPeeHNX1idQs1o8Qjc8YUqxPIBIyQOa5Kr947qK9087g0Hxt4uv/wC0NReYvMd3n3BJZvoDk/TA/SvRNL8M6JYgbma9eRXK5O8K0Q3HJX5F9PmruVlkkkMVuvmeVqEUZVQUAVgpJzzuwD6DNZNjBeGSyF48bEz3iBI8EEGHgZzwRz61zy13N7HQarHa3XwYg8R3nlw+TcSAyRgOFwSO+4H36iuDt73fqelW0rSkXSp8ynYGy5XJWPAIOPTFevaZGZvgFPFHa+S0N3MFhk6Hnq3A65rzKzumS80GK9mRFeQLhCx3YuGCgYUgggAHmrnFKxEHe9zk7a3C+G7yWCwYMlzGAbvccgq/zZlJHH9a7q31S1i8SRabdTwoJLNSFVhvBx2C844+npXml/oelReE9Ztbm+mlQ3EDFlUZB3FQFJbnO7npXZaf4Y0iXxVpOorFNI7WEaCQkbAoaQcjB59eal2tqW2csPDHinxPbTan4Yle4061t/MmnDkKSVyQC2CTyOK8v1LU2sS1tbrvHV85JPfqexNemXniD+xNNTwbpNulvb72mKjgFyu3kAc9BXkN3ZPdO7KQ+4/MD6ivk8VKDrWvocVRXbIfMF0BLdp8o6oP05/+vXO6teylz5mMdhxiu+8OeGjresW+mXUq2cD5DyH7q4BO4+5OBXKeJfCjaRqLQT3EcqBmCOjBi4DFcgDPXHSu2hGOkrjVF2ucTGJb2Xy4VLljgAdcmvYfCltY6JaSm9HmcYQgctJ6DocAde1cVDpEulmPUJt0SHBGfvc+o7Vt6c1tHeSQCXdLMOMAEAdgDnr9cVlmE/aR5U9EKdjI1vUpdRvXP+q8vACj7v49qn0TSte1XUIrvSJCs8bfPO52rGACdxduFAHv9K1r7QpLe1Kaiyw4b5YvvSMT0JAyOaS20S7tbcQ3xCwllkC7s7mI4yOMDB5/KoozpwgaxWl2XpZ9d0XUDqjX1wssxztWQjc3QnKnBx9awvO1nUb03VzO+4sSWLHPXpn3rvNQ1W1u5VMSoojjbbgcAnGfxOK81nvZGuJHHKbuT/hXLD3pN8pnNtvQlupJLifFxK2xRtJXrgdhXX6joPgvw1p1hfxXrXFzPb+ZPCoEuxiAVzlSAM5BGc15/u82UIgY7uVwMkj6Dmtm+8O6lYOLO5ttshYAEsO4OOe3416+EtTi21oTbXUTQfFFro815eT2VtMbgBMuo2qv+yhIGe/Ss/U2025CNou/bIxJLH5gc85x/StmztYNNM+k3dqLi6m2sJEKv5YA6L27881oz+HvEWneFYvEM1oyabPMyRT4yCQ21+Rz1z2roq+/TSjqU2raHIFVE+2RQIWwc9z3wf8ACsi6097creOuEl3bMjGce1fQmg+FE1mHzPCEX2O580BJL+X5J1BwQyBBjJwQS3HpXnPjXTtb0bxE9lrgtpHGMtavmPoOAD6ZrKpRdPZgqbtc8riaR32FQAT0xWyBdW6bTgc5GB7Vfdbf7R5s3Ax0PU49RUJ1APIzSBQq9BnrWUqspO1hMx0mJuUa6X90pyy8gH8q622WBLn7VbJ5Yz5ihM5WPsoJ+bHXvXOT3CSpgADvxWlpdoZ0NzNKyRLjcR146DGc4+gNaNSlGyHZtWRq3Er6jbeaUG7gqMZwM5yR9KZa3DzO8U68x8kj8MYpZbjTlumh09JHLqC0rcAlR823IHy8cDrU901pY4miJZphgrxkHrnjtXLKMoaIzlTa2KF+hedLpkLjH3T0BHsOPzqjNcX9wwZ2WBW53DgfiaTU7w3J2OGj+XAPqaxZCCBFJu3NgAYPJ7YFbQpuVmw5W7XNu1Sa6n2RlXWPlmIzk/X1NdBDppvM/bCSpwAEGCBj1xn9a3fBnw/8f63GINB0eTYzAtPP+5X8S+CfwBr6C0L9m3Xrh0uNe1QWYyGaK1Bds47udo/Q1v8A2biKj9yOhnPRnzBJBZWreTFll+7lyeMeuaw3sFvZxHYoZWydyRqSfyUZr9HNA+A/gPRpFmmt3vpc7i9ztbJ9cbf6169Y6Hp2nJtsLeKAdP3agfyrvoZFNO85GfOlsflPafCf4j69Csuk6JdCPJwWXYD/AN94rorf9nH4u3CAHT0TgDDzRD9N1fqWsAAy3ap0gQmvWhllNKzZf1iVrWPzFh/Zf+LUbeZ5Ftk9QZkJ/nVeX9nP4u2W5PsCTpncAksZOe+Bur9T0gjHapHgjlHQAitPqNMaxc10PxZ8T+DPFfhaUx+ItOuLTH8UiHZ+DD5f1qY319qdtFHcn9yqjbGgAXgYycdeK/Yi90+1vIntbxElicEMjjKkH1BrynVPhD4Sm3PFaKqHtGFUr9ODxWE8Ar6M2ji7/Ej8w75CdNkkTohUj9RXO3FzFc220nMg6Z/lX6Q6l+z14bvkItZ5FVxyHVWH9K8s1j9lR2Zn064jOexGz+hrJ4KXQ0jiYvc+Pbvyg/nQvviYAK/OcY9OorpXiM/gZSgyBLkflzXpur/s5eN9OhCW6eaEBA2kHP65/SsCbwj4j0HwtJpN/ZzJIH3D5Cc/Q4xXJUwso2djWnUg3ozxO2bezKQSdoWtmzBEwtmYjfxkZ6ng8+hqna209vcSC4jZCOoYEHn/APVU0BUXsbuejqQPxo1W5suxjac4t7iUHjK4q9b4E+5TmrRhhfVWY/KAxjl+nUN+OKhW2aa/eHTlaTBG0AZP1NRUV0XSlaSNZpdvQ1ctUmupBDbq0jn+FRk1eTQrWwUTeIblYOM+UnzSH244FLceMTb2/wBh0CAWydDIfvn8sYrhjRbZ6c8XFaItJpkFmS/iCYQKv8APzE+mBmu1vjZ33hNLuxXEW3KZ64U45/KvCmkeZzJIS7HqW5Ner+HLyP8A4RJrCVJTIvmAYQleckc9O9bezUdWcVSs57nIH1NZ9xJETscjjkVtR21zOOIyoPTd3z7VbTS4bX99PGsjA4HzDj65rGeJjE5J1ox3Zw13aqyeYgzj0rY0+zkkCkDnArUmklVCliisDksA2Cp+hAqOC5gtoyxyZFX5i+MD6DPNZSxba0Rg8V0SLojtbZcyyDcTgKOW/Krtre24YxlWGB3H86wIry6RzdRbXJB4xj+vWqJ8RguZpIwG6ED2rNVKr2IWIqdDtZL6WNkjCrg9T04//VV+D7PdRCSGQMB9456V5pFqv2m+86X5Y26KDnHvWvHc/ZVYQkOjHJPb8R1ovKL1LWIa3O0PiSDToPs9qvmkkjPUe9YOn63pdlvnuPvknKnqB2rNjuiblZmCsAAOhwBVK7s4pL2S6gI2yNlUPqatVLrVlKvfW5X1jxTrN2xisY2jQnGQpHH1rk4Zg12JNWzIBzg+tdbdyXENuDvBPQMM4rKkt2vXWabJbGDXRRq3VrGkKjnozPuLmW5lBtshcYA7CpLfTZ5OGzgnJFdDa2AGCFzXR2ulzyMPlwK1ukrI3jTSOZttNji7VfkSaMKkKgHrz712kOjxw/vJiFA9SAKy9U1rw9YlXc+a8fKhemaxleWiKltZH//V/SiijBoxXpHlhRSgUtADaXFLilwaLjsNxRinYNGDSuFhBRTgKXii4xlFP4o4ouA0DNLilozikA08daz7G8k1GMS2YUqWYbt2R8rEce/FeDfHn4rL4N03/hH9FlH9o3IBIB5RPw6V8L6bf6zYzfa7S8uI52bcWjldCST1+UiuWtX5XoddKgpLU/W9UmjULMwYjqcYzS5wM18K+BPjZ490OZItUnOp2o4ZJ/mfHs/DZHua+4/DHiDRvF2lrqmlsGXo6fxI2M4I61hHHa2sXLB26kyyBhkfrUnatYWcLLgg0jWEJXgc10LEx6mLw8j4d/bN8IalqfhHT/GGmZb+yp2SZR/cnAG78GUD8a8C+B2ovqfgjxNCIxI0SRMUbo3yPwOnpX6nXmiW17bSWV4iywyqUeNhkMp6gg18iah8EdM+Fra/faNn+z9XjV44RyYJED7gpHOPmGKUqkZPRm1OMoqzPn+Q6nI8m51to/t1o6bBltpWIlX6dyRnJpmm292LiNbYLGkWo3IkLfOwDREZU8Y59jUtzp9zPc3cekQPLcbrORhLkoVXyRn5uAQoz61Abi00/UFbVr3z5DqxS2jg52l432xyEAkcAnqOlY7miPS/C1q0vwT1e0urp7sC4mJl6MBleB16V5hpEFheHQpLW3klYTnYSc7cTsxPAUdeRxXr/wAPr2S++G2tSND/AGa0dxMIwc/MRt+Y7s5yc9eK8ws9bvV0rS5r/UmDtM3mBJPlfEhwoEZ2njjFOq1ZBBbleXwzrN1Z61py2EdkGKvDLPgo7rIp+6Qw6ZNaNrpt1baxo8l9qkSlbcJJBGM+YwZz8mNoxg+natAXFlqk+s6Uo3BYnLKBjaFkXoSMZFQ2Vjai80QwwkrFH8jk/dw79cd+azjqhyVjg5Phxe+O7iUeGHLmBmDzyfIEwSe2cnH614Mt6LWadLa3d1RQGbcM+aBjccj7pOeOvvX1Za6Rc3Mlza+a1jbLcFpmjdowU38liCM5FfIurR3NpqUlqFkdnxlmONpJGA3QD0OeleFiMPGNSyiYNanXSeJ7Oxs7Y/ZStyFw75UxuMkgbNvX3z6Vg67NpUkzawqPiTJiRsFUzySMAZ+bOMjpT5Ipre0ht9XO6NTsiOAUUH5mxt4PXk+9N1ayBs2a0IMCMYoy38RHoD83f0rkquStFbCm5W8jI1Ca11K3VZZmK7QAT147n2FWbHTrXTCkxV9w53YDEjtx2x9axI7oaY8e755gQwDAYyOmRivY/CsmgabplzreuCSa9u4NlvCEYbRuBZ8Y+6Ox6Vz1nJRtHVEKN3YqQ2iatpEd/qFvJeb5fL3wMI3ULjYCSG4OTzXOeOY5bERG0+SCUZiV23Mqg45OOfrXqmr/AA4g0rQofE73bXVneWxeERSf6u5x/q3QHgdDkjjPWvP/AA54E1XxzrjxTnNrDE0kjhgwj29QNpO857LnJ7VvTw80kpa9TqlSbjZHn/8AqbONI5QxkJ3R9WDfl0OeKn1XTJdGtEtr2Mx3TgSFD08twGQ49TmvWF8G634L8SW8Mlv5dwcyWjSxiNZtuDyJQB8vXtina54A8Ta1Z3XjTVHcy3UrZeQgRERgDajfdPPyrtPauiMJN8tjHkcVqef+BX1DTPFVjeaFaxahcsB5KXMe9QzKePL3ANg+pwfSrfiDTPENzrVymt3Aju1O5lX7oxnIwBwewHv1p3hm21vQ9Vju9Mke3nB8tXUA47MeQeBzn8aq3lzq1lezCNgsksxbz0ABLZwfmXsc8iu1uCguZGLbbsiokc2nTfZArG6ZNxIx/q/XkZB+hrpJfGlv/wAIE3hC3muhEs3nReayPGjHBZQpTP3snOR16Vhvp2valp02pyWb+VDIqzXKR/L0yBuxgd+B161i2uqR2Mc07QhmZ8bHGVZM9cH2rGFZQTjFj5e5SsNd1eO98y4upY8fdIJCgnvtGBitHWFsxBBcLM91csXaV3zjBxtGCT055zznpxUV3fpeaaAY8zRsqJIuABH3HrkcYNZZd7u4jjw3XBbtgdKxrVHaxUpu1jnJTLc3WX5HSobiFXbC10Os2Sx3kjWX+qBC4znBxz+dVbLRdV1WUpYxttH33Iwqj1LHgfnW1B87XKZ6mACEiO7qpxx6Vr6Vqtna4e6jaTH3Vz8u7tuHce1dNHZeENGj2Xkpv5uuyInZn6jj9a07bWrK7haGxtEtAvGAByD0Oa9qjgHL4mO7Wpxln/puo/u5GwuXXIGAOpyMYr0CeaTxNPbxWFlEjInlRJAnzSHruYk8k4rP1D7NHYLeOoBI2uQMHB4I4r7u+B3hfTND8FW1zBGPPuQZGkIG/B6Dd1wMdKbymU5cvNoTOpofPXhL9nbxRrsS3ni+SKwjYgrEq7pdp/IL+tfSvhr4H/D/AMOiOSOxW5mj5E13+8bPrt4X9K9aAjj6YGaGkx0r1cPl9Gj8K1OXnYRWkECCKJQqj+FQFH5CpiYo8BRVUtnqc0nFdvoSWDNJ/AMULJJ0ZvyqEcUtAD7nULLT7SS/1GbyooVLO7dABXz9rf7UPhLSZvJ06znuhnAkZhGre+MMa9H+IWl/294QvtKUFmeMlQOpYdK/M/VbG/uITE9rLuj65jbgj8KynJrY2pxT3PsuX9prW5sGy0u3QH+87t/LbTI/2j/FzHH2Oy+mJP8A4uvjvTV8TS2KSWFrPJGcgOsbMDj3xViLTtatpftOoQ3EAc/6xlZR+ZGKyvI15I9j7m0/4y+NL2MXI0RJY253RlgCPbJNaE3x5sbB0i17TpbXecffBHP/AAEV5d4F+Pcfg7w/badqttNLPZhkSSH5kZCSRlRkZAOORWj4m+Nfg/4i6Zcabrum3EiOg2MyHCOpBRwAvBDYyfTPbNL2jvYUqaa0Pa7b4l+FJE815HgTGT5gGB+INeg2bQahape2jLLHIAyMp6g96+NdP2zQKSPlZcY9q56/8F31hvvfCsko38tbrKyde8ZDLg/jVc7WpmoJ6H3a1pE3UVnXmjadeDbcxJIP9tQf518HyeNPHnh+YR2eu3dqR/y737NkY6/NN8p59K6iz+PPxL0/bHqBtLzd0JWM5/GLFZ/WI9UV7F7pn0VrHwj8CayD9r06LLdWUFT/AOO4rxvX/wBlXwhdkz6NdXNnJ1UZEi/kRn9a1dN/aLl2hdb0lw2cZgbP6Esa9C0/44fDfUMLPeGzc9VuEdcH3YqBRzUZ6CXtI7HxT43+BHijwZdyawg/tC1cfM0S7SvOfnUk/gc15Bbw6zaRz6vo0DrDu8p5SudpABx2559K/XG08SeFdTQNp+o2kwP9yZD19s1cbR7KJGMMCRiQ7m2KAG9zjrx3qZ4aDVkaQxMou8j8Wpr+W5mLzM0kh/icnP5dqvJaGZ8g/wCNfq3r3wm8C+INz6jpds7sMb1jCP8A99KAf1rxnWv2ZPDvzSaFNNasOis29fpzk/rXHPBzjrE6YYyN7M+JLTStp+SPcfU9K7a11GTTdHezI8sOxZmPYd/5V6TrPwa8d6Hu+wQfbE/vREZ/75zn9K8F1uDXLKdrXW4ZbbJwwnVkyOw5xxXj4qlVvytDqV7q0WXpfENv5SyomyMcBiTnnpWVJe22pbsSMhyMHOA1c5cXU18UtcbtpwoXgCte28NX8kL+YB225xj3rCOFS1ZlChzF2TU44xiKNQ5659RWffwy32141MWcbiDlT+HX9a07fSdA01WOot5j8Ecnjjkce9Y11qtsqmOyjCDGBjPSrjhtVKJqsPbUtv5lkUhu921gfuEAj68VzV8bZflt2Lcnk8GkluZZSWkJNV1g85/kBNdPs1FF8q2SI1meNgV7VrW96+BGGIJNVl08gFj0X+dXrG2JlB25459qxqW6mTp+RbeeeMq9sxfcMMCB/Sp2mmWNfM2ox75/z2rYsIohKiyYALfe7YqHWNKkN8kNriRCMbsZHufYVlyxsDp2RhvI8cAZvnU9Aa6HSLF7nbIVwjcZ+lYcS2luyh2BAyCp5HNaEus3enWHl2UqoCTg45+nNEV71iqdoy1Z3jQ6dpkfmXBC49a5nUPHtpa5TTo9x/vHp+VeX3k17dSFruRmY8nJqERgDivQjS7nS6nY3dR8UavqZ/eSFV9BxWA5eQ5ckn3p22lxW6iktCLs/9b9K+aMU6ivQueaIBRgUtFACYpaKKACiiigAoopQM0AJRS4oxRcEJXm/wAVPiDYfDrwnPrEzA3LLsto88tIen4DrXZ65rOneHdLm1nVXCQW6l3J9uw9zX5f/Ejx9qXxN8RHUrnK2sTMLeLsF7E++Kwq1OVG9GnzO7OSv9X1fxXrM2vaoxeadsnPOB2FdBYae5IB5J6VHpdhtAIFd/pensxGF64rxa9a70PWp07al7QtFMjqretfS/w2lk8O6mJYzi3kxHIOgJP3T9RXG+FvC6LELhyST2I4FdF4i1fS/DdmlzO+yG3ZZHPckEAf/Wrni22XI+sk6VJivF7D44+CGso7jUGns1ZA2Z49owec5BPFdfpvxM8B6tgafqlvIT23Y/nXpKSORxZ3BHNeVfFnzRoSNG4Qgty3Tp0rvn8Q6HGu97uED/fFea/EnWNJ1LQjHZSpcMhJKoc4BHWri10Jt3PFL7w1oviHRWt7+JyjkSC7UkEOg3qGH3uo5wCMd68z1XwBqttqll9nWGRr3Vlf5MMdio+9hnGGwa9ht72ywBLdpbytBnbjMUilcc5OcnpxisbVtU0rTjpVzGssZt9TjkcN82DIrRrgcEgk85btWTnK5aRmeDfC2v8AhrQ9f0fUoWMsksjoHydyMqkYPOSBj6V8rG/ePwzpwsbR2KXUi4mDKynqcjacfSvva08SaBq2qXbJPcSpby/vy4C7cov3AO31NRvqXgPX7O9fTHtJoHibaZECjfjnlSPm75rWcvdTZMfiaPkXwmNYbx9rkeoCEQNFP5RjKlyd6kbgPmx68V2NpaSPbWDGTcRu3Y6H5j/SvdNT8EaJYxy+IrHT7WC8ktm3SRSuzEOyA5UnGTn0rye3t5RaW6onyq0gA9PmHenTdyZvU634aWiQ+L3VlBBnBw2MZ38cDPSuYvvDmhT3evW09sfnEvnbepxMpOD9RXWeDFNt4tMs56yZGOp+bNad5YTJrWpeVdw7ZRMI9x5GWyN3y+lVUgmlclas8btfAvhiTS7ae4gMkSNIIlb+EgpuyffIryLxjp/hQeLNQsXtpgiK8hGRsU+WpBj5/HHHNe/T6jqK+HWl0mW3eWKeRWSUkdVQ5AA9vavNho0+r6iNV1a/tWguIC22VhG6OY1GCoQ8AggcnI5715+IpJpRijZK6Z8lalPo+oQZszskyfmfgkehH0r2rw1ZaLqNtZaVqMsGn3FrAzGeUO5aNiqlcxox5BPH41st8B4tS8LjxJZ3UP215gAFkBRkZST/AAjnOMcdK8f8WQfEHwrZWct/CIbfbJBDKUwW+6W5yd3bBwK4FScZaIytZ3aPU7n4Hrrkt1f+GtVtJLaAoGOXSLYw+XDOq/Pj7wIFeF6ldah4aku9AmhiglWZUlkjbLARsMhGHVSRnIPIr0z4WWx17xJa+F7u/MenTPHcTwyEqsx43bnGCu08ADrXtHjj4M3WoeOh4w1R7e7097uJZIIAQqQIAo8wg5AKqM4ycnr3reHNLc03Ob8LeJPDEmmJqfjuS4kghuI3EDDcsrfeSRXzkKu1gRjnIFeq/GS11yC00/4l/Dry/wCzryBHmRcLsEQwAy9cEdTjA/GvnL4uXnh0eI4bfwLu2WiN5cCofKjVepYMzMzHIHJwPSvJ5PHnjBNLm0me7kFvcAh4844OflA6AYPQAVpGSi9hTas4s9P1/wAe+GYL+x1zQZG+1yCR57OONkhRnDARgYwwPXI9elcJpmtapDZve3AKyK+6JWPyqSfmOD3xXmSXN5LMLiNj50RDLgDAC9Cfyra03xDquqK+nTokhY5MzDlAOW2gYHPuKzxcZVI3fQ51G2p0Oo+JNQ1S0ewSV1ti28xjhWf+8QO/v6VzMWm6vfllsY2dIWAdlUsBnpkgY/Wtq1gS4uUtImEayNtLt0A9a9f03Wrjwros2mWkEDxlgTEM+ZKUw3mFuy5GcY7VwUmr3kOC5tzzG40/w1Z2Ysy8kszYMkvSP5QSU2jLZY8DKiuXmfTzL9ntJfs4JAG7JAHOckDPX2q5q9yssxki/dycsxHdj19q54zWZtz5il5d+Q+f0xjv9e1ddOUJ/ZJcos62wvvDy6ZJNd2zO8MvJQgq54Chc4IGeTkd6ytS1bUtYURXbBIF+7BHwg/xrpte8Ot4c8L6asyAS37PO4/ujC7QT3PGa40CvpMHQUYXtqRN9iERqo2qMVdsOLnb03CoArOQq8mtqw0W6uR5xPlqD94/0rsbSWolFsNWDS6JLbJ1Drj/AIEwH9a/Tfw7ax6L4dtvtTiJIYF3FjgKAM8mvzh0TT59f8Zab4W0seabq6iEnGdqRsHcn6Kpr9QJIIpIfssqh0K7CpGQRjBBrag09UYVdNCjb6vaX9qt9pp+0QNkrKn3CAcEhj7iuT1j4geH9DUvqmpWVuB1BkDsPwTJrynx98EfE+rkx+CNefT7TB22DqfLUkktsdSGAJ5wQcV8l+JvgF8WtIZ572za9Qc+ZC5kz7/MBW06vLtEyjSu73Psi4/aE+HsDbf7ahJ9reYj8wlSWv7Q3gF87tTtZfos6H8niA/WvizQ/gL8QNUg+3X8Cabar96W7bYPwABJqprnw0t9HlEUGoQ3hA+ZlUqufQHJz9eK5nXl2OhUI2P0L0r4z/DvVwBDqMcbdxIQP60ax8Zvh9pduZYr5bsj+C3Bc/mcD9a/L280eW0UuI2x6r7VmWdnq99L9n0qGWRz2TNR9aa3H9WW59w+I/2kricmHw7YhF6b5iM/kM/zrxbVPiF4y1edrme52buyDFeSPoviXQWU6xBPbh+V80cH8a6G1ufOjDVpGSnuLl5di/darrM0JWS6lI9NxxisOSW4f5ZXZvqc1JqOrWFpCySON5GNo61ydx4lJXNvD7bmP9BQ6sY6Mai3qdESwq1YEG8RHbarHB5xXCLqmrX8nlwnH+6KlXR9XkIklc5HvUOq38KG4d2fRuheLLXQLJoxL55ycJnPp37V6TofxJ8PXMKC9lNvKeCpVio/4EBivmXQdDnWHEzYGepqTXruz0yJoIWDuB93PWm3pdkNJ7H3djStSh+z3qwzRt/C5Vh+Wa8K8ZeHrLTluls7OGJUkBQsQPlburYx26V8y6brF1chpHuLiPb3WQ9h6V0MF/rGpQG1F+7pgMVl+YdeOc5riniYP3Wa06bR31vp16UEwt3VNwXfDIjDLdBjcOTW9eaTq1vGT58U6g/dmHzA9MHG7n8a8ojuvEWgStbq6kLtdl3HBBGV657HtU2reLjqa/adQgnjmJGXt5AFPvtKn+dQmma3O1v9Bv3+z3L6GTEWwJEdSJDjsDg+9a3h/wAT6no8kix6lqujmNsbCGaPH0LKK5bwt8ULDTnaPUZ7uRUGYElVdqP/AHuCM49O9ehQfFfwVp4W+ZE1Ce6LRyRZ2gfdw2GDY79/wq426CZ3tp8bfE+lW4kGq2WqoeSk0UsUv0ysbjP41v6Z+094fDmLXdOuYOf9ZblZV/IlW/8AHao6j8P/AAf4h0qK40mKFL25x5RRzsDEZ2tg9c8ZA/CvmHX9GvPD+pPpmpxG2mQ8rncCPUHjI/CtHUnHqZqlF9D76034xfCvxDEps9Sjhl7pcI8J/wDHgBn8a6e50vQvEVqY2EF7Ew6ArIMfgTX5htHBLkOM474q7Fe3mlAXGi6vPA6gEKpK4PpyWB/KqjiO6JeHXRn2Nrf7PXgq8nN3pkP2KbJP7scc/wCzxXB61+zdPe27LpGqGC442+apKEe5BJH5V4xYftI/E7QJEhNzDqMSEZE8eCR6bkK/nivbvD/7UmmX8Sya/pTwZz89tJvGf91gD/49S5aEt0CjVjsz5J8d/Dbxr4FvGi8TWrbMnbcRHfEw9Qw6f8CANcBDBLMcRrX6sWXxF+GHj3Tvsb3cLlxtMFwAp54xjn+dfMXxO+CCeGVfxJ4VzLYZy8QO4xBu4I6qPfmuatQUVzU3obUa13aaPl220d2+aSuhttNXAAX6Yrdt9LLfO5wtTXOuaJo8ewN5sg7L0rzpXZ3RaRU/skqgymAeo70rw6bYIZLp1RSOQep/CuS1Lxnf3RKwARj8zXHz3NxcnMzlvrVKhfcTmdvqnibTmVbazRiqdx/St/VtMutK04XsH7yKRFY+gVgOv515EExzX0jZH+0/h/CW5Jtgp/4Bx/SpqYeOjRjKCk7niN3bxlBdRD69v0qJS0qFAcbuuehrUmgZSUXoexrCvkMbAjis1SlezJ9mKumXOSp2k46A9MVUmhkgbZIpU+9a2jRXNzeIsYIXPLdvxroJdFivpPPuZPKVMhs/41vGcoy5ZFJSODIJOB19K1rPQNWvyDBEQPVuP/r10jX3hrSF2W0ZuJPUcD8+f5Vm3fi3VJx5VuVgj9EHP5mtVKT2RVktz//X/S2ijmjmvQPNCilApcCi4CYowaWlpXAbg0uKWii4CcUtFFIAprukaGWQhVUZJPYU6vjP9o/4w/ZW/wCEB8MzHzWXN1KhPyg8BOO/c1E5qKuXTg5OyPLvj/8AFa68a69J4X0ST/iWWbbWZekrr1JPcZryLSbJztLjNZ+l2GduOn869K0jT9pDsOlePia57FOkoqxd06xXGWGBXrXhLw9Ne3CNs+UMKpeHfDVzqTLlSEPQ4r25Vt/DlgIVxvC5Pb2rginJm5Fqmp6fo2nSIZFjjjGZJCcBQOTz7CvlHWdZu/iNrimHcmnWzbok6eac/wCsbPUDsPrXpHxC0bUdV06yMs5W0km+eEZ+YrkgsfTIzjBqpoejxQbQi7BgA8da76NF9Tlq1eiPQPFvj7xNJ4En0SyEZdbTyIwIwxJCYH3s81+e+qW/xBuFP9p2M5x3W3A/8eVRX1948lx4a1KGM4xC2P8Avmvz7tNT1O0Aa0uJYz/sOR/I11ckexhKbRsS3l7BL5E0k0Mg7MzqfyzX0f8As16rqN94g1ewvLyZ4VsdwEjlgCCeRuzivm248Ta1fKgvpjcGMbQZfnOPqete8/sx3ZPjfUSUDMdPb5VwucMK0jFLYwu29z217eaE+bK32iH7HHm24BYjGWB69uMH6V2epxMb5numxGJLVtj5XgM2QoOMkD05rIMpMMcyARj7OQkg5kwAflPfrxVrUbZRLMY4yyMls6vjGGEmcn2PFKSR0RfQ9B8OXkd3qN4miIGZSoAkXGfl/iHBrg7DTfCGqAQ6jZwx2wmO5YkI+cgAtg5rp/C27/hLdVi1FcIwhJMfOf3Y6Y/CvHrifUBYXaLc7WFwQH5LKuQMA9jWVSLcEVF+8z2C8/4Riy1BLbRpZWuHDee6EBVUDgHAByTjjNcow82EuzOzCRupbBHGBjp61uaJ4shgjj8ORadH5s0a5ujgMTjOSQCe1UwJY4WAwP3pz+nriqw6fK0yKu6sX/DpEHiBZI4hGA2QOAa1/EUcD+KtVsnVldxcbmQgH5lY5X39KytNLx62kzSbhxjkenTgmuo1uE/8JtcCKZgjl9oJOctG3b61tNaEw3Z5J4c8F6baQNqDS3U8vnsqmSdiu1kHBXO3PB5xmvNvFdhZR+OLSLSLEXd3LFEGSdwUIMaKABkc8d66Pxv488Q+Fw9noFu95ISHklXcY4xggAsRjcSeOe1eE6f8TPGt7qFq2othjJHCNvzyx4IyxUc45zXm1Ki+FI0UlsY8l/ptp4PufNaWC7W7UwqsjDYFB525x17kV5VrHiTxX4iMd1rF3dXkduBHGZCWSPceAo6DOD2/lX0bpGkR3HhLU7e9mtmu4HSSLDh3GZFB34zzgnv1ruPBvw78CX1jp17q0ksMkJcKhQuJS4wwKpubAwOSuM1GHoSvYibas3sfO3jTxFaTWWl6X4ftxazPbRxTRjO55MnDMCSdzE57AjFdV4fn+LcGu22kvPJpCWqRQ3UqApEqfKENxjgk/Ly/U19BRfCXwpea3fzSWk5VIFhiklHliAAEh0abZjAOeOlepfDzQtasfCkWjafJA9k53G+LNK8o3E7lBUZP+1ux3BNd1PBa3Zm6tj5N8PfFG3sPFcenahZWv9oTGWD7csbOcyKAHMbFtxJxgBeo9K4LXPh98Ttb8UXyWto8rO+4yNEqblI+VsBQEyCOABxX6BWnwm8Dafqz65JbfaruSUTGa4xI4cArwzAnGD0+ld9cWcs9sXBSGFV5dztUAD/CtZ0UovmIjK7Vj8otc0W/+GkraPr0KCRomO4Kp3h1I+9zxk9O1cTo1rrWuatFb6PCis4ZflUIgUDJJ6Dgc81+rN5oXhfXPDUuqzQW908heOKaWMEqydwWGeo4rnLrQPC9zaiwvtKDxADiMIBxjscda4oYCc/evc0nOMZNM+IvCfhCJdS8jVD9pMxMdqkRUqzgAuXIyAF4zyMZHrWN4rTSPD9wkVhqCXNyMpMYzlFUcFcjrn0zX2lrfhDw7qIdobe9tmli8ktGAdsY/hXaeAepHevFbr9nrw0Wllje7YyD5C0Z+U5znqazq5TNvRE1K0LWSPlzUbjT5cSwFWJBzt7fUVc8E+FJfEepoeEtY3DO7EKCR/CM9TXu9l8A7XTLo3NxdGWLqFaEg/ma7yXwnqllp3l+DbKHyI/nvLl/lfYOw46596mjl1Wk72HS9ne8meVfG1Vkt9LuUHyrvXjt0wK8WsdNub9tsKkjqfavoXxRNpV7okiakoYQupXPbKqe9eZ6dB4j8U3Q0bwVYSXDHgsBsiQdNzucACvbjWduWKKlTTd2YzW+k6HEZ7plZuuSeB/jXZ+Cvh38R/ixLu8M2zQabkK15KNkeO+wnGce1e5+Af2fdL0S6XWPGksep3o+ZYcZgj/Bx8x/CvpC3nlsVWO2by1QYVV4UAdAAOMVXsm/iZDrJaI4fwN8GvDnwuGbNGnv5ExLdSnc5z1CngKD7CvTI7S6uBmFGP0FPu/iBp2hQed4leONQMgkjcfovU/gK+dPiB+0/FGGsfDQa37eYeXI9lHT8SK3eIcFZIyVBSd2z3nV7iz8Owfatdnitl6jzGAJ+g6mvnjxh8erTT90PhsDcDgSyAk/VV/xFfLureLPE3iq7e4keT5z992JYj654FZFo2hWcoGq3RDZwdiNK5P4DH5kVl9YnN2RaoxidhrfjTxN4rk86+nkf3kOQPovQflWz4c+GXizxOBc2tu/lH/lvP8AKn/Ac4z+FfTvhXwZ4C8L2ceqI0c8jqGWWbDHJGfkXnH4V0lz4hnu8xabGSoH+sfgY+np9cVXslH3psn2nSKPJNO+Cvh/ToRPq7NeTKNxUttiyO2BgkfUmuk8L6PDpKuJBbxM2AgtEChODnkZyemMk1keJfHvhDQA0viDUkllX/llEd2D6dcD865S1+IHxF8WMIfh/wCHJktz0urlRGpHrmTb+maxnUjc0jCTWp77ceGtM13w+2ga4DfQyKw3z4Z8kk5DYGCM4GO1fmV4y0XUvCetX3hyInzLWZo8nqVB+Vs+64Nfox4H17xZFdnwx4+gSC8K+dbyxENHKnR1yP4lOPzr5k/aY0J7HxtBrSLiO+tkyR3dMof0UV1U5KcLmDXJKx8XzwzpIRMDu75rrfAqaZca2NL1xd1tcqVyeNrDkEHt3FbkWm2moT/Z7jjzFIDehrlNZ0u90K8Ec3Kn5o37MB/WsnTcGpGkpqa5T0vxJ4I1bwZHLNZxtLZsd4mUAlR/dYjpXD2up2cswh1KWZCeNsQ5z9SCMV9W+EviJ4Zl8H2+o6/PEmY/Kljf5mLL8pG0Ak569O9Zdx8FfC3iwL4i8H3qwxXI3opUlOeuMcj6YrWpTT1gzCnVcVyzPnBWuQvl+fJ5fYZx+eKqXFiHjLcHH519A3H7PnjGMZsJ7W49t5X/ANCUVzGofCD4kWEbeZpUkqgHJheN/wCTZrF052NOeD2PDpIzbsssi4BHbvU1rezW4/0WVk3feAPB9OKm1O01PS86dqcEsJ6qJFII9xnqPpWAwPToa53E2SLOpXV1eSGSeV3KgDJPp0H4VUVboukSSN83IAPTvWhhZbY45bPYdqraehNyA/ylRt57dqCrM1ra61FEMR2SAHOGUHt69aiv7yLzxJ9kQYXB2huv4mtW1tZv+WJDY559On9aseVLGuTECuecdaLkamRaa7HZELY3FzanOfkdlGf+A4rQuNbv9RZZbi/Ny4GF85yzAemWNcvepA1w2wYBPQ9az3gUfdxQUmd39qv9u5lJ915/lWPqN1uC5ZlbpzkGuZSSeM/uXI+hrQXV9RUbZGDj0cZ/nQUmjVsbq1EoafhVGFA6c8Emr2n3ESTPaq2U+8n9azY9T018LNDsPcpjH5cVZij0qebzYLryePuuCP1GaB3R0G3cOcEe4re07xZ4l0U40q+nhUjaU3loyDwQUbKke2K56Gxu5Bm1aOcf7LjP64plxb6lbAtdW8qKP4tpK/mOKliKGsajql02Z5WwxJ+QAD8hxXMmEltqksT3rTvp98gRGBVh+WKz1JVualRSLuylJlHMb8EdqZu9Oa+gtE0LwB4s+Ht5Ysyw+I4Fa4tn4BmVAXaIscc7eACe3FeL2eh6jeti3hIHq3FJ2W4c3QpSR/uUkx1/nXvfw+mF34Pa1bko0iD2Byf6158mk6dZ2iQaxMg25JCnJz6YHNeg+ANU0udbjT9NQoqYYFgBu96wlK6saI8+u0CvtI5qrE+nQOZ9STegHA6810mqWgiu5oyP4z/OuVv7cmBgc9KlK43sRXni2cKYdNjSFRwDt5/w/SrPiW2mljhuoVLh13nA4AIzk1zlza2iWKTRCQsx5YjC49jXeob+68IW02msRIP3bbW25UDaQeR610ezSaM3UueZQrE7FZW2DHBxnn0pIV5w1aGnxQvqUdvffu4zJhz6etN1KKG21WeC2YNGkjBD6rng/lV8ulxKR//Q/TCil2mjBruPNEopcGgCgdhKKdxRxQFg20baKKAsBWkxS1ynjXxhpngfw5c6/qTqBChKKT95uwH1NS5WRUVd2R5n8dvipD8PPDZsdPO/Ur4GOEdkBHzMfoK/OS3hudRuHvL1jJLKxZ2PcmtXWtb1rxtrsmv61M0skrHaD0RSei+groNK04sfKjHA715WJxB6dCjyot6XpYwrHovavXPDPh99RmTghOCaydD0RZWRGHfnivobQNM+xRowXGegxjj1ry9ZyOt7Gja29toOn/aMjK4Az2zXE3l62pXZvCSy4G3/AD/KvLvi34vvdYa78M6FOY4LZA91PGed+4YjUjoe59q9B8PxPLoOnzuOXtLU98n9ymf/ANdenQwr3OWrWsaHiW2dvDunK/GZ3B/J+KxYICFXsQRxXX68jHQbFz8xFy3Pb7knT2rm1GzvzkV3xikrHHJ3Z5h49k8rSNS5wPLYf+O1+eqP8i7Tniv01t7HT9Z16TS9TiWeCRirI/QjA9MV4dqGgfCSS5vLW68PvB9kZgzQTSrkK+35RkipjG6uXU6HyJGP3e7PJJ4r3/8AZon2/EG5QnYGsJBkdfvL/jTPiN4A8E6N4GtfGnhFLmP7TciEpM+8bSjMeCM5yBVT9m9j/wALMCqAd9rIMH/eSnaxifU8KKkKPGDv8mQb2+7xu5rW1OSQJK1w+1mt4Wwo+VsSDgdemSe1ZQ89LdQGBjxOPK98vxn0zxWleyxSWzLCvP2FWdG6riReR39uamex0x2O08LbY/FNybIbQyQlfM5wQnf8c1xaaWkt5c2rbVBuvmx0J8ztXc6YkkfiCSS/IAe3hJZeMjYBxj0rnbWfTbTUZrkkyxLNvQAZwofIz16ionFumkhQ+JnaXWgeG7bM07M00fyoQTxjjsPSuEC2oaQqrMQ/XsPzNdjq/jIajcpDaQCFJH3AcDOex46Vy00k4aYrGqgOC2cnkjtgipw0XGL5h1JLRF20lA1BG8vAAHf/AGa63xTP5His3CwtK5RCEQ/eBj4xkdcH1ri4fMGoQ+bKADtOAFHGOmSM123iW/nsddg2XREJWJjkqSvygkAkZ4reautDOG7Pk/VvH/i5La6KWsVrZNIgJdDI6MCwBPK5zk9Aaw9cutL8Papo2rzRvJdFFaS4hx5T4uJDvKFc5x2Br6FklttXu0u9VdZZICfKJCgANkHgDBz715F8Sb+PQ2iFonm28DF1gXHB3kkDA4z1+tcM6MoRbky762Oc0dNL1OLUrlCSJsyneQDtEingADvjqa7G38G+J7rRYdW+HToNQhDRvJPICEifGVRNmCzepPGK+Yr3xAmta1KYVktJiGjjtWJUEdcFhgnBA474q74K+IHj7Sr6fTNESU3BZMxhpNhCk8Fc85z1opV03Zoibuj6IbVfE2h3EHgDXwbuW9aJ1m3bWDNw8chVSMccECu+0vXvGmlyaloVs5utYtUEcFpEgS2QEBV2sxLHBI6mvUPB/marpEPibxFZLYXJjC3DzfwFMgBGce2ePWsbXPHgDvD4aiWAt8rXRUea46cHtXVOty6Qd2KFCUtZLQpWUviLw/8AZ9X+Kd/Hc6lFuNvp1gu2JWYYLSyNktgemPxrn/EfivVvEs2bsiOBP9XCn3R9T1JrnpGeWUzSsXc8lmOST7k801/uVzay+J3O6MIx0ij1nRiyfDuBF/iuJR/48aeADyetJoilvAFt6C6l/wDQjQpy2K9fCr92jy8T8bJgKfGPkFIMAZasDVFu7u1mSwkMTquVx0OOx+vtXSznNaa/hjJt7dPOmP8AAMAfUk9B9M1n6hDqFxptwbqRVCxNtijGFBOOSTyT+Vcxa+JfEmmxiKfSoJFA5MO5Sf1bNX7bxvpOr+fo0sL2t28Tfu2OTj6YGBUNpqxSumeOeBPgXaeP9S/4S7xVdPHp8bCOO2i+9M0f3ixI4APA+lfXel+FfCmh2f2XToGhhjGeGGT9eM8k1578PLpdO8EWTMRGhR5GZjtUZduSelcV49+N+ieHLN49PkWQ55lc8M3+wufm56c1x2sdibbPabzVNB0G2kvb0JHEDks+SfoMV87/ABC/aN0zSka30GGNDg7ZXUs7f7qg4H4n8K+S/FnxX8T+LJsJIyIM/M5yfwHAX8Bmqvgf4WeL/iJeeZo1vJKm795eTbvKXJ5O8jBx6ZoXNJ2iU0krso+IfHniDxNcSTyN5auSWdjlyD+GB+Art/Cvwd1O507/AISTxHMmnaecHzpss7k9AiLySfcgV7ndfCvwL8JfD51/UY/7e1JRhDcYFqj4zuEQ4YDtkmvnLxh8RfGPjGQ3ciT3Cx/JGI0JRM9FRVGB0q4wj9tkc7atEl8Tal4a0lTZ2G9LUcDdgzTY/ib+FAewGcDvXk994jLQEadCI1Y4UDkn8STWNqllrj3OdUilikkOFikUiVj7IeTX0d4C/Z61HVNDHjLxXfjSNOEJl3IA0wUeu7hD6jbmonWUfhKjTvq2Y2g/EbTvhz4dSyvmfUL9/nCDiOPgfLnqcY9K4TxJ8bvF/iUG3SRLS3B4SMZz+J5rkNabSra8mj0NGkjOU82Y73YA9eema5by3LYVfwAoVRyWouVI6vwvrC6frsGtSjzbiCRZFMnIypyMjuK/V34f+M9N8deH01OzASUALNEONjd8e3pX4/KixZZz83oD/OvTdA8QeIvCjW+peHbqW2mZAX2k4OcYBHQj61z1afNsXGT6n6WeOYPsZ07XV4NndDd/uSA7h+aivJf2l9CW+8Ex6ug+aynGf91yF/mTXgD/ALRHj7UdPbQtZFtPFKQrSeWA/XqCuBn8K+wPHFmvin4T3gHzNcacJ1PX5hGHH612YBSUXGRz4i3MmfmvBJ5cscn91hmu51HQovEul/ZGOHX5429D3/MV56hBBA9OK9P8NXBlgQk9iD/KvQilJNM5ajcWmj55niubVms5v4WOR7jg/wAq+0v2fNSe48JNYvz9mlKqfZiTXyr4w0qTTNbkt3zz8wJ7hiSD+VfTP7PFu8Ph65umGFkmwPw4/pXJTVqjRpWlzU7n1Nanin+IHjTw3etK7RgwOu5Mbhkds8ZqtaEkjFeC+N/El7c+HPEmmag+xoJFkt9pIZRjBB9AcZH1rWpPl3OWnHmPmHX/ABBe65ZRR6qd0lqgjVuMhVwBnA5OKwt9rNaobiEMQ2Nw647Aj86p3E7zyyTMSTJnPPqc1Siklgc7WP4/4V5k1c9KGx6DP4J02WzGpWEwS1Me4vuJYP3Urt/Ko/Cfwu1/xBcn+xprckIXbziy4x26cmvo79nLwX4d8UaLq9jNNHLeyqPKRwuY1ZfvgHkfNkcY6V4/4j8deIPDMtx4MuILdJ9PneEXQjBl2hiOWOQxGeCRnHesqamviG5PZHIeGvCfijWJpILC0SR4xnZ5gUtjsuQf1Iqz4k0PxH4WtA2u6bPZrJkAvtYHHXlSfWuc0bxjr2iXf2vSbgxygcMQDjnPRgR1AI9DWn4i+LPj/wAV2a6Z4j1Ke7gRtyo7ZXPTOK3ckNNnl8km4kkckmqjDjBrqnW3BDSIrEioWsdNc5+YD2qVK4zmGVVIZDUkYY89c1oTacAw8puD0zUHkzQ8Y/KqTGQlF6EYqFo+as7m/i/Wmkg/eFAWK8bSwtuiYrjpXSad4y1zTmxHICOhyAcj8c1zn8RqFkHJoGkdnrPiOz8QQx/aoUt50b/WID8w9CM4/IVifZbgjcnzL6jpWHtI4PStDTbyW1uFjySjHBXtUVG1G6GrmlY3xs51lAw6MM8+9aN74l1OYNAhWJOm1R/U1havGILstFnJPIPHP/16RAZF3Sdahe8uZoaLEVtd3cT3SjKJ94k16J8NlW31wxgljLGQxxhQQDjHrWP4Ufw605t9ZVmZ2AHzbUx6n1P411iahp48XW0ujwFLUSrEGGdoz8pwOnfrWjpJwcifaPm5bGn4hjVNTkGMbxmuOuYw4KnuK9J8YQ+XcRSf3ty/yrgpYgTXLE3RzF1qKT+E4tLI/eW87DPqucj+dbOgBrzwfeWkYy0Tggeuct/7LXF38ckV1LGMhS2f612XgR3239mTgPDuH1BC/wDs1buV7XM+WxwcokimKTqQwxkGrGr/AGZr0y2aPHE6qyq/XoAf1qaa2vL69eNVeaXcRwCxPOBXdSeCdc1GOCfW3isI4oxHmU4cqOh2kg5puSS1YWdz/9H9NOaTmnUV2nn2G80c06ikA0ClwKWigBMCl20UM6opdyFVRkk9AB3oY7FW9u7TTrSS+vZFiiiG53Y4AFfmJ8VviHqPxN8USSxO39mWzlbWPoCAfvEep6817D+0D8VZdeu28D+HX/0WE/6TMp++390ewr5707TeBtFeZisVb3Ud1Cjb3mJp9j5hEES16joWkLEgB61X0bSQuCRya9i8OeHw2J5h8orx3UlUlZHfpa5s+GNESCMXt0vbIHrXGeO/HU09wPCPhubNy+ftMsfSFOhUMP4z0x25q/418Zywyt4Y8ODNwV2yS/wwgjnHq2OgrlPD3hm3sUBUZbqWPViepPua9rA4Hm1Zx4ivZWRj3Ghw2Phm7WJQB5WT6k7gST7mvW/Cw3+EdKbGQ2n23Hr+5T8hWDrkCJ4eu1x/yyP8xW54NOfBmk7v4tOtePX9ynfsK9WpTUGkjgU3Lc3teyPDdkyngXZ57fck6VywAz+VdZrabvDNuzcg3oOf+AP09q5VnBYY6Diufuavoc5pronjRe3zjj6gV4vrGsw2WvavZyTP+7kkzuikKj9513BSCB7V7DaSbPHCLjOZE/kK+X/HVnD/AMJxrJNs7N50jZiYEjLZ3YbAPuKiGzKlqzp/ik/2n4HWc0bK4GoIQyAgYMb9AQP5V5j+zrKY/inbFuFMLjPsXSu48VAv8AEysilNQi/1mMn5W6YPArz34By+T8V9NHXcSmPq6U5bmdtT7Q8m1jRDIS7ZmClO6tv4JODkA9qt3szSaa1wjpHixkEMiEBsrtwrEc4PXn0rMmXEoVz5f7+UFR0By3Of/rVdXy/se0Qnc9lMG5+Uj5TkcE56+lRLY6IsoeE9QjHj8afHctIH0+OXyTnh8kM2enPsa47VfG2qQeIfEWlx2xaezlk3cZUkSHhcZzW74YedvidbSy26qr6QoWYfeIEzgKf1P5V534ve4XxV4jjjv1S32yNEp3F06ncwC/1NH2EH2mdLZeKtYe40p5rfCz7fMJ+Ty+VHfHrXrs6Wcs84O5+QRkMe30r5esreyk/sG7munlaNjt2p8rkOnXLAjH0r6jmlvBcSnCg7VJHJwMfhV0kRJlW3CC+haKEjG3nAH863fENxeXeoQSlAxRFVST2XaB/KseMyebE0swHThR05+tT6+LMXiLLNID3A6DkdPlNbW90zT1KEK3kTOFRB0zlj6+1eZfEJtmqJ9sUhyGwUPvnv9a7thYbn/fSEY45PqP8AZq3qPw5bW7qLWdSvf7PsFGWZxukkGAcIvHuMmuaq1Fe8bQTb0R4Z4X+H82reP76a0gN1cI7tEuSdpI6ljwOuck19P6NbeH/hzp0ltOsVzqMzbnjhAZVPo78A49OazL/xHb2unvpPhiD7JbEfPMcefLgcliOBnvXHrlhuPf1rz4xSdo6HSqUVuaOta3qmu3H2jUZCwH3Yx9xB2CjpXPHLEk1ckOOKp9a0SsWxMVG4+U1PikKgjmrSEeo6Jdx2Xw0e9nBKQSTyEDqQoLHHvXM+EfF2k+MtM/tbSRIqBtpEo2kEfia0ZZkg+El2HOAftQ/8cNeP/Ai4jl8JzvGcr9oJGeDzu+tduHqSTjDoRPD054epWe6aPdJHOzFVbYcTZ6bCaVmG2o4mCxTsP+eTf1r0DxjLvLpYbGeVeSkbsB64UnFfPHgbX/EXiPxdY6ncQi0t5ftSSomEWXyygRm6bzjPrXs8aajqKMkChIyp3SSHCjI6k1wmmp4U0HxDYWt1dPqeqEzpA8YCQx7sMwGckkYHp1rKS1NKZ8+eNvip4gUL4X0wyLHar5YLDCjPOVXoevUivPPD3g7xP491cQ6VDJfXTNlnJ+RfUvI2FUfU/Svov4bfCnSfi5NceK9cuXtLO1uWtfs8SgyTNHy25jwoycdD3r7Y0HSdE8PWkeleHoIrdI02xqO+O3bn8a41H+Y63LWx84+Bf2cND8PRJqnjox6hcjBWDkWyH33BTIf+AkV7/wCYBbJZWCCOCNdsaIoWNQOgVeBj8K2Uiu/PMkwJY9fMH8gK3HtLuK2H2LZJIwy2TgD6Vop20RnK7OFk0q1KF9Sw5YfdcZz7YNNn1Cw0DS5ZLdCuyFnOzAAIBx0NSahbX1u/mXqnJOc+tc94r09ovCNzdxNuR7d8+oODxWtl3IV2fInwYsB4n8Ra18S9XJlujftBA78lFABOM9PvD8q+n9Mnm0t3tIbdbm1u9z3MJIBy2clQSAc55Ga+Hfhh8SrDwlo02i3cM7E30sxePb/EFA6kdNtfW9lr6m/WKNkf93E2xiA+GQMOM9ea8DFKam2d0dT5z+PPwMm8MXUWu+FIpHt7pWle3ALSRcg8gZGOccGvk+UTROYp8hl4IbII/A1+xnju8t4tdtYpWwfsvKnn7zDGcZ9K8g8VeBvBHiq8xqttGXiRQGTCk5+Yk5B9a0p4ppWkRyXPzu8P+FPEfiqVovD9lPd7PvtEhZVH+0QMCu71K0gsZBp18jQzxIqgMpU5H1Ar9DdCe48OhNH0FYI7eLagRo/vHA5LBh39q3fGH/CO3eoNo+u6XHeoqgtIMZViOcA46fWtFilJ3BRPzOl0Xan2hSOx5r9FfhVcrrHw501ZDuUwG3b/AICxUj8q4W4+HHwi1pjHGLuzYn7owB+HysP1rufhxZaVotneeHtDleW1tLjMTSfe2uiMc8D+IntXdgayc3E58TD3bo/NTU7F9M1a505+DbyvEf8AgBIrrfCs2AyHsf51s/GrSBo/xI1KJOFmladfpIxNcboF1HbXW6U4VhgmvUg7M5KivHQ9I8UeEF8X2ltJbusc8Y2bmzjbkHsD05r27wfpFp4d0i30iy5jiXGT1Y92P1NeeabJiGP24r07SpMgVpKKvc51J25WejWRDDHXIr5R+Onhm68NCK/srqV4r1n3RnOBzuwT0IBY4ya+pbBuAK5P4vaUmr+Ap1ODLEweIHuw7Vz14podN2kfnjAHkk8sruJ4AHXNQtExY88+h61oQLskaNxtOcHPUc4z+FTw6Z9r1SOxtXGJX2qzdM9sn615cn2PRiXPCM2u2euwz+HneO4Rg3yNsJAIOCcjitDx1rmo+N/GFxrdxEI5LqQYVF2jpjOAP/r1vnwZqdlPJDITDeqdq5+VWC8EA9MkgYyRmqx8N6trphltoiqqhMs6gsAiZ+bAGNwA6buT+kXbZdjz6+tJtPustGyjJwHH9KzGYtyoxXu3xdh0600LQ7C0RoriNJDcI3UnCAOTgZLHPHbHWvC1fbn3qmNEe5jwaXzSo2LxmmEjdkd6YeDipK6EeTmmlie+KR5MHA5qEBnbJ4ppPqNFhWaRtm4DAJ+bvjsOvJ6VECC22RMH6Yp6Dy2EgPzKQQfccimyTSSyNLKSzt1J6mhXGNMClsL3qOa18tiA2QO9SRYMgMh4oKhzxwPSr1SuwW5U8licClFo+7HerYUs4CA8D0qzKpBSUcA9aQMpnzN2yUlv7ueeKmBOKlmTI+X+E/oTUe1qV+4GlY+H9W1i3kutPtzMkJ+fbjI4z06mp7K//sq4iSVjJGGVivIZGU9CDjkYr0j4V3r2qXkCqWLFWGAcdxWl4h8M6Hc77i8aKx3ks8jHL5PPyooOfxIrZxioc19TPmk58tjoPFyiSwiuQMAMDn1DCvOZfWvTtTWG+8LRvA/mIkalXxtLAY5xzivMJDwRXnX7HXYrt4bGqR/2hPd21rGDtLTPhsD0UAsfyq9AfDGixOdFW5vbl1MZlKlIwD1xkgnp6VRtraCeUvIoLL0zWvIg2ZHHoBWFTFNPlPQw+AjOPO2LFrOvyRfZrZlsYsfMIAFZvdiBn9arrp1u7b5wZnzndISxz+NSxuVHHU9anWUAhj+Vck6spbno08NCC0R//9L9NaKk2ijaK7LnCMAJpdpp4GKKVxWGhTmncUUUrjDisHxNojeItCudES4ktPtKbDNDjeo743Ajnp0rf5o5oC9j4o1r9mHVtMie48P3325iSSkwCuf+BDgn8K8zg8M6hpl21jqcLwzRnDo4wQa/SLFcD8QPDFvrOmNfogNzbLuUgclRyRn6ZxXnYvCKS5obnXRxDTtI+avD2iCaRdw+Uda6DxPr8ukImgaCqyX0qbueREnTew9+wpNR1SXQrRbHTUD6hOP3S9o17yyHoAO2epxXN+HtPSz1W53uZZpoo5JpWOWd9zjJJ5wOg9qrLsA370kPE4jl0RR0fw+9nCBOxllZi8kjfedmOST+NdfFb+WuFFaBUdhT44ZJn2Rgk+1fSRhGK0PMk3J3Zz+tof7Du1/6ZGpvBBZ/Bmihhndptt8vr+6XrV7xFaeRpk8D9TAxJ9fpXl1l4mvNP8C6JY6WDG8mlwmSc8BQExwfXjiuPFS2kbUYt6HtGsyq3hZcHdtvlGe33W6VyYPzVmeENVs9d+F8Gp6czSRveR/O+fmIyCRnqPetAlgpI654rjubtWOYV9vjyPb/AH4v5Cvmzx/YSS+O9ZdcrseRzh3UjGTnhgCPbFfRk8sUXiyKa5YIN0ZJbgADHOTXKaz4O17WPE2o6lZyW81pcq6xBXjY/MCBkZyaUHuObszyLWfKn/Z6nljcyBdQiw24kZwRx9M15h8FZRD8VNIkbgGdFz9XWvcPFnh3WfDvwFv9L1iBbeWO9icKgG3aWAB+XjNfPXwrnMHxK0Vz3vYgfxYUS3IvqfeEiSfaT5Y80C6Yc+hJwM+uea0lPmaXayK5RTDcKVYYOQq/LnqeahureQ3c3mAxBb05YcDJ5LZPOMVJLNZwaZaO+J2TzwDGoG7MY43cZIAJ4NRJ2V2bx0OX8NJB/wALC0547hix04houSN3nvz6AYwOlee+L1tJfH3iBXtS88kMpkKsdjfuycADBGR716X4Y1OK58W6an2SOPbbOiO5HmhfNZtuDz1JP5VyXiPUdbTxLqdvFfSBI0lZY0B8xSEJB6ZOOo60uaPJdsdrzaRzGm6frsljpclppoWJJH3ZRsxjcp3ZJPXHevoS4eySYvJMu0xoM7+d2OemPyr5lfW1vdLs7q7ubq4b7QylmYgnByARkcDFfR8hnEkW0qm+2jPCj34we9aU2ZS7D/tNjGyvCjOVI5CE556ZOa2ryHUdW1mLSrC1eVyu7cCAABjJb5TjFW7Lwu0UKan4luGtbf7wjJIlcdtqDkZ/Ck1fxZeaijWGnj7JZ9PLThmA6byOv0zWVXEpXjA1p0G3zMt3Eug+FZWMKpqF8Rg5/wBTH+A6n8a5TUNRvdWm+1alIZH7Doqj0VRwBVQKAMDilbGDmuFtyd5HbGKSsjLn5jYDrtI/SkX7opsrfKcU4cJmqQNFeY1UU81NK3vUUQyeaabFbQnUYGTTGqY42kCqznHFbRM27naSsG+HAQgEG4lBB6EEc5rlPBFrYWGmyw2MSwoXztQYGea6QSE+AVhHVrmQD6kcVjaHZXOm2zxXQAJORg59a9LDJcp5+Ik1JpPQ6UykjFUb/UZtO06e8t4xMyxn5CcAjPeoZ5WC8VAzF9PuQeR5bf1rqOU8t13xBqmpQbJ5sJxiKP5EH4Dk/ia4zwPfeH7PULSK4KS389zKtpLIGKo4xvVQGHJBXrnp0qzeBt0fuy5/EjNYvhiZn8R6Omk2pVI7+cSuV3nonVjnbn2PNYyfvG0Ej6t+Dfhu30LwtfW8DFmfUbqbJA4LthgPbIOPSuxlzHFvdcOjZU/jWX4FlMGhOcffmmJ/GZ67QNFdxrG4BBNc3NbU3dpaEmpagY5Io5OSIgST1yTSwXSfZXkHBOFGPf8A/XVfWbN3uy8YyBhcfTms25Bhto0Pyli0mOnsP5U+VMlto071zdaTLFKd3GUz1BHNclfgXfg25hb+K2fj3AJrbE+yFY26lWNYNo3maG8R/jhkA/75NVy6Amflj4P0W51bxBPbQxM6C5ZWwMjJPevpHSNEtvEHxfth5jgfb47ddrFQ0duQnOMZyqUvwF1GPT5te0phknU2I9sqAP5V9M+DINFutbsbwxwvLH8yuAu7O09COa8PF1W6ridtJJRufOHxO8Ua1qfx/h0WwuXjgE0cDIuMELI2Qc57Vy2oeOfFUvxNvNAsDE9ql2IcOgJGFAOCMHtXs8vw80W48WzePN0gvBLLKOTtJYEDgnsWrnPD3woXRvFD+Lp7rzg0jXLow53Mc46ds0p1adtiVBti+GvHkur/ABeHhGG2YodQMImVzgqjckjp0FdNrnxD0688d6zpoYg2QlaQsvyhY/lJz9SKy/g58ONe0T4lW2uaqI5It80xdWBILo5GQeep9K8lkjvVu/FOo38Lx+dFNhnQjcJLiPGCRzxUvktoU423PZ9L8W6fqukXF3ZSpMibUJRs4LZIB646V1HgO/8AO8SXiKNqvaocA91JH8hXx/bJbWnwzuLeL5ft2oovHpFHz+Hz1758APD8+kOmrSMfKvUnhTP8RiQkn88j8K7MGowqKSZlVi3B3OC/ag0xYPFFlqiDH2i3Kt7lNo/rXzXA2EBHqP519nftRafv0TStTA/1dw0ZPs6E/wDstfGlu218D1zX0LPPirxPftMfdZKx9c16To0x4ryLw7dLNpqox5A/UV6Vo78jmtmcbWp6xp7g4rG+JxZfAF9MmcxruyOoxn8as6Y+MHNdHfaZHr2jXGjzEhbmNo8jqNwwDWU1dWBPU/NW7mS6u7m82BNw3Adge+PrVXSlN3eLBMxVfvhhwVI5zmpNS0y40y+k0ub5pEcxkLzlgcYHrzW7Y22nJBBaX0oYlt5ToY24+8D+teNNas9NW3PfNF8Eax4x8LPqE99I95AwTyZdvMYBaJiCM85Pzfh2r3f4HLfz2EHhDw9ZQmzUmOV5kEj/ADv+8LE9MMTtB4xjivhjUvEdxZ6ld2Xhe6eCG7RIpljchXwMFRzyvoO2TXv/AMNfiXpvhXSNV8T6tN5Fzeaa8EcC7gJZwoCOjAbdwZRu56g96VuperPFvjP4ovfFXjS9e8RV+xyNaR+WoVdsbHBwMDvXjQGTitqe6E24zFmLktznqfWsWXG7jrQNDdgByagbIbLVJgMeuKbKAq89aVtSit8iHIGTU6PFJA0b4Qrlt3Usey9eKqswJwaljtmlG7IAq7X3BMrZPep4YJpziJSa1LG0iW6idwCodSc9MZr0DXoo4WieBQi4IwBiok7Bc85g0uSSREmOwFgCe4FfSngr4WeHoNSmTVk+2DYxjLkqAeMHCkZ/GvCJV/iU9a9w03xULOCK/vJVgQxAYZhuOR2UEn9K560pO1mGr0OI1WDTbDVI7dI0QB3UjAA7Y5rhvEtqlnenYP3chDL/AF/Wup8Q3unatcNLZ7zuBJLDAzxjGea4rWb+6nsLW0nIIjzg4APXuep/GumLurmUYyUtSirKTyOtdtYxeF7eNHtrabUJyPm81tkSn6IAT+dcW8ezy5OquM/411/h+XEclo45xuHv6/0rPENqDlE7MLTjOooyOhGoaw6eRbvHYw9ClqgU493OWP51lf2dF5vnS5lfu0hLE/nWkzIox0+lUnYgk+9eRKrKW7PoqeGpw2R6TpCrc+GWg/uqy4/Dj+Veav0IPavQvBErzWt3bnBK7WH45Brhb+NobuSE9mP6812U37qPHrxSqtIoW+Umwv8AFV1yzxk1nD5ZQw7VomVSp44FcuI0mengZXg0QRkgfMc+1Tqwzhaq+YoOOlNaU/wj8a55PU7VY//T/Su21Kzu3Mdu+8jriru70/GvmPS/FV+nm2drIkbSE+aRzg56Dn610Vr4j8QJeeWJh5QwQDySc9/avIw3EdCrLlascs6bie+UVxcviYm1CQFftAGSrdMevXIqxb+JFXzY2KzCEZ8xSBuOM8Dn+dez9apaWkRY63FLiucfxLZ21l9uvQIlPIyeo/Gqdh430LUFVklCbjgZIx+eacsVSjbmla4WOwoqjb6jZ3TBYHDE+hq+RitYzi1dMEhKwfFOsJ4f8N32tSRtMLaB38tPvPgcKPc1vdeBXGfERC3gnURhj+5PCHDdf4Tzg+nvTbDZnz34c0+VtSt31eNknv4pLl9+MlVQnBHbBIwK4zQrmF/FE1vAThLcbvr5sn9K9OutG8RWvjxrm+3XctzERCy52wwtIilNoGBhScnvivA/CmoLH8S9b03IY2+yP/x5z/WtKNZ8yRU6KUXI9yVWc4UZ4z+FbUYEMIZRgMoJP0qMNFbqXwMkZGfTsPyqk15JegITtjX7x6ZFdrqczOdKxS12dLiznCdPKYZ/CvG7W5ePwBokMRjQzaagy2SSFyMew46163dmPyJgn3djY/75Ned+FNDtdY8I+H7u7yyxWgXyxjDYkfg98Vy4pXSSOihK12yx8NYbiL4QRfbG3t9qjO7aUU/NgbVPIAHTI6VuM2x9q8//AK66vUERfCVxDGAFW5gAAGAPnUYFcrhVGFHHHWuXbQ0bucZ4ii83VZQBn90vH4V8KRK0AJV2UhiOD719467IE1p4icM0S4A6kYr4K1BWgupU3cCRv5ms47sqeyMW41PUpt1vLcSPG3JRjxxWz8PpfI+IGjS+l7D/AOhCuYc/vSTWt4VkaLxdpbr1F3F/6FV31Mep+hupSmHW7qPcTJFdIN0nJAYrwuOD1zzWfBDJI8X2xvmM0vyr90gocfjn3FXvEiS2/iW8dtsytcJ8o4bqvPHXA4qjp11Hdqgs2DbLhlw3VG2NkED0Gaz5G9ZM6ZNfZOf8KLap400zG4uI5QCOFwJW/HjNZ3ic3EXj67a3t1MhjYiT/tlwPT261d8NSzp4s0x2CxqXmUpj5vv9s5PP1r2C7+GNp/wkb+K/Ft28dqwHl2MRw8vy4O4k/KDz0FOTjGPvCjdzsjxPwd4a8ZeObNIIIVhZZy0kwKqkaYOWbk57DA59q+kYZdB8Moiaagvr+NAjXDgiNSP7g6k578CqNxqgFiNI0iBLCxXpBDxnHQux+Zj9TWG/yrxxXC5vWz0OxQSd2JeXVzfztd3jmSVzksf5VRUc1LnNRKOTU3LJAtQyDCmpxUU3Cn6UCMNxxn8KncYXFVnPSppWIUe9UMoS9aIjzTJMscVLEMLVJiaJDwarTGpnOBWdM7E4rZGdjtA23wRCD/z+Nz+VLLIKqg58FRg/8/jf0pJm6AV6eHfuHmYn4yKaTinQDzLKdR3jb+tVHbjFXLOWGO1lNywjTa25z0A5roRgjxK7jG+Et/fQfqKZoHhTxfr+rWGpmBYrTT72WQs52DbtUDAOSSa7o3ei2kBuNGszfyqPllnP7vI7qq9fzrj7jVfHOrapBd61epY2ccg2QAbA3B4xxn8zWckt2aRbvY+ofCYWTwssiDo7k/jKzA/rW1Zs4NvGpxukA/WuO8LXc1tpFsR91o8svY5JNdxp8lhPcxSK3lmM7wCe45rBxsjbqSy6kGvZOf4yB+GKs3s0EkoRh0UAfkDWOtjK1wMDduJyR+f9KrSyyNfHf034/DOKTj2DmezNG+t1UPJF/AmMfpWRbxFNIgI6PG5H4jFWFvXIl3chh/M1W026L6ZbRydNhH600nsF0fAvgWS+sPGfimaNgsFo0k0gPXcC+0j8q9a/Z+8WXer+KJTqEcZ8i1kkV1yDkDHfIrx1IriP4keJtFtNpNzKFwcj7zP/AI88GvXvhV4dn8KSarNeMmYrKaJCp5LkduPrXjYq3tWmdtNe4R+HPiXY3dhfG5Ett9niDszjcv8ArFGRt57+ldXo/jvTNT0q8uobhJY4YxubDLjPTO4d8GvmjSnurTR9Ssb2IrNJ5S5PGFV8sCD68VLa3Ri8GaxDCnEskKPgYyAHwOK55Ri3oWlZH2j4L8V2t1FdXtuu7yIHbKMGx8prhF8TaZqdolsz4DMA2VyDgHgkV438L5bvS/BOu6tby+SqIyk5+blBwAeO9cbBrOoaP4TbUEYyH7WigPjGArk5H4U5U7aImx7LdaToN/KI9ViQwwhmCRcZYnrz3xivZPD6aPo7aBomlblVZpfkfqBKp7/jXyg/iaONbB76ORnniMpMZ+UZcrt/QGvaIfFFwPiDoGnRwgRfaIV81urnaq4H0IrbDp+0SJqfAzpP2hNPa9+Gk8/8VrPFL+BcIf8A0Kvz9QYcgV+mXxVs/tnw71yAjOLZnH1Rg/8ASvzQ2gFcdxX08tDy4bM9G8LXcYU2znDZyvvxXbP/AMJpNOE8Om1ijI5ebcWz9FHr714vFdG3dQM7uoIrtNO8W63bgJEcj3xn+VacyasYyg73R6np2h/Gm6OLfU9PQ+hSStK80D9o61XzbPUNOlUDIALqT+YPP41yVh8RddgwfKLY/wBoD/2WuttPjFfW6j7TZSOB6MD/AOy1jKF+pS5+x8/6z4c8f2WpGXWtIga4L+dkSryxO7cOfWuY1bRvE0zmePTBHKzbmbzEPP0zXo/xQ8Z654v1aK/0pWgjiQABlwwYAdx1H1rk7TXJ7B4rmVJLiVI2R0kJEbMcfNxzwM8A1yyhK5vGTtqjlorzxhps4nk09GZRgHGf5E1Hq/iLU9aSKPV7R1EKhEVVIAA9ODXrF3feH9K8O3F39qOoXNxgxW67lMLMuT8yybsKeMHOa8aPiHVlI82SXI5ywyP1rPlfUtSfYzZZLY8sjIP97n8iKy5TaM26HeB74P8AWtyTXGuSRciJ8+qKP5CqUq2kp3LGFP8AsmpcWWpFFTGxG1gaS4XDCustNQ0eGBbe702Kfb/y03Ojn/vkgfpWL5+lh5IrqKTJJMTKwGB6EEc1Dix3OcnGGzTF3khVzn2q9cxo7Dy8496gQeS+Q2CPanYq4iSywkSZJAPI717JrDwXOlw3Nudy8EfqK8bjQu5Luoyc/NxmuysNWS30g6bOA+GyrZ4x6fnmonFu1gY6QAZFWoLeLy1kIyx9ayje27/M7qp6YzWlYX1syGJnHtmuatTlym1Fpy1L0y8A+xFcpqfMSMegbFdRcTRvCojbJz269Kw49O1HU4JLaygedkO5hGpYgevFa4ZPk1JxDtUuZ7OrwrF0KYIrU0y4McqSdgcH6dP61zU7SRXPlOCpU4IPXI7Vq2n+sMWeGGRWso3i0TTnyzUkehOUONn1zVWTcp7VBZTGW2GTgp8p/Dp+lSCK6upPKtUaVj/dH+FeDKDTsfVKrFxUmdf4KuCmoywd5Iz+hFUPE9ubbWXB/jVW/p/Stjwp4Z1XT9Vhv70qg5UjJzyMdOKPGsSLqMb53blI49j/APXrrop8up4+MlGVW8TgZAV+b05q1bh7g4jXGe9VZmAYg9OlcvfXWsRZSGbCf7IAq50lO1yaWKlTuonefYLeAGa7nSMDr3NQHxN4U09f3ayXEgHXHU/jivJppbl23TszH3OakW2Z+cE1SpRXQieIqS3Z/9T0PSo9NsLo3lz5kckrkurAkZ5zwMgE55rtY9UHnBLaUoH42uPTtyMivKbHxZcpHNDqELHKkfNgjJPXK56deQKht7++urhLjTQZY42w1xghVJ/hJ6/kO9flcqEr3Ycz3se0NfyS3PkwyxkkbXGTyfw7YrCv9WgsHS1Y+U4cABunX16VQtCsUp1O6kiiCsBvH8XfnIHT1qV1j1eNPPhilnzuSQSA557Aj9KwgmnqTzJEut6pr95ALHTpv3j8/vWyqqOm0dPpXnNlr/ivSDdwaghmjt5AxkbgcgE4IwCM5rsDYtLMlvLKEng+ZI2IyDzyuDjGOvNP87VZruSxv4BMrqFYK4G5eckZ6YBrphUaVpahGz3L+kePJ5NTgmsWe3hdhuY/KoyOgyf5cV9GHxxp1z4edUuFEyKMOTx25Jr5wsNBsrYIiQeWI2AjZvvEf3W/HjvmsnxFqQsL+HTry0k+y3oKNLGcAMAT0OPT1rtwWaVaEmqRMo9GfT3hnxAkcn2m5vhOGxwDkY9ifT61reNdY0zVPAmpCzkjlYwNhSwAJ9CcjA9eeK+avD6mxsoxYzebENwxJjcBnoRk9KueIrg2HhzUGYKHeJihwWRR64A59SK9TD8TT5lCoiFT1ujnbj4lXngKS2j1iZoTf3Fy11LIC77EZdyJnPDMRjAxjoa8p8BwWVr4q1PXLIER37eapYdtxA4rM+I7zfEXXV1XVJMGDCIFHyhV64HHXjt2rU0HFrOYY+iRAfqa+oo19dCqjvoe/i8a+IklfbCgwD3NK+oiUbUO1R0FedxagY0CuTxyF/rV22umkYBcknpXoUq/VnM4HZyzbreQZ/gb+RrK+HLD/hANHByM27A4+8cSuKjhnB3I5wdrdfoaZ8OWdPBGmgD5fLlXj7xxcSjFdE6l2mKCeqO81A7/AAjdIOCLiAkdhiReK5UFTnPTIxXYanGIvCd6ocE+ZCSF+6v7xOAe9cHE7MVBrmnLVm8Focj4qXGtJNg/6sZx14r4V1OS3+2XGQf9a/BHI5NfemtzBNYWQjcRGMenU18B+JMrrl8oPyi4k4Hb5zWS3LltYxN8Zc7x9Kt6MTFr9lOONtwh59jWWcgZ7Vo6HaajqetW1npEMlxM0qbY41LsefQVS8zNbn6LeKJY5Ncv0jhY7Z4ydoO7IK4YY7d6E8IeKtdljTQ4dqC5/wBKuZgEjiiKtuYMcZJOOmTXpf8Awia2mqT6p4qvAQzZWytxiRumPNcHAHqOeKuajq8+oKkCqIYE+5Cgwo/AdTWFSutonVTodWc94X8J+Ffh5bRpoijUNSjaRjqV0N7r5jZKRbgNoHHRaS/upri5Mtw7PI5yWY5J/GrpHy1kznMwFcrd9WdcUlsSYqCfheKsgZqvcD5fpSGUk6Zpo605Pu0mKBkwHFVp8YP0q4q5Ws+6bbkUyWYEhG4CrMx+UCs+RvnB96uzGmBVwBUiUynCqjuAkvArNl61oSnisyRhnmt0ZI7CPYPBCyyHCpdOzE9gADWVZ6zpOsQm50m4juIwcFo2DAH0OKS+f/i3U4B6zSf+gCvE/ggnk6HfIMECdehz/frroVHpHuZVcLGVKdZvVWPbpJMg7etMjAutPuYJwGVkYEHv1qtIxHAq1p/zW8ue4au48o+bn0c2UYa1aVD6ozD+Rpv/AAiWoS6lb32tTTsmQ8eWz9Ms3H4A5rp7g4jUnoK424stTu9bW41a6BjGoRG3SRi2AITlVC5xnPfFc1WNtjpptXPtbTYJINIsy/G6BGH0NWSTXc6JpMOveDtOMbBZIrdFz1/A1Un8Mx2g/wBJmBPsMD881VOquWzFOm+bQ5WOaeM7kdh9CRUiXEyEsDnPrzWjLFp0C+XIdz+o5GKgEVjKcISDnGPWtFJPoQ00VVcOCp4J44pmieVPYxIDhl6Z7802VFjmCJ6j+dVtASRrFGQHOSM9qLqwrH51fGCCTTvi5qWAVLuGGPdQf60aN4x8SeH2YWt5IA8ZVlJ3j51weDkdDXuf7R3w61ufW7Xx1osLTKIglyIwSVZD1P1Ujn2r58v7f7QiCCEjjB/vdOhFcOIp3a0OulK2h1tp4tt3vI7rXY1nQnDIe4Hc8+tXp10m90y5n0/MUNxdKFRM8HBwpH48V54uiazKQkFvI/HZSf5V1eh6F43tTiwsJ3BIYL5TkbhnBzt9zXD9Snq0jodaK0Z2nhrQ52i1rR0Z2S3tpbgKrEA/uzgnBGcY6V5/eBJvC7wquXS4UkA9irdq9GGt3Oivf2z2r2dxcxvA6MceWsgO7jrzuNcC7WtsvyAA+p4rSGGk37we0VtCDUI4rm0sDbsQ0cW2UZPGGJH866LTPEmpaj430WTIXyrmCOJUGAoDj8yepNchJJLdSbIA0rf3YwWP5DNe5/CD4Wa5ceILbxfr0JtbS0YvDHKMSSPjhtv8Kg8888dK9DDUIxeiOatN21Z9X67b/wBoaFe2rDJmtplx6lkIr8vZ9G1pLiRI7K5bZIwysMhHDEdQK/VF8lGA7gio7V5Dbrk9M/zr0pq558J2uflFcTJkLhg6kqwKkEHuDkdq0LTUYI3xK4X/AHuP51+qMMFqu4yRISzFs7R39asHTdIulKT2sLg9dyA1Kj2KdRH5t6XeQ3H+odXA/unP8q6ZSrDoDX2rrHwn+HuvRkXOlwRvjiSFRG4+jAZr5n8e/C3V/BE6XGkNJqOnzuEXCkzQuTwrjncp7MD9QKcnoJSTZ5dc7DkkCuduBGx4ArqL7RfEUORNp92v/bF/8K5K7ttThP721uE/3o3H9KxZa3KTxx5wQK4fWNZltLlrfaqr2OOtdVNOyH97lfqCP51zGpW9rfHMjDNZSiap6mV/bkEqrH5W5vZetPd4HGZLXr32/wCFVk0hYSWhYZ9aQwXanh6z1LshGGmfdZDH9Cw/rURg0+YbBKw9MmqM9ncytuZs1Pa2BDF5ueOBUsrl6jCn2efypSOejdiKJtLupGMygMp6EEciq17bvH93lev0qewvXC7Gbp2peQ9inPYzqMFGGPSqqQsj4fIHvXUmdz0NMNwTwwpco+Y51oA5zwfoat2u+2kBhkMZ/wBocfjgVdcwsxLIKaYIJOBkVLiCdi8sl9cjdsjmx/zzK7vyyDXR+EdQ8TaDqp1rwq81tdxjBCjt6FTwVNch9gVYi6zKMHgGltb3WLKTfazD8GIos0TLXc2PGWp32va5Lquo2wtrm4bzJVVdqlyPmKj3OTUvhm0stT16z07UXMMUziNnXqpbIU9/4sUy88R3F/a+TqUJMi8pImCVb1pmn38V8WWVRHdKNyuOMleQR70X7iadrI9H1bTdM+HWv3Wl6+n2pWVJbdwMhlOcnHA9O1cxdfEi+QldIiSBMYHyjP5c1Q8Sa/qXiaytv7WfzZbMGJZP4inoT3xisWDQrmXGBXHWhFSukdVKdRwSkyxbeLNcutZtJr25kkVJ0OM4H3gDwMCvdvHMML2sN1EOQcn/AIEAf6V41F4beMCTIyvPT0r2zWV+0+FopOM7Ac9/l4rO66Fs8kljLcisa5aGNikhwT610rqMbh3pLSCCZmSQA9MZFNuyFFXZwl1FbkfKV5962bOyV4wUHauvOg2M7ZaJTj1Fb0Om2yRDLKmB0pcxW2h//9XQ8R6HrNmIrm0uF2fN5pjUFeQc43Z9656y8TaxIDp+np5kSvg7MDMmByPl6Y65r0HQr06lpCahcSq0F2gBCH5CJBhs47ZP4Vy/iyWwtdOWy0yRrW5WUF41ADHPGV46e4r84p1G37KojOM2+p11rdztpMltr9ti3kyju5zliMMQF2bV/E1h+HLKXTw8y3A8lyVjJOSobofrVnQtbsZ9Hl0q9mSUsWiXzl3YcKByDzk5BFc9pHiKy8N6nDp08CXoZmCBEDkZJXKnBIABOc9qiVCS5kgkrmn4t1aHw9fw3l/5ojuU2NO2CIyvzBvl253dB0o03xtp+rR/ZIPNLSgCGQAbtyZAbGenTIzWvqXh+08VJcRmJmhSMbRCV25zkKB6jmvL9I8F63pUV0iWrhNxYlZCku3GQcKRgjucYp0qVKcfeepShfVHvWgaxLrdp9guHUOcbP7wAOM//W7VgeNtEutUZIwW227GU/N8pK9gMZ5+vavNPBV7M1+0vkiWa2X/AJacJhWAfc3ALYzyTmvSNT1iax0+W8uguxkVlK7TguccE5GB6j161hOhKFTRiejsyG0Y3OmxQWyGN4/vkseF7kep+uK6HXNSnk8N3hUOqi3JVxgt8o6hSMduBXn1jrcN+WfTFnDjG5icrkdxjjJ9K7rU7mZ9Iv8AT70dbclAD+8fI3DYeuewIpey/eRfmEXroeL5P2qXBJBYnJ4PXuKv6fdGC+bHOY/61SlGy4kDZDBjwxyfx96W151DA/55ZP519zRnZmT3Ov05Hu7oRE8Hlj6D1rsYbma6LWukRjbGPmc9gO+a5vTIY5bQtcuIrZOZiPvseoUevGKt/wBsz3hFhYoIoScLEgwPTLf3jjua1jWudkIxhHzN4wzW0uZvmBBG4dM7c4q98OpCngnTxnAb7Qpx1P8ApU3ArCuJJt8aOxOIz9M8itT4duV8EWQGBh7oF+rDF1LwPevThO8Tlt71z0u8czeGNRgcACMREKvb94nU9zXnsDjzDzzjiu3+0B/DGqWkYChURwO/+tTkn15rzaKVFlOTjp/WpnLuUjP1y2e41SNojgBBn8zXwB4jlkXxDqCNyPtMvH/AzzX6D3kd3dalDbWKNLNIuFRASx5PQCs7w3+zh4V0TWpvFPxDK6hcyStLHpqt+6QsSR5xU/NjuucdiKn2qSLUHJnyp8K/gn4r+J87XtuEs9Lh4mvJwSg9kAILN7ZAr7s8DeBPB3wts2tfBkJkupP9fqNzh5XI/wCea/djUdsAn1NdldX811EluAkcEQxHDEoSJB/sooAH5VQyf4q55VXI6IUlEhdmZzJISWPUnkmmZyaGOc/WmjrUGo5/u5rHkIacVryEhcVhHH2oY9aGwRdqrdHAq13qpdfdpDKS0+mL7VIOtAyZTheazLtg2cVok/LWTctwaolHPykBh7GrklZty2MkVoSHgUARZFOzxUQOTilY4WncCtNKcc1kzSEnmr0zccms1+v41XMxWOpZRL4AkjbgNcMM9+VFedfDzw/beG9Oube0keRZJA3z4yMbvQD1r0gjPw/f2u2x/wB8rXIeG94s5Q3ByP616eEinBN9DhxFWa5qaejN1ySTWhpALrIg7qaziVH3jirVi8n2eY2bbH2NtbqQcdcGu0884iDwZql5D594yWkC5zJL6ewFYrWXgCxvWtLOabUL551cSEhY4nCYGAOTx65rk7zV9R1Ms2rzSTSDPMjEj8B0H5Vl+G1tG16fYhEkcqFnY9crxgD6VlVmlGx0U4u+p93eGNcvNG0mCOHaVeKMjI77BUl1LqN6Dc3DYVjnJ4H4VmWYxo1iSuf3MeR7bRWq90zbrp4gecKp5VR2AFRGKUUxu97FJbbzMBTn36D+tX49MkAwGVfocmpJ72WFtlvtI2gkhcc+lUGv7hsKRjP1qrk2Lv2a2tjulGSOfeqejS/Z9KijAwSCT+Jpl1lInZW3AKTkfTvTLaYBAJTwR+VWuVEWl3L8rmRTHJjYeqkZB/OsRtE0Dd5n2ODd67BWmbMSnMTZz+NV5LG5jJyM464rVVF0RLg+45IdNtziCGIfRF/wqdbhOi4T3UAVnmKU9QaaVKjBzQ5hyHGeJfhr4T8V6h/aWpiUTYCs0T7dwHTIwaoW/wAJPh5ZvvjsTIR3lldufXggfpXoKbui96ewIAz3Gay5U3dlc7tYyLDQdC0sbNOs4YvooJ/M5NdHG4YYrO/iJqRZNp5rWOhlLXc0h71nW0hCbG/hkI/r/Wr4ORmsrdiaTb2cfqK2ZBsA4PNW4fvVRYjNXIDyKVxNGoCVwRWbqtqtxG0X/PRcqfRh0NXgcjBqOb95BuxzG1DIQJcQXdlFd7QXkUbgQDg45qFYLGRwLiKMr3+RT/MVl6cxW6nsugVt6D/Zbnj861GGDigbvcpanoXhm9wrWFuwxyTGoJ/KuRu/ht4Bu8/aNJtznrjeP5MK7jOKaxGKCk2ePXvwG+FN9nfprR+8c0g/mxrmbv8AZj+GNx/x7m+gP+zMpH/jyGvoTijr0qHFdiuZ9z5Pu/2TfDsmTYavdR+gkRH/AFAWuUvf2TNWT/kG61C59JYSv6hzX20yke1RnilyRY/ayXU/PXUf2XPiLBxby2dyPZ2U/wDoJrznVfgD8UdJZmfSncL/ABRNuH64r9T81GWfHBqZUYsaxEup+Pl54d8Q6UpGp2U8JXgll4/Q1iyHHBBB9xiv2Xkd/LYdeDgNyPyNfL/gXWrPxD8QLnwpr0dvqUbIztHcW8ZMTDbt2krnkbsjPpWUqVmbQquWp8BZGabJITFsXg1+qupfBj4VagCLjQ7VWI5MQaM8/wC4VrzvU/2X/hhdgmy+1WpP9yVmA/B91J0GNYiPVH5wESk/Mc0odlr7V1T9kk8tomr59BOv9VArzPWP2ZPiXp7E2kUF4vYxSKCfwLZrOVKaZoq0GfOwu5lbAp7TNIBnhgcgiu21b4Y+PtDLf2not6m3qwidl/MAjFcPMrQnZKpRv7rDB/I1nyvqaJroX7ecbGQkgkfUf5/GvWdEaOexikb7xXB+o4rxUF+Npr1LwTOJUks5GGUO4d+DXPWStc2gdjIq7cIM11Vni40AwsPmAZcfrWO0Q6rxxW/oYLW8seRwe/vXLFq+htJWR5SVOzae3FVbW/e0uyEUNle9aV/Gbe6mhbja7fzrDtYpJm8w5+Y/pV2M0za+23srddufQVPFHLIPnY8+9PgtXbAI4rYihjj4PHtWcpWKWp//1ub0DwP8TvDc0E9mIkhdQWKuHCLjcWUDqRjGB1JrvtEt9TvNRfWNWhMxS32cqSW+fPCnGG6/hmut8P3d3Ho4stUDxmNcgE5k+ZscDgELnBq1ruleJreS1sfCZjuLu5jkl3HhFjjAzuAGS+WGMYHXNfBfv6snTcdTG55/rJ0tNS/tHTrMtPKpja0KDcSFAL46ccfNnHvxW1Drlk96PD9xp2brzEWUoP8AVsOcFsdc9hmuY0jwV4vvlm8Q6nfW1oYtzzFy29ihO5QMYHA6e9belWthqNzPqer3axy35Mr4+Ro3PC5GT0JHOa75YCMaS520w57M7idrFE+xMfLjVwRu4+b0P4Z5rMtTokE81r80zyNhxg9G9D/dxXgGu2HjOy/eJK8m1wjKe5OcD9Oua6O18WawtvDaavYfZlXCyXSPhkOepUqwOBzjNeNUwbT913LjK+x6re+CfCV1YPYWhMCMN21VxtHXK8jg9azPD/hzRPDtlPa2cyXFvLAWG8kFSOADuHByR9KXQ/EaahOlnAfPiZfNjuGH3gFyRgEYJPQciuy0S8S9SU3MMaqhwVC43A9TyTXPJzhHkbBs8i8NJ/Yuqz6pdyBYgMvGrZJXJ2nC5J69cVh6hrWp+JL69LuZBEkqlGbaFQAnJPI5HcZr2I2dnpmpyyIkC287AyB87lGBgj256VzGvx+HLi0untpImvLdXy8eQrAjnzFHYZ5wa6MM/fuxwS3PPJP9Y3I4OODkfge/1qbTd0mr+Sgyxi4HrzVaU7Z5M44Y/d+7+Ge1T6Xk6sSvXyuPzr62ktTKb1OqvWYMlucARqF49e/P1zW/4fMYywHzZArmb5Wiunhbqu0fjgZrZ0SbbIVPHSohFpnSa98xyjDjg/zNaHw+Yf8ACD2T5x+/vBuPJ/4+peg/GsW9kJVcf7VdB8KrC/1PwfZ2NjH5kn2u9G4dB/pMlevQ+Exe9juo9sfh/V14UC3Bx34kTk1g+H/Bt/qf+nXh+xWYIPmTDDP6hE+8fr0969VtrPSvDyTW4xe3EqhZCf8AUrgg/VjkewrPubue7fdO2cdB0A+gFZVp3aSOmnS6sVJrLSYTZ+H0MQPDzH/WP9T2Htmsthkc1I/3qhfpWJvYYcVE1SZ4qIkd6LjK4HX60uMmkPBpRRcEMnOEzWFGc3Q+ta9y3y1hwvtulHrSbHFaGsetUrs4FXCc81n3R5Ap3EmV4zgH3qYVEnQ1IKEMVulY12QFNbEn3KwLx/kNU2JKxgXHKn3I/nWjJ0rMfLMF9SP51ozMAKEwIl4NNkamq1MlfAzTDcpTnNVGGSKmdieTVdsE00DOt8wD4eHb1F9/RaozyELjBFWXwPh2WPU3/wDRapTPla9bBfwzy8X8RnPcLu2tmtTRpFdZdv8AdP8AKsV+TWtov35AP7p/lXYch4VqVsVjdh15qvYauukT31xqoW2s1MO2XaRvcqeM4+Y8Vt36bo5APU1yHibwXr/iHT7mUSmGAeU1vvBKl1DA/hz15rGrHRnTTkrn6BaZcWMnhjTL4lVR7OFwzkLwUBHX2qoniHRFkGx2uWzwkCM/6gbf1rK8G+H7a/8ACemTampklisbePBY7RsiUcAY7+tdzpekQRykBVTC8YAFcyttcs4e51LXLyY/ZrUQ7jkGZwD+SbqryWWrTp/pt4Rg8rCCo/Pg/pXUz2qrKWz7VXa3BU7Tya3VjFo5K6srayt3mttwcxurFmzuyh6/jWvYMr2ILjJZBg+nNN1K1YWr5B+6R+YIq1YReVptu6sGLpjFVzJAkV87MFepqcXsiEqrc45+lZF/PeoVjt4sYbHvUY0+a6R2uH2tsI4757U+ZE6pm4NR3DoD24pEnjdstWXDDDZR+QZASql2yRnA6nFZL+JdK+02dlbsZnvfMMfl4I2xMFcsT0AY46GqvEHc6fzFBLLx6VCZVIAHNYsGsxeW0t+FgQMyqN2SSpKnsPSs+bVrdpEMRfKSlcDABPluw3dflO365xWypSbtYxlJJHSS3EMIDSsq7jgZOMn0+tSA5Irg5NduLy38yWKNMSROoJLfK5kX2wwKcexqo95qnmXGbgsXSfggADypJAMYHB2qB1reNBmbqJJHreVYZUg/SsiUbbuQD+JVP5E1X0JPJgY9BI7OFzuKqxyAT6irdwf9Mx/ejP6Ef41Mt7Au5pMcgH2q1CTmqOfkX6VPC3IpNjaNtMcZqSMDe6MeHFQRkleafuCTKab2Isc8xFrrFrLLwshMDn3PT+VbMqGOUxnsazPEkLpbyyxfeTE6fVCGP6A1djuBdILkHO8ZqB9AbrTDTicmm02rjG01lDDDcg06kJxQyTi7GSay0iS9R3drWWUSqzZDJG7Z/HaOK3JNZ09Z/siy4kIG3Ktj5vunOOhrAFzFDHq1kVYl3fy1x94ug4H/AAIkVNaW4tNatre4AZms9p/3o2TFIo2rHUY5YI1mljeVyw+XIBKnkAEA8cZq2J4jjDLycDkcn0FcYbd0tbmS3/1ljdmVR6hkUkfjn9KjkFxeXUH2MLsurZ2jLkrhmZ2BGAecEUXFY7G5m8iMybWfBAwoyeTjjpWBpdt4cm1aTXLG0VLxlMbTFArEDGRn8RVW1t5W1wtLM27y0l+U/KWUBXAB7EtVy0Ro59QtomKlJA6EDpvQf/E0mx3fQ6Amod6vkKQcHB56VzcF7qg01L25kiKtH5hJBByFHyYB/vZGfSov7XjtvtF3FCCHijucBjkq20HrkAjd260IFsdVnioiaxJNU3tG0qvCyTCN0GGB3qSuSQODj86sW+q2V3O1vGSHUsCG45U4NFxGl5jr90kVg6toOh63GY9Xs4blSMESoG/nWnHcQTrugcMD6UN1oZW2p4R4h/Z6+G2rkyWls1jI2eYDgf8AfIxWp8M/gz4b8FfbLO7IvxeMNrSoAVQAfL1PcZr1x+DikgbbcK3pWXInqzRVZWsfGF/4c1GHULi3iiOI5HAAx0Ge30qhp3ySun3eOfwrrfiHrGsaR8QZNNjYR27yLJwvJUnkEmuZ1Gez0zVvILjdI+FXv8wDf1rycRQUHeJ6NGo5RszzfxSjf2nKidZSMfQgZq9p2llVBfgVP4nvNM0rU0vtXVyTGNqJjr9TXIXnxPjRSun2gXjq5z/Kud36GyR6IlnkfICBTmjgt1zcSIgH95gP514Ze/EHX7tdkbCNfRRXLXOp6pesWmlZs+9L2T6lKR//1/oHxVZaQulp41vbkSSRbZm28Yj/AIj83BGOTjk145L8RdH0vUfJ8L3a30Bg+0I8WSYn3FWj9RkbTj2rkfGPifX9E1298IWGorLpVzvFt5Y3worEOYkJGApGQOmAMAdq8fj0iSG9XVrW3WFbaRbWWAjEsxlDEME7gbcZz1IrxJ4WnL9317nLues3/jGybTZ9aZ5ftzv5rJ1/esxwNpGMHAHHNSaZqXhnXL+8vZrcxRyR+ZIihmK9C5wctkHPvXm/inS7+wMEdgkkFw0ouYw+UMMUeAWbPIIdWwe+Miu+0fwSmiwSal4iuZbKymjZ1tZgTMVc4QFM53vkYB5yfWq+qzlDkkx2Vrnc2Ov+Gtb0+Xw6NszOVWONpCpcLkls5GNuPXNZ8epz+GfJ0LxLaxvZXIcwHcJN4U4HzKTwp4Oa8UTRLK+F62nb7V7UGUK4YOY1ZRhtm5snPQ8ADrWzDp9/rOkR+L1tmisxiFPJGcuAB8w45zznngivMeXtptrQ0jsepeGPDPkO0lgJIGBDRxlzJHkDKgDJ4Jx3r0KxlvLhUg1a1W2mUZb+DJ4zjaRkn2rkPC0WpeIGjtLaNIbtFVyNy+QV24yxGQrEHjjqatPp+maXfaZeatdvfRi5ZL5skRQ+Yu1HDA9VkIHQdc1zVslqSSk2Cu3Y888Ypr914ilhtkdFHCO27GwAZbGc5HSq2n2tt4a8P3kZnRDNEQpOGO4jJ3DkgH09K+qfFdj4Vg1W2tY5yzPBGyrGPMfay8NkkfexkYPTnvXiPxI8GX2j2F42lp5sCSCMyMCJIyxB2kc884yxFaU8K4NQa2NYxaZ56zGYtKSCWJPy9Pwqzpn/ACEyV/55f1quiSRbopBh0OD9RVrRVA1SRW/545/8er6GjS94wnuzfuiTct7hf5Cp7XzFbCj5j0rotF8Ja/4m1BodIgLAYDytxGnAzuc8Dj8a978P+FfD3g4edFtvtQAGJyPkjPcoG6nPQ4FT7PU7Ix7nD+G/h5c6hbRah4lZrK052g8SyZ/uqQTj3xXuGjafpfh7R00bw5ALS0+ZtgJLMXJZmdjkksSSecVzU9xcXc3nXDl3PUnmuuA2qAOgAH6V3UI6WFUSWpxN6Al5Io45NUATV7UGH26U+9ZpfFcc37zOmOw1z8xqCRhiklmjiGXOBVF5ZZx+6Gwerdfy/wAahsZJNcRwpukOPT1/+vVB5ruYjy/3aHglh8x+g7fiKtLDGh39WPVj1pr9PxpqwjP0xy9mrMzMdzcscnG44zWmOlYujnOno3u3/oRrYYhV5py0YIpXL5GBWZaqDcDPbNXJ5B1NVLU/vs1JRfduKz7g8irj8Vn3BzRcEhU6U/pRF92ug0/SbWW2+338ypGMgKepP+RVwTeiFJ2Vzmp2ITiudvGO01v3UUxiNwqnyg2C2OM/WnSeGp2eBJpFBmdRgf3CAS361ahJvQjnSOEBLTqo67hgfjXQSaPqAvILO4jaNpz8u70HJP4VuXcvhlNT0/UdHQNiQr5KD5mYZCkj3bHNbOqXVxp82nXmssHcSSb9vOAygY49K1jSXUzdR9jl/EWi6fpcME+mzGVW3I5JB+dTg4xXHSvuHFdn4pstLihi1PSX3RTMwI5xuB569OvSuGJ4qaqtKxVN3VyJhnr0qN8LyKkJzxVeTjkmskaHTyNn4fBQf+X48fgtUZ/lXBov7n7L8N5Zh1W4cj64GK8i+FWv6zrum3cmt3DXDRSIFLdgd3H6V6eDqWSg+px4jDSnCVZPSJ6WeTitbSJI4TJJJ91VYtjk4ArGll5zWpojZaTP91v5V6B5lrnIW/i7wNE7DSY4nlBPz3jcA/7hI/lWR4h8TarqUAW51C0eEcpa2wQY/wBo4546de9ee3unR/aZnZePMbt708eGItNh/tcMMyoRtXb8oJ4yM55xxgdqxqyfK0b04q592eEtSSPwlYBmAJtYz/44K6TT9RSWQoTuG05/yK8t8PHd4a01+xs4T/44K73w35SzSPKQB5bfyrN0koKRSnrYimlLMSD3piysBwaoNMoif13fpTZpQ0EYHPX+dXykXLt3cvJD5b4IyK5STxBo+gaJa32tzLbpjahbu2TwB3OK1s/KSfUfzFcL4njgl+HVxPMoYxCMqWGcHzV5HpwaUo2Wg4u71LOvfFuy064je2sZLiBo45ZplXCxo5KhiDyM7TRqmvXtxpv2y2kETx6zHaOEH3ovP2Fec9QK8b+Itnq2o67DqGnmaWC007T5bm0iBP2iPMmRgdSADx7100Wm+MrjxHPov2LbpcmrLqYvWccxh/NEez724kgH0rHkqdy24EHhrQdL1e3bx/q95Kl/LcTpGxlIVkaM4g2HjHzE4AzxWd8I9VWPxJLYawAsk6SppzdjHHcS+ai/7W85PfGK6zTPhld6f4iN5caiZtLjmkubexCkbJZFKZJz/CpwOtdtp/g/w5Y28MQt1f7LLJPC0g3Mkkzb3Kk5IyaqMJPyIc1sU5UjN5BHKA+2+mHPON2ev51lQ22oXU3n+S6lpI3bf8vSN1bAPYFhiu8YKWJXjJyfxqPHavWjiGtUjjlC5ycHh27kiENw6p8qgleeUeRh6jkPWhdeH7eRJGXc7t5vBOFIlZmdTjHB3ECugXHen8dql1pXuHIjK0LTYdKR1to/ISR9wiByF/U9c1vXXzXULeu4fmB/hVYU+5YqsEno+P0NTzNttjtbY0AcxqasQkAjNVk/1OPQmpEPzUMDfixtFJKRnNNg+6DSTcn8KozJtRCSxoz9CNp9wwwa5XQfMjtnsn+9A5Tn07VuNIHXyieg4/Cvlr47+KPGHhDVbO58NXBt4r2NgSOhlQg89f4SazlpqVFcz5T6kpDjFfnZD8YPjbEvFxHL/wACUH/0Gnt+0R8WbNtlzErFfvDIHvj7lZ+28jb2DP0NJpp9TXwHB+1L46g4u9OD/Rh/8TW1B+1tqMa/6Zo7n/dZD/QU/bIPYyPuDJHGaiaKPIcqCR0JHI+hr4/g/a50fgXek3K/Taf61vW/7WfgKTi5tbuL1OzOPyp+2iT7CZ9OCCFGZ0RQX+8QAM/X1qvJZ28kaQkbRH9wqSCuPQjpXhNt+078LLgfvLiWL/ejaugtfj18KbwgJqsaE9nBH86FUi+oeyl2PT/7OtkmS6jyGjQxgZ42nGc/kOa5qbxN4R03VZXutWtUklVUaNpU425wfXPJrwv4m+O9T8bafc6Z4FuBDpVlH5uoaiz+XFtONqbupyxwFHLHoDXyj4X8Kf8ACcaxc6Vo1zI8lvbPdM7KVDKjKpCgE8/Nnt0qZ1GnZFRpXV2fpXbWS3VjbSabPFc/Z5GdCCGRgzbsHHcdqp/2RexRrEybttpJblgRySPkOPwFfnJ4J8e+J/B9wNT0K7e4tUYNLFuwcdTlD/MZr9E/AXj3R/iBoceqaW43kfvIsjcp7giinO+4TpWV0SXMV75csxicO0UL8DP7yNyCBj/ZNMlZVuC0mQoulbkY+WZE3fqDmu1KkHmo2z0zWjVzJHJ6BJavPKsckZkRREyKRvAjwoLDqOBXSH1NZn2DyrhJmMaxwlmD9CAQcgnAGBnkk1hWnjnw5e6nJpsU4QIgdZpcJFICcfu2Yjdj2GKQJNnVOOSarAlXBHqKkS4t7lc20iSj1Rg38iajZWB+YYxQ2B84fHPTR/wkFrqW9Iw6Mu5mAzjaRgV8s+NpntPH9pqVq++KaKGTcPu5G6Nv/Qa+vv2hbXfodpfKOYpgM+zKRXyp4hsPP0TS9RXkxtNAx7jayuP/AEM1xYo7sM9EdL8RbGC4tYrjAOGP5GvBbuxKZCjg19Ha5Cbvwws4IJ8pH/QZrxK4jzOErgR2M5qDSiwGQa3oNHhCgkZOK2La1crgLmtmHTpiAQKly1Gkf//Qqa9G9pPFarbGGVnXzAylyiQ9SoHsOc10kOhW/jCaTSNAhldNRRpHlKbZF8rDDyyx2kk9fbvXU6n8SfB2ufFG+S0vYINMa18qKVkQ7mkVVkCsTwW5z1rrk8YeELER2nhrUI3nswsgwV2hV3BlUA8FgxyO+B6V4l6SqybeiOa3Y+dV1HRrbwnc6ZqgmbWHvfsjKUIEdvbuUzuywLnkuemeAOK9O074beIvij4pbxDbrJbafHOWcTujyNtBBZdgC7x2HQH1xiuOGs6HfaxN401S8gjtLGeRYtP2KvnxyTPK5bnczZY9/avsPw5rHwy0GwhttD1qIogLLsmUsxb5izANgk5z0r0ac4TldvQ1lFpaI5DSPhP4a8MawZIIri7LL9n4C4AcN98ZyTnuMCvCdDmu4fEOqfB26X7KLO5lkkuGA8pIpTv39yX8sqAOny+9fWOreN/DU8bjS/EWn2Ur7d8ytGZCVzx8zEY5Pavku8Gn+IPiNq0U2pxvBPNC73UbKgfEMaNucHkDb0+vrWmKnGNN8oqcXex7BZWOm3R/sTT0jjsEb/XPkNJ/tcHqT06AelcR448PWVhpMkGnrIxvJBBGARgZI3E57BefqK7O+g8Ow6atvoV15758kSO37oE9GLA4yDWdclb/AEKY6rcxJcWzNLb+VjCSRjIOOcg9CDxg14spy5Up7nXGHKrHqHwz8Mm18UD+0iLrydMtlikYYKgIFxgH1XvT9W8N6d4n0LX5JY1a2huLlyd5VZ5VkLDcwzhUIA47ivJdH+IOteN/EEGheELlbJpbJItRvRjERjJU+Xn5QzHJr6nTRNCsvAM3h3w/LC0IgePzJW3qzsPmeVsjcWYktzyTXdR5ZRFqmfnjeWMj6zPZ2cIZmndUjjJfvwFPUj3r2Lwp8HjbXA1rxpKYEaPatnFgysM5yzchR+Zr0zStC8OeF5nutFhV7x2JN04ztz1ESHhB6Hk471deeWaQzTMXdurE5NbKqtkJUNbs0XvVS0TTbGMW9rGMJEvp7seSazGNOYjHFVmbNO5vYejgSrXZk1we8K4YngV0d9qiwQB4RuLjgngZI/WtqU0kzGortI5W9njNxLMx4ZjWY08kuFhXA/vN/Qd/0qQQpnfKd7e/T8B0rQt7P7Tl5XEaDgE9z7Vwyd2dEVpqYwgRMyMS7nuf8KKs3cT27tC3JHf1HbFU80ikKTVcseg9akY1BnapbpgZoQNGT4dVhosG7qQT+ZJrVkbArL0M40e2bpmJT+YzVx3LdTTluJbFaU5zUVv/AK3NXFsp5sjoME8+2P8AGlW3VIoJYwS0oJI/EgYoUWxOSIpVkEZlI+UHGfc1nspkNdHDbXN3AtixCIZeT3DBWP8AjVkWllpd210MTxxxBgDggsTj+laxpN6kynYd/Yk9/fG3swqKkUZJbpkoD+ZNWF0l7vQo3eRY1hMhOepIzgCr8lw+6OS3yhmuoxx6BUwPoKw/Ek/l6bbqjEK0krYHf5uK1SSuZ3b0Hznyo5tDOPLjgEhP+0XH9KyWZ5PEqQnqLNQo9zGDWvr32e3s5dbjkDG6jSJFz/dOWP6CvPNY1wQ68mq6ec+UsSjd32qAQfxFPns1cShe9ibwnoTw6hYX9w+2SfzDHGRghlVsE/iK6W+mt9Bexjv5VmKNKJ9vON4Hb8K4rxTql7L4hjuIpAsaBWtzEcAIwyDx3IPNY0rtI5llJZm5JPJP40+e2iQcnNqza8R6np1wkWn6MCLaHcwLdWZjkn6VymTnFW1tp5ziBCw9hVgWMEQ3Xkqqf7qfM3/1qXJKbuzROMVZGYRT1tLmYHykJHr0H5mrzXdnAP8ARoQT/ekOf04H6VkX2p3cibTIQv8AdX5R+QxVKMI7slyk9kamv2jxfD2W3cgkzsPlOeSBxXjvwosNS0+wvxqcXlM7oQOOcbvc+teuTuH8Auev+l//ABNc9ozMYJMnuP611YaKbUjGriJQpzo23sXJTk1saIfncex/lWK5JNbegruuCvrkfpXoHmI8Vvx803++3865XULKKHUrrVpbhVzbQoI+ScZfnHQfnXsX/CB65fSSyThLWEux3ynAxnrziub17w/8OdG+0XGu6s08zwqpitivy7ScE4ycEms5RujSEj6p8Gael54N0uUtgi0jGPoorq47Jba3kcNzjH51x/gK8VPBemE/8+6dPpXX3Fwiae7buWIrnTlsbvlMC7jjjjDKeWPSqO7HWmSyM7Ak5x0phYnk11xjpqcknqT+Yp/MfzrMskgvdDbS7tRJE7Hcp74IPb3qwTzz9a8P+K/jLWPCHhqEeH5RDdXF40YcgHCgL2OfWlKyWo4pt2R7y0MK4ECbVVQoHsowBmgPjivzq1T4ufFyyv8A7LbalLOQMsUjRlzkjAwvTivcvg98XvEviDWY/DnjBR5k6N5UhQI25QTggAZyBSjUT0HKjJK7PqUuKaXPQVCXNAb3rVIzuSCkpuadkVVhXHA9qWsTU/EOjaLtXUJG81+UijGWI9celZ48XWc7ItlBJNuQOdhBAz2OF4PqKhzQ+VnWDrTrw5sQT0Vgf6Vy1r4hvb26hgjsXiSTl2cNlB6entzXV3SZ09wO3+NVGSYmmtzRXmNwPU01PvVXF1HEh3/xAH8xVVdRjBzg1dybHXwkKoBonb0rnP7chHVTxTm162Y5IahyQnFmseCGrwn9oPRG1PwCb+EZlsLhJh/utlG/mK9gGt2Lgx5Izj86TXNLg1vRrrSpxuS4iZSPfGR+oFS3zKyBKzufnFa3EbW6OxHIzVXU/KukEmR5iYx789Pxrz3xUuqaHq0mnxSFPJd4iPdGK/yxXPprersT+96DPIHasHKMdGdii3szumE3QoePp2/H3qkyy5KlT0/r/wDXrkh4j1WPqyt+FTReI9SdtoVTn61nzovkZvzInXb1z61Va2hYnK9cVl/8JLc5+ePP41KPEYYgND1/H+lPmQuWRYeytmH3e1FvpNpJKEUDJ6fWoB4jsiMPH09qtwa7pxkBUfMCCOD2oTimFpHt/wAWruLw78MfDngLTwE+2p/ad9jq5KhoVJ9Asp/KrX7I8Edz8WxaOMrLp1ymPrsrzf4sarLq99pd4QVj/s63jTP/AEzijQ/qK9m/Yx8PaxqPxZGtW0LG1srWVZ5cHapkwEXPTJweKpyUpXROqifL+qQ3nhLxZeQ2Z2S2V1JGNwyMI5AyO+QK7XTtf13wmieIvBlx5EV8DlWAYJIDlkI9Mg4PpVr476PNonxX1iCcAGSfzCByAWUEj6561jeCIE1XSdX0mZube3+3wA/3o3Tfj6oWrG9pFpXid1ZftF/FWxP70204/wBpCP5GuptP2qvF0OP7R0uGUd9jEfzFeG3tkYXBTG1xkc1RMEgHK/lV+90ZHLHqj6fk/ai8Oa1aHTvEOkXCxOR5gjcc4OcZ4OK0LL4ufBi91pdbje60+4CiNgVDRsmclSDnGfUEV8ktCD95f0qrJa2znDKDR7w+SHQ+55dS+HHiD/S/DuupZzli3KnBLeoJ7YHSur0ZPFEOo2y2V/bT6dkecqyBjg/eIJVTz1x29a/OVdOtgw8tdpPdeK6XSrnVdMu1FnfXUQDcKJW2/lmmnIlwR+gvxgtIp/BczzR+YIwr4zj7rD618krCNe8LzwWsaxfZbmOTC55EqkHrn+4K+urtpfEXwphubli8s9hlj3LbM5+ua+Q9Di1bT9C1iSON0cW3mKZFIBMbYHX/AHqK8bhh5W3NdEuD4bFkRysZQn6ZxXAafoYZ/tt66xqwyNxArf8Ah5rdx4i0id70gushHA7ECvI9btr8XUkbzSOFYjBJxgV5dmd56k+o+F9NXE1ypI6hcmsi5+IPhmA4t45ZSOh4Uf1rxya2KoSayjwMU4wXULn/0ee8CQXfhjSZ49TAlt7lNvmKgbJP8IOOQcmon8EandxHU9JbbA4LFI2HmAcnG3Oe31r0yDSFu9DTRtUUWssDKcIwfCjrj7vOKz2nl0q4ktvDqTIS8e0S4+fkhjgHoB718B7eMpuUNGaRgr6HMxeB9ZtvCw1vUcWttKpX96NrhGJBJHXJHPrVvwrbzavA2jadGDPCjGLkbyFU7evIXOOa9T8Xa9a6rojaFeXSqsKLuUDcCzDhcZHP8q4PQbT7JpkPiDRiPKt5VSVmJ3+VnDkYGcfhXXCtpdnR0ODm8K6y9tNql1ewRLAN3zsu5v8AdFVfCvw68V67p1zfW5Zpk3XUcG3d5isOuADgkKCM+tesappXhrxCiW+nqZJrktK6ISAoQqBjcBxluldr4Y1a78ExXo0vM10uyA7sFEXYDu3Z4xuxjnpXVTrtjjHucRp/hX4o23he21vRdTV9PCiSAIVzyefk6gg5zkcd642Z/GN9dDQbaDYhGZZIcMzSEFdhVcn5snPtXs3heS6uopNCuNwgV3nilhGEVpHLOmD3+Y4I4xXoFhZW2mRtJbKBK/337kVqqUpy1Wg2keU/Dz4UXOig3Xi2XbE3K2MOASCc5kK4259M59RXuTTjyEtIUWKGMbY4kAVFHYADiqPmF+W5pu7Heu6KS0FylkvzRv8ASqZfmmNPsbavzfyrROzGXmk45qg94HGLYbz6/wAI/H/Cq7o03M5z/sjp/wDXp7uAuMYGO1U6nQHEjCl/nmOT6dhU093NMQZ2zgYGapCQ7ABUbZPWs7gkWQ5Zgo7nAq1cSBw8afdiUAfietU7YgSgt/DlvyGaSFt1tO/pt/U00xsWeTzLdGJyR8p/n/WqBfHFSu+ICT65qhupN2GT7s81DO+IHb0U0bhVe7cLZzE9Nh/lSjvcT2Kmkn/iU23/AFxT/wBBFXbdJLm7SCLqzD9KzdPYLptuvpCn/oIrS09UkvohI2wbs5+nNWtZWF9k6e6ijgYr5gZ/LbIXoBwP6Vl2Ext4EnT7yQMRn13NitJ/s8959ktAQzQthm75bpWOzJabrKRhujgAP+8STj9a63pqYLsacjnz2/66v/6LeqtrAb23+xggM0IIz7O2f51l32txCRvJUn94zAnphlZf61iLd3EhUliNi7RjjjOcVLqpPQag2dwus2Fi00Uo3vG+6FhyN20DOfqK4y61Ca4t4raTBEIO09+fWhYpXGY1zUM0UMfM8n1CjJ+nYVD5pGiio6GLO5PDcj0rJa1nkIkSIuqkEjsR6E1tz6hDD/x7RjPq/JrmNQvbi45dj9BVJQW7CzNXUWgv9S+13DRwIMKkMZ3FVAwBxkdPeiS7tIFxbRAn+9Jyfy5FcpG2JB7mtEuR1qpVktkQqfdk0+oXE42yucf3RwPyqju54qN3B6VGG9azdWT3NFFLYJHYZrLnfmrUzZHNZM7DNTcEdhujPgN43OP9L/otUbeySyiZN2d2Kjklx4Hf0F2P/ZavXBG0fSvYwSvTueXi/jM+RlTpzWtoTlppMEg7WwR1Hy1hSVq+Hj/pLr6g/wAq6zlueFXV9fy3M0WoyyT7XZQZGLcZ964/WWgSW7RYEd/s6Pufn+Ijp0rvdRgH2ic/9NG/nXMa5cajBpt6sQ2wCxBLheS29uM1jNm0Ern2J4BvHk8D6XMrcNbqRjpXXy3LSQbGPevOPhTvm+GmjTN/z6r+hNds+4YJ4+tVFK1yZN3ZI3ynFRljmqz3cEYJkccenP8ALNRC78z/AFEckmemAAP/AB4itEzNl1jlTXzf8d7e9jtYL+3hEkUU7qSeQrMFIJ+oBr6F23shClFjHclsnHsAMfrVO60yy1aG80/UYxLDMw3KelTNcysVCXK7n5y6pqniqNUFsyiOQdVYAL9c4xXTfDey1tvFml3OnLLdzpcxtJKisUVc/N8+MYA6819jaT8JPAOlSGaGyEjZzmU7sfTgV6Altp+mwiKARQjHAXAxWMadnc2dZPZFg+9JWXLrGlwj97Og/HP8s1Rk8U6OnCs7/wC4p/rit+ddzn5Wzpc4pua5Y+Kom4t7S4k/AD+tRt4i1NhiDT2z/tPj+ho9rEPZyOq8iBn81kUv03Ec/nVlQFGB09K4v+1fE0oGy1jTPqxP9BURm8XyHrEg9gf8aXtF2GoM7pR8wq8QXt2SvODF4obrcgf7qn/Gsy707xJI2ft8o4524FDqPsDp+Z6TdI4tY5ACRtA6VmDeOxr5a8P6B468bX+q2S67dWsOnzeWu0Bs89OoxV+f4YePbEnyPE12T15Qf/FUvaNq9i/ZrufSp6c1Czc18uy6B8W7EgW3iGRwP78X+DVXOo/G6x4/tG2nH/TSNx/Ims/aoPZN7H065ABCmuw0HUhdwm3kP7yPnnuPWvjP/hPPi7an/SbSxuAOu1nXP5qasxfHHxV4eP8AaWr6F+7j5doZgeDx0KiqjVSYnRbMH4y+GLbT/ideR3EYMV4iXUfplhtbH/AlNcCPCWhzKdieWxBAPPU1v/FX41+GfiFLp2s6XZ3NrcWqPFKsuwhlyGXDK3OCT1ArzI+PbZxtKsv4VUnFlKM0Q3vheK0laKcbTyQexHrWX/YsET5XBwf6VqSeJ9PvVAmY8etQ/wBpaS5+WTH0P/1qm0S7tGE+kIxLA1F/ZRUhgR610HmWTt+7k4x7Um2NuEkHGe3r+NS4oFJnIT6POXLxkYJp1rpl7C+8pkY9R2rrDC23AZTTfLlQjilyIamzudD0EfEWDTrCS5hs47Ast5dTuESG26lzu64CgAAEkkADJr2XxX8f/Dngbwwvw4+CLPb2KktPeRgpNcOepL8MB24OcD0r5qsXjt7mRb5X+yXSGO4VOuD0YeuGAOPauZv9Ml06UI5DI3KOOhH+NP4dhbmxFrFrqoNvqoKu5Jye5J6gnuTXp3wW0f8A4qzVI7xMwR6FqTs/8OBbOVP/AH1j8a8HZQ525r6m8I6PP4E+Ft1q2tybdQ8RxC1s7f8AjjsiweaaT0DKhVR1O4UQ1eop7XR84+Krq5t9YaGFyMIDj061iJqN/wCVvD5Gcc10+pCK9vZJ25ycD6VU+x2+NqrgegpSTcmXGSsrmQus3i8kA1ZOuyqdssf1qw2m256ZFRS6fG7by3NTaRV4sE1qLOShGO+KsLrFrkFW5+hqqmnDlM/e4qdNGaEFshsU1zEux+k/gRzffCXTWOQTbbf/ABzFfLfh/wA2bxXNpFyxcTpPCQTnqcj+VfUnwp/efCvTR6IR+grwHStAUeNr3X1mIt9PlLS/Jjll4QEnknk/Stqy0TOaGkmjw74WiXTr250+Q4LLnHupwf5UviazMepyhRwxz+dX7UxWXjr/AEb5Y7h5AM9t5LD9TVrxdbkXCyMc7x/LFeS5J6o9erHlseZ3NopBArngtghO/LEHHT/Gu3mjLNkelcRPCFuZEPZjVxVzJvQ//9L0gW9l9mfULS3aa4ILeWzHJfBOM9SOuB0ryjxT4sj8Nack+oTC9vrqTy444HUG2UYPRFyc8jJpmneNtE1Sa38MeJrSUXcrkwGNXBdsHawK4IGDkHirPjL4b2l14Xe58PQrDqFi26KYNyQfvpIVJy3CkFsn3r83oJUqqjiOptc4PxH4o0ie8torppY5SqPtPB9Szccn0J619AfCRLTTPCjPrkRJaLzWEoIGwLub0GcDrivAdE0rUvFunQahcWay3tpG0d3M+1HKj5RkcZVVGAcV794J1h9U8PT2TD7Qs8LxZJypDIUHJ5wM167mrezgjSDtucPrSNd+MbTVtLtJ4rFopdghkIEhYcYZQDwRyK9I8KaPrE8ctzrKpBBchP8ARgDn5V25dick8e1bXhrwtZ+HbBLYFpHUfeZi2PZckgD6V1O7tXfQwzjH3i0mSW8ENrGIbZQiqMAD2qYv2NVg2DxTZZRkAda6S7FvzfQ0xXOcZqqrFR81LvAdvrTTAssxYEE4qPIXAquzselN3nOKGwLQf3pkr8dahVsVHK5xSAFYbeKQtxzVZJAFwaDJkcUAWo3xkn+6a0dKtHu7G5CHB+XHuVySBWErMc4/u1pSXT2nlQQN/qfmOP7x6/pVxfVkyKcn/HsxP97FUA3vWhqEsciiWLgSMWI9DwCPzFZKk0plWJ91UdTfbptwRz+7b+VWc1nak3+hSr6xtRFq4CWXFjAp7RJ/6CKuwzCGUS43be1Nt4j9jj+X+BcH6AU4W7gZlwg/2v8ADrW7ptaolNbCT3s7zC4QlGUYG2suN3luSxJZjyT1OavzvaRJkZkPvwKz7e/kMrCMhBjooA/Uc0Nd2C8ixLZuMNKRGP8Aa6/lTlazg+7mQ+/A/wA/jWbMwL8801m4zT50loHKaD3s0iBN2B/dHAFZFxK20qKm3fJuFZkr9T61m5tlWKUhI6msa6PFX53OdorKuXApAVlfEyg+taEjmsgOPMH1q08hC+tO4C7iTTC5BqLeTTGfHFMCKaUHrWS7FnxVyd8daynkzJgelUiTrJxjwJIf+nsf+y1fuSdorNuHx8P5WP8ADdg/gNtZ2j+KdG8UQSSaO5cQkB8qVIJz6gehr2MFJKFmediaU5NzS0Rec5atbw//AMfbfQ/yrFcsD0qxZavp+ju15qLlY15YgFjjHoATXYcVtDzu/TFxcDH/AC0b+dcb4ltNUj0e71Ftws/sfljJ+XfvY8DpnFeqR+OfhdHO7pA1w7MWJnDKmT7Ej+VZPjTxx4V1nwrPonn2trbydIYFy2QD1IXI6+tRNxsaU7p7Hrnwbbz/AIWaMGkdB5DA7cc4kYdwa7iZNNhBeZiy9zI5/kCB+lfO/wABNE1jxD4TaW+1K6ttPtpmhtoVYorDAZ8Hg43k17tH4E8GK266g+1MO8ztJk+vzE1krjluUrnxf4T05dpuIAc8BNpP6c1Qbx3HcHbpVjd3ZPQhCFP44NegWOm6FY/LYWsEPpsQL/IVeu9SsdMjWW9lSJT0JKjP09ad5E2XU84jv/Heof8AHtpcVuOxmcsfyAWtC10Pxl9q/wBLvIkEyklY4sbSuO7M3r6V0qeLLOXIsoLq4PYojBfzOBQdR164lZ4NO+UdPPdQf0NWo3DQzv8AhELqQZu9QmY+ilVH/joFPXwXoinfO0kp/wBt2b9CauC68TD/AFlhFj/YkGf1NSx6wocRX8Uls2cZcfL/AN9DI/M1Xsl1Qud9CKLwzoMXMdup+oq8mmadFwkSD8KvqFZd278jkVGc9noSgugry7jUt7dOEUD6CnGGM9f5VExmX+I0GWTHU1rePYzlzdxfs8PalFvF6VH5snqaPMf1q+ZdidRzW8AGTxWLq89tYWcl25ACDP8AStVnfHWuD1PVxF4vsdKuNpgkjldwRuyybdvGD6mpnJArlv4ZeG203Q5dQuk2zalM1y4xggN90H8ADXfSaXDP8zLVA+INLRBuuUX13cfzrSt9ZspvkW4hY+m5f8aqMoJWFLm3Mufw5atztrMm8LWbDmPNdus6MMxkEexzQSrdSR+FDpwewc0keay+DrBzgoPyrG1P4caNqVpJYzxgrKpU/iOv4V7NJats8wY29qpmNT98dKzdGJSqSPyF1/wPquha/e6EvItZmUAjBK5yv6Yrl5ND1ZGLGI/gK/Q345fDe91KePxn4ah8yeFNt1Eg+ZlXlXA7kcg9+lfMiTWk6q6FfmGccZrJ0FfU6FWdjwKS0vosxyREZ9qomGROdh/KvfdS06O7jzEAJB0Pr7Vx7WdzFkyRsCOvFZzo2NFWv0PLSSOhIp6yzL91mH4mvRXtEPzOi456j0qs2nWbEjy1/Co9myvaI4oaherwJGqzHrN+vV/zAro/7GsWOSnX3/wqA6DBjCkjn3o5ZD5osz4vEF0g2sA2at2/iHA8meJWj67TyPwz0qKbQGA/dOM9gcCsa5sbq1OJUP1HI/Sk3JAlFnoWma3o1hMLqCG1DLyDKrPg/wC6Wx+lS6v4/k1a4kn1CeS4lKhA7/3VxhVAACoMDCqAOK8vCOx2oCT6VfXR75huZduexpqb6A4R6m6Nc08DBX9KU6xpxHA/nWC2i3meMVKukzlVSQY9SKOeXYSjE211Swk+71pv9oaeeCR+dYCaVej7oxR/Zd6TkgfmKXPLsNRR0YvdPzlWzjnrVuO7D/PHz6Y6VyqaZeE7QuSR0GK93+F2n+F7uzh0LWGKX08hRMqdp3fdy3QZ9zQpy7BJRSPqv4U+I/Dtl8L7L+072KDYG3IWG/oOAD3PavNvHXi3Tbq1a20NUigLlhGhyWYgAyOepY4AHoOBWN4h+FsmkxPqNkmSn3gB2rzxYYxyoxVSnJrlZgoRT5kzkNXmdNYtLwKFKyoOPTIFdh4tt8RRM3UHH5iuS8XQstqs6c7SG/Kr2s+MNE1GzSCOUmRiCcKcA+5xXA42k0erN3pQkc2684rjNTjEd8x6ZANduBG3zoc5rldfj2zpIO4x+VOD1Odn/9PhPBNnrF9bPdWmnsq20YlXe6+cdoJ+hHtwcVxuk/FLXNLSW1vAohmlkDzkkgfKPl24zkY/WvX/AA7JD4fmuxDJcP5sbBvNYDC4OB0449K4qHwD4a1u7lFsl1IgcyyKhBUHjpwcE18lRoUpzl7VaHS6Z5oPHcDaZefaXkVpTIi44Owr37fPn14r7Z+Gtx9q+H+k3bqqPLbRsVQYAyo9a+dtR+HnhqTRbpLy1feHBt9rcxoVH3yAMsTz04r6V8J2kel+EtO06IELFbRKM/7or0YwppNwQ4qzsdfuGATT2ZQuR1NVAxOB2xSO5BAzWsZWRqixvAODSTEBlqgZSG9asO+4qakZJy/C9acp3uc9M0622+YA3SmXNzEk37rBHtVcttxGrBZhHBc5PXA6VlzsiXDKMde1JLeTzRccAdSP5VnbjuwOTSb6IZeEhFQyy54q1a2U12WO4RgDjPc+lJZwpJGlw+CfMIK+wVjz9SKaiwbRnqRihnwOKS4Gyd1XgA//AF6ruwxUgXbZz5gx1wcfXHFRMxJO7kmoIZvKdXAyVOa1WjsoUN60ocfwxjrn39hVLUNDPvX2FYR/CoB+p5/rVNW9ahlmaWQyN1JyaVTSluBKzc1mam3+hSj/AGDV1321k6lL/okn+6aI7gzpYrsxaekKHBwMmsxn7k1W85gm3sKjaQkVvVqN7ERjYhu5DtqlZPudyOwpbt8LVWxb75FY3NEjRkkqCSU7aaz54qtLJ2FO4FgyHYAKoTyYBAqYyYi3d6yp5CKAZVlbPWs2c8VbdgaoTthTnrVCKbMBIv1q8WG2sdpczKB2NXmclcDigQjM2/npUbMKaz4xmqjy/Mc00MjlbsKzi53kVNLJt6VRdsP9asTOlvrlrf4fXLDvcj+S15d8G5FWzv0GM/uicHP97r716Fqrbvh/cJ63Sj/0Csvwh4X0/wAMRXH2BnYzhS28g9M4xgD1r0MNFuUGiZV4Rw9Wk93Y6W4mOaw7x95KHuMVpXDYOaxnPmzEnoK9NnhI4S80dIpSyr15rlNY06B13YwRXql6o5IFcTq1vvjYDjINZTgjVSbZ7p+z9em++HrFzyl7Oo+mQR/Ova84rwT9mwEeBr60bkxahJ9eUQ17fqd4mm6fJeyDdsX5R6seAPzpRkkgktR76hqM16miaLGJryUZ6/LGo6s5/kO9a1voOg6JMbnVM6jqDcu54RT6KOeBUuh6XL4W0dr+4Hmahf4eSQ9UTsg9O5qhJI8khlkzlu5oS5ncTdka51VpNysgRT0Cdqy5bgyTsUyB6GuB8c/EPw94B083usPukx8kKEB3P49B+FfIHiX9prxlqUzJ4eji0+I99okf824/Sq50hKDkff6eeT8pIxVkXjMvlXIDA8HNfl4nxz+KiyeaNXk65x5cWPy2V6Z4Y/ah8UWMqR+K7aG/h6M8Y8qUD1GMqT+ApqvqJ0H0Puz7OLEeZZndEeWX09x/hViKZZUDrXLeDfGegeMdOGqaDMs0RwHTI3ISM4cAnBrflj+zTbk+5J09jWllLVGeq0L+73pu/nFV8+9ZdxftFqMenqv+thkk3ehTGB+pP4U7A2bufWnj7ua4DStQ1LU7aWKScgCJXMqhQUYvKpUcEdFU8jvT0e8aTR7m4uHE0oQOPuxuu0E5HQs3P40IVjujzXmmoSNF8SdMI/ihmH/oJr0oZJrzTXRs+IekSdisw/NR/hQxI9dWO3ugtveoJIpMq6noQa8B/wCFU+Lk1e5t7XUY1hE7iJC0e4R5O3IMinpjqK94V8Rqw4wavX+nwXDPLbwxLLfIpa5diuzbgE5HA4Hp1qKsboqnKzPK5PhD8QLK3STT78Suy7sGIYBz0ykjfyqgNO+NOhoTJaxzKpxw0iE/nHj9a9NWW+Jh06a+4QEG4gmcEZ6AgEKeh7Cub1XX/GmjxXYsNQlufKQGLzNrjIHcMrZ/OsXzR1ubXTdirF4l8fW2lve3+ls1vD98o6Mw/AsCfwFQaX8UdIvbtbG4RoZX4CyKyEn23DB/Or3gj4o6/r/hnUX1eK2naGMPjygm4YBOdhFc346stI1/wq3ifRbZILiymTf5eSCGyVYZJI6EHmhVWKUUeuNKGVLhMkH17Zr8ufinod94b8W6lp9kxAt7p9uO6Od6/owr9JPC2q/214etr4f8tIxn/eHDfqDXyf8AtG+GpLTX7fxVGv7m9jSKT081QQM9uVUV0tc0TKDtI+QYtf1mIE+ZnHYirsfi7U15dFP44rsE0jTbtCHjAPqOKxdR8NW0QLW5YYGcdax5JLqdPNF9CqPGJwBcQHnvUg8SaNKf30ZBPtWDNpUjJtQjg981myaZdRfw7vpzUc8kVyRsdsup6DJjEhX/AD9KsFtMmJaGdQD24P8AUV5s8TJFiRDnd+lRg4+6CPpQ6r6oXs10PTzaqwzFKhz+H+NONlKRklWOOea86EsscaskrqTnPNS/2nqUZ+SYn64NCqrqg9k+jO5WylXd8gGOe3P61E1lOf4f5f41yf8AburR43ODkZ6Uh1/VmYAMBk4zin7SIezkdWmnzFjuAH1x/jTTp8+eAB+Irl21rVBnMnQ46Cof7X1MhiJcbR6Ch1IhyPodf9hmHDY/OmfYJBwCoH1riW1bVnDOJGIHU4GP5VM95fMF2zMSRnjFT7RAqbOxigMMod2GBVmO6a0kS4hYB42DKfQg5FcQg1GYHLOTXWaJ4aubpftN1I3y87CTVqV9hSj3Z+lul3MWuaBa6qy/8fMKufT5hXgnxA8D22jwXHiGyYJCg3yRYyfcrj+Ve4aFNFpnw2sbp/uw2aOcegTJ/lXzh4i+J1/4mtXs7Cz8i1kyjSzg4bHUA9Kqo4pamFODb0PAdc1211OI2sKsBjKlgQT+GP615kFCAr6V7FqUNmIDI8kDbR91SNxx2HFeT3a2gJKbuWyfp6CvMlK09T6OlS9rh0oK1i9Y6g9pw2WQ/pWlqEC39v50Dg7RnB4J9vrVzSpdCewjWaLcqM28E/McgYP4YrndVNtBKBpUjGMjJDEE5rljiE5uKRl9Vs7Nn//UzIJbfULye0vMK18y28TcKAzcMSfRVBNepNdeBPD15b+F9JuhNBHGGvY1fiQg/u0J9c5JweeK8UtdW8HW06WGozsyuiopSPHzcFmUsQMAAjI9ayxqGl6DqTXOl39lIboH5XblRkdTjg18zyNuyO3msfSfxF8T+GLj4fy6XZNa2jFlZLeMrvPX7xHPH1q/aN5VlBEf4YkA/wC+RXxZ4h13Sp9VWxa8t5JJHVSYWLKSx6dBX2lP8j+WD904/KuulTcY6ijK7bNJXBYgHpTixzzWdFIS5Oehp5kJY1TNELM4UtinpPwG9KpzMctimW4ZxsB6imtwNHz3c/MelMkWRmxEpY+1Ps0jWXc/zY9elX77YuJIQBuZunHcir5NdSVIr4ljSRSRgAZxz3GKvRGOKdVUAEDBPf1/rWXE7COUHnJUcf7wq1I2y8kc9j/7KtNJIcmalpIPtDsf+eoz9N9RWsU1rMtvcr5bNKeG44KtjrUVo27zZADhWyT6BXyTWLDPi3SaRgT5jNtJ5+6cH86b0JHXEhe4dh3Y/pxVRn9KrtKuST35qsZTWT3LL5cAe9RPIOhqn5hqs8vPFIDRaQAZFX/sFwLU3bfKAM/hXOmT5ea7+SyuZNCeRgwKRBmbjA4HHXPP0qoRvcTdjjHlyOay9TYi0b6Gn+bk1S1F82pA78VKKNXzB0qKSXAwKrbj1NQSTAcCmwCd+DUNlIFD1XlkBJpLU4DH1oDYvtKKqTMSaSRwoqi8p+9nimI0GbEQ9qwbibnrV+S4Bg/CuXuJnmbZErMevAJ/lTAuvKO1UZ5D6VSWdx14PpXUeHvC2o+LPN+wuiLBjeWznn0ABpobutzjnkCzKO5NXWkPHFdVqvgO506MyxzG4kVsBUU8/magtPBHia8GTCIl7tIwAx+GaakpaIc4uO5yEs6rkkgAdSe1Zy39tOreQ4cr12nPNet69pnhmPSW0rXdVtLHKqGO9M8D03A15a/iv4BeEhIZNVfUHzuIiR2yfbIx+tO0uZKK0HCVL2TlJ+8V7cNdTRwtwZGx9K2te8MXlrpa3OlxT3M7OFwibsDnnAFcFqH7SPw5svm0HQ7mZl+4ZPLiAPrkFj+lcVq/7VPjG7QxaNZQWSYwCx8xvz2rXUqUnFo5o4hRmpNXR6+2na7Y+AbmLxFG8ckl4rxK+Adnyc4HToetbtvaXsAYzROMqCMg18SeIfin4+8Ur5Os6lLJFnPlqSq/lmsseOfGUYATU7oYGB+8b/GuzDQ9nFcxzYup7ao5JWufb91vHVT+RrC8zEjA5HTrXyInxB8bAYOpXB+rk/1pR8RPGiHIv3z7k/411+2RyeyZ9bXSMyZArk76JsZ/OvA0+KvjxQFN6SB6jP8AWnf8LS8YvkSTo31Wl7SLBUpbn1R8E/FeieEbbU9K1u5ELXd4XgUgnJKqp6A+levQ/Ev4caz4lsNOu9XtIre2fzZjLIEBZOindgda/PSTxRcXNo1/cf8AHwzhlKDjIPP6VgfZr7UJC2ws7ZYhQWbH+6MmseZmvItz9ftW8eeDdXl8201Wxl3HgJPGcD8GrzDx/wDELRvB3h+XWIpoppGDCFVYMCwHtnjNfGfw98K6KuivcaztW4ll4SUFSEA9/fNc18VBo2mzQaRpCjJXzJHUjHPRf05+tTGbWiF7LqefeIfEWqeKNVl1fWZWmlkYnLHPX0rDxTafQ23uXYBTsZpVUt0qzmKOLai5Y9+1CGkdT4G8aax4C16PXNHcjBxNHn5ZU7qw7+3oa/T3wb4n07xv4Yttd00gpOuSo52OOHQ+4P6V+STKA2GP5V7n8H/Guu+HZZ9I8P3cgMxWQRY+Td0Jxnr0onio0Yuc9i6eDliJqnDdn6LBvz71zGpJfvfQ3tqjyeVKUZAv8DRSKWzjpkjoaZ4Zm8WZmsfGEKx3KBZEZCMOjgEdOhGea6mtsJi6eJpqrSd0c+NwVTC1PZVVqefW+ma/YabLb6faKxnCM0bMqjdvk35OR1XZzXSS2urX01obkRxRRtHM6LyVdMHYvJ4yOv61vAnNSrXUjjuTxk7cmvL/ABQXXx7ojjpmbI/4DxXqqjMRIryXxlIkXjDQ2lYLl5FGe/yUWA9e3futtaM9umpaFJat5e6BhKDMNyYQgnI9MVmDoR71qadMsNyC4yjAhge4PWi2liOpwmoXOs67i4+ywoqlo1a0XEZHBByM811OgaGmo2wklUzJHF5TqDy75PHHPGRk1xuv+GtU0tHsrMr9laYzROp2jbtO5W9xgfnXvXwhj0pfBaOqfvJ52RWx34/xrzKtZ0rxZ6tOgqiUkcFo/wALJ7CG7a1EMEM0LRLGihPmPCrlvmJ+pPvXHeANC1xL3UvD2t2UrJIpW4lOTs7oCM8cjjj1r3bUraO81TyBciCRG+UZy/HU44xn1zW9420XTZdWg1EXa2Ur27hpNpYSAEY6dxk/nXKsWm7G0sMrHxz4Qvm8LeJL/wAFX+UEcpkgVuMo2N23155/GvR/EfhjSfGWhT+H9VTfBcDII6qRyrqexB6GuS+Kng+TVltpJ5FttQVDJa3OTiaMEhTuH3SD2btjmvMdM+L2seDpBpfje0l2xDBmj5GPXpketerQq3irnm1qNndbnjvib4LfEHwrMzWdq+o2wJ2yQgM2O2VBznHtXmN8NRs5Giv7aaB0+8JI2UjPTORX6UWXj3QLkpDPL9nllRZEjnUxsyt0IDcYPrWko065v5Z8JIksSZPDDKlvT61vZPZmfP3R+UxSGViYnHJ5H161AYpUbOM+4r9PtZ+Gvw+8QZ+36dAzMOWVArfnivJtZ/Zn8K3eW0W8ls27Ajeo/wDHhR7NjVVHwoyjd84x9RUDWtpIclFJr6j1T9mbxnabn0q+tbsf3W3Rt/Ij9a8z1X4R/EbSWY3ekvIo6tCVk/kc/pUOBaqdjyRtItDbloxjnpnpVFtGTHysR9a62702901jHe281uW4xKjKB+YxWcAG+64NS6aL52c8+izOFw33RgnB55pV0XaQWfoQfSt4xyj0PPaneXIRjgfjU+zQ/aMzBotvJ+9JLFjzjt+VKNJsUGCOT1ySK1IwFyruuDx9Pzq9DYmc7LdJZT/sKT/LNPkQnNmKlnbRptjQBe47Uu2MDaqgfhXfWHgPxdqJAsNJuJM9Gddo/NsV3umfAn4jag37yCCzX1kcfyUNTUBcx44pIijBXt1/H/Cp4Jrpp1tLUFpZm2Io6lm4A/M19KWn7NGqPEW1PVYw2PuxRsR+ZK/yr1LwT8FfDXhG6j1V83FzHhlkk/hOOwycVdmQ5rudpq8MmhfD/wAjALWluvDDI3IvQ9iDXyB4z8Y+KPHdnJpGtTq0NsgaGKFFiiXI5wqBRk9z1NfWvxDv4JNCOjKSZbr5Aq9SAQWIHsBXh0Xw2OmrJeyXCuUKtzxuVhwACe3T8K5cVOKdjpwUG05tHyS2nxAkoM45BLZ/rVGKzhku2jlVcsu4ZHcV2mq2P2TUrm0cf6qaRMeysQP5VzNxBKp3IgfHQZwRXkX6M+ooRjyOO1yN9ORcHp9MCqEulwluoFWw983ypGi/U5/kKgkkv1HMiL9AamKa1uN0qb0bP//V+TriO7u7VGmfaSoGW/h/3cGtbSNYttM0wafBaQXVxKMySyqflUcALg9/Wud1W+lKBJRsQHBDDlv9oKf881CtzqawW0qR+XEEIRgOGGfWvNhTlyu51s1Jni1HxVpFuLaG3P2qIHywRuy45OSa/Qe4l3SE+rZr89fBn2jVviTo8U/RbqNvwV1Jr75klG3Oeac1aKQU2tTRtpAVJ96eJBms60cBCajabDGsbGiNF5CSxospPvZ9P6is/wA7kinW0yIzbzgY7/WqitRs3IpTGxYf561cndZoV8vJIzn6lj0rm3vlRyUG769KhF/PJGULED0HFaSkrGaTNdJjBC6M3U9D6gg0t9qEUjsYQ3zAHJ9e/wDIVzLzkHOeaTzyeazbKSNhtQuTGYN5CHOQPfrVUTENVDeWPFDPjjvRfuUXfOBNPLgDNZMbEtzU8su0YzUMCd5sCqXnEmq7zFhikiPzUWA0IiHmRG6FgD+Nes6q7Wrsvz/ZRGF/2Wcp3PtXjJk2Tpnpu5r0HUdSuhA7SOXtQpeJR0yRj+tdNKN07GdV7Hn3mHtVa+l/cfjUIkwMGqWoSt5Cgd5F/rXP1NLaG08wLEVUeb1qGaT5ye9VCSetAFh3GODTo32oRnrWc8mOBThJwM0DFupJfLwTgkdq7HT/AAZcTaOuoTykkqWEaLkkc9ya4ufXLXwnpN7431OBZ4dORfKik+5NNKwRF564BZuPSvnjXf2vPihd5t9EW002MZ2iKJWYD6ybv0q405y+FEupGL1PpjQPDPjTXrJriWw+yASMi+a2AVHQ9O9es6tP4Y8P+FF0vWb+y06RYVjlmBDMSAMkfWvyq1n4xfFLxEzLrXiC+dH4KrKY1x/ux7RiuRvYbadfPlnaaVjy0jFjz7k10LCye7M/rCTukfetz8Rf2e/DClJr+61WYHnyguP6Yrkrj9rTw5ookt/Bfh9lRv4p5tu7HTICk/rXxMbWFRzIPzFTw6a9wMwAuP8AZGauOEpp3bIqV6k5XbPoDWP2pviPqDs2nRWdiG/uIzsPxZsfpXler/Fj4ja8xOpatcEH+FNqD/x0CuUl0uaIHeCMdc1S+zD1rpVKC2Ri23uxLi8u7pi91LJKzdS7Fv5k1WHAwOlWDAo6tUTIB0Oau3YlxGZNJv7Um3PfFKEGeopiH9s0D5uBThEWQspziocFjgdaBl/7JdBd5Ax15NVCzd+KaVcfep8nUH2FDAbk0mTSE4pu6gWpdiuAsPkOPlzkH0r2L4NLGfGjy/e2Wznnn0FeJDmvY/gl8viO7YdRbN/MUm9AW56T8VNTOn6HI9vtR5nVFIABHUnH5V8syzzXL+ZMxc+pr2v4w3jMlraZ4LM2PpgV4evFKDdge47NW7W2lu5fKi5Pf2qqqPI4jjGSeBXfaZZxWkRbHbk1Qipa6DGqBpyWb0HAqw2l2uCAMVptOpHAqEyKfamijmruwMBJGGU96XSNTutC1KPUrA7ZEPGO4PatyQBuDXO39uIn3DhTzRKnGacZLQcKkoSU4uzR+jmm6wLbUItTvLLVg8sSozyqjRqu3joQa7tPEGlnhpNv+8MUvw41+LXfAuk6w8m4S2sSuQedyKEbPvuBzXZSDSJVw+0/7wrbC4WnRhyUVZGGLxdSvU56zuzlY9X02Q/JMpq7HdQMMq6n8a0jp3h2X70cJ+qiozofhtj/AKmL8AB/KutRZxcyJI3Hk9R+deB/F7d/wkPhmRTjF84494mr3xdD0NR+7QD6MR/WvA/FunP40+LOm+CNKkMEWmRtfXMw+YoWGxRls8nP60Sixxep9COMM5/2jUsBO/mpl0O5MYUXbN6l1Xn8lFPTSNWjGUaOT8x/Wq9nJEOUbl4SqyNbXKCSNv4T/Suh8G38Phe3lsLBwIJGLqkoyY2P90gjIrlWh1KM5ltieP4CD/jVSS78psyxyxkf3kYD88VjUoxmrTRVOtKDvFnQy+G5tZ1+KS1fmdv3rsxBVc5bp7dBXd6xHDekyXiHyI0a3s0Y/M5cqWfjsoX9a8ng1a33gQTrn0Dc/lmtZNVvVkWfzCzoMKx5IHoM9BXNHL6alzHVLMJyjys1fijpNlbeAAt4C0ksX2VNpAKqAxyCQectXxPqn2j/AIRTVvOcTxInkw+aoZgXKpu3DB6nivq/xc03jSKOHWp5cRKVURkAYPfbjGfevF9d+F98+gyaXo1wkm+eKQo+EBWN1bA6DPy1pKm+hnGqranx94n1LXX16RPNZ2jzECxzhFPCj29K+r/gQl63hKa8vpGkLzbQGOcBR2/OvnXWPht480SSS4vtNnfeTh4VMi4+q5r6u+FljJp3gK3VwVkZpHIIwQc4wR+FaRQqkrrQ9GBPanCWRehqn5EaFJYMhjgk56g9c1aKtjOOK01RzEwu5F461IL/AKgr19KpYpux6dx2Ir7T9E1SIwahbRyqezqD+vWuC1P4MfDfWPnksVjb+9ExU/1H6V6B5THml8tgOhpuw9UfPd/+zJ4Tlk8ywvbqAH+E7HH8hViy/Zq8F2+Ddz3VwfdlUfote9fvh0zULfam4y1TaJXPI4TT/gt8O9KIkhsFdh3kYt/UCuysdD8O6Yvl2tvDGB0wg/wqZoptmSG/WoVjbrtP5UWXQV5Gm09rGP3fbsBioWvj0VePeqRRvQ/lUfOOadyXcne8nHKkD6V8+fGD4neJvA91FZaTHDsuY94mlDMwYEggKCB2717q4kdgiHbnJJ69PrXz3+0RpDXnhW21Yrl7OXDEf3WIX+Zqajag2i6aV9Sp4F1OG/0i48U67cTXl5cRhvMchEiUnJCAA8E4B4zX0QLezu/DaNdW0TMbMXCyKx3bRIygEHjrmvh74V3Gq6jbT6RZWrXa/KuFBOFLZx6Y45zX1VaaPrskv9oeI7krG0C24so8KEjjJKg7OMMWJNeHUw060ldHuQr06ULpnyf8QbVLXxrfrGMLI6yj/togf1964kruBGK9A+KTbvG11IRwwTAHYbABXCxdeVArlrq02j18LLmpqXcrrCgHOB/n6VBLZQvkYrS86ND1UD61BLe2qjDyL+dYa3OnlR//1vnPU/hZ46ubkoircLGAA6NkY4xk12X/AAo34m3Xh+MXK28cNvkBpJlUYbHygZ68V9cW9lp3hvTZItdQpcIyqYQeTn0I4rVkvbLXLYTainkwL8kUKngn1bnrXgfW52skdvKtz4l+HPw317QfHdvqWobCkG7O1s+nIr6gvHRHaMdua7DWfBsWj2Vrq6R7C4J+9n5W+7x/9evPNSm/0lgOOK9CM/aUecwi2qnKalnLhMVDJJhjVG1mwnNNeRs5NYHSjREoxzUDXAD4NVTLlAao3Eu0hhTGbTSjt3qOJyeB9Kq2nm3KkRgk4wMetakZtbJraKdCZWJY88HcSo/KrjTb3JlLsVRG9xKI4+WOf0GahSXBK9wcGtDRmWTUPMHRFZsVz81xvuHZeMsaTgrApamssvNRyzZOBVprOGKAyvJzjOPcisAzMJCp6g4pShYIyT2NRH2nJqGefmoPPwuTWc9wGPWpRR6PcCNPCKyoqhmC5IHJ+Yd65CBj3rpQ7X3huLTbNWabC5GMDqCeTXLXCTWErW9wNrrwRXRiI7W7GNF73I55l80B+mefpXXX2sWC2kht2LF1IRScAbvb2rm00h7iLzzKAWXIAGefQ1KdLtoLdpCWcqwU8gAZYDPfPHanThNLQc3FmMHyKq3rgIg9ZFH8639YitLaKL7MoXeS3UlsccHtiuTvpdvlD1kFZTjZ2ZcZpq6NN5ASTURfiq2/HFNaXArOxQ89aZPIqoeccUxZAeprQ0aC3uNR8++OILcGaT/dQbj+gqkgvY8c/aU8cR3Gi6R4Is18pbeMXEyDruK4Td74LfSvi+T5m4ruvHviWfxT4mu9auOs8hKr/dUnhfwFcaYhnBFepShyxscVSXNJson0phIB5qaddku3pxXZ/Djw6nibxnZadPjyVfzpc/3I/mP54xVt2RCPbfhl8GrQ2C+I/GMW95f9TasOijjc45GT2H417at54d0z/Qbd7WLbwIwyKR+FfOXxT+MN5f3baB4TkMNrDhZJhwzt6L/dUfmTXiFta6jqL/aGlkLE5zuOfzzXL7Kc1eTNuZLY+z/GOjad4h054zGizAExuAM57DPoa+PNVspLC4ZGGOcY9CK9M8L+LNa0xk0jVWM8TcRufvKe2T3Hb1rG8bWTyXhkVQPN+cAevet8PeKcZGNX+ZHmjHI5qEir62lw4YqhOwZb2A61WMTdR0raxKZXwaaeKl2k9KYRzU2HcarlSSppqB87vxp+3tTTx0oC5aWQPaOrYPzDqeR9BW14a8K6/wCLro22hQGVoxl3JCqo92P8utc+kDEjkCv0Q+GvgzQfDng+2kspSfOiWWV/L+ZnZQW5JHAPAqJ1YQ+Jlxg5bHzTY/s/+JZXDahdW0PPONz/ANMV6XpP7O2gGAvq17I46uUQIuPrur38f2cVOBI3HUkL/Q1x2vXE/wDZl1/ZwVH8t1YOzEbeM9Mc5xj8aiOLg9glRmtWfJ/jrR/A9jrn9neEYt9tbLtaZ23edJ/ERx90dB61f+FsMNrqt20ChT5BHH1FcTZWWqa3ZTT2iqIrSPzJ5DwFHOPck49OtdP8LpCNTvSxJHk45+orVu6IWhmfFWcy6pbxn+GMn8zXl4rvPiJL5muKPSMfzNcGOlO1gZu6NbAuZ36dBXQyy5GOw6Vn2qGG1VfUVE8ruwiTkk4A9TTBFrzsHmnC4zwRgVZVNH0pBJq4kuJO8cbBEHsWIYk/QD8a1rOTwjrTi1t0n0+VzhHkYSwknoGwqsuT35+lIbMVZAW2N1qOdA6lD3p+r2F1pd61rdrskjOCOo4Pr3zUPmeYobvVoh7HuHwF+Ko8Jaj/AMIXrjEWF5LiOQ9IZW4BPorHGcdM5r7rZTX5OJCf7WtXX+KaP/0IV+pd5qa6RbSTXSM6xLn5cZx+NdNJs5qy1Rrqp3AVLLzIcV5rL8TNNjCvb2sknfG4D+lZc/xQvXYm2sEGf78hP8lpuqiOR9j12MDeN3rXzh8Kr2e4+M/iZ5HO5owOvZSoH866KT4heJZDmKK3i9OGb+op3w0tgniq6vnRfNuY2aRwMEnK/pS9pd6DUWkfQcbyiDzA54J9amg1C8RsbyaqrKqRNC3XPAqNSQcitlJmMoo6dNUnjGCA1WE1mMf6yPn2rAZjgE96r3NzBZ20l5csFjiUu7HsByTV87J5UdPLeaNcgrcRKxP95QawZ9J0SU74A0J/6ZHZ/KvjbWP2hPFuu3s0PgWyRLePO2SXliB3PYZ9K8+T9pb4kWku2dIJcf7B/wAazdVdS1Rdro+/Dpl1Ad1peMw9JRu/XNV2fW4c7oopvdHwfyYAfrXxlZftYa3AANU0uKT3VmQ/1rtNN/av8KTYXUtOuYSepR1cD8CFqfawYexl2PpKTWWt4z9ohnhbGclSwz9U3AfjTtMjKWEYfgnc3/fTE/1rzHRfjN4H8asdH0W4k+1TLhIpEwTkjPIJHAr1mJQqqhONqjP4CrjJEctjw34w/Fe3+HNkNN0hRJqdypKKfuxKeN5H8hXwfq3jHxlrdw1zqWpXMjk95Gx+WavfFPxPdeLvHmo6wrERec0UQPaOM7F/MDNedM869WrkqVLyOynTSV2dEdR1k9b24z/vt/jTf7T10f8AL/cf99t/jXPrLMe5pGln9TUcyNeU6Maxrq8i/uM/77/40/8At3xF21G4/wC/j/41yvmzFguTya2ZLNkh8wOc0ucOU1B4i8ToPl1K55/6aP8A408eJvFg+5qdyP8Ato/+Nc0Vlx941C5mXo1HOOx2C+LfGUYwuq3WP+ur/wCNSDx145j+7q92P+2r/wCNcR5044zR5s5HBo5w5T0FPiT8Qoh8msXf/f1/8auQ/Fj4lW7b01e4YjnDSOR/OvLPNm3YY1IZZQOtHN2J5F2Psz4V/H261a+j8PeNmCyuwWG6HdiQNr/X1zX1DrFlZ3tk9rqUKXELYLRyAFTtIPIPHavyPiuZo5lnViGQgg+hFfql4H1seKvBdhqz8tPbgP8A7wG1v1FdFKd1ZmFWCWqOgjvNPs4/stgqIg4EcC8fkoxUMlvfXwyFEKHqXIzj2AzXnGt/GD4e+Fibe5ud00ZKtHEhLAjqMnA/WvL9Y/an0eM+ToWnTTHs0zhAfwUN/Or5ktzFQk9j1rx98ONB8RaJLGW8u7jQtHPj5twGcEjnB6Yr4MNrcDO4Nxx1NfU/w++NVx431/8A4RvWLJLWWcMYWjYkHAJKkH6V823+ppZ3k9ukZJSVlIPsa83MErKUT2struCcJvQx1s5S5DL+dTmylA4RT9BUzausnzeWQfr/APWqL+0ZW5jX8K8q8j1niKdtz//XtzS+JvEesSaurmUIdyNKpIf25xx9KZYX3iLWbuayTH2wSALGgG1F6lsenHrXg2s/HTxnFbnT7C/SMAFTthQEceu0GvPrv4n+OVkGpWt/LA7RGItGApIJyeleHTwtXqdMpJaH2zD4p8QajrUvh7V7sXEVhGsYwAAH7jjrjpWTe3G6d3968b/Z/wBV1DVYtVuL+Z5cPHy5JyxBJPPfmvWtVZUuXC+tek6LhhkvMxpSTqsvW0uVIFOlkNY9tNgnJq1LOiFY3OGYEqD1IHXFcp2FlpCExVG5kzGD6GkZyRVdnBi5oBnX+H51SydjIqEkgbiOvHOKivZkbUYZkxtQMRjpwSRXK2dxDGSrKGPvVybUZFj8tFA7Z9sYrZVPd5TNQd7m7pQ1AoJ7KMsx4DEZHv8A5NVWsz/aRt74iIld/HA61jW1/dxw+QkjKvoDgVRlld5CzEk+tTdW0Q+VnWXj6VBGTExaUdMtmucS5LOWJ5JzWc09CyDrUylccdDutJtLe6tvOnj3glgXycLtAwPxz+ldHpmnxrrVgjwRmCSAuDtB3MQd2fXBrnvCVziynt7maOOO4YJFvYDDgbmJHUDGOavaZr2m6Rd2ovbpZETzDuTLBA2QFOB68/jXRDlSTZjO7Z6pZoqXDwoMBGIA9B2rwvxPdE6zcnP8ZFen6v4ttdIA1JIZJopgADtKDJGQcsBngdq8bt72DVPEQlnUBZWZgrn5c7TgE1pXkpWiKkmrs2otYisIEbyWLugYFjwSPlBxjpxRJrE92mEtlJJB4BOGBBzgfTp6VqmEWWn5eFR50bq4I+7gk8cdPmxn2rUeWSa2Y2+2RkGGKeoXAXHqOlHJPuS5xWyOWuo9Xv0JlhwIRvOFxgHA/L0rktTYRiDHVpAK9Lu31AGS5DMIgo3noCuxx+PzFa8WuLh3lhLMSA2Rk9KxrQs9zWnO62NnzipxmmtOTVPzARkVEZRmuc3L4lPrRMi3eh6lC7tH5kJjJQ4ba/ysM+4OKz3l2rxVq1fdpF8x7Kv/AKFWlKN5q5FR2iz4Qv4I49REY6eYevsaZKg80kdM1avmzqaO3d2NMmniDK+OSTmvZaPPTuYl4P8ASSB7fyrsNEm/sTRtT1eIlZHiW2iIJGDKfmI/AGuPIeWUykdTXSayyxeHbSNOBNI0h/4DkDP51jJalI5awtjd3AhGeeTivSbeeOwP2O2RSUX5mPc+n4Vx2hqUD3Q7cCtuzja8n2NIsSZwztkgfgoJP5UPUq5u3fl3VqZouHXnHofUVp6zKbzR7S9YfMCVP1x/9as290q60nyzI6zW865jnjJKuPxAII7ggGpvMMnh4pn/AFcn86cVqrik7rQ5qMJDqMyjOJbck4PcAiuTlkGQFXG0YJHf3r0CDQ7/AGjV7nENsV8sMxA3ZznAzkgZ54rkdZsrSwlWG3kLsfv5GAGFU7XIWxj7s03ilzQTUgh8LRJKHmXcg6jpn8aiYqxOPWjJzRQMchVWGMHkda/UnR40uPC2mFyEVrO3Ykdv3Skmvy2UtF/CD71+oPhi4W58HabG/wDHpsK/nCBXDjk2kdWGau7jbu3kTTzdSqIxIAUX+IL1ye9cNct/o1yh5zE38q7zxFqYuJiWjaONPlQnHzKARkAcivPmcSrMF/iQj9DWVGGl2XVlfY+UtMuJI/h1c2sR2ie9Alx/EFEZUH2BzVr4bfJqd4D3h/qKqaYp/wCEIvkP/LO8U/nsH9Km+HbEatdY4/ck/qK9NfCcctzmPHh3a6R6L/U1yFuoeZV966rxsc62x/2f6mubsRm4HtVCOgkfbHWhoWn3N9cAWkbSTOdkSqMn/aIH5DPpmsiYjbXsOiTTeGdEg1nR7SZ32sktwqEhc43DPYYIpJXE9jq/Dfwk8PTsreJb1HvThhaKRtT2Yg8n15Fbfiv4YWWqWA0+L/QgpyDEo2sPQ+1eNaX4xsR4la8ad/KRS6l+Az9do5PGema9/wDhv4wm8TTSaZe5dD/qmI7jsK6aXJsYT53qeQ6x4Xvm0GTTtRkae709A0MrD5nhBCsh9dvBHfrXkkDbCyN+FfV/xag1PRLvSNXsYna0S4KXmwZwkg2fNjPy4Jr5n8SWaWHiC5gi4Qv5iemyQB1/Q1FWPK7IqjJtalCHm6gbussZ/JhX6j+J4kGkSE9ZFCj8a/LWORUdZD/CwP5HNfqvdwLqumQyZ4MYb8xWtLZkVuh87S6R5TYAxV6DTkYDNdndWe1imOhqpHbqkgwKylBoSmjBGmjsDXXeCbcQa+FIxujb+Yp5tGKMFODg4PpkYzWF8LtO8VaXPPF4rkEzi4kNvJuDEwsARn6HI5p8rTG2mrnuMvEpx2NSIfm+tVmJWXcKlj+9iuqL0Odmk7ggCvB/2htfk0b4fSWsDbHvX8rg87f4v517izDtXxt+1NfyXt5pXhy3Pz+W8zD/AH22j/0Gpm+go7nDeEIltPD7xxXYVruyEvkKAd6rhmOeoZSMn2BrzbxMsmn6h9vtpFRmbBYgY6dweKzNKvfGGgQtZ228QtuyoYYG4FTg9sgmsDUbHWb/AOabHXJ3MCa5rSO650MXiy7AC3UdldDp88QB/wDHSK5vWFtNQvGubNEhD4JRTwDjnHPTNUrHS57W9imuQpRGBYA5JFXtS05b6/LWRGzBxuG0nv0qeVroNy8z3H9mjRftHj/7S4DC1hd89cZIA/nX2b8TvEv/AAivgfUdZVgrrHsjP+23TH5V8/fsqaQ0NrqeruOCI4VPrjLH+lXP2qtf8rRtM8NRNh55HuJFz/AmFXP4k10x0gc09ZWPiJMkguSfU1Yltw0gK4wRmohGx6sBT47Z5XEfm8sccsRXJZ3udKaAW2054pGt1xnirU+lTWrFJWH1DEiqUlk20yeZwB6mhopMouNswHvXSSnNufpXOfZ1zvLdPrWmk00sRhjBc/7IJ/kKVgcktWV800IHzUxtbv8A55Sf98n/AApjWV22AYpMf7rUcpmq0P5kRi2LfdqRrYhcAcj0oGn3QbHkyc9MqavtE8WlzW72siMzAiTaeAKQe2h/MjAnQrzikIyoNRC13cB+tW0g2LtzmhGjKIGCa++v2ZNbN74Ll0pjuazmbA7gNhv5mvhI28ZPLGvpP9mfWRp3i6fRi3y3URI9yoJ/pWtN2lczqq8Tzz4xadFpnjrVNLVdi/aWmDYHKuScV5jbGK3uEmDA7SDg19G/tG2Edp49jvJV3R3duNwHcpj/ABr5uktI95aLIGeAaJytJhT1iez+FLyPT/iXo09pIrxfa4NrjB4l27hkehYiqPilorfxNf2/l4KXEgPHv9K4fwszweJNMkZj+7vICPp5i13nxAdU8a6pGAcC6f8A9CNcGMXNA2puUZaHPpKW5Me707cVMbhgcR4HcisoTE5RAMetO+ZRgc/hXlSpnV7V9z//0PhiJoZAzSxFi38Wa3/Fk2nW9pp1lYou8Qb5WHOWJxg/lXP3Or7oBaxoqBeCQOax53eSUck8YFZ2e7LcuiPqz4FSpZ+F769WPcXuAu1eCcKOtdt4x8T6V4atLjVdUjlmjDqiiHG4Ekdd1ch8H449L+H8l+FMhM0sm1eScADH6VnfGO4D+EnTAy1yo49jXVOmpU4xZzwnacmjkpP2g9Ks5G/s3RncOfmNxOO3TCqnr71oeE/jPrvjbxhb6ZPY2lvAY3XMYcuF9mLY/Svmy80q4i2mRdgcZXPBIr2P4V+EtQ0bxXDeaiNu+1aZB/snOM/lXNOlBJ2R0RqSb3PqN5F24FUxKChBpkjFSPes7zwpIrh5WtzrvcsiVVfPSp5LgEZWotLsJNaumtoGCFULnIz0IqK5tZLSMGR13E42H7wqvZu1w51exJDcYb5jWiLm2itCpXfJKTz/AHQP8c1gXNtfWiia4jKIehPvU9obSW2a4nZ9yk4wOPzqJUmxudkWZVZbeNn43EkfSq7ylVIqpPqBnZWbgKAAB7VA9wpWhRfUS8yQy5bNO83gis43AFOWdWyDVKINqx7z8RJTH4U009j5f/oBrxrTtWOnX8d75ay7M/K3TkYrX8QeN73X9Ng0q5ijRLfbtKZydoK85J9a4tnGc1pJ63REdrHeTeLNZ1GGWwiRSJhjAzkDvg5qNrvxRbI1+gMarl2IwMEnce/rXNaNqcOnagt1dAsgBBA7+3tW9qfi+zu7KW0hicGZMckYBPPp61ad1dsiSs7JGHLrGpTxmKaZmQjGM8Yzn+dZrvl4l65aqXm+tJJcESQbfUn8sVnuapKx0BcLxiq7SjPWqsk5J3Cq5k71HKPmLssx28Vq2DNLpF+kfUqv/oVcw0tbelXKR6TftIMgIKcbqSsVTjGbtLY+LbpQdSiA5yzGqNzCBOec81fmIN/Cf941Wm+eXcK9ZnD7utihH8qMw5xz+Vdb8QdNj0O+ttDjcyC3gUsx7s6qx/DNcpGUwQ+CCea0PEt1cX17HPeOXcwx7mPU/IKyafMn0LjOCpyi1roNtGEenjHc12lhpZEEat0I3NXN6dbCeW2tgPvN0/OvcJ9G+z2FxcAY8pAv/juatK+pzyep55Y3731tqGiv/q0Q3MXs8WCR+KbqzbKXfpdxEBkEqRU3h2SO21SCScZFy7wt/uyKyH+dULElIrmLOdv9DTYLZmnrrCDRbSykcGZCzGNckgOAQSenI+tee6lK0suX6jA/TFbmr6st7fI0MZyqIp9yBiufvo2jkDv/ABknHpz3qYrWzKZTwKKKKLEARTcGnUHoTQUR7mA2g1+k/ha42eDNFuB0+wQZ/BAK/NuMAvzX6C+FLkv4D0XB4+wxfoK5sSrpG9F7nTeJNV0+5tlS03mXGDuAAA9uTn9K46xYl3Rv7p/kakuiWJzUGmcXDfQ1EIWQTlqfK+m3ESeGtZs3OHE8bgeu18H+VL8PJT/bFyD3gP8AMVh6laXtkLjU4sNA9zNEyg8/K5HI/Hiuj8PWH9ialaTiQuNQtS4GMbeFJHv1xXQ5pWi+pKpSknNbI5Pxrn+2Sf8AZ/qa57T/APXZrofGv/IYP+7/AFrn7D/W1s+hkdJp1rb3upQWt3J5UTsAz+g/+v0r0rxF42e18GTeEtOjIiJQLIQQxGcnPY5wOleVxo0s0cSAszMoAH1Fe7fFCPSZfA9iLIRi4gdFnCgBgCGxuxz1ojcmTsfO9tD0UV9G+BtctfBum28F6RL5jrIm04KBjnHv19q8LtIlRg7Yr034c6VZ+IPEDWOpL5sawsygk8FemPpT2eobn2zqa29/pro2CJU7+4r4f+K1qtp4kR0/5aW6jj1RmT+QFfS3iPxDNpuhXLWpzNBAxQe6jivkHWtTvdZ0jTtR1Fy88gn3sf8ArqSB+GcVpOfMrGdONnc5iQkrsHcV+pHgDVV13wZp1+hzvto8/UAZr8t2r7z/AGbtabUfAxsmOWspmjwf7p6foKqi9Qrr3T0vUYPLuGX3rIMWGB966DXLqzt5t80ka5HcgVxlz4k0KLI+0ISP7pzW7aOVanN/FTVfEOjaJFceGSVlaYK+1Sx2kHoB74rpfBF9qV3Z2M+qcyuh38Ec8+tVJvHWiIBhGkwP7tV7Lx5aXmqQWdtBs8x9u89RwT6e1Zu19zRXStY9tJLkEduDTlb58jpVZ7aaPP75zg44Cj+lVRbD+KWX/voj+WK1RkzbLhvlHWvgf406suq/F6dAw2WMMUOM9wu8/q1fcQghBz8x/wCBv/8AFVzlx4C8C3t3JqV7pFtNcSnMkr7izEDGSd3pSaCLtqfAFzeREY3CsOeZSMg1+jo8BfD9cf8AEksjj1Qn+Zp48F+A14Gi2I/7YrSsXzo/M1ssc4NLbnEuWDYwegPpX6bL4U8GJwmkWA/7YR/4Up0PwpbhpF0uxUKM5+zxf/E0OBXtEcJ8DNKTRPANusxCyXTCZgeCMqMA18ofH3Wp/EXxJuDbRSPDZRR26YViDxvYjj1bFfeGmCKG0G6OMbjvACLgZxwOKk+z6YzmRrS1JPUmCIk/jtpyjdWIjP3rs/KkWN+3At5j/wBs2/wqVNJ1dmylrOf+2bf4V+qoSwUfLa2w+kMY/wDZaeJYEHyQwrj0iT/Cs1SXc19t5H5hXdhqRtFea2mQgYOY2/wrD/s++kjPlwuc+vFfqhdG3uYzHcRROp7NGhH/AKDXHyeFPDjHJsoOfRF/wpSovoNV12PzYOkakBzC/wCVdf4Ds7ibUpbBVCvKqhS3ABBPevvSTw14ejiZvscHAP8AAv8AhXzP4htrPSddF7bRLEoYfcAHGfas3Brc5cdNToTikb8nw9uFM9rcrb3n2dgZGimICFOWDZj71fbwZAmqppb2VuDKjy+abg+WoQ8qxEWcg/KRirlx418JQXeqT28kkw1VQr7IxEIxgjhUwCRnOT1PWoLnx74XurqGKMTR28scv2o7QXWSUl8ocZwG7U9D5xQio2Ktr4KN/cQzvYQxBJ5IQzzHGVUFukZOOR2rH8UeFZ7Cwlup/IiWYskcCF2Yj7u4EoBg9eoPtXTP8UNJuEhtVjktlguvMWaLDMYyhVtyuGQkkLnK/wAqTVPFMHiTT7i0tI7mdppk8hXjTZGFABYFUDAseSM4HYU+VMuVNNKx8nL4S19lGLd/++T/AIV1tr8G/iLfwLc2OnmRG77lX9CRX3R5NgFCkICPYVppqkcCeWJQoHbdTVLzPp413yrQ+Cz8D/il/wBAw/8AfxP8a7v4Y/C34j+GPHFhrWoWHlW8LnzX8xCQpUg8A89a+tm1y37zg/8AAv8A69QNr1oOsyn8apUkncJVm1Y8U+OvgPxN40utOufDlt5rRCVJNzKuAduOp5+6a8GPwM+JuM/YUH/bVf8AGvtK51+xV428wcN+m00jeJNO2nEh/AUShGTvcUa0oqyR8c6f8FfiJZalbXdxaxqkU0cjfvAThWBP6VgeL7yO/wDFN/dpkCS4dhkc9T1619l6n4qsYIGmZjhVJ59hXxTeSWb3L3bKx3uWOT61x4qldWiaQnKTuzI2oh571IxCjAGM1qGTTWXzPJz/AMCNKLuzwGSFVz65PT6157wr3Zsot6n/0fieTwX4mEm1rGcH0KmuvvPg94402xjvryxZRKuVU43Ae4zkV9ceE/EXg6XX/t3iqZY7aEGTZGVYsw+6o56ZrR8d/GbwTr4h0/TdsCCTdNI3LbR0UBc+9eXPFVLpRidFOMWnc8x+HOmXWieCIbC8Xy5VaR3U9ssT/KuA+Kbebo9jF18253kdcgZJ4r1O78UaF4lvJJPDEitDGixFBlXAVQpO1gM7sZ4ryH4iO8zafZjrtcj2yCB/OvYhVc4xRyuny3Z5v4wT7bfabJhTkHhMEYXntxXsvg2VbmdbszCcCAqHzkgFmBX2xjFeLR2rw3MFq4yUjcj/AIEVFer+A7KTTra6gkGPmX9c1jOPu+hdOV5Hqd9crjIH3VGa5qQsOSa6DQLZtcu1EBDI27JJwMKCT/L0qW3u9Mnvvsc+iFULD98blCv5Bc4/CpcPaLmN+dRdrCeE7uO0vpLiWURDyWUFu5JHFVbq9tJbSP7VMzzRsDjHHXnLd67C00PRrjVJ7TT7AT/KrqfOAXGPmx8uRg06S38ORWH2mPTo3djsaMyjIB/i6DpmrVJ8trmTqJu9jnr3V9JvoXt3+YF9wOD2Bx+pFczFdJFbG2ldwjEkhRXoWnDQJ8BdOhXZ8oDy5JPuAOtaup2Oj6dARPpluZo8MsYl5IbvkgdMUnSbV7j9rboeLzyJvLR5C9s9aga4UBUz15r2NdW0kMsKaPb7e7GUf4Vdsl07U9QjsoNIsiW53bycDqelT7FN2uV7Z9UeG+YoGSaDMoOOc+1euz681pfTWEej2Jigb5GZj8xPXjt0rc0nxPPdv5z22n27McMSC2Mdjz26dKTpRTtcPavseEF267W9zg4pitK5wqsfoCa+mrfxM/miNbixVSQNqRnJJ6Dn3rJ1PxN4q01J4dQnskmXDRRohwynPUnvxR7CLV0w9q72sfO7R30km2OGUn0CMf6Vej0LxDcMFhsbliRkYift+Fey2fjvWHtmuNRvIYZQBhUXP64pNR8eaoI7b7HqaBj/AK4lG4HtxVRpQtqyXUl2PIx4S8XuCU0y7OBk4ifp+VVLnQNf0+Jb7UbKe3iDbQ8qMgyecfMBXqR+IOsRyAT6qoTHUK39BUXxGu72TRtOae7e4S7YyICMKAAOeef4vSh042vEFVlzWZ5N5xPB6Um9arAndtFQ3U62tu93LuEcYBYgdMnA/WuV2W50Jcz0J2cbq6VYoofBN1fD78rshPsorj1lSRRIh4YZFdS91C3gC4gGd6SSE5HHI4reglzoznJ20Pjgo7X6bASFByaruQZOavwXBhuliwCrK2SfpVJhGHLE8A16DWpxRZhIP3ox61u+I/8AkKkeiRj/AMdFYaMPNGD3rZ1+RH1Rypzwg/ICsralnY+EIVuNfsoGHUn+Rr6p8T6F5Wg38gXGMn/x2vlTwhci38QWVww4V+fxBr751+CPUdDvYV4LW+4fildFCnzJnPWlytHxt4csrYadbXV3t2idSpbH3g3GM981w8LDz7sdiDj867tbFbrQoJQ2wWMzOyno2wtj8a83glAmmz3X+tYzVmbwd4mE8a/b4/w/nWdMmJSB61o3Eix3KSnouOlUZGWRy46E96Wl7hqQ4NGKfxTCy+tJgGKjkOENSbl9aikZCuBQA6EdW7AV92eB7qO58C6S8bA7LVVI9CO1fCADCE45NfZnw11vSZ/AVlAJ4oZbZDFKkjbTkE4PvkYrGsrpGtN2Z1txJyabpsqRyNPJwqgkkDP8qx59T0dSTJfQAf7/AP8AWqW38T+FdIt5Ly61CFgq52puZj7Dis0mUz5o1DypbPVoQ3zJeyOo74Z8/wAqteHdTl1rU7KzmRUWxt3RCv8AFwBz+VclquqQ3up3eo2xKC4mkk2+zMSP0NangieKPXgXcKDGw54rXki2pPdCjUcU4p6MreOVK6uB/s/1rl7JgJsetdT48kR9YXy2BwnOPrXIWzYnU+9amKOosryfTbuO/tTiSE7l+tev2vhW/wBd8K3mtQTefIyhTF3BVg3H4Zrxfk5FeoeHrrWb3QVtdLVB5EgWUs+3JPKH9CKqApHnTTGW1wykPGdu08EEdQa9Y8PQ+JtV0aGbQLXZDbbUZyQu5h1Yc885puo6LoDauktwH+0lR5sS4KPIAOhzkf1ra03xde6JplxpbQNbxbCIlbGAzemPqTWs/d1TM0W9Q19pJHDPn15ryvxY0W61hiAUCNnwOBlnY1m6tqV2qpHa/wCsmcJn0zVfV5mluVSQ5MUaoT7gc/rmsLmiVjHfg19Dfs7X0t2+v+FoS2+5thNHg7fmRgvXjH3q+dmcE10vwz8Vjwh47tdYmYrAzNBPj/nnJxn8Dg/hVQlZ6hNXR9bR/DTxHLhruS3gH+0+4/8Aju6tu2+GCKu681EfSNc/zApmqfF74c2DbZdTVsc/Ikjf+y1zE/7QXw2tziOe4lx/chP/ALMRWy5Dn5p9D0RPh94ZjGZpbiX2yV/kauxeG/C2lst5ZWn72M5VnYsR27k14fc/tLeD41/0azvJT7hF/wDZjXNaj+01byQtHYaQ5z3klA/kDTc6aDlqM+xJteuGzuI5qj/bk2cbq+KJP2jdam4XT4hx/fJ/pVST9oLXXPFpGPxNHtkHsX1PuE63Lj75qo2uS4P7w18OyfH7xIThLeMfif8ACqT/AB08TkE+VH+Z/wAKXtkL2LPuttZuQM+YarNrl0R/rWH418Jn42eKmHRBn3P+FU3+MHip/wC4PxNHt0HsGfdx1y6LbVlYn2NMmutWucwjzSp+915Hp+NfIXhz9onxF4dyy6da3Dn+KUt/QV1E37W/j6SczRWGnx5GMbWI+vUU/bRE6Mj6Y87WQOPN/I00za76TH8Gr5ef9rD4kN9yCwX/ALZsf/Zqqv8AtU/FFuR9jX2ETf8AxdP2sR+yl2Pqdn189Fm/JqYW8Q4+7P8Ak1fJ0n7UfxWf7s1sv0iP/wAXUEv7TnxYkQKt3EpHUiM8/wDj1HtYh7GR9ZlfEjNgRzn8Gp32bxQ4ysU/5NXx0/7Rnxbl66iB/up/9eqT/Hz4rTE7tXkX6CpdVdB+wkfYt1Z+KWjKGKcZHoa4e58E6zeMfNtpW+oJr5cuPjR8T7jIk1ec59CB/SseT4meP5uZdVuSf94f4VDqJ7jjSadz6yHw11NhkWbf9805fhnqXX7KQffAr49l8c+M52LS6ncEn/aqk3ijxI/37+c/8DNTeJaps+1I/hnqEj7TCq/UqP612Nn4J1S0iESPDGoHQyov9a/PM6zrc7hDcynccfeNegW9q3kIJ5HZgBklj1/OmppA6TZ9q/8ACLXOf3l7Zj6zx/8AxVRf8I3ax/67VLBee9xH/jXxwIefvN+ZpfKUdST+NHtRex8z7G/sXQIv9frmnqf+u6f4037J4PTiTxBYD/tstfHm1R2/Wk2riq9t5B7DzPqrXrjwTZWMl1BrtpM8SlljjfczH0AFeLSePoWPyRP7HpXABYu45pwVBWcqjvdFRpJbm7rHim41S1NqisitwxHpXJi3jCgMuQDnnmtEKG6ilISs277miSWxm+TGCSqDn2pwQryBV/g9KbtGeuaVh3P/0uPH7PPgyNCbrX5HPHQL1H4mnxfBT4Y2S4utakJyRlVXJB7E5Nbkqaiw2EoR3Gzj8sVRZLiFGIg3v/DhQB7+lcawjtrNs2VePSIyw+HXwi0W4F1bajemVejRsqdPwNc743i8Mah4t0VdJaV90m2VpGU5XPIwFUAn1rfeS6CDNiWbjPb+tc9rttapLba5NA8L2bgnn5ducnPJq6UFCSldk1Jc0bJHFaxaaavxYj0uEAQogyPxpvxQ8eX3gPxQ9j4bjt2SWNHcTJvw3PTkY4NcLouvW2ofE6S+vX2RsrHPJxgjA7muK+JepDUvFNxcBty5O0+3QV6Epxace5zqEk0zr7L9oTxvpvy2lvp6DaygCAjG4YJHz9eazU+NvidQA0Fq3rlWGf8Ax6vHqYTgZrJwVrGnO1qj6W8K/E3x3rq3J0ewiPlqFZ4naNl3c8H5uuOld9o2q+L7uzePV9OhgdmABy5YAY569/pXHfBow6T4YeW4gYveTF9w3cqoCjofUGvUJdasV/ePEVXPH3/8aylybMuM59CnbNq9tNCVtYwq3HnSSlzufPONvYDtVjWfEvinX9WeSTTraHZgB2mJLIBxxxSJqumLb+ZOoDYJxk49u9Y9xqtvOitEYt47l9pGfTkUlKKViuad7s8zvPjSI9UmiXS1QQyFGUSkg7DtJGR3xW94b/aH0vQtbfVX0uQxsDsjWXBXIOOdhrE+I9ppUvh8XFglqJY33SNFtDtk85A6/lXztIwaXIHerpqKldClJ2sz6kuP2g9HfU21GPTZNjjPllwQGz1zs5rOl+OWhBoWtbGZdjSPOC64kaRix/5Z8AZ4xXzYe9RYNXyon2kkfWOlfH3wZpxjkn0dpJElDFmcn5N27gbeoHArtLT42eGvHfiG9SHTZCrWYWJ5Wz5bB/vY2jscV8NYrb0XWLnRjJLaKCzgAnnp+BpOCs13FzvTyPra3leDbvCyIHySxwSM1c1u/tbq+a9sVSKMgARFgAOMZ6CvldvGWpuckD8c/wCNVX8U6qzbgyj8M/zqHRjaxp7eV2z67sPEWgWmivY6jBHLM0m4Sg8hePlFaHjf4j6Rrun6fZaREI/siFW3tkYIUccD+7Xxn/wk+rk4LJj/AHR/hTTr19LkSbG+oFVFKN7EObaSPprSvHOn6RNK1xFFOXXC7j0JxyOtZ/jHx7pniS0FuIUhGzDLCdvmFSGXOMdxXzp/bNwv3EiH/ARQNev1OVKD8BWcqUXq0XGvOKaT3PdoPjZ4Zg0W30q60RhNA2JJBJ94AnA+56Y71PP478/SrjS7a2VY7os6nJJUMuAPfFfPD6g8r+ZIke71Kjr+VWG13UCOWU/gKpRUXzIUqsnHk6GvcWj2cbXMpAXeIxkcnqf6Vj3DxmIsh3ZNQXGrXt0uyUjAOcYxzVX7VJjHFb+00MOXU7GHSdLezjmit9zsvJDkc9/WmW+ixmVpLuANk9S5AH+Jrl49Tu7cHySBkenFP/tnUTyXz+AqOYo6Ble0nWSEbSjcYr7m0DXY9U0uxv2YGO5gEcnoGxg18I6bObyFjNyc5Ne1eCPHFx4b0ySzmhS7s5MkI5wY2PcEMp6810YauoP3jGtSc1oVPGtpceF5b7TGGEmYlM/XBx7EZrwa8kJiPYk9q77xl4jv/EN59rvpfMYDaBk4UDoq+wrzu/OAkQ6jJP41FSSlK6LhG0bMyjy2cmmlc1Ljjmo24BqCiNRk4JxUmBTUXAyafQAmBUWcHiphV37Q2MbU4/2R/hSbHYbbyQxHLpvBHAz3qWMTTHy4VJJPQf8A1qh+0Sei/wDfI/wqeC+ngB8vAz6AUuYLBJpeoO5YREZ7c0DRdSONqYp/9p3mc76Uanejo9HMO49dE1PJTCjJ7mqVzZy2VyscjZJI6H1qyNQuz/H/ACqCeaWd0aQ52nNHMIjmJaQliTj15qIHYwb05qSRkJ3ZFQkg9DVCOkfJCuvcV0/hnWl0ueRJxvhuVKOucYYcoQfY1ydiy3FrtB+Ze9TwruUqRVJ2Ez0Kea58PtBqF5Cs7uN8cxLZ4P3Tg4OKxNc8S3mp/wCn38m8E8KvQe1bnh3xOljaHS9ft/tli3bGWXtwcj8O9S6jbfDjDTaF9tkZufJkACj2J44+holawrM5Oyv4ponvVQ4j4Xd3c9PyGTWRNIWYu5yWOTWle3DSKFwFCjAVeFUeg/xrFmbJqUUQscAkVkvycnvV+ZtqVnMcnFMViHYo4FWbW3NzOsAONx64zioqfHNJC3mRHaw70hnSx+F435M/6f8A16l/4Ra0B+ec4/CudF/ed5Gpxv7vGPMakxnTx+F9NXkzsfxH+FS/8I3oueZH/wC+h/hXKLf3Y/5aNSNqN455c4HSlcLHVjw5orqHWVgM+oq2mjeG0wr4Y+5P+NcOtzc5zvNSG7uv+ehoEd0tj4ajOREGPpz/AI1L5eiqeLVa4D7be/8APQ/nThe3v/PRvzouOwzUbSZr+VoIiELfKAO2Kq/Yr09Im/I1f/tC9HSVs/Wk+33v/PVvzoTCxUGnX56wvj6Go7i1ubXb9oUoG6Zq+t/eZ/1rce9MmnmuU2TOzAdMnpQmFjIopzKVODTaYhc0ZpKKYBRRRQAUUU4DNAGzodi11debjKx8n69q7vEtedxMY02xkj6VI08rdWP51LY7Ho0KIJB52SCP4WAP8jTAuT99QPdq85bcRuyc0wAng0rhY9M8tP4pU/76oaKEjBlX8GrzcRj+KplAHSi4WPSltRgHzUH41KtmWP8ArU/OvOUdhwKnSR1bgmi4rHpMenM3HmqfxqUafFjJlQAdT/k1wCTtnnNWNpbGetO4rHoA0iEMq+cpLDI+nrVkaRaJgGcZx6f/AF64BJHErNkkAAdelWobhicgmncLH//TcNQT+7VSTU2H3QPzrL/s+RQd0znPuP6CmiwjA5JP1Jru5TlbLr6pOw+Tb+dYWum+1nSp9LYqizoV3AHg9QfzrTFsicA0phQetHKtmCbR87Wnwd1az1H+0o9Qj3DOBsYdRjrms28+C+t3dy873sA3HOMNX03sHYVCwbsoqXSiV7RnzH/wo3URwb5D9FNMb4H6hjH2oH6L1/Wvp8sR/DUZc+lNwQudnzyvw88Y21ulnBfyrHGMKqsQAPpmsmX4deLmOXuZm+rV9Nbz6U0uT1peyQ/as+VJPhv4nA+dnf6tWe3w38QDOUY/jX10eRg0zYh5IFS6MQ9sz4+b4eeIDnMDE1BJ4D11BzA35V9hOibuMenSmiGI8FQaPYor2jPjk+CtaUZaBvyqm/hPVUPMLflX2a9tC3VB+VV2sLQ9Y1/Kj2PZh7Q+NG8N6ivWJvyqBtCvl/5Zt+VfZbaVYN1jX8hVWXQ9OIz5Kn8KPZeYe1XY+OW0m7H8DD8KiOm3QPKH8q+vj4c0tyd8Cio38K6Mw5hWl7Jh7Rdj5BNjOOxphtpQeQa+tn8GaI/WECqr+BtCLf6ul7Fj9qj5RMEg6g0hjYda+ppPAGhNklSPpVZ/h3oZHQij2TH7RHzCY3puxxX0w3w50Y8DNVj8NdKPTNJ0mHtEfOGG6U0hx619GN8M9L65NQt8M9K6kvR7Fh7RHzyVfHSm4f0r6H/4VrpQ6Fqafhtp5+6TR7Fi9oeG6TObafDcBu9dXc3cYtxFESA3Jr0F/hxCozFjPvXPXXw/15ZCtrskTtkkH+RpOlItSRwkzh/mb7qjJ/CufuJvOkL5r0O6+H/i9l8tIUC9zuPP6Vn/APCtPFZ6xoP+Bf8A1qOSQOSOF3Co2YE4r0MfDHxLjL+Wv505fhfrfWR1H50+Rk8yPPKTNekj4Y6kPvyj8BU3/CtrpB80lHs2PmR5qkZPzZApSpH8Qr01fh5JjliakPgAL1yaFSYudHlvA6mjIr1L/hBEHUGl/wCEJhA6UeyYc6PLdwFGc9q9QPg2BRnbTD4WhUdKXsmHtEeZhgOMHNBcjsa9Fbw7Ah5Wo20W2A5Wj2diuY85ZS3QfhURifPAr0NtKgHRDUDabED9w03EXMcnpsj29wA4wrcGukXh9wNPaxQf8s6heOSMbiMVLVik7mkkgUYY8elNmuEKbUrHkumTioPtbGkM0JZQBzWaXLtkdKa0jOeahkkEYwOpoEQXD7jgdqrdOTSsSTTc0CF69KUK2c06PA5NSb19KATCJIjuEuQcfLj19/ambMLnNO3AdKNxNIZGM9qMU889KTYxpgCnApQ3rS+U9KIXNJgLu9TRuX1pwtpDTxYzHoKLBch3LSBhVoafOe1SrpdwetPlC5Q3L60oYetaa6RN1qdNGmc7QKOUVzEYqwwarFCOldenhu4bqKsp4XnxzTURXOF2t6UoRz0FehxeEp34C5rRi8EykZAp8rFzI8r8t+mKcIZD0FevJ4EmJHyiraeA2A5Ao5WPmR4uLeXuKsLayYBwa9sXwKDjgc+lWo/AsB65OPSjkYuZHiIt5MdDS/Z5e9e6DwLaj+En8TVhPBdivWEEn3NCpNh7RHhK2kzADip002dztUiveE8K6aoH7gZ6d6vJ4dsUXi3UfSj2QvaHgiaHenpzV1PDWot0/lXvEejW6/IsQA4qY6Xb4yBjHHFP2QvaHhcfhfUemV/Wpf8AhE9T/vCvcU063jHCnPvTvskS8lKpUh+1PGI/CepAj5l/Opx4X1Qcbk/X/CvYjZxdQvTrmmG3jHGBntSdNMn2jPJI/C+qgkMyDPfn/CrEfhjVFI+Zfcc16mbXeA3SntBgDpk0/ZIPaH//1MwSHvQZVzjuaTFIxxjHNeikcQ/dSZHNMDetNyTyOtOwXJM00nPQ0EMeW7Um09fWiwDdnrSlBjg0hb+Hp70mGJ7UWBjTGD1prR46DFOJIODRlm4PNFhXI2hG3PrUZii28VPkkYoPQE0WAqeSval8vjFWTtA47CnBVI3EdKTQ7lDyjTDE561okJ1PSjYDiiwXMwxAc4zSGPP3cfhWmsaseOaY8PzDZiiwrmX5ZHOMU3k8MMVrNGMZ61GIwQCKLDuZpBxxUfLf/qrWK87SMU0xkHa3XPFILmVtUnpmmeSo7GtfyyBg9KY0YxmmkFzK+zx55Wj7OnQCtPyWdcgcUw2jLg469KEFzMNvGODxTDbg9BWt5YXg0eUoHFAXMY2zZ4zUEtmHH71c/wCfat1oj93GeeM0wx54NIdzAGnQRNuWMA+tS+QK2/K4phhHQCmhGKYgOMZpDCO4rdEGOD1p32WQjcMYpWC5zvlEsF/lR5BI4BrfNq5bp070osyBQBzhgIYDHH+e1L9lGM7c10H2UbSBQLZlHp2pgc39jUDG2kFkPSuj+zknjr701k5xkUh3ObaxTHIqJtNjxnbwa6oW+RnOaEgnIwABk9zQFzlDo9uxwRn8KoyaZah9gjb67Tj+VdwYnQ4fvQ0JXovB4zRYdziH0K2I4QcVB/Ylsw+5j1Fd2I9xIYcDrTDboeduR2osHMzhD4dgYZ25qBvDcG7GzNegbY+gTJHB6U8Iv3lTH5UguzzOXwnA3TOKzZ/BCyqQjGvWwIyCTwQeOKcEDLlCPypcqY+Zo+f5/hbdTNutptvswqi3wq1nOFlQ4r6R+zkkYx05pVtAzBQKORD9pI+aP+FWa/082Mf5+tVT8KtYPMk6H6V9TmxIGcDH9ajS03dMA0uRB7SR8uD4U6j3lqVPhbdL1ck+1fUIhVAS2D1NPVFPIUChwQe0Z8wf8K0uIxzup6/Dmbbu5xX0+yxD5No+tR7VGQFB9DijkQOoz5rX4bXGOhqZfhrKedpzX0eJkUbnTGe+BTgwLfKuQaXIhe0Z84D4by/3GP4VcHw3mU5aM19AswQ4ZR9RThIh+XHNPkQKcjwhfh1IU3+WRU8fw+ZPlKdea9tDwB8FRk5609ZIUHNHKg9ozx5fh5GeCv6irkXw8t1GcZPpXqZcbyhAwfamllRQuwn8RRyicmecR+BLOMZZM+1WF8HWKkfIBXfGeMrjYR2zxTVySWIxkdP6UcqDmZxv/CK2aYAjB59KlXw1YoeFArrWUAgg4Hcd6ieLOCpGT60WQmznk0K1Q5Kj8ql/se3GAFGfats/uwBI3JqXyDjPXvk07AYf9mRL/Dz61KunQnoAM/yrZ8qQHHH1pm1w2HP1FMDJ/s+MEsp5HFH2CMZ3np61rCCRcfOM56c0NCwbPHHXNIDJNnsbaqs3v2pDax8uoIPStgxSMNnWmNbuF2jp/MZ60CZj/ZIzwcn60G1xjyvxrV+yTMSAOmCOaga3cKTnHNMRQ+zoqknJ9Kd5CZ+XOavGIjLHnHWnOhiB8zd9OP8AGh2HYzHtm6oCff0p/wBgbHfA61O26fMYOQOx4NSqZDtUjnp2paBcpNbHPyE47mpPsjEYJJz0GKnZ5QSFGeORmqfn3QP3RjPY0BdgbJjnPJ+lI9pzk8j3FSTTNgl1LAdenH61Um1yCGM/xegxQkNMd9kJIDY6ZyRUbWzAdBV+1TVr+MPY2pcN/EWQD8i2a2rbwv4wlzvSCNT03Pkj/vkGmDdj/9k=',caminhao:'data:image/jpeg;base64,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'};
const DK = {
  mi: n => 'R$ ' + (n/1e6).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2}) + ' mi',
  blk: (label, html, cls) => `<section class="blk">${label?`<div class="ey ${cls||''}">${label}</div>`:''}${html}</section>`,
  lead: t => `<p class="lead">${t}</p>`,
  stats: a => `<div class="stats4" style="grid-template-columns:repeat(${a.length},1fr)">`+a.map(s=>`<div class="snum ${s[2]||'bn'}"><b class="tnum">${s[0]}</b><span>${s[1]}</span></div>`).join('')+`</div>`,
  hl: (big, txt, navy) => `<div class="hl"><div class="big tnum ${navy?'navy':''}">${big}</div><div class="txt">${txt}</div></div>`,
  boxes: (cols, a) => `<div class="grid${cols}">`+a.map(b=>`<div class="box ${b[0]}"><div class="bt">${b[1]}</div><p>${b[2]}</p></div>`).join('')+`</div>`,
  tree: (cons, central, causas, rodape) => `<div class="tree"><div class="tlab">Consequências</div>
    <div class="trow">${cons.map(t=>`<div class="tbox cons">${t}</div>`).join('')}</div>
    <div class="tarr"><span>↑</span><span>↑</span><span>↑</span></div>
    <div class="central"><div class="cl">Problema central</div><div class="ct">${central}</div></div>
    <div class="tarr"><span>↑</span><span>↑</span><span>↑</span></div>
    <div class="trow">${causas.map(t=>`<div class="tbox cau">${t}</div>`).join('')}</div>
    <div class="tlab" style="margin-top:8px;color:var(--orange)">${rodape||'Causas — onde o projeto atua'}</div></div>`,
  funil: rows => { const mx = rows[0][1], cor = ['var(--lav)','var(--blue)','var(--navy)','var(--purple)','var(--orange)'];
    return `<div class="fn-wrap">`+rows.map((f,i)=>`<div class="frow"><div class="fbar" style="width:${Math.max(30,82-i*12)}%;background:${cor[i%cor.length]}"><div class="fey">${f[0]}</div><div class="fn tnum">${f[2]||Math.round(f[1]).toLocaleString('pt-BR')}</div></div>${f[3]?`<div class="fnote">${f[3]}</div>`:''}</div>`).join('')+`</div>`; },
  hlbar: (b, txt) => `<div class="hlbar"><b class="tnum">${b}</b><span>${txt}</span></div>`,
  objgeral: t => `<div class="objgeral">${t}</div>`,
  lista: a => `<ul class="clean">`+a.map((t,i)=>`<li><span class="num">${i+1}</span><div>${t}</div></li>`).join('')+`</ul>`,
  steps: a => `<div class="steps">`+a.map(s=>`<div class="step"><b>${s[0]}</b><span>${s[1]}</span></div>`).join('')+`</div>`,
  fluxo: a => { const cor=['var(--blue)','var(--purple)','var(--teal-d)','var(--orange)'];
    return `<div class="trow" style="grid-template-columns:repeat(${a.length},1fr)">`+a.map((f,i)=>`<div class="tbox cons" style="background:${cor[i%cor.length]}">${f[0]}<br><span style="font-weight:400;font-size:11px;opacity:.92">${f[1]}</span></div>`).join('')+`</div>`; },
  tabela: (head, rows, num, tot) => `<table><thead><tr>${head.map((h,i)=>`<th class="${(num||[]).includes(i)?'n':''}">${h}</th>`).join('')}</tr></thead><tbody>`+
    rows.map((r,ri)=>`<tr class="${tot&&ri===rows.length-1?'tot':''}">${r.map((c,i)=>`<td class="${(num||[]).includes(i)?'n':''}">${c}</td>`).join('')}</tr>`).join('')+`</tbody></table>`,
  cams: a => { const cor=[['var(--blue-l)','var(--blue)'],['var(--teal-l)','var(--teal-d)'],['var(--orange-l)','var(--orange)'],['var(--purple-l)','var(--purple)']];
    return `<div class="cams" style="grid-template-columns:repeat(${a.length},1fr)">`+a.map((c,i)=>`<div class="cam" style="background:${cor[i%4][0]}"><div class="cam-ey" style="color:${cor[i%4][1]}">${c.ey}</div><h4>${c.h}</h4><ul>${c.itens.map(t=>`<li>${t}</li>`).join('')}</ul><div class="price" style="color:${cor[i%4][1]}">${c.preco}</div></div>`).join('')+`</div>`; },
  huge: (v, sub) => `<div><div class="huge tnum">${v}</div><div class="huge-sub">${sub}</div></div>`,
  split: (a, b) => `<div class="split"><div class="edu" style="flex:${a[2]}"><span class="sl">${a[0]}</span><span class="ss">${a[1]}</span></div><div class="sau" style="flex:${b[2]}"><span class="sl">${b[0]}</span><span class="ss">${b[1]}</span></div></div>`,
  src: a => `<div class="src">`+a.map(s=>`<div class="scard ${s[0]}"><div class="se">${s[1]}</div><div class="sv tnum">${s[2]}</div><p>${s[3]}</p></div>`).join('')+`</div>`,
  navybar: (t, firme) => `<div class="navybar ${firme?'firme':''}">${t}</div>`,
  ente: (nm, mt, vb, vs) => `<div class="ente"><div><div class="nm">${nm}</div><div class="mt">${mt}</div></div><div class="vv"><b>${vb}</b><span>${vs}</span></div></div>`,
  nota: (icone, cabeca, itens, rodape) => `<div class="mpbox"><div class="mphead"><div class="mpicon">${icone}</div><div>${cabeca}</div></div>${itens&&itens.length?`<ul>${itens.map(t=>`<li>${t}</li>`).join('')}</ul>`:''}${rodape?`<p class="mpnote">${rodape}</p>`:''}</div>`,
  fotos: a => `<div class="fotos">`+a.map(f=>`<figure><img src="${f[0]}" alt="${f[1]}"><figcaption><b>${f[1]}</b><span>${f[2]}</span></figcaption></figure>`).join('')+`</div>`,
  modal: a => `<div class="modal">`+a.map(m=>`<div class="mcard"><div class="mic">${m[0]}</div><div><b>${m[1]}</b><span>${m[2]}</span></div></div>`).join('')+`</div>`,
  chips: a => `<div class="chips">`+a.map((c,i)=>`<span class="chip ${i<3?'c1':''}">${c}</span>`).join('')+`</div>`,
  modalPage: (lead, foco) => ({t:'Modalidades de execução', s:'Onde a ação acontece', s2:'Onde a ação acontece — unidades fixas e itinerantes', corpo:
    DK.blk('', DK.lead(lead))
    + DK.fotos([[DK_IMG.carreta,'Carreta da Saúde da Mulher','unidade itinerante com consultórios, sala de coleta e acolhimento'],[DK_IMG.caminhao,'Unidade móvel em caminhão','toldo, escadas de acesso e sala climatizada — montagem em minutos']])
    + DK.blk('As modalidades — o gestor escolhe conforme o território', DK.modal([
        ['🚛','Carreta da Mulher','consultórios e coleta em bairros, distritos e zona rural'],
        ['🚌','Ônibus da saúde','rota programada por UBS, com agenda de convocação'],
        ['⛺','Tenda com cabine','cabine privativa em praças, eventos, escolas e empresas'],
        ['🏥','UBS (Atenção Primária)','sala de coleta na própria unidade de referência'],
        ['🚑','Pronto atendimento / UPA','oportunidade de rastreio para quem já está no serviço'],
        ['🏢','Ações extramuros','mutirões em comunidades, presídios, aldeias e ribeirinhos']]))
    + DK.blk('Programas que se integram à mesma ação', DK.chips(['Carreta da Mulher','Saúde da Mulher','Mutirão das Mulheres','PinkPapa · colo do útero','RosalindTest · mama','Linda Life Tech','Ultrassonografia','Mamografia','Agora Tem Especialistas']))
    + DK.navybar(foco,true)}),
  link: (url, t) => `<a href="${url}" target="_blank" rel="noopener">${t} &#8599;</a>`
};
function deckHTML(S){
  const band = `<div class="band"><b>${S.faixa}</b><span>${S.alvo} · Proposta técnica</span></div>`;
  const ft = n => `<div class="ft"><span>${S.rodape}</span><span class="pgn">${String(n).padStart(2,'0')}</span></div>`;
  const sec = (no,t,s,navy) => `<div class="sec"><div class="sqr" ${navy?'style="background:var(--navy)"':''}>${no}</div><div><h2>${t}</h2><div class="ssub">${s}</div></div></div><div class="rule"></div>`;
  const pg = (n, cab, corpo) => `<div class="pg">${band}<div class="pbody">${cab}<div class="fill">${corpo}</div></div>${ft(n)}</div>`;
  const marca = S.logo ? `<img src="${S.logo}" alt="${S.marca}">` : `<span class="wm">${S.marca}</span>${S.marcaSub?`<span class="wms">${S.marcaSub}</span>`:''}`;
  const sum = `<table class="sum"><tbody>${S.paginas.map((p,i)=>`<tr><td class="n so">${String(i+1).padStart(2,'0')}</td><td class="st"><b>${p.t}</b><span>${p.s}</span></td><td class="n sp">${String(i+3).padStart(2,'0')}</td></tr>`).join('')}</tbody></table>`;
  const rede = S.fecho.rede;
  return `<!DOCTYPE html>
<html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">
<title>${S.titulo} · ${S.alvo}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap">
<style>
:root{
  --navy:#17204A; --navy2:#2B3A86; --ink:#1B2240; --muted:#5B6383; --faint:#8A90AE;
  --bg:#E9ECF4; --card:#fff; --line:#E4E7F1; --soft:#EEF0F8;
  --orange:#E0651A; --orange-l:#FDEBDD; --purple:#6A3FA0; --purple-l:#EFE8F8;
  --teal:#0E9488; --teal-d:#0A6B62; --teal-l:#DFF3F0; --blue:#3A4FA8; --blue-l:#E6E9F8; --lav:#8E97C9;
  --green:#0F7B55; --on1:#C6CCEA; --on2:#9AA2C8; --on3:#FFE2CC; --r1:#1E2A5E; --r2:#242F66; --r3:#2A3570; --r4:#1C2656; --em:#F6A868;
  color-scheme:light;
  ${S.cores||''}
}
*{box-sizing:border-box} b,strong{font-weight:700}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 "Inter",system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;padding:22px 16px 48px}
.deck{max-width:840px;margin:0 auto;display:flex;flex-direction:column;gap:22px}
.tnum{font-variant-numeric:tabular-nums}
.pg{background:var(--card);border-radius:12px;overflow:hidden;box-shadow:0 1px 2px rgba(20,34,90,.06),0 14px 36px rgba(20,34,90,.10);display:flex;flex-direction:column;min-height:1188px}
.band{background:var(--navy);color:#fff;display:flex;justify-content:space-between;align-items:center;padding:12px 34px;font-size:11px;letter-spacing:.06em}
.band b{text-transform:uppercase;letter-spacing:.1em;font-weight:800}
.band span{color:var(--on1)}
.pbody{padding:30px 34px 22px;flex:1;display:flex;flex-direction:column}
.fill{flex:1;display:flex;flex-direction:column;justify-content:space-between;gap:20px}
.blk{display:block}
.sec{display:flex;align-items:center;gap:16px;margin-top:4px}
.sqr{width:50px;height:50px;border-radius:10px;background:var(--orange);color:#fff;display:grid;place-items:center;font-size:21px;font-weight:800;flex:none}
.sec h2{margin:0;font-size:28px;font-weight:800;color:var(--navy);letter-spacing:-.02em}
.sec .ssub{font-size:14px;color:var(--muted);font-style:italic;margin-top:2px}
.rule{height:2px;background:linear-gradient(90deg,var(--orange),transparent 85%);opacity:.55;margin:14px 0 24px;border-radius:2px}
.ey{font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;font-weight:800;color:var(--orange);margin:0 0 12px}
.lead{font-size:15.5px;color:var(--ink);margin:0;line-height:1.62;text-align:justify}
.lead + .lead{margin-top:12px}
.stats4{display:grid;gap:18px}
.snum b{display:block;font-size:34px;font-weight:800;letter-spacing:-.02em;line-height:1}
.snum span{display:block;font-size:12.5px;color:var(--muted);margin-top:8px;line-height:1.35}
.snum.b1 b{color:var(--blue)} .snum.b2 b{color:var(--green)} .snum.b3 b{color:var(--purple)} .snum.b4 b{color:var(--orange)} .snum.bn b{color:var(--navy)}
.hl{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px 28px;display:flex;align-items:center;gap:26px;box-shadow:0 8px 24px rgba(20,34,90,.06)}
.hl .big{font-size:50px;font-weight:900;color:var(--orange);letter-spacing:-.03em;line-height:1;white-space:nowrap}
.hl .big.navy{color:var(--navy)}
.hl .txt{font-size:16px;color:var(--ink);line-height:1.5}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.box{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;box-shadow:0 4px 14px rgba(20,34,90,.04)}
.box .bt{font-size:11.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--navy);margin-bottom:6px}
.box p{margin:0;font-size:13.5px;color:var(--muted);line-height:1.5}
.box.o{border-top:4px solid var(--orange)} .box.b{border-top:4px solid var(--blue)} .box.t{border-top:4px solid var(--teal)} .box.p{border-top:4px solid var(--purple)} .box.n{border-top:4px solid var(--navy)}
.fn-wrap{display:flex;flex-direction:column;gap:8px}
.frow{display:flex;align-items:center;gap:16px}
.fbar{border-radius:10px;padding:9px 18px;color:#fff;flex:none}
.fbar .fey{font-size:10.5px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;opacity:.92}
.fbar .fn{font-size:22px;font-weight:800;letter-spacing:-.01em;margin-top:1px}
.fnote{font-size:13px;color:var(--muted);font-style:italic;min-width:0}
.hlbar{background:var(--teal-l);border-radius:12px;padding:14px 20px;display:flex;align-items:baseline;gap:14px}
.hlbar b{font-size:28px;color:var(--teal-d);font-weight:800;white-space:nowrap} .hlbar span{font-size:14px;color:var(--ink)}
.tlab{font-size:10.5px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:2px 0 8px}
.trow{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.tbox{border-radius:10px;padding:15px 14px;font-size:13.5px;font-weight:600;text-align:center;line-height:1.35}
.tbox.cons{background:var(--navy);color:#fff}
.tbox.cau{background:#fff;border:1px solid var(--line);color:var(--ink);box-shadow:0 4px 14px rgba(20,34,90,.05)}
.tarr{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:8px 0}
.tarr span{text-align:center;color:var(--orange);font-size:22px;font-weight:800;line-height:1}
.central{background:var(--orange);color:#fff;border-radius:10px;padding:14px 16px;text-align:center}
.central .cl{font-size:10px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;opacity:.9}
.central .ct{font-size:18px;font-weight:800}
.cams{display:grid;gap:16px} .fill>.cams{flex:1}
.cam{border-radius:16px;padding:20px 20px 22px;display:flex;flex-direction:column;min-height:380px}
.cam-ey{font-size:11px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;margin-bottom:4px}
.cam h4{margin:0 0 14px;font-size:19px;color:var(--navy);line-height:1.2}
.cam ul{margin:0;padding-left:16px;flex:1} .cam li{font-size:13.5px;color:var(--ink);margin:0 0 11px;line-height:1.45}
.cam .price{font-size:21px;font-weight:800;letter-spacing:-.01em;margin-top:8px}
.navybar{background:var(--navy);color:#fff;border-radius:12px;padding:17px 22px;text-align:center;font-size:15.5px;font-weight:600;font-style:italic}
.navybar.firme{font-style:normal;font-weight:700}
.huge{font-size:60px;font-weight:900;color:var(--navy);letter-spacing:-.03em;line-height:1;margin:2px 0 6px}
.huge-sub{font-size:14px;color:var(--muted);font-style:italic}
.split{display:flex;min-height:58px;border-radius:12px;overflow:hidden}
.split div{display:flex;flex-direction:column;justify-content:center;padding:8px 18px;color:#fff}
.split .sl{font-size:15px;font-weight:800} .split .ss{font-size:12px;opacity:.92}
.split .edu{background:var(--navy)} .split .sau{background:var(--orange)}
table{border-collapse:collapse;width:100%;font-size:13.5px}
thead th{background:var(--navy);color:#fff;text-align:left;font-size:11.5px;letter-spacing:.04em;padding:11px 12px;font-weight:700}
thead th.n{text-align:right}
td{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:nth-child(even) td{background:var(--soft)}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr.tot td{font-weight:800;color:var(--navy);border-top:2px solid var(--navy);border-bottom:none;background:#fff !important}
table.sum td{padding:7px 12px;background:#fff !important}
table.sum .so{color:var(--orange);font-weight:800;width:46px;text-align:left;font-size:18px}
table.sum .st b{color:var(--navy);font-size:15.5px;display:block} table.sum .st span{color:var(--muted);font-style:italic;font-size:12.5px}
table.sum .sp{color:var(--navy);font-weight:800;vertical-align:middle}
.kpiband{background:var(--navy);border-radius:16px;padding:26px 28px;display:grid;grid-template-columns:repeat(4,1fr);gap:18px}
.kpiband b{display:block;color:#fff;white-space:nowrap;font-size:27px;font-weight:800;letter-spacing:-.02em;line-height:1}
.kpiband span{display:block;color:var(--on1);font-size:12.5px;margin-top:8px}
.src{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.scard{border-radius:14px;padding:18px 20px}
.scard .se{font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px}
.scard .sv{font-size:27px;font-weight:800;letter-spacing:-.02em;line-height:1.05}
.scard p{margin:8px 0 0;font-size:12.5px;color:var(--muted);line-height:1.45}
.scard a{color:inherit;font-weight:700}
.scard.hoje{background:var(--orange-l)} .scard.hoje .se,.scard.hoje .sv{color:var(--orange)}
.scard.edu{background:var(--blue-l)} .scard.edu .se,.scard.edu .sv{color:var(--blue)}
.scard.sau{background:var(--teal-l)} .scard.sau .se,.scard.sau .sv{color:var(--teal-d)}
ul.clean{padding-left:0;margin:0;list-style:none;display:flex;flex-direction:column;gap:10px}
ul.clean li{font-size:14.5px;display:flex;gap:14px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 16px;box-shadow:0 4px 14px rgba(20,34,90,.04)}
ul.clean li .num{flex:none;width:30px;height:30px;border-radius:50%;background:var(--navy);color:#fff;display:grid;place-items:center;font-size:13px;font-weight:800}
.objgeral{background:#fff;border:1px solid var(--line);border-left:5px solid var(--orange);border-radius:0 12px 12px 0;padding:16px 20px;font-size:16px;font-weight:600;color:var(--navy);line-height:1.45}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;counter-reset:st}
.step{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px 16px;box-shadow:0 4px 14px rgba(20,34,90,.04)}
.step:before{counter-increment:st;content:counter(st);display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--navy);color:#fff;font-size:13px;font-weight:800;margin-bottom:11px}
.step b{display:block;color:var(--navy);font-size:15px;margin-bottom:4px} .step span{font-size:13px;color:var(--muted);line-height:1.5;display:block}
.ente{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;background:linear-gradient(120deg,var(--navy),var(--navy2));color:#fff;border-radius:14px;padding:22px 26px}
.ente .nm{font-size:24px;font-weight:800} .ente .mt{font-size:13px;color:var(--on1);margin-top:3px}
.ente .vv{text-align:right} .ente .vv b{font-size:18px;display:block} .ente .vv span{font-size:11.5px;color:var(--on1)}
.ft{margin-top:auto;padding:14px 34px 16px;display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--line);font-size:11px;color:var(--faint)}
.pgn{background:var(--orange);color:#fff;border-radius:6px;padding:3px 9px;font-weight:800;font-size:11px}
.mpbox{border:1px solid var(--line);background:var(--orange-l);border-left:5px solid var(--orange);border-radius:0 12px 12px 0;padding:18px 20px}
.mpbox .mphead{display:flex;gap:14px;align-items:flex-start;font-size:13.5px;line-height:1.5}
.mpbox .mpicon{flex:none;width:40px;height:40px;border-radius:10px;background:var(--orange);color:#fff;display:grid;place-items:center;font-size:20px}
.mpbox li{font-size:13px;color:var(--ink);line-height:1.5;margin:0 0 7px}
.mpbox ul{margin:12px 0 4px;padding-left:18px}
.mpbox a{color:var(--navy);font-weight:700}
.mpbox .mpnote{margin:8px 0 0;color:var(--muted);font-size:12.5px;font-style:italic}
.closing{position:relative;overflow:hidden;background:var(--navy);color:#fff;border-radius:12px;min-height:1188px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:48px 40px;box-shadow:0 14px 36px rgba(20,34,90,.16)}
.closing:after{content:"";position:absolute;right:-140px;top:-120px;width:460px;height:460px;border-radius:50%;background:radial-gradient(circle,var(--orange) 0%,transparent 68%);opacity:.5}
.closing .clsvg{position:relative;z-index:1;width:min(440px,92%);margin-bottom:22px}
.closing .cl-phrase{position:relative;z-index:1;font-size:48px;font-weight:900;letter-spacing:-.02em;line-height:1.08;margin:6px 0 20px}
.closing .cl-phrase em{font-style:normal;color:var(--em)}
.closing .cl-sub{position:relative;z-index:1;font-size:16px;color:var(--on1);max-width:52ch;line-height:1.6}
.closing .cl-logo{position:relative;z-index:1;margin-top:40px;display:flex;flex-direction:column;align-items:center;gap:12px}
.closing .cl-logo .chip{background:#fff;border-radius:10px;padding:8px 16px;display:flex;flex-direction:column;align-items:center}
.closing .cl-logo a{font-size:14px;color:#fff;font-weight:700;letter-spacing:.03em;text-decoration:none;border-bottom:2px solid var(--orange)}
.wm{color:var(--navy);font-size:27px;font-weight:800;letter-spacing:-.02em;line-height:1.05;display:block}
.wms{color:var(--orange);font-size:10.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;display:block;margin-top:2px}
.cover{position:relative;overflow:hidden;background:var(--navy);color:#fff;border-radius:12px;min-height:1188px;display:flex;flex-direction:column;box-shadow:0 14px 36px rgba(20,34,90,.16)}
.cover svg.rings{position:absolute;inset:0;width:100%;height:100%;z-index:0}
.cover .logo{position:relative;z-index:2;margin:44px 40px 0;background:#fff;border-radius:14px;padding:14px 20px;width:max-content;max-width:260px;box-shadow:0 8px 24px rgba(0,0,0,.18)}
.cover .logo img{display:block;width:100%;max-width:168px;height:auto}
.cover .titleblock{position:relative;z-index:2;background:var(--orange);margin:auto 60px 0 0;padding:38px 40px}
.cover .titleblock .eyebrow{font-size:12.5px;letter-spacing:.16em;text-transform:uppercase;font-weight:800;color:var(--on3)}
.cover .titleblock h1{font-size:50px;line-height:1.04;letter-spacing:-.02em;margin:12px 0 14px;font-weight:800;max-width:15ch}
.cover .titleblock .sub{font-size:17px;color:#fff;opacity:.94;max-width:44ch;margin:0;line-height:1.45}
.cover .meta{position:relative;z-index:2;padding:44px 40px 36px;display:grid;grid-template-columns:1fr 1fr;gap:28px 36px;max-width:740px}
.cover .meta .k{font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--on2);font-weight:800;padding-left:12px;border-left:3px solid var(--orange);margin-bottom:5px}
.cover .meta .d{font-size:15px;color:#fff;padding-left:12px;line-height:1.4}
.cover .meta .d small{color:var(--on2);font-size:12.5px}
.cover .url{position:relative;z-index:2;padding:0 40px 34px;font-size:12.5px}
.cover .url a{color:var(--on1);text-decoration:none;font-weight:600}
.noprint{position:fixed;right:18px;bottom:18px;z-index:9;background:var(--orange);color:#fff;border:0;border-radius:999px;padding:13px 20px;font:700 14px Inter,system-ui,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.25);cursor:pointer}
.fotos{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.fotos figure{margin:0;border-radius:14px;overflow:hidden;background:#fff;border:1px solid var(--line);box-shadow:0 4px 14px rgba(20,34,90,.06)}
.fotos img{display:block;width:100%;height:210px;object-fit:cover}
.fotos figcaption{padding:10px 14px} .fotos figcaption b{display:block;color:var(--navy);font-size:14px} .fotos figcaption span{font-size:12.5px;color:var(--muted)}
.modal{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.mcard{display:flex;gap:12px;align-items:flex-start;background:#fff;border:1px solid var(--line);border-top:4px solid var(--orange);border-radius:12px;padding:14px}
.mcard .mic{font-size:26px;line-height:1} .mcard b{display:block;color:var(--navy);font-size:14px} .mcard span{font-size:12.5px;color:var(--muted);line-height:1.4}
.chips{display:flex;flex-wrap:wrap;gap:8px} .chip{background:var(--soft);border:1px solid var(--line);color:var(--navy);border-radius:999px;padding:7px 14px;font-size:13px;font-weight:600} .chip.c1{background:var(--navy);color:#fff;border-color:var(--navy)}
@page{size:A4;margin:0}
@media print{
  *{-webkit-print-color-adjust:exact !important;print-color-adjust:exact !important}
  body{padding:0;background:#fff}
  .deck{zoom:.9449;width:840px;max-width:none;gap:0;margin:0}
  .pg,.cover,.closing{height:1188px;min-height:0;border-radius:0;box-shadow:none;break-after:page;page-break-after:always;break-inside:avoid}
  .noprint{display:none}
}
@media (max-width:720px){ .fotos,.modal{grid-template-columns:1fr !important}
  .pg,.cover,.closing{min-height:0}
  .stats4,.grid3,.grid4,.cams,.steps,.src,.kpiband{grid-template-columns:1fr 1fr !important}
  .cover .meta,.grid2{grid-template-columns:1fr}
  .trow,.tarr{grid-template-columns:1fr !important} .tarr{display:none}
  .pbody{padding:22px 18px 14px} .band{padding:11px 18px} .ft{padding:14px 18px 16px}
  .cover .logo{margin:28px 20px 0} .cover .titleblock{margin:40px 0 0;padding:28px 20px} .cover .titleblock h1{font-size:34px}
  .cover .meta,.cover .url{padding-left:20px;padding-right:20px}
  .hl{flex-direction:column;align-items:flex-start;gap:10px} .hl .big{font-size:38px;white-space:normal} .huge{font-size:40px}
  .closing .cl-phrase{font-size:32px}
}
</style></head><body>
<button class="noprint" onclick="window.print()">Salvar em PDF / Imprimir</button>
<div class="deck">

<div class="cover">
  <svg class="rings" viewBox="0 0 840 1188" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <circle cx="700" cy="400" r="430" fill="var(--r1)"/><circle cx="700" cy="400" r="300" fill="var(--r2)"/>
    <circle cx="700" cy="400" r="175" fill="var(--r3)"/><circle cx="150" cy="1090" r="260" fill="var(--r4)"/>
  </svg>
  <div class="logo">${marca}</div>
  <div class="titleblock">
    <div class="eyebrow">${S.capa.sobre}</div>
    <h1>${S.capa.titulo}</h1>
    <p class="sub">${S.capa.sub}</p>
  </div>
  <div class="meta">${S.capa.meta.map(m=>`<div><div class="k">${m[0]}</div><div class="d"><b>${m[1]}</b>${m[2]?`<br><small class="tnum">${m[2]}</small>`:''}</div></div>`).join('')}</div>
  <div class="url"><a href="${S.url}" target="_blank" rel="noopener">${S.urlTxt}</a></div>
</div>

${pg(2, sec('≡','Sumário',S.paginas.length+' seções, cada uma responde a uma pergunta do gestor',true), sum + `<div class="kpiband">${S.destaques.map(k=>`<div><b class="tnum">${k[0]}</b><span>${k[1]}</span></div>`).join('')}</div>`)}

${S.paginas.map((p,i)=>pg(i+3, sec(String(i+1).padStart(2,'0'), p.t, p.s2||p.s), p.corpo)).join('\n')}

<div class="closing">
  <svg class="clsvg" viewBox="0 0 420 230" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <line x1="210" y1="120" x2="92" y2="58" stroke="var(--blue)" stroke-width="3"/>
    <line x1="210" y1="120" x2="328" y2="58" stroke="var(--purple)" stroke-width="3"/>
    <line x1="210" y1="120" x2="210" y2="198" stroke="var(--teal)" stroke-width="3"/>
    <circle cx="210" cy="120" r="42" fill="var(--orange)"/>
    <path d="M195 120 l11 12 l21 -25" stroke="#fff" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    <g font-family="Inter,sans-serif" font-weight="700" font-size="11.5" fill="#fff">
      <circle cx="92" cy="54" r="34" fill="var(--blue)"/><text x="92" y="58" text-anchor="middle">${rede[0]}</text>
      <circle cx="328" cy="54" r="34" fill="var(--purple)"/><text x="328" y="58" text-anchor="middle">${rede[1]}</text>
      <circle cx="210" cy="198" r="34" fill="var(--teal)"/><text x="210" y="202" text-anchor="middle">${rede[2]}</text>
    </g>
  </svg>
  <div class="cl-phrase">${S.fecho.frase}</div>
  <div class="cl-sub">${S.fecho.sub}</div>
  <div class="cl-logo"><div class="chip">${marca}</div><a href="${S.url}" target="_blank" rel="noopener">${S.urlTxt}</a></div>
</div>

</div></body></html>`;
}
async function baixarDeck(S, arquivo){
  // gera o PDF A4 (1 página por seção) a partir do mesmo HTML e baixa direto na máquina
  const btn=document.activeElement, old=btn&&btn.tagName==='BUTTON'?btn.innerHTML:null; if(old) btn.innerHTML='⏳ Gerando PDF…';
  const pdfName=arquivo.replace(/\.html$/,'.pdf'); let f;
  try{
    if(!window.html2canvas) await new Promise((ok,er)=>{const sc=document.createElement('script'); sc.src='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'; sc.onload=ok; sc.onerror=er; document.head.appendChild(sc);});
    f=document.createElement('iframe'); f.style.cssText='position:fixed;left:-10000px;top:0;width:880px;height:1300px;border:0'; document.body.appendChild(f);
    const D=f.contentDocument; D.open(); D.write(deckHTML(S)); D.close();
    await new Promise(r=>setTimeout(r,400)); try{ await D.fonts.ready; }catch(e){}
    await Promise.all([...D.images].map(im=>im.complete?0:new Promise(r=>{im.onload=im.onerror=r;})));
    const nb=D.querySelector('.noprint'); if(nb) nb.remove();
    const st=D.createElement('style'); st.textContent='.pg,.cover,.closing{border-radius:0!important;box-shadow:none!important}'; D.head.appendChild(st);
    D.querySelectorAll('svg [fill^="var("],svg [stroke^="var("]').forEach(el=>{const cs=f.contentWindow.getComputedStyle(el); if(el.getAttribute('fill')) el.setAttribute('fill',cs.fill); if(el.getAttribute('stroke')) el.setAttribute('stroke',cs.stroke);});
    const {jsPDF}=window.jspdf, doc=new jsPDF({unit:'pt',format:'a4'}), W=595.28, H=841.89;
    const pages=[...D.querySelectorAll('.cover,.pg,.closing')];
    for(let i=0;i<pages.length;i++){ const cv=await html2canvas(pages[i],{scale:1.6,useCORS:true,backgroundColor:'#ffffff',windowWidth:880});
      if(i) doc.addPage(); doc.addImage(cv.toDataURL('image/jpeg',0.88),'JPEG',0,0,W,H,undefined,'FAST'); }
    doc.save(pdfName);
  }catch(e){ console.error(e); alert('Não foi possível gerar o PDF ('+e.message+'). Baixando a versão HTML, que também pode ser salva em PDF.');
    const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([deckHTML(S)],{type:'text/html;charset=utf-8'})); a.download=arquivo; document.body.appendChild(a); a.click(); a.remove();
  }finally{ if(f) f.remove(); if(old) btn.innerHTML=old; }
}
/* Conteúdo da apresentação PinkPapa (rastreio do colo do útero) — dados do município selecionado. Identidade vinho/rosa. */
function apresSpec(c){
  const x=_ctx(c), R=x.recon, m=c.muni, K=DK;
  const hoje=new Date(), ymd=hoje.toISOString().slice(0,10).replace(/-/g,'');
  const ref='PP-DNAHPV-'+(m[5]||m[1]||'')+'-'+ymd;
  const pA=(c.covA*100).toFixed(0)+'%', pM=(c.covM*100).toFixed(0)+'%', pAd=(c.ades*100).toFixed(0)+'%';
  const prazo=c.prazo||12, t3=Math.max(1,Math.round(prazo/3));
  const mortes=Math.round(c.mortesEvit||0), ente=m[4]?'estado':'município';
  const sus=R&&!R.semSaldo, emenda=R&&R.saldoEmendas>0;
  const paginas=[
  {t:'Apresentação', s:'O projeto em uma página', corpo:
    K.blk('', K.lead(x.alvo+' tem <b>'+fmt(x.pop)+' mulheres de 25 a 64 anos</b> (Censo 2022) e cobertura estimada de rastreio do câncer do colo do útero de <b>'+pA+'</b>, distante da meta de 70% da OMS. A citologia convencional deixa passar de 30% a 45% das lesões de alto grau, depende de coleta com espéculo e não alcança quem nunca se rastreou.')
      + K.lead('Este projeto propõe um <b>mutirão de rastreio por DNA-HPV com autocoleta</b>: busca ativa pela Atenção Primária, teste molecular de alta sensibilidade e navegação de cada mulher positiva até a colposcopia e o tratamento.'))
    + K.boxes(3,[['b','Objeto','Mutirão de rastreio por DNA-HPV (autocoleta), com busca ativa e navegação das positivas'],
        ['t','Público',fmt(x.testes)+' mulheres rastreadas, de ~'+fmt(x.conv)+' convocadas na busca ativa'],
        ['o','Entrega','Laudo individual, seguimento garantido na rede e painel de indicadores por UBS']])
    + K.blk('O que o '+ente+' passa a ter', K.stats([[fmt(x.testes),'mulheres rastreadas com laudo individual','bn'],['~'+fmt(x.hpv),'positivas navegadas até a colposcopia','b3'],
        ['~'+fmt(x.les),'lesões de alto grau detectadas e tratadas','b4'],['~'+fmt(x.casos),'cânceres evitados por tratamento precoce','b2']]))
    + K.hl(pA+' → '+pM,'é o salto de <b>cobertura do rastreio</b> neste ciclo de '+prazo+' meses, com um teste que só precisa ser repetido a cada 5 anos após resultado negativo.')
    + K.navybar('O kit é o instrumento; o objeto é o serviço. Nenhum resultado dispensa laudo e conduta profissional.')},

  {t:'Realidade e problema', s:'O que falta na rede hoje', corpo:
    K.blk('O contexto local', K.stats([[pA,'cobertura atual estimada do rastreio','b1'],[fmt(x.pop),'mulheres de 25 a 64 anos no '+ente,'b2'],
        ['30–45%','das lesões de alto grau a citologia não detecta','b3'],['~'+fmt(x.lesC),'lesões que o Papanicolau perderia neste ciclo','b4']]))
    + K.hl('~'+fmt(x.les),'<b>lesões de alto grau</b> esperadas entre as mulheres rastreadas — todas tratáveis antes de virarem câncer, se houver teste sensível e seguimento garantido.')
    + K.blk('A árvore do problema', K.tree(['Câncer diagnosticado em estágio avançado','Tratamento oncológico caro e mutilante','Mortes evitáveis de mulheres em idade ativa'],
        'Baixa cobertura e seguimento fragmentado',
        ['Citologia de baixa sensibilidade, com espéculo','Mulheres que nunca se rastrearam, fora do radar','Positivas sem seguimento garantido na rede']))
    + K.blk('A cobrança das metas oficiais', K.nota('&#9878;','<b>O rastreio do colo do útero já é meta pactuada e cobrada do gestor.</b> A estratégia global da OMS (90-70-90) fixa 70% das mulheres rastreadas com teste de alto desempenho, e o SUS incorporou o teste molecular de DNA-HPV como método de rastreio.',
        ['<b>Portaria SECTICS/MS nº 3/2024:</b> incorpora o teste de DNA-HPV ao SUS para o rastreio do câncer do colo do útero (SIGTAP 0202100251).',
         '<b>Lei nº 14.758/2023:</b> Política Nacional de Prevenção e Controle do Câncer — rastreio organizado e diagnóstico oportuno como dever do sistema.'],
        'Com cobertura medida e seguimento registrado, o gestor demonstra o cumprimento das metas e responde aos órgãos de controle.'))},

  {t:'Público-alvo e objetivos', s:'Para quem e para quê', corpo:
    K.blk('Do universo ao atendimento', K.funil([['Mulheres de 25 a 64 anos — população-alvo',x.pop,'','Censo 2022 (IBGE)'],
        ['Convocadas pela busca ativa',x.conv,'~'+fmt(x.conv),'prioridade a quem nunca se rastreou'],
        ['Rastreadas por DNA-HPV (autocoleta)',x.testes,'','adesão de '+pAd+' — base do cálculo'],
        ['HPV de alto risco positivo',x.hpv,'~'+fmt(x.hpv),'seguem para triagem e colposcopia'],
        ['Lesões de alto grau (NIC2+)',x.les,'~'+fmt(x.les),'tratadas na referência']])
      + '<div style="height:8px"></div>' + K.hlbar('~'+fmt(x.casos),'cânceres evitados por tratamento precoce'+(mortes?' — e cerca de '+fmt(mortes)+' mortes evitadas':'')+', nas premissas do painel'))
    + K.blk('Objetivo geral', K.objgeral('Garantir a cada mulher de 25 a 64 anos um rastreio de alta sensibilidade e, às positivas, o seguimento completo até o tratamento — elevando a cobertura de '+pA+' para '+pM+'.'))
    + K.blk('Objetivos específicos', K.lista(['<b>Convocar</b> ~'+fmt(x.conv)+' mulheres por busca ativa, priorizando quem nunca se rastreou.',
        '<b>Realizar</b> '+fmt(x.testes)+' testes de DNA-HPV por autocoleta, com genotipagem 16/18.',
        '<b>Detectar</b> ~'+fmt(x.les)+' lesões de alto grau, das quais ~'+fmt(x.lesC)+' invisíveis à citologia.',
        '<b>Assegurar</b> o seguimento das positivas na rede e evitar ~'+fmt(x.casos)+' cânceres.']))},

  {t:'Justificativa', s:'O dever legal e a cobrança', s2:'O dever legal e o que a evidência recomenda', corpo:
    K.blk('', K.lead('O rastreio organizado do câncer do colo do útero, com diagnóstico e tratamento oportunos, é obrigação legal do ente. O projeto dá ao '+ente+' o meio de cumpri-la com a tecnologia já incorporada ao SUS — e de demonstrar esse cumprimento com registro auditável.'))
    + K.boxes(2,[['b','Lei nº 11.664/2008','Assegura as ações de prevenção, detecção e tratamento dos cânceres do colo do útero e de mama no SUS.'],
        ['b','Lei nº 14.758/2023','Política Nacional de Prevenção e Controle do Câncer — rastreio organizado e linha de cuidado integral.'],
        ['b','Lei nº 12.732/2012','Primeiro tratamento oncológico no SUS em até 60 dias após o diagnóstico.'],
        ['b','Portaria SECTICS/MS nº 3/2024','Incorpora o teste molecular de DNA-HPV ao SUS para o rastreio (Diretrizes INCA/MS).']])
    + K.blk('O que a evidência mostra', K.stats([['90–95%','de sensibilidade do DNA-HPV para lesões de alto grau','b1'],['5 anos','de intervalo após resultado negativo','b2'],
        ['~100%','de aceitação da autocoleta, sem espéculo','b3'],['~30%','de economia para o SUS no longo prazo (CONITEC)','b4']]))
    + K.hl(fmtMoney(x.preco),'por mulher testada — ante dezenas de milhares de reais por paciente no <b>tratamento oncológico tardio</b>. Prevenir é a decisão de menor custo.',true)
    + K.navybar('O serviço converte a meta de cobertura em execução demonstrável: teste realizado, laudo emitido e seguimento registrado.',true)},

  {t:'Descrição do projeto', s:'As camadas de serviço', s2:'Três camadas de serviço em torno de cada mulher', corpo:
    K.cams([{ey:'Rastreio',h:'A mulher alcançada',itens:['<b>Busca ativa</b> pela Atenção Primária e agentes comunitários','<b>Kit de autocoleta</b> DNA-HPV, sem espéculo (SIGTAP 0202100251)','<b>Teste molecular</b> com genotipagem 16/18 e laudo em até 48h'],preco:DK.mi(x.receita)},
        {ey:'Seguimento',h:'A positiva tratada',itens:['<b>Citologia reflexa</b> nas HPV+ (~'+fmt(x.cito)+')','<b>Colposcopia</b> (~'+fmt(x.colp)+') e <b>biópsia</b> (~'+fmt(x.biop)+')','<b>EZT/conização</b> (~'+fmt(x.ezt)+') na referência pactuada'],preco:'Na rede · MAC/FAEC/OCI'},
        {ey:'Navegação',h:'Ninguém se perde',itens:['<b>Navegação de pacientes</b> do teste ao tratamento','<b>Reconvocação</b> em 5 anos após resultado negativo','<b>Painel de indicadores</b> por UBS e consolidado'],preco:'Incluso no serviço'}])
    + K.navybar('O kit é o instrumento; o objeto é o serviço — convocar, testar, laudar e navegar cada mulher até o desfecho.')
    + K.blk('O que não integra o objeto', K.boxes(2,[['n','Procedimentos de seguimento','Colposcopia, biópsia e EZT são executados e financiados pela rede (MAC/FAEC/OCI). O projeto dimensiona, encaminha e monitora.'],
        ['n','Tratamento oncológico','Casos de câncer confirmados seguem a linha de cuidado da alta complexidade, com registro e prazo acompanhados.']]))},

  DK.modalPage('O mutirão chega onde a mulher está. A autocoleta de DNA-HPV não exige mesa ginecológica nem espéculo — por isso a ação pode ser executada em unidades fixas da rede ou em estruturas itinerantes, escolhidas pelo gestor conforme o território, e todas integram o serviço contratado.','Num mesmo dia de ação, a carreta pode reunir o rastreio do colo (PinkPapa), da mama (RosalindTest) e exames de imagem — várias linhas de cuidado, uma só convocação.'),

  {t:'Metodologia', s:'A jornada da mulher', s2:'A jornada da mulher, da convocação ao tratamento', corpo:
    K.steps([['Busca ativa','ACS e Atenção Primária convocam, priorizando quem nunca se rastreou; meta por UBS.'],
        ['Autocoleta','Em pontos fixos e ações itinerantes, sem espéculo, com orientação da equipe.'],
        ['Teste DNA-HPV','Análise molecular com genotipagem 16/18 e laudo em até 48 horas.'],
        ['Triagem reflexa','Citologia apenas nas HPV+; só as alteradas seguem para a colposcopia.'],
        ['Laudo e devolutiva','Resultado à mulher e à UBS; negativo reconvocado em 5 anos.'],
        ['Seguimento','Colposcopia, biópsia e EZT na referência pactuada, com navegação.']])
    + K.blk('O fluxo entre atenção primária, laboratório e referência', K.fluxo([['Atenção Primária','convoca e orienta'],['Laboratório','testa e lauda'],['Referência','confirma e trata'],['Atenção Primária','acompanha e reconvoca']]))
    + K.hl('48h','é o prazo do laudo do teste molecular — e cada positiva tem o <b>caminho até a colposcopia definido antes do início</b> da ação, pactuado em CIR/PPI.')
    + K.navybar('Nenhum resultado dispensa laudo profissional. A autocoleta sinaliza e encaminha; diagnóstico e conduta são sempre do profissional de saúde.',true)},

  {t:'Plano de trabalho e cronograma', s:'Metas, lotes e prazos', s2:'Metas, lotes de implantação e prazos', corpo:
    K.tabela(['Meta','Atividade','Quantidade','Parâmetro de aferição'],[
        ['<b>M1</b>','Busca ativa e convocação','~'+fmt(x.conv)+' mulheres','Convocadas sobre a população-alvo'],
        ['<b>M2</b>','Testes de DNA-HPV por autocoleta',fmt(x.testes)+' testes','Testes válidos sobre convocadas'],
        ['<b>M3</b>','Triagem reflexa das HPV+','~'+fmt(x.cito)+' citologias','Citologias reflexas realizadas'],
        ['<b>M4</b>','Seguimento por colposcopia e biópsia','~'+fmt(x.colp)+' colposcopias','Positivas com seguimento no prazo'],
        ['<b>M5</b>','Tratamento das lesões (EZT)','~'+fmt(x.ezt)+' procedimentos','Lesões tratadas sobre detectadas'],
        ['<b>M6</b>','Navegação e monitoramento',fmt(x.testes)+' mulheres','Mulheres sem perda de seguimento']],[2])
    + K.blk('Implantação faseada por lotes de UBS', K.boxes(3,[['t','Lote 1 · meses 1–'+t3,'UBS de maior população-alvo e menor cobertura — cerca de '+fmt(x.testes*0.5)+' testes'],
        ['o','Lote 2 · meses '+t3+'–'+(2*t3),'Demais UBS urbanas da rede — cerca de '+fmt(x.testes*0.3)+' testes'],
        ['p','Lote 3 · meses '+(2*t3)+'–'+prazo,'Distritos, zona rural e ações itinerantes — cerca de '+fmt(x.testes*0.2)+' testes']]))
    + K.hl(prazo+' meses','de execução, com <b>medição mensal</b>: começa pelas unidades de maior demanda, avalia os indicadores e expande, sem interromper o seguimento já iniciado.',true)
    + K.navybar('Paga-se o que foi efetivamente realizado: teste com laudo emitido e seguimento registrado.',true)},

  {t:'Metas e indicadores', s:'Como o resultado é medido', s2:'Como o resultado é medido e comprovado', corpo:
    K.stats([['≥ '+pM,'de cobertura do rastreio ao fim do ciclo','b2'],['≤ 48h','entre o recebimento da amostra e o laudo','b2'],
        ['≥ 90%','das HPV+ com seguimento no prazo','b2'],['100%','das lesões de alto grau com tratamento indicado','b2']])
    + K.tabela(['Resultado','Indicador','Meio de verificação'],[
        ['<b>Cobertura ampliada</b>','Percentual da população-alvo testada no ciclo','SISCAN e painel do projeto'],
        ['<b>Tempestividade</b>','Tempo médio entre a coleta e o laudo','Registro com data no laboratório'],
        ['<b>Seguimento efetivo</b>','HPV+ com colposcopia realizada no prazo','Regulação e prontuário da referência'],
        ['<b>Resolutividade</b>','Lesões tratadas sobre lesões detectadas','Registro de EZT/conização'],
        ['<b>Adesão</b>','Mulheres testadas sobre convocadas','Listas de convocação por UBS'],
        ['<b>Reconvocação</b>','Negativas com retorno agendado em 5 anos','Agenda da Atenção Primária']])
    + K.hl('~'+fmt(x.casos),'cânceres evitados é o <b>resultado final esperado</b> — medido pelo tratamento precoce das lesões detectadas, com retorno socioeconômico estimado de '+(c.roiSoc*100).toFixed(0)+'%.')
    + K.navybar('Todos os indicadores são apurados por mês e comprovados na fonte: SISCAN, regulação e laboratório.',true)},

  {t:'Recursos e fontes', s:'Quanto custa e de onde vem', corpo:
    K.huge(fmtMoney(x.receita),'valor de referência do ciclo · '+fmtMoney(x.preco)+' por mulher rastreada')
    + K.split(['Rastreio · objeto do projeto',DK.mi(x.receita)+' — kit, teste e laudo',76],['Seguimento','na rede · MAC/FAEC/OCI',24])
    + K.tabela(['Componente','Quantidade','Valor unitário','Valor'],[
        ['Kit PinkPapa — autoteste DNA-HPV (SIGTAP 0202100251)',fmt(x.testes),fmtMoney(x.preco),fmtMoney(x.receita)],
        ['Citologia reflexa <span style="color:var(--muted)">(na rede, referencial)</span>','~'+fmt(x.cito),'MAC/SIA','—'],
        ['Colposcopia <span style="color:var(--muted)">(na rede, referencial)</span>','~'+fmt(x.colp),'MAC/FAEC/OCI','—'],
        ['Biópsia e EZT <span style="color:var(--muted)">(na rede, referencial)</span>','~'+fmt(x.biop+x.ezt),'MAC/FAEC/OCI','—'],
        ['Total do projeto','','',fmtMoney(x.receita)]],[1,2,3],true)
    + K.blk('De onde vem o recurso', K.src([['hoje','Fonte da ação',(x.fonte||'MAC').split(' (')[0].replace('Média e Alta Complexidade','MAC'),'fonte selecionada no painel para custear o rastreio (produção nova)'],
        ['edu','SUS 360 · saldo a comprovar',R?(R.semSaldo?'sem saldo':DK.mi(R.envelope)):'a confirmar',R?(sus?'já antecipado ao fundo — comporta ~'+fmt(R.acaoTestadas)+' mulheres. '+K.link(x.painel,'Conferir na fonte'):'recurso antecipado já consumido nesta competência. '+K.link(x.painel,'Conferir na fonte')):'gestor sem recurso próprio de especializada nesta competência'],
        ['sau','Emendas no saldo',emenda?DK.mi(R.saldoEmendas):'a prospectar',emenda?'parcela do saldo oriunda de emendas. '+K.link(R.emendaURL,'Ver emendas do gestor'):'emenda parlamentar e Mutirão das Mulheres como fontes complementares']]))
    + K.navybar(sus?'O seguimento das HPV+ gera produção ambulatorial que consome o saldo já antecipado — e evita a glosa por não-produção (PATE, NT 33/2026).':'Cada fonte executa a sua parcela: o MAC paga a produção nova; emenda e Mutirão das Mulheres complementam.',true)},

  {t:'Monitoramento e riscos', s:'Como se acompanha e se previne', s2:'Como se acompanha a execução e se previne o que pode dar errado', corpo:
    K.boxes(3,[['b','Comitê gestor','Secretaria de Saúde, Atenção Primária e executora. Reunião mensal e relatório trimestral.'],
        ['b','Medição mensal','Relatório de serviços até o quinto dia útil. Paga-se o que foi efetivamente prestado.'],
        ['b','Painel de indicadores','Cobertura, tempestividade e seguimento, por UBS e consolidado.']])
    + K.blk('Riscos e respostas', K.tabela(['Risco','Resposta'],[
        ['<b>Baixa adesão à autocoleta</b>','Busca ativa pelos ACS, educação em saúde e pontos de coleta itinerantes'],
        ['<b>Perda de seguimento das HPV+</b>','Navegação de pacientes e alerta de prazo para cada positiva'],
        ['<b>Gargalo na colposcopia</b>','Dimensionamento prévio da demanda e referência pactuada em CIR/PPI antes do início'],
        ['<b>Atraso no laudo</b>','Prazo contratual de 48h, com logística de amostras por lote de UBS'],
        ['<b>Dados sensíveis de saúde</b>','Registro no SISCAN, criptografia e consentimento, conforme a LGPD']]))
    + K.hl('0','mulheres perdidas entre o teste positivo e o tratamento é a <b>meta de navegação</b> — cada caso tem responsável, prazo e registro.',true)
    + K.navybar('A Secretaria de Saúde é a controladora dos dados do rastreio. Tratamento conforme a LGPD, com relatório de impacto antes da operação.',true)},

  {t:'Contratação e decisão', s:'Caminhos legais e o que se pede', s2:'Dois caminhos já instruídos e o que se pede ao gestor', corpo:
    K.boxes(2,[['o','Lei nº 14.133/2021 — contratação pública','Pregão eletrônico ou registro de preços. Estudo técnico preliminar e termo de referência prontos; pagamento mensal pelo serviço prestado.'],
        ['p','Lei nº 13.019/2014 — MROSC','Parceria com OSC por Termo de Colaboração, com Plano de Trabalho, chamamento público ou dispensa justificada e prestação de contas.']])
    + K.hl('Rota do painel','<b>'+x.instr.label+'</b> — as peças de instrução (ETP, nota técnica, minuta e plano de trabalho ou termo de referência) já saem geradas com os dados de '+x.alvo+'.',true)
    + K.blk('O que se pede ao gestor', K.lista(['<b>Validar</b> o dimensionamento ('+fmt(x.testes)+' mulheres, cobertura de '+pA+' para '+pM+') e a fonte do recurso.',
        '<b>Autorizar</b> a abertura do instrumento — licitação ou parceria — com as peças já instruídas.',
        '<b>Pactuar</b> o seguimento das HPV+ em CIR/PPI e designar o comitê gestor e o fiscal.']))
    + K.navybar('Decisão de baixo risco: tecnologia incorporada ao SUS, peças prontas e pagamento por serviço efetivamente prestado.',true)},

  {t:'Proponente e base documental', s:'Quem faz e o que sustenta', corpo:
    K.ente('PinkPapa · PinkLab','Rastreio do câncer do colo do útero por DNA-HPV com autocoleta','lp.tealliance.com.br','Plataforma e base documental')
    + K.boxes(2,[['o','Quem faz','PinkPapa (PinkLab), com a G3 Health Service na estruturação, no dimensionamento e na instrução do processo de contratação.'],
        ['t','Base documental','Dimensionamento por IBGE (Censo 2022) e Manual DNA-HPV (INCA/MS) · SUS 360 (PATE) · referência '+ref+'.']])
    + K.blk('Documentos que acompanham o projeto', '<div class="grid4">'+['Estudo técnico preliminar','Termo de referência','Nota técnica','Proposta técnica e comercial','Plano de trabalho','Minuta do instrumento','Memória de cálculo','Proposta (PNSB)'].map((d,i)=>'<div class="box '+(i%2?'o':'n')+'"><div class="bt" style="margin:0">'+d+'</div></div>').join('')+'</div>')
    + K.blk('Fontes públicas', K.lead('IBGE (Censo 2022, SIDRA 9514) · INCA/MS (Manual e Diretrizes do rastreio por DNA-HPV) · CONITEC · SUS 360 / PATE (NT nº 33/2026) · Portal da Transparência. <span style="color:var(--muted);font-style:italic">Adesão e parâmetros da rede são estimativas, a confirmar no plano de trabalho. Valores sujeitos a pesquisa de preços. Este documento apoia a decisão do gestor e não constitui parecer jurídico nem orientação clínica.</span>'))
    + K.navybar('Dados e metodologia completos no painel PinkPapa, onde esta apresentação é gerada e atualizada por município ou estado.')}
  ];
  return { titulo:'Projeto Técnico', alvo:x.alvo, faixa:'Projeto Rastreio DNA-HPV', rodape:'PinkPapa · PinkLab · Documento de apoio à decisão do gestor',
    marca:'PinkPapa', marcaSub:'PinkLab · G3 Health Service', url:'https://lp.tealliance.com.br/', urlTxt:'lp.tealliance.com.br',
    cores:'--navy:#7C1D4F;--navy2:#B4126A;--ink:#2A1622;--muted:#75606B;--faint:#A48E9A;--bg:#F1E6EC;--line:#F1DDE7;--soft:#FBF3F7;--orange:#E6007E;--orange-l:#FDE6F2;--on1:#F0CFDF;--on2:#E3A9C6;--on3:#FFE0F0;--r1:#882158;--r2:#932661;--r3:#9F2B6A;--r4:#701A47;--em:#FF9CCB;',
    capa:{sobre:'Proposta técnica · '+hoje.getFullYear(), titulo:'Rastreio do câncer do colo do útero', sub:'DNA-HPV por autocoleta — mutirão com busca ativa e seguimento garantido',
      meta:[['Preparado para',x.orgao,''],['Proponente','PinkPapa · PinkLab','contato@pinkpapa.com.br'],['Local de realização',x.alvo,fmt(x.pop)+' mulheres de 25 a 64 anos'],['Data e referência',dataExtenso(hoje),ref]]},
    destaques:[['~'+fmt(x.conv),'convocadas na busca ativa'],[fmt(x.testes),'mulheres rastreadas'],['~'+fmt(x.casos),'cânceres evitados'],[DK.mi(x.receita),'valor de referência']],
    paginas,
    fecho:{rede:['Atenção Primária','Laboratório','Referência'], frase:'Rastrear hoje.<br><em>Evitar o câncer amanhã.</em>',
      sub:'O PinkPapa reúne atenção primária, laboratório e referência em torno de cada mulher — do convite ao desfecho, nenhuma se perde no caminho. Nenhuma mulher deveria morrer de um câncer evitável.'},
    arquivo:'Apresentacao_PinkPapa_'+_mun()+'.html' };
}
function baixarApresentacao(){ if(!_reqCalc()) return; const S=apresSpec(lastCalc); baixarDeck(S,S.arquivo); }

/* ===== documentos técnicos (proposta técnica + nota técnica) em PDF ===== */
/* Proposta Técnica e Nota Técnica: formato de texto padrão (Times, cab. 12 / corpo 11, justificado).
   Mantém a API (titleblock/toc/box/h1/p/li/tbl/link/sign) usada pelos geradores e o render em 2 passes. */
function _tec(doc,titulo,alvo){
  const W=doc.internal.pageSize.getWidth(),H=doc.internal.pageSize.getHeight();
  const ML=72,MR=57,MT=60,MB=56,CW=W-ML-MR,LH=15.4;
  let y, startPage;
  function head(){ doc.setFont('times','italic');doc.setFontSize(9);doc.setTextColor(90,90,90);
    doc.text(doc.splitTextToSize(titulo+' — '+alvo,CW),ML,MT-22,{align:'left'});
    doc.setDrawColor(0,0,0);doc.setLineWidth(0.3);doc.line(ML,MT-12,W-MR,MT-12);
    doc.setTextColor(0,0,0); return MT; }
  function nl(){ doc.addPage(); y=head(); }
  function ensure(h){ if(y+h>H-MB) nl(); }
  function body(){ doc.setFont('times','normal');doc.setFontSize(11);doc.setTextColor(0,0,0); }
  function just(L){ return (L.length>1)?{align:'justify',maxWidth:CW}:{}; }
  const tocH=n=>20+n*14+14;   // deve coincidir com toc() para o render em 2 passes
  const api={
    sections:[],   // {title,page} capturado em cada h1 (p/ o sumário)
    startPage:1,
    begin(append){ if(append) doc.addPage(); startPage=doc.internal.getNumberOfPages(); api.startPage=startPage; y=head(); return api; },
    titleblock(meta){
      doc.setFont('times','bold');doc.setFontSize(13);doc.setTextColor(0,0,0);
      let L=doc.splitTextToSize(meta.tipo,CW); L.forEach((ln,i)=>doc.text(ln,W/2,y+13+i*16,{align:'center'})); y+=L.length*16+5;
      doc.setFont('times','normal');doc.setFontSize(11);
      L=doc.splitTextToSize(meta.sub,CW); L.forEach((ln,i)=>doc.text(ln,W/2,y+12+i*14,{align:'center'})); y+=L.length*14+10;
      doc.setFontSize(10.5);doc.setTextColor(40,40,40);
      meta.linhas.forEach(l=>{ const LL=doc.splitTextToSize(l,CW); LL.forEach((ln,i)=>doc.text(ln,ML,y+11+i*13)); y+=LL.length*13+1; });
      doc.setTextColor(0,0,0);doc.setDrawColor(0,0,0);doc.setLineWidth(0.4);doc.line(ML,y+7,W-MR,y+7); y+=20; return api; },
    tocReserve(n){ y+=tocH(n); return api; },
    toc(entries){
      doc.setFont('times','bold');doc.setFontSize(12);doc.setTextColor(0,0,0);doc.text('SUMÁRIO',ML,y+10); y+=20;
      doc.setFont('times','normal');doc.setFontSize(11);
      entries.forEach(e=>{ doc.textWithLink(e.title,ML,y+10,{pageNumber:startPage+(e.page-1)});
        doc.text(String(e.page),W-MR,y+10,{align:'right'}); y+=14; });
      y+=14; return api; },
    box(label,value){ ensure(42);
      doc.setDrawColor(0,0,0);doc.setLineWidth(0.5);doc.rect(ML,y,CW,30);
      doc.setFont('times','normal');doc.setFontSize(10);doc.setTextColor(60,60,60);doc.text(label,ML+8,y+12);
      doc.setFont('times','bold');doc.setFontSize(12);doc.setTextColor(0,0,0);doc.text(value,ML+8,y+25);
      y+=30+12; return api; },
    h1(t){ ensure(30); api.sections.push({title:t,page:doc.internal.getCurrentPageInfo().pageNumber});
      doc.setFont('times','bold');doc.setFontSize(12);doc.setTextColor(0,0,0);
      const L=doc.splitTextToSize(t.toUpperCase(),CW); L.forEach((ln,i)=>doc.text(ln,ML,y+12+i*15)); y+=L.length*15+9; return api; },
    p(t){ body(); const L=doc.splitTextToSize(t,CW); ensure(L.length*LH+6); doc.text(L,ML,y+11,just(L)); y+=L.length*LH+7; return api; },
    li(t){ body(); const L=doc.splitTextToSize(t,CW-16); ensure(L.length*LH+4);
      doc.text('•',ML+3,y+11); doc.text(L,ML+16,y+11,(L.length>1)?{align:'justify',maxWidth:CW-16}:{}); y+=L.length*LH+5; return api; },
    link(url){ body(); const L=doc.splitTextToSize(url,CW); ensure(L.length*LH+6);
      L.forEach((ln,i)=>doc.textWithLink(ln,ML,y+11+i*LH,{url})); y+=L.length*LH+8; return api; },
    tbl(head0,body0,cw,rightCols){ ensure(42);
      const cs=Object.assign({},cw||{});
      (rightCols||[]).forEach(ci=>cs[ci]=Object.assign({halign:'right'},cs[ci]||{}));
      doc.autoTable({startY:y,head:[head0],body:body0,margin:{left:ML,right:MR,top:MT},theme:'grid',
        headStyles:{fillColor:[255,255,255],textColor:[0,0,0],fontStyle:'bold',lineColor:[0,0,0],lineWidth:0.4,font:'times',fontSize:10},
        styles:{font:'times',fontSize:10,cellPadding:4,lineColor:[0,0,0],lineWidth:0.4,overflow:'linebreak',textColor:[0,0,0]},
        columnStyles:cs});
      y=doc.lastAutoTable.finalY+12; return api; },
    sign(contratante){ ensure(96); y+=24;
      doc.setFont('times','normal');doc.setFontSize(11);doc.setTextColor(0,0,0);
      const Lc=doc.splitTextToSize(contratante,230);
      doc.text('______________________________________',ML,y);
      doc.text('______________________________________',W-MR-230,y);
      doc.text(Lc,ML,y+13); doc.text('Interessado / Contratante',ML,y+13+Lc.length*12);
      doc.text('[ Executante técnico ]',W-MR-230,y+13); doc.text('Executante técnico',W-MR-230,y+25);
      y+=50; doc.text('Local e data: ____________________________________, ______ de __________________ de 2026.',ML,y); return api; },
    footer(){ const n=doc.internal.getNumberOfPages();
      for(let i=startPage;i<=n;i++){ doc.setPage(i);
        doc.setFont('times','normal');doc.setFontSize(9);doc.setTextColor(0,0,0);
        doc.setDrawColor(0,0,0);doc.setLineWidth(0.3);doc.line(ML,H-40,W-MR,H-40);
        doc.text('Rastreio por DNA-HPV (autocoleta) · documento de apoio à decisão',ML,H-28);
        doc.text('Página '+(i-startPage+1)+' de '+(n-startPage+1),W-MR,H-28,{align:'right'}); } return api; }
  };
  return api;
}
// renderiza em 2 passes: o 1º mede a página de cada seção (p/ o sumário), o 2º desenha com capa + sumário
function _renderTec(doc,titulo,alvo,meta,sumario,body,append){
  const {jsPDF}=window.jspdf;
  const s=_tec(new jsPDF({unit:'pt',format:'a4'}),titulo,alvo).begin(false);
  s.titleblock(meta); s.tocReserve(sumario.length); body(s);
  const pags=s.sections.map(x=>x.page);
  const w=_tec(doc,titulo,alvo).begin(append);
  w.titleblock(meta);
  w.toc(sumario.map((t,i)=>({title:t,page:pags[i]||1})));
  body(w); w.footer();
  return doc;
}
// reconciliação: dimensiona a ação pelo saldo SUS 360 (encaixe dinheiro × demanda). Fonte única p/ painel e peças.
// emendas no saldo SUS 360 não trazem o nº da emenda/proposta — deep-link ao Portal da Transparência
// com o gestor já preenchido na Busca Livre (palavraChave) + faixa de anos; usuário clica "Consultar".
function emendasURL(nomeGestor){
  const termo=(nomeGestor||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toUpperCase();
  return 'https://portaldatransparencia.gov.br/emendas/consulta?termo='+encodeURIComponent(termo)+'&de=2024&ate=2026';
}
function reconFrom(c){
  const m=c.muni, key=m[4]?(PATE_UF[m[1]]||''):(m[5]||''), d=key?PATE[key]:null;
  if(!d) return null;
  const pop=m[3], envelope=d.saldo||0, custoMeta=c.custoPrograma, preco=c.preco, ades=c.ades, covA=c.covA, covM=c.covM;
  const testesGap=c.testes;                                  // testadas p/ atingir a meta
  const testadasSaldo=preco>0?Math.floor(envelope/preco):0;  // o que o saldo em caixa paga
  const acaoTestadas=Math.max(0, testesGap>0?Math.min(testadasSaldo,testesGap):testadasSaldo); // encaixe
  const acaoConvocadas=ades>0?Math.round(acaoTestadas/ades):0;
  const ptsAcao=pop>0?acaoTestadas/pop*100:0;                // +pontos de cobertura efetiva
  const covB=covA+(pop>0?acaoTestadas/pop:0);                // cobertura resultante da ação
  const semSaldo=envelope<=0, saldoLimita=!semSaldo&&testadasSaldo<testesGap, demandaLimita=!semSaldo&&!saldoLimita;
  const folga=Math.max(0,envelope-custoMeta), falta=Math.max(0,custoMeta-envelope);
  console.assert(acaoTestadas<=testadasSaldo+1 && (testesGap<=0||acaoTestadas<=testesGap),'reconFrom: ação excede saldo/demanda');
  return {d,pop,envelope,custoMeta,preco,ades,covA,covM,testesGap,testadasSaldo,acaoTestadas,acaoConvocadas,
    ptsAcao,covB,semSaldo,saldoLimita,demandaLimita,folga,falta,custoTestada:preco,custoConvocada:preco*ades,mm:d.mutiraoMulheres||0,
    saldoEmendas:d.saldoEmendas||0, emendaURL:emendasURL(m[0])};
}
function reconFrase(r){
  if(!r) return '';
  const pw='Custo por mulher rastreada: '+fmtMoney(r.custoTestada)+' por teste ('+fmtMoney(r.custoConvocada)+' por mulher convocada). ';
  if(r.semSaldo) return pw+'Não há saldo antecipado a comprovar nesta competência: a ação é orçada por MAC (produção nova do rastreio) e/ou emenda, podendo ser enquadrada no Mutirão das Mulheres.';
  if(r.saldoLimita) return pw+'Com o saldo a comprovar de '+fmtMoney(r.envelope)+', a ação cabe em aproximadamente '+fmt(r.acaoTestadas)+' mulheres rastreadas (convocando ~'+fmt(r.acaoConvocadas)+'), elevando a cobertura de '+(r.covA*100).toFixed(0)+'% para ~'+(r.covB*100).toFixed(0)+'% — é a ação executável com o recurso já no fundo. Para a meta de '+(r.covM*100).toFixed(0)+'% o complemento de '+fmtMoney(r.falta)+' entra por MAC (produção nova), emenda ou Mutirão das Mulheres nos ciclos seguintes.';
  return pw+'A ação até a meta de '+(r.covM*100).toFixed(0)+'% custa '+fmtMoney(r.custoMeta)+' e rastreia aproximadamente '+fmt(r.acaoTestadas)+' mulheres; o saldo a comprovar ('+fmtMoney(r.envelope)+') cobre a ação com folga de '+fmtMoney(r.folga)+', que o município pode destinar ao seguimento das HPV+ e ao próximo ciclo. O mutirão converte esse recurso já antecipado em produção, cumprindo o encontro de contas do PATE (NT nº 33/2026) e evitando a glosa por não-produção.';
}
function _ctx(c){
  const m=c.muni, alvo=m[4]?m[0]:m[0]+'/'+m[1];
  const orgao=m[4]?(typeof UF_STATS!=='undefined'&&UF_STATS[m[1]]?UF_STATS[m[1]].orgao:('Secretaria de Saúde — '+m[0])):('Secretaria Municipal de Saúde de '+m[0]+'/'+m[1]);
  const pop=m[3], testes=Math.round(c.testes), conv=Math.round(c.adicionais), preco=c.preco;
  return {m,alvo,orgao,pop,testes,conv,preco,
    hpv:Math.round(c.hpvPos),les:Math.round(c.lesoes),lesC:Math.round(c.lesoesCitoPerde),casos:Math.round(c.casosEvit),
    cito:Math.round(testes*0.0926),colp:Math.round(testes*0.0618),biop:Math.round(testes*0.0433),ezt:Math.round(testes*0.0155),
    fonte:c.fonteLabel||'Média e Alta Complexidade (MAC)', instr:c.instr||INSTRUMENTOS.MROSC,
    receita:Math.round(c.custoPrograma), recon:reconFrom(c),
    painel:(()=>{const k=m[4]?(PATE_UF[m[1]]||''):(m[5]||'');return k?'https://sus360.saude.gov.br/painel/saldo-gestor/'+m[1]+'/'+k:'';})()};
}
function genPropostaTecnica(doc,c,append){
  const x=_ctx(c);
  const meta={tipo:'PROPOSTA TÉCNICA E COMERCIAL', sub:'Mutirão de rastreio de câncer de colo do útero por DNA-HPV (autocoleta) — '+x.alvo,
    linhas:['Interessado: '+x.orgao, 'Rota jurídica: '+x.instr.label+'  ·  Fonte de recurso: '+x.fonte]
      .concat(x.painel?['Competência PATE: '+PATE_COMP]:[])};
  const sumario=['1. Problema · Necessidade · Solução · Benefício','2. Objeto e enquadramento legal','3. Dimensionamento e alcance',
    '4. Plano de execução do mutirão','5. Investimento','6. Governança e pontos de averiguação','7. Documentação correlata'];
  const body=(w)=>{
  w.box('Valor estimado da contratação', fmtMoney(x.receita)+'  ·  '+fmt(x.testes)+' kits × '+fmtMoney(x.preco));
  w.h1('1. Problema · Necessidade · Solução · Benefício');
  w.p('PROBLEMA. O câncer do colo do útero é o 3º mais frequente entre as brasileiras e quase 100% evitável por rastreio de qualidade; a citologia detecta apenas 55–70% das lesões de alto grau. Em '+x.alvo+' a cobertura estimada é de '+(c.covA*100).toFixed(0)+'%.');
  w.p('NECESSIDADE. Ampliar o rastreio com tecnologia de maior sensibilidade e garantir o seguimento das positivas. Um mutirão com busca ativa e autocoleta alcança as mulheres que nunca se rastrearam.');
  w.p('SOLUÇÃO. Autoteste de DNA-HPV por autocoleta (ANVISA; SIGTAP 0202100251; Portaria SECTICS/MS nº 3/2024), custeável por '+x.fonte+'. Autocoleta sem espéculo, aceitação ~100%, sensibilidade 90–95%, rastreio a cada 5 anos após negativo, com monitoramento por IA.');
  w.p('BENEFÍCIO. Estima-se detectar ~'+fmt(x.les)+' lesões de alto grau (das quais ~'+fmt(x.lesC)+' que a citologia perderia) e evitar ~'+fmt(x.casos)+' câncer(es), estruturando a linha de cuidado e alinhando o município ao Previne Brasil e às metas 90-70-90.');
  w.h1('2. Objeto e enquadramento legal');
  w.p(x.instr.base);
  w.p('Em qualquer hipótese observam-se a motivação do ato, a pesquisa de preços (IN SEGES/ME nº 65/2021) e o dimensionamento pelo Manual DNA-HPV (INCA/MS) e PCDT. A composição de custos do fornecedor é referência e não substitui a pesquisa de mercado.');
  w.h1('3. Dimensionamento e alcance');
  w.tbl(['Etapa','Valor','Significado'],[
    ['População-alvo (25–64)',fmt(x.pop),'mulheres do município (IBGE 2022)'],
    ['Mulheres convocadas','~'+fmt(x.conv),'busca ativa — ainda sem rastreio'],
    ['Mulheres atendidas (testadas)',fmt(x.testes),'adesão '+(c.ades*100).toFixed(0)+'% — realizam a autocoleta'],
    ['HPV de alto risco +','~'+fmt(x.hpv),'('+(c.prev*100).toFixed(0)+'%) — seguem p/ colposcopia'],
    ['Lesões NIC2+','~'+fmt(x.les),'('+(c.pLes*100).toFixed(0)+'%) — ~'+fmt(x.lesC)+' que o Papanicolau perderia'],
    ['Cânceres evitados','~'+fmt(x.casos),'por tratamento precoce'],
  ],{0:{cellWidth:150,fontStyle:'bold',textColor:C_WINE}});
  w.p('Desdobramentos assistenciais esperados na rede (NÃO integram o objeto; Manual DNA-HPV INCA/MS):');
  w.tbl(['Procedimento','% s/ rastreadas','Volume','Financiamento'],[
    ['Citologia reflexa','9,26%','~'+fmt(x.cito),'MAC / SIA'],
    ['Colposcopia','6,18%','~'+fmt(x.colp),'MAC / FAEC / OCI'],
    ['Biópsia','4,33%','~'+fmt(x.biop),'MAC / FAEC'],
    ['Excisional (EZT/conização)','1,55%','~'+fmt(x.ezt),'MAC / FAEC / OCI'],
  ]);
  w.h1('4. Plano de execução do mutirão — linha de cuidado, ponto a ponto');
  ['1. Busca ativa / convocação — ACS e Atenção Primária (e-SUS/SISAB), priorizando quem nunca se rastreou; meta por UBS.',
   '2. Pontos de autocoleta — UBS, UPA, centros comunitários e ações itinerantes; insumos e EPI. Sem mesa ginecológica/espéculo.',
   '3. Teste DNA-HPV com genotipagem (16/18 + demais AR) — núcleo da ação; laudo em até 48h (laboratório executante).',
   '4. Triagem reflexa — citologia reflexa nas HPV+, evitando encaminhar todo HPV+ à colposcopia.',
   '5. Laudo e devolutiva — resultado e registro; negativo reconvocado em 5 anos, com IA.',
   '6. Seguimento garantido — colposcopia e biópsia na rede (referência pactuada em CIR/PPI). Assegurar antes do início.',
   '7. Tratamento das lesões — EZT/CAF e conização na referência.',
   '8. Registro no SISCAN e indicadores — Previne Brasil e 90-70-90.',
   '9. Educação em saúde e comunicação — integra-se à vacinação de HPV.'].forEach(t=>w.li(t));
  w.h1('5. Investimento');
  w.tbl(['Componente','Qtd.','Unitário','Total','Fonte'],[
    ['Kit de autocoleta (DNA-HPV + genotipagem + laboratório + IA + capacitação)',fmt(x.testes),fmtMoney(x.preco),fmtMoney(x.receita),x.fonte],
    ['Seguimento (citologia reflexa, colposcopia, biópsia, EZT)','conf. desdobr.','tabela SUS','programado na rede','MAC/FAEC/OCI'],
  ],{0:{cellWidth:180}},[1,2,3]);
  if(x.recon) w.p('Dimensionamento pela fonte (SUS 360). '+reconFrase(x.recon));
  if(x.painel){ w.p('Fonte oficial da viabilidade orçamentária (Saldo do Gestor — Programa Agora Tem Especialistas / SUS 360, competência '+PATE_COMP+'):');
    w.link(x.painel); }
  w.h1('6. Governança e pontos de averiguação (TCU/MP)');
  ['Motivação e enquadramento legal expressos.','Pesquisa de preços (IN 65/2021) — a composição de custos não a substitui.',
   'Segregação de funções: rastreio pela contratada; diagnóstico e tratamento na rede pública.',
   'Fonte de financiamento clara e registro em SIA/SIH.','Rastreabilidade: SISCAN, cadeia de custódia e responsabilidade técnica do laudo.',
   'Conformidade com a LGPD (dado sensível de saúde).','Plano de trabalho e prestação de contas com metas auditáveis.',
   'Gestão de riscos, com a capacidade de seguimento assegurada antes do início.'].forEach(t=>w.li(t));
  w.h1('7. Documentação correlata — '+x.instr.label);
  x.instr.docs.forEach(t=>w.li(t));
  w.sign(x.orgao);
  };
  return _renderTec(doc,'Proposta Técnica — Mutirão PinkPapa',x.alvo,meta,sumario,body,append);
}
function genNotaTecnica(doc,c,append){
  const x=_ctx(c);
  // estratificação de custos (estimativa, base planilha de custeio)
  const kitLab=x.testes*200, log=x.testes*20, plat=30000, cap=30000, coord=40000;
  const sub=kitLab+log+plat+cap+coord, trib=Math.round(x.receita*0.12), custo=sub+trib, margem=x.receita-custo;
  const margemPct=x.receita>0?(margem/x.receita*100):0, unit=x.testes>0?custo/x.testes:0;
  const meta={tipo:'NOTA TÉCNICA', sub:'Fundamentação técnica, legal e orçamentária — mutirão de rastreio por DNA-HPV — '+x.alvo,
    linhas:['Interessado: '+x.orgao, 'Rota jurídica: '+x.instr.label+'  ·  Fonte de recurso: '+x.fonte,
      'Elaboração: área técnica da unidade demandante — a ratificar']};
  const sumario=['1. Fundamentação técnica','2. Base legal','3. Dimensionamento e metas','4. Enquadramento orçamentário e financeiro',
    '5. Estratificação de custos','6. Documentação correlata','7. Conclusão'];
  const body=(w)=>{
  w.h1('1. Fundamentação técnica');
  ['Câncer de colo do útero é quase 100% evitável por rastreio (INCA; OMS); DNA-HPV detecta 90–95% (citologia 55–70%) e é o teste primário recomendado pela OMS.',
   'Incorporado ao SUS (Portaria SECTICS/MS nº 3/2024), SIGTAP 0202100251.',
   'Autocoleta com aceitação ~100% alcança quem nunca se rastreou (cobertura atual '+(c.covA*100).toFixed(0)+'%).',
   'CONITEC projeta -30% de custo no longo prazo substituindo a citologia.'].forEach(t=>w.li(t));
  w.h1('2. Base legal — '+x.instr.label);
  w.p(x.instr.base);
  w.h1('3. Dimensionamento e metas');
  w.p('População-alvo '+fmt(x.pop)+'. Ciclo: ~'+fmt(x.conv)+' convocadas, '+fmt(x.testes)+' testadas, ~'+fmt(x.hpv)+' HPV+, ~'+fmt(x.les)+' lesões NIC2+, ~'+fmt(x.casos)+' câncer(es) evitado(s). Seguimento assegurado antes do início (colposcopia pactuada em CIR/PPI).');
  w.h1('4. Enquadramento orçamentário e financeiro');
  w.tbl(['Componente','Fonte','Observação'],[
    ['Rastreio (teste DNA-HPV)',x.fonte+' · SIGTAP 0202100251','Valor contratado: '+fmtMoney(x.receita)],
    ['Citologia reflexa','MAC / SIA','Produção na rede/laboratório'],
    ['Colposcopia, biópsia, EZT','MAC / FAEC / OCI','Programado na rede'],
  ],{0:{cellWidth:150}});
  if(x.recon) w.p('Dimensionamento pela fonte (SUS 360). '+reconFrase(x.recon));
  if(x.painel){ w.p('Viabilidade orçamentária do gestor (Programa Agora Tem Especialistas / SUS 360, competência '+PATE_COMP+'): o seguimento das HPV+ gera produção ambulatorial que consome o saldo já antecipado ao fundo e cumpre o encontro de contas do PATE (NT nº 33/2026), evitando a glosa por não-produção. Os valores podem ser conferidos na fonte oficial:');
    w.link(x.painel); }
  w.h1('5. Estratificação de custos — custo da operação e margem');
  w.p('Estimativa (a validar no regime tributário e na composição analítica), base: planilha de custeio de referência. Cenário: '+fmt(x.testes)+' testes × '+fmtMoney(x.preco)+'.');
  w.tbl(['Item','Base','Valor'],[
    ['(=) Receita contratada',fmt(x.testes)+' × '+fmtMoney(x.preco),fmtMoney(x.receita)],
    ['(-) Exame molecular + kit (laboratório)',fmt(x.testes)+' x R$ 200',fmtMoney(kitLab)],
    ['(-) Logística e laudo 48h',fmt(x.testes)+' x R$ 20',fmtMoney(log)],
    ['(-) Plataforma digital + IA','alocação do ciclo',fmtMoney(plat)],
    ['(-) Capacitação e suporte','1 evento',fmtMoney(cap)],
    ['(-) Coordenação e gestão','equipe, ~1 mês',fmtMoney(coord)],
    ['(=) Subtotal de custos diretos','',fmtMoney(sub)],
    ['(-) Tributos (estimativa ~12%)','a validar (regime)',fmtMoney(trib)],
    ['(=) Custo total estimado','',fmtMoney(custo)],
    ['(=) MARGEM OPERACIONAL','',fmtMoney(margem)+'  ('+margemPct.toFixed(1)+'%)'],
  ],{0:{cellWidth:230}},[2]);
  w.box('Margem operacional estimada', fmtMoney(margem)+'  ('+margemPct.toFixed(1)+'% da receita · custo unitário ~'+fmtMoney(unit)+')');
  w.p('LEITURA. Margem operacional estimada de '+fmtMoney(margem)+' (~'+margemPct.toFixed(1)+'% da receita; custo unitário efetivo ~'+fmtMoney(unit)+' contra preço de '+fmtMoney(x.preco)+'). '+(margem<0?'No cenário atual a margem é negativa — os custos fixos (plataforma, capacitação, coordenação) não se diluem em um volume pequeno; recomenda-se rever preço/volume. ':'')+'A margem deve ser justificada na composição analítica apresentada ao controle.');
  w.p('ESCALA. Em volume maior (p.ex. 4.000 testes/ano) os custos fixos diluem-se e o custo integrado cai à ordem de R$ 250/exame — recomendando contratação por volume anual. Para mutirão isolado, ancorar o preço em pesquisa de mercado (IN 65/2021).');
  w.h1('6. Documentação correlata — '+x.instr.label);
  x.instr.docs.forEach(t=>w.li(t));
  w.h1('7. Conclusão');
  w.p('O mutirão por DNA-HPV é tecnicamente adequado, legalmente enquadrável e vantajoso frente à citologia e ao tratamento tardio. Recomenda-se: assegurar o seguimento; instruir a contratação com a documentação correlata acima; justificar o preço pela composição ou adotar patamar conservador; e registrar metas e indicadores auditáveis.');
  w.sign('Área Técnica — '+x.orgao);
  };
  return _renderTec(doc,'Nota Técnica — Mutirão PinkPapa',x.alvo,meta,sumario,body,append);
}
/* ===== renderizador PADRÃO EDITAL (Times, preto, justificado) ===== */
function _ed(doc){
  const W=doc.internal.pageSize.getWidth(), H=doc.internal.pageSize.getHeight();
  const ML=72, MR=57, MT=60, MB=58, CW=W-ML-MR, LH=16.8;   // margens ~ABNT em pt
  let y=MT;
  function ensure(h){ if(y+h>H-MB){ doc.addPage(); y=MT; } }
  function body(){ doc.setFont('times','normal'); doc.setFontSize(11); doc.setTextColor(0,0,0); }
  function just(L){ return (L.length>1)?{align:'justify',maxWidth:CW}:{}; }
  const api={
    title(lines){ doc.setTextColor(0,0,0);
      lines.forEach(l=>{ const s=l.s||12; doc.setFont('times', l.b===false?'normal':'bold'); doc.setFontSize(s);
        const L=doc.splitTextToSize(l.t,CW); ensure(L.length*s*1.25+6);
        L.forEach((ln,i)=>doc.text(ln,W/2,y+s+i*s*1.25,{align:'center'})); y+=L.length*s*1.25+4; });
      y+=6; return api; },
    h1(t){ ensure(30); doc.setFont('times','bold'); doc.setFontSize(12); doc.setTextColor(0,0,0);
      const L=doc.splitTextToSize(t.toUpperCase(),CW); L.forEach((ln,i)=>doc.text(ln,ML,y+12+i*15)); y+=L.length*15+9; return api; },
    h2(t){ ensure(22); doc.setFont('times','bold'); doc.setFontSize(12);
      const L=doc.splitTextToSize(t,CW); L.forEach((ln,i)=>doc.text(ln,ML,y+11+i*14)); y+=L.length*14+5; return api; },
    p(t){ body(); const L=doc.splitTextToSize(t,CW); ensure(L.length*LH+6);
      doc.text(L,ML,y+11,just(L)); y+=L.length*LH+6; return api; },
    al(items){ body(); const al='abcdefghijklmnopqrstuvwxyz';
      items.forEach((t,i)=>{ const L=doc.splitTextToSize(al[i]+') '+t,CW-18); ensure(L.length*LH+4);
        doc.text(L,ML+18,y+11,(L.length>1)?{align:'justify',maxWidth:CW-18}:{}); y+=L.length*LH+4; }); return api; },
    inc(items){ body(); items.forEach(t=>{ const L=doc.splitTextToSize(t,CW); ensure(L.length*LH+4);
        doc.text(L,ML,y+11,just(L)); y+=L.length*LH+4; }); return api; },
    tbl(head,body0,cw){ ensure(44); doc.autoTable({startY:y,head:[head],body:body0,margin:{left:ML,right:MR},theme:'grid',
        styles:{font:'times',fontSize:10,textColor:[0,0,0],lineColor:[0,0,0],lineWidth:0.4,cellPadding:4,overflow:'linebreak'},
        headStyles:{fillColor:[255,255,255],textColor:[0,0,0],fontStyle:'bold',lineColor:[0,0,0],lineWidth:0.4},
        columnStyles:cw||{}});
      y=doc.lastAutoTable.finalY+10; return api; },
    gap(h){ y+=(h||8); return api; },
    sign(blocks){ ensure(70+blocks.length*54); y+=26;
      doc.setFont('times','normal'); doc.setFontSize(11); doc.setTextColor(0,0,0);
      blocks.forEach(b=>{ doc.text('______________________________________',W/2,y,{align:'center'});
        b.forEach((s,i)=>doc.text(s,W/2,y+13+i*12,{align:'center'})); y+=52; });
      doc.text('__________________________, ______ de __________________ de 2026.',W/2,y+8,{align:'center'}); return api; },
    done(ref){ const n=doc.internal.getNumberOfPages();
      for(let i=1;i<=n;i++){ doc.setPage(i); doc.setFont('times','normal'); doc.setFontSize(9); doc.setTextColor(0,0,0);
        doc.setDrawColor(0,0,0); doc.setLineWidth(0.3); doc.line(ML,H-40,W-MR,H-40);
        doc.text(ref,ML,H-28); doc.text('Página '+i+' de '+n,W-MR,H-28,{align:'right'}); }
      return doc; }
  };
  return api;
}
const _DISC='Documento em modelo de trabalho. Os campos entre colchetes devem ser preenchidos pelo órgão com os dados locais. As estimativas de quantidade devem ser confirmadas pelo SISCAN, pelo e-SUS APS e pela base populacional; as de valor, por pesquisa de mercado própria, nos termos da Instrução Normativa SEGES/ME nº 65/2021. Trata-se de modelo de trabalho (minuta), que não substitui o juízo da área técnica, da assessoria jurídica e do controle interno.';

function genETP(doc,c){
  const x=_ctx(c), w=_ed(doc);
  w.title([
    {t:'[ BRASÃO / TIMBRE DO MUNICÍPIO ]',b:false,s:10},
    {t:x.orgao.toUpperCase(),s:12},
    {t:'ESTUDO TÉCNICO PRELIMINAR — ETP',s:13},
    {t:'CONTRATAÇÃO DE SERVIÇOS DE RASTREAMENTO ORGANIZADO DO CÂNCER DO COLO DO ÚTERO POR TESTE MOLECULAR DNA-HPV COM AUTOCOLETA',s:11},
  ]);
  const execLabel = x.instr.key==='MROSC'
    ? '[ OSC — razão social / CNPJ ], apoiada por laboratório de biologia molecular com responsabilidade técnica própria'
    : '[ credenciada(s) — razão social / CNPJ ], laboratório de biologia molecular com responsabilidade técnica própria';
  w.tbl(['Campo','Conteúdo'],[
    ['Processo administrativo nº','[ ___ / ______ ]'],
    ['Unidade demandante',x.orgao],
    ['Base legal',x.instr.key==='MROSC'?'Lei nº 13.019/2014 (MROSC) e, no que couber, a Lei nº 14.133/2021 (art. 18, aplicação subsidiária)':'Lei nº 14.133/2021 (arts. 18, 79 e 74, IV)'],
    ['Rota jurídica pretendida',x.instr.label],
    ['Modelo de execução','Ação concentrada e itinerante (mutirão) integrada à Atenção Primária, com retaguarda laboratorial e navegação de pacientes'],
    ['Executora',execLabel],
    ['Data','[ ___/___/______ ]'],
  ],{0:{cellWidth:150,fontStyle:'bold'}});
  w.p(_DISC);

  w.h1('1. Descrição da necessidade da contratação');
  w.p('1.1. O câncer do colo do útero é neoplasia de causa conhecida, evolução lenta e lesão precursora tratável e, ainda assim, permanece entre as principais causas de morte por câncer na população feminina brasileira, concentrando-se justamente nas mulheres que o rastreamento oportunístico não alcança. É doença quase integralmente evitável por rastreamento de qualidade associado ao tratamento tempestivo das lesões precursoras (INCA; OMS).');
  w.p('1.2. O modelo praticado na rede é predominantemente oportunístico, dependente da procura espontânea da usuária. A citologia convencional exige estrutura física específica (mesa ginecológica, espéculo e foco de luz) e profissional executor, impõe exposição corporal que afasta parcela relevante das mulheres e apresenta elevado absenteísmo e perda de seguimento entre a coleta e a conduta. Em '+x.alvo+', a cobertura estimada do rastreamento é da ordem de '+(c.covA*100).toFixed(0)+'%, inferior à meta de 70% (pilar 70 das metas 90-70-90 da Organização Mundial da Saúde).');
  w.p('1.3. Em 2024, a Comissão Nacional de Incorporação de Tecnologias no SUS (CONITEC) recomendou a adoção do teste molecular de detecção do DNA do Papilomavírus Humano (DNA-HPV) como exame primário de rastreamento, em substituição à citologia convencional, no âmbito de modelo de rastreamento organizado. A incorporação foi formalizada pela Portaria SECTICS/MS nº 3, de 7 de março de 2024, e o procedimento consta da Tabela SIGTAP sob o código 0202100251 (exame molecular de detecção de HPV), de média complexidade, com faixa etária de 25 a 64 anos e registro por BPA-I.');
  w.p('1.4. A autocoleta vaginal apresenta aceitação próxima de 100% e alcança mulheres que nunca se rastrearam, constituindo vetor essencial para elevar a cobertura. A necessidade da contratação decorre, assim, de quatro fatores convergentes: epidemiológico (persistência de mortalidade evitável); assistencial (baixa cobertura, absenteísmo e fragmentação do seguimento no modelo vigente); normativo (adequação à estratégia nacional de rastreamento organizado com teste molecular DNA-HPV); e de equidade (concentração da não-cobertura nas mulheres de maior vulnerabilidade social e territorial, que o modelo de espera passiva não alcança).');

  w.h1('2. Previsão no plano de contratações e alinhamento institucional');
  w.p('2.1. A ação [ está / não está ] prevista no Plano Municipal de Saúde e na Programação Anual de Saúde vigentes, aderindo às diretrizes de atenção integral à saúde da mulher e de detecção precoce de neoplasias, bem como aos indicadores do Previne Brasil relativos à cobertura de citopatológico.');
  w.p('2.2. Recomenda-se verificar a compatibilidade com o Plano Plurianual (PPA), a Lei de Diretrizes Orçamentárias (LDO) e a Lei Orçamentária Anual (LOA) vigentes, registrando-se expressamente a fonte de financiamento pretendida — recursos do bloco de Manutenção das Ações e Serviços Públicos de Saúde (MAC), recursos próprios, emendas parlamentares ou transferências fundo a fundo específicas.');

  w.h1('3. Requisitos da contratação');
  w.h2('3.1. Requisitos de natureza técnica e sanitária');
  w.al([
    'Kit de autocoleta vaginal composto por coletor, tubo com meio de transporte e manual ilustrado de instruções em português, com registro ativo na ANVISA e prazo de validade não inferior a 12 (doze) meses na data da entrega;',
    'Exame de biologia molecular para detecção e genotipagem do DNA-HPV, contemplando no mínimo 28 (vinte e oito) genótipos, com identificação individualizada, no mínimo, dos tipos 16 e 18;',
    'Laboratório analítico com inscrição regular no SCNES/CNES, licença sanitária vigente para diagnóstico molecular e responsável técnico habilitado;',
    'Controle interno de amplificação por amostra e participação em programa de controle de qualidade externo, quando disponível;',
    'Liberação do laudo em até 48 (quarenta e oito) horas contadas do recebimento da amostra no laboratório;',
    'Logística própria ou contratada de recolhimento e transporte de material biológico, com cadeia de custódia e conservação adequada;',
    'Plataforma digital (web e móvel) para cadastro, rastreabilidade, laudo digital, alerta automático de resultado alterado e seguimento longitudinal por até 5 (cinco) anos;',
    'Conformidade integral à Lei nº 13.709/2018 (LGPD), com criptografia, controle de acesso por perfil, registro de logs e encarregado de dados indicado;',
    'Plano de Gerenciamento de Resíduos de Serviços de Saúde (PGRSS), nos termos da RDC ANVISA nº 222/2018.',
  ]);
  w.h2('3.2. Requisitos de natureza assistencial');
  w.al([
    'Observância das diretrizes do Ministério da Saúde e do INCA para o rastreamento do câncer do colo do útero;',
    'Atendimento gratuito, humanizado, acessível e sem qualquer forma de discriminação, vedada cobrança direta ou indireta à usuária;',
    'Submissão integral à regulação do acesso exercida pela Secretaria Municipal de Saúde;',
    'Capacitação inicial e continuada das equipes da Atenção Primária quanto ao manuseio dos kits, à orientação da usuária e ao uso da plataforma;',
    'Navegação de pacientes: nenhuma mulher incluída na ação poderá ser liberada sem registro do canal e da data previstos para a devolutiva do resultado.',
  ]);
  w.h2('3.3. Natureza do serviço');
  w.p('3.3.1. A operação de campo (autocoleta realizada pela própria usuária, com apoio das equipes da Atenção Primária — Agentes Comunitários de Saúde e enfermagem) é de natureza comum, não constitui ato médico nem exige profissional médico especialista. Já o processamento laboratorial (biologia molecular — reação em cadeia da polimerase com genotipagem do HPV) é atividade técnica especializada de laboratório, executada sob responsabilidade técnica própria.');
  w.p('3.3.2. Os atos médicos especializados (colposcopia, biópsia, exérese da zona de transformação e tratamento) não integram este objeto e permanecem na rede pública, observada a segregação de funções.');
  w.h2('3.4. Vedação quanto a tecnologias não incorporadas');
  w.p('3.4.1. Nos termos do art. 19-T da Lei nº 8.080/1990, é vedado, em todas as esferas de gestão do SUS, o pagamento, o ressarcimento ou o reembolso de medicamento, produto ou procedimento clínico ou cirúrgico experimental, de uso não autorizado pela ANVISA ou não incorporado por ato do Ministério da Saúde. A solução pretendida restringe-se a tecnologia já incorporada ao SUS (SIGTAP 0202100251).');

  w.h1('4. Estimativa das quantidades e dimensionamento do primeiro ciclo');
  w.p('4.1. População-alvo de '+fmt(x.pop)+' mulheres de 25 a 64 anos. Dimensionamento do primeiro ciclo, considerando a meta de cobertura e a adesão estimada:');
  w.tbl(['Parâmetro','Estimativa'],[
    ['População-alvo (25 a 64 anos)',fmt(x.pop)],
    ['Mulheres convocadas (busca ativa)','~'+fmt(x.conv)],
    ['Testes DNA-HPV realizados (adesão '+(c.ades*100).toFixed(0)+'%)',fmt(x.testes)],
    ['Resultados HPV de alto risco positivos','~'+fmt(x.hpv)],
    ['Lesões NIC2+ esperadas','~'+fmt(x.les)],
    ['Cânceres evitados (estimativa)','~'+fmt(x.casos)],
  ],{0:{cellWidth:300}});
  w.p('4.2. Desdobramentos assistenciais esperados na rede (não integram o objeto; Manual DNA-HPV INCA/MS):');
  w.tbl(['Procedimento','Volume estimado','Financiamento'],[
    ['Citologia reflexa','~'+fmt(x.cito),'MAC / SIA'],
    ['Colposcopia','~'+fmt(x.colp),'MAC / FAEC / OCI'],
    ['Biópsia','~'+fmt(x.biop),'MAC / FAEC'],
    ['Exérese da zona de transformação (EZT)','~'+fmt(x.ezt),'MAC / FAEC / OCI'],
  ],{0:{cellWidth:230}});
  w.p('4.3. As quantidades deverão ser confirmadas com os dados do SISCAN, do e-SUS APS e da base populacional municipal antes do início. O seguimento (colposcopia e EZT) deverá estar assegurado e pactuado em CIR/PPI previamente à ação.');

  w.h1('5. Levantamento das soluções de mercado');
  w.p('5.1. A solução pretendida — kit de autocoleta, exame molecular DNA-HPV com genotipagem, logística, laudo e plataforma de seguimento — é ofertada por laboratórios e integradores no mercado nacional, em arranjo de solução integrada. Comparativamente à citologia convencional, o teste molecular DNA-HPV apresenta sensibilidade de 90 a 95% para lesões de alto grau (ante 55 a 70% da citologia), permite intervalo de rastreamento de cinco anos após resultado negativo e viabiliza a autocoleta, com redução de custo projetada no longo prazo (CONITEC).');
  w.p('5.2. Justifica-se, assim, a escolha da solução integrada por DNA-HPV com autocoleta como a de melhor relação entre benefício assistencial, alcance de equidade e custo, atendida a necessidade descrita no item 1.');

  w.h1('6. Estimativa do valor da contratação');
  w.p('6.1. O valor deverá ser estimado por pesquisa de mercado própria (Instrução Normativa SEGES/ME nº 65/2021 — mínimo de três fontes, atualizada em até seis meses), que constitui o parâmetro de aceitabilidade do preço.');
  w.p('6.2. A estratificação de custos da operação, quando apresentada, tem caráter de demonstração de exequibilidade (memória de cálculo) e não constitui o fundamento do preço: a eventual margem é resultado, e não parâmetro, da contratação. Por não se tratar de obra de engenharia, não se aplica régua de BDI nem limite de lucro; o único parâmetro de aceitabilidade é a compatibilidade com o preço de mercado (Lei nº 14.133/2021, arts. 11 e 23).');
  w.p('6.3. Para ciclo isolado de '+fmt(x.testes)+' testes, recomenda-se ancorar o valor unitário em pesquisa de mercado e, se necessário, adotar patamar conservador, prevendo-se a revisão do valor por volume em ciclos recorrentes.');

  w.h1('7. Justificativa do não-parcelamento');
  w.p('7.1. O objeto constitui solução integrada e indissociável (coleta, exame molecular, logística, laudo e seguimento), cujo fracionamento comprometeria a cadeia de custódia, a responsabilidade técnica do laudo e a rastreabilidade do seguimento, razão pela qual se justifica a contratação em objeto único, sem prejuízo da segregação de funções em relação aos atos especializados mantidos na rede.');

  w.h1('8. Contratações correlatas e interdependentes');
  w.p('8.1. A ação pressupõe a retaguarda assistencial da rede para o seguimento das mulheres com resultado alterado (colposcopia, biópsia e EZT), cuja capacidade deverá estar pactuada em CIR/PPI antes do início. Tais procedimentos não integram o objeto desta parceria e são financiados por MAC/FAEC/OCI.');

  w.h1('9. Base legal');
  w.al([x.instr.baseLegalETP,
    x.instr.key==='MROSC'
      ? 'Lei nº 14.133/2021 — aplicação subsidiária, especialmente quanto ao planejamento (art. 18) e à pesquisa de preços (art. 23);'
      : 'Lei nº 13.019/2014 (MROSC) — rota alternativa de parceria com organização da sociedade civil, afastada neste caso em favor do credenciamento;',
    'Lei nº 8.080/1990 e CF, art. 196 — dever do SUS na detecção precoce do câncer; Lei nº 11.664/2008 — ações de rastreamento do colo do útero;',
    'Portaria SECTICS/MS nº 3/2024 — incorporação do teste DNA-HPV ao SUS; Tabela SIGTAP, código 0202100251;',
    'Lei nº 8.080/1990, art. 19-T — vedação a tecnologias não incorporadas;',
    'Lei nº 13.709/2018 (LGPD) — tratamento de dado pessoal sensível de saúde;',
    'Manual de apoio à implementação do teste DNA-HPV (INCA/MS) e PCDT — dimensionamento e linha de cuidado.',
  ]);

  w.h1('10. Demonstração dos resultados pretendidos');
  w.al([
    'Elevação da cobertura do rastreamento rumo à meta de 70%, com priorização das mulheres nunca rastreadas;',
    'Redução do intervalo entre a coleta e a conduta e qualificação do encaminhamento à Atenção Especializada;',
    'Seguimento longitudinal nominal da população-alvo, com indicadores físico-financeiros auditáveis (Previne Brasil e metas 90-70-90);',
    'Fortalecimento da equidade no acesso ao rastreamento.',
  ]);

  w.h1('11. Providências prévias ao início');
  w.al([
    'Garantia da capacidade de seguimento (colposcopia e EZT) pactuada em CIR/PPI;',
    'Cadastro das unidades e dos profissionais no CNES e habilitação de acesso ao SISCAN (siscan.saude.gov.br/login.jsf);',
    'Adequação à LGPD, com definição do encarregado de dados e dos controles de segurança;',
    'Capacitação das equipes da Atenção Primária quanto à orientação da autocoleta e ao registro do procedimento.',
  ]);

  w.h1('12. Impactos ambientais');
  w.p('12.1. O manejo dos resíduos observará o Plano de Gerenciamento de Resíduos de Serviços de Saúde (PGRSS), nos termos da RDC ANVISA nº 222/2018, com segregação, acondicionamento e destinação adequados do material biológico e dos insumos.');

  w.h1('13. Posicionamento conclusivo sobre a viabilidade');
  w.p('13.1. Diante do exposto, a contratação é tecnicamente viável, '+x.instr.conc+' e economicamente vantajosa frente à citologia convencional e ao tratamento tardio. Recomenda-se prosseguir com a elaboração '+x.instr.prox+', assegurada a capacidade de seguimento antes do início da ação.');

  w.sign([
    ['[ NOME / MATRÍCULA / CARGO ]','Responsável técnico pela elaboração'],
    ['Autoridade competente — '+x.orgao,''],
  ]);
  return w.done('ETP — Rastreamento do colo do útero (DNA-HPV autocoleta) — '+x.alvo);
}

function genPlanoTrabalho(doc,c){
  const x=_ctx(c), w=_ed(doc);
  const kitLab=x.testes*200, log=x.testes*20, plat=30000, cap=30000, coord=40000, sub=kitLab+log+plat+cap+coord;
  w.title([
    {t:'[ BRASÃO / TIMBRE DO MUNICÍPIO ]',b:false,s:10},
    {t:x.orgao.toUpperCase(),s:12},
    {t:'PLANO DE TRABALHO',s:13},
    {t:'PARCERIA — LEI FEDERAL Nº 13.019/2014 (MROSC) — RASTREAMENTO DO CÂNCER DO COLO DO ÚTERO POR DNA-HPV COM AUTOCOLETA',s:11},
  ]);
  w.p(_DISC);
  w.h1('1. Identificação das partes e do instrumento');
  w.tbl(['Campo','Conteúdo'],[
    ['Administração Pública parceira',x.orgao],
    ['Organização da Sociedade Civil (OSC)','[ OSC — razão social / CNPJ / endereço ]'],
    ['Parceiro técnico-laboratorial','[ laboratório — razão social / CNPJ ] — biologia molecular, sob responsabilidade técnica própria'],
    ['Representante legal da OSC','[ nome / CPF / cargo ]'],
    ['Instrumento','Termo de Colaboração (art. 2º, VII, da Lei nº 13.019/2014)'],
    ['Vigência prevista','[ 12 meses ] a partir da assinatura'],
  ],{0:{cellWidth:170,fontStyle:'bold'}});
  w.h1('2. Objeto da parceria');
  w.p('2.1. Execução, em regime de mútua cooperação, de ação concentrada e itinerante (mutirão) de rastreamento organizado do câncer do colo do útero por teste molecular DNA-HPV com autocoleta vaginal, integrada à Atenção Primária do Município, com busca ativa nominal, retaguarda laboratorial, laudo digital e seguimento longitudinal das usuárias, sem cobrança direta ou indireta.');
  w.h1('3. Descrição da realidade objeto da parceria e nexo de causalidade (art. 22, I)');
  w.p('3.1. A cobertura do rastreamento em '+x.alvo+' situa-se na ordem de '+(c.covA*100).toFixed(0)+'%, com concentração da não-cobertura em mulheres de maior vulnerabilidade social e territorial. O modelo oportunístico vigente não alcança as mulheres que nunca se rastrearam, perpetuando mortalidade evitável.');
  w.p('3.2. A parceria enfrenta essa realidade por meio de mobilização comunitária, autocoleta e navegação de pacientes, em interesse público recíproco, elevando a cobertura rumo à meta de 70% e qualificando o seguimento das lesões precursoras. O nexo de causalidade entre a ação proposta e o resultado pretendido assenta-se na maior sensibilidade do teste molecular e na aceitação quase universal da autocoleta.');
  w.h1('4. Descrição de metas, etapas, cronograma e prazos (art. 22, II)');
  w.tbl(['Fase','Atividades','Prazo','Responsável'],[
    ['1. Planejamento','Pactuação com a Secretaria, definição das unidades de coleta (UBS/UPA/centros comunitários), meta por unidade e cadastro no SISCAN','Mês 1','OSC + Secretaria'],
    ['2. Capacitação','Treinamento das equipes da Atenção Primária (ACS/enfermagem) para orientar a autocoleta e registrar o procedimento SIGTAP 0202100251','Mês 1 a 2','OSC / laboratório'],
    ['3. Convocação','Busca ativa das mulheres de 25 a 64 anos, priorizando as que nunca se rastrearam; campanha e agendamento','Mês 2 em diante','Secretaria + ACS'],
    ['4. Autocoleta','Entrega e retirada do coletor; a mulher realiza a autocoleta sem espéculo e sem mesa ginecológica','Contínuo','Unidades de saúde'],
    ['5. Análise laboratorial','Processamento por PCR com genotipagem e emissão de laudo em até 48 horas','Contínuo','Laboratório executante'],
    ['6. Encaminhamento','Mulheres HPV+ de alto risco encaminhadas à colposcopia/tratamento na rede','Contínuo','Secretaria'],
    ['7. Monitoramento','Acompanhamento por plataforma/IA, painel de cobertura e indicadores (Previne Brasil / 90-70-90)','Até 5 anos','OSC + laboratório'],
  ],{0:{cellWidth:85,fontStyle:'bold'},2:{cellWidth:66}});
  w.h1('5. Forma de execução das atividades');
  w.al([
    'A OSC coordena a mobilização comunitária, a logística dos kits e a navegação das pacientes, com apoio das equipes da Atenção Primária;',
    'O laboratório executante realiza a etapa de biologia molecular, sob responsabilidade técnica própria, com laudo em até 48 horas e cadeia de custódia;',
    'A Administração Pública exerce a regulação do acesso e assegura o seguimento (colposcopia/EZT) na rede;',
    'Toda a operação é registrada em plataforma digital, em conformidade com a LGPD, com rastreabilidade e alerta de resultado alterado.',
  ]);
  w.h1('6. Parâmetros e indicadores de aferição do cumprimento (art. 22, III)');
  w.al([
    'Número de mulheres testadas em relação à meta do ciclo ('+fmt(x.testes)+' testes);',
    'Percentual de cobertura alcançado na população-alvo (rumo a 70%);',
    'Tempo médio entre coleta e laudo (meta: até 48 horas);',
    'Percentual de resultados HPV positivos com seguimento efetivado (colposcopia/conduta registrada);',
    'Percentual de mulheres nunca rastreadas alcançadas pela ação.',
  ]);
  w.h1('7. Previsão de receitas e de despesas — memória de cálculo');
  w.p('7.1. Os valores a seguir têm caráter de demonstração de exequibilidade e devem ser confirmados por pesquisa de mercado (IN SEGES/ME nº 65/2021). Referência do ciclo: '+fmt(x.testes)+' testes.');
  w.tbl(['Componente','Base','Valor (R$)'],[
    ['Exame molecular + kit (laboratório)',fmt(x.testes)+' × R$ 200',fmtMoney(kitLab)],
    ['Logística e laudo em 48h',fmt(x.testes)+' × R$ 20',fmtMoney(log)],
    ['Plataforma digital + monitoramento','alocação do ciclo',fmtMoney(plat)],
    ['Capacitação e suporte às equipes','1 evento',fmtMoney(cap)],
    ['Coordenação e gestão da ação','equipe, ~1 mês',fmtMoney(coord)],
    ['Subtotal','—',fmtMoney(sub)],
    ['Tributos sobre repasse','regime da OSC, a validar','a validar'],
    ['Valor total da parceria','—','[ a confirmar por pesquisa de mercado ]'],
  ],{0:{cellWidth:210}});
  w.h1('8. Cronograma de desembolso');
  w.p('8.1. Os repasses observarão [ parcela única / parcelas ] vinculadas ao cumprimento das metas e à prestação de contas, creditados em conta bancária específica da parceria, movimentada eletronicamente (arts. 51 e 53 da Lei nº 13.019/2014). Detalhar: [ parcelas, datas e condicionantes ].');
  w.h1('9. Contrapartida');
  w.p('9.1. [ Quando exigida ] A contrapartida da OSC, se houver, será definida em bens e/ou serviços economicamente mensuráveis, vedada a exigência de contrapartida financeira quando não prevista no edital, nos termos do art. 35, § 1º, da Lei nº 13.019/2014.');
  w.h1('10. Prestação de contas');
  w.p('10.1. A OSC prestará contas na forma dos arts. 63 a 72 da Lei nº 13.019/2014, com relatório de execução do objeto, relatório de execução financeira quando exigido e comprovação das metas físico-financeiras auditáveis, submetidos ao gestor da parceria e à comissão de monitoramento e avaliação, priorizado o controle de resultados.');
  w.sign([
    ['[ INSTITUTO ] — Organização da Sociedade Civil','Representante legal'],
    [x.orgao,'Gestor da parceria'],
  ]);
  return w.done('Plano de Trabalho (MROSC) — Colo do útero DNA-HPV — '+x.alvo);
}

function genTermoColaboracao(doc,c){
  const x=_ctx(c), w=_ed(doc);
  w.title([
    {t:'[ BRASÃO / TIMBRE DO MUNICÍPIO ]',b:false,s:10},
    {t:x.orgao.toUpperCase(),s:12},
    {t:'TERMO DE COLABORAÇÃO Nº [ ___ / ______ ]',s:13},
    {t:'LEI FEDERAL Nº 13.019/2014 (MROSC) — RASTREAMENTO DO CÂNCER DO COLO DO ÚTERO POR DNA-HPV COM AUTOCOLETA',s:11},
  ]);
  w.p('Termo de Colaboração que entre si celebram o MUNICÍPIO, por meio da '+x.orgao+', inscrita no CNPJ nº [ ___ ], neste ato representada por [ cargo / nome ], doravante denominada ADMINISTRAÇÃO PÚBLICA, e [ INSTITUTO — razão social ], inscrita no CNPJ nº [ ___ ], com sede em [ ___ ], neste ato representada por [ nome / cargo ], doravante denominada OSC, mediante as cláusulas e condições seguintes, observada a Lei nº 13.019/2014 e, no que couber, a legislação municipal de regência.');
  const cl=(n,t,ps)=>{ w.h1('Cláusula '+n+' — '+t); ps.forEach(p=>w.p(p)); };
  cl('Primeira','Do objeto',[
    'Constitui objeto deste Termo a execução, em regime de mútua cooperação, de ação concentrada e itinerante de rastreamento do câncer do colo do útero por teste molecular DNA-HPV com autocoleta, conforme o Plano de Trabalho que o integra independentemente de transcrição.']);
  cl('Segunda','Do Plano de Trabalho',[
    'O Plano de Trabalho, aprovado pela Administração Pública, é parte integrante e indissociável deste Termo, e dele constam as metas, as etapas, o cronograma de execução e de desembolso, os indicadores e a memória de cálculo. Alterações do Plano observarão o art. 57 da Lei nº 13.019/2014.']);
  cl('Terceira','Das obrigações da Administração Pública',[
    'I — exercer a regulação do acesso e integrar a ação à Atenção Primária; II — disponibilizar as unidades de coleta e o apoio das equipes; III — assegurar a capacidade de seguimento (colposcopia e EZT) na rede; IV — repassar os recursos conforme o cronograma de desembolso; V — designar o gestor da parceria e a comissão de monitoramento e avaliação; VI — analisar e manifestar-se sobre a prestação de contas.']);
  cl('Quarta','Das obrigações da OSC',[
    'I — executar o objeto com observância das diretrizes do Ministério da Saúde e do INCA e da natureza do serviço definida no Plano de Trabalho; II — assegurar, por si e por seu parceiro técnico-laboratorial, o exame molecular com responsabilidade técnica própria, laudo em até 48 horas e cadeia de custódia; III — manter plataforma de rastreabilidade e seguimento em conformidade com a LGPD; IV — não cobrar, direta ou indiretamente, das usuárias; V — manter conta bancária específica e movimentação eletrônica dos recursos; VI — prestar contas na forma dos arts. 63 a 72; VII — manter a regularidade jurídica, fiscal e trabalhista durante toda a vigência.']);
  cl('Quinta','Do valor e dos repasses',[
    'O valor global da parceria é de R$ [ ___ ] (referência de exequibilidade: '+fmtMoney(x.receita)+' para '+fmt(x.testes)+' testes), estimado por pesquisa de mercado (IN SEGES/ME nº 65/2021), repassado conforme o cronograma de desembolso do Plano de Trabalho, vedada a destinação a finalidade diversa da pactuada.']);
  cl('Sexta','Da conta bancária específica e da aplicação financeira',[
    'Os recursos serão depositados e geridos em conta bancária específica da parceria e, enquanto não empregados, aplicados em caderneta de poupança ou em fundo de aplicação financeira de curto prazo, nos termos do art. 51 da Lei nº 13.019/2014, revertendo os rendimentos ao objeto.']);
  cl('Sétima','Da vigência e das alterações',[
    'A vigência é de [ 12 (doze) meses ], contados da assinatura, prorrogável nos termos do art. 55 da Lei nº 13.019/2014. As alterações far-se-ão por termo aditivo, mediante proposta fundamentada e prévia manifestação técnica e jurídica.']);
  cl('Oitava','Da contrapartida',[
    '[ Quando exigida ] A contrapartida da OSC será prestada na forma do Plano de Trabalho, observado o art. 35, § 1º, da Lei nº 13.019/2014.']);
  cl('Nona','Do monitoramento, da avaliação e do gestor da parceria',[
    'A execução será acompanhada pelo gestor da parceria e pela comissão de monitoramento e avaliação, com base nos indicadores do Plano de Trabalho, podendo haver visita in loco e relatório técnico de monitoramento, nos termos dos arts. 58 a 62.']);
  cl('Décima','Da prestação de contas',[
    'A prestação de contas observará os arts. 63 a 72 da Lei nº 13.019/2014, priorizado o controle de resultados, com apresentação de relatório de execução do objeto e, quando exigido, de relatório de execução financeira.']);
  cl('Décima Primeira','Dos bens remanescentes',[
    'Os bens eventualmente adquiridos, produzidos ou transformados com recursos da parceria terão sua destinação definida na forma do art. 36 da Lei nº 13.019/2014 e do Plano de Trabalho.']);
  cl('Décima Segunda','Da proteção de dados pessoais (LGPD)',[
    'As partes observarão a Lei nº 13.709/2018 no tratamento de dados pessoais sensíveis de saúde, com base legal, finalidade específica, segurança da informação e encarregado indicado, vedado uso diverso do objeto.']);
  cl('Décima Terceira','Das sanções',[
    'Pela execução da parceria em desacordo com o Plano de Trabalho e com as normas aplicáveis, a Administração poderá aplicar as sanções do art. 73 da Lei nº 13.019/2014 (advertência, suspensão temporária e declaração de inidoneidade), assegurados o contraditório e a ampla defesa.']);
  cl('Décima Quarta','Da denúncia e da rescisão',[
    'O Termo poderá ser denunciado a qualquer tempo, com as responsabilidades das partes relativas ao período de vigência, e rescindido por descumprimento, mediante notificação prévia, nos termos do art. 42, XVI, da Lei nº 13.019/2014.']);
  cl('Décima Quinta','Da publicidade',[
    'A eficácia deste Termo fica condicionada à publicação do respectivo extrato no meio oficial de publicidade da Administração Pública, nos termos do art. 38 da Lei nº 13.019/2014.']);
  cl('Décima Sexta','Do foro',[
    'Fica eleito o foro da Comarca de '+x.alvo+' para dirimir as questões oriundas deste Termo, com renúncia a qualquer outro, por mais privilegiado que seja. E, por estarem de acordo, firmam o presente em 2 (duas) vias de igual teor e forma.']);
  w.sign([
    [x.orgao,'Administração Pública'],
    ['[ INSTITUTO ] — Organização da Sociedade Civil','Representante legal'],
  ]);
  w.gap(6); w.p('Testemunhas: 1) ______________________________   2) ______________________________');
  return w.done('Termo de Colaboração (MROSC) — Colo do útero DNA-HPV — '+x.alvo);
}

function genTermoReferencia(doc,c){
  const x=_ctx(c), w=_ed(doc);
  w.title([
    {t:'[ BRASÃO / TIMBRE DO MUNICÍPIO ]',b:false,s:10},
    {t:x.orgao.toUpperCase(),s:12},
    {t:'TERMO DE REFERÊNCIA',s:13},
    {t:'CREDENCIAMENTO PARA RASTREAMENTO DO CÂNCER DO COLO DO ÚTERO POR TESTE MOLECULAR DNA-HPV COM AUTOCOLETA — LEI Nº 14.133/2021',s:11},
  ]);
  w.p(_DISC);
  w.h1('1. Do objeto');
  w.p('1.1. Contratação, por credenciamento (art. 79 da Lei nº 14.133/2021), de pessoa(s) jurídica(s) para a execução de ação concentrada e itinerante (mutirão) de rastreamento organizado do câncer do colo do útero por teste molecular DNA-HPV com autocoleta vaginal, compreendendo o fornecimento do kit, a análise laboratorial com genotipagem, a logística, o laudo digital e a plataforma de seguimento, integrada à Atenção Primária do Município, sem cobrança direta ou indireta à usuária.');
  w.p('1.2. O procedimento corresponde ao código SIGTAP 0202100251 (exame molecular de detecção de HPV), tecnologia incorporada ao SUS pela Portaria SECTICS/MS nº 3/2024.');
  w.h1('2. Da fundamentação e da justificativa do credenciamento');
  w.p('2.1. A necessidade está demonstrada no Estudo Técnico Preliminar (ETP): cobertura estimada de '+(c.covA*100).toFixed(0)+'% em '+x.alvo+', inferior à meta de 70%, com concentração da não-cobertura nas mulheres de maior vulnerabilidade, que o modelo oportunístico não alcança.');
  w.p('2.2. Adota-se o credenciamento porque o interesse público é mais bem atendido pela contratação simultânea de todos os interessados aptos (art. 79, I e II), com preços fixados pela Administração — hipótese de inviabilidade de competição e inexigibilidade de licitação (art. 74, IV). A seleção não se dá por disputa de preço, mas pela habilitação ao atendimento de parâmetros objetivos de qualidade.');
  w.h1('3. Da descrição da solução como um todo');
  w.p('3.1. A solução é integrada e indissociável (kit, exame molecular, logística, laudo e seguimento), de modo a preservar a cadeia de custódia, a responsabilidade técnica do laudo e a rastreabilidade do seguimento, mantida a segregação de funções em relação aos atos especializados, que permanecem na rede pública.');
  w.h1('4. Dos requisitos técnicos, sanitários e assistenciais');
  w.al([
    'Kit de autocoleta vaginal com registro ativo na ANVISA e validade não inferior a 12 meses na entrega;',
    'Exame de biologia molecular com genotipagem de, no mínimo, 28 tipos de HPV, identificados individualmente ao menos os tipos 16 e 18;',
    'Laboratório com inscrição regular no SCNES/CNES, licença sanitária vigente para diagnóstico molecular e responsável técnico habilitado;',
    'Liberação do laudo em até 48 horas do recebimento da amostra, com controle interno de amplificação por amostra;',
    'Logística de recolhimento e transporte do material biológico, com cadeia de custódia;',
    'Plataforma digital para cadastro, rastreabilidade, laudo digital, alerta de resultado alterado e seguimento por até 5 anos, em conformidade integral à LGPD (Lei nº 13.709/2018);',
    'Atendimento gratuito, humanizado e sem discriminação, vedada cobrança direta ou indireta à usuária, submetido à regulação do acesso pela Secretaria;',
    'Plano de Gerenciamento de Resíduos de Serviços de Saúde (PGRSS), nos termos da RDC ANVISA nº 222/2018.',
  ]);
  w.h2('4.1. Natureza do serviço e segregação de funções');
  w.p('4.1.1. A operação de campo (autocoleta pela própria usuária, apoiada por ACS e enfermagem) é de natureza comum e não constitui ato médico; o processamento laboratorial é atividade técnica especializada sob responsabilidade técnica própria. Os atos médicos especializados (colposcopia, biópsia, EZT e tratamento) não integram o objeto e permanecem na rede pública.');
  w.h1('5. Do modelo de execução do objeto');
  w.p('5.1. A demanda será distribuída entre as credenciadas por critério objetivo e impessoal (p.ex. rodízio ou rateio por capacidade declarada e por território), vedada a preferência injustificada. A Secretaria exerce a regulação do acesso, assegura o seguimento (colposcopia/EZT) pactuado em CIR/PPI antes do início e integra a ação à Atenção Primária.');
  w.h1('6. Do modelo de gestão do contrato');
  w.p('6.1. A execução será acompanhada por fiscal e gestor designados (arts. 117 e seguintes), com recebimento provisório e definitivo mediante conferência dos laudos liberados e do registro no SISCAN, e com registro da produção em BPA-I.');
  w.h1('7. Dos critérios de medição e pagamento');
  w.p('7.1. A medição será por teste efetivamente realizado e com laudo liberado, ao preço unitário fixado pela Administração, mediante relatório de produção e comprovação do registro no SISCAN; não se remunera amostra sem laudo válido.');
  w.h1('8. Da estimativa de preço e da forma de fixação');
  w.p('8.1. O preço unitário será fixado pela Administração e ancorado em pesquisa de mercado (IN SEGES/ME nº 65/2021 — mínimo de três fontes, atualizada em até seis meses). Referência do ciclo: '+fmt(x.testes)+' testes.');
  w.tbl(['Item','Quantidade de referência','Preço unitário (fixado)','Valor de referência'],[
    ['Teste DNA-HPV com autocoleta (SIGTAP 0202100251)',fmt(x.testes),fmtMoney(x.preco),fmtMoney(x.receita)],
  ],{0:{cellWidth:230}});
  w.p('8.2. A estratificação de custos, quando apresentada, é demonstração de exequibilidade (memória de cálculo) e não parâmetro do preço; o único parâmetro de aceitabilidade é a compatibilidade com o preço de mercado (arts. 11 e 23 da Lei nº 14.133/2021).');
  w.h1('9. Das obrigações das partes');
  w.al([
    'Da credenciada: executar o objeto conforme os requisitos; manter a regularidade jurídica, fiscal, trabalhista e sanitária durante toda a vigência; observar a LGPD; não cobrar das usuárias;',
    'Da Administração: fixar e publicar os preços; distribuir as demandas de forma impessoal; regular o acesso; assegurar o seguimento na rede; fiscalizar e pagar pela produção medida.',
  ]);
  w.h1('10. Da proteção de dados pessoais (LGPD)');
  w.p('10.1. O tratamento de dados pessoais sensíveis de saúde observará a Lei nº 13.709/2018, com base legal e finalidade específicas, segurança da informação, controle de acesso por perfil, registro de logs e encarregado indicado, vedado uso diverso do objeto.');
  w.h1('11. Das sanções');
  w.p('11.1. O descumprimento sujeita a credenciada às sanções dos arts. 155 e seguintes da Lei nº 14.133/2021, assegurados o contraditório e a ampla defesa.');
  w.sign([
    ['[ NOME / MATRÍCULA / CARGO ]','Responsável técnico pela elaboração'],
    ['Autoridade competente — '+x.orgao,''],
  ]);
  return w.done('Termo de Referência (credenciamento) — Colo do útero DNA-HPV — '+x.alvo);
}

function genEditalCredenciamento(doc,c){
  const x=_ctx(c), w=_ed(doc);
  w.title([
    {t:'[ BRASÃO / TIMBRE DO MUNICÍPIO ]',b:false,s:10},
    {t:x.orgao.toUpperCase(),s:12},
    {t:'EDITAL DE CHAMAMENTO PÚBLICO PARA CREDENCIAMENTO Nº [ ___ / ______ ]',s:13},
    {t:'LEI Nº 14.133/2021 (ARTS. 79 E 74, IV) — RASTREAMENTO DO CÂNCER DO COLO DO ÚTERO POR DNA-HPV COM AUTOCOLETA',s:11},
  ]);
  w.p(_DISC);
  w.h1('1. Do objeto e da modalidade');
  w.p('1.1. A '+x.orgao+' torna público o chamamento permanente para o CREDENCIAMENTO de pessoas jurídicas interessadas em executar ação de rastreamento do câncer do colo do útero por teste molecular DNA-HPV com autocoleta, nos termos do Termo de Referência anexo, do art. 79 e da hipótese de inexigibilidade do art. 74, IV, da Lei nº 14.133/2021.');
  w.p('1.2. O credenciamento não gera obrigação de contratação ou de demanda mínima; as contratações decorrentes observarão a necessidade da Administração e a disponibilidade orçamentária, à fonte '+x.fonte+'.');
  w.h1('2. Das condições de participação');
  w.p('2.1. Poderá se credenciar qualquer pessoa jurídica cujo objeto social seja compatível e que atenda, cumulativamente, aos requisitos de habilitação e aos requisitos técnicos e sanitários deste edital e de seu Termo de Referência, aceitando os preços fixados pela Administração.');
  w.p('2.2. O chamamento é permanente: os pedidos de credenciamento podem ser apresentados a qualquer tempo durante a vigência e serão analisados por ordem de protocolo.');
  w.h1('3. Da documentação de habilitação');
  w.al([
    'Habilitação jurídica: ato constitutivo e representação legal;',
    'Regularidade fiscal, trabalhista e com o FGTS (certidões vigentes);',
    'Qualificação técnica: laboratório com inscrição regular no SCNES/CNES, licença sanitária para diagnóstico molecular e responsável técnico habilitado;',
    'Registro ANVISA do kit e do método; comprovação de capacidade de laudo em até 48 horas;',
    'Declaração de conformidade à LGPD e de não cobrança às usuárias;',
    'Declarações exigidas em lei (inexistência de fato impeditivo, trabalho de menor, etc.).',
  ]);
  w.h1('4. Dos requisitos técnicos do serviço');
  w.p('4.1. Observar-se-ão integralmente os requisitos técnicos, sanitários e assistenciais definidos no Termo de Referência (kit ANVISA; genotipagem mínima de 28 tipos com identificação de 16/18; laudo em 48h; logística com cadeia de custódia; plataforma de seguimento em conformidade com a LGPD; PGRSS).');
  w.h1('5. Da tabela de preços fixada pela Administração');
  w.p('5.1. Os valores são fixados pela Administração, ancorados em pesquisa de mercado (IN SEGES/ME nº 65/2021), e são idênticos para todas as credenciadas, afastando a disputa por preço (inviabilidade de competição):');
  w.tbl(['Serviço','Preço unitário fixado','Referência do ciclo'],[
    ['Teste DNA-HPV com autocoleta (SIGTAP 0202100251)',fmtMoney(x.preco),fmt(x.testes)+' testes = '+fmtMoney(x.receita)],
  ],{0:{cellWidth:230}});
  w.h1('6. Do credenciamento e da distribuição impessoal das demandas');
  w.p('6.1. Deferido o credenciamento, firma-se o termo de credenciamento. A distribuição das demandas entre as credenciadas observará critério objetivo e impessoal (rodízio ou rateio por capacidade e por território), publicado e auditável, vedada preferência injustificada.');
  w.h1('7. Das obrigações da credenciada');
  w.al([
    'Executar o objeto conforme o Termo de Referência, com gratuidade e sob a regulação do acesso da Secretaria;',
    'Registrar a produção no SISCAN e em BPA-I; manter a cadeia de custódia e a responsabilidade técnica do laudo;',
    'Manter, durante toda a vigência, as condições de habilitação e os requisitos técnicos e sanitários;',
    'Observar a LGPD e a segregação de funções (os atos médicos especializados permanecem na rede pública).',
  ]);
  w.h1('8. Da vigência e do descredenciamento');
  w.p('8.1. O credenciamento vigora por [ 12 meses ], prorrogável na forma da lei. O descredenciamento ocorrerá a pedido ou por descumprimento, mediante processo com contraditório e ampla defesa.');
  w.h1('9. Da fiscalização, da medição e do pagamento');
  w.p('9.1. A execução será fiscalizada por gestor e fiscal designados; o pagamento observará a produção medida — teste realizado e com laudo liberado, ao preço fixado —, comprovado o registro no SISCAN.');
  w.h1('10. Da proteção de dados (LGPD) e das sanções');
  w.p('10.1. O tratamento de dados sensíveis de saúde observará a Lei nº 13.709/2018. O descumprimento sujeita a credenciada às sanções dos arts. 155 e seguintes da Lei nº 14.133/2021, assegurada a ampla defesa.');
  w.sign([
    ['Autoridade competente — '+x.orgao,'Ordenador(a) de despesa'],
    ['[ NOME / MATRÍCULA / CARGO ]','Pregoeiro(a) / Comissão de Contratação'],
  ]);
  return w.done('Edital de credenciamento — Colo do útero DNA-HPV — '+x.alvo);
}
function _reqCalc(){ if(!lastCalc){ alert('Selecione um município ou estado primeiro.'); return false;} return true; }
function baixarPropTec(){ if(!_reqCalc())return; const {jsPDF}=window.jspdf; const d=new jsPDF({unit:'pt',format:'a4'});
  genPropostaTecnica(d,lastCalc,false); d.save('Proposta_Tecnica_PinkPapa_'+lastCalc.muni[0].replace(/[^\w]/g,'_')+'.pdf'); }
function baixarNotaTec(){ if(!_reqCalc())return; const {jsPDF}=window.jspdf; const d=new jsPDF({unit:'pt',format:'a4'});
  genNotaTecnica(d,lastCalc,false); d.save('Nota_Tecnica_PinkPapa_'+lastCalc.muni[0].replace(/[^\w]/g,'_')+'.pdf'); }
function baixarPacote(){ const r=montarPDF(); if(!r) return;
  genPropostaTecnica(r.doc,lastCalc,true); genNotaTecnica(r.doc,lastCalc,true);
  r.doc.save('Pacote_PinkPapa_'+lastCalc.muni[0].replace(/[^\w]/g,'_')+'.pdf'); }
function _mun(){return lastCalc.muni[0].replace(/[^\w]/g,'_');}
function baixarETP(){ if(!_reqCalc())return; const {jsPDF}=window.jspdf; const d=new jsPDF({unit:'pt',format:'a4'});
  genETP(d,lastCalc,false); d.save('ETP_PinkPapa_'+_mun()+'.pdf'); }
// peças por rota: [0]=instrumento (Termo de Colaboração | Edital de credenciamento); [1]=peça (Plano | Termo de Referência)
const _GEN={termo:[genTermoColaboracao,'TermoColaboracao_MROSC_'],edital:[genEditalCredenciamento,'Edital_Credenciamento_'],
  plano:[genPlanoTrabalho,'PlanoDeTrabalho_MROSC_'],tr:[genTermoReferencia,'TermoReferencia_']};
function _baixaRota(i){ if(!_reqCalc())return; const k=instrSel().pecas[i][0],[gen,pre]=_GEN[k];
  const {jsPDF}=window.jspdf; const d=new jsPDF({unit:'pt',format:'a4'}); gen(d,lastCalc); d.save(pre+_mun()+'.pdf'); }
function baixarInstrumento(){ _baixaRota(0); }
function baixarPeca(){ _baixaRota(1); }

/* ---------- envio de e-mail DIRETO (Apps Script + MailApp) ---------- */
async function enviarEmail(){
  const r=montarPDF(); if(!r) return;
  const email=document.getElementById('in-dest-email').value.trim();
  const btn=document.getElementById('btnMail'), st=document.getElementById('mailStatus');
  if(!email){ st.style.color='#C81E5B'; st.textContent='Informe o e-mail do destinatário.'; return; }
  const assunto='Proposta PinkPapa — rastreio de câncer de colo do útero ('+r.alvo+')';
  const corpo='Prezado(a) '+(document.getElementById('in-dest-nome').value.trim()||'Gestor(a)')+',\n\n'+
    'Segue em anexo a proposta técnica e comercial do PinkPapa — programa de rastreio de câncer de colo do útero por teste de DNA-HPV com autocoleta — para '+r.alvo+'.\n\n'+
    'Valor total do projeto: '+fmtMoney(lastCalc.custoPrograma)+' ('+fmt(lastCalc.testes)+' testes).\n'+
    'Referência: '+r.ref+'\n\n'+
    'Permaneço à disposição.\n\n'+
    (document.getElementById('in-prop-nome').value.trim()||'PinkPapa · PinkLab')+'\nExecutante técnico\n'+
    document.getElementById('in-prop-email').value.trim()+'\n'+document.getElementById('in-prop-tel').value.trim();

  if(!MAIL_ENDPOINT){
    // sem backend: baixa o PDF e abre o compositor JÁ preenchido (sem menu de escolha)
    r.doc.save(nomeArq());
    st.style.color='#7C1D4F';
    st.textContent='Abrindo seu e-mail… anexe o PDF que acabou de baixar.';
    location.href='mailto:'+email+'?subject='+encodeURIComponent(assunto)+'&body='+encodeURIComponent(corpo+'\n\n(Anexe o PDF baixado: '+nomeArq()+')');
    return;
  }
  // com backend: envia de verdade, com anexo, sem sair da página
  btn.disabled=true; st.style.color='#7C1D4F'; st.textContent='Enviando…';
  try{
    const b64 = r.doc.output('datauristring').split(',')[1];
    await fetch(MAIL_ENDPOINT,{method:'POST',mode:'no-cors',
      headers:{'Content-Type':'text/plain;charset=utf-8'},
      body:JSON.stringify({action:'enviarProposta',token:MAIL_TOKEN,para:email,assunto,corpo,
        nomeArquivo:nomeArq(),pdfBase64:b64,ref:r.ref,alvo:r.alvo,
        valor:lastCalc.custoPrograma,copia:document.getElementById('in-prop-email').value.trim()})});
    st.style.color='#12A97A'; st.textContent='✅ Proposta enviada para '+email;
  }catch(e){
    st.style.color='#C81E5B'; st.textContent='Falha no envio. Baixando o PDF…'; r.doc.save(nomeArq());
  }finally{ btn.disabled=false; }
}

initUF(); renderRank();
document.getElementById('mailNote').textContent = MAIL_ENDPOINT
  ? 'O e-mail é enviado diretamente pelo servidor, com o PDF em anexo.'
  : 'Envio direto com anexo requer o Apps Script configurado (mail_endpoint.txt). Sem ele, o PDF é baixado e seu cliente de e-mail abre já preenchido.';
</script>
</body>
</html>
"""

out = (HTML.replace("__TOTM__", TOTM_BR).replace("__BUILD__", BUILD)
       .replace("__DATA__", DATA_JS).replace("__UFSTATS__", UFSTATS_JS)
       .replace("__PATE__", PATE_JS).replace("__PATEUF__", PATEUF_JS).replace("__PATECOMP__", PATE_COMP)
       .replace("__COB__", COB_JS).replace("__COBUF__", COBUF_JS)
       .replace("__MAIL_ENDPOINT__", MAIL_ENDPOINT).replace("__MAIL_TOKEN__", MAIL_TOKEN)
       .replace("__CHART__", CHART).replace("__JSPDF__", JSPDF).replace("__AUTOTABLE__", AUTOTABLE))

(BASE/"index.html").write_text(out, encoding="utf-8")
(BASE/".nojekyll").write_text("", encoding="utf-8")
print(f"OK: index.html ({len(out)//1024} KB) build {BUILD}")
print(f"Mail endpoint: {'CONFIGURADO' if MAIL_ENDPOINT else 'nao configurado (fallback mailto)'}")
print(f"Brasil 25-64: {TOT_M:,} | {len(muns)} municipios | {len(uf_stats)} UFs")
