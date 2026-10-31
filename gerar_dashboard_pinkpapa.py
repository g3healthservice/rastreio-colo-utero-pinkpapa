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
        <div class="fld" style="max-width:320px"><label>Instrumento jurídico (documentação correlata)</label>
          <select id="in-instrumento" onchange="calc()">
            <option value="CONTRATO">Contrato administrativo — Lei 14.133/2021</option>
            <option value="CREDENCIAMENTO">Credenciamento / inexigibilidade — Lei 14.133/2021</option>
            <option value="MROSC">Parceria com OSC (MROSC) — Lei 13.019/2014</option>
          </select></div>
      </div>
      <div class="selrow" style="margin-top:8px">
        <div class="fld"><label>Executante / proponente</label><input type="text" id="in-prop-nome" value="PinkPapa · PinkLab"></div>
        <div class="fld"><label>Contato — e-mail (opcional)</label><input type="text" id="in-prop-email" placeholder="contato@pinkpapa.com.br"></div>
        <div class="fld" style="max-width:200px"><label>Contato — telefone (opcional)</label><input type="text" id="in-prop-tel" placeholder=""></div>
      </div>
      <div class="btnrow">
        <button class="btn" onclick="baixarPacote()">📦 Baixar pacote completo (proposta + proposta técnica + nota técnica)</button>
        <button class="btn sec" onclick="baixarPDF()">📄 Só a proposta (PNSB)</button>
        <button class="btn sec" onclick="baixarPropTec()">📑 Só a proposta técnica</button>
        <button class="btn sec" onclick="baixarNotaTec()">🧾 Só a nota técnica</button>
        <button class="btn sec" id="btnMail" onclick="enviarEmail()">✉️ Enviar proposta por e-mail</button>
        <span id="mailStatus"></span>
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
  CONTRATO:{label:'Contrato administrativo (Lei nº 14.133/2021)',
    base:'Contratação por contrato administrativo, com Estudo Técnico Preliminar (ETP), Termo de Referência (TR) e pesquisa de preços (IN SEGES/ME nº 65/2021).',
    docs:['Estudo Técnico Preliminar (ETP)','Termo de Referência (TR)','Pesquisa de preços — mín. 3 fontes (IN SEGES/ME nº 65/2021)','Dotação orçamentária e autorização da despesa','Habilitação jurídica, fiscal, técnica e econômico-financeira','Minuta de contrato','Plano de trabalho e cronograma físico-financeiro']},
  CREDENCIAMENTO:{label:'Credenciamento / inexigibilidade (arts. 79 e 74, IV, da Lei nº 14.133/2021)',
    base:'Credenciamento por chamamento público, com justificativa da inviabilidade de competição e preços fixados pela Administração.',
    docs:['Edital de chamamento público para credenciamento','Justificativa da inviabilidade de competição','Tabela de preços fixada pela Administração','Requisitos técnicos de habilitação dos credenciados','Pesquisa/tabela de referência de preços','Termo de credenciamento e plano de trabalho']},
  MROSC:{label:'Parceria com OSC — MROSC (Lei nº 13.019/2014)',
    base:'Parceria com Organização da Sociedade Civil por Termo de Fomento, Termo de Colaboração ou Acordo de Cooperação, precedida de chamamento público (arts. 30–31), com Plano de Trabalho (art. 22) e prestação de contas (arts. 63–72).',
    docs:['Chamamento público (edital) ou justificativa de dispensa/inexigibilidade (arts. 30–31)','Plano de Trabalho (art. 22): metas, cronograma e memória de cálculo','Comprovação da OSC: CNPJ, estatuto e objeto social compatível','Certidões de regularidade (fiscal, trabalhista, FGTS) e consulta CEPIM/CADIN','Declarações dos arts. 33 e 34 (capacidade técnica e operacional)','Designação do gestor da parceria e da comissão de monitoramento e avaliação','Conta bancária específica e movimentação eletrônica dos recursos','Prestação de contas e relatório de execução do objeto (arts. 63–72)']},
};
function instrSel(){const el=document.getElementById('in-instrumento');const k=el?el.value:'CONTRATO';return Object.assign({key:k},INSTRUMENTOS[k]||INSTRUMENTOS.CONTRATO);}
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
  renderPate();
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
    doc.setTextColor(255);doc.setFont('helvetica','bold');doc.setFontSize(10);doc.text('G3 HEALTH SERVICE',M,16);
    doc.setFont('helvetica','normal');doc.setFontSize(7.5);
    doc.text('PinkPapa · rastreio de câncer de colo do útero por DNA-HPV (autocoleta)',W-M,16,{align:'right'});
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
      doc.text('G3 Health Service · '+pMail+(pTel?' · '+pTel:''),M,H-28);
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
  gradiente(0,0,W,H,[230,0,126],[36,12,26]);
  // grid decorativo
  doc.setDrawColor(255,255,255);doc.setLineWidth(0.3);
  for(let i=1;i<7;i++){doc.setGState(new doc.GState({opacity:0.07}));doc.line(0,H*i/7,W,H*i/7);doc.line(W*i/7,0,W*i/7,H);}
  doc.setGState(new doc.GState({opacity:1}));doc.setLineWidth(1);

  doc.setTextColor(255);doc.setFont('helvetica','bold');doc.setFontSize(11);
  doc.text('G3 HEALTH SERVICE',M,64);
  doc.setFont('helvetica','normal');doc.setFontSize(8.5);doc.setTextColor(255,220,238);
  doc.text('em parceria com PinkLab · PinkPapa',M,78);

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
      ['1. Planejamento','Pactuação com a Secretaria, definição das unidades de coleta (UBS/UPA/centros comunitários), meta por unidade e cadastro no SISCAN.','Mês 1','G3 + Secretaria'],
      ['2. Capacitação','Treinamento das equipes da Atenção Primária (ACS/enfermagem) para orientar a autocoleta e registrar o procedimento SIGTAP 0202100251.','Mês 1–2','G3 / PinkLab'],
      ['3. Convocação','Busca ativa das mulheres de 25 a 64 anos, priorizando as que nunca se rastrearam; campanha local e agendamento.','Mês 2 em diante','Secretaria + ACS'],
      ['4. Autocoleta','Entrega e retirada do coletor; a mulher realiza a autocoleta sem espéculo e sem constrangimento. Sem necessidade de mesa ginecológica.','Contínuo','Unidades de saúde'],
      ['5. Análise laboratorial','Processamento por PCR com genotipagem (28 tipos de HPV, 19 de alto risco) e emissão de laudo.','Contínuo','PinkLab'],
      ['6. Encaminhamento','Mulheres HPV+ de alto risco encaminhadas à colposcopia/tratamento da lesão precursora (CAF/EZT), fechando a linha de cuidado.','Contínuo','Secretaria'],
      ['7. Monitoramento por IA','Acompanhamento por inteligência artificial por até 5 anos, com painel de cobertura e indicadores (Previne Brasil / metas 90-70-90).','5 anos','G3 + PinkLab'],
    ],
    theme:'grid',headStyles:{fillColor:C_PINK,fontSize:9},styles:{fontSize:8.4,cellPadding:5,lineColor:[240,215,230]},
    columnStyles:{0:{cellWidth:80,fontStyle:'bold',textColor:C_WINE},2:{cellWidth:66},3:{cellWidth:88}},margin:{left:M,right:M}});
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
  gradiente(M,y,W-2*M,76,[230,0,126],[124,29,79]);
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
  y=doc.lastAutoTable.finalY+30;

  if(y>H-120) { doc.addPage(); y=header('Aceite'); y+=10; }
  doc.setDrawColor(190,170,182);
  doc.line(M,y+26,M+210,y+26);doc.line(W-M-210,y+26,W-M,y+26);
  doc.setFontSize(9);doc.setTextColor(60);
  doc.setFont('helvetica','bold');doc.text('G3 Health Service',M,y+40);
  doc.setFont('helvetica','normal');doc.setFontSize(8);doc.setTextColor(120);
  doc.text(pNome+(pTel?' · '+pTel:''),M,y+52);
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
  box.innerHTML = `
  <div style="border:1px solid #f3cfe3;border-radius:12px;overflow:hidden">
    <div style="background:linear-gradient(90deg,var(--wine),var(--pink));color:#fff;padding:10px 14px;font-weight:700;font-size:13.5px">
      🏛️ Viabilidade orçamentária — Programa Agora Tem Especialistas (SUS 360)
      <span style="font-weight:400;font-size:11px;opacity:.92"> · ${PATE_COMP}</span></div>
    <div style="padding:8px 14px;background:${cor}14;border-bottom:1px solid #f3cfe3;color:${cor};font-weight:700;font-size:13px">${tag}</div>
    <table style="width:100%;border-collapse:collapse;font-size:12.5px">
      ${linha('Recursos antecipados ao fundo', brl(rep), 'parcela única + emendas já transferidas ao fundo de saúde')}
      ${linha('Produção aprovada (SIA/SIH)', brl(prod)+' · '+pct.toFixed(0)+'%', 'quanto já foi executado e comprovado')}
      ${linha('Saldo a comprovar com produção', brl(saldo), 'NÃO é caixa — é recurso cuja contrapartida (serviço prestado) ainda falta entregar')}
      ${linha('Componente ambulatorial (OCI)', brl(repAmb)+' → '+brl(prodAmb), 'é aqui que entra o seguimento das mulheres HPV+')}
      ${linha('Mutirão das Mulheres', brl(mm), mm>0?'o gestor já tem valor nesta rubrica (adesão comprovada)':'ainda sem valor — oportunidade de enquadramento')}
    </table>
    <div style="padding:10px 14px;background:#fff0f7;font-size:12px;color:var(--wine);line-height:1.55">
      <b>Como usar (sequência):</b> 1) o rastreio por DNA-HPV é pago por <b>MAC</b> (SIGTAP 0202100251); 2) os positivos geram <b>seguimento</b> (colposcopia, biópsia, EZT) = <b>produção ambulatorial OCI</b>; 3) essa produção <b>consome o saldo acima</b> e cumpre o encontro de contas do PATE (NT 33/2026); 4) pode ser contabilizada no <b>Mutirão das Mulheres</b>. Em resumo: o mutirão PinkPapa é o meio de ${ente} executar recurso federal já antecipado — evitando a glosa por não-produção.
    </div>
  </div>`;
}
function baixarPDF(){const r=montarPDF();if(r) r.doc.save(nomeArq());}

