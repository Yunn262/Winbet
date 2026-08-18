"""
FootballAI - Motor de dados usando Football-Data.org API v4

IMPORTANTE:
- Não usa soccerdata
- Não usa FBref
- Não usa Understat
- Não importa o próprio scraper.py
- Usa Football-Data.org diretamente
- A API Key vem de Streamlit Secrets ou variável de ambiente
"""

import os
from typing import Dict, List, Any, Optional

import requests
import streamlit as st


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_URL = "https://api.football-data.org/v4"

COMPETICOES = {
    "Premier League": "PL",
    "Brasileirao Serie A": "BSA",
    "La Liga": "PD",
    "Serie A": "SA",
    "Bundesliga": "BL1",
    "Ligue 1": "FL1",
    "Liga Portugal": "PPL",
    "Champions League": "CL",
}


# ============================================================
# TOKEN
# ============================================================

def obter_token() -> str:
    """
    Procura a chave primeiro nos Secrets do Streamlit
    e depois nas variáveis de ambiente.
    """

    try:
        token = st.secrets.get(
            "FOOTBALL_DATA_ORG_KEY",
            ""
        )

        if token:
            return str(token).strip()

    except Exception:
        pass

    return os.getenv(
        "FOOTBALL_DATA_ORG_KEY",
        ""
    ).strip()


# ============================================================
# MOTOR PRINCIPAL
# ============================================================

