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


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
}

.titulo {
    font-size: 38px;
    font-weight: 800;
}

.subtitulo {
    color: #94a3b8;
    margin-bottom: 25px;
}

.card {
    padding: 20px;
    border-radius: 15px;
    border: 1px solid rgba(255,255,255,.10);
    margin-bottom: 20px;
}

.melhor {
    padding: 18px;
    border-radius: 12px;
    border: 1px solid rgba(16,185,129,.5);
    background: rgba(16,185,129,.10);
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# MOTOR
# ============================================================

if "ai_engine" not in st.session_state:
    st.session_state.ai_engine = FootballAIEngine(
        liga_nome="Premier League"
    )

engine = st.session_state.ai_engine


# ============================================================
# CABEÇALHO
# ============================================================

st.markdown(
    '<div class="titulo">⚽ FootballAI Predictor</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitulo">'
    'Análise automática com API-Football'
    '</div>',
    unsafe_allow_html=True
)

st.markdown("---")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Sistema")

    liga = st.selectbox(
        "Campeonato",
        [
            "Premier League",
            "La Liga",
            "Serie A Italiana",
            "Bundesliga",
            "Ligue 1",
            "Champions League",
            "Brasileirao Serie A",
            "Liga Portugal",
            "Eredivisie",
            "Noruega",
            "Escócia",
            "Dinamarca",
            "Polônia",
            "Bulgária"
        ]
    )

    # Recria o motor se a liga mudar
    if st.session_state.get("liga_atual") != liga:

        st.session_state.ai_engine = FootballAIEngine(
            liga_nome=liga
        )

        st.session_state.liga_atual = liga

        engine = st.session_state.ai_engine

    if st.button(
        "🧪 Testar API",
        use_container_width=True
    ):

        with st.spinner("Testando conexão..."):

            resultado_api = engine.testar_api()

        if resultado_api.get("ok"):

            st.success(
                "🟢 API-Football funcionando!"
            )

        else:

            st.error(
                "🔴 API não respondeu."
            )

            st.caption(
                resultado_api.get(
                    "mensagem",
                    "Erro desconhecido."
                )
            )

    st.markdown("---")

    st.subheader("📊 Mercados analisados")

    st.write("⚽ Ambas marcam")
    st.write("⚽ Mais de 1,5 golos")
    st.write("⚽ Mais de 2,5 golos")
    st.write("⚽ Menos de 3,5 golos")
    st.write("⚽ Menos de 4,5 golos")
    st.write("🏠 Time 1 ganha ou empata")
    st.write("✈️ Time 2 ganha ou empata")
    st.write("🏆 Time 1 ganha direto")
    st.write("🏆 Time 2 ganha direto")


# ============================================================
# ABAS
# ============================================================

aba_dia, aba_h2h = st.tabs(
    [
        "🔥 Palpites do Dia",
        "🔎 H2H"
    ]
)


# ============================================================
# PALPITES DO DIA
# ============================================================

with aba_dia:

    st.subheader(
        "🔥 Palpites do Dia"
    )

    st.write(
        f"Jogos reais da **{liga}** analisados pela API-Football."
    )

    data_pesquisa = st.date_input(
        "📅 Escolha a data",
        value=date.today()
    )

    if st.button(
        "🚀 GERAR PALPITES DO DIA",
        type="primary",
        use_container_width=True
    ):

        data_str = data_pesquisa.strftime(
            "%Y-%m-%d"
        )

        with st.spinner(
            "🔎 Procurando jogos reais..."
        ):

            jogos = engine.get_scheduled_events(
                data_str
            )

        if not jogos:

            st.warning(
                "⚠️ Nenhum jogo encontrado para esta data."
            )

            st.info(
                "Tente outra data ou verifique a conexão "
                "da API-Football."
            )

        else:

            # O bot pode trabalhar com 10 ou mais.
            # Não corta os jogos encontrados.
            quantidade = len(jogos)

            st.success(
                f"✅ {quantidade} jogos encontrados."
            )

            if quantidade >= 10:

                st.info(
                    "🔥 Existem 10 ou mais jogos. "
                    "O sistema analisará os melhores jogos disponíveis."
                )

            else:

                st.info(
                    f"ℹ️ Existem apenas {quantidade} jogos "
                    "nesta data. Todos serão analisados."
                )

            st.markdown("---")

            # Guardar resultados
            resultados_dia = []

            # ====================================================
            # ANALISAR CADA JOGO
            # ====================================================

            for numero, jogo in enumerate(
                jogos,
                1
            ):

                casa = jogo.get(
                    "home_team",
                    "?"
                )

                fora = jogo.get(
                    "away_team",
                    "?"
                )

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"### {numero}. ⚽ "
                        f"{casa} × {fora}"
                    )

                    st.caption(
                        f"🏆 {jogo.get('league', liga)}"
                    )

                    if jogo.get("start_time"):

                        st.caption(
                            f"🕒 {jogo['start_time']}"
                        )

                    with st.spinner(
                        f"Analisando {casa} × {fora}..."
                    ):

                        try:

                            analise = (
                                engine.analisar_confronto_completo(
                                    casa,
                                    fora
                                )
                            )

                        except Exception as e:

                            st.error(
                                f"Erro na análise: {e}"
                            )

                            continue

                    mercados = analise.get(
                        "mercados",
                        {}
                    )

                    melhor = analise.get(
                        "melhor_mercado",
                        "Sem dados suficientes"
                    )

                    chance = analise.get(
                        "melhor_chance",
                        0
                    )

                    # ============================================
                    # MELHOR OPORTUNIDADE
                    # ============================================

                    st.markdown(
                        f"""
                        <div class="melhor">
                            🔥 <b>MELHOR OPORTUNIDADE</b>
                            <br><br>
                            <span style="font-size:23px;">
                                {melhor}
                            </span>
                            <br><br>
                            📊 Confiança estatística:
                            <b>{chance}%</b>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # ============================================
                    # MERCADOS
                    # ============================================

                    col1, col2 = st.columns(2)

                    lista = list(
                        mercados.items()
                    )

                    meio = (
                        len(lista) + 1
                    ) // 2

                    with col1:

                        for mercado, pct in lista[:meio]:

                            if pct is None:

                                st.write(
                                    f"⚪ {mercado}: "
                                    "Sem dados"
                                )

                            else:

                                st.write(
                                    f"🎯 {mercado}: "
                                    f"**{pct}%**"
                                )

                                st.progress(
                                    max(
                                        0,
                                        min(
                                            float(pct),
                                            100
                                        )
                                    ) / 100
                                )

                    with col2:

                        for mercado, pct in lista[meio:]:

                            if pct is None:

                                st.write(
                                    f"⚪ {mercado}: "
                                    "Sem dados"
                                )

                            else:

                                st.write(
                                    f"🎯 {mercado}: "
                                    f"**{pct}%**"
                                )

                                st.progress(
                                    max(
                                        0,
                                        min(
                                            float(pct),
                                            100
                                        )
                                    ) / 100
                                )

                    # ============================================
                    # H2H
                    # ============================================

                    h2h = analise.get(
                        "h2h",
                        []
                    )

                    if h2h:

                        st.caption(
                            f"🔎 Histórico H2H analisado: "
                            f"{len(h2h)} jogos"
                        )

                    resultados_dia.append(
                        {
                            "jogo":
                                f"{casa} × {fora}",

                            "mercado":
                                melhor,

                            "chance":
                                chance
                        }
                    )


# ============================================================
# H2H
# ============================================================

with aba_h2h:

    st.subheader(
        "🔎 Análise H2H"
    )

    st.write(
        "Digite livremente as duas equipas. "
        "Não é necessário escolher de uma lista."
    )

    c1, c2 = st.columns(2)

    with c1:

        equipa_1 = st.text_input(
            "🏠 Time 1",
            placeholder="Ex: Barcelona"
        )

    with c2:

        equipa_2 = st.text_input(
            "✈️ Time 2",
            placeholder="Ex: Real Madrid"
        )

    if st.button(
        "🤖 ANALISAR H2H",
        type="primary",
        use_container_width=True
    ):

        if not equipa_1.strip() or not equipa_2.strip():

            st.warning(
                "⚠️ Digite os dois times."
            )

        else:

            with st.spinner(
                "🔎 Procurando os times e analisando o H2H..."
            ):

                try:

                    resultado = (
                        engine.analisar_confronto_completo(
                            equipa_1.strip(),
                            equipa_2.strip()
                        )
                    )

                except Exception as e:

                    st.error(
                        f"Erro ao analisar: {e}"
                    )

                    resultado = None

            if resultado:

                mercados = resultado.get(
                    "mercados",
                    {}
                )

                melhor = resultado.get(
                    "melhor_mercado",
                    "Sem dados suficientes"
                )

                chance = resultado.get(
                    "melhor_chance",
                    0
                )

                # ============================================
                # VEREDITO
                # ============================================

                st.markdown(
                    f"""
                    <div class="melhor">
                        🔥 <b>MELHOR OPORTUNIDADE</b>
                        <br><br>
                        <span style="font-size:26px;">
                            {melhor}
                        </span>
                        <br><br>
                        📊 Probabilidade histórica:
                        <b>{chance}%</b>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown("---")

                # ============================================
                # TODOS OS MERCADOS
                # ============================================

                st.subheader(
                    "📊 Análise dos Mercados"
                )

                for mercado, pct in mercados.items():

                    col_a, col_b = st.columns(
                        [4, 1]
                    )

                    with col_a:

                        st.write(
                            f"🎯 {mercado}"
                        )

                        if pct is not None:

                            st.progress(
                                max(
                                    0,
                                    min(
                                        float(pct),
                                        100
                                    )
                                ) / 100
                            )

                    with col_b:

                        if pct is not None:

                            st.metric(
                                "Chance",
                                f"{pct}%"
                            )

                        else:

                            st.write(
                                "Sem dados"
                            )

                st.markdown("---")

                # ============================================
                # H2H ANTERIORES
                # ============================================

                h2h = resultado.get(
                    "h2h",
                    []
                )

                st.subheader(
                    f"📋 Últimos confrontos "
                    f"({len(h2h)})"
                )

                if not h2h:

                    st.info(
                        "Não foram encontrados "
                        "confrontos H2H suficientes."
                    )

                else:

                    for jogo in h2h:

                        st.write(
                            f"⚽ "
                            f"**{jogo.get('home_team', '?')}** "
                            f"{jogo.get('home_score', '?')} "
                            f"- "
                            f"{jogo.get('away_score', '?')} "
                            f"**{jogo.get('away_team', '?')}**"
                        )

                        if jogo.get("date"):

                            st.caption(
                                str(
                                    jogo["date"]
                                )
                            )

                        st.markdown("---")