/* ===== documentos técnicos (proposta técnica + nota técnica) em PDF ===== */
function _tec(doc,titulo,alvo){
  const W=doc.internal.pageSize.getWidth(),H=doc.internal.pageSize.getHeight(),M=44;
  let y, startPage;
  function band(){ doc.setFillColor(...C_PINK);doc.rect(0,0,W,6,'F');
    doc.setTextColor(...C_WINE);doc.setFont('helvetica','bold');doc.setFontSize(8.5);doc.text('PINKPAPA · PINKLAB',M,24);
    doc.setTextColor(...C_GREY);doc.setFont('helvetica','normal');doc.setFontSize(7.5);
    doc.text(doc.splitTextToSize(titulo+' — '+alvo,W/2-10),W-M,24,{align:'right'});
    doc.setDrawColor(240,215,230);doc.line(M,32,W-M,32); return 50; }
  function nl(){ doc.addPage(); y=band(); }
  function ensure(h){ if(y+h>H-34) nl(); }
  const api={
    begin(append){ if(append) doc.addPage(); startPage=doc.internal.getNumberOfPages(); y=band(); return api; },
    h1(t){ ensure(26); doc.setFont('helvetica','bold');doc.setFontSize(11.5);doc.setTextColor(...C_WINE);doc.text(t,M,y+12); y+=23; return api; },
    p(t){ doc.setFont('helvetica','normal');doc.setFontSize(9.3);doc.setTextColor(40,28,38);
      const L=doc.splitTextToSize(t,W-2*M); ensure(L.length*11.4+6); doc.text(L,M,y+9); y+=L.length*11.4+7; return api; },
    li(t){ doc.setFont('helvetica','normal');doc.setFontSize(9.3);doc.setTextColor(40,28,38);
      const L=doc.splitTextToSize(t,W-2*M-14); ensure(L.length*11.4+4);
      doc.setTextColor(...C_PINK);doc.text('•',M+3,y+9);doc.setTextColor(40,28,38);doc.text(L,M+15,y+9); y+=L.length*11.4+5; return api; },
    tbl(head,body,cw){ ensure(42);
      doc.autoTable({startY:y,head:[head],body:body,margin:{left:M,right:M,top:40},theme:'grid',
        headStyles:{fillColor:C_PINK,fontSize:8.3,textColor:255},styles:{fontSize:8,cellPadding:4,lineColor:[240,215,230],overflow:'linebreak'},
        columnStyles:cw||{},didDrawPage:function(){ if(doc.internal.getCurrentPageInfo().pageNumber>startPage){ doc.setFillColor(...C_PINK);doc.rect(0,0,W,6,'F'); } }});
      y=doc.lastAutoTable.finalY+12; return api; },
    sign(contratante){ ensure(96); y+=22;
      doc.setDrawColor(120,110,116); doc.line(M,y,M+210,y); doc.line(W-M-210,y,W-M,y);
      doc.setFont('helvetica','normal');doc.setFontSize(8.6);doc.setTextColor(60,50,56);
      doc.text(doc.splitTextToSize(contratante,210),M,y+12); doc.text('Contratante',M,y+12+2+ (doc.splitTextToSize(contratante,210).length*10));
      doc.text('PinkPapa / PinkLab',W-M-210,y+12); doc.text('Executante técnico',W-M-210,y+24);
      y+=46; doc.text('Local e data: ____________________________________, ______ de __________________ de 2026.',M,y); return api; },
    footer(){ const n=doc.internal.getNumberOfPages();
      for(let i=startPage;i<=n;i++){ doc.setPage(i);
        doc.setFont('helvetica','normal');doc.setFontSize(7.5);doc.setTextColor(...C_GREY);
        doc.text('PinkPapa · PinkLab — rastreio por DNA-HPV (autocoleta) · documento de apoio à decisão',M,H-22);
        doc.text('p. '+(i-startPage+1),W-M,H-22,{align:'right'}); } return api; }
  };
  return api;
}
function _ctx(c){
  const m=c.muni, alvo=m[4]?m[0]:m[0]+'/'+m[1];
  const orgao=m[4]?(typeof UF_STATS!=='undefined'&&UF_STATS[m[1]]?UF_STATS[m[1]].orgao:('Secretaria de Saúde — '+m[0])):('Secretaria Municipal de Saúde de '+m[0]+'/'+m[1]);
  const pop=m[3], testes=Math.round(c.testes), conv=Math.round(c.adicionais), preco=c.preco;
  return {m,alvo,orgao,pop,testes,conv,preco,
    hpv:Math.round(c.hpvPos),les:Math.round(c.lesoes),lesC:Math.round(c.lesoesCitoPerde),casos:Math.round(c.casosEvit),
    cito:Math.round(testes*0.0926),colp:Math.round(testes*0.0618),biop:Math.round(testes*0.0433),ezt:Math.round(testes*0.0155),
    fonte:c.fonteLabel||'Média e Alta Complexidade (MAC)', instr:c.instr||INSTRUMENTOS.CONTRATO,
    receita:Math.round(c.custoPrograma)};
}
function genPropostaTecnica(doc,c,append){
  const x=_ctx(c), w=_tec(doc,'Proposta Técnica — Mutirão PinkPapa',x.alvo).begin(append);
  w.h1('Proposta Técnica e Comercial — Mutirão de rastreio (DNA-HPV)');
  w.tbl(['Campo','Conteúdo'],[
    ['Objeto','Aquisição de testes de DNA-HPV com autocoleta e execução de mutirão de rastreio, com linha de cuidado integrada à rede'],
    ['Município / Executor',x.orgao],
    ['Público-alvo',fmt(x.pop)+' mulheres de 25–64 anos (IBGE 2022)'],
    ['Dimensionamento','~'+fmt(x.conv)+' convocadas · '+fmt(x.testes)+' testes (adesão '+(c.ades*100).toFixed(0)+'%)'],
    ['Valor da contratação',fmtMoney(x.receita)+' — '+fmt(x.testes)+' kits × '+fmtMoney(x.preco)],
    ['Fonte de recurso',x.fonte],
    ['Instrumento jurídico',x.instr.label],
    ['Executante / proponente','PinkPapa / PinkLab — executante técnico'],
  ],{0:{cellWidth:120,fontStyle:'bold',textColor:C_WINE}});
  w.h1('1. Problema · Necessidade · Solução · Benefício');
  w.p('PROBLEMA. O câncer do colo do útero é o 3º mais frequente entre as brasileiras e quase 100% evitável por rastreio de qualidade; a citologia detecta apenas 55–70% das lesões de alto grau. Em '+x.alvo+' a cobertura estimada é de '+(c.covA*100).toFixed(0)+'%.');
  w.p('NECESSIDADE. Ampliar o rastreio com tecnologia de maior sensibilidade e garantir o seguimento das positivas. Um mutirão com busca ativa e autocoleta alcança as mulheres que nunca se rastrearam.');
  w.p('SOLUÇÃO. O PinkPapa é autoteste de DNA-HPV (ANVISA; SIGTAP 0202100251; Portaria SECTICS/MS nº 3/2024), custeável por '+x.fonte+'. Autocoleta sem espéculo, aceitação ~100%, sensibilidade 90–95%, rastreio a cada 5 anos após negativo, com monitoramento por IA.');
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
   '3. Teste DNA-HPV com genotipagem (16/18 + demais AR) — núcleo da ação; laudo em até 48h (PinkLab).',
   '4. Triagem reflexa — citologia reflexa nas HPV+, evitando encaminhar todo HPV+ à colposcopia.',
   '5. Laudo e devolutiva — resultado e registro; negativo reconvocado em 5 anos, com IA.',
   '6. Seguimento garantido — colposcopia e biópsia na rede (referência pactuada em CIR/PPI). Assegurar antes do início.',
   '7. Tratamento das lesões — EZT/CAF e conização na referência.',
   '8. Registro no SISCAN e indicadores — Previne Brasil e 90-70-90.',
   '9. Educação em saúde e comunicação — integra-se à vacinação de HPV.'].forEach(t=>w.li(t));
  w.h1('5. Investimento');
  w.tbl(['Componente','Qtd.','Unitário','Total','Fonte'],[
    ['Kit PinkPapa (DNA-HPV + genotipagem + laboratório + IA + capacitação)',fmt(x.testes),fmtMoney(x.preco),fmtMoney(x.receita),x.fonte],
    ['Seguimento (citologia reflexa, colposcopia, biópsia, EZT)','conf. desdobr.','tabela SUS','programado na rede','MAC/FAEC/OCI'],
  ],{0:{cellWidth:180}});
  w.h1('6. Governança e pontos de averiguação (TCU/MP)');
  ['Motivação e enquadramento legal expressos.','Pesquisa de preços (IN 65/2021) — a composição de custos não a substitui.',
   'Segregação de funções: rastreio pela contratada; diagnóstico e tratamento na rede pública.',
   'Fonte de financiamento clara e registro em SIA/SIH.','Rastreabilidade: SISCAN, cadeia de custódia e responsabilidade técnica do laudo.',
   'Conformidade com a LGPD (dado sensível de saúde).','Plano de trabalho e prestação de contas com metas auditáveis.',
   'Gestão de riscos, com a capacidade de seguimento assegurada antes do início.'].forEach(t=>w.li(t));
  w.h1('7. Documentação correlata — '+x.instr.label);
  x.instr.docs.forEach(t=>w.li(t));
  w.sign(x.orgao);
  w.footer();
  return doc;
}
function genNotaTecnica(doc,c,append){
  const x=_ctx(c), w=_tec(doc,'Nota Técnica — Mutirão PinkPapa',x.alvo).begin(append);
  // estratificação de custos (estimativa, base planilha de custeio)
  const kitLab=x.testes*200, log=x.testes*20, plat=30000, cap=30000, coord=40000;
  const sub=kitLab+log+plat+cap+coord, trib=Math.round(x.receita*0.12), custo=sub+trib, margem=x.receita-custo;
  const margemPct=x.receita>0?(margem/x.receita*100):0, unit=x.testes>0?custo/x.testes:0;
  w.h1('Nota Técnica — fundamentação e estratificação de custos');
  w.tbl(['Campo','Conteúdo'],[
    ['Assunto','Fundamentação técnica, legal e orçamentária de mutirão de rastreio por DNA-HPV'],
    ['Interessado',x.orgao],
    ['Instrumento jurídico',x.instr.label],
    ['Fonte de recurso',x.fonte],
    ['Elaboração','PinkPapa / PinkLab (apoio técnico) — a ratificar pela área técnica'],
  ],{0:{cellWidth:120,fontStyle:'bold',textColor:C_WINE}});
  w.h1('1. Fundamentação técnica');
  ['Câncer de colo do útero é quase 100% evitável por rastreio (INCA; OMS); DNA-HPV detecta 90–95% (citologia 55–70%) e é o teste primário recomendado pela OMS.',
   'Incorporado ao SUS (Portaria SECTICS/MS nº 3/2024), SIGTAP 0202100251.',
   'Autocoleta com aceitação ~100% alcança quem nunca se rastreou (cobertura atual '+(c.covA*100).toFixed(0)+'%).',
   'CONITEC projeta −30% de custo no longo prazo substituindo a citologia.'].forEach(t=>w.li(t));
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
  w.h1('5. Estratificação de custos — custo da operação e margem');
  w.p('Estimativa (a validar no regime tributário e na composição analítica), base: planilha de custeio de referência. Cenário: '+fmt(x.testes)+' testes × '+fmtMoney(x.preco)+'.');
  w.tbl(['Item','Base','Valor'],[
    ['(=) Receita contratada',fmt(x.testes)+' × '+fmtMoney(x.preco),fmtMoney(x.receita)],
    ['(−) Exame molecular + kit (laboratório)',fmt(x.testes)+' × R$ 200',fmtMoney(kitLab)],
    ['(−) Logística e laudo 48h',fmt(x.testes)+' × R$ 20',fmtMoney(log)],
    ['(−) Plataforma digital + IA','alocação do ciclo',fmtMoney(plat)],
    ['(−) Capacitação e suporte','1 evento',fmtMoney(cap)],
    ['(−) Coordenação e gestão','equipe, ~1 mês',fmtMoney(coord)],
    ['(=) Subtotal de custos diretos','',fmtMoney(sub)],
    ['(−) Tributos (estimativa ~12%)','a validar (regime)',fmtMoney(trib)],
    ['(=) Custo total estimado','',fmtMoney(custo)],
    ['(=) MARGEM OPERACIONAL','',fmtMoney(margem)+'  ('+margemPct.toFixed(1)+'%)'],
  ],{0:{cellWidth:230}});
  w.p('LEITURA. Margem operacional estimada de '+fmtMoney(margem)+' (~'+margemPct.toFixed(1)+'% da receita; custo unitário efetivo ~'+fmtMoney(unit)+' contra preço de '+fmtMoney(x.preco)+'). '+(margem<0?'No cenário atual a margem é negativa — os custos fixos (plataforma, capacitação, coordenação) não se diluem em um volume pequeno; recomenda-se rever preço/volume. ':'')+'A margem deve ser justificada na composição analítica apresentada ao controle.');
  w.p('ESCALA. Em volume maior (p.ex. 4.000 testes/ano) os custos fixos diluem-se e o custo integrado cai à ordem de R$ 250/exame — recomendando contratação por volume anual. Para mutirão isolado, ancorar o preço em pesquisa de mercado (IN 65/2021).');
  w.h1('6. Documentação correlata — '+x.instr.label);
  x.instr.docs.forEach(t=>w.li(t));
  w.h1('7. Conclusão');
  w.p('O mutirão por DNA-HPV é tecnicamente adequado, legalmente enquadrável e vantajoso frente à citologia e ao tratamento tardio. Recomenda-se: assegurar o seguimento; instruir a contratação com a documentação correlata acima; justificar o preço pela composição ou adotar patamar conservador; e registrar metas e indicadores auditáveis.');
  w.sign('Área Técnica — '+x.orgao);
  w.footer();
  return doc;
}
function _reqCalc(){ if(!lastCalc){ alert('Selecione um município ou estado primeiro.'); return false;} return true; }
function baixarPropTec(){ if(!_reqCalc())return; const {jsPDF}=window.jspdf; const d=new jsPDF({unit:'pt',format:'a4'});
  genPropostaTecnica(d,lastCalc,false); d.save('Proposta_Tecnica_PinkPapa_'+lastCalc.muni[0].replace(/[^\w]/g,'_')+'.pdf'); }
function baixarNotaTec(){ if(!_reqCalc())return; const {jsPDF}=window.jspdf; const d=new jsPDF({unit:'pt',format:'a4'});
  genNotaTecnica(d,lastCalc,false); d.save('Nota_Tecnica_PinkPapa_'+lastCalc.muni[0].replace(/[^\w]/g,'_')+'.pdf'); }
function baixarPacote(){ const r=montarPDF(); if(!r) return;
  genPropostaTecnica(r.doc,lastCalc,true); genNotaTecnica(r.doc,lastCalc,true);
  r.doc.save('Pacote_PinkPapa_'+lastCalc.muni[0].replace(/[^\w]/g,'_')+'.pdf'); }

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
