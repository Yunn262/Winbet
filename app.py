import streamlit as st
from datetime import date
from scraper import FootballAIEngine


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="FootballAI Predictor",
    page_icon="⚽",
    layout="wide"
)


LIGAS = [
    "Premier League",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
    "Liga Portugal",
    "Brasileirao Serie A",
    "Champions League"
]


# ============================================================
# CABEÇALHO
# ============================================================

st.title("⚽ FootballAI Predictor")

st.caption(
    "Análise de futebol baseada nos dados disponíveis "
    "na Football-Data.org"
)


# ============================================================
# MENU
# ============================================================

pagina = st.sidebar.radio(
    "Navegação",
    [
        "🔥 Palpite Diário",
        "🔎 Análise H2H"
    ]
)


# ============================================================
# FUNÇÃO AUXILIAR
# ============================================================

def criar_motor(liga):

    return FootballAIEngine(
        league_name=liga
    )


# ============================================================
# PALPITE DIÁRIO
# ============================================================

if pagina == "🔥 Palpite Diário":

    st.header("🔥 Palpite Diário")

    st.write(
        "O sistema procura automaticamente os jogos disponíveis "
        "nas principais competições e seleciona os melhores mercados."
    )

    data_selecionada = st.date_input(
        "📅 Data dos jogos",
        value=date.today()
    )

    data_str = data_selecionada.strftime(
        "%Y-%m-%d"
    )


    if st.button(
        "🚀 GERAR PALPITE DO DIA",
        use_container_width=True
    ):

        todos_jogos = []

        progresso = st.progress(
            0,
            text="A procurar jogos..."
        )


        for numero, liga in enumerate(LIGAS):

            try:

                motor = criar_motor(
                    liga
                )

                jogos = motor.get_scheduled_events(
                    data_str
                )


                for jogo in jogos:

                    jogo["_liga"] = liga

                    todos_jogos.append(
                        jogo
                    )


            except Exception:
                pass


            progresso.progress(
                int(
                    ((numero + 1) / len(LIGAS))
                    * 100
                ),
                text=f"A verificar {liga}..."
            )


        progresso.empty()


        # ----------------------------------------------------
        # REMOVER DUPLICADOS
        # ----------------------------------------------------

        unicos = {}

        for jogo in todos_jogos:

            chave = (
                jogo.get("home_team", ""),
                jogo.get("away_team", "")
            )

            unicos[chave] = jogo


        todos_jogos = list(
            unicos.values()
        )


        if not todos_jogos:

            st.warning(
                "Nenhum jogo foi encontrado para esta data."
            )

            st.stop()


        # ----------------------------------------------------
        # QUANTIDADE DO BILHETE
        # ----------------------------------------------------

        if len(todos_jogos) >= 10:

            quantidade = 10

        elif len(todos_jogos) >= 6:

            quantidade = 6

        elif len(todos_jogos) >= 5:

            quantidade = 5

        else:

            st.warning(
                f"Foram encontrados apenas "
                f"{len(todos_jogos)} jogos."
            )

            st.info(
                "São necessários pelo menos 5 jogos "
                "para montar o Palpite Diário."
            )

            st.stop()


        st.success(
            f"⚽ {len(todos_jogos)} jogos encontrados. "
            f"O bilhete terá {quantidade} seleções."
        )


        # ----------------------------------------------------
        # ANÁLISE DOS JOGOS
        # ----------------------------------------------------

        resultados = []

        barra = st.progress(
            0,
            text="A analisar os jogos..."
        )


        jogos_para_analisar = todos_jogos[
            :min(
                len(todos_jogos),
                20
            )
        ]


        for numero, jogo in enumerate(
            jogos_para_analisar
        ):

            try:

                liga = jogo["_liga"]

                motor = criar_motor(
                    liga
                )


                analise = motor.analisar_confronto_completo(
                    jogo["home_team"],
                    jogo["away_team"]
                )


                resultados.append({

                    "jogo": jogo,

                    "mercado":
                        analise.get(
                            "melhor_mercado",
                            "Mais de 1.5 golos"
                        ),

                    "chance":
                        float(
                            analise.get(
                                "melhor_chance",
                                0
                            )
                        )

                })


            except Exception:

                pass


            barra.progress(
                int(
                    ((numero + 1)
                    / len(jogos_para_analisar))
                    * 100
                ),
                text=(
                    f"A analisar "
                    f"{numero + 1}/"
                    f"{len(jogos_para_analisar)}"
                )
            )


        barra.empty()


        if not resultados:

            st.error(
                "Não foi possível calcular os palpites "
                "com os dados disponíveis."
            )

            st.stop()


        # ----------------------------------------------------
        # ORDENAR POR CONFIANÇA
        # ----------------------------------------------------

        resultados = sorted(
            resultados,
            key=lambda x: x["chance"],
            reverse=True
        )


        selecionados = resultados[
            :quantidade
        ]


        # ----------------------------------------------------
        # BILHETE FINAL
        # ----------------------------------------------------

        st.markdown("---")

        st.subheader(
            "🎟️ BILHETE DO DIA"
        )


        soma = 0


        for numero, item in enumerate(
            selecionados,
            start=1
        ):

            jogo = item["jogo"]

            chance = item["chance"]

            soma += chance


            st.markdown(
                f"""
### {numero}. ⚽ {jogo['home_team']} 🆚 {jogo['away_team']}

**🎯 {item['mercado']}**

📊 Confiança calculada: **{chance:.0f}%**

🏆 Competição: **{jogo['_liga']}**
"""
            )

            st.progress(
                min(
                    chance / 100,
                    1.0
                )
            )

            st.markdown("---")


        # ----------------------------------------------------
        # RESUMO
        # ----------------------------------------------------

        confianca_media = (
            soma / len(selecionados)
        )


        st.subheader(
            "🧠 Resumo da análise"
        )


        c1, c2, c3 = st.columns(3)


        c1.metric(
            "Jogos no bilhete",
            len(selecionados)
        )


        c2.metric(
            "Confiança média",
            f"{confianca_media:.1f}%"
        )


        if confianca_media >= 80:

            classificacao = "🔥 Muito forte"

        elif confianca_media >= 70:

            classificacao = "🟢 Forte"

        elif confianca_media >= 60:

            classificacao = "🟡 Moderada"

        else:

            classificacao = "⚪ Baixa"


        c3.metric(
            "Classificação",
            classificacao
        )


        st.info(
            "💡 Melhor oportunidade do bilhete: "
            f"**{selecionados[0]['mercado']} — "
            f"{selecionados[0]['chance']:.0f}%**"
        )


