# -*- coding: utf-8 -*-
"""Kit FMUP — quatro ferramentas para o pedido de admissão a provas.

Interface web. Corre no Streamlit Community Cloud, de graça.
"""
import io
import types
import zipfile

import streamlit as st

from ferramentas import capa, formularios, processo, tese

st.set_page_config(page_title="Kit FMUP — admissão a provas",
                   page_icon="🎓", layout="centered")

st.title("Kit FMUP")
st.caption("Quatro ferramentas para o pedido de admissão a provas de "
           "doutoramento — Faculdade de Medicina da Universidade do Porto.")

with st.expander("Ler primeiro — a ordem em que se faz isto"):
    st.markdown("""
**Antes de tudo, pergunte aos orientadores: «posso mandar imprimir?»**
É a pergunta mais barata de fazer, e a que destranca o resto. Depois de
impressos os três exemplares, qualquer correção obriga a reimprimir os três.

1. **Verificar a tese** — antes de pedir orçamento. Diz-lhe quantas páginas
   têm cor e que espessura vai ter a lombada.
2. **Formulários** — pode ir fazendo em paralelo. Peça já aos orientadores o
   número do documento de identificação e a categoria exata de cada um: é o
   que costuma travar tudo e demora dias a ser respondido.
3. **Capa** — só depois de a gráfica lhe dizer a **largura da lombada**. Esse
   número não se inventa.
4. **Verificar o processo** — o último passo, antes de carregar em enviar.

**E a regra que vale mais do que todas:** não pague à gráfica antes de ver a
prova da capa e de ter por escrito que o preço inclui a cor.
""")

t1, t2, t3, t4 = st.tabs(["1 · Verificar a tese", "2 · Formulários",
                          "3 · Capa", "4 · Verificar o processo"])


# ═══════════════════════════════════════════════ 1. verificar a tese
with t1:
    st.subheader("Verificar a tese antes de imprimir")
    st.write("Carregue o PDF final da tese. Nada é guardado: o ficheiro é "
             "analisado e desaparece quando fechar a página.")
    pdf = st.file_uploader("PDF da tese", type="pdf", key="tese")

    if pdf is not None:
        barra = st.progress(0.0, text="A analisar página a página...")
        try:
            r = tese.analisar(pdf.getvalue(), progresso=lambda p: barra.progress(p))
        except Exception as e:
            barra.empty()
            st.error(f"Não consegui ler esse PDF: {e}")
        else:
            barra.empty()
            a, b, c = st.columns(3)
            a.metric("Páginas", r["paginas"])
            a.caption(f'{r["tamanho_mb"]} MB')
            b.metric("Páginas com cor", len(r["paginas_a_cores"]))
            b.caption(f'{r["percentagem_cor"]}% do total')
            c.metric("Lombada estimada",
                     f'{r["lombada"][90]["frente_verso"]:.0f} mm')
            c.caption("90 g/m², frente e verso")

            if r["paginas_fora_a4"]:
                st.error(f"**{len(r['paginas_fora_a4'])} página(s) não são A4:** "
                         f"{tese.resumir(r['paginas_fora_a4'])}\n\n"
                         "A gráfica vai imprimi-las encolhidas ou cortadas. "
                         "Corrija antes de imprimir.")
            else:
                st.success("Todas as páginas são A4.")

            if r["paginas_a_cores"]:
                st.info(f"**Páginas a cores:** {tese.resumir(r['paginas_a_cores'])}"
                        "\n\nSe a diferença de preço for grande, peça orçamento "
                        "para imprimir só estas a cores e o resto a preto.")
            else:
                st.success("Nenhuma página tem cor — peça orçamento a preto e "
                           "branco, é bastante mais barato.")

            if r["fontes_nao_incorporadas"]:
                st.error("**Fontes não incorporadas no PDF:** "
                         + ", ".join(r["fontes_nao_incorporadas"])
                         + "\n\nNo computador da gráfica podem ser trocadas por "
                         "outras e o texto muda de sítio. Volte a exportar o PDF "
                         "com as fontes incorporadas.")
            if r["imagens_baixa_resolucao"]:
                piores = r["imagens_baixa_resolucao"][:6]
                st.warning(f"**{len(r['imagens_baixa_resolucao'])} imagem(ns) abaixo "
                           f"de {tese.DPI_MINIMO} ppp** — vão sair desfocadas. "
                           + ", ".join(f"pág. {p} ({d} ppp)" for p, d in piores))

            st.markdown("##### Espessura da lombada, por gramagem")
            st.table({
                "Papel": [f"{g} g/m²" for g in r["lombada"]],
                "Frente e verso": [f'{v["frente_verso"]:.1f} mm'
                                   for v in r["lombada"].values()],
                "Só frente": [f'{v["so_frente"]:.1f} mm'
                              for v in r["lombada"].values()],
            })
            st.caption("Estimativa. Quem manda é a gráfica, que mede o miolo já "
                       "impresso. Capa dura acrescenta 5 a 6 mm.")

            st.markdown("##### Para colar no email às gráficas")
            st.code(tese.texto_para_a_grafica(r), language=None)


