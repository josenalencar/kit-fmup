# -*- coding: utf-8 -*-
"""Preenche os quatro impressos da FMUP a partir de um dicionário de dados.

O que estiver por preencher sai a VERMELHO, com a marca [A PREENCHER], e vem
listado à parte. Assim ninguém assina um formulário com campos vazios.

Adaptado do programa de linha de comandos: aqui não escreve ficheiros, devolve
os bytes de cada documento.
"""
import io
import os
import unicodedata

import docx
import fitz
from docx.oxml.ns import qn

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
W14 = '{http://schemas.microsoft.com/office/word/2010/wordml}'
BRANCOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'formularios_em_branco')
RED = (0.80, 0.10, 0.10)
MARK = '[A PREENCHER]'
NAO_APLICAVEL = 'Não aplicável / Not applicable'


def _simplificar(nome):
    sem = unicodedata.normalize('NFKD', nome)
    sem = ''.join(c for c in sem if not unicodedata.combining(c))
    return ''.join(c for c in sem.lower() if c.isalnum() or c == '.')


def _branco(nome):
    """Lê o formulário oficial em branco, tolerando acentos estragados."""
    alvo = _simplificar(nome)
    candidatos = [os.path.join(BRANCOS, nome)]
    if os.path.isdir(BRANCOS):
        candidatos += [os.path.join(BRANCOS, f) for f in sorted(os.listdir(BRANCOS))
                       if _simplificar(f) == alvo]
    for p in candidatos:
        if os.path.exists(p):
            with open(p, 'rb') as fh:
                return fh.read()
    raise FileNotFoundError(f'Falta o formulário em branco: {nome}')


class _Estado:
    """Guarda o que ficou por preencher durante um preenchimento."""

    def __init__(self):
        self.falta = []

    def val(self, v, label=None):
        if v is None or (isinstance(v, str) and not v.strip()):
            self.falta.append(label or 'campo por identificar')
            return MARK, True
        return v, False

