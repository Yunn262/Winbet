import streamlit as st
import pandas as pd
from datetime import datetime
from scraper import FootballAIEngine
from auditoria import AuditoriaPalpites

# Configurações de layout profissionais e responsivas
st.set_page_config(page_title="FootballAI Predictor Pro", page_icon="🔮", layout="wide")

# Configuração da Liga na Barra Lateral (Mapeado de acordo com o plano grátis da Football-Data.org)
st.sidebar.markdown("## 🛠️ Painel de Controle IA")
liga_atual = st.sidebar.selectbox(
    "Campeonato Base:", 
    ["Premier League", "La Liga", "Serie A Italiana", "Bundesliga", "Ligue 1", "Champions League"]
)

# Mantém os motores de IA e auditoria ativos na sessão do Streamlit
if "ai_engine" not in st.session_state or st.session_state.get("liga_anterior") != liga_atual:
    st.session_state.ai_engine = FootballAIEngine(liga_nome=liga_atual)
    st.session_state.liga_anterior = liga_atual
if "auditoria" not in st.session_state:
    st.session_state.auditoria = AuditoriaPalpites()

# FUNÇÃO COM CACHE: Essencial para proteger as suas 10 requisições por minuto da Football-Data
@st.cache_data(ttl=600)  # Guarda em cache por 10 minutos
def carregar_jogos_reais_cached(liga_nome, data_selecionada):
    engine = FootballAIEngine(liga_nome=liga_nome)
    return engine.buscar_jogos_reais_api(data_selecionada)

