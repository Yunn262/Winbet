import streamlit as st
import pandas as pd
from scraper import FootballAIEngine
from auditoria import AuditoriaPalpites

st.set_page_config(page_title="FootballAI Predictor Pro", page_icon="📊", layout="wide")

# Inicialização das classes no estado da sessão do Streamlit
if "ai_engine" not in st.session_state:
    st.session_state.ai_engine = FootballAIEngine()
if "auditoria" not in st.session_state:
    st.session_state.auditoria = AuditoriaPalpites()

# ============================================================
# MENU LATERAL DE NAVEGAÇÃO
# ============================================================
st.sidebar.markdown("## 🛠️ Painel de Controle IA")
aba_selecionada = st.sidebar.radio(
    "Navegação do Sistema:",
    ["🗓️ Palpites do Dia (Lote 10+)", "🔎 Pesquisa de Confrontos H2H", "📈 Desempenho e Assertividade"]
)

st.sidebar.markdown("---")
liga_atual = st.sidebar.selectbox("Campeonato Base:", ["Premier League", "Brasileirão Série A", "La Liga"])
if st.sidebar.button("🔄 Sincronizar Banco de Dados"):
    st.session_state.ai_engine = FootballAIEngine(liga_nome=liga_atual)
    # Executa a liquidação automática ao atualizar os dados históricos do FBref
    st.session_state.auditoria.liquidar_palpites_com_base_dados(st.session_state.ai_engine.df_jogos)
    st.sidebar.success("Base de dados sincronizada e palpites liquidados!")

# ============================================================
# ABA 1: PALPITES DO DIA (GRAVA AUTOMATICAMENTE OS JOGOS)
# ============================================================
if aba_selecionada == "🗓️ Palpites do Dia (Lote 10+)":
    st.title("🗓️ Lista Automatizada de Palpites do Dia")
    st.write("Os palpites gerados aqui são salvos automaticamente para auditoria futura do robô.")
    st.markdown("---")
    
    lista_jogos = st.session_state.ai_engine.obter_jogos_do_dia()
    
    cols = st.columns(2)
    for idx, jogo in enumerate(lista_jogos):
        with cols[idx % 2]:
            st.markdown(f"### ⚽ Jogo {idx + 1}: {jogo['home']} vs {jogo['away']}")
            res = st.session_state.ai_engine.analisar_confronto_completo(jogo['home'], jogo['away'])
            
            st.info(f"💡 **Melhor mercado:** {res['melhor_mercado']} | **Chance:** `{res['melhor_chance']}%`")
            st.caption(f"⚡ *Múltipla:* {res['combinada_1']}")
            
            # Grava no banco de dados de auditoria em segundo plano
            st.session_state.auditoria.registrar_palpite(
                casa=jogo['home'], fora=jogo['away'], 
                mercado=res['melhor_mercado'], chance=res['melhor_chance'],
                combinada=res['combinada_1']
            )
            st.markdown("---")

# ============================================================
# ABA 2: PESQUISA AVANÇADA DE CONFRONTOS
# ============================================================
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
        
        st.warning(f"🎯 O melhor mercado para este confronto é: **{res['melhor_mercado']}** — **Chance: {res['melhor_chance']}%**")
        st.session_state.auditoria.registrar_palpite(equipa_casa, equipa_fora, res['melhor_mercado'], res['melhor_chance'], res['combinada_1'])
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.subheader("📊 Linhas de Resultado e Golos")
            for mercado, pct in res["mercados"].items():
                if "Escanteios" not in mercado and "cartões" not in mercado:
                    st.write(f"🔹 {mercado}: **{pct}%**")
                    st.progress(pct / 100)
        with col_m2:
            st.subheader("🎯 Linhas Avançadas")
            for mercado, pct in res["mercados"].items():
                if "Escanteios" in mercado or "cartões" in mercado:
                    st.write(f"🚩 {mercado}: **{pct}%**")
                    st.progress(pct / 100)

# ============================================================
# ABA 3: PAINEL DE ASSERTIVIDADE (AUDITORIA E MÉTRICAS)
# ============================================================
elif aba_selecionada == "📈 Desempenho e Assertividade":
    st.title("📈 Estatísticas de Assertividade do Bot")
    st.write("Acompanhe o rendimento real da inteligência matemática com base nos resultados reais coletados pós-jogo.")
    st.markdown("---")
    
    # Executa uma liquidação preventiva ao abrir a página
    st.session_state.auditoria.liquidar_palpites_com_base_dados(st.session_state.ai_engine.df_jogos)
    stats = st.session_state.auditoria.obter_estatisticas_gerais()
    
    # Indicadores Visuais de Alta Escaneabilidade (Cards)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🎯 Taxa de Acerto Geral", f"{stats['win_rate']}%")
    m2.metric("🟢 Bilhetes Verdes (Greens)", stats['greens'])
    m3.metric("🔴 Bilhetes Vermelhos (Reds)", stats['reds'])
    m4.metric("⏳ Jogos Aguardando Fim", stats['pendentes'])
    
    st.markdown("---")
    st.subheader("📋 Histórico Completo de Entradas Registradas")
    
    if not st.session_state.auditoria.historico:
        st.info("Nenhum palpite foi gerado ou armazenado na base de dados até ao momento.")
    else:
        # Transforma o JSON do histórico num DataFrame formatado para exibição do Streamlit
        df_historico_visual = pd.DataFrame(st.session_state.auditoria.historico)
        
        # Estilização básica de colunas para melhor legibilidade
        df_historico_visual.columns = [
            "ID", "Data Registro", "Equipa Casa", "Equipa Fora", 
            "Mercado Sugerido", "Confiança IA", "Múltipla Sugerida", "Resultado Validação", "Placar Final"
        ]
        
        # Apresenta a tabela estruturada e interativa
        st.dataframe(df_historico_visual.sort_values(by="ID", ascending=False), use_container_width=True)