# ───────────────────────────────────────────── 1. admission form (docx)
def _docx(D, est):
    val = est.val
    d = docx.Document(io.BytesIO(_branco(
        'Impressos_admissao_provas_doutoramento_atualizado_2023__versao_mais_atual_ (4).docx')))

    def sdts_of(p):
        return [s for s in p._p.iter(W + 'sdt')]

    def set_text(sdt, text, red=False):
        if text is None:
            text, red = MARK, True
        content = sdt.find(W + 'sdtContent')
        # Inline controls hold w:r directly; block-level ones wrap it in a w:p.
        runs = content.findall(W + 'r')
        if not runs:
            para = content.find(W + 'p')
            if para is not None:
                content, runs = para, para.findall(W + 'r')
        model = runs[0] if runs else None
        for r in runs[1:]:
            content.remove(r)
        if model is None:
            model = content.makeelement(W + 'r', {})
            content.append(model)
        for kid in list(model):
            if kid.tag != W + 'rPr':
                model.remove(kid)
        rPr = model.find(W + 'rPr')
        if rPr is None:
            rPr = model.makeelement(W + 'rPr', {})
            model.insert(0, rPr)
        # The template styles every control as "Texto do Espaço Reservado",
        # which prints grey. Answers must read as answers, not as prompts.
        for tag in ('w:rStyle', 'w:color', 'w:b'):
            old = rPr.find(qn(tag))
            if old is not None:
                rPr.remove(old)
        c = rPr.makeelement(W + 'color', {})
        c.set(qn('w:val'), 'C00000' if red else '000000')
        rPr.append(c)
        if red:
            rPr.append(rPr.makeelement(W + 'b', {}))
        t = model.makeelement(W + 't', {})
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        t.text = text
        model.append(t)

    def tick(sdt, on=True):
        pr = sdt.find(W + 'sdtPr')
        cb = pr.find(W14 + 'checkbox')
        chk = cb.find(W14 + 'checked')
        chk.set(W14 + 'val', '1' if on else '0')
        state = cb.find(W14 + ('checkedState' if on else 'uncheckedState'))
        char = chr(int(state.get(W14 + 'val'), 16))
        content = sdt.find(W + 'sdtContent')
        for t in content.iter(W + 't'):
            t.text = char

    def put(p, value, label):
        v, red = val(value, label)
        set_text(sdts_of(p)[0], v, red)

    ps = d.paragraphs
    by = {}
    for p in ps:
        if sdts_of(p):
            by.setdefault(p.text.split('Click')[0].strip(), []).append(p)

    put(ps[10], D.student['nome'], 'Nome do estudante')
    g = sdts_of(ps[11])
    tick(g[0], D.student['grau'] == 'Licenciado')
    tick(g[1], D.student['grau'] == 'Mestre')
    put(ps[12], D.student['id_doc'], 'B.I./C.C./passaporte do estudante')
    put(ps[13], D.student['id_validade'], 'Validade do documento de identificação')
    put(ps[14], D.student['email'], 'Email do estudante')
    put(ps[17], D.phd['programa'], 'Programa doutoral')
    put(ps[18], D.phd['ano_curricular'], 'Ano curricular')
    put(ps[19], D.phd['area'], 'Área científica')

    for base, who, who_label in ((21, D.orientador, 'orientador'),
                                 (28, D.coorientador, 'coorientadora'),
                                 (35, D.coorientador2, 'coorientador 2')):
        put(ps[base + 0], who['nome'], f'Nome do/a {who_label}')
        put(ps[base + 1], who['grau'], f'Grau do/a {who_label}')
        put(ps[base + 2], who['categoria'], f'Categoria da {who_label}')
        put(ps[base + 3], who['instituicao'], f'Instituição do/a {who_label}')
        put(ps[base + 4], who['email'], f'Email do/a {who_label}')
        put(ps[base + 5], who['id_doc'], f'B.I./C.C. do/a {who_label}')

    put(ps[42], D.phd['titulo'], 'Título da tese')
    put(ps[47], D.data_submissao, 'Data de submissão')

    # The reception date belongs to the Academic Office, not to the candidate:
    # blank it so the template's "Click or tap to enter a date." does not print.
    set_text(sdts_of(ps[2])[0], '')

    # Six controls sit at body level, outside any paragraph: keywords 2-4, the
    # Q1 article line, and the two Q2/Q3 article lines, in document order.
    body = d.element.body
    block = [el for el in body if el.tag == W + 'sdt']
    if len(block) != 6:
        raise RuntimeError(f'expected 6 block-level controls, found {len(block)}')
    kw2_4, q1_line, q2q3_lines = block[:3], block[3], block[4:]

    keywords = D.phd['palavras_chave']
    if isinstance(keywords, str):                  # tolerate the old single-string form
        keywords = [k.strip() for k in keywords.split(';')]
    put(ps[45], keywords[0], 'Palavra-chave 1')
    for i, (sdt, kw) in enumerate(zip(kw2_4, list(keywords[1:]) + [''] * 3)):
        if kw is None:
            est.falta.append(f'Palavra-chave {i + 2}')
        set_text(sdt, kw)

    if D.anexos['D_artigo_q1'] and D.artigo_q1 is None:
        est.falta.append('Artigo Q1 do critério D')
    set_text(q1_line, D.artigo_q1 if D.anexos['D_artigo_q1'] else NAO_APLICAVEL)
    for i, (sdt, art) in enumerate(zip(q2q3_lines,
                                       list(D.artigos_q2q3) + [NAO_APLICAVEL] * 2)):
        if art is None and D.anexos['D_dois_artigos']:
            est.falta.append(f'Artigo {i + 1} do critério D')
        set_text(sdt, art)

    boxes = [s for p in ps[55:66] for s in sdts_of(p)]
    order = ['A_tese', 'B_cv', 'C_resumo', 'D_artigo_q1', 'D_dois_artigos',
             'E_pareceres', 'F_declaracao', 'G_documento_id', 'H_tres_teses']
    for s, k in zip(boxes, order):
        tick(s, D.anexos[k])
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


