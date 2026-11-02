#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera os modelos editáveis (.docx) das peças de instrução do mutirão PinkPapa,
NEUTROS (sem a figura da G3 Health Service / PinkLab) e nas DUAS rotas jurídicas:
  - MROSC (Lei 13.019/2014): Termo de Colaboração + Plano de Trabalho
  - Credenciamento (Lei 14.133/2021, arts. 79 e 74, IV): Edital + Termo de Referência
ETP e Nota Técnica servem às duas rotas.
Conteúdo alinhado ao gerador do painel (gerar_dashboard_pinkpapa.py).
"""
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE = Path(__file__).resolve().parent / "modelos"
BASE.mkdir(exist_ok=True)

DISC = ("Documento em modelo de trabalho (minuta). Os campos entre colchetes devem ser preenchidos "
        "pelo órgão com os dados locais. As estimativas de quantidade devem ser confirmadas pelo SISCAN, "
        "pelo e-SUS APS e pela base populacional; as de valor, por pesquisa de mercado própria, nos termos "
        "da Instrução Normativa SEGES/ME nº 65/2021. Não substitui o juízo da área técnica, da assessoria "
        "jurídica e do controle interno.")


def novo():
    doc = Document()
    st = doc.styles["Normal"].font
    st.name = "Times New Roman"
    st.size = Pt(12)
    return doc


def titulo(doc, linhas):
    for i, (txt, sz, bold) in enumerate(linhas):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(txt)
        r.bold = bold
        r.font.size = Pt(sz)


def disc(doc):
    p = doc.add_paragraph()
    r = p.add_run(DISC)
    r.italic = True
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)


def h1(doc, t):
    p = doc.add_paragraph()
    r = p.add_run(t.upper())
    r.bold = True
    r.font.size = Pt(12)


def h2(doc, t):
    p = doc.add_paragraph()
    r = p.add_run(t)
    r.bold = True
    r.font.size = Pt(12)


def par(doc, t):
    p = doc.add_paragraph(t)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def al(doc, itens):
    for i, t in enumerate(itens):
        p = doc.add_paragraph(f"{chr(97+i)}) {t}")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Pt(18)


def inc(doc, itens):
    for t in itens:
        par(doc, t)


def tbl(doc, head, linhas):
    t = doc.add_table(rows=1, cols=len(head))
    t.style = "Table Grid"
    for c, h in zip(t.rows[0].cells, head):
        c.paragraphs[0].add_run(h).bold = True
    for linha in linhas:
        cells = t.add_row().cells
        for c, v in zip(cells, linha):
            c.text = v
    doc.add_paragraph()


def sign(doc, blocos):
    doc.add_paragraph()
    for nome, papel in blocos:
        p = doc.add_paragraph("______________________________________")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(nome)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if papel:
            p = doc.add_paragraph(papel)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("Local e data: ____________________________________, ______ de __________________ de ______.")


def salva(doc, nome):
    caminho = BASE / nome
    doc.save(caminho)
    print("OK:", caminho.name)


ORG = "SECRETARIA MUNICIPAL DE SAÚDE DE [ MUNICÍPIO / UF ]"
BRASAO = ("[ BRASÃO / TIMBRE DO MUNICÍPIO ]", 10, False)


# ===================== 1) ETP — serve às duas rotas =====================
def gerar_etp():
    d = novo()
    titulo(d, [BRASAO, (ORG, 12, False),
               ("ESTUDO TÉCNICO PRELIMINAR — ETP", 13, True),
               ("CONTRATAÇÃO DE SERVIÇOS DE RASTREAMENTO ORGANIZADO DO CÂNCER DO COLO DO ÚTERO "
                "POR TESTE MOLECULAR DNA-HPV COM AUTOCOLETA", 11, True)])
    tbl(d, ["Campo", "Conteúdo"], [
        ["Processo administrativo nº", "[ ___ / ______ ]"],
        ["Unidade demandante", "[ Secretaria Municipal de Saúde de ___ / ___ ]"],
        ["Rota jurídica pretendida", "[ selecionar ] MROSC (Lei 13.019/2014) OU Credenciamento (Lei 14.133/2021, arts. 79 e 74, IV)"],
        ["Base legal", "Lei 13.019/2014 (MROSC) e/ou Lei 14.133/2021 (arts. 18, 79 e 74, IV), conforme a rota"],
        ["Modelo de execução", "Ação concentrada e itinerante (mutirão) integrada à Atenção Primária, com retaguarda laboratorial e navegação de pacientes"],
        ["Executora", "[ OSC — razão social/CNPJ (rota MROSC) ] OU [ credenciada(s) — razão social/CNPJ (rota 14.133) ], apoiada(s) por laboratório de biologia molecular com responsabilidade técnica própria"],
        ["Data", "[ ___/___/______ ]"],
    ])
    disc(d)

    h1(d, "1. Descrição da necessidade da contratação")
    par(d, "1.1. O câncer do colo do útero é neoplasia de causa conhecida, evolução lenta e lesão precursora tratável e, ainda assim, permanece entre as principais causas de morte por câncer na população feminina brasileira, concentrando-se justamente nas mulheres que o rastreamento oportunístico não alcança. É doença quase integralmente evitável por rastreamento de qualidade associado ao tratamento tempestivo das lesões precursoras (INCA; OMS).")
    par(d, "1.2. O modelo praticado na rede é predominantemente oportunístico, dependente da procura espontânea da usuária. A citologia convencional exige estrutura física específica (mesa ginecológica, espéculo e foco de luz) e profissional executor, impõe exposição corporal que afasta parcela relevante das mulheres e apresenta elevado absenteísmo e perda de seguimento. Em [ MUNICÍPIO ], a cobertura estimada é da ordem de [ __ ]%, inferior à meta de 70% (pilar 70 das metas 90-70-90 da OMS).")
    par(d, "1.3. Em 2024, a CONITEC recomendou a adoção do teste molecular de detecção do DNA-HPV como exame primário de rastreamento, em substituição à citologia, no âmbito de modelo de rastreamento organizado. A incorporação foi formalizada pela Portaria SECTICS/MS nº 3, de 7 de março de 2024, e o procedimento consta da Tabela SIGTAP sob o código 0202100251 (de média complexidade, faixa de 25 a 64 anos, registro por BPA-I).")
    par(d, "1.4. A autocoleta vaginal apresenta aceitação próxima de 100% e alcança mulheres que nunca se rastrearam. A necessidade decorre de quatro fatores convergentes: epidemiológico (mortalidade evitável); assistencial (baixa cobertura, absenteísmo e fragmentação do seguimento); normativo (estratégia nacional de rastreamento organizado com DNA-HPV); e de equidade (não-cobertura concentrada nas mulheres de maior vulnerabilidade).")

    h1(d, "2. Previsão no plano de contratações e alinhamento institucional")
    par(d, "2.1. A ação [ está / não está ] prevista no Plano Municipal de Saúde e na Programação Anual de Saúde vigentes, aderindo às diretrizes de atenção integral à saúde da mulher e aos indicadores do Previne Brasil.")
    par(d, "2.2. Verificar a compatibilidade com o PPA, a LDO e a LOA, registrando-se a fonte de financiamento pretendida (MAC, recursos próprios, emendas parlamentares ou transferências fundo a fundo específicas).")

    h1(d, "3. Requisitos da contratação")
    h2(d, "3.1. Requisitos de natureza técnica e sanitária")
    al(d, [
        "Kit de autocoleta vaginal com registro ativo na ANVISA e validade não inferior a 12 meses na entrega;",
        "Exame de biologia molecular com genotipagem de, no mínimo, 28 tipos de HPV, identificados individualmente ao menos os tipos 16 e 18;",
        "Laboratório com inscrição regular no SCNES/CNES, licença sanitária vigente para diagnóstico molecular e responsável técnico habilitado;",
        "Controle interno de amplificação por amostra e liberação do laudo em até 48 horas do recebimento;",
        "Logística de recolhimento e transporte do material biológico, com cadeia de custódia;",
        "Plataforma digital para cadastro, rastreabilidade, laudo digital, alerta de resultado alterado e seguimento por até 5 anos;",
        "Conformidade integral à LGPD (Lei 13.709/2018), com criptografia, controle de acesso por perfil, logs e encarregado de dados indicado;",
        "Plano de Gerenciamento de Resíduos de Serviços de Saúde (PGRSS), nos termos da RDC ANVISA nº 222/2018.",
    ])
    h2(d, "3.2. Requisitos de natureza assistencial")
    al(d, [
        "Observância das diretrizes do Ministério da Saúde e do INCA para o rastreamento do câncer do colo do útero;",
        "Atendimento gratuito, humanizado e sem discriminação, vedada cobrança direta ou indireta à usuária;",
        "Submissão integral à regulação do acesso exercida pela Secretaria;",
        "Capacitação inicial e continuada das equipes da Atenção Primária;",
        "Navegação de pacientes: nenhuma mulher poderá ser liberada sem registro do canal e da data da devolutiva do resultado.",
    ])
    h2(d, "3.3. Natureza do serviço e segregação de funções")
    par(d, "3.3.1. A operação de campo (autocoleta pela própria usuária, apoiada por ACS e enfermagem) é de natureza comum e não constitui ato médico; o processamento laboratorial é atividade técnica especializada sob responsabilidade técnica própria.")
    par(d, "3.3.2. Os atos médicos especializados (colposcopia, biópsia, EZT e tratamento) não integram este objeto e permanecem na rede pública, observada a segregação de funções.")
    h2(d, "3.4. Vedação quanto a tecnologias não incorporadas")
    par(d, "3.4.1. Nos termos do art. 19-T da Lei nº 8.080/1990, é vedado o pagamento de tecnologia não incorporada ao SUS. A solução restringe-se a tecnologia já incorporada (SIGTAP 0202100251).")

    h1(d, "4. Estimativa das quantidades e dimensionamento do primeiro ciclo")
    par(d, "4.1. População-alvo de [ ___ ] mulheres de 25 a 64 anos. Dimensionamento do primeiro ciclo conforme a meta de cobertura e a adesão estimada:")
    tbl(d, ["Parâmetro", "Estimativa"], [
        ["População-alvo (25 a 64 anos)", "[ ___ ]"],
        ["Mulheres convocadas (busca ativa)", "~[ ___ ]"],
        ["Testes DNA-HPV realizados (adesão [ __ ]%)", "[ ___ ]"],
        ["Resultados HPV de alto risco positivos", "~[ ___ ]"],
        ["Lesões NIC2+ esperadas", "~[ ___ ]"],
        ["Cânceres evitados (estimativa)", "~[ ___ ]"],
    ])
    par(d, "4.2. Desdobramentos assistenciais esperados na rede (não integram o objeto; Manual DNA-HPV INCA/MS): citologia reflexa (MAC/SIA), colposcopia, biópsia e EZT (MAC/FAEC/OCI).")
    par(d, "4.3. As quantidades deverão ser confirmadas com o SISCAN, o e-SUS APS e a base populacional antes do início. O seguimento (colposcopia e EZT) deverá estar assegurado e pactuado em CIR/PPI previamente à ação.")

    h1(d, "5. Levantamento das soluções de mercado")
    par(d, "5.1. A solução integrada (kit de autocoleta, exame molecular DNA-HPV com genotipagem, logística, laudo e plataforma de seguimento) é ofertada por laboratórios e integradores no mercado nacional. Comparada à citologia, o teste molecular apresenta sensibilidade de 90 a 95% (ante 55 a 70%), intervalo de 5 anos após negativo e viabiliza a autocoleta, com redução de custo projetada no longo prazo (CONITEC).")
    par(d, "5.2. Justifica-se a escolha da solução integrada por DNA-HPV com autocoleta como a de melhor relação entre benefício assistencial, equidade e custo.")

    h1(d, "6. Estimativa do valor da contratação")
    par(d, "6.1. O valor deverá ser estimado por pesquisa de mercado própria (IN SEGES/ME nº 65/2021 — mínimo de três fontes, atualizada em até seis meses), parâmetro de aceitabilidade do preço.")
    par(d, "6.2. A estratificação de custos, quando apresentada, tem caráter de demonstração de exequibilidade (memória de cálculo) e não fundamenta o preço: a eventual margem é resultado, e não parâmetro. Por não se tratar de obra, não se aplica régua de BDI nem limite de lucro; o único parâmetro é a compatibilidade com o preço de mercado (Lei 14.133/2021, arts. 11 e 23).")
    par(d, "6.3. Para ciclo isolado, recomenda-se ancorar o valor unitário em pesquisa de mercado e prever revisão por volume em ciclos recorrentes.")

    h1(d, "7. Justificativa do não-parcelamento")
    par(d, "7.1. O objeto é solução integrada e indissociável (coleta, exame molecular, logística, laudo e seguimento), cujo fracionamento comprometeria a cadeia de custódia, a responsabilidade técnica do laudo e a rastreabilidade, sem prejuízo da segregação de funções.")

    h1(d, "8. Contratações correlatas e interdependentes")
    par(d, "8.1. A ação pressupõe a retaguarda assistencial da rede (colposcopia, biópsia e EZT), pactuada em CIR/PPI antes do início, financiada por MAC/FAEC/OCI e fora do objeto.")

    h1(d, "9. Base legal (conforme a rota escolhida)")
    h2(d, "9.1. Rota MROSC (Lei nº 13.019/2014)")
    al(d, [
        "Lei nº 13.019/2014 (MROSC) — parcerias com organizações da sociedade civil por Termo de Colaboração, precedido de chamamento público (art. 24) ou de sua dispensa/inexigibilidade justificada (arts. 30 e 31);",
        "Lei nº 14.133/2021 — aplicação subsidiária (planejamento, art. 18; pesquisa de preços, art. 23).",
    ])
    h2(d, "9.2. Rota Credenciamento (Lei nº 14.133/2021)")
    al(d, [
        "Lei nº 14.133/2021 — contratação por credenciamento (art. 79), com inexigibilidade de licitação por inviabilidade de competição (art. 74, IV); preços fixados pela Administração; planejamento (art. 18) e pesquisa de preços (art. 23).",
    ])
    h2(d, "9.3. Comuns a ambas as rotas")
    al(d, [
        "CF, art. 196, e Lei nº 8.080/1990 — dever do SUS na detecção precoce; Lei nº 11.664/2008 — ações de rastreamento do colo do útero;",
        "Portaria SECTICS/MS nº 3/2024 — incorporação do DNA-HPV ao SUS; SIGTAP 0202100251;",
        "Lei nº 8.080/1990, art. 19-T — vedação a tecnologias não incorporadas;",
        "Lei nº 13.709/2018 (LGPD) — dado pessoal sensível de saúde;",
        "Manual de apoio à implementação do teste DNA-HPV (INCA/MS) e PCDT.",
    ])

    h1(d, "10. Demonstração dos resultados pretendidos")
    al(d, [
        "Elevação da cobertura rumo à meta de 70%, priorizando as mulheres nunca rastreadas;",
        "Redução do intervalo entre coleta e conduta e qualificação do encaminhamento à Atenção Especializada;",
        "Seguimento longitudinal nominal, com indicadores auditáveis (Previne Brasil e metas 90-70-90);",
        "Fortalecimento da equidade no acesso ao rastreamento.",
    ])

    h1(d, "11. Providências prévias ao início")
    al(d, [
        "Garantia da capacidade de seguimento (colposcopia e EZT) pactuada em CIR/PPI;",
        "Cadastro das unidades e dos profissionais no CNES e habilitação de acesso ao SISCAN;",
        "Adequação à LGPD, com encarregado de dados e controles de segurança;",
        "Capacitação das equipes da Atenção Primária.",
    ])

    h1(d, "12. Impactos ambientais")
    par(d, "12.1. O manejo de resíduos observará o PGRSS (RDC ANVISA nº 222/2018), com segregação, acondicionamento e destinação adequados.")

    h1(d, "13. Posicionamento conclusivo sobre a viabilidade")
    par(d, "13.1. A contratação é tecnicamente viável, economicamente vantajosa frente à citologia e ao tratamento tardio, e legalmente enquadrável tanto na Lei nº 13.019/2014 (parceria com OSC, por Termo de Colaboração) quanto na Lei nº 14.133/2021 (credenciamento, com inexigibilidade por inviabilidade de competição — arts. 79 e 74, IV). Escolhida a rota, recomenda-se elaborar as peças correspondentes (Termo de Colaboração + Plano de Trabalho, ou Edital de credenciamento + Termo de Referência) e a pesquisa de preços, assegurada a capacidade de seguimento antes do início.")

    sign(d, [["[ NOME / MATRÍCULA / CARGO ]", "Responsável técnico pela elaboração"],
             ["Autoridade competente — [ Secretaria ]", ""]])
    salva(d, "ETP_RastreioColoUtero_DNA-HPV.docx")


# ===================== 2) Nota Técnica — serve às duas rotas =====================
def gerar_nota():
    d = novo()
    titulo(d, [BRASAO, (ORG, 12, False),
               ("NOTA TÉCNICA", 13, True),
               ("FUNDAMENTAÇÃO TÉCNICA, LEGAL E ORÇAMENTÁRIA — MUTIRÃO DE RASTREIO POR DNA-HPV (AUTOCOLETA)", 11, True)])
    tbl(d, ["Campo", "Conteúdo"], [
        ["Interessado", "[ Secretaria Municipal de Saúde de ___ / ___ ]"],
        ["Rota jurídica", "[ MROSC (Lei 13.019/2014) OU Credenciamento (Lei 14.133/2021) ]"],
        ["Fonte de recurso", "[ MAC / PAP / emenda / crédito / recurso próprio ]"],
        ["Elaboração", "Área técnica da unidade demandante — a ratificar"],
    ])
    disc(d)
    h1(d, "1. Fundamentação técnica")
    inc(d, [
        "O câncer de colo do útero é quase 100% evitável por rastreio (INCA; OMS); o DNA-HPV detecta 90–95% (citologia 55–70%) e é o teste primário recomendado pela OMS.",
        "Incorporado ao SUS pela Portaria SECTICS/MS nº 3/2024, SIGTAP 0202100251.",
        "A autocoleta tem aceitação ~100% e alcança quem nunca se rastreou (cobertura atual [ __ ]%).",
        "A CONITEC projeta -30% de custo no longo prazo substituindo a citologia.",
    ])
    h1(d, "2. Base legal")
    par(d, "2.1. Rota MROSC: Lei nº 13.019/2014, instrumentalizada por Termo de Colaboração, com Plano de Trabalho (art. 22) e prestação de contas (arts. 63–72).")
    par(d, "2.2. Rota Credenciamento: Lei nº 14.133/2021 (art. 79), com inexigibilidade por inviabilidade de competição (art. 74, IV) e preços fixados pela Administração.")
    par(d, "2.3. Comuns: CF art. 196 e Lei nº 8.080/1990; Lei nº 11.664/2008; Portaria SECTICS/MS nº 3/2024; Lei nº 13.709/2018 (LGPD).")
    h1(d, "3. Dimensionamento e metas")
    par(d, "3.1. População-alvo [ ___ ]. Ciclo: ~[ ___ ] convocadas, [ ___ ] testadas, ~[ ___ ] HPV+, ~[ ___ ] lesões NIC2+, ~[ ___ ] câncer(es) evitado(s). Seguimento assegurado antes do início (colposcopia pactuada em CIR/PPI).")
    h1(d, "4. Enquadramento orçamentário e financeiro")
    tbl(d, ["Componente", "Fonte", "Observação"], [
        ["Rastreio (teste DNA-HPV)", "[ fonte ] · SIGTAP 0202100251", "Valor a confirmar por pesquisa de mercado"],
        ["Citologia reflexa", "MAC / SIA", "Produção na rede/laboratório"],
        ["Colposcopia, biópsia, EZT", "MAC / FAEC / OCI", "Programado na rede"],
    ])
    h1(d, "5. Estratificação de custos — demonstração de exequibilidade")
    par(d, "5.1. A estratificação de custos (memória de cálculo) demonstra a exequibilidade e NÃO fundamenta o preço; a eventual margem é resultado, não parâmetro. O preço deve ser ancorado em pesquisa de mercado (IN SEGES/ME nº 65/2021). Em escala (volume anual), os custos fixos diluem-se e o custo unitário integrado cai, recomendando-se contratação por volume.")
    h1(d, "6. Conclusão")
    par(d, "6.1. O mutirão por DNA-HPV é tecnicamente adequado, legalmente enquadrável (MROSC ou credenciamento) e vantajoso frente à citologia e ao tratamento tardio. Recomenda-se assegurar o seguimento, instruir o processo com a documentação da rota escolhida, justificar o preço por pesquisa de mercado e registrar metas e indicadores auditáveis.")
    sign(d, [["Área Técnica — [ Secretaria ]", ""]])
    salva(d, "NotaTecnica_RastreioColoUtero_DNA-HPV.docx")


# ===================== 3) MROSC — Termo de Colaboração =====================
def gerar_termo_colab():
    d = novo()
    titulo(d, [BRASAO, (ORG, 12, False),
               ("TERMO DE COLABORAÇÃO Nº [ ___ / ______ ]", 13, True),
               ("LEI FEDERAL Nº 13.019/2014 (MROSC) — RASTREAMENTO DO CÂNCER DO COLO DO ÚTERO POR DNA-HPV COM AUTOCOLETA", 11, True)])
    disc(d)
    par(d, "Termo de Colaboração que entre si celebram o MUNICÍPIO, por meio da [ Secretaria Municipal de Saúde ], inscrita no CNPJ nº [ ___ ], neste ato representada por [ cargo / nome ], doravante denominada ADMINISTRAÇÃO PÚBLICA, e [ OSC — razão social ], inscrita no CNPJ nº [ ___ ], com sede em [ ___ ], neste ato representada por [ nome / cargo ], doravante denominada OSC, mediante as cláusulas seguintes, observada a Lei nº 13.019/2014 e, no que couber, a legislação municipal de regência.")
    cl = [
        ("Primeira — Do objeto", ["Constitui objeto deste Termo a execução, em regime de mútua cooperação, de ação concentrada e itinerante de rastreamento do câncer do colo do útero por teste molecular DNA-HPV com autocoleta, conforme o Plano de Trabalho que o integra independentemente de transcrição."]),
        ("Segunda — Do Plano de Trabalho", ["O Plano de Trabalho, aprovado pela Administração Pública, é parte integrante e indissociável deste Termo, dele constando metas, etapas, cronograma de execução e de desembolso, indicadores e memória de cálculo. Alterações observarão o art. 57 da Lei nº 13.019/2014."]),
        ("Terceira — Das obrigações da Administração Pública", ["I — exercer a regulação do acesso e integrar a ação à Atenção Primária; II — disponibilizar as unidades de coleta e o apoio das equipes; III — assegurar a capacidade de seguimento (colposcopia e EZT) na rede; IV — repassar os recursos conforme o cronograma de desembolso; V — designar o gestor da parceria e a comissão de monitoramento e avaliação; VI — analisar e manifestar-se sobre a prestação de contas."]),
        ("Quarta — Das obrigações da OSC", ["I — executar o objeto com observância das diretrizes do Ministério da Saúde e do INCA e da natureza do serviço definida no Plano de Trabalho; II — assegurar, por si e por seu parceiro técnico-laboratorial, o exame molecular com responsabilidade técnica própria, laudo em até 48 horas e cadeia de custódia; III — manter plataforma de rastreabilidade e seguimento em conformidade com a LGPD; IV — não cobrar, direta ou indiretamente, das usuárias; V — manter conta bancária específica e movimentação eletrônica dos recursos; VI — prestar contas na forma dos arts. 63 a 72; VII — manter a regularidade jurídica, fiscal e trabalhista durante toda a vigência."]),
        ("Quinta — Do valor e dos repasses", ["O valor global da parceria é de R$ [ ___ ], estimado por pesquisa de mercado (IN SEGES/ME nº 65/2021), repassado conforme o cronograma de desembolso do Plano de Trabalho, vedada a destinação a finalidade diversa da pactuada."]),
        ("Sexta — Da conta bancária específica e da aplicação financeira", ["Os recursos serão depositados e geridos em conta bancária específica e, enquanto não empregados, aplicados em poupança ou fundo de curto prazo, nos termos do art. 51 da Lei nº 13.019/2014, revertendo os rendimentos ao objeto."]),
        ("Sétima — Da vigência e das alterações", ["A vigência é de [ 12 (doze) meses ], contados da assinatura, prorrogável nos termos do art. 55. As alterações far-se-ão por termo aditivo, mediante proposta fundamentada e prévia manifestação técnica e jurídica."]),
        ("Oitava — Da contrapartida", ["[ Quando exigida ] A contrapartida da OSC será prestada na forma do Plano de Trabalho, observado o art. 35, § 1º, da Lei nº 13.019/2014."]),
        ("Nona — Do monitoramento, da avaliação e do gestor da parceria", ["A execução será acompanhada pelo gestor da parceria e pela comissão de monitoramento e avaliação, com base nos indicadores do Plano de Trabalho, podendo haver visita in loco e relatório técnico, nos termos dos arts. 58 a 62."]),
        ("Décima — Da prestação de contas", ["A prestação de contas observará os arts. 63 a 72, priorizado o controle de resultados, com relatório de execução do objeto e, quando exigido, de execução financeira."]),
        ("Décima Primeira — Dos bens remanescentes", ["Os bens eventualmente adquiridos com recursos da parceria terão destinação definida na forma do art. 36 e do Plano de Trabalho."]),
        ("Décima Segunda — Da proteção de dados pessoais (LGPD)", ["As partes observarão a Lei nº 13.709/2018 no tratamento de dados sensíveis de saúde, com base legal, finalidade específica, segurança da informação e encarregado indicado, vedado uso diverso do objeto."]),
        ("Décima Terceira — Das sanções", ["Pela execução em desacordo com o Plano de Trabalho, a Administração poderá aplicar as sanções do art. 73 da Lei nº 13.019/2014, assegurados o contraditório e a ampla defesa."]),
        ("Décima Quarta — Da denúncia e da rescisão", ["O Termo poderá ser denunciado a qualquer tempo e rescindido por descumprimento, mediante notificação prévia, nos termos do art. 42, XVI."]),
        ("Décima Quinta — Da publicidade", ["A eficácia fica condicionada à publicação do extrato no meio oficial de publicidade da Administração, nos termos do art. 38."]),
        ("Décima Sexta — Do foro", ["Fica eleito o foro da Comarca de [ ___ ] para dirimir as questões oriundas deste Termo. E, por estarem de acordo, firmam o presente em 2 (duas) vias de igual teor e forma."]),
    ]
    for t, ps in cl:
        h1(d, "Cláusula " + t)
        for p in ps:
            par(d, p)
    sign(d, [["[ Secretaria ]", "Administração Pública"],
             ["[ OSC ] — Organização da Sociedade Civil", "Representante legal"]])
    par(d, "Testemunhas: 1) ______________________________   2) ______________________________")
    salva(d, "MROSC_TermoColaboracao_RastreioColoUtero.docx")


# ===================== 4) MROSC — Plano de Trabalho =====================
def gerar_plano():
    d = novo()
    titulo(d, [BRASAO, (ORG, 12, False),
               ("PLANO DE TRABALHO", 13, True),
               ("PARCERIA — LEI FEDERAL Nº 13.019/2014 (MROSC) — RASTREAMENTO DO CÂNCER DO COLO DO ÚTERO POR DNA-HPV COM AUTOCOLETA", 11, True)])
    disc(d)
    h1(d, "1. Identificação das partes e do instrumento")
    tbl(d, ["Campo", "Conteúdo"], [
        ["Administração Pública parceira", "[ Secretaria Municipal de Saúde de ___ / ___ ]"],
        ["Organização da Sociedade Civil (OSC)", "[ OSC — razão social / CNPJ / endereço ]"],
        ["Parceiro técnico-laboratorial", "[ laboratório — razão social / CNPJ ] — biologia molecular, sob responsabilidade técnica própria"],
        ["Representante legal da OSC", "[ nome / CPF / cargo ]"],
        ["Instrumento", "Termo de Colaboração (art. 2º, VII, da Lei nº 13.019/2014)"],
        ["Vigência prevista", "[ 12 meses ] a partir da assinatura"],
    ])
    h1(d, "2. Objeto da parceria")
    par(d, "2.1. Execução, em regime de mútua cooperação, de ação concentrada e itinerante (mutirão) de rastreamento organizado do câncer do colo do útero por teste molecular DNA-HPV com autocoleta vaginal, integrada à Atenção Primária, com busca ativa nominal, retaguarda laboratorial, laudo digital e seguimento longitudinal das usuárias, sem cobrança direta ou indireta.")
    h1(d, "3. Descrição da realidade objeto da parceria e nexo de causalidade (art. 22, I)")
    par(d, "3.1. A cobertura em [ MUNICÍPIO ] situa-se na ordem de [ __ ]%, com concentração da não-cobertura em mulheres de maior vulnerabilidade. O modelo oportunístico não alcança quem nunca se rastreou, perpetuando mortalidade evitável.")
    par(d, "3.2. A parceria enfrenta essa realidade por mobilização comunitária, autocoleta e navegação de pacientes, em interesse público recíproco, elevando a cobertura rumo à meta de 70%. O nexo de causalidade assenta-se na maior sensibilidade do teste molecular e na aceitação quase universal da autocoleta.")
    h1(d, "4. Descrição de metas, etapas, cronograma e prazos (art. 22, II)")
    tbl(d, ["Fase", "Atividades", "Prazo", "Responsável"], [
        ["1. Planejamento", "Pactuação com a Secretaria, definição das unidades de coleta e meta por unidade; cadastro no SISCAN", "Mês 1", "OSC + Secretaria"],
        ["2. Capacitação", "Treinamento das equipes da APS (ACS/enfermagem) para a autocoleta e o registro SIGTAP 0202100251", "Mês 1 a 2", "OSC / laboratório"],
        ["3. Convocação", "Busca ativa das mulheres de 25 a 64 anos, priorizando as que nunca se rastrearam", "Mês 2 em diante", "Secretaria + ACS"],
        ["4. Autocoleta", "Entrega e retirada do coletor; a mulher realiza a autocoleta sem espéculo e sem mesa ginecológica", "Contínuo", "Unidades de saúde"],
        ["5. Análise laboratorial", "Processamento por PCR com genotipagem e laudo em até 48 horas", "Contínuo", "Laboratório executante"],
        ["6. Encaminhamento", "HPV+ de alto risco encaminhadas à colposcopia/tratamento na rede", "Contínuo", "Secretaria"],
        ["7. Monitoramento", "Plataforma/IA, painel de cobertura e indicadores (Previne Brasil / 90-70-90)", "Até 5 anos", "OSC + laboratório"],
    ])
    h1(d, "5. Forma de execução das atividades")
    al(d, [
        "A OSC coordena a mobilização comunitária, a logística dos kits e a navegação das pacientes, com apoio da APS;",
        "O laboratório executante realiza a biologia molecular, sob responsabilidade técnica própria, com laudo em até 48 horas e cadeia de custódia;",
        "A Administração Pública exerce a regulação do acesso e assegura o seguimento (colposcopia/EZT) na rede;",
        "Toda a operação é registrada em plataforma digital, em conformidade com a LGPD, com rastreabilidade e alerta de resultado alterado.",
    ])
    h1(d, "6. Parâmetros e indicadores de aferição (art. 22, III)")
    al(d, [
        "Número de mulheres testadas em relação à meta do ciclo;",
        "Percentual de cobertura alcançado (rumo a 70%);",
        "Tempo médio entre coleta e laudo (meta: até 48 horas);",
        "Percentual de HPV+ com seguimento efetivado;",
        "Percentual de mulheres nunca rastreadas alcançadas.",
    ])
    h1(d, "7. Previsão de receitas e de despesas — memória de cálculo")
    par(d, "7.1. Os valores têm caráter de demonstração de exequibilidade e devem ser confirmados por pesquisa de mercado (IN SEGES/ME nº 65/2021).")
    tbl(d, ["Componente", "Base", "Valor (R$)"], [
        ["Exame molecular + kit (laboratório)", "[ qtd ] × [ R$ ]", "[ ___ ]"],
        ["Logística e laudo em 48h", "[ qtd ] × [ R$ ]", "[ ___ ]"],
        ["Plataforma digital + monitoramento", "alocação do ciclo", "[ ___ ]"],
        ["Capacitação e suporte às equipes", "1 evento", "[ ___ ]"],
        ["Coordenação e gestão da ação", "equipe, ~1 mês", "[ ___ ]"],
        ["Tributos sobre repasse", "regime da OSC, a validar", "a validar"],
        ["Valor total da parceria", "—", "[ a confirmar por pesquisa de mercado ]"],
    ])
    h1(d, "8. Cronograma de desembolso")
    par(d, "8.1. Os repasses observarão [ parcela única / parcelas ] vinculadas ao cumprimento das metas e à prestação de contas, creditados em conta bancária específica, movimentada eletronicamente (arts. 51 e 53 da Lei nº 13.019/2014).")
    h1(d, "9. Contrapartida")
    par(d, "9.1. [ Quando exigida ] A contrapartida da OSC, se houver, será em bens e/ou serviços economicamente mensuráveis, vedada a exigência de contrapartida financeira quando não prevista no edital (art. 35, § 1º).")
    h1(d, "10. Prestação de contas")
    par(d, "10.1. A OSC prestará contas na forma dos arts. 63 a 72, com relatório de execução do objeto e, quando exigido, de execução financeira, submetidos ao gestor e à comissão de monitoramento e avaliação, priorizado o controle de resultados.")
    sign(d, [["[ OSC ] — Organização da Sociedade Civil", "Representante legal"],
             ["[ Secretaria ]", "Gestor da parceria"]])
    salva(d, "MROSC_PlanoDeTrabalho_RastreioColoUtero.docx")


# ===================== 5) Credenciamento — Edital =====================
def gerar_edital():
    d = novo()
    titulo(d, [BRASAO, (ORG, 12, False),
               ("EDITAL DE CHAMAMENTO PÚBLICO PARA CREDENCIAMENTO Nº [ ___ / ______ ]", 13, True),
               ("LEI Nº 14.133/2021 (ARTS. 79 E 74, IV) — RASTREAMENTO DO CÂNCER DO COLO DO ÚTERO POR DNA-HPV COM AUTOCOLETA", 11, True)])
    disc(d)
    h1(d, "1. Do objeto e da modalidade")
    par(d, "1.1. A [ Secretaria Municipal de Saúde ] torna público o chamamento permanente para o CREDENCIAMENTO de pessoas jurídicas interessadas em executar ação de rastreamento do câncer do colo do útero por teste molecular DNA-HPV com autocoleta, nos termos do Termo de Referência anexo, do art. 79 e da hipótese de inexigibilidade do art. 74, IV, da Lei nº 14.133/2021.")
    par(d, "1.2. O credenciamento não gera obrigação de contratação ou de demanda mínima; as contratações observarão a necessidade da Administração e a disponibilidade orçamentária, à fonte [ ___ ].")
    h1(d, "2. Das condições de participação")
    par(d, "2.1. Poderá se credenciar qualquer pessoa jurídica com objeto social compatível que atenda, cumulativamente, aos requisitos de habilitação e técnicos deste edital e de seu Termo de Referência, aceitando os preços fixados pela Administração.")
    par(d, "2.2. O chamamento é permanente: os pedidos podem ser apresentados a qualquer tempo durante a vigência e serão analisados por ordem de protocolo.")
    h1(d, "3. Da documentação de habilitação")
    al(d, [
        "Habilitação jurídica: ato constitutivo e representação legal;",
        "Regularidade fiscal, trabalhista e com o FGTS (certidões vigentes);",
        "Qualificação técnica: laboratório com inscrição regular no SCNES/CNES, licença sanitária para diagnóstico molecular e responsável técnico habilitado;",
        "Registro ANVISA do kit e do método; comprovação de capacidade de laudo em até 48 horas;",
        "Declaração de conformidade à LGPD e de não cobrança às usuárias;",
        "Declarações exigidas em lei (inexistência de fato impeditivo, trabalho de menor, etc.).",
    ])
    h1(d, "4. Dos requisitos técnicos do serviço")
    par(d, "4.1. Observar-se-ão integralmente os requisitos técnicos, sanitários e assistenciais definidos no Termo de Referência (kit ANVISA; genotipagem mínima de 28 tipos com identificação de 16/18; laudo em 48h; logística com cadeia de custódia; plataforma de seguimento em conformidade com a LGPD; PGRSS).")
    h1(d, "5. Da tabela de preços fixada pela Administração")
    par(d, "5.1. Os valores são fixados pela Administração, ancorados em pesquisa de mercado (IN SEGES/ME nº 65/2021), e idênticos para todas as credenciadas, afastando a disputa por preço (inviabilidade de competição):")
    tbl(d, ["Serviço", "Preço unitário fixado", "Referência do ciclo"], [
        ["Teste DNA-HPV com autocoleta (SIGTAP 0202100251)", "[ R$ ___ ]", "[ ___ ] testes = [ R$ ___ ]"],
    ])
    h1(d, "6. Do credenciamento e da distribuição impessoal das demandas")
    par(d, "6.1. Deferido o credenciamento, firma-se o termo de credenciamento. A distribuição das demandas observará critério objetivo e impessoal (rodízio ou rateio por capacidade e por território), publicado e auditável, vedada preferência injustificada.")
    h1(d, "7. Das obrigações da credenciada")
    al(d, [
        "Executar o objeto conforme o Termo de Referência, com gratuidade e sob a regulação do acesso da Secretaria;",
        "Registrar a produção no SISCAN e em BPA-I; manter a cadeia de custódia e a responsabilidade técnica do laudo;",
        "Manter, durante toda a vigência, as condições de habilitação e os requisitos técnicos e sanitários;",
        "Observar a LGPD e a segregação de funções (os atos médicos especializados permanecem na rede pública).",
    ])
    h1(d, "8. Da vigência e do descredenciamento")
    par(d, "8.1. O credenciamento vigora por [ 12 meses ], prorrogável na forma da lei. O descredenciamento ocorrerá a pedido ou por descumprimento, mediante processo com contraditório e ampla defesa.")
    h1(d, "9. Da fiscalização, da medição e do pagamento")
    par(d, "9.1. A execução será fiscalizada por gestor e fiscal designados; o pagamento observará a produção medida — teste realizado e com laudo liberado, ao preço fixado —, comprovado o registro no SISCAN.")
    h1(d, "10. Da proteção de dados (LGPD) e das sanções")
    par(d, "10.1. O tratamento de dados sensíveis de saúde observará a Lei nº 13.709/2018. O descumprimento sujeita a credenciada às sanções dos arts. 155 e seguintes da Lei nº 14.133/2021, assegurada a ampla defesa.")
    sign(d, [["Autoridade competente — [ Secretaria ]", "Ordenador(a) de despesa"],
             ["[ NOME / MATRÍCULA / CARGO ]", "Comissão de Contratação"]])
    salva(d, "Credenciamento_Edital_RastreioColoUtero.docx")


# ===================== 6) Credenciamento — Termo de Referência =====================
def gerar_tr():
    d = novo()
    titulo(d, [BRASAO, (ORG, 12, False),
               ("TERMO DE REFERÊNCIA", 13, True),
               ("CREDENCIAMENTO PARA RASTREAMENTO DO CÂNCER DO COLO DO ÚTERO POR DNA-HPV COM AUTOCOLETA — LEI Nº 14.133/2021", 11, True)])
    disc(d)
    h1(d, "1. Do objeto")
    par(d, "1.1. Contratação, por credenciamento (art. 79 da Lei nº 14.133/2021), de pessoa(s) jurídica(s) para a execução de ação concentrada e itinerante (mutirão) de rastreamento organizado do câncer do colo do útero por teste molecular DNA-HPV com autocoleta vaginal, compreendendo o fornecimento do kit, a análise laboratorial com genotipagem, a logística, o laudo digital e a plataforma de seguimento, integrada à Atenção Primária, sem cobrança direta ou indireta à usuária.")
    par(d, "1.2. O procedimento corresponde ao código SIGTAP 0202100251, tecnologia incorporada ao SUS pela Portaria SECTICS/MS nº 3/2024.")
    h1(d, "2. Da fundamentação e da justificativa do credenciamento")
    par(d, "2.1. A necessidade está demonstrada no ETP: cobertura estimada de [ __ ]% em [ MUNICÍPIO ], inferior à meta de 70%, com concentração da não-cobertura nas mulheres de maior vulnerabilidade.")
    par(d, "2.2. Adota-se o credenciamento porque o interesse público é mais bem atendido pela contratação simultânea de todos os interessados aptos (art. 79, I e II), com preços fixados pela Administração — hipótese de inviabilidade de competição e inexigibilidade de licitação (art. 74, IV). A seleção não se dá por disputa de preço, mas pela habilitação a parâmetros objetivos de qualidade.")
    h1(d, "3. Da descrição da solução como um todo")
    par(d, "3.1. A solução é integrada e indissociável (kit, exame molecular, logística, laudo e seguimento), preservando a cadeia de custódia, a responsabilidade técnica do laudo e a rastreabilidade, mantida a segregação de funções em relação aos atos especializados, que permanecem na rede pública.")
    h1(d, "4. Dos requisitos técnicos, sanitários e assistenciais")
    al(d, [
        "Kit de autocoleta vaginal com registro ativo na ANVISA e validade não inferior a 12 meses na entrega;",
        "Exame de biologia molecular com genotipagem de, no mínimo, 28 tipos de HPV, identificados ao menos os tipos 16 e 18;",
        "Laboratório com inscrição regular no SCNES/CNES, licença sanitária vigente e responsável técnico habilitado;",
        "Liberação do laudo em até 48 horas, com controle interno de amplificação por amostra;",
        "Logística de recolhimento e transporte do material biológico, com cadeia de custódia;",
        "Plataforma digital para cadastro, rastreabilidade, laudo digital, alerta de resultado alterado e seguimento por até 5 anos, em conformidade à LGPD;",
        "Atendimento gratuito, humanizado e sem discriminação, submetido à regulação do acesso pela Secretaria;",
        "PGRSS nos termos da RDC ANVISA nº 222/2018.",
    ])
    h2(d, "4.1. Natureza do serviço e segregação de funções")
    par(d, "4.1.1. A operação de campo (autocoleta pela própria usuária, apoiada por ACS e enfermagem) é de natureza comum e não constitui ato médico; o processamento laboratorial é atividade técnica especializada sob responsabilidade técnica própria. Os atos médicos especializados (colposcopia, biópsia, EZT e tratamento) não integram o objeto e permanecem na rede pública.")
    h1(d, "5. Do modelo de execução do objeto")
    par(d, "5.1. A demanda será distribuída entre as credenciadas por critério objetivo e impessoal (rodízio ou rateio por capacidade declarada e por território), vedada preferência injustificada. A Secretaria exerce a regulação do acesso, assegura o seguimento (colposcopia/EZT) pactuado em CIR/PPI antes do início e integra a ação à Atenção Primária.")
    h1(d, "6. Do modelo de gestão do contrato")
    par(d, "6.1. A execução será acompanhada por fiscal e gestor designados (arts. 117 e seguintes), com recebimento provisório e definitivo mediante conferência dos laudos liberados e do registro no SISCAN, e registro da produção em BPA-I.")
    h1(d, "7. Dos critérios de medição e pagamento")
    par(d, "7.1. A medição será por teste efetivamente realizado e com laudo liberado, ao preço unitário fixado pela Administração, mediante relatório de produção e comprovação do registro no SISCAN; não se remunera amostra sem laudo válido.")
    h1(d, "8. Da estimativa de preço e da forma de fixação")
    par(d, "8.1. O preço unitário será fixado pela Administração e ancorado em pesquisa de mercado (IN SEGES/ME nº 65/2021 — mínimo de três fontes, atualizada em até seis meses).")
    tbl(d, ["Item", "Quantidade de referência", "Preço unitário (fixado)", "Valor de referência"], [
        ["Teste DNA-HPV com autocoleta (SIGTAP 0202100251)", "[ ___ ]", "[ R$ ___ ]", "[ R$ ___ ]"],
    ])
    par(d, "8.2. A estratificação de custos, quando apresentada, é demonstração de exequibilidade (memória de cálculo) e não parâmetro do preço; o único parâmetro de aceitabilidade é a compatibilidade com o preço de mercado (arts. 11 e 23 da Lei nº 14.133/2021).")
    h1(d, "9. Das obrigações das partes")
    al(d, [
        "Da credenciada: executar o objeto conforme os requisitos; manter a regularidade jurídica, fiscal, trabalhista e sanitária na vigência; observar a LGPD; não cobrar das usuárias;",
        "Da Administração: fixar e publicar os preços; distribuir as demandas de forma impessoal; regular o acesso; assegurar o seguimento na rede; fiscalizar e pagar pela produção medida.",
    ])
    h1(d, "10. Da proteção de dados pessoais (LGPD)")
    par(d, "10.1. O tratamento de dados sensíveis de saúde observará a Lei nº 13.709/2018, com base legal e finalidade específicas, segurança da informação, controle de acesso por perfil, logs e encarregado indicado, vedado uso diverso do objeto.")
    h1(d, "11. Das sanções")
    par(d, "11.1. O descumprimento sujeita a credenciada às sanções dos arts. 155 e seguintes da Lei nº 14.133/2021, assegurados o contraditório e a ampla defesa.")
    sign(d, [["[ NOME / MATRÍCULA / CARGO ]", "Responsável técnico pela elaboração"],
             ["Autoridade competente — [ Secretaria ]", ""]])
    salva(d, "Credenciamento_TermoReferencia_RastreioColoUtero.docx")


if __name__ == "__main__":
    gerar_etp()
    gerar_nota()
    gerar_termo_colab()
    gerar_plano()
    gerar_edital()
    gerar_tr()
    print("Concluído: 6 modelos neutros em", BASE)
