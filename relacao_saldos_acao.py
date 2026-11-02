#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relação de municípios com SALDO A EXECUTAR (SUS 360 / PATE), dimensionando o
tamanho da ação PinkPapa pelo recurso já em caixa — não pela meta de 70%.

Base (4 figuras pedidas): custo por mulher rastreada, Componente ambulatorial
(OCI), Saldo a comprovar com produção e Produção aprovada (SIA/SIH).

Dimensionamento: mulheres rastreáveis = Saldo a comprovar ÷ custo do kit.
Fonte local (mesma do painel): dados/pate_saldo_202607.json + municipios_pinkpapa.json.
Gera CSV pt-BR (';' , decimal ',', BOM p/ Excel) e imprime o topo p/ validação.

Uso:
  python3 relacao_saldos_acao.py                      # municipais com saldo>0
  python3 relacao_saldos_acao.py --preco 590 --adesao 0.80
  python3 relacao_saldos_acao.py --min-mulheres 500   # só ação >= 500 mulheres
  python3 relacao_saldos_acao.py --uf RS --top 30
"""
import argparse, csv, json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def brl(v):
    try:
        return f"{float(v):,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")
    except (TypeError, ValueError):
        return ""


def main():
    ap = argparse.ArgumentParser(description="Relação de municípios com saldo a executar, ação dimensionada pelo saldo.")
    ap.add_argument("--preco", type=float, default=590.0, help="custo por mulher testada (kit), padrão 590")
    ap.add_argument("--adesao", type=float, default=0.80, help="adesão ao convite (convocadas->testadas), padrão 0,80")
    ap.add_argument("--meta", type=float, default=0.70, help="cobertura-meta p/ dimensionar a demanda, padrão 0,70")
    ap.add_argument("--min-saldo", type=float, default=0.01, help="saldo a comprovar mínimo (padrão >0)")
    ap.add_argument("--min-mulheres", type=int, default=0, help="só ações que rastreiam >= N mulheres")
    ap.add_argument("--uf", help="filtra por UF")
    ap.add_argument("--top", type=int, default=25, help="quantas linhas imprimir no terminal")
    ap.add_argument("--out", help="CSV de saída")
    a = ap.parse_args()

    pate = json.load(open(BASE / "dados/pate_saldo_202607.json", encoding="utf-8"))
    muns = json.load(open(BASE / "municipios_pinkpapa.json", encoding="utf-8")) \
        if (BASE / "municipios_pinkpapa.json").exists() \
        else json.load(open(BASE / "dados/municipios_pinkpapa.json", encoding="utf-8"))
    # pop/cobertura por ibge6
    info = {str(d.get("ibge") or "")[:6]: d for d in muns}

    rows = []
    for ibge6, d in pate.items():
        if d.get("tipo") != "MUNICIPAL":
            continue
        saldo = d.get("saldo") or 0.0
        if saldo < a.min_saldo:
            continue
        if a.uf and (d.get("uf") or "").upper() != a.uf.upper():
            continue
        mi = info.get(ibge6, {})
        pop = mi.get("m2564") or 0                      # mulheres 25-64 (alvo do rastreio)
        cob = mi.get("cobSiscan")                        # 0..1 ou None
        covA = cob if cob is not None else 0.0
        # (A) o que o saldo em caixa financia
        testadas_saldo = int(saldo / a.preco) if a.preco > 0 else 0
        # (B) o que a demanda precisa p/ chegar a 70% (gap de cobertura × adesão)
        testadas_gap = int(pop * max(0.0, a.meta - covA) * a.adesao) if pop > 0 else 0
        custo_gap = round(testadas_gap * a.preco, 2)
        # ação recomendada = encaixa os dois: o menor entre dinheiro e necessidade
        testadas = min(testadas_saldo, testadas_gap) if testadas_gap > 0 else testadas_saldo
        convocadas = int(testadas / a.adesao) if a.adesao > 0 else 0
        pts = (testadas / pop * 100) if pop > 0 else 0                 # +pontos de cobertura
        receita = round(testadas * a.preco, 2)                        # cabe no saldo e na demanda
        regime = "saldo limita" if testadas_saldo <= testadas_gap else "demanda limita (sobra saldo)"
        folga = round(saldo - custo_gap, 2) if testadas_saldo > testadas_gap else 0.0
        if testadas < a.min_mulheres:
            continue
        rows.append({
            "uf": d.get("uf") or "", "ibge6": ibge6, "nome": d.get("nome") or mi.get("nome") or "",
            "pop": pop, "cob": round(covA * 100) if cob is not None else "",
            "prod": d.get("producao") or 0.0, "pct": d.get("pctExecutado") or 0.0,
            "saldo": saldo, "oci_saldo": d.get("saldoAmbulatorial") or 0.0,
            "oci_rep": d.get("repAmbulatorial") or 0.0, "oci_prod": d.get("prodAmbulatorial") or 0.0,
            "mm": d.get("mutiraoMulheres") or 0.0, "regime": regime, "folga": folga,
            "testadas": testadas, "convocadas": convocadas, "pts": pts, "receita": receita,
        })

    rows.sort(key=lambda r: r["saldo"], reverse=True)

    # self-check: receita dimensionada nunca excede o saldo; contagem íntegra
    assert all(r["receita"] <= r["saldo"] + a.preco for r in rows), "receita dimensionada acima do saldo"
    assert all(r["testadas"] >= a.min_mulheres for r in rows), "linha abaixo do mínimo de mulheres"

    out = Path(a.out) if a.out else BASE / "dados" / "relacao_saldos_acao_202607.csv"
    out.parent.mkdir(exist_ok=True)
    COLS = [
        ("UF", "uf"), ("cod_IBGE", "ibge6"), ("Município", "nome"),
        ("Mulheres 25-64", "pop"), ("Cobertura atual %", "cob"),
        ("Produção aprovada (SIA/SIH)", "prod"), ("% executado", "pct"),
        ("Saldo a comprovar", "saldo"), ("Saldo OCI (ambulatorial)", "oci_saldo"),
        ("OCI repassado", "oci_rep"), ("OCI produzido", "oci_prod"),
        ("Mutirão das Mulheres", "mm"),
        ("Regime", "regime"),
        (f"Ação recomendada — mulheres ({int(a.meta*100)}% ou saldo)", "testadas"),
        ("Convocadas (busca ativa)", "convocadas"),
        ("+pontos de cobertura", "pts"),
        ("Receita da ação", "receita"),
        ("Folga de saldo (p/ seguimento/próx. ciclo)", "folga"),
    ]
    money = {"prod", "saldo", "oci_saldo", "oci_rep", "oci_prod", "mm", "receita", "folga"}
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([lbl for lbl, _ in COLS] + ["Painel (link)"])
        for r in rows:
            link = f"https://sus360.saude.gov.br/painel/saldo-gestor/{r['uf'].lower()}/{r['ibge6']}"
            line = []
            for _, k in COLS:
                v = r[k]
                if k in money:
                    v = brl(v)
                elif k == "pts":
                    v = f"{v:.1f}".replace(".", ",")
                line.append(v)
            w.writerow(line + [link])

    tot_saldo = sum(r["saldo"] for r in rows)
    tot_acao = sum(r["testadas"] for r in rows)
    n_saldo = sum(1 for r in rows if r["regime"] == "saldo limita")
    n_dem = len(rows) - n_saldo
    print(f"Competência 202607 · preço kit R$ {brl(a.preco)} · adesão {a.adesao*100:.0f}% · meta {a.meta*100:.0f}%")
    print(f"Municípios com saldo a executar"
          + (f" (UF={a.uf})" if a.uf else "")
          + (f", ação ≥ {a.min_mulheres} mulheres" if a.min_mulheres else "")
          + f": {len(rows)}")
    print(f"  Saldo a comprovar somado: R$ {brl(tot_saldo)}")
    print(f"  Ação recomendada (mulheres, total): {tot_acao:,}".replace(",", "."))
    print(f"  Regime: {n_saldo} 'saldo limita' (dinheiro é o teto) · {n_dem} 'demanda limita' (saldo sobra p/ seguimento)")
    print(f"CSV: {out}\n")
    w0 = max((len(r["nome"]) for r in rows[:a.top]), default=10)
    print(f"{'Município':<{w0}}  {'UF':<2}  {'Saldo a comprovar':>18}  {'Ação(mulh.)':>11}  {'+pts':>5}  {'Cob.':>4}  Regime")
    for r in rows[:a.top]:
        reg = "saldo" if r["regime"] == "saldo limita" else "demanda↑"
        print(f"{r['nome']:<{w0}}  {r['uf']:<2}  R$ {brl(r['saldo']):>15}  {r['testadas']:>11,}  {r['pts']:>4.0f}  {str(r['cob'])+'%':>4}  {reg}".replace(",", "."))


if __name__ == "__main__":
    main()
