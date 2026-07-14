#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador do painel PinkPapa (G3 Health Service) — rastreio de cancer de colo do utero
por teste DNA-HPV com autocoleta (produto PinkPapa / PinkLab).
Mesmo padrao dos dashboards Rosalind/Linda: HTML self-contained, 5.570 municipios IBGE,
funil/ROI ao vivo, ranking, comparativo de custo, gerador de proposta PDF (PNSB).
Publica no GitHub Pages g3healthservice.
"""
import json, datetime, pathlib, re

BASE = pathlib.Path("/Users/gersongomes/pinkpapa")
DADOS = json.load(open(BASE/"dados/municipios_pinkpapa.json", encoding="utf-8"))
BUILD = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# ---- 27 capitais (nome exato IBGE) ----
CAPITAIS = {
 'AC':'Rio Branco','AL':'Maceió','AP':'Macapá','AM':'Manaus','BA':'Salvador','CE':'Fortaleza',
 'DF':'Brasília','ES':'Vitória','GO':'Goiânia','MA':'São Luís','MT':'Cuiabá','MS':'Campo Grande',
 'MG':'Belo Horizonte','PA':'Belém','PB':'João Pessoa','PR':'Curitiba','PE':'Recife','PI':'Teresina',
 'RJ':'Rio de Janeiro','RN':'Natal','RS':'Porto Alegre','RO':'Porto Velho','RR':'Boa Vista',
 'SC':'Florianópolis','SP':'São Paulo','SE':'Aracaju','TO':'Palmas'}

# ---- montar array compacto e stats por UF ----
muns = [[d['nome'], d['uf'], d['pop'] or 0, d['m2564'] or 0] for d in DADOS if d['m2564']]
muns.sort(key=lambda x:-x[3])
uf_stats = {}
for nome,uf,pop,m in muns:
    s = uf_stats.setdefault(uf, {'pop':0,'m':0,'capital':None})
    s['pop']+=pop; s['m']+=m
for nome,uf,pop,m in muns:
    if CAPITAIS.get(uf)==nome:
        uf_stats[uf]['capital']=[nome,uf,pop,m]
TOT_M = sum(x[3] for x in muns)
TOT_POP = sum(x[2] for x in muns)

DATA_JS = json.dumps(muns, ensure_ascii=False, separators=(',',':'))
UFSTATS_JS = json.dumps({k:{'pop':v['pop'],'m':v['m'],'capital':v['capital']} for k,v in uf_stats.items()}, ensure_ascii=False, separators=(',',':'))

# ---- libs vendorizadas (inline) ----
def vend(name):
    return open(BASE/"vendor"/name, encoding="utf-8").read().replace('</script','<\\/script')
CHART = vend("chart.umd.js")
JSPDF = vend("jspdf.umd.min.js")
AUTOTABLE = vend("jspdf.autotable.min.js")

TOTM_BR = f"{TOT_M:,}".replace(",",".")
PCTM_BR = f"{100*TOT_M/TOT_POP:.1f}".replace(".",",")

HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>PinkPapa · Painel de Rastreio de Câncer de Colo do Útero (DNA-HPV) — G3 Health Service</title>
<style>
:root{
  --pink:#E6007E; --pink2:#FF4DA6; --wine:#7C1D4F; --green:#12A97A; --red:#C81E5B;
  --ink:#2A1622; --muted:#7a6b73; --bg:#fff; --soft:#fff2f8; --line:#f1d9e6; --card:#fff;
}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.5}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
a{color:var(--pink)}
h1,h2,h3{margin:0}
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
.card .num.pink{color:var(--pink)} .card .num.green{color:var(--green)} .card .num.red{color:var(--red)}
.card .lbl{font-size:13.5px;margin-top:4px}
.card .src{font-size:11px;color:var(--muted);margin-top:8px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;margin-top:6px}
.selrow{display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end}
.selrow .fld{flex:1;min-width:220px}
label{font-size:12.5px;color:var(--muted);font-weight:600;display:block;margin-bottom:4px}
input[type=text],input[type=number],select{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:10px;font-size:14px;background:#fff;color:var(--ink)}
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
.step{display:flex;align-items:center;gap:10px;margin:7px 0}
.step .lbl{width:230px;font-size:12.5px;color:var(--ink)}
.step .bar-track{flex:1;background:#f6e6ef;border-radius:8px;height:16px;overflow:hidden}
.step .bar-fill{height:100%;background:linear-gradient(90deg,var(--pink),var(--pink2));border-radius:8px}
.step .val{width:92px;text-align:right;font-weight:700;font-size:13px;color:var(--wine)}
.roi{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px}
.roi .b{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px;text-align:center}
.roi .b b{display:block;font-size:22px;font-weight:800;color:var(--wine)}
.roi .b.green b{color:var(--green)} .roi .b span{font-size:11.5px;color:var(--muted)}
.callout{background:#fff6fb;border:1px solid var(--line);border-left:4px solid var(--pink);border-radius:10px;padding:12px 14px;font-size:13px;color:var(--ink);margin-top:12px}
.btnrow{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
.btn{background:var(--pink);color:#fff;border:none;border-radius:10px;padding:11px 18px;font-size:14px;font-weight:700;cursor:pointer}
.btn.sec{background:#fff;color:var(--pink);border:1px solid var(--pink)}
.btn:hover{filter:brightness(1.05)}
table.cmp{width:100%;border-collapse:collapse;margin-top:10px;font-size:13.5px}
table.cmp th,table.cmp td{border:1px solid var(--line);padding:10px 12px;text-align:left}
table.cmp th{background:#fbe7f2;color:var(--wine)}
table.cmp td.pp{background:#fff2f8;font-weight:600}
.tick{color:var(--green);font-weight:800} .cross{color:var(--red);font-weight:800}
.rank{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:8px}
.rank th,.rank td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:right}
.rank th:first-child,.rank td:first-child,.rank th:nth-child(2),.rank td:nth-child(2){text-align:left}
.rank th{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase}
.rank tr{cursor:pointer} .rank tr:hover td{background:var(--soft)}
.pill{display:inline-block;background:#fbe7f2;color:var(--wine);border-radius:999px;padding:3px 10px;font-size:12px;font-weight:700;margin:2px 4px 2px 0}
.foot{padding:26px 0;color:var(--muted);font-size:12.5px}
.foot b{color:var(--ink)}
.tag{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:4px 12px;font-size:12px;margin-top:14px}
.note{font-size:11.5px;color:var(--muted);margin-top:6px}
.src2{font-size:11px;color:var(--muted)}
</style>
</head>
<body>

<div class="hero">
  <div class="wrap">
    <div class="brand">G3 Health Service · PinkPapa (PinkLab)</div>
    <h1>Rastreio de câncer de colo do útero por teste DNA-HPV com autocoleta</h1>
    <p>Painel de apoio à decisão para secretarias municipais e estaduais de saúde: dimensiona a população-alvo (mulheres de 25 a 64 anos), o custo-benefício frente ao tratamento oncológico e o alinhamento às metas oficiais de rastreamento — município a município.</p>
    <div class="kpis">
      <div class="kpi"><b>__TOTM__</b><span>mulheres de 25 a 64 anos no Brasil (Censo 2022) — população-alvo do rastreamento</span></div>
      <div class="kpi"><b>17.010</b><span>casos novos/ano de câncer de colo do útero (INCA, 2023–2025)</span></div>
      <div class="kpi"><b>7.143</b><span>óbitos em 2023 — 1 mulher a cada ~90 min (Obs. de Oncologia)</span></div>
      <div class="kpi"><b>R$ 350</b><span>custo do kit PinkPapa por mulher × dezenas de milhares no tratamento tardio</span></div>
    </div>
    <div class="tag">Autoteste DNA-HPV homologado ANVISA · Nome técnico SIGTAP 0202100251 · Incorporado ao SUS (Portaria SECTICS/MS nº 3/2024)</div>
  </div>
</div>

<!-- 01 PROBLEMA -->
<section>
  <div class="wrap">
    <div class="h">01 · O problema</div>
    <h3 class="title">Câncer de colo do útero: quase 100% evitável, mas ainda mata milhares por rastreio tardio</h3>
    <div class="cards">
      <div class="card"><div class="num red">17.010</div><div class="lbl">casos novos por ano no Brasil (taxa 15,38/100 mil mulheres)</div><div class="src">INCA — Estimativa 2023–2025</div></div>
      <div class="card"><div class="num red">7.143</div><div class="lbl">óbitos em 2023, em alta de 8,3% desde 2019 — 3º câncer mais frequente entre brasileiras</div><div class="src">Observatório de Oncologia (SIM/SUS)</div></div>
      <div class="card"><div class="num">1 em 7</div><div class="lbl">mulheres com citologia normal e HPV-16 positivo tinham lesão de alto grau <b>não detectada</b> pelo Papanicolau</div><div class="src">Estudo ATHENA</div></div>
      <div class="card"><div class="num">4 a 6 meses</div><div class="lbl">de espera média no agendamento; rastreio ainda oportunístico e de baixa cobertura</div><div class="src">Diretrizes MS / material PinkLab</div></div>
    </div>
    <div class="callout">O HPV é a infecção sexualmente transmissível mais prevalente do mundo e o <b>principal causador do câncer de colo do útero</b>. A citologia (Papanicolau) tem sensibilidade de apenas 55–70% para lesões de alto grau (NIC2+); o teste de DNA-HPV chega a 90–95%, com valor preditivo negativo de 98–99% — o que permite espaçar o rastreio para 5 anos após resultado negativo.</div>
  </div>
</section>

<!-- 02 SOLUCAO / REGULATORIO -->
<section class="alt">
  <div class="wrap">
    <div class="h">02 · A solução e seu enquadramento oficial</div>
    <h3 class="title">PinkPapa: autocoleta de DNA-HPV, alinhada às novas diretrizes do Ministério da Saúde</h3>
    <div class="grid2">
      <div>
        <div class="panel">
          <b style="color:var(--wine)">Como funciona</b>
          <p style="font-size:14px">Autoteste de HPV homologado pela ANVISA. A mulher faz a <b>autocoleta</b> (escova no canal vaginal, movimento de rotação 360°, 5×) em UBS, UPA, centros comunitários ou hospitais — sem mesa ginecológica, sem espéculo, sem constrangimento. Detecta <b>28 tipos de HPV</b> (19 de alto risco oncogênico + 9 de baixo risco), informando o tipo viral. Acompanhamento por IA por até 5 anos.</p>
          <div>
            <span class="pill">Alto risco: 16, 18, 31, 33, 35, 39, 45, 51, 52, 56, 58, 59, 66, 68…</span>
            <span class="pill">Antecipa o diagnóstico em até 10 anos</span>
            <span class="pill">Aceitação ~100% (não invasivo)</span>
          </div>
        </div>
      </div>
      <div>
        <div class="panel">
          <b style="color:var(--wine)">Nome técnico e enquadramento (o que buscar no edital)</b>
          <table class="cmp" style="margin-top:8px">
            <tr><th>Campo</th><th>Valor oficial</th></tr>
            <tr><td>Procedimento SIGTAP</td><td class="pp">0202100251 — Exame molecular de detecção de HPV</td></tr>
            <tr><td>Descrição técnica</td><td>Análise molecular de material cérvico-vaginal por amplificação de ácido nucleico (PCR) com genotipagem parcial ou estendida</td></tr>
            <tr><td>Faixa etária</td><td>25 a 64 anos (300–779 meses)</td></tr>
            <tr><td>Financiamento</td><td>Média e Alta Complexidade (MAC)</td></tr>
            <tr><td>Incorporação</td><td>Portaria SECTICS/MS nº 3, de 07/03/2024 (CONITEC)</td></tr>
            <tr><td>Diretriz</td><td>Rastreamento organizado — DNA-HPV substitui o Papanicolau (MS/INCA, 2024)</td></tr>
          </table>
          <div class="note">Para compra de insumo/kit, o item é catalogado como material de detecção de DNA-HPV (CATMAT/BPS); o procedimento/serviço é o SIGTAP 0202100251 acima.</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- 03 FUNIL POR MUNICIPIO -->
<section>
  <div class="wrap">
    <div class="h">03 · Dimensionamento por município</div>
    <h3 class="title">Selecione um município e veja a população-alvo, o funil de rastreio e o custo-benefício</h3>
    <p class="lead">Todos os números partem da população feminina de 25 a 64 anos do Censo 2022 (IBGE). As premissas de cobertura, adesão e prevalência são ajustáveis — os valores-padrão estão documentados na metodologia.</p>
    <div class="panel">
      <div class="selrow">
        <div class="fld">
          <label>Município (digite para buscar — sem precisar de acento)</label>
          <input type="text" id="busca" placeholder="Ex.: sao paulo, salvador, campinas…" autocomplete="off" oninput="onBusca()">
          <div id="sug" style="position:relative"></div>
        </div>
        <div class="fld" style="max-width:160px">
          <label>ou selecione a UF</label>
          <select id="seluf" onchange="onUF()"><option value="">—</option></select>
        </div>
      </div>
      <div id="muniBox" style="display:none">
        <div class="muni-hero">
          <div class="mn" id="mn"></div><div class="mt" id="mt"></div>
        </div>
        <div class="grid2">
          <div>
            <div class="ctl"><label>Cobertura atual de rastreio (ajuste manual)</label><input type="range" id="in-cov-atual" min="1" max="100" value="40" oninput="calc()"><span class="rangeval" id="v-cov-atual">40%</span></div>
            <div class="ctl"><label>Cobertura-meta (OMS: 70%)</label><input type="range" id="in-cov-meta" min="1" max="100" value="70" oninput="calc()"><span class="rangeval" id="v-cov-meta">70%</span></div>
            <div class="ctl"><label>Adesão ao convite</label><input type="range" id="in-adesao" min="1" max="100" value="80" oninput="calc()"><span class="rangeval" id="v-adesao">80%</span></div>
            <div class="ctl"><label>Prevalência de HPV de alto risco</label><input type="range" id="in-prev" min="1" max="30" value="10" oninput="calc()"><span class="rangeval" id="v-prev">10%</span></div>
            <div class="ctl"><label>Lesões alto grau (NIC2+) entre HPV+</label><input type="range" id="in-lesao" min="1" max="40" value="12" oninput="calc()"><span class="rangeval" id="v-lesao">12%</span></div>
            <div class="ctl"><label>Progressão a câncer se não tratada</label><input type="range" id="in-prog" min="1" max="40" value="15" oninput="calc()"><span class="rangeval" id="v-prog">15%</span></div>
            <div class="ctl"><label>Preço do kit PinkPapa (R$)</label><input type="number" id="in-preco" value="350" min="1" oninput="calc()"></div>
          </div>
          <div>
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
        <div class="selrow" style="margin-top:14px">
          <div class="fld"><label>Nome do interessado / autoridade (opcional, entra na proposta)</label><input type="text" id="in-dest-nome" placeholder="Ex.: Secretaria Municipal de Saúde de …"></div>
          <div class="fld" style="max-width:260px"><label>E-mail do destinatário (opcional)</label><input type="text" id="in-dest-email" placeholder="nome@municipio.gov.br"></div>
        </div>
        <div class="btnrow">
          <button class="btn" onclick="baixarPDF()">📄 Baixar proposta em PDF (PNSB)</button>
          <button class="btn sec" onclick="enviarEmail()">✉️ Enviar proposta por e-mail</button>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- 04 CUSTO-BENEFICIO -->
<section class="alt">
  <div class="wrap">
    <div class="h">04 · Custo-benefício</div>
    <h3 class="title">R$ 350 na prevenção × dezenas de milhares no tratamento tardio</h3>
    <p class="lead">O valor por exame do PinkPapa cruzado com o custo real dos procedimentos do SUS para câncer de colo do útero. Fonte dos custos: Observatório de Oncologia (APAC/SIA-SIH do SUS) e Tabela Unificada SIGTAP.</p>
    <table class="cmp">
      <tr><th>Item</th><th>PinkPapa (DNA-HPV, autocoleta)</th><th>Papanicolau (citologia)</th><th>Tratamento do câncer (tardio)</th></tr>
      <tr><td>Custo unitário</td><td class="pp">R$ 350 / mulher</td><td>R$ 14,37 / exame (SIGTAP)</td><td>R$ 10.000 / paciente / ano (média)</td></tr>
      <tr><td>Sensibilidade (NIC2+)</td><td class="pp">90–95%</td><td>55–70%</td><td>—</td></tr>
      <tr><td>Intervalo</td><td class="pp">5 anos (após negativo)</td><td>3 anos (2 normais)</td><td>—</td></tr>
      <tr><td>Coleta</td><td class="pp">Autocoleta (sem profissional/estrutura)</td><td>Requer médico/enfermeiro + estrutura</td><td>—</td></tr>
      <tr><td>Procedimentos típicos</td><td class="pp">1 teste + acompanhamento IA</td><td>Exame + consulta + repetições</td><td>Cirurgia + radioterapia (R$ 4.038/APAC) + braquiterapia (R$ 3.936/APAC) + quimioterapia + internações (R$ 2.183)</td></tr>
    </table>
    <div class="cards" style="margin-top:16px">
      <div class="card"><div class="num pink">≈ 28×</div><div class="lbl">um único tratamento oncológico anual equivale a ~28 kits PinkPapa de prevenção</div><div class="src">R$ 10 mil ÷ R$ 350</div></div>
      <div class="card"><div class="num green">−30%</div><div class="lbl">de redução estimada de custos do SUS no longo prazo com rastreio por DNA-HPV</div><div class="src">CONITEC / impacto orçamentário</div></div>
      <div class="card"><div class="num">R$ 184 mi</div><div class="lbl">impacto orçamentário incremental em 5 anos da incorporação — compensado pela queda em tratamentos tardios</div><div class="src">CONITEC (2024)</div></div>
      <div class="card"><div class="num red">64%</div><div class="lbl">das pacientes em radioterapia se tratam fora do próprio município — custo e barreira de acesso</div><div class="src">Observatório de Oncologia</div></div>
    </div>
  </div>
</section>

<!-- 05 METAS -->
<section>
  <div class="wrap">
    <div class="h">05 · Metas e cobertura</div>
    <h3 class="title">Alinhamento às metas oficiais de eliminação do câncer de colo do útero</h3>
    <div class="cards">
      <div class="card"><div class="num pink">90-70-90</div><div class="lbl">Meta OMS até 2030: <b>90%</b> vacinadas, <b>70%</b> rastreadas com teste de alta performance, <b>90%</b> tratadas</div><div class="src">OMS / ONU (resolução de 194 países, 2020)</div></div>
      <div class="card"><div class="num">≥ 40%</div><div class="lbl">meta de cobertura do exame de rastreio nos municípios (indicador Previne Brasil)</div><div class="src">Ministério da Saúde — Previne Brasil</div></div>
      <div class="card"><div class="num red">em queda</div><div class="lbl">a cobertura de citologia nas capitais chegou ao menor valor da série histórica em 2023</div><div class="src">SISCAN / INCA</div></div>
      <div class="card"><div class="num green">-97%</div><div class="lbl">de redução possível na incidência atingindo as metas 90-70-90</div><div class="src">OMS / SBOC</div></div>
    </div>
    <div class="callout">Estratégia de eliminação = <b>Vacinação + Rastreio + Tratamento</b>. O PinkPapa atua diretamente no pilar do <b>rastreio</b>, com o teste de alta performance (DNA-HPV) que a própria OMS recomenda para atingir a meta de 70% de cobertura — e a autocoleta é o vetor para alcançar as mulheres que nunca se rastrearam.</div>
  </div>
</section>

<!-- 06 RANKING -->
<section class="alt">
  <div class="wrap">
    <div class="h">06 · Ranking de oportunidade</div>
    <h3 class="title">Municípios por população-alvo (mulheres 25–64 anos)</h3>
    <p class="lead">Clique em um município para carregá-lo no dimensionamento acima. Ranking completo dos 5.570 municípios com busca na seção 03.</p>
    <table class="rank" id="rankTable">
      <thead><tr><th>#</th><th>Município</th><th>UF</th><th>Mulheres 25–64</th><th>População</th><th>% alvo</th></tr></thead>
      <tbody id="rankBody"></tbody>
    </table>
  </div>
</section>

<!-- 07 METODOLOGIA -->
<section>
  <div class="wrap">
    <div class="h">07 · Metodologia e fontes</div>
    <h3 class="title">Como os números são calculados</h3>
    <div class="grid2">
      <div class="panel">
        <b style="color:var(--wine)">Modelo do funil</b>
        <ol style="font-size:13.5px;padding-left:18px">
          <li>População-alvo = mulheres de 25 a 64 anos do município (IBGE, Censo 2022, SIDRA 9514).</li>
          <li>Mulheres adicionais = alvo × (cobertura-meta − cobertura atual).</li>
          <li>Testes DNA-HPV = adicionais × adesão ao convite.</li>
          <li>HPV alto risco+ = testes × prevalência.</li>
          <li>Lesões NIC2+ = HPV+ × % de lesão; das quais a citologia perderia (95%−60%) por menor sensibilidade.</li>
          <li>Casos de câncer evitados = lesões × progressão evitada pelo tratamento precoce.</li>
          <li>Mortes evitadas = casos × letalidade evitável (40%).</li>
        </ol>
      </div>
      <div class="panel">
        <b style="color:var(--wine)">Fontes oficiais</b>
        <ul class="src2" style="padding-left:18px;line-height:1.7">
          <li>IBGE — Censo 2022 (população feminina por idade, SIDRA 9514/4709).</li>
          <li>INCA — Estimativa de Incidência 2023–2025.</li>
          <li>Observatório de Oncologia — Atenção ao câncer de colo de útero no SUS (custos APAC/SIA-SIH).</li>
          <li>SIGTAP — Tabela Unificada SUS, procedimentos 0202100251 e 0203010086.</li>
          <li>CONITEC / MS — Portaria SECTICS nº 3/2024 e relatório de incorporação DNA-HPV.</li>
          <li>OMS/ONU — Estratégia global de eliminação (90-70-90).</li>
        </ul>
        <div class="note">Ferramenta de apoio à decisão e prospecção comercial. Não substitui avaliação epidemiológica local nem diagnóstico médico. Premissas ajustáveis; valores-padrão conservadores.</div>
      </div>
    </div>
  </div>
</section>

<div class="wrap foot">
  <b>G3 Health Service</b> · Painel PinkPapa (PinkLab) — rastreio de câncer de colo do útero por DNA-HPV.<br>
  Contato: g3.healthservice@proton.me · Build __BUILD__ · Dados: IBGE Censo 2022, INCA, Observatório de Oncologia, CONITEC, OMS.
</div>

<script>__CHART__</script>
<script>__JSPDF__</script>
<script>__AUTOTABLE__</script>
<script>
const MUNICIPIOS = __DATA__;      // [nome, uf, pop, m2564]
const UF_STATS = __UFSTATS__;     // {uf:{pop,m,capital}}
const norm = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
let selected = null, lastCalc = null;

/* ---- formatação ---- */
const fmt = n => Math.round(n).toLocaleString('pt-BR');
const fmtMoney = n => 'R$ '+Math.round(n).toLocaleString('pt-BR');
const fmtPct = n => (n*100).toFixed(0).replace('.',',')+'%';

/* ---- busca ---- */
function onBusca(){
  const q = norm(document.getElementById('busca').value.trim());
  const sug = document.getElementById('sug');
  if(q.length<2){ sug.innerHTML=''; return; }
  const hits = MUNICIPIOS.filter(m=>norm(m[0]).includes(q)).slice(0,8);
  sug.innerHTML = '<div style="position:absolute;z-index:9;background:#fff;border:1px solid var(--line);border-radius:10px;width:100%;box-shadow:0 8px 24px rgba(124,29,79,.12);overflow:hidden">'+
    hits.map(m=>`<div style="padding:9px 12px;cursor:pointer;font-size:14px" onmousedown="pick('${m[0].replace(/'/g,"\\'")}','${m[1]}')">${m[0]} <span style="color:var(--muted)">/ ${m[1]} · ${m[3].toLocaleString('pt-BR')} mulheres 25-64</span></div>`).join('')+'</div>';
}
function pick(nome,uf){
  selected = MUNICIPIOS.find(m=>m[0]===nome && m[1]===uf);
  document.getElementById('busca').value = nome+' / '+uf;
  document.getElementById('sug').innerHTML='';
  showMuni();
}
function onUF(){
  const uf = document.getElementById('seluf').value;
  if(!uf) return;
  const list = MUNICIPIOS.filter(m=>m[1]===uf);
  selected = list[0]; // maior do estado
  document.getElementById('busca').value = selected[0]+' / '+uf;
  showMuni();
}
function showMuni(){
  if(!selected) return;
  document.getElementById('muniBox').style.display='block';
  document.getElementById('mn').textContent = selected[0]+' / '+selected[1];
  document.getElementById('mt').textContent = selected[3].toLocaleString('pt-BR')+' mulheres de 25 a 64 anos · '+selected[2].toLocaleString('pt-BR')+' habitantes (Censo 2022)';
  calc();
}

/* ---- núcleo do cálculo ---- */
const CUSTO_PRECOCE = 1500;    // tratamento de lesão precursora (CAF/EZT + acompanhamento), estimativa SUS
const CUSTO_TARDIO  = 30000;   // episódio de câncer invasivo (cirurgia+radio+braqui+quimio+internações), estimativa conservadora
const VALOR_MORTE   = 1000000; // valor social por morte evitada (genérico, ajustável)
const SENS_DNA = 0.95, SENS_CITO = 0.60;
const LETALIDADE_EVIT = 0.40;

function upd(id,suf){ document.getElementById('v-'+id).textContent = document.getElementById('in-'+id).value+suf; }
function calc(){
  if(!selected) return;
  ['cov-atual','cov-meta','adesao','prev','lesao','prog'].forEach(id=>{ const el=document.getElementById('v-'+id); if(el) el.textContent=document.getElementById('in-'+id).value+'%'; });
  const popAlvo = selected[3];
  const covA=+val('cov-atual')/100, covM=+val('cov-meta')/100, ades=+val('adesao')/100;
  const prev=+val('prev')/100, pLes=+val('lesao')/100, pProg=+val('prog')/100;
  const preco=+document.getElementById('in-preco').value||0;

  const ganho = Math.max(0, covM-covA);
  const adicionais = popAlvo*ganho;
  const testes = adicionais*ades;
  const hpvPos = testes*prev;
  const lesoes = hpvPos*pLes;
  const lesoesCitoPerde = lesoes*(SENS_DNA-SENS_CITO); // ganho de detecção do DNA-HPV
  const casosEvit = lesoes*pProg;
  const mortesEvit = casosEvit*LETALIDADE_EVIT;

  const custoPrograma = testes*preco;
  const custoEvitado = casosEvit*(CUSTO_TARDIO-CUSTO_PRECOCE);
  const valorSocial = mortesEvit*VALOR_MORTE;
  const roiFin = custoPrograma>0 ? (custoEvitado-custoPrograma)/custoPrograma : 0;
  const roiSoc = custoPrograma>0 ? (custoEvitado+valorSocial-custoPrograma)/custoPrograma : 0;
  const custoPorMorte = mortesEvit>0 ? custoPrograma/mortesEvit : 0;
  const custoPorCaso = casosEvit>0 ? custoPrograma/casosEvit : 0;

  const steps = [
    ['População-alvo (25–64 anos)', popAlvo, popAlvo],
    ['Mulheres adicionais no rastreio', adicionais, popAlvo],
    ['Testes DNA-HPV (c/ adesão)', testes, popAlvo],
    ['HPV de alto risco positivos', hpvPos, popAlvo],
    ['Lesões NIC2+ detectadas', lesoes, popAlvo],
    ['Casos de câncer evitados', casosEvit, popAlvo],
    ['Mortes potencialmente evitadas', mortesEvit, popAlvo],
  ];
  document.getElementById('funnel-box').innerHTML = steps.map(s=>{
    const pct = Math.max(1,(s[1]/s[2])*100);
    return `<div class="step"><div class="lbl">${s[0]}</div><div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div><div class="val">${fmt(s[1])}</div></div>`;
  }).join('');
  document.getElementById('roi-custo').textContent = fmtMoney(custoPrograma);
  document.getElementById('roi-cpm').textContent = mortesEvit>0 ? fmtMoney(custoPorMorte) : '—';
  document.getElementById('roi-soc').textContent = (roiSoc>=0?'+':'')+fmtPct(roiSoc);
  document.getElementById('resumo').innerHTML =
    `Para levar <b>${selected[0]}</b> de ${(covA*100).toFixed(0)}% a ${(covM*100).toFixed(0)}% de cobertura, seriam <b>${fmt(testes)}</b> testes DNA-HPV (R$ ${fmt(custoPrograma)}), `+
    `detectando ~<b>${fmt(lesoes)}</b> lesões de alto grau — sendo <b>${fmt(lesoesCitoPerde)}</b> que o Papanicolau provavelmente perderia. `+
    `Estimativa: <b>${fmt(casosEvit)}</b> cânceres e <b>${fmt(mortesEvit)}</b> mortes evitados; custo de tratamento evitado de <b>R$ ${fmt(custoEvitado)}</b> e retorno socioeconômico de <b>${(roiSoc*100).toFixed(0)}%</b>. `+
    `Frente ao Papanicolau (não somado a ele), o DNA-HPV é custo-efetivo e reduz gastos no longo prazo (CONITEC: −30%).`;

  lastCalc = {muni:selected, steps, custoPrograma, custoEvitado, valorSocial, roiFin, roiSoc, custoPorMorte, custoPorCaso, lesoes, lesoesCitoPerde,
    premissas:[
      ['Cobertura atual', (covA*100).toFixed(0)+'%'],
      ['Cobertura-meta', (covM*100).toFixed(0)+'%'],
      ['Adesão ao convite', (ades*100).toFixed(0)+'%'],
      ['Prevalência HPV alto risco', (prev*100).toFixed(0)+'%'],
      ['Lesões NIC2+ entre HPV+', (pLes*100).toFixed(0)+'%'],
      ['Progressão a câncer evitada', (pProg*100).toFixed(0)+'%'],
      ['Preço do kit PinkPapa', 'R$ '+preco.toLocaleString('pt-BR')],
    ]};
}
function val(id){ return document.getElementById('in-'+id).value; }

/* ---- ranking ---- */
function renderRank(){
  const body = document.getElementById('rankBody');
  body.innerHTML = MUNICIPIOS.slice(0,60).map((m,i)=>
    `<tr onclick="pick('${m[0].replace(/'/g,"\\'")}','${m[1]}');window.scrollTo({top:document.querySelector('.panel').offsetTop-40,behavior:'smooth'})">`+
    `<td>${i+1}</td><td>${m[0]}</td><td>${m[1]}</td><td>${m[3].toLocaleString('pt-BR')}</td><td>${m[2].toLocaleString('pt-BR')}</td><td>${(100*m[3]/m[2]).toFixed(1)}%</td></tr>`).join('');
}
function initUF(){
  const ufs = [...new Set(MUNICIPIOS.map(m=>m[1]))].sort();
  document.getElementById('seluf').innerHTML = '<option value="">—</option>'+ufs.map(u=>`<option value="${u}">${u}</option>`).join('');
}

/* ================= PDF (PNSB) ================= */
const MESES=['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'];
const dataExtenso = d => d.getDate()+' de '+MESES[d.getMonth()]+' de '+d.getFullYear();

const valueLabelPlugin={id:'vl',afterDatasetsDraw(c){const{ctx}=c;c.data.datasets.forEach((ds,di)=>{c.getDatasetMeta(di).data.forEach((bar,i)=>{ctx.save();ctx.fillStyle='#2A1622';ctx.font='bold 12px Arial';ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(Math.round(ds.data[i]).toLocaleString('pt-BR'),bar.x+8,bar.y);ctx.restore();});});}};
function chartImg(config,w,h){const cv=document.createElement('canvas');cv.width=w;cv.height=h;config.plugins=(config.plugins||[]).concat([valueLabelPlugin]);const ch=new Chart(cv.getContext('2d'),config);const img=ch.toBase64Image('image/png',1.0);ch.destroy();return img;}
function regionalImg(m){
  const uf=m[1], s=UF_STATS[uf], cap=s.capital, labels=[],data=[],bg=[];
  labels.push(m[0]+'/'+uf);data.push(m[3]);bg.push('#E6007E');
  if(cap && cap[0]!==m[0]){labels.push('Capital ('+cap[0]+')');data.push(cap[3]);bg.push('#7C1D4F');}
  labels.push('Total '+uf);data.push(s.m);bg.push('#B4126A');
  return chartImg({type:'bar',data:{labels,datasets:[{data,backgroundColor:bg}]},options:{responsive:false,animation:false,indexAxis:'y',layout:{padding:{right:70}},plugins:{legend:{display:false},title:{display:true,text:'Mulheres 25–64 — comparação regional (Censo 2022)',font:{size:13}}},scales:{x:{ticks:{callback:v=>v.toLocaleString('pt-BR')}}}}},700,240);
}
function funnelImgs(steps){
  const a=steps.slice(0,3), d=steps.slice(3);
  const i1=chartImg({type:'bar',data:{labels:a.map(s=>s[0]),datasets:[{data:a.map(s=>Math.round(s[1])),backgroundColor:'#E6007E'}]},options:{responsive:false,animation:false,indexAxis:'y',layout:{padding:{right:70}},plugins:{legend:{display:false},title:{display:true,text:'Alcance do programa — estimativa',font:{size:13}}},scales:{x:{ticks:{callback:v=>v.toLocaleString('pt-BR')}}}}},700,190);
  const i2=chartImg({type:'bar',data:{labels:d.map(s=>s[0]),datasets:[{data:d.map(s=>Math.round(s[1])),backgroundColor:'#7C1D4F'}]},options:{responsive:false,animation:false,indexAxis:'y',layout:{padding:{right:70}},plugins:{legend:{display:false},title:{display:true,text:'Resultados de detecção — estimativa',font:{size:13}}},scales:{x:{ticks:{callback:v=>v.toLocaleString('pt-BR')}}}}},700,240);
  return[i1,i2];
}
function pnsb(c){
  const m=c.muni,uf=m[1],passo=l=>c.steps.find(s=>s[0]===l)[1];
  const covA=c.premissas.find(p=>p[0]==='Cobertura atual')[1], covM=c.premissas.find(p=>p[0]==='Cobertura-meta')[1];
  return {
    problema:'O câncer de colo do útero é o 3º mais frequente entre as brasileiras e a 1ª causa de morte por câncer na América Latina: 17.010 casos novos e mais de 7.100 óbitos por ano no Brasil (INCA; Observatório de Oncologia). É causado pelo HPV e quase 100% evitável com rastreio de qualidade — mas a citologia (Papanicolau) detecta só 55–70% das lesões de alto grau, e a cobertura de rastreio está em queda. Em '+m[0]+'/'+uf+', a cobertura estimada hoje é de '+covA+', para uma população-alvo de '+m[3].toLocaleString('pt-BR')+' mulheres de 25 a 64 anos (Censo 2022, IBGE).',
    necessidade:'Para levar '+m[0]+' à cobertura-meta de '+covM+' (patamar da meta 70% da OMS), seria preciso incluir mais '+fmt(passo('Mulheres adicionais no rastreio'))+' mulheres no rastreio — cerca de '+fmt(passo('Testes DNA-HPV (c/ adesão)'))+' testes, considerando a adesão estimada. O rastreio oportunístico atual e a espera de 4 a 6 meses por consulta deixam muitas mulheres sem qualquer exame.',
    solucao:'O PinkPapa é um autoteste de DNA-HPV homologado pela ANVISA (procedimento SIGTAP 0202100251, incorporado ao SUS pela Portaria SECTICS/MS nº 3/2024). A autocoleta é feita pela própria mulher em UBS, UPA ou centro comunitário — sem espéculo, sem mesa ginecológica, sem constrangimento e com aceitação próxima de 100%. Detecta 28 tipos de HPV (19 de alto risco), com sensibilidade de 90–95% (contra 55–70% do Papanicolau), antecipa o diagnóstico em até 10 anos e permite espaçar o rastreio para 5 anos após resultado negativo, com acompanhamento por IA.',
    beneficio:'Com as premissas simuladas para '+m[0]+', o investimento em rastreio seria de R$ '+fmt(c.custoPrograma)+', detectando ~'+fmt(c.lesoes)+' lesões de alto grau (das quais ~'+fmt(c.lesoesCitoPerde)+' que o Papanicolau perderia) e evitando '+fmt(passo('Casos de câncer evitados'))+' casos e '+fmt(passo('Mortes potencialmente evitadas'))+' mortes — a um custo de R$ '+fmt(c.custoPorMorte)+' por morte evitada, com retorno socioeconômico de '+(c.roiSoc*100).toFixed(0)+'%. Substituindo (e não somando-se a) o Papanicolau, o teste de DNA-HPV é custo-efetivo e reduz o gasto do SUS no longo prazo (estimativa CONITEC: -30%, por menos falsos-negativos, intervalos de 5 anos e menos tratamentos tardios), alinhando o município às metas 90-70-90 da OMS e ao indicador de cobertura do Previne Brasil.'
  };
}
function montarPDF(){
  if(!lastCalc){alert('Selecione um município primeiro.');return null;}
  const c=lastCalc,m=c.muni,uf=m[1],{jsPDF}=window.jspdf;
  const doc=new jsPDF({unit:'pt',format:'a4'});
  const W=doc.internal.pageSize.getWidth(),H=doc.internal.pageSize.getHeight(),M=40;let y=46;
  const dest=document.getElementById('in-dest-nome').value.trim();
  const hoje=new Date(),ref='PINKPAPA-'+uf+'-'+hoje.getFullYear()+String(hoje.getMonth()+1).padStart(2,'0')+String(hoje.getDate()).padStart(2,'0');
  function bar(){doc.setFillColor(230,0,126);doc.rect(0,0,W,26,'F');doc.setTextColor(255);doc.setFont('helvetica','bold');doc.setFontSize(11);doc.text('G3 HEALTH SERVICE',M,17);doc.setFont('helvetica','normal');doc.setFontSize(7.5);doc.text('PinkPapa — rastreio de câncer de colo do útero por DNA-HPV (autocoleta)',W-M,17,{align:'right'});}
  function header(sub){bar();doc.setTextColor(124,29,79);doc.setFont('helvetica','bold');doc.setFontSize(13);doc.text('Proposta — '+m[0]+'/'+uf,M,46);doc.setTextColor(110);doc.setFont('helvetica','normal');doc.setFontSize(9);doc.text(sub+' · Ref. '+ref,M,60);doc.setDrawColor(230);doc.line(M,68,W-M,68);return 82;}
  function footer(){const p=doc.internal.getNumberOfPages();for(let i=1;i<=p;i++){doc.setPage(i);doc.setFontSize(7.5);doc.setTextColor(140);doc.text('G3 Health Service · g3.healthservice@proton.me · Ferramenta de apoio à decisão, não substitui diagnóstico médico',M,H-22);doc.text('Fontes: IBGE (Censo 2022), INCA, Observatório de Oncologia, CONITEC/MS, OMS · pág. '+i+'/'+p,M,H-12);}}

  // pág 1 — ofício + PNSB
  bar();y=54;
  doc.setTextColor(42,22,34);doc.setFont('helvetica','bold');doc.setFontSize(14);doc.text('PROPOSTA TÉCNICA E COMERCIAL',M,y);
  doc.setFont('helvetica','normal');doc.setFontSize(9);doc.setTextColor(110);doc.text('Brasília/DF, '+dataExtenso(hoje),W-M,y,{align:'right'});
  y+=18;doc.setDrawColor(230);doc.line(M,y,W-M,y);y+=16;
  doc.setTextColor(42,22,34);doc.setFontSize(10);
  doc.text('Ref.: '+ref,M,y);y+=16;
  doc.setFont('helvetica','bold');doc.text('Ao(À) '+(dest||'Secretaria Municipal/Estadual de Saúde de '+m[0]+'/'+uf),M,y);y+=14;
  doc.setFont('helvetica','normal');
  doc.text('Assunto: Implantação de rastreio de câncer de colo do útero por teste DNA-HPV (autocoleta).',M,y);y+=18;
  const P=pnsb(c);
  function bloco(tit,txt,cor){doc.setFont('helvetica','bold');doc.setTextColor(cor[0],cor[1],cor[2]);doc.setFontSize(11);doc.text(tit,M,y);y+=13;doc.setFont('helvetica','normal');doc.setTextColor(50,40,46);doc.setFontSize(9.5);const lines=doc.splitTextToSize(txt,W-2*M);doc.text(lines,M,y);y+=lines.length*12+8;}
  bloco('PROBLEMA',P.problema,[200,30,91]);
  bloco('NECESSIDADE',P.necessidade,[124,29,79]);
  bloco('SOLUÇÃO',P.solucao,[230,0,126]);
  bloco('BENEFÍCIO',P.beneficio,[18,169,122]);
  footer();

  // pág 2 — gráficos
  doc.addPage();y=header('Dimensionamento e alcance');
  const reg=regionalImg(m);doc.addImage(reg,'PNG',M,y,W-2*M,(W-2*M)*240/700);y+=(W-2*M)*240/700+10;
  const[i1,i2]=funnelImgs(c.steps);
  doc.addImage(i1,'PNG',M,y,W-2*M,(W-2*M)*190/700);y+=(W-2*M)*190/700+8;
  doc.addImage(i2,'PNG',M,y,W-2*M,(W-2*M)*240/700);
  footer();

  // pág 3 — tabelas
  doc.addPage();y=header('Premissas e custo-benefício');
  doc.autoTable({startY:y,head:[['Etapa do funil','Estimativa']],body:c.steps.map(s=>[s[0],fmt(s[1])]),theme:'grid',headStyles:{fillColor:[230,0,126]},styles:{fontSize:9}});
  y=doc.lastAutoTable.finalY+14;
  doc.autoTable({startY:y,head:[['Premissa','Valor']],body:c.premissas,theme:'grid',headStyles:{fillColor:[124,29,79]},styles:{fontSize:9}});
  y=doc.lastAutoTable.finalY+14;
  doc.autoTable({startY:y,head:[['Indicador','Valor']],body:[
    ['Investimento no rastreio',fmtMoney(c.custoPrograma)],
    ['Custo de tratamento evitado',fmtMoney(c.custoEvitado)],
    ['Custo por câncer evitado',c.custoPorCaso>0?fmtMoney(c.custoPorCaso):'—'],
    ['Custo por morte evitada',c.custoPorMorte>0?fmtMoney(c.custoPorMorte):'—'],
    ['Retorno socioeconômico',(c.roiSoc*100).toFixed(0)+'%'],
    ['Custo unitário PinkPapa','R$ '+(+document.getElementById('in-preco').value).toLocaleString('pt-BR')],
    ['Comparativo: Papanicolau (SIGTAP)','R$ 14,37 / exame'],
    ['Comparativo: tratamento/ano (SUS)','R$ 10.000 / paciente'],
  ],theme:'grid',headStyles:{fillColor:[18,169,122]},styles:{fontSize:9}});
  y=doc.lastAutoTable.finalY+16;
  // assinaturas
  doc.setDrawColor(180);doc.line(M,y+30,M+200,y+30);doc.line(W-M-200,y+30,W-M,y+30);
  doc.setFontSize(9);doc.setTextColor(60);
  doc.text('G3 Health Service (proponente)',M,y+44);
  doc.text((dest||'Secretaria de Saúde')+' (contratante)',W-M-200,y+44);
  doc.setFontSize(8);doc.setTextColor(120);doc.text('Local e data: ____________________________, '+dataExtenso(hoje),M,y+66);
  footer();
  return {doc,ref};
}
function baixarPDF(){const r=montarPDF();if(r) r.doc.save('Proposta_PinkPapa_'+(selected?selected[0].replace(/\s/g,'_'):'')+'.pdf');}
function enviarEmail(){
  const r=montarPDF();if(!r)return;
  const email=document.getElementById('in-dest-email').value.trim();
  const file=r.doc.output('blob');
  const f=new File([file],'Proposta_PinkPapa_'+(selected?selected[0].replace(/\s/g,'_'):'')+'.pdf',{type:'application/pdf'});
  const assunto='Proposta PinkPapa — rastreio de câncer de colo do útero ('+(selected?selected[0]+'/'+selected[1]:'')+')';
  const corpo='Segue em anexo a proposta técnica e comercial do PinkPapa para '+(selected?selected[0]+'/'+selected[1]:'')+'.';
  if(navigator.canShare && navigator.canShare({files:[f]})){
    navigator.share({files:[f],title:assunto,text:corpo}).catch(()=>{});
  } else {
    r.doc.save(f.name);
    location.href='mailto:'+email+'?subject='+encodeURIComponent(assunto)+'&body='+encodeURIComponent(corpo+'\n\n(Anexe o PDF que acabou de ser baixado.)');
  }
}

initUF();renderRank();
</script>
</body>
</html>
"""

out = HTML
out = out.replace("__TOTM__", TOTM_BR)
out = out.replace("__BUILD__", BUILD)
out = out.replace("__DATA__", DATA_JS)
out = out.replace("__UFSTATS__", UFSTATS_JS)
out = out.replace("__CHART__", CHART)
out = out.replace("__JSPDF__", JSPDF)
out = out.replace("__AUTOTABLE__", AUTOTABLE)

dest = BASE/"index.html"
dest.write_text(out, encoding="utf-8")
(BASE/".nojekyll").write_text("", encoding="utf-8")
print(f"OK: {dest} ({len(out)//1024} KB)  build {BUILD}")
print(f"Brasil mulheres 25-64: {TOT_M:,} ({100*TOT_M/TOT_POP:.1f}%)  ·  {len(muns)} municipios")