# ============================================================
# H2H
# ============================================================

else:

    st.header("🔎 Análise H2H")

    st.write(
        "Escreva os nomes das duas equipas. "
        "O sistema procura os confrontos disponíveis "
        "e calcula as probabilidades dos mercados."
    )


    # --------------------------------------------------------
    # ESCOLHA DA COMPETIÇÃO
    # --------------------------------------------------------

    liga_h2h = st.selectbox(
        "🏆 Competição onde procurar os dados",
        LIGAS
    )


    col1, col2 = st.columns(2)


    with col1:

        equipa1 = st.text_input(
            "⚽ Time 1",
            placeholder="Ex.: Arsenal"
        )


    with col2:

        equipa2 = st.text_input(
            "⚽ Time 2",
            placeholder="Ex.: Chelsea"
        )


    analisar = st.button(
        "🤖 ANALISAR H2H",
        use_container_width=True
    )


    if analisar:

        if not equipa1.strip() or not equipa2.strip():

            st.warning(
                "Digite os dois nomes das equipas."
            )

            st.stop()


        if equipa1.strip().lower() == equipa2.strip().lower():

            st.warning(
                "As duas equipas precisam ser diferentes."
            )

            st.stop()


        with st.spinner(
            "A procurar dados H2H e forma recente..."
        ):

            motor = criar_motor(
                liga_h2h
            )


            h2h = motor.pesquisar_jogo(
                equipa1.strip(),
                equipa2.strip()
            )


            analise = motor.analisar_confronto_completo(
                equipa1.strip(),
                equipa2.strip()
            )


        # ----------------------------------------------------
        # DADOS ENCONTRADOS
        # ----------------------------------------------------

        if h2h:

            st.success(
                f"✅ {len(h2h)} confronto(s) encontrado(s)."
            )

        else:

            st.info(
                "ℹ️ Não foram encontrados confrontos "
                "diretos suficientes nesta competição. "
                "A análise usa os dados de forma recente "
                "disponíveis para as equipas."
            )


        st.markdown("---")


        # ----------------------------------------------------
        # VEREDITO
        # ----------------------------------------------------

        mercados = analise.get(
            "mercados",
            {}
        )


        if not mercados:

            st.error(
                "Não existem dados suficientes para calcular "
                "os mercados."
            )

            st.stop()


        ordenados = sorted(
            mercados.items(),
            key=lambda x: x[1],
            reverse=True
        )


        melhor_nome = ordenados[0][0]

        melhor_pct = ordenados[0][1]


        st.subheader(
            "🧠 Melhor oportunidade"
        )


        st.success(
            f"🎯 **{melhor_nome}**\n\n"
            f"Probabilidade calculada: **{melhor_pct}%**"
        )


        # ----------------------------------------------------
        # MERCADOS
        # ----------------------------------------------------

        st.subheader(
            "📊 Probabilidades dos mercados"
        )


        mercados_desejados = [

            "Ambas Marcam",

            "Mais de 1.5 golos",

            "Mais de 2.5 golos",

            "Menos de 3.5 golos",

            "Menos de 4.5 golos",

            "Casa ou Empate (1X)",

            "Fora ou Empate (X2)",

            "Vitória Casa",

            "Vitória Fora"

        ]


        for mercado in mercados_desejados:

            pct = mercados.get(
                mercado,
                0
            )


            col_a, col_b = st.columns(
                [4, 1]
            )


            with col_a:

                st.write(
                    f"**{mercado}**"
                )

                st.progress(
                    min(
                        pct / 100,
                        1.0
                    )
                )


            with col_b:

                st.metric(
                    "Chance",
                    f"{pct}%"
                )


        # ----------------------------------------------------
        # DESTAQUES
        # ----------------------------------------------------

        st.markdown("---")

        st.subheader(
            "🏆 Destaques"
        )


        primeiro = ordenados[0]


        segundo = (
            ordenados[1]
            if len(ordenados) > 1
            else primeiro
        )


        terceiro = (
            ordenados[2]
            if len(ordenados) > 2
            else segundo
        )


        c1, c2, c3 = st.columns(3)


        with c1:

            st.info(
                f"""
🥇 **Melhor oportunidade**

{primeiro[0]}

**{primeiro[1]}%**
"""
            )


        with c2:

            st.info(
                f"""
🥈 **Segunda melhor**

{segundo[0]}

**{segundo[1]}%**
"""
            )


        with c3:

            st.info(
                f"""
🥉 **Terceira melhor**

{terceiro[0]}

**{terceiro[1]}%**
"""
            )


        # ----------------------------------------------------
        # FORMA DAS EQUIPAS
        # ----------------------------------------------------

        estatisticas = analise.get(
            "estatisticas",
            {}
        )


        st.markdown("---")

        st.subheader(
            "📈 Dados usados pelo modelo"
        )


        a, b = st.columns(2)


        with a:

            st.markdown(
                f"""
### ⚽ {equipa1}

Média de golos marcados:
**{estatisticas.get('media_golos_casa', 0)}**

Média de golos sofridos:
**{estatisticas.get('media_golos_sofridos_casa', 0)}**

Jogos analisados:
**{estatisticas.get('jogos_casa', 0)}**
"""
            )


        with b:

            st.markdown(
                f"""
### ⚽ {equipa2}

Média de golos marcados:
**{estatisticas.get('media_golos_fora', 0)}**

Média de golos sofridos:
**{estatisticas.get('media_golos_sofridos_fora', 0)}**

Jogos analisados:
**{estatisticas.get('jogos_fora', 0)}**
"""
            )


        # ----------------------------------------------------
        # H2H ENCONTRADO
        # ----------------------------------------------------

        if h2h:

            st.markdown("---")

            st.subheader(
                "📋 Confrontos encontrados"
            )


            for jogo in h2h[:10]:

                st.write(
                    f"⚽ **{jogo.get('home_team', '?')}** "
                    f"vs "
                    f"**{jogo.get('away_team', '?')}**"
                )

                st.caption(
                    f"Resultado: "
                    f"{jogo.get('score', '?')} | "
                    f"Data: "
                    f"{jogo.get('date', '')}"
                )
