# Kit FMUP — admissão a provas de doutoramento

Quatro ferramentas, numa página web, para o pedido de admissão a provas na
Faculdade de Medicina da Universidade do Porto:

1. **Verificar a tese** antes de pedir orçamento — páginas A4, páginas a cores,
   espessura da lombada, fontes incorporadas, imagens de baixa resolução.
2. **Preencher os formulários** obrigatórios — requerimento, os dois Pareceres
   e a Declaração de divulgação.
3. **Gerar a capa** — contracapa, lombada e capa, no modelo da U.Porto.
4. **Verificar o processo** antes de submeter — anexos completos, versões
   assinadas, campos por preencher, tamanho do email.

Nasceu de um processo real, concluído em 2026. Cada verificação corresponde a
uma coisa que correu mal e custou tempo ou dinheiro.

---

## Pôr isto no ar — dez minutos, e é grátis

Só é preciso uma vez. Depois é um link que se envia a quem precisar.

### 1. Criar o repositório no GitHub

1. Conta em <https://github.com> (gratuita).
2. **New repository** → nome, por exemplo `kit-fmup` → **Create repository**.
3. Carregar os ficheiros: **Add file → Upload files**, arrastar **tudo** o que
   está nesta pasta (incluindo a pasta `ferramentas/` e a
   `formularios_em_branco/`) → **Commit changes**.

   > Se preferir a linha de comandos:
   > ```bash
   > git init && git add . && git commit -m "Kit FMUP"
   > git branch -M main
   > git remote add origin https://github.com/O-SEU-NOME/kit-fmup.git
   > git push -u origin main
   > ```

### 2. Publicar no Streamlit Community Cloud

1. <https://share.streamlit.io> → **Sign in with GitHub** → autorizar.
2. **Create app** → **Deploy a public app from GitHub**.
3. Escolher o repositório, o ramo `main`, e o ficheiro **`streamlit_app.py`**.
4. **Deploy**. A primeira construção demora dois ou três minutos — ele está a
   instalar o PyMuPDF e o python-docx.

Fica com um endereço do género `https://kit-fmup.streamlit.app`. É esse que se
envia aos colegas: abrem o link e usam. Não instalam nada.

### 3. Sempre que quiser mudar alguma coisa

Edite o ficheiro no GitHub e grave. A app reconstrói-se sozinha em segundos.

---

## O que convém saber antes de publicar

**A app adormece ao fim de 12 horas sem visitas.** O primeiro visitante a
seguir vê um botão para a acordar e espera cerca de meio minuto. Não é avaria.
Vale a pena avisar quem receber o link.

**O repositório é público.** Não há nada de privado no código, mas quem abrir o
repositório vê tudo o que lá estiver — não ponha aqui a sua tese, nem
formulários já preenchidos. O plano gratuito permite **uma** app privada, se
preferir esse caminho.

**Os ficheiros dos utilizadores não são guardados.** A tese que alguém carregar
é processada em memória e desaparece quando a página fecha — nada é escrito em
disco nem enviado para outro lado. Mas *passa* pelos servidores do Streamlit
enquanto é analisada. Quem tiver reservas quanto a isso deve usar a versão de
linha de comandos, que corre no próprio computador.

**Memória: 1 GB.** Chega bem. Uma tese de 200 páginas e 13 MB analisa-se em
poucos segundos.

---

## Correr no seu computador, sem publicar nada

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Abre em `http://localhost:8501`.

---

## Como está feito

```
streamlit_app.py           a interface
ferramentas/
    capa.py                gera a capa
    tese.py                analisa o PDF da tese
    formularios.py         preenche os quatro impressos
    processo.py            confere os anexos
    logos.py               logótipos da U.Porto, em base64
formularios_em_branco/     os impressos oficiais, por preencher
requirements.txt
```

**A capa verifica-se a si própria.** Depois de desenhar o texto da lombada, o
programa rasteriza a página, mede a tinta a 300 ppp e volta a desenhar até o
bloco estar centrado e com pelo menos 2 mm livres até cada vinco, reduzindo o
corpo da letra se for preciso. As folgas que aparecem no ecrã são medidas, não
estimadas. É a lição que custou três provas de gráfica: numa lombada estreita,
um título em três linhas encosta ao vinco e passa para a capa da frente.

**A letra é Helvetica.** O modelo oficial da U.Porto usa Myriad Pro, que é paga
e não vem em nenhum sistema. É uma das catorze fontes-base do PDF, que qualquer
gráfica tem.

**Os formulários preenchem seis campos que ninguém vê.** O modelo oficial tem
seis controlos fora dos parágrafos — três palavras-chave e as três linhas dos
artigos — que passam despercebidos a quem preenche à mão e se assinam em
branco.

---

## Contactos úteis

- **Gráfica** — Grafipronto, Campus S. João · +351 223 203 757 ·
  campus@grafipronto.pt · Galeria Comercial do Campus S. João, Rua Dr. Plácido
  da Costa, 4200-450 Porto · todos os dias, 9h–23h.
  Imprime direto de um PDF, mas **não faz design nem entrega**.
- **Levantamento** — Secretariado do 2.º e 3.º Ciclo em Bioética ·
  bioetica@med.up.pt
- **Submissão** — Serviços de Pós-Graduação · posgraduacao@med.up.pt ·
  **por email**, não pelo SIGARRA.
- **Assinar sem imprimir** — <https://cmd.autenticacao.gov.pt> (Chave Móvel
  Digital). O Decreto-Lei 12/2021 equipara-a à assinatura à mão.
