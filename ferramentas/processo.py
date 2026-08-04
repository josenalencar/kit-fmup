# -*- coding: utf-8 -*-
"""Confere os anexos do email de admissão a provas, antes de o enviar."""
import re

import fitz

LIMITE_EMAIL_MB = 25

# (código, o que é, padrões no nome do ficheiro, precisa de assinatura)
DOCUMENTOS = [
    ("A", "A tese", [r"\btese\b", r"^a\b"], False),
    ("A1", "Requerimento de admissão a provas", [r"\ba1\b", r"admiss"], True),
    # \borient exige limite de palavra: assim "Coorientadora" não entra aqui
    ("A2", "Parecer do orientador", [r"\ba2\b", r"parecer.*\borient"], True),
    ("A3", "Parecer do coorientador", [r"\ba3\b", r"parecer.*coorient"], True),
    ("A4", "Declaração de divulgação", [r"\ba4\b", r"declara"], True),
    ("B", "Curriculum vitae", [r"\bb\b", r"curric", r"\bcv\b"], False),
    ("C", "Resumo e abstract", [r"\bc\b", r"resumo", r"abstract"], False),
    ("D", "Artigo(s) do critério D", [r"\bd1?\b", r"artigo"], False),
    ("G", "Documento de identificação",
     [r"\bg\b", r"identifica", r"passaporte", r"cart.o de cidad"], False),
]

SUSPEITOS = ["preenchido", "sem assinatura", "por assinar", "rascunho", "draft"]
ASSINADOS = ["assinado", "assinada", "signed"]


def _encontrar(nomes, padroes):
    achados = []
    for f in nomes:
        base = f.lower()
        if any(re.search(p, base) for p in padroes):
            achados.append(f)
    return achados


def verificar(ficheiros):
    """`ficheiros` é uma lista de (nome, bytes). Devolve o relatório."""
    nomes = sorted(n for n, _ in ficheiros)
    conteudo = dict(ficheiros)

    documentos, problemas, avisos, usados = [], [], [], set()
    for codigo, nome, padroes, precisa in DOCUMENTOS:
        achados = _encontrar(nomes, padroes)
        if not achados:
            documentos.append(dict(codigo=codigo, nome=nome, estado="falta",
                                   ficheiro=None, extras=[]))
            problemas.append(f"{codigo} — {nome}: não encontrei nenhum ficheiro")
            continue
        usados.update(achados)
        assinados = [a for a in achados if any(m in a.lower() for m in ASSINADOS)]
        escolhido = assinados[0] if assinados else achados[0]
        estado = "ok"
        if precisa:
            tem = any(m in escolhido.lower() for m in ASSINADOS)
            suspeito = any(m in escolhido.lower() for m in SUSPEITOS)
            if suspeito and not tem:
                estado = "assinar"
                problemas.append(f"{codigo} — {nome}: «{escolhido}» parece a versão "
                                 f"por assinar")
            elif not tem:
                estado = "confirmar"
                avisos.append(f"{codigo} — {nome}: «{escolhido}» não diz ASSINADO no "
                              f"nome; confirme que é a versão assinada")
        documentos.append(dict(codigo=codigo, nome=nome, estado=estado,
                               ficheiro=escolhido,
                               extras=[a for a in achados if a != escolhido]))

    # campos por preencher dentro dos PDF
    por_preencher = []
    for nome in nomes:
        if not nome.lower().endswith(".pdf"):
            continue
        try:
            doc = fitz.open(stream=conteudo[nome], filetype="pdf")
        except Exception as e:                       # ficheiro corrompido
            problemas.append(f"{nome}: o ficheiro não abre ({e})")
            continue
        paginas = [i for i, pag in enumerate(doc, 1)
                   if "A PREENCHER" in pag.get_text().upper()
                   or "CLICK OR TAP" in pag.get_text().upper()]
        if paginas:
            por_preencher.append((nome, paginas))
            problemas.append(f"{nome}: ainda tem campos por preencher")
        doc.close()

    total = sum(len(b) for _, b in ficheiros)
    total_mb = round(total / 1024 / 1024, 1)
    if total_mb > LIMITE_EMAIL_MB:
        avisos.append(f"os anexos somam {total_mb} MB, acima do limite de "
                      f"{LIMITE_EMAIL_MB} MB do Gmail")

    return dict(
        documentos=documentos,
        sobra=[f for f in nomes if f not in usados],
        por_preencher=por_preencher,
        total_mb=total_mb,
        cabe_no_email=total_mb <= LIMITE_EMAIL_MB,
        problemas=problemas,
        avisos=avisos,
        tamanhos={n: round(len(b) / 1024 / 1024, 1) for n, b in ficheiros},
    )
