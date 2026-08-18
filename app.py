import streamlit as st
import pandas as pd
from datetime import datetime

from scraper import FootballAIEngine
from auditoria import AuditoriaPalpites


# ============================================================
# CONFIGURAÃ‡ÃƒO
# ============================================================

st.set_page_config(
    page_title="FootballAI Predictor Pro",
    page_icon="ðŸ”®",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ESTILO
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        color: #94a3b8;
        font-size: 16px;
        margin-bottom: 25px;
    }

    .match-card {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(148,163,184,.18);
        background: rgba(15,23,42,.55);
        margin-bottom: 15px;
    }

    .team-name {
        font-size: 20px;
        font-weight: 700;
    }

    .market-card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(148,163,184,.18);
        margin-bottom: 10px;
    }

    .best-market {
        font-size: 22px;
        font-weight: 800;
    }

    .small-muted {
        color: #94a3b8;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LIGAS
# ============================================================

LIGAS = [
    "Premier League",
    "La Liga",
    "Serie A Italiana",
    "Bundesliga",
    "Ligue 1",
    "Champions League",
]


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("## ðŸ› ï¸ FootballAI")

liga_atual = st.sidebar.selectbox(
    "Campeonato:",
    LIGAS,
)

aba_selecionada = st.sidebar.radio(
    "NavegaÃ§Ã£o:",
    [
        "ðŸ—“ï¸ Palpites do Dia",
        "ðŸ”Ž Pesquisa H2H",
        "ðŸ“ˆ Desempenho",
    ],
)

st.sidebar.markdown("---")

if st.sidebar.button(
    "ðŸ”„ Sincronizar dados",
    use_container_width=True,
):
    st.cache_data.clear()
    st.sidebar.success("Cache limpo. PrÃ³xima consulta serÃ¡ atualizada.")


# ============================================================
# SESSION STATE
# ============================================================

if (
    "ai_engine" not in st.session_state
    or st.session_state.get("liga_anterior") != liga_atual
):
    st.session_state.ai_engine = FootballAIEngine(
        liga_nome=liga_atual
    )
    st.session_state.liga_anterior = liga_atual

if "auditoria" not in st.session_state:
    st.session_state.auditoria = AuditoriaPalpites()


# ============================================================
# CACHE DOS JOGOS
# ============================================================

@st.cache_data(ttl=600)
def carregar_jogos_reais_cached(
    liga_nome: str,
    data_selecionada: str,
):
    engine = FootballAIEngine(liga_nome=liga_nome)

    return engine.buscar_jogos_reais_api(
        data_selecionada
    )


# ============================================================
# FUNÃ‡ÃƒO DE ANÃLISE SEGURA
# ============================================================

def analisar_jogo(casa, fora):
    try:
        resultado = st.session_state.ai_engine.analisar_confronto_completo(
            casa,
            fora,
        )

        if not isinstance(resultado, dict):
            return None

        return resultado

    except Exception as exc:
        st.error(
            f"NÃ£o foi possÃ­vel analisar {casa} vs {fora}: {exc}"
        )
        return None


# ============================================================
# ABA 1 â€” PALPITES DO DIA
# ============================================================

if aba_selecionada == "ðŸ—“ï¸ Palpites do Dia":

    st.markdown(
        '<div class="main-title">ðŸ”® FootballAI Predictor Pro</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "AnÃ¡lise prÃ©-jogo baseada nos dados disponÃ­veis da Football-Data.org."
        "</div>",
        unsafe_allow_html=True,
    )

    col_data, col_info = st.columns([1, 2])

    with col_data:
        data_escolhida = st.date_input(
            "ðŸ“… Data dos jogos:",
            value=datetime.now().date(),
        )

    data_pesquisa = data_escolhida.strftime("%Y-%m-%d")

    with col_info:
        st.info(
            f"ðŸ† Campeonato selecionado: **{liga_atual}**"
        )

    st.markdown("---")

    with st.spinner(
        "âš½ Procurando jogos oficiais..."
    ):
        lista_jogos = carregar_jogos_reais_cached(
            liga_atual,
            data_pesquisa,
        )

    if not lista_jogos:

        st.warning(
            f"NÃ£o foram encontrados jogos da **{liga_atual}** "
            f"para **{data_pesquisa}**."
        )

        st.caption(
            "Verifique a data, a competiÃ§Ã£o e a chave "
            "FOOTBALL_DATA_ORG_KEY nas Secrets do Streamlit."
        )

    else:

        st.success(
            f"âœ… {len(lista_jogos)} jogo(s) encontrado(s)."
        )

        # ----------------------------------------------------
        # FILTRO OPCIONAL
        # ----------------------------------------------------

        mostrar_jogos = st.slider(
            "Quantidade de jogos para analisar:",
            min_value=1,
            max_value=len(lista_jogos),
            value=min(10, len(lista_jogos)),
        )

        jogos_exibidos = lista_jogos[:mostrar_jogos]

        # ----------------------------------------------------
        # CARDS
        # ----------------------------------------------------

        for idx, jogo in enumerate(jogos_exibidos):

            casa = jogo.get("home", "?")
            fora = jogo.get("away", "?")

            st.markdown(
                '<div class="match-card">',
                unsafe_allow_html=True,
            )

            col_jogo, col_status = st.columns([4, 1])

            with col_jogo:
                st.markdown(
                    f'<div class="team-name">'
                    f'âš½ {casa} vs {fora}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            with col_status:
                st.caption(
                    jogo.get("status", "SCHEDULED")
                )

            data_jogo = jogo.get("date", "")

            if data_jogo:
                try:
                    dt = datetime.fromisoformat(
                        data_jogo.replace("Z", "+00:00")
                    )
                    st.caption(
                        f"ðŸ• {dt.strftime('%d/%m/%Y %H:%M')}"
                    )
                except Exception:
                    pass

            res = analisar_jogo(casa, fora)

            if res:

                st.markdown("---")

                melhor = res.get(
                    "melhor_mercado",
                    "Sem mercado",
                )

                chance = res.get(
                    "melhor_chance",
                    0,
                )

                st.info(
                    f"ðŸŽ¯ **Melhor mercado:** "
                    f"**{melhor}**  \n"
                    f"ðŸ“Š **ConfianÃ§a do modelo:** `{chance}%`"
                )

                combinada_1 = res.get(
                    "combinada_1",
                    "",
                )

                pct_1 = res.get(
                    "pct_combinada_1",
                    0,
                )

                combinada_2 = res.get(
                    "combinada_2",
                    "",
                )

                pct_2 = res.get(
                    "pct_combinada_2",
                    0,
                )

                c1, c2 = st.columns(2)

                with c1:
                    st.markdown(
                        f"ðŸ”¥ **Combo 1**  \n"
                        f"{combinada_1}  \n"
                        f"ConfianÃ§a estimada: **{pct_1}%**"
                    )

                with c2:
                    st.markdown(
                        f"ðŸ›¡ï¸ **Combo 2**  \n"
                        f"{combinada_2}  \n"
                        f"ConfianÃ§a estimada: **{pct_2}%**"
                    )

                # Auditoria
                try:
                    st.session_state.auditoria.registrar_palpite(
                        casa=casa,
                        fora=fora,
                        mercado=melhor,
                        chance=chance,
                        combinada=combinada_1,
                    )
                except Exception:
                    pass

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )


# ============================================================
# ABA 2 â€” H2H
# ============================================================

elif aba_selecionada == "ðŸ”Ž Pesquisa H2H":

    st.markdown(
        '<div class="main-title">ðŸ”Ž AnÃ¡lise H2H</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "Compare duas equipas e veja os mercados calculados pelo modelo."
        "</div>",
        unsafe_allow_html=True,
    )

    with st.spinner("Carregando equipas..."):
        try:
            lista_equipas = (
                st.session_state.ai_engine.obter_todas_equipas()
            )
        except Exception as exc:
            lista_equipas = []
            st.error(
                f"Erro ao carregar equipas: {exc}"
            )

    if not lista_equipas:

        st.warning(
            "NÃ£o foi possÃ­vel carregar as equipas desta competiÃ§Ã£o."
        )

        st.info(
            "Verifique a chave da Football-Data.org e se "
            "a competiÃ§Ã£o estÃ¡ disponÃ­vel no teu plano."
        )

    else:

        c1, c2 = st.columns(2)

        with c1:
            equipa_casa = st.selectbox(
                "ðŸ  Equipa da Casa:",
                lista_equipas,
                index=0,
            )

        with c2:
            index_fora = (
                1 if len(lista_equipas) > 1 else 0
            )

            equipa_fora = st.selectbox(
                "âœˆï¸ Equipa de Fora:",
                lista_equipas,
                index=index_fora,
            )

        st.markdown("---")

        if st.button(
            "ðŸ¤– ANALISAR CONFRONTO",
            use_container_width=True,
            type="primary",
        ):

            with st.spinner(
                "Analisando forma, golos e classificaÃ§Ã£o..."
            ):
                res = analisar_jogo(
                    equipa_casa,
                    equipa_fora,
                )

            if res:

                melhor = res.get(
                    "melhor_mercado",
                    "Sem mercado",
                )

                chance = res.get(
                    "melhor_chance",
                    0,
                )

                st.markdown(
                    "### ðŸŽ¯ VEREDITO DO MODELO"
                )

                st.success(
                    f"**{melhor}** â€” confianÃ§a **{chance}%**"
                )

                try:
                    st.session_state.auditoria.registrar_palpite(
                        casa=equipa_casa,
                        fora=equipa_fora,
                        mercado=melhor,
                        chance=chance,
                        combinada=res.get(
                            "combinada_1",
                            "",
                        ),
                    )
                except Exception:
                    pass

                st.markdown("---")

                # ------------------------------------------------
                # MERCADOS
                # ------------------------------------------------

                st.subheader(
                    "ðŸ“Š Mercados analisados"
                )

                mercados = res.get(
                    "mercados",
                    {},
                )

                if mercados:

                    col_m1, col_m2 = st.columns(2)

                    mercados_lista = list(
                        mercados.items()
                    )

                    metade = (
                        len(mercados_lista) + 1
                    ) // 2

                    with col_m1:
                        for mercado, pct in mercados_lista[:metade]:

                            st.write(
                                f"ðŸ”¹ **{mercado}** â€” {pct}%"
                            )

                            st.progress(
                                max(
                                    0.0,
                                    min(
                                        1.0,
                                        float(pct) / 100,
                                    ),
                                )
                            )

                    with col_m2:
                        for mercado, pct in mercados_lista[metade:]:

                            st.write(
                                f"ðŸ”¹ **{mercado}** â€” {pct}%"
                            )

                            st.progress(
                                max(
                                    0.0,
                                    min(
                                        1.0,
                                        float(pct) / 100,
                                    ),
                                )
                            )

                # ------------------------------------------------
                # COMBINAÃ‡Ã•ES
                # ------------------------------------------------

                st.markdown("---")

                st.subheader(
                    "ðŸ§  CombinaÃ§Ãµes sugeridas"
                )

                combo1 = res.get(
                    "combinada_1",
                    "NÃ£o disponÃ­vel",
                )

                combo2 = res.get(
                    "combinada_2",
                    "NÃ£o disponÃ­vel",
                )

                pct1 = res.get(
                    "pct_combinada_1",
                    0,
                )

                pct2 = res.get(
                    "pct_combinada_2",
                    0,
                )

                c1, c2 = st.columns(2)

                with c1:
                    st.markdown(
                        f"""
                        <div class="market-card">
                            <h4>ðŸ”¥ Combo 1</h4>
                            <div class="best-market">
                                {combo1}
                            </div>
                            <p>
                                ConfianÃ§a estimada:
                                <b>{pct1}%</b>
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with c2:
                    st.markdown(
                        f"""
                        <div class="market-card">
                            <h4>ðŸ›¡ï¸ Combo 2</h4>
                            <div class="best-market">
                                {combo2}
                            </div>
                            <p>
                                ConfianÃ§a estimada:
                                <b>{pct2}%</b>
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # ------------------------------------------------
                # ESTATÃSTICAS BASE
                # ------------------------------------------------

                stats = res.get(
                    "estatisticas",
                    {},
                )

                if stats:

                    st.markdown("---")

                    st.subheader(
                        "ðŸ“ˆ Dados utilizados pelo modelo"
                    )

                    s1, s2, s3, s4 = st.columns(4)

                    s1.metric(
                        "Golos casa",
                        stats.get(
                            "media_golos_casa",
                            "-",
                        ),
                    )

                    s2.metric(
                        "Golos sofridos casa",
                        stats.get(
                            "media_golos_sofridos_casa",
                            "-",
                        ),
                    )

                    s3.metric(
                        "Golos fora",
                        stats.get(
                            "media_golos_fora",
                            "-",
                        ),
                    )

                    s4.metric(
                        "Golos sofridos fora",
                        stats.get(
                            "media_golos_sofridos_fora",
                            "-",
                        ),
                    )

                    p1, p2, p3 = st.columns(3)

                    p1.metric(
                        "PosiÃ§Ã£o casa",
                        stats.get(
                            "posicao_casa",
                            "-",
                        ),
                    )

                    p2.metric(
                        "PosiÃ§Ã£o fora",
                        stats.get(
                            "posicao_fora",
                            "-",
                        ),
                    )

                    p3.metric(
                        "Golos esperados",
                        stats.get(
                            "golos_esperados",
                            "-",
                        ),
                    )


# ============================================================
# ABA 3 â€” DESEMPENHO
# ============================================================

elif aba_selecionada == "ðŸ“ˆ Desempenho":

    st.markdown(
        '<div class="main-title">ðŸ“ˆ Desempenho do Bot</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "HistÃ³rico dos palpites registrados nesta sessÃ£o."
        "</div>",
        unsafe_allow_html=True,
    )

    try:
        stats = (
            st.session_state.auditoria
            .obter_estatisticas_gerais()
        )
    except Exception:
        stats = {
            "win_rate": 0,
            "greens": 0,
            "reds": 0,
            "pendentes": 0,
        }

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "ðŸŽ¯ Taxa de acerto",
        f"{stats.get('win_rate', 0)}%",
    )

    m2.metric(
        "ðŸŸ¢ Greens",
        stats.get("greens", 0),
    )

    m3.metric(
        "ðŸ”´ Reds",
        stats.get("reds", 0),
    )

    m4.metric(
        "â³ Pendentes",
        stats.get("pendentes", 0),
    )

    st.markdown("---")

    st.subheader(
        "ðŸ“‹ HistÃ³rico"
    )

    historico = getattr(
        st.session_state.auditoria,
        "historico",
        [],
    )

    if not historico:

        st.info(
            "Nenhum palpite foi registrado nesta sessÃ£o."
        )

    else:

        df = pd.DataFrame(historico)

        # MantÃ©m compatibilidade caso a auditoria
        # tenha colunas diferentes.
        nomes_colunas = [
            "ID",
            "Data Registro",
            "Equipa Casa",
            "Equipa Fora",
            "Mercado Sugerido",
            "ConfianÃ§a IA",
            "MÃºltipla Sugerida",
            "Resultado ValidaÃ§Ã£o",
            "Placar Final",
        ]

        if len(df.columns) == len(nomes_colunas):
            df.columns = nomes_colunas

        if "ID" in df.columns:
            df = df.sort_values(
                by="ID",
                ascending=False,
            )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# RODAPÃ‰
# ============================================================

st.markdown("---")

st.caption(
    "FootballAI Predictor Pro â€¢ "
    "AnÃ¡lise prÃ©-jogo baseada nos dados disponÃ­veis da API. "
    "As probabilidades sÃ£o estimativas do modelo e nÃ£o garantem resultados."
)
