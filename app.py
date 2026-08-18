import streamlit as st
import pandas as pd
from scraper import FootballAIEngine
from auditoria import AuditoriaPalpites

st.set_page_config(page_title="FootballAI Predictor Pro", page_icon="📊", layout="wide")

if "ai_engine" not in st.session_state:
    st.session_state.ai_engine = FootballAIEngine()
if "auditoria" not in st.session_state:
    st.session_state.auditoria = AuditoriaPalpites()

# MENU LATERAL
st.sidebar.markdown("## 🛠️ Painel de Controle IA")
aba_selecionada = st.sidebar.radio(
    "Navegação do Sistema:",
    ["🗓️ Palpites do Dia (Lote 10+)", "🔎 Pesquisa de Confrontos H2H", "📈 Desempenho e Assertividade"]
)

st.sidebar.markdown("---")
liga_atual = st.sidebar.selectbox("Campeonato Base:", ["Premier League", "Brasileirão Série A", "La Liga"])
if st.sidebar.button("🔄 Sincronizar Banco de Dados"):
    st.session_state.ai_engine = FootballAIEngine(liga_nome=liga_atual)
    st.sidebar.success("Base de dados sincronizada!")

# ABA 1: PALPITES DO DIA
if aba_selecionada == "🗓️ Palpites do Dia (Lote 10+)":
    st.title("🗓️ Lista Automatizada de Palpites do Dia")
    st.write("Análise preditiva em lote gerada de forma 100% matemática para as próximas 24 horas.")
    st.markdown("---")
    
    lista_jogos = st.session_state.ai_engine.obter_jogos_do_dia()
    
    cols = st.columns(2)
    for idx, jogo in enumerate(lista_jogos):
        with cols[idx % 2]:
            st.markdown(f"### ⚽ Jogo {idx + 1}: {jogo['home']} vs {jogo['away']}")
            res = st.session_state.ai_engine.analisar_confronto_completo(jogo['home'], jogo['away'])
            
            st.info(f"💡 **Melhor mercado:** {res['melhor_mercado']}  Chance {res['melhor_chance']}%")
            st.caption(f"⚡ *Múltipla Sugerida:* {res['combinada_1']}")
            
            st.session_state.auditoria.registrar_palpite(
                casa=jogo['home'], fora=jogo['away'], 
                mercado=res['melhor_mercado'], chance=res['melhor_chance'],
                combinada=res['combinada_1']
            )
            st.markdown("---")

# ABA 2: PESQUISA AVANÇADA
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
        
        st.session_state.auditoria.registrar_palpite(equipa_casa, equipa_fora, res['melhor_mercado'], res['melhor_chance'], res['combinada_1'])
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
                    
        st.markdown("---")
        st.subheader("🧠 Sugestões de Bilhetes e Combinações Criativas (IA)")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown(f"""
            <div style="background-color:#1E293B;padding:15px;border-radius:10px;border-left:5px solid #10B981;">
                <h4 style="margin:0;color:#10B981;">🔥 Combo Combinada Pro</h4>
                <p style="margin:5px 0 0 0;font-size:16px;"><b>{res['combinada_1']}</b></p>
            </div>
            """, unsafe_allow_html=True)
        with col_c2:
            st.markdown(f"""
            <div style="background-color:#1E293B;padding:15px;border-radius:10px;border-left:5px solid #3B82F6;">
                <h4 style="margin:0;color:#3B82F6;">🛡️ Combo Chance Dupla Pro</h4>
                <p style="margin:5px 0 0 0;font-size:16px;"><b>{res['combinada_2']}</b></p>
            </div>
            """, unsafe_allow_html=True)

# ABA 3: PERFORMANCES
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
        st.info("Nenhum palpite registrado na base de dados até ao momento.")
    else:
        df_visual = pd.DataFrame(st.session_state.auditoria.historico)
        df_visual.columns = ["ID", "Data Registro", "Equipa Casa", "Equipa Fora", "Mercado Sugerido", "Confiança IA", "Múltipla Sugerida", "Resultado Validação", "Placar Final"]
        st.dataframe(df_visual.sort_values(by="ID", ascending=False), use_container_width=True)

