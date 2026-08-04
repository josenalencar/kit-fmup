# -*- coding: utf-8 -*-
"""Gera a capa da tese (contracapa + lombada + capa) a partir do modelo da U.Porto.

O texto da lombada é ajustado e depois VERIFICADO: a página é rasterizada, a
tinta é medida, e o desenho repete-se até o bloco estar centrado e com pelo
menos 2 mm livres até cada vinco. É a lição que custou três provas de gráfica.
"""
import base64

import fitz

from .logos import LOGO_FMUP, LOGO_UPORTO_H, LOGO_UPORTO_V

MM = 72 / 25.4

PANEL_W, PAGE_H = 210.0, 297.0

FRENTE = dict(
    grau=(8.7, 31.1, 24),
    ano=(20.0, 31.1, 11),
    logo_fmup=(83.8, 19.8, 50.2, 24.1),
    titulo=(30.1, 176.8, 30, 12.8, 150.0),
    bloco=(30.1, 193.5, 9.1, 3.8),
)
TRAS = dict(
    logo_uporto=(25.0, 20.4, 45.2, 9.5),
    universidade=(151.65, 37.1, 10.1),
)
LOMBADA = dict(
    barra_y=(19.98, 29.89),
    barra_sobra=5.0,
    ciclo=(20.4, 25.0, 34.6, 39.3, 11),
    logo_uporto=(65.2, 7.58, 36.0),
    titulo=(131.5, 209.5, 12, 1.205),
    autor=(249.0, 285.0, 9.1, 1.205),
    folga_min=2.5,
)
AMARELO = (255 / 255, 241 / 255, 1 / 255)


def _r(x0, y0, x1, y1):
    return fitz.Rect(x0 * MM, y0 * MM, x1 * MM, y1 * MM)


def _largura(texto, fonte, corpo):
    return fitz.get_text_length(texto, fontname=fonte, fontsize=corpo) / MM


def _quebrar(texto, fonte, corpo, maximo):
    linhas, atual = [], ""
    for palavra in texto.split():
        tentativa = (atual + " " + palavra).strip()
        if atual and _largura(tentativa, fonte, corpo) > maximo:
            linhas.append(atual)
            atual = palavra
        else:
            atual = tentativa
    if atual:
        linhas.append(atual)
    return linhas


def _altura_maiuscula(corpo):
    return corpo * 0.717 * 25.4 / 72


def _ajustar(texto, fonte, corpo0, fator, comprimento, largura_util):
    """Reduz o corpo até o bloco caber na lombada com folga."""
    corpo = corpo0
    while corpo > 5.0:
        linhas = _quebrar(texto, fonte, corpo, comprimento)
        entrelinha = corpo * fator * 25.4 / 72
        bloco = (len(linhas) - 1) * entrelinha + _altura_maiuscula(corpo)
        if bloco <= largura_util:
            return linhas, corpo, entrelinha, bloco
        corpo -= 0.25
    raise ValueError("O título é demasiado longo para esta lombada. "
                     "Aumente a largura da lombada ou encurte o título.")


def _desenhar(dados, correcao, folga):
    lombada = float(dados["lombada_mm"])
    largura_folha = PANEL_W * 2 + lombada
    vinco_tras, vinco_frente = PANEL_W, PANEL_W + lombada
    centro = PANEL_W + lombada / 2

    doc = fitz.open()
    page = doc.new_page(width=largura_folha * MM, height=PAGE_H * MM)
    page.draw_rect(page.rect, color=None, fill=(1, 1, 1))

    def escrever(x, base, texto, fonte, corpo):
        page.insert_text((x * MM, base * MM), texto, fontname=fonte, fontsize=corpo)

    def imagem(b64, x, y, larg, alt):
        page.insert_image(_r(x, y, x + larg, y + alt), stream=base64.b64decode(b64))

    # contracapa
    x, y, w, h = TRAS["logo_uporto"]
    imagem(LOGO_UPORTO_H, x, y, w, h)
    xu, base, corpo = TRAS["universidade"]
    escrever(xu, base, "UNIVERSIDADE DO PORTO", "helv", corpo)

    # barra amarela, contínua sobre os dois vincos
    y0, y1 = LOMBADA["barra_y"]
    sobra = LOMBADA["barra_sobra"]
    page.draw_rect(_r(vinco_tras - sobra, y0, vinco_frente + sobra, y1),
                   color=None, fill=AMARELO)

    # capa da frente
    xg, baseg, corpog = FRENTE["grau"]
    escrever(vinco_frente + xg, baseg, dados["grau"], "helv", corpog)
    xa, basea, corpoa = FRENTE["ano"]
    escrever(vinco_frente + xa, basea, str(dados["ano"]), "helv", corpoa)

    x, y, w, h = FRENTE["logo_fmup"]
    imagem(LOGO_FMUP, vinco_frente + x, y, w, h)

    xt, base_ult, corpo_t, entre_t, max_t = FRENTE["titulo"]
    proporcao = entre_t / corpo_t
    linhas = _quebrar(dados["titulo"], "hebo", corpo_t, max_t)
    while len(linhas) > 5 and corpo_t > 18:
        corpo_t -= 1
        linhas = _quebrar(dados["titulo"], "hebo", corpo_t, max_t)
    entre_t = corpo_t * proporcao
    for i, linha in enumerate(linhas):
        base = base_ult - (len(linhas) - 1 - i) * entre_t
        escrever(vinco_frente + xt, base, linha, "hebo", corpo_t)

    xb, base_b, corpo_b, entre_b = FRENTE["bloco"]
    bloco = [dados["autor"].upper(), dados["linha_tese"],
             dados["linha_faculdade"], dados["curso"].upper()]
    for i, linha in enumerate(bloco):
        escrever(vinco_frente + xb, base_b + i * entre_b, linha, "helv", corpo_b)

    # lombada: ciclo / faculdade / ano
    b1, b2, b3, b4, corpo_c = LOMBADA["ciclo"]
    for base, texto in ((b1, dados["ciclo"]), (b2, "CICLO"),
                        (b3, dados["sigla"]), (b4, str(dados["ano"]))):
        escrever(centro - _largura(texto, "helv", corpo_c) / 2, base, texto,
                 "helv", corpo_c)

    yl, wl, hl = LOMBADA["logo_uporto"]
    imagem(LOGO_UPORTO_V, centro - wl / 2, yl, wl, hl)

    # lombada: título e autor, com o corpo ajustado
    util = lombada - 2 * folga
    info = {}
    for chave, texto, fonte in (("titulo", dados["titulo"], "hebo"),
                                ("autor", dados["autor"].upper(), "helv")):
        y_ini, y_lim, corpo0, fator = LOMBADA[chave]
        linhas, corpo, entre, bloco_w = _ajustar(
            texto, fonte, corpo0, fator, y_lim - y_ini, util)
        x_prim = (centro + bloco_w / 2 - _altura_maiuscula(corpo)
                  + correcao.get(chave, 0.0))
        for i, linha in enumerate(linhas):
            page.insert_text(((x_prim - i * entre) * MM, y_ini * MM), linha,
                             fontname=fonte, fontsize=corpo, rotate=270)
        info[chave] = dict(corpo=corpo, linhas=len(linhas))

    return doc, info, (vinco_tras, vinco_frente, centro, largura_folha)


