import streamlit as st
from datetime import date
from scraper import APIFootballAPI


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
    padding: 16px;
    border-radius: 12px;
    border: 1px solid rgba(16,185,129,.5);
    background: rgba(16,185,129,.10);
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# MOTOR
# ============================================================

if "api" not in st.session_state:

    st.session_state.api = (
        APIFootballAPI()
    )

api = st.session_state.api


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

    if st.button(
        "🧪 Testar API",
        use_container_width=True
    ):

        with st.spinner(
            "Testando conexão..."
        ):

            funcionando = (
                api.testar_api()
            )

        if funcionando:

            st.success(
                "🟢 API-Football funcionando!"
            )

        else:

            st.error(
                "🔴 API não respondeu."
            )

            if api.last_error:

                st.caption(
                    api.last_error
                )

    st.markdown("---")

    st.write(
        "### Mercados"
    )

    st.write(
        "⚽ Ambas marcam"
    )

    st.write(
        "⚽ Mais de 1.5"
    )

    st.write(
        "⚽ Mais de 2.5"
    )

    st.write(
        "⚽ Menos de 3.5"
    )

    st.write(
        "⚽ Menos de 4.5"
    )

    st.write(
        "⚽ Casa ganha ou empata"
    )

    st.write(
        "⚽ Fora ganha ou empata"
    )

    st.write(
        "⚽ Casa ganha"
    )

    st.write(
        "⚽ Fora ganha"
    )


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

    data_pesquisa = st.date_input(
        "📅 Data",
        value=date.today()
    )

    if st.button(
        "🚀 GERAR PALPITES",
        type="primary",
        use_container_width=True
    ):

        data_str = (
            data_pesquisa.strftime(
                "%Y-%m-%d"
            )
        )

        with st.spinner(
            "🔎 Procurando jogos..."
        ):

            jogos = (
                api.get_scheduled_events(
                    data_str
                )
            )

        if not jogos:

            st.warning(
                "⚠️ Nenhum jogo encontrado para esta data."
            )

            if api.last_error:

                st.error(
                    api.last_error
                )

            st.info(
                "Experimente outra data."
            )

        else:

            # Até 12 jogos
            jogos = jogos[:12]

            st.success(
                f"✅ {len(jogos)} jogos encontrados."
            )

            st.markdown("---")

            for numero, jogo in enumerate(
                jogos,
                1
            ):

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"### {numero}. ⚽ "
                        f"{jogo['home_team']} "
                        f"× "
                        f"{jogo['away_team']}"
                    )

                    st.caption(
                        f"🏆 {jogo['tournament']} "
                        f"| "
                        f"{jogo.get('country', '')}"
                    )

                    # --------------------------------
                    # ANÁLISE
                    # --------------------------------

                    with st.spinner(
                        "Analisando..."
                    ):

                        analise = (
                            api.analisar_h2h(
                                jogo[
                                    "home_team"
                                ],
                                jogo[
                                    "away_team"
                                ]
                            )
                        )

                    if analise.get(
                        "erro"
                    ):

                        st.warning(
                            analise["erro"]
                        )

                        continue

                    melhor = analise.get(
                        "melhor_mercado"
                    )

                    chance = analise.get(
                        "melhor_chance"
                    )

                    if chance is not None:

                        st.markdown(
                            f"""
                            <div class="melhor">
                            🔥 <b>MELHOR OPORTUNIDADE</b><br><br>
                            <span style="font-size:22px;">
                            {melhor}
                            </span><br><br>
                            📊 <b>{chance}%</b>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    st.markdown("")

                    mercados = (
                        analise[
                            "mercados"
                        ]
                    )

                    col1, col2 = st.columns(2)

                    lista = list(
                        mercados.items()
                    )

                    meio = (
                        len(lista) + 1
                    ) // 2

                    with col1:

                        for mercado, pct in (
                            lista[:meio]
                        ):

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
                                    min(
                                        pct,
                                        100
                                    ) / 100
                                )

                    with col2:

                        for mercado, pct in (
                            lista[meio:]
                        ):

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
                                    min(
                                        pct,
                                        100
                                    ) / 100
                                )

                    st.caption(
                        f"📊 Forma: "
                        f"{analise['dados_casa']} jogos "
                        f"casa | "
                        f"{analise['dados_fora']} jogos "
                        f"fora | "
                        f"H2H: "
                        f"{analise['dados_h2h']} jogos"
                    )


# ============================================================
# H2H
# ============================================================

with aba_h2h:

    st.subheader(
        "🔎 Análise H2H"
    )

    st.write(
        "Digite as duas equipas. "
        "O sistema procura os nomes automaticamente."
    )

    c1, c2 = st.columns(2)

    with c1:

        equipa_casa = st.text_input(
            "🏠 Equipa 1",
            placeholder="Ex: Barcelona"
        )

    with c2:

        equipa_fora = st.text_input(
            "✈️ Equipa 2",
            placeholder="Ex: Real Madrid"
        )

    if st.button(
        "🤖 ANALISAR CONFRONTO",
        type="primary",
        use_container_width=True
    ):

        if (
            not equipa_casa.strip()
            or
            not equipa_fora.strip()
        ):

            st.warning(
                "Digite as duas equipas."
            )

        else:

            with st.spinner(
                "🔎 Procurando equipas e analisando H2H..."
            ):

                resultado = (
                    api.analisar_h2h(
                        equipa_casa.strip(),
                        equipa_fora.strip()
                    )
                )

            if resultado.get(
                "erro"
            ):

                st.error(
                    resultado["erro"]
                )

            else:

                st.success(
                    "✅ Análise concluída."
                )

                st.markdown("---")

                melhor = resultado[
                    "melhor_mercado"
                ]

                chance = resultado[
                    "melhor_chance"
                ]

                if chance is not None:

                    st.markdown(
                        f"""
                        <div class="melhor">
                        🔥 <b>MELHOR OPORTUNIDADE</b><br><br>
                        <span style="font-size:25px;">
                        {melhor}
                        </span><br><br>
                        📊 Confiança estatística:
                        <b>{chance}%</b>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.markdown("---")

                st.subheader(
                    "📊 Mercados"
                )

                for mercado, pct in (
                    resultado[
                        "mercados"
                    ].items()
                ):

                    if pct is None:

                        st.write(
                            f"⚪ {mercado}: "
                            "Dados insuficientes"
                        )

                    else:

                        col_a, col_b = st.columns(
                            [4, 1]
                        )

                        with col_a:

                            st.write(
                                f"🎯 {mercado}"
                            )

                            st.progress(
                                min(
                                    pct,
                                    100
                                ) / 100
                            )

                        with col_b:

                            st.metric(
                                "Chance",
                                f"{pct}%"
                            )

                st.markdown("---")

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "🏠 Forma Casa",
                    resultado[
                        "dados_casa"
                    ]
                )

                c2.metric(
                    "✈️ Forma Fora",
                    resultado[
                        "dados_fora"
                    ]
                )

                c3.metric(
                    "🔎 H2H",
                    resultado[
                        "dados_h2h"
                    ]
                )

                if resultado[
                    "h2h"
                ]:

                    st.subheader(
                        "📋 Confrontos anteriores"
                    )

                    for jogo in resultado[
                        "h2h"
                    ]:

                        st.write(
                            f"⚽ "
                            f"{jogo['home']} "
                            f"{jogo['home_goals']} "
                            f"- "
                            f"{jogo['away_goals']} "
                            f"{jogo['away']}"
                        )
