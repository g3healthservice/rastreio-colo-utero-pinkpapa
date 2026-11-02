#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monta os RASCUNHOS de e-mail de prospecção por ente (município/estado), a partir
da lista de saldos já enriquecida com contato (emails_conasems.py / CONASS).

NÃO envia nada. Gera:
  - dados/rascunhos_<comp>.csv : uma linha por ente (Para, Assunto, Corpo, ...)
  - dados/rascunhos_amostra/*.txt : alguns rascunhos prontos para leitura

Uso:
  python3 gerar_rascunhos.py                         # todos, lista completa
  python3 gerar_rascunhos.py --in dados/saldos_202607_municipais_com_OCI_contatos.csv
  python3 gerar_rascunhos.py --amostra 10 --min-saldo 100000
"""
import argparse, csv, json, re
from pathlib import Path

ASSINATURA = "Atenciosamente,\nG3 Health Service — PinkPapa\nRastreio de câncer de colo do útero por DNA-HPV (autocoleta)"


def parse_brl(s):
    """'143.352.519,36' -> 143352519.36 ; vazio/—/0 -> 0.0."""
    try:
        return float((s or "0").replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def fmt_int(n):
    return f"{int(n):,}".replace(",", ".")


def _brl(v):
    return f"{float(v):,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")


def dimensiona(saldo, pop, covA, preco, ades, meta):
    """Encaixe dinheiro × demanda (mesma lógica do painel reconFrom). Devolve dict ou None."""
    if saldo <= 0 or preco <= 0:
        return None
    testadas_saldo = int(saldo / preco)
    testadas_gap = int(pop * max(0.0, meta - covA) * ades) if pop > 0 else 0
    acao = min(testadas_saldo, testadas_gap) if testadas_gap > 0 else testadas_saldo
    pts = (acao / pop * 100) if pop > 0 else 0
    covB = covA + (acao / pop) if pop > 0 else None
    saldo_limita = testadas_gap > 0 and testadas_saldo < testadas_gap
    return {"acao": acao, "convocadas": int(acao / ades) if ades > 0 else 0,
            "pts": pts, "covB": covB, "saldo_limita": saldo_limita,
            "falta": max(0.0, testadas_gap * preco - saldo)}


def corpo_ente(r, comp, info=None, preco=590.0, ades=0.80, meta=0.70):
    """Monta assunto e corpo a partir das colunas da linha r (dict)."""
    uf = r["UF"]; ente = r["Município/Ente"].title(); tipo = r["Tipo"]
    estadual = tipo == "ESTADUAL"
    alvo = ente if estadual else f"{ente}/{uf}"
    orgao = (f"Secretaria de Estado da Saúde de {ente}" if estadual
             else f"Secretaria Municipal de Saúde de {ente}/{uf}")
    saldo = r.get("Saldo a executar", "").strip()
    oci = r.get("Saldo OCI (ambulatorial)", "").strip()
    emendas = r.get("Saldo emendas", "").strip()
    mutM = r.get("Mutirão das Mulheres", "").strip()
    pct = (r.get("% executado", "") or "").strip()
    link = r.get("Painel (link)", "").strip()
    sec = (r.get("Secretário(a) (CONASEMS)", "") or "").strip()

    assunto = f"Rastreio de câncer de colo do útero (DNA-HPV) — saldo a executar de R$ {saldo} · {alvo}"

    linhas = []
    linhas.append(f"Prezada {orgao},")
    if sec and "SES" not in sec and "via CONASS" not in sec:
        linhas.append(f"A/C {sec.title()} — Secretaria de Saúde")
    linhas.append("")
    linhas.append("Identificamos, no painel oficial Saldo do Gestor (SUS 360 — Programa Agora Tem "
                  f"Especialistas, competência {comp[4:]}/{comp[:4]}), que o ente dispõe de recurso "
                  "federal já antecipado ao fundo de saúde ainda a executar:")
    linhas.append("")
    linhas.append(f"  • Saldo total a executar: R$ {saldo}")
    if oci and oci not in ("0,00", ""):
        linhas.append(f"  • Componente ambulatorial (OCI): R$ {oci}")
    if emendas and emendas not in ("0,00", ""):
        linhas.append(f"  • Emendas: R$ {emendas}")
    if mutM and mutM not in ("0,00", ""):
        linhas.append(f"  • Mutirão das Mulheres: R$ {mutM}")
    if pct:
        linhas.append(f"  • Percentual executado: {pct}%")
    linhas.append("")

    # ação que cabe no saldo (demonstra a disponibilidade do serviço, dimensionada pelo recurso)
    mi = (info or {}).get((r.get("cod_IBGE") or "").strip(), {})
    pop = mi.get("m2564") or 0
    covA = mi.get("cobSiscan")
    covA = round(covA * 100) / 100 if covA is not None else None  # mesma cobertura (arredondada) do painel
    dim = dimensiona(parse_brl(saldo), pop if not estadual else 0,
                     covA if (covA is not None and not estadual) else 0.0, preco, ades, meta)
    if dim:
        if not estadual and pop > 0 and covA is not None:
            txt = (f"Com esse saldo, a ação PinkPapa rastreia aproximadamente {fmt_int(dim['acao'])} mulheres "
                   f"(R$ {int(preco)} por teste, convocando ~{fmt_int(dim['convocadas'])}), elevando a cobertura de "
                   f"{covA*100:.0f}% para cerca de {dim['covB']*100:.0f}%.")
            if dim["saldo_limita"]:
                txt += (f" É a ação já executável com o recurso no fundo; o complemento para a meta de {meta*100:.0f}% "
                        f"(R$ {_brl(dim['falta'])}) pode entrar por MAC, emenda ou Mutirão das Mulheres nos ciclos seguintes.")
            else:
                txt += " O recurso cobre a meta com folga, que ainda financia o seguimento das mulheres HPV+ e o próximo ciclo."
        else:
            txt = (f"Com esse saldo, a ação PinkPapa rastreia aproximadamente {fmt_int(dim['acao'])} mulheres "
                   f"(R$ {int(preco)} por teste) — dimensionável por município conforme a pactuação.")
        linhas.append(txt)
        linhas.append("")

    linhas.append("O mutirão de rastreio por DNA-HPV com autocoleta é um caminho direto para executar "
                  "esse recurso: o rastreio é pago por MAC (SIGTAP 0202100251) e o seguimento das mulheres "
                  "HPV+ (colposcopia, biópsia, EZT) gera produção ambulatorial que consome o saldo e cumpre "
                  "o encontro de contas do PATE — evitando a glosa por não-produção.")
    if link:
        linhas.append("")
        linhas.append(f"Confira os números na fonte oficial: {link}")
    linhas.append("")
    linhas.append("Recomendamos estruturar a ação por credenciamento (Lei nº 14.133/2021, arts. 79 e 74, IV): "
                  "com os preços fixados pela Administração e a distribuição impessoal da demanda, é a rota mais "
                  "aderente à análise dos órgãos de controle (TCE/MP). A parceria via MROSC (Lei nº 13.019/2014, "
                  "Termo de Colaboração) permanece como alternativa quando houver organização da sociedade civil executora.")
    linhas.append("")
    linhas.append(f"Em anexo seguem a apresentação do PinkPapa, a proposta técnica e comercial dimensionada para {alvo} "
                  "e a documentação de instrução das duas rotas — ETP e Nota Técnica (comuns), Edital de Credenciamento "
                  "e Termo de Referência (14.133), e Termo de Colaboração e Plano de Trabalho (MROSC).")
    linhas.append("")
    linhas.append(ASSINATURA)
    return assunto, "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser(description="Gera rascunhos de e-mail por ente (sem enviar).")
    ap.add_argument("--in", dest="inp", default="dados/saldos_202607_contatos.csv")
    ap.add_argument("--out")
    ap.add_argument("--comp", default="202607", help="competência AAAAMM (para o texto)")
    ap.add_argument("--amostra", type=int, default=5, help="quantos .txt de amostra gerar")
    ap.add_argument("--min-saldo", type=float, default=0, help="(reservado) filtro futuro")
    ap.add_argument("--preco", type=float, default=590.0, help="custo por mulher testada (kit)")
    ap.add_argument("--adesao", type=float, default=0.80, help="adesão ao convite")
    ap.add_argument("--meta", type=float, default=0.70, help="cobertura-meta p/ dimensionar a demanda")
    a = ap.parse_args()

    src = Path(a.inp)
    out = Path(a.out) if a.out else Path("dados") / f"rascunhos_{a.comp}.csv"
    amostra_dir = Path("dados") / "rascunhos_amostra"
    amostra_dir.mkdir(parents=True, exist_ok=True)

    # população/cobertura por ibge6 (mesma fonte do painel), p/ dimensionar a ação no corpo
    mp = Path("municipios_pinkpapa.json")
    if not mp.exists():
        mp = Path("dados") / "municipios_pinkpapa.json"
    info = {str(d.get("ibge") or "")[:6]: d for d in json.load(open(mp, encoding="utf-8"))} if mp.exists() else {}

    with src.open(encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f, delimiter=";")
        rows = list(rd)

    i_email = "E-mail (CONASEMS)"
    n = sem_email = 0
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["UF", "Ente", "Tipo", "Para (e-mail)", "Saldo a executar", "Assunto", "Corpo"])
        for r in rows:
            para = (r.get(i_email, "") or "").strip()
            if not para:
                sem_email += 1
            assunto, corpo = corpo_ente(r, a.comp, info, a.preco, a.adesao, a.meta)
            w.writerow([r["UF"], r["Município/Ente"], r["Tipo"], para,
                        r.get("Saldo a executar", ""), assunto, corpo])
            if n < a.amostra:
                nome = re.sub(r"[^\w]+", "_", f"{r['UF']}_{r['Município/Ente']}")[:40]
                (amostra_dir / f"{nome}.txt").write_text(
                    f"PARA: {para}\nASSUNTO: {assunto}\n\n{corpo}\n", encoding="utf-8")
            n += 1

    print(f"Rascunhos gerados: {n}  | sem e-mail de destino: {sem_email}")
    print(f"CSV: {out}")
    print(f"Amostras .txt: {amostra_dir}/ ({min(a.amostra, n)} arquivos)")


if __name__ == "__main__":
    main()