def _medir(doc, faixas, vinco_tras, vinco_frente):
    pm = doc[0].get_pixmap(dpi=300)
    ppmm = 300 / 25.4
    larg, alt, n, dados = pm.width, pm.height, pm.n, pm.samples
    saida = {}
    for nome, (ya, yb) in faixas.items():
        esq = dir_ = None
        for xi in range(int(vinco_tras * ppmm), int(vinco_frente * ppmm)):
            for yi in range(int(ya * ppmm), min(int(yb * ppmm), alt)):
                p = (yi * larg + xi) * n
                if dados[p] + dados[p + 1] + dados[p + 2] < 330:
                    esq = xi if esq is None else esq
                    dir_ = xi
                    break
        if esq is not None:
            saida[nome] = (esq / ppmm, dir_ / ppmm)
    return saida


def gerar(titulo, autor, ano=2026, curso="BIOÉTICA", lombada_mm=17,
          grau="D", ciclo="3.º", sigla="FMUP",
          linha_tese="TESE DE DOUTORAMENTO APRESENTADA",
          linha_faculdade="À FACULDADE DE MEDICINA DA UNIVERSIDADE DO PORTO EM"):
    """Devolve (bytes do PDF, relatório).

    O relatório traz as folgas medidas em milímetros, para se poder confirmar
    que o texto da lombada não vai parar em cima do vinco.
    """
    titulo, autor = titulo.strip(), autor.strip()
    if not titulo or not autor:
        raise ValueError("Falta o título ou o nome do autor.")

    dados = dict(titulo=titulo, autor=autor, ano=ano, curso=curso,
                 lombada_mm=float(lombada_mm), grau=grau, ciclo=ciclo,
                 sigla=sigla, linha_tese=linha_tese,
                 linha_faculdade=linha_faculdade)

    faixas = {"titulo": (LOMBADA["titulo"][0] - 2, LOMBADA["titulo"][1] + 2),
              "autor": (LOMBADA["autor"][0] - 2, LOMBADA["autor"][1] + 2)}
    folga, correcao = LOMBADA["folga_min"], {}
    doc = info = None
    for _ in range(6):
        doc, info, (vt, vf, centro, folha) = _desenhar(dados, correcao, folga)
        medido = _medir(doc, faixas, vt, vf)
        correcao = {k: correcao.get(k, 0.0) + centro - (a + b) / 2
                    for k, (a, b) in medido.items()}
        pior = min([min(a - vt, vf - b) for a, b in medido.values()] or [9])
        desvio = max([abs(centro - (a + b) / 2) for a, b in medido.values()] or [0])
        if pior >= 2.0 and desvio <= 0.05:
            break
        if pior < 2.0:
            folga += 0.4
    doc, info, (vt, vf, centro, folha) = _desenhar(dados, correcao, folga)
    medido = _medir(doc, faixas, vt, vf)

    relatorio = dict(
        folha_mm=(folha, PAGE_H),
        lombada=(vt, vf, float(lombada_mm)),
        elementos={
            nome: dict(corpo=round(info[nome]["corpo"], 2),
                       linhas=info[nome]["linhas"],
                       folga_esq=round(medido[nome][0] - vt, 2),
                       folga_dir=round(vf - medido[nome][1], 2))
            for nome in ("titulo", "autor") if nome in medido
        },
    )
    return doc.tobytes(garbage=4, deflate=True), relatorio


def previsualizar(pdf_bytes, dpi=90):
    """PNG da capa, para mostrar no ecrã."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return doc[0].get_pixmap(dpi=dpi).tobytes("png")