# ═══════════════════════════════════════════════════ 2. formulários
with t2:
    st.subheader("Formulários da FMUP")
    st.write("Preencha o que souber. O que deixar em branco sai a **vermelho** "
             "nos formulários, com a marca `[A PREENCHER]` — para não assinar "
             "nada em branco.")

    def _ou_none(v):
        v = (v or "").strip()
        return v or None

    with st.form("formularios"):
        st.markdown("##### O estudante")
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome completo", help="Como está no documento de identificação")
        num = c2.text_input("Número de estudante U.PORTO")
        c1, c2 = st.columns(2)
        id_doc = c1.text_input("Documento de identificação",
                               placeholder="Cartão de Cidadão 12345678")
        id_val = c2.text_input("Validade do documento", placeholder="dd-mm-aaaa")
        c1, c2 = st.columns(2)
        email = c1.text_input("Email")
        telem = c2.text_input("Telemóvel", placeholder="+351 912 345 678")
        c1, c2 = st.columns(2)
        grau = c1.selectbox("Grau que já tem", ["Mestre", "Licenciado"])
        conclusao = c2.text_input("Data de conclusão da tese", placeholder="dd/mm/aaaa")

        st.markdown("##### O doutoramento")
        titulo = st.text_area("Título da tese", height=80)
        c1, c2, c3 = st.columns(3)
        programa = c1.text_input("Programa doutoral", "Bioética")
        area = c2.text_input("Área científica", "Bioética")
        ano_curr = c3.text_input("Ano curricular", "2025/2026")
        st.write("Palavras-chave — o formulário tem quatro caixas separadas")
        k = st.columns(4)
        chaves = [k[i].text_input(f"Palavra-chave {i+1}", key=f"kw{i}") for i in range(4)]

        st.markdown("##### Orientador e coorientador")
        st.caption("O número do documento e a categoria exata têm de ser pedidos "
                   "a eles por escrito. «Professor Auxiliar» e «Professor Auxiliar "
                   "com Agregação» não são a mesma coisa.")
        o1, o2 = st.columns(2)
        with o1:
            st.markdown("**Orientador**")
            o_nome = st.text_input("Nome", key="on")
            o_cat = st.text_input("Categoria", key="oc",
                                  placeholder="Professor Catedrático")
            o_email = st.text_input("Email", key="oe")
            o_id = st.text_input("N.º do documento", key="oi")
        with o2:
            st.markdown("**Coorientador**")
            c_nome = st.text_input("Nome", key="cn")
            c_cat = st.text_input("Categoria", key="cc")
            c_email = st.text_input("Email", key="ce")
            c_id = st.text_input("N.º do documento", key="ci")

        st.markdown("##### Critério D — os artigos")
        st.caption("Basta cumprir uma via. Escreva a referência por extenso, com "
                   "DOI e o quartil verificado no Scimago ou no JCR.")
        via = st.radio("Via que vai invocar",
                       ["Dois ou mais artigos como primeiro autor",
                        "Um artigo Q1 como primeiro autor"], index=0)
        if via.startswith("Um"):
            art_q1 = st.text_area("Artigo Q1", height=70)
            arts = ["", ""]
        else:
            art_q1 = ""
            arts = [st.text_area(f"Artigo {i+1}", height=70, key=f"art{i}")
                    for i in range(2)]

        st.markdown("##### Declaração de divulgação")
        d1, d2, d3 = st.columns(3)
        tipo = d1.radio("Tipo", ["Total", "Parcial"])
        ambito = d2.radio("Âmbito", ["Geral", "Só na U.Porto"])
        formato = d3.radio("Formato", ["Digital", "Papel"])

        data_sub = st.text_input("Data de submissão", placeholder="dd/mm/aaaa")
        gerar_forms = st.form_submit_button("Preencher os formulários",
                                            type="primary")

    if gerar_forms:
        D = types.SimpleNamespace()
        D.student = dict(nome=_ou_none(nome), grau=grau, id_doc=_ou_none(id_doc),
                         id_doc_curto=_ou_none(id_doc), id_validade=_ou_none(id_val),
                         email=_ou_none(email), telemovel=_ou_none(telem),
                         numero_uporto=_ou_none(num),
                         data_conclusao=_ou_none(conclusao))
        D.phd = dict(programa=_ou_none(programa), ano_curricular=_ou_none(ano_curr),
                     area=_ou_none(area), titulo=_ou_none(titulo),
                     palavras_chave=[_ou_none(x) for x in chaves])
        inst = "Faculdade de Medicina da Universidade do Porto"
        D.orientador = dict(nome=_ou_none(o_nome), grau="Doutor",
                            categoria=_ou_none(o_cat), instituicao=inst,
                            email=_ou_none(o_email), id_doc=_ou_none(o_id))
        D.coorientador = dict(nome=_ou_none(c_nome), grau="Doutor",
                              categoria=_ou_none(c_cat), instituicao=inst,
                              email=_ou_none(c_email), id_doc=_ou_none(c_id))
        NA = formularios.NAO_APLICAVEL
        D.coorientador2 = dict(nome=NA, grau="—", categoria="—", instituicao="—",
                               email="—", id_doc="—")
        D.artigo_q1 = _ou_none(art_q1) or NA
        D.artigos_q2q3 = [_ou_none(a) for a in arts]
        D.declaracao = dict(
            doutoramento=True, mestrado=False,
            tipo_total=tipo == "Total", tipo_parcial=tipo == "Parcial",
            ambito_uporto=ambito.startswith("Só"), ambito_geral=ambito == "Geral",
            formato_papel=formato == "Papel", formato_digital=formato == "Digital",
            observacoes=("Entrega em formato digital: ficheiro PDF remetido por "
                         "via eletrónica, não em suporte físico (CD/DVD)."
                         if formato == "Digital" else ""))
        D.anexos = dict(A_tese=True, B_cv=True, C_resumo=True,
                        D_artigo_q1=via.startswith("Um"),
                        D_dois_artigos=not via.startswith("Um"),
                        E_pareceres=True, F_declaracao=True, G_documento_id=True,
                        H_tres_teses=True)
        D.data_submissao = _ou_none(data_sub)

        try:
            docs, falta = formularios.preencher(D)
        except Exception as e:
            st.error(f"Não consegui preencher os formulários: {e}")
        else:
            if falta:
                st.warning(f"**Faltam {len(falta)} campo(s)** — saem a vermelho "
                           "nos ficheiros:\n\n"
                           + "\n".join(f"- {m}" for m in falta)
                           + "\n\n**Não assine nem envie enquanto houver vermelho.**")
            else:
                st.success("Está tudo preenchido. Nenhum campo ficou a vermelho.")
                st.info("A seguir: os Pareceres A2 e A3 são assinados pelo "
                        "orientador e pelo coorientador; o A1 e a Declaração, por "
                        "si. Pode assinar sem imprimir, com a Chave Móvel Digital "
                        "em https://cmd.autenticacao.gov.pt — o Decreto-Lei "
                        "12/2021 equipara-a à assinatura à mão.")

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                for nome_f, dados in docs.items():
                    z.writestr(nome_f, dados)
            st.download_button("Descarregar os quatro formulários (zip)",
                               buf.getvalue(), "Formularios FMUP.zip",
                               "application/zip", type="primary")
            for nome_f, dados in docs.items():
                st.download_button(nome_f, dados, nome_f, key="d" + nome_f)


