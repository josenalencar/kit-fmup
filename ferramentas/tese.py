# -*- coding: utf-8 -*-
"""Analisa o PDF da tese antes de ir para a gráfica.

Responde ao que a gráfica vai perguntar: quantas páginas, se são todas A4,
quantas têm cor a sério, se as fontes estão incorporadas, e que espessura vai
ter a lombada.
"""
import fitz

A4 = (210.0, 297.0)
TOLERANCIA_MM = 1.0
LIMIAR_COR = 18
DPI_MINIMO = 150

# espessura de uma folha, em mm, por gramagem — papel offset corrente
FOLHA_MM = {80: 0.104, 90: 0.115, 100: 0.128, 120: 0.152}


def _mm(pontos):
    return pontos / 72 * 25.4


def resumir(numeros):
    """[1,2,3,7,8] -> '1-3, 7-8'"""
    numeros = sorted(set(numeros))
    saida, i = [], 0
    while i < len(numeros):
        j = i
        while j + 1 < len(numeros) and numeros[j + 1] == numeros[j] + 1:
            j += 1
        saida.append(str(numeros[i]) if j == i else f"{numeros[i]}-{numeros[j]}")
        i = j + 1
    return ", ".join(saida)


def analisar(pdf_bytes, progresso=None):
    """Devolve um dicionário com tudo o que a gráfica precisa de saber."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    n = len(doc)
    if n == 0:
        raise ValueError("Esse PDF não tem páginas.")

    # ---------------------------------------------------- tamanho das páginas
    formatos, fora = {}, []
    for i, pag in enumerate(doc, 1):
        larg, alt = round(_mm(pag.rect.width), 1), round(_mm(pag.rect.height), 1)
        formatos[(larg, alt)] = formatos.get((larg, alt), 0) + 1
        if abs(larg - A4[0]) > TOLERANCIA_MM or abs(alt - A4[1]) > TOLERANCIA_MM:
            fora.append(i)

    # ------------------------------------------------------------------- cor
    coloridas = []
    for i, pag in enumerate(doc, 1):
        if progresso and i % 10 == 0:
            progresso(i / n)
        pm = pag.get_pixmap(dpi=36, colorspace=fitz.csRGB)
        dados, passo = pm.samples, pm.n
        for p in range(0, len(dados) - passo, passo * 7):
            r, g, b = dados[p], dados[p + 1], dados[p + 2]
            if max(r, g, b) - min(r, g, b) > LIMIAR_COR:
                coloridas.append(i)
                break
    if progresso:
        progresso(1.0)

    # --------------------------------------------------------------- fontes
    sem_fonte = set()
    for pag in doc:
        for f in pag.get_fonts(full=True):
            objeto = str(doc.xref_object(f[0]))
            if "FontFile" not in objeto and "FontDescriptor" not in objeto:
                sem_fonte.add(f[3])

    # -------------------------------------------------------------- imagens
    baixas = []
    for i, pag in enumerate(doc, 1):
        for info in pag.get_images(full=True):
            px_larg = info[2]
            for r in pag.get_image_rects(info[0]):
                largura_pol = r.width / 72
                if largura_pol > 0.3:
                    dpi = px_larg / largura_pol
                    if dpi < DPI_MINIMO:
                        baixas.append((i, int(dpi)))
                break

    folhas_fv = (n + 1) // 2
    lombada = {g: dict(frente_verso=round(folhas_fv * e, 1),
                       so_frente=round(n * e, 1))
               for g, e in sorted(FOLHA_MM.items())}

    return dict(
        paginas=n,
        tamanho_mb=round(len(pdf_bytes) / 1024 / 1024, 1),
        formatos=formatos,
        paginas_fora_a4=fora,
        paginas_a_cores=coloridas,
        percentagem_cor=round(len(coloridas) * 100 / n),
        folhas_frente_verso=folhas_fv,
        lombada=lombada,
        fontes_nao_incorporadas=sorted(sem_fonte),
        imagens_baixa_resolucao=sorted(baixas, key=lambda x: x[1]),
    )


def texto_para_a_grafica(r):
    """Parágrafo pronto a colar no pedido de orçamento."""
    linhas = [f"Miolo: {r['paginas']} páginas A4, impressão frente e verso."]
    if r["paginas_a_cores"]:
        linhas.append(f"Cor: {len(r['paginas_a_cores'])} das {r['paginas']} páginas "
                      f"têm cor ({r['percentagem_cor']}%). Páginas a cores: "
                      f"{resumir(r['paginas_a_cores'])}.")
        linhas.append("Agradeço que indiquem o preço com tudo a cores e também o "
                      "preço imprimindo a cores só estas páginas.")
    else:
        linhas.append("Cor: nenhuma página tem cor; pode ser tudo a preto e branco.")
    linhas.append("Papel: 90 g/m2 (agradeço que indiquem também o preço em 80 g/m2).")
    linhas.append(f"Lombada estimada: cerca de {r['lombada'][90]['frente_verso']:.0f} mm "
                  f"em 90 g/m2, frente e verso.")
    linhas.append("Agradeço que confirmem a medida real da lombada depois de "
                  "imprimirem o miolo, e que me enviem uma prova digital da capa "
                  "antes de imprimirem, com confirmação de que o preço inclui a cor "
                  "e quantos exemplares estão incluídos.")
    return "\n\n".join(linhas)