# ───────────────────────────────────────────── 2. Declaração (overlay)
def _declaracao(D, est):
    val = est.val
    doc = fitz.open(stream=_branco('Declaracao.pdf'), filetype='pdf')
    p = doc[0]

    def txt(x, y, s, label=None, size=9, width=None):
        v, red = val(s, label)
        col = RED if red else (0, 0, 0)
        if width:
            rect = fitz.Rect(x, y - 2, x + width, y + 40)
            p.insert_textbox(rect, v, fontsize=size, fontname='helv', color=col)
        else:
            p.insert_text((x, y), v, fontsize=size, fontname='helv', color=col)

    def check(x, y):
        # ZapfDingbats maps U+2713 to a circled numeral, so use a plain bold X
        p.insert_text((x + 2.8, y + 11.2), 'X', fontsize=12,
                      fontname='hebo', color=(0, 0, 0))

    txt(89, 191, D.student['nome'], 'Nome do estudante', 10)
    txt(89, 238, D.student.get('id_doc_curto') or D.student['id_doc'],
        'B.I./C.C./passaporte do estudante', 8.5)
    txt(206, 238, D.student['telemovel'], 'Telemóvel', 8.5)
    txt(321, 238, D.student['email'], 'Email do estudante', 9)
    txt(89, 269, D.student['numero_uporto'], 'Número de estudante U.PORTO', 9)
    txt(321, 314, D.student['data_conclusao'], 'Data de conclusão', 9)
    txt(89, 346, D.phd['area'], 'Área científica', 10)
    txt(89, 394, D.phd['titulo'], 'Título da tese', 9, width=418)
    orientadores = None
    if D.orientador['nome'] and D.coorientador['nome']:
        orientadores = (f"{D.orientador['grau']} {D.orientador['nome']} (orientador); "
                        f"{D.coorientador['grau']} {D.coorientador['nome']} (coorientador)")
    txt(89, 442, orientadores,
        'Nomes dos orientadores', 8.5, width=418)
    txt(89, 676, D.declaracao['observacoes'], 'Observações da Declaração', 8, width=418)
    txt(89, 730, D.data_submissao, 'Data de submissão', 9)

    if D.declaracao['doutoramento']:   check(85.0, 304.5)
    if D.declaracao['mestrado']:       check(201.3, 304.5)
    if D.declaracao['tipo_total']:     check(85.0, 614.2)
    if D.declaracao['tipo_parcial']:   check(85.0, 631.2)
    if D.declaracao['ambito_uporto']:  check(187.7, 614.9)
    if D.declaracao['ambito_geral']:   check(187.7, 631.9)
    if D.declaracao['formato_papel']:  check(317.5, 614.9)
    if D.declaracao['formato_digital']:check(317.5, 631.9)

    return doc.tobytes()


def _parecer(D, est, role, who):
    """Fill a Parecer by locating its ruled blanks, which sit at different x
    offsets on the Orientador and Coorientador variants."""
    val = est.val
    doc = fitz.open(stream=_branco(f'Parecer {role}.pdf'), filetype='pdf')
    p = doc[0]

    blanks = {}
    for b in p.get_text('dict')['blocks']:
        for line in b.get('lines', []):
            for s in line['spans']:
                if set(s['text'].strip()) <= {'_', '/'} and '_' in s['text']:
                    blanks.setdefault(round(s['bbox'][1]), s['bbox'])
    ys = sorted(blanks)
    if len(ys) < 7:
        raise RuntimeError(f'{role}: found only {len(ys)} ruled blanks')
    nome, ident, aluno, prog, tit1, tit2, dt = (blanks[y] for y in ys[:7])

    def put(bbox, s, label=None, size=10, dx=4.0):
        v, red = val(s, label)
        p.insert_text((bbox[0] + dx, bbox[3] - 3.0), v, fontsize=size,
                      fontname='helv', color=RED if red else (0, 0, 0))

    put(nome,  who['nome'], f'Nome do/a {role.lower()}', 10)
    put(ident, who['id_doc'], f'Documento de identificação do/a {role.lower()}', 9)
    put(aluno, D.student['nome'], 'Nome do estudante', 9)
    put(prog,  D.phd['programa'], 'Programa doutoral', 10)
    # O título ocupa duas linhas no impresso. Parte-se no último espaço que
    # ainda caiba na primeira; se for curto, a segunda linha fica vazia.
    title = D.phd['titulo']
    if title is None:
        est.falta.append('Título da tese')
        put(tit1, MARK, None, 9.5)
    elif len(title) <= 88:
        put(tit1, title, 'Título da tese', 9.5)
    else:
        cut = title.rfind(' ', 0, 88)
        cut = cut if cut > 0 else 88
        put(tit1, title[:cut], 'Título da tese', 9.5)
        put(tit2, title[cut:].strip(), 'Título da tese', 9.5)
    if D.data_submissao is None:
        est.falta.append('Data de submissão')
        put(dt, MARK, None, 8)
    else:
        dd, mm, yy = D.data_submissao.split('/')
        x0, y1 = dt[0], dt[3]
        for off, part in ((5, dd), (35, mm), (65, yy)):
            p.insert_text((x0 + off, y1 - 3.0), part, fontsize=10, fontname='helv')
    return doc.tobytes()


def preencher(D):
    """Devolve ({nome do ficheiro: bytes}, [campos por preencher])."""
    est = _Estado()
    saida = {
        'A1 - Admissao as provas - PREENCHIDO.docx': _docx(D, est),
        'A2 - Parecer do Orientador - PREENCHIDO.pdf':
            _parecer(D, est, 'Orientador', D.orientador),
        'A3 - Parecer do Coorientador - PREENCHIDO.pdf':
            _parecer(D, est, 'Coorientador', D.coorientador),
        'A4 - Declaracao de divulgacao - PREENCHIDO.pdf': _declaracao(D, est),
    }
    vistos, unicos = set(), []
    for m in est.falta:
        if m not in vistos:
            vistos.add(m)
            unicos.append(m)
    return saida, unicos