# ═══════════════════════════════════════════════════════════ 3. capa
with t3:
    st.subheader("Capa da tese")
    st.warning("**Faça isto só depois de a gráfica lhe dizer a largura da "
               "lombada.** Esse número não se inventa: é ele que decide se o "
               "título da lombada fica direito ou em cima da dobra.")

    with st.form("capa"):
        c_titulo = st.text_area("Título completo da tese", height=80)
        c_autor = st.text_input("O seu nome, como quer que apareça na capa")
        c1, c2, c3 = st.columns(3)
        c_lombada = c1.number_input("Lombada (mm)", 5.0, 60.0, 17.0, 0.5,
                                    help="A medida que a gráfica lhe deu")
        c_ano = c2.number_input("Ano", 2020, 2040, 2026)
        c_curso = c3.text_input("Área", "Bioética")
        with st.expander("Mestrado, outra faculdade, outro texto"):
            m1, m2 = st.columns(2)
            c_grau = m1.selectbox("Letra na capa", ["D", "M"],
                                  help="D = doutoramento, M = mestrado")
            c_ciclo = m2.selectbox("Ciclo", ["3.º", "2.º"])
            c_sigla = st.text_input("Sigla na lombada", "FMUP")
            c_lt = st.text_input("Linha 1", "TESE DE DOUTORAMENTO APRESENTADA")
            c_lf = st.text_input(
                "Linha 2", "À FACULDADE DE MEDICINA DA UNIVERSIDADE DO PORTO EM")
        gerar_capa = st.form_submit_button("Gerar a capa", type="primary")

    if gerar_capa:
        try:
            pdf_bytes, rel = capa.gerar(
                c_titulo, c_autor, ano=int(c_ano), curso=c_curso,
                lombada_mm=c_lombada, grau=c_grau, ciclo=c_ciclo, sigla=c_sigla,
                linha_tese=c_lt, linha_faculdade=c_lf)
        except ValueError as e:
            st.error(str(e))
        else:
            larg, alt = rel["folha_mm"]
            vt, vf, lom = rel["lombada"]
            st.success(f"Folha de **{larg:.0f} × {alt:.0f} mm** "
                       f"— 210 + {lom:g} + 210. Sem sangria nem marcas de corte.")
            e = rel["elementos"]
            st.table({
                "Na lombada": ["Título", "Nome do autor"],
                "Linhas": [e["titulo"]["linhas"], e["autor"]["linhas"]],
                "Corpo": [f'{e["titulo"]["corpo"]} pt', f'{e["autor"]["corpo"]} pt'],
                "Folga à esquerda": [f'{e["titulo"]["folga_esq"]} mm',
                                     f'{e["autor"]["folga_esq"]} mm'],
                "Folga à direita": [f'{e["titulo"]["folga_dir"]} mm',
                                    f'{e["autor"]["folga_dir"]} mm'],
            })
            st.caption("As folgas são medidas no PDF já desenhado, não estimadas. "
                       "Se o título não coubesse, o corpo da letra foi reduzido "
                       "até sobrarem pelo menos 2 mm até cada vinco.")
            st.download_button("Descarregar a capa em PDF", pdf_bytes,
                               "Capa.pdf", "application/pdf", type="primary")
            st.image(capa.previsualizar(pdf_bytes),
                     caption="Contracapa · lombada · capa")


