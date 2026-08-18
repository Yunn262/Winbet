import streamlit as st
import pandas as pd
from datetime import datetime
from scraper import FootballAIEngine
from auditoria import AuditoriaPalpites

st.set_page_config(page_title="FootballAI Predictor Pro", page_icon="📊", layout="wide")

# Configuração da Liga na Barra Lateral
st.sidebar.markdown("## 🛠️ Painel de Controle IA")
liga_atual = st.sidebar.selectbox("Campeonato Base:", ["Premier League", "Brasileirão Série A", "La Liga"])

# Mantém os motores ativos na sessão do Streamlit
if "ai_engine" not in st.session_state or st.session_state.get("liga_anterior") != liga_atual:
    st.session_state.ai_engine = FootballAIEngine(liga_nome=liga_atual)
    st.session_state.liga_anterior = liga_atual
if "auditoria" not in st.session_state:
    st.session_state.auditoria = AuditoriaPalpites()

# FUNÇÃO COM CACHE CRÍTICA: Protege a sua cota diária de 100 chamadas da API
@st.cache_data(ttl=3600)
def carregar_jogos_reais_cached(liga_nome, data_selecionada):
    engine = FootballAIEngine(liga_nome=liga_nome)
    return engine.buscar_jogos_reais_api(data_selecionada)

aba_selecionada = st.sidebar.radio(
    "Navegação do Sistema:",
    ["🗓️ Palpites do Dia (Jogos Reais)", "🔎 Pesquisa de Confrontos H2H", "📈 Desempenho e Assertividade"]
)

# ABA 1: PALPITES COM JOGOS REAIS DA API-FOOTBALL
if aba_selecionada == "🗓️ Palpites do Dia (Jogos Reais)":
    st.title("🗓️ Lista de Palpites com Jogos Reais do Dia")
    st.write("Dados puxados ao vivo diretamente dos servidores da API-Football.")
    
    # Campo de seleção de data para o utilizador buscar qualquer dia
    data_pesquisa = st.date_input("Escolha a data para buscar jogos:", datetime.now()).strftime("%Y-%m-%d")
    
    with st.spinner("Conectando à API-Football e extraindo partidas oficiais..."):
        lista_jogos = carregar_jogos_reais_cached(liga_atual, data_pesquisa)
        
    st.markdown("---")
    
    if not lista_jogos:
        st.warning(f"Nenhum jogo oficial encontrado para a liga {liga_atual} na data {data_pesquisa}.")
        st.info("💡 Dica: Certifique-se de que a sua API Key está configurada nas Secrets do Streamlit.")
    else:
        st.success(f"✅ {len(lista_jogos)} Jogos Reais localizados com sucesso!")
        cols = st.columns(2)
        for idx, jogo in enumerate(lista_jogos):
            with cols[idx % 2]:
                st.markdown(f"### ⚽ Jogo: {jogo['home']} vs {jogo['away']}")
                res = st.session_state.ai_engine.analisar_confronto_completo(jogo['home'], jogo['away'])
                
                st.info(f"💡 **Melhor mercado:** {res['melhor_mercado']} | **Chance:** `{res['melhor_chance']}%`")
                st.caption(f"⚡ *Múltipla Sugerida:* {res['combinada_1']}")
                
                st.session_state.auditoria.registrar_palpite(
                    casa=jogo['home'], fora=jogo['away'], 
                    mercado=res['melhor_mercado'], chance=res['melhor_chance'],
                    combinada=res['combinada_1']
                )
                st.markdown("---")

# ABA 2: PESQUISA AVANÇADA H2H
elif aba_selecionada == "🔎 Pesquisa de Confrontos H2H":
    st.title("🔎 Painel Avançado de Pesquisa H2H")
    st.markdown("---")
    
    lista_equipas = st.session_state.ai_engine.obter_todas_equipas()
    c1, c2 = st.columns(2)
    with c1:
        equipa_casa = st.selectbox("Selecione a Equipa da Casa:", lista_equipas, index=0)
    with c2:
        equipa_fora = st.selectbox("Selecione a Equipa de Fora:", lista_equipas, index=1 if len(lista_equipas) > 1 else 0)
        
    if st.button("🤖 PROCESSAR ANÁLISE PREDITIVA PROFISSIONAL", use_container_width=True):
        res = st.session_state.ai_engine.analisar_confronto_completo(equipa_casa, equipa_fora)
        
        st.markdown("### 🚨 VERDITO FINAL DO MOTOR DE IA")
        st.warning(f"🎯 O melhor mercado será ou é **{res['melhor_mercado']}**  Chance **{res['melhor_chance']}%**")
        st.markdown("---")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.subheader("📊 Linhas de Resultado e Golos")
            for mercado, pct in res["mercados"].items():
                if "Escanteios" not in mercado and "cartões" not in mercado:
                    st.write(f"🔹 {mercado}: **{pct}%**")
                    st.progress(pct / 100)
        with col_m2:
            st.subheader("🎯 Linhas Avançadas (Cantos e Disciplinar)")
            for mercado, pct in res["mercados"].items():
                if "Escanteios" in mercado or "cartões" in mercado:
                    st.write(f"🚩 {mercado}: **{pct}%**")
                    st.progress(pct / 100)

# ABA 3: PERFORMANCES (AUDITORIA)
elif aba_selecionada == "📈 Desempenho e Assertividade":
    st.title("📈 Estatísticas de Assertividade do Bot")
    st.markdown("---")
    
    stats = st.session_state.auditoria.obter_estatisticas_gerais()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🎯 Taxa de Acerto Geral", f"{stats['win_rate']}%")
    m2.metric("🟢 Bilhetes Verdes (Greens)", stats['greens'])
    m3.metric("🔴 Bilhetes Vermelhos (Reds)", stats['reds'])
    m4.metric("⏳ Jogos Aguardando Fim", stats['pendentes'])
    
    st.markdown("---")
    if not st.session_state.auditoria.historico:
        st.info("Nenhum palpite armazenado na base de dados até ao momento.")
    else:
        df_visual = pd.DataFrame(st.session_state.auditoria.historico)
        st.dataframe(df_visual, use_container_width=True)
