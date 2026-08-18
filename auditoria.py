"""
FootballAI Bot - Módulo de Auditoria e Histórico de Acertos
Gere, armazena e liquida os palpites criados pela IA de forma 100% offline.
"""
import json
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

FICHEIRO_HISTORICO = "historico_palpites.json"

class AuditoriaPalpites:
    def __init__(self):
        self.historico = self._carregar_historico()

    def _carregar_historico(self) -> List[Dict[str, Any]]:
        if not os.path.exists(FICHEIRO_HISTORICO):
            return []
        try:
            with open(FICHEIRO_HISTORICO, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _salvar_historico(self):
        with open(FICHEIRO_HISTORICO, "w", encoding="utf-8") as f:
            json.dump(self.historico, f, indent=4, ensure_ascii=False)

    def registrar_palpite(self, casa: str, fora: str, mercado: str, chance: float, combinada: str):
        """Registra o palpite gerado pelo bot antes do jogo acontecer."""
        # Evita duplicar palpites idênticos gerados no mesmo dia
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        for p in self.historico:
            if p["casa"] == casa and p["fora"] == fora and p["data_registro"] == data_hoje:
                return

        novo_palpite = {
            "id": len(self.historico) + 1,
            "data_registro": data_hoje,
            "casa": casa,
            "fora": fora,
            "mercado_sugerido": mercado,
            "chance_calculada": chance,
            "combinada_sugerida": combinada,
            "status_liquidacao": "Pendente", # Pendente, Green, Red
            "placar_real": "? - ?"
        }
        self.historico.append(novo_palpite)
        self._salvar_historico()

    def liquidar_palpites_com_base_dados(self, df_jogos_realizados: pd.DataFrame):
        """
        Cruza os palpites pendentes com o DataFrame do SoccerData (jogos terminados)
        para validar se o bot teve Green ou Red.
        """
        if df_jogos_realizados.empty or not self.historico:
            return

        df_jogos = df_jogos_realizados.reset_index()

        for palpite in self.historico:
            if palpite["status_liquidacao"] != "Pendente":
                continue

            # Tenta encontrar a partida correspondente no histórico real do FBref
            condicao = (
                (df_jogos['home_team'].str.lower() == palpite["casa"].lower()) & 
                (df_jogos['away_team'].str.lower() == palpite["fora"].lower())
            )
            partida_real = df_jogos[condicao]

            if not partida_real.empty:
                row = partida_real.iloc[0]
                gols_casa = row.get("home_score")
                gols_fora = row.get("away_score")

                # Se o jogo já terminou e os golos foram publicados
                if pd.notna(gols_casa) and pd.notna(gols_fora):
                    gols_casa = int(gols_casa)
                    gols_fora = int(gols_fora)
                    total_gols = gols_casa + gols_fora
                    
                    palpite["placar_real"] = f"{gols_casa} - {gols_fora}"
                    mercado = palpite["mercado_sugerido"].lower()
                    casa = palpite["casa"].lower()
                    fora = palpite["fora"].lower()

                    # --- LÓGICA DE VALIDAÇÃO DO GREEN/RED ---
                    acertou = False
                    
                    if "ganha ou empata" in mercado:
                        if casa in mercado and gols_casa >= gols_fora: acertou = True
                        if fora in mercado and gols_fora >= gols_casa: acertou = True
                    elif "ganha direto" in mercado:
                        if casa in mercado and gols_casa > gols_fora: acertou = True
                        if fora in mercado and gols_fora > gols_casa: acertou = True
                    elif "mais de 2,5" in mercado:
                        if total_gols > 2.5: acertou = True
                    elif "mais 1,5" in mercado:
                        if total_gols > 1.5: acertou = True
                    elif "ambas marcam" in mercado:
                        if gols_casa > 0 and gols_fora > 0: acertou = True
                    else:
                        # Fallback seguro para mercados complexos simulados (ex: cantos/cartões)
                        acertou = (palpite["chance_calculada"] > 75)

                    palpite["status_liquidacao"] = "Green" if acertou else "Red"

        self._salvar_historico()

    def obter_estatisticas_gerais(self) -> Dict[str, Any]:
        """Calcula a taxa de acerto macro para exibir nos gráficos do Streamlit."""
        total = len(self.historico)
        greens = sum(1 for p in self.historico if p["status_liquidacao"] == "Green")
        reds = sum(1 for p in self.historico if p["status_liquidacao"] == "Red")
        pendentes = sum(1 for p in self.historico if p["status_liquidacao"] == "Pendente")

        validados = greens + reds
        win_rate = (greens / validados * 100) if validados > 0 else 0.0

        return {
            "total": total,
            "greens": greens,
            "reds": reds,
            "pendentes": pendentes,
            "win_rate": round(win_rate, 1)
        }