# ═══════════════════════════════════════ 4. verificar o processo
with t4:
    st.subheader("Verificar o processo antes de submeter")
    st.write("Carregue **todos** os ficheiros que vai anexar ao email de "
             "submissão — e só esses.")
    anexos = st.file_uploader("Anexos do email", accept_multiple_files=True,
                              type=["pdf", "docx", "doc", "jpg", "png"],
                              key="anexos")

    if anexos:
        r = processo.verificar([(f.name, f.getvalue()) for f in anexos])

        st.markdown("##### Os documentos obrigatórios")
        icones = {"ok": "✅", "falta": "❌", "assinar": "🖊️", "confirmar": "❔"}
        for d in r["documentos"]:
            linha = f'{icones[d["estado"]]} **{d["codigo"]}** — {d["nome"]}'
            if d["ficheiro"]:
                linha += f'  \n`{d["ficheiro"]}`'
            st.markdown(linha)
            for extra in d["extras"]:
                st.caption(f"também encontrei: {extra}")

        if r["sobra"]:
            st.caption("Ficheiros que não encaixei em nenhum documento: "
                       + ", ".join(r["sobra"]))

        if r["por_preencher"]:
            st.error("**Ainda há campos por preencher:**\n\n"
                     + "\n".join(f"- `{n}` — página(s) {p}"
                                 for n, p in r["por_preencher"]))

        if r["cabe_no_email"]:
            st.success(f"Os anexos somam {r['total_mb']} MB — cabe num email só.")
        else:
            st.warning(f"Os anexos somam {r['total_mb']} MB, acima dos "
                       f"{processo.LIMITE_EMAIL_MB} MB do Gmail. Envie a tese por "
                       "link e o resto em anexo, e diga-o no corpo do email.")

        if r["problemas"]:
            st.error("**A resolver antes de enviar:**\n\n"
                     + "\n".join(f"- {p}" for p in r["problemas"]))
        if r["avisos"]:
            st.warning("**A confirmar:**\n\n"
                       + "\n".join(f"- {a}" for a in r["avisos"]))
        if not r["problemas"] and not r["avisos"]:
            st.success("Está tudo. Pode enviar.")

        st.info("""**Duas coisas que isto não consegue ver:**

- Os **três exemplares em papel** são obrigatórios *no momento* do pedido:
  têm de estar na Faculdade quando o processo entra, não depois.
- Guarde a **confirmação escrita da entrega**, com data e nome de quem
  recebeu. É a prova de que cumpriu.

O processo entrega-se **por email**, para posgraduacao@med.up.pt — não é
pelo SIGARRA.""")


st.divider()
st.caption("Nada do que carregar aqui é guardado. Os ficheiros são processados "
           "em memória e desaparecem quando fechar a página. · "
           "Gráfica: Grafipronto Campus S. João, +351 223 203 757, "
           "campus@grafipronto.pt · Levantamento: bioetica@med.up.pt")