class SoccerDataScraper:

    def __init__(
        self,
        league_name: str = "Premier League",
        season: Optional[str] = None
    ):

        self.league_name = league_name

        self.competition = COMPETICOES.get(
            league_name,
            "PL"
        )

        self.season = self.normalizar_temporada(
            season
        )

        self.token = obter_token()

        self.last_events = []

        self.last_error = ""


    # ========================================================
    # TEMPORADA
    # ========================================================

    @staticmethod
    def normalizar_temporada(
        season: Optional[str]
    ) -> Optional[int]:

        if not season:
            return None

        valor = str(season).strip()

        # 2024
        if valor.isdigit() and len(valor) == 4:
            return int(valor)

        # 2024-2025
        if "-" in valor:

            primeiro = valor.split("-")[0]

            if primeiro.isdigit():
                return int(primeiro)

        return None


    # ========================================================
    # REQUEST CENTRAL
    # ========================================================

    def request_api(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ):

        if not self.token:

            self.last_error = (
                "FOOTBALL_DATA_ORG_KEY não foi encontrada."
            )

            return None


        headers = {
            "X-Auth-Token": self.token,
            "Accept": "application/json"
        }


        try:

            resposta = requests.get(
                BASE_URL + endpoint,
                headers=headers,
                params=params or {},
                timeout=25
            )


            if resposta.status_code == 200:

                self.last_error = ""

                return resposta.json()


            if resposta.status_code == 400:

                self.last_error = (
                    "Pedido inválido enviado à "
                    "Football-Data.org."
                )


            elif resposta.status_code == 403:

                self.last_error = (
                    "A Football-Data.org recusou o acesso. "
                    "Verifica a API Key e o plano."
                )


            elif resposta.status_code == 404:

                self.last_error = (
                    "Recurso não encontrado ou indisponível "
                    "para esta competição."
                )


            elif resposta.status_code == 429:

                self.last_error = (
                    "Limite de requisições atingido. "
                    "Aguarda antes de tentar novamente."
                )


            else:

                self.last_error = (
                    f"Erro HTTP {resposta.status_code} "
                    "da Football-Data.org."
                )


            return None


        except requests.RequestException as erro:

            self.last_error = (
                f"Erro de conexão com a API: {erro}"
            )

            return None


    # ========================================================
    # TESTE DA API
    # ========================================================

    def testar_api(self) -> bool:

        dados = self.request_api(
            f"/competitions/{self.competition}"
        )

        return dados is not None


    # ========================================================
    # JOGOS POR DATA
    # ========================================================

    def get_scheduled_events(
        self,
        date_str: str
    ) -> List[Dict[str, Any]]:

        parametros = {
            "dateFrom": date_str,
            "dateTo": date_str
        }


        if self.season:

            parametros["season"] = self.season


        dados = self.request_api(
            f"/competitions/{self.competition}/matches",
            params=parametros
        )


        if not dados:

            self.last_events = []

            return []


        partidas = dados.get(
            "matches",
            []
        )


        eventos = []


        for partida in partidas:

            home = partida.get(
                "homeTeam",
                {}
            ) or {}


            away = partida.get(
                "awayTeam",
                {}
            ) or {}


            score = partida.get(
                "score",
                {}
            ) or {}


            full_time = score.get(
                "fullTime",
                {}
            ) or {}


            home_score = full_time.get(
                "home"
            )


            away_score = full_time.get(
                "away"
            )


            status = partida.get(
                "status",
                "SCHEDULED"
            )


            eventos.append({

                "event_id":
                    partida.get("id"),

                "home_team":
                    home.get("name", "?"),

                "away_team":
                    away.get("name", "?"),

                "home_team_id":
                    home.get("id"),

                "away_team_id":
                    away.get("id"),

                "tournament":
                    (
                        partida.get(
                            "competition",
                            {}
                        ) or {}
                    ).get(
                        "name",
                        self.league_name
                    ),

                "season":
                    (
                        partida.get(
                            "season",
                            {}
                        ) or {}
                    ).get(
                        "startDate",
                        ""
                    ),

                "start_time":
                    partida.get(
                        "utcDate",
                        ""
                    ),

                "status":
                    self.traduzir_status(
                        status
                    ),

                "status_short":
                    status,

                "venue":
                    partida.get(
                        "venue",
                        ""
                    ) or "",

                "referee":
                    self.obter_arbitro(
                        partida
                    ),

                "home_score":
                    home_score,

                "away_score":
                    away_score,

                "raw":
                    partida
            })


        self.last_events = eventos

        return eventos


    # ========================================================
    # STATUS
    # ========================================================

    @staticmethod
    def traduzir_status(
        status: str
    ) -> str:

        estados = {

            "SCHEDULED":
                "Agendado",

            "TIMED":
                "Agendado",

            "IN_PLAY":
                "Em andamento",

            "PAUSED":
                "Intervalo",

            "FINISHED":
                "Terminado",

            "POSTPONED":
                "Adiado",

            "SUSPENDED":
                "Suspenso",

            "CANCELLED":
                "Cancelado"
        }

        return estados.get(
            status,
            status
        )


    # ========================================================
    # ÁRBITRO
    # ========================================================

    @staticmethod
    def obter_arbitro(
        partida: Dict[str, Any]
    ) -> str:

        arbitros = partida.get(
            "referees",
            []
        ) or []


        if not arbitros:
            return ""


        return arbitros[0].get(
            "name",
            ""
        )


    # ========================================================
    # EQUIPAS
    # ========================================================

    def obter_todas_equipas(
        self
    ) -> List[str]:

        parametros = {}

        if self.season:
            parametros["season"] = self.season


        dados = self.request_api(
            f"/competitions/{self.competition}/teams",
            params=parametros
        )


        if not dados:
            return []


        equipas = []


        for equipa in dados.get(
            "teams",
            []
        ):

            nome = equipa.get(
                "name"
            )

            if nome:
                equipas.append(nome)


        return sorted(equipas)


    # ========================================================
    # ID DA EQUIPA
    # ========================================================

    def obter_id_equipa(
        self,
        nome: str
    ) -> Optional[int]:

        alvo = nome.strip().lower()

        parametros = {}

        if self.season:
            parametros["season"] = self.season


        dados = self.request_api(
            f"/competitions/{self.competition}/teams",
            params=parametros
        )


        if not dados:
            return None


        equipas = dados.get(
            "teams",
            []
        )


        # Correspondência exata
        for equipa in equipas:

            nome_api = str(
                equipa.get("name", "")
            ).strip().lower()


            short_name = str(
                equipa.get("shortName", "")
            ).strip().lower()


            if alvo == nome_api or alvo == short_name:

                return equipa.get("id")


        # Correspondência parcial
        for equipa in equipas:

            nome_api = str(
                equipa.get("name", "")
            ).strip().lower()


            if (
                alvo in nome_api
                or nome_api in alvo
            ):

                return equipa.get("id")


        return None


    # ========================================================
    # JOGOS DA EQUIPA
    # ========================================================

    def obter_jogos_equipa(
        self,
        team_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:

        parametros = {
            "status": "FINISHED",
            "limit": limit,
            "competitions": self.competition
        }


        if self.season:
            parametros["season"] = self.season


        dados = self.request_api(
            f"/teams/{team_id}/matches",
            params=parametros
        )


        if not dados:
            return []


        return dados.get(
            "matches",
            []
        )


    # ========================================================
    # ESTATÍSTICAS DA EQUIPA
    # ========================================================

    def get_team_stats_for_ai(
        self,
        equipa_nome: str
    ) -> Dict[str, Any]:

        team_id = self.obter_id_equipa(
            equipa_nome
        )


        if not team_id:

            return {
                "team_name": equipa_nome,
                "jogos_analisados": 0,
                "erro":
                    "Equipa não encontrada."
            }


        jogos = self.obter_jogos_equipa(
            team_id,
            limit=10
        )


        if not jogos:

            return {
                "team_name": equipa_nome,
                "jogos_analisados": 0,
                "erro":
                    "Não existem jogos suficientes."
            }


        dados = []


        for jogo in jogos:

            score = jogo.get(
                "score",
                {}
            ) or {}


            full_time = score.get(
                "fullTime",
                {}
            ) or {}


            gols_casa = full_time.get(
                "home"
            )


            gols_fora = full_time.get(
                "away"
            )


            if (
                gols_casa is None
                or gols_fora is None
            ):
                continue


            home_team = (
                jogo.get(
                    "homeTeam",
                    {}
                ) or {}
            ).get(
                "name",
                ""
            )


            is_home = (
                home_team.lower()
                == equipa_nome.lower()
            )


            if is_home:

                gols_marcados = gols_casa
                gols_sofridos = gols_fora

            else:

                gols_marcados = gols_fora
                gols_sofridos = gols_casa


            total = (
                gols_casa
                + gols_fora
            )


            dados.append({

                "marcados":
                    float(gols_marcados),

                "sofridos":
                    float(gols_sofridos),

                "total":
                    float(total)
            })


        if not dados:

            return {
                "team_name": equipa_nome,
                "jogos_analisados": 0
            }


        quantidade = len(dados)


        media_marcados = (
            sum(
                x["marcados"]
                for x in dados
            )
            / quantidade
        )


        media_sofridos = (
            sum(
                x["sofridos"]
                for x in dados
            )
            / quantidade
        )


        over15 = sum(
            x["total"] >= 2
            for x in dados
        )


        over25 = sum(
            x["total"] >= 3
            for x in dados
        )


        btts = sum(
            x["marcados"] > 0
            and x["sofridos"] > 0
            for x in dados
        )


        vitorias = sum(
            x["marcados"]
            > x["sofridos"]
            for x in dados
        )


        empates = sum(
            x["marcados"]
            == x["sofridos"]
            for x in dados
        )


        derrotas = sum(
            x["marcados"]
            < x["sofridos"]
            for x in dados
        )


        return {

            "team_name":
                equipa_nome,

            "jogos_analisados":
                quantidade,

            "media_golos_marcados":
                round(
                    media_marcados,
                    2
                ),

            "media_golos_sofridos":
                round(
                    media_sofridos,
                    2
                ),

            "over_1_5_pct":
                round(
                    over15
                    / quantidade
                    * 100,
                    1
                ),

            "over_2_5_pct":
                round(
                    over25
                    / quantidade
                    * 100,
                    1
                ),

            "btts_pct":
                round(
                    btts
                    / quantidade
                    * 100,
                    1
                ),

            "vitorias_pct":
                round(
                    vitorias
                    / quantidade
                    * 100,
                    1
                ),

            "empates_pct":
                round(
                    empates
                    / quantidade
                    * 100,
                    1
                ),

            "derrotas_pct":
                round(
                    derrotas
                    / quantidade
                    * 100,
                    1
                )
        }


    # ========================================================
    # H2H
    # ========================================================

    def pesquisar_jogo(
        self,
        equipa_casa: str,
        equipa_fora: str
    ) -> List[Dict[str, Any]]:

        id_casa = self.obter_id_equipa(
            equipa_casa
        )


        if not id_casa:
            return []


        jogos = self.obter_jogos_equipa(
            id_casa,
            limit=100
        )


        resultados = []


        alvo = equipa_fora.lower()


        for jogo in jogos:

            home = (
                jogo.get(
                    "homeTeam",
                    {}
                ) or {}
            )


            away = (
                jogo.get(
                    "awayTeam",
                    {}
                ) or {}
            )


            nome_home = home.get(
                "name",
                ""
            )


            nome_away = away.get(
                "name",
                ""
            )


            if (
                alvo not in nome_home.lower()
                and alvo not in nome_away.lower()
            ):
                continue


            score = jogo.get(
                "score",
                {}
            ) or {}


            full_time = score.get(
                "fullTime",
                {}
            ) or {}


            gols_home = full_time.get(
                "home"
            )


            gols_away = full_time.get(
                "away"
            )


            resultados.append({

                "date":
                    jogo.get(
                        "utcDate",
                        ""
                    ),

                "home_team":
                    nome_home,

                "away_team":
                    nome_away,

                "score":
                    f"{gols_home if gols_home is not None else '?'}"
                    f"-"
                    f"{gols_away if gols_away is not None else '?'}",

                "home_score":
                    gols_home,

                "away_score":
                    gols_away,

                "status":
                    jogo.get(
                        "status",
                        ""
                    )
            })


        return resultados


    # ========================================================
    # ANÁLISE COMPLETA
    # ========================================================

    def analisar_confronto_completo(
        self,
        equipa_casa: str,
        equipa_fora: str
    ) -> Dict[str, Any]:

        casa = self.get_team_stats_for_ai(
            equipa_casa
        )


        fora = self.get_team_stats_for_ai(
            equipa_fora
        )


        over15_casa = float(
            casa.get(
                "over_1_5_pct",
                0
            )
        )


        over15_fora = float(
            fora.get(
                "over_1_5_pct",
                0
            )
        )


        over25_casa = float(
            casa.get(
                "over_2_5_pct",
                0
            )
        )


        over25_fora = float(
            fora.get(
                "over_2_5_pct",
                0
            )
        )


        btts_casa = float(
            casa.get(
                "btts_pct",
                0
            )
        )


        btts_fora = float(
            fora.get(
                "btts_pct",
                0
            )
        )


        win_casa = float(
            casa.get(
                "vitorias_pct",
                0
            )
        )


        win_fora = float(
            fora.get(
                "vitorias_pct",
                0
            )
        )


        draw_casa = float(
            casa.get(
                "empates_pct",
                0
            )
        )


        draw_fora = float(
            fora.get(
                "empates_pct",
                0
            )
        )


        loss_casa = float(
            casa.get(
                "derrotas_pct",
                0
            )
        )


        loss_fora = float(
            fora.get(
                "derrotas_pct",
                0
            )
        )


        over15 = (
            over15_casa * 0.5
            + over15_fora * 0.5
        )


        over25 = (
            over25_casa * 0.5
            + over25_fora * 0.5
        )


        btts = (
            btts_casa * 0.5
            + btts_fora * 0.5
        )


        vitoria_casa = (
            win_casa * 0.65
            + loss_fora * 0.35
        )


        vitoria_fora = (
            win_fora * 0.65
            + loss_casa * 0.35
        )


        empate = (
            draw_casa * 0.5
            + draw_fora * 0.5
        )


        casa_ou_empate = min(
            99,
            vitoria_casa + empate
        )


        fora_ou_empate = min(
            99,
            vitoria_fora + empate
        )


        menos35 = max(
            1,
            100 - over25
        )


        mercados = {

            "Mais de 1.5 golos":
                self.limitar(
                    over15
                ),

            "Mais de 2.5 golos":
                self.limitar(
                    over25
                ),

            "Menos de 3.5 golos":
                self.limitar(
                    menos35
                ),

            "Ambas Marcam":
                self.limitar(
                    btts
                ),

            "Casa ou Empate (1X)":
                self.limitar(
                    casa_ou_empate
                ),

            "Fora ou Empate (X2)":
                self.limitar(
                    fora_ou_empate
                ),

            "Vitória Casa":
                self.limitar(
                    vitoria_casa
                ),

            "Vitória Fora":
                self.limitar(
                    vitoria_fora
                ),

            "Empate":
                self.limitar(
                    empate
                )
        }


        # Se não houver dados suficientes,
        # não apresenta confiança artificialmente alta.

        jogos_casa = casa.get(
            "jogos_analisados",
            0
        )


        jogos_fora = fora.get(
            "jogos_analisados",
            0
        )


        if (
            jogos_casa < 3
            or jogos_fora < 3
        ):

            mercados = {
                mercado:
                    min(valor, 65)
                for mercado, valor
                in mercados.items()
            }


        ordenados = sorted(
            mercados.items(),
            key=lambda x: x[1],
            reverse=True
        )


        melhor_mercado = ordenados[0][0]
        melhor_chance = ordenados[0][1]


        # Combinações simples.
        # Não usamos escanteios/cartões porque
        # esses dados não vêm deste endpoint.

        combinada_1 = (
            "Mais de 1.5 golos + "
            + melhor_mercado
        )


        combinada_2 = (
            "Mais de 1.5 golos + "
            "Ambas Marcam"
        )


        pct_combinada_1 = self.limitar(
            min(
                over15,
                melhor_chance
            ) * 0.90
        )


        pct_combinada_2 = self.limitar(
            min(
                over15,
                btts
            ) * 0.85
        )


        media_golos_casa = float(
            casa.get(
                "media_golos_marcados",
                0
            )
        )


        media_golos_fora = float(
            fora.get(
                "media_golos_marcados",
                0
            )
        )


        media_sofridos_casa = float(
            casa.get(
                "media_golos_sofridos",
                0
            )
        )


        media_sofridos_fora = float(
            fora.get(
                "media_golos_sofridos",
                0
            )
        )


        return {

            "melhor_mercado":
                melhor_mercado,

            "melhor_chance":
                melhor_chance,

            "mercados":
                mercados,

            "combinada_1":
                combinada_1,

            "pct_combinada_1":
                pct_combinada_1,

            "combinada_2":
                combinada_2,

            "pct_combinada_2":
                pct_combinada_2,

            "estatisticas": {

                "media_golos_casa":
                    round(
                        media_golos_casa,
                        2
                    ),

                "media_golos_sofridos_casa":
                    round(
                        media_sofridos_casa,
                        2
                    ),

                "media_golos_fora":
                    round(
                        media_golos_fora,
                        2
                    ),

                "media_golos_sofridos_fora":
                    round(
                        media_sofridos_fora,
                        2
                    ),

                "jogos_casa":
                    jogos_casa,

                "jogos_fora":
                    jogos_fora
            }
        }


    # ========================================================
    # LIMITAR PERCENTAGEM
    # ========================================================

    @staticmethod
    def limitar(
        valor: float
    ) -> int:

        return int(
            max(
                1,
                min(
                    99,
                    round(valor)
                )
            )
        )


# ============================================================
# COMPATIBILIDADE COM O APP.PY
# ============================================================

FootballAIEngine = SoccerDataScraper
