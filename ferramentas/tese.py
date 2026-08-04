# -*- coding: utf-8 -*-
"""Verificação de PRÉ-IMPRESSÃO do PDF da tese.

NÃO lê o conteúdo. Não olha para o texto, citações, margens, paginação nem
formatação. Responde só ao que a gráfica vai perguntar, e são cinco coisas:

1. TAMANHO DAS PÁGINAS
   Lê a caixa de cada página, converte para milímetros e compara com A4
   (210 x 297) com 1 mm de tolerância. Apanha o artigo colado em formato
   carta e a figura numa página deitada — que a gráfica imprime encolhidas
   ou cortadas, e só se descobre com o livro na mão.

2. PÁGINAS COM COR A SÉRIO
   Desenha cada página em miniatura (36 ppp) e percorre um em cada sete
   pixels. Cinzento tem os três canais RGB iguais; só há cor quando eles se
   separam. Uma página conta como colorida quando algum ponto tem o canal
   mais forte e o mais fraco separados por mais de LIMIAR_COR (18 em 255) —
   margem que existe para não contar o serrilhado acinzentado das letras.
   É uma amostragem, não um varrimento: uma marca colorida minúscula pode
   escapar. Serve para orçamentar, não para certificar.

3. FONTES INCORPORADAS
   Para cada tipo de letra, vai ao objeto interno do PDF ver se lá está o
   ficheiro da fonte. Se não estiver, o computador da gráfica substitui-a e
   o texto muda de posição — parágrafos saltam de página.
   Ressalva: as catorze fontes-base do PDF (Helvetica, Times, Courier)
   legitimamente não trazem ficheiro incorporado e são assinaladas aqui.
   Qualquer gráfica as tem. Esta verificação foi pensada para o miolo.

4. IMAGENS DE BAIXA RESOLUÇÃO
   Divide a largura da imagem em pixels pela largura em polegadas do sítio
   onde está colada. Abaixo de DPI_MINIMO (150) assinala. No ecrã não se
   nota; no papel nota-se.

5. ESPESSURA DA LOMBADA
   Conta as folhas (em frente e verso são metade das páginas) e multiplica
   pela espessura típica de uma folha, por gramagem.
   É uma ESTIMATIVA, não uma medição: serve para saber se o número que a
   gráfica der faz sentido. Quem manda é a gráfica, que mede o miolo já
   impresso.
"""
import fitz

A4 = (210.0, 297.0)
TOLERANCIA_MM = 1.0      # o que ainda conta como A4
LIMIAR_COR = 18          # separação entre canais RGB a partir da qual é cor
DPI_MINIMO = 150         # abaixo disto uma imagem sai desfocada no papel
AMOSTRAGEM = 7           # analisa um em cada N pixels, para ser rápido

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
    # A caixa da página vem em pontos (1 pt = 1/72 polegada). Converte-se para
    # milímetros e compara-se com A4, com 1 mm de folga para arredondamentos.
    formatos, fora = {}, []
    for i, pag in enumerate(doc, 1):
        larg, alt = round(_mm(pag.rect.width), 1), round(_mm(pag.rect.height), 1)
        formatos[(larg, alt)] = formatos.get((larg, alt), 0) + 1
        if abs(larg - A4[0]) > TOLERANCIA_MM or abs(alt - A4[1]) > TOLERANCIA_MM:
            fora.append(i)

    # ------------------------------------------------------------------- cor
    # Miniatura de cada página a 36 ppp, e amostragem de um em cada 7 pixels.
    # Cinzento tem R=G=B; só há cor quando os canais se separam. Basta um
    # ponto colorido para a página contar — daí o break.
    coloridas = []
    for i, pag in enumerate(doc, 1):
        if progresso and i % 10 == 0:
            progresso(i / n)
        pm = pag.get_pixmap(dpi=36, colorspace=fitz.csRGB)
        dados, passo = pm.samples, pm.n
        for p in range(0, len(dados) - passo, passo * AMOSTRAGEM):
            r, g, b = dados[p], dados[p + 1], dados[p + 2]
            if max(r, g, b) - min(r, g, b) > LIMIAR_COR:
                coloridas.append(i)
                break
    if progresso:
        progresso(1.0)

    # --------------------------------------------------------------- fontes
    # Uma fonte só viaja com o PDF se o objeto trouxer FontFile/FontDescriptor.
    # Sem isso, a gráfica substitui-a e o texto muda de sítio. As fontes-base
    # do PDF (Helvetica, Times, Courier) aparecem aqui por não as trazerem —
    # é esperado, e qualquer gráfica as tem.
    sem_fonte = set()
    for pag in doc:
        for f in pag.get_fonts(full=True):
            objeto = str(doc.xref_object(f[0]))
            if "FontFile" not in objeto and "FontDescriptor" not in objeto:
                sem_fonte.add(f[3])

    # -------------------------------------------------------------- imagens
    # Resolução efetiva = pixels da imagem a dividir pelo tamanho em polegadas
    # do sítio onde ela está colada. Ignoram-se imagens com menos de 0,3 pol,
    # que são ícones e não se notam.
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

    # em frente e verso, duas páginas por folha
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