# Menu de navegação lateral por abas
aba_selecionada = st.sidebar.radio(
    "Navegação do Sistema:",
    ["🗓️ Palpites do Dia (Jogos Reais)", "🔎 Pesquisa de Confrontos H2H", "📈 Desempenho e Assertividade"]
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Sincronizar Banco de Dados"):
    st.cache_data.clear()  # Limpa o cache para forçar uma nova consulta fresca à API
    st.sidebar.success("Cache limpo! Os dados serão atualizados na próxima consulta.")

# ============================================================
# ABA 1: PALPITES DO DIA (JOGOS REAIS DA LIGA SELECIONADA)
# ============================================================
if aba_selecionada == "🗓️ Palpites do Dia (Jogos Reais)":
    st.title("🗓️ Lista de Palpites com Jogos Reais do Dia")
    st.write(f"Análise preditiva em lote puxada diretamente dos servidores da Football-Data.org para a **{liga_atual}**.")
    
    # Campo para o utilizador buscar jogos de qualquer dia do calendário
    data_pesquisa = st.date_input("Escolha a data para buscar jogos:", datetime.now()).strftime("%Y-%m-%d")
    
    with st.spinner("Conectando à API Football-Data e extraindo partidas oficiais..."):
        lista_jogos = carregar_jogos_reais_cached(liga_atual, data_pesquisa)
        
    st.markdown("---")
    
    if not lista_jogos:
        st.warning(f"Nenhum jogo oficial encontrado para a liga {liga_atual} na data {data_pesquisa}.")
        st.info("💡 **Dica:** Lembre-se que o plano gratuito cobre apenas as ligas principais da Europa. Certifique-se também de que o seu `FOOTBALL_DATA_TOKEN` está configurado nas Secrets do Streamlit.")
    else:
        st.success(f"✅ {len(lista_jogos)} Jogos Reais localizados para hoje!")
        
        # Exibe os jogos em uma grelha de 2 colunas
        cols = st.columns(2)
        for idx, jogo in enumerate(lista_jogos):
            with cols[idx % 2]:
                st.markdown(f"### ⚽ Jogo: {jogo['home']} vs {jogo['away']}")
                res = st.session_state.ai_engine.analisar_confronto_completo(jogo['home'], jogo['away'])
                
                # Exibição do palpite estrito solicitado
                st.info(f"💡 **Melhor mercado será ou é:** {res['melhor_mercado']} | **Chance:** `{res['melhor_chance']}%`")
                st.caption(f"⚡ *Múltipla Sugerida:* {res['combinada_1']}")
                
                # Grava no banco de dados de auditoria em segundo plano para o histórico
                st.session_state.auditoria.registrar_palpite(
                    casa=jogo['home'], fora=jogo['away'], 
                    mercado=res['melhor_mercado'], chance=res['melhor_chance'],
                    combinada=res['combinada_1']
                )
                st.markdown("---")

# ============================================================
# ABA 2: PESQUISA AVANÇADA DE CONFRONTOS PERSONALIZADOS (H2H)
# ============================================================
elif aba_selecionada == "🔎 Pesquisa de Confrontos H2H":
    st.title("🔎 Painel Avançado de Pesquisa H2H")
    st.write("Escolha ou pesquise duas equipas da lista oficial da liga para detalhar as percentagens de todas as linhas de mercados.")
    st.markdown("---")
    
    lista_equipas = st.session_state.ai_engine.obter_todas_equipas()
    
    c1, c2 = st.columns(2)
    with c1:
        equipa_casa = st.selectbox("Selecione a Equipa da Casa:", lista_equipas, index=0)
    with c2:
        equipa_fora = st.selectbox("Selecione a Equipa de Fora:", lista_equipas, index=1 if len(lista_equipas) > 1 else 0)
        
    if st.button("🤖 PROCESSAR ANÁLISE PREDITIVA PROFISSIONAL", use_container_width=True):
        res = st.session_state.ai_engine.analisar_confronto_completo(equipa_casa, equipa_fora)
        
        # CARD DE DESTAQUE SUPERIOR: VERDITO DO ALGORITMO
        st.markdown("### 🚨 VERDITO FINAL DO MOTOR DE IA")
        st.warning(f"🎯 O melhor mercado será ou é **{res['melhor_mercado']}** — Chance **{res['melhor_chance']}%**")
        
        # Salva a consulta na auditoria
        st.session_state.auditoria.registrar_palpite(equipa_casa, equipa_fora, res['melhor_mercado'], res['melhor_chance'], res['combinada_1'])
        st.markdown("---")
        
        # Divisão de mercados em duas colunas com barras de progresso visuais
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
        
        # SEÇÃO DE ELABORAÇÃO DE COMBINAÇÕES SEGUIDAS E PERSONALIZADAS (EXIGIDO)
        st.subheader("🧠 Sugestões de Bilhetes Criativos e Combinados pela IA")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown(f"""
            <div style="background-color:#1E293B;padding:18px;border-radius:10px;border-left:5px solid #10B981;">
                <h4 style="margin:0;color:#10B981;font-size:16px;">🔥 Combo Bilhete Múltiplo Pro</h4>
                <p style="margin:8px 0 8px 0;font-size:16px;color:white;"><b>{res['combinada_1']}</b></p>
                <span style="background-color:#10B981;color:black;padding:2px 6px;border-radius:4px;font-weight:bold;font-size:12px;">Previsão IA: {res['pct_combinada_1']}%</span>
            </div>
            """, unsafe_allow_html=True)
            
        with col_c2:
            st.markdown(f"""
            <div style="background-color:#1E293B;padding:18px;border-radius:10px;border-left:5px solid #3B82F6;">
                <h4 style="margin:0;color:#3B82F6;font-size:16px;">🛡️ Combo Chance Dupla Pro</h4>
                <p style="margin:8px 0 8px 0;font-size:16px;color:white;"><b>{res['combinada_2']}</b></p>
                <span style="background-color:#3B82F6;color:white;padding:2px 6px;border-radius:4px;font-weight:bold;font-size:12px;">Previsão IA: {res['pct_combinada_2']}%</span>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# ABA 3: PAINEL DE ASSERTIVIDADE (AUDITORIA HISTÓRICA)
# ============================================================
elif aba_selecionada == "📈 Desempenho e Assertividade":
    st.title("📈 Estatísticas de Assertividade do Bot")
    st.write("Acompanhe o rendimento real do modelo matemático em tempo real com base nas entradas registradas.")
    st.markdown("---")
    
    stats = st.session_state.auditoria.obter_estatisticas_gerais()
    
    # Cards de indicadores superiores
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🎯 Taxa de Acerto Geral", f"{stats['win_rate']}%")
    m2.metric("🟢 Bilhetes Verdes (Greens)", stats['greens'])
    m3.metric("🔴 Bilhetes Vermelhos (Reds)", stats['reds'])
    m4.metric("⏳ Jogos Aguardando Fim", stats['pendentes'])
    
    st.markdown("---")
    st.subheader("📋 Histórico Completo de Entradas Registradas")
    
    if not st.session_state.auditoria.historico:
        st.info("Nenhum palpite foi gerado ou armazenado na base de dados local até ao momento.")
    else:
        df_visual = pd.DataFrame(st.session_state.auditoria.historico)
        df_visual.columns = [
            "ID", "Data Registro", "Equipa Casa", "Equipa Fora", 
            "Mercado Sugerido", "Confiança IA", "Múltipla Sugerida", "Resultado Validação", "Placar Final"
        ]
        # Exibe a tabela invertida para mostrar as entradas mais recentes no topo
        st.dataframe(df_visual.sort_values(by="ID", ascending=False), use_container_width=True)
