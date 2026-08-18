# ============================================================
# scraper.py
# FOOTBALL AI BOT - API-FOOTBALL
# ============================================================

import requests
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any


BASE_URL = "https://v3.football.api-sports.io"


# ============================================================
# API KEY
# ============================================================

def obter_api_key() -> str:
    """
    Streamlit Cloud:
    
    Settings
    -> Secrets
    
    API_FOOTBALL_KEY = "SUA_CHAVE"
    """

    try:
        chave = st.secrets["API_FOOTBALL_KEY"]
        return str(chave).strip()
    except Exception:
        return ""


# ============================================================
# ENGINE
# ============================================================

class FootballAIEngine:

    def __init__(self, liga_nome: str = "Premier League"):

        self.liga_nome = liga_nome
        self.api_key = obter_api_key()

        self.headers = {
            "x-apisports-key": self.api_key,
            "Accept": "application/json"
        }

        self.ligas = {
            "Premier League": 39,
            "La Liga": 140,
            "Serie A Italiana": 135,
            "Bundesliga": 78,
            "Ligue 1": 61,
            "Champions League": 2,
            "Brasileirao Serie A": 71,
            "Liga Portugal": 94,
            "Primeira Liga": 94,
            "Eredivisie": 88,
            "Noruega": 103,
            "Escócia": 179,
            "Dinamarca": 119,
            "Polônia": 106,
            "Bulgária": 172
        }

        self.league_id = self.ligas.get(
            liga_nome,
            39
        )

        self.season = self._obter_temporada()

        # diagnóstico
        self.last_error = ""
        self.last_results = 0

    # ========================================================
    # TEMPORADA CORRETA
    # ========================================================

    def _obter_temporada(self) -> int:
        """
        API-Football representa uma temporada europeia
        pelo ano em que ela começa.

        Exemplo:
        2025/26 -> season=2025
        2026/27 -> season=2026
        """

        hoje = datetime.now()

        if hoje.month >= 8:
            return hoje.year

        return hoje.year - 1

    # ========================================================
    # REQUEST
    # ========================================================

    def _get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:

        self.last_error = ""

        if not self.api_key:

            self.last_error = (
                "API_FOOTBALL_KEY não encontrada nos Secrets."
            )

            return None

        try:

            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=self.headers,
                params=params or {},
                timeout=25
            )

            # -----------------------------------------------
            # HTTP ERROR
            # -----------------------------------------------

            if response.status_code != 200:

                self.last_error = (
                    f"HTTP {response.status_code}: "
                    f"{response.text[:500]}"
                )

                return None

            data = response.json()

            # -----------------------------------------------
            # ERRO DA API
            # -----------------------------------------------

            erros = data.get("errors", {})

            if erros:

                self.last_error = str(erros)

                return data

            self.last_results = int(
                data.get("results", 0) or 0
            )

            return data

        except requests.Timeout:

            self.last_error = (
                "Tempo limite excedido ao contactar a API."
            )

            return None

        except requests.RequestException as e:

            self.last_error = (
                f"Erro de conexão: {e}"
            )

            return None

        except Exception as e:

            self.last_error = (
                f"Erro inesperado: {e}"
            )

            return None

    # ========================================================
    # DIAGNÓSTICO
    # ========================================================

    def diagnostico(self) -> Dict[str, Any]:

        if not self.api_key:

            return {
                "ok": False,
                "mensagem": "API_FOOTBALL_KEY não configurada.",
                "liga": self.liga_nome,
                "league_id": self.league_id,
                "season": self.season
            }

        data = self._get(
            "/status"
        )

        if not data:

            return {
                "ok": False,
                "mensagem": self.last_error,
                "liga": self.liga_nome,
                "league_id": self.league_id,
                "season": self.season
            }

        return {
            "ok": True,
            "mensagem": "API-Football conectada.",
            "liga": self.liga_nome,
            "league_id": self.league_id,
            "season": self.season,
            "resultados": data.get("results", 0)
        }

    # ========================================================
    # COMPETIÇÃO / TEMPORADA
    # ========================================================

    def verificar_liga_temporada(self) -> Dict[str, Any]:

        data = self._get(
            "/leagues",
            {
                "id": self.league_id,
                "season": self.season
            }
        )

        if not data:

            return {
                "ok": False,
                "mensagem": self.last_error
            }

        resposta = data.get(
            "response",
            []
        )

        if not resposta:

            return {
                "ok": False,
                "mensagem": (
                    f"A liga {self.liga_nome} "
                    f"não possui dados para season={self.season}."
                )
            }

        item = resposta[0]

        liga = item.get(
            "league",
            {}
        )

        return {
            "ok": True,
            "id": liga.get("id"),
            "nome": liga.get("name"),
            "pais": item.get("country", {}).get("name"),
            "season": self.season,
            "coverage": item.get(
                "seasons",
                [{}]
            )[0].get(
                "coverage",
                {}
            )
        }

    # ========================================================
    # JOGOS POR DATA
    # ========================================================

    def get_scheduled_events(
        self,
        date_str: str
    ) -> List[Dict]:

        """
        Busca jogos reais da liga para uma data.

        Exemplo:
        2026-08-18
        """

        try:
            datetime.strptime(
                date_str,
                "%Y-%m-%d"
            )
        except ValueError:

            self.last_error = (
                "Data inválida. Use YYYY-MM-DD."
            )

            return []

        params = {
            "league": self.league_id,
            "season": self.season,
            "date": date_str
        }

        data = self._get(
            "/fixtures",
            params
        )

        if not data:

            return []

        resposta = data.get(
            "response",
            []
        )

        jogos = []

        for item in resposta:

            fixture = item.get(
                "fixture",
                {}
            )

            teams = item.get(
                "teams",
                {}
            )

            goals = item.get(
                "goals",
                {}
            )

            league = item.get(
                "league",
                {}
            )

            status = fixture.get(
                "status",
                {}
            )

            home = teams.get(
                "home",
                {}
            )

            away = teams.get(
                "away",
                {}
            )

            jogos.append({

                "fixture_id":
                    fixture.get("id"),

                "event_id":
                    fixture.get("id"),

                "home_team":
                    home.get("name", "?"),

                "away_team":
                    away.get("name", "?"),

                "home_team_id":
                    home.get("id"),

                "away_team_id":
                    away.get("id"),

                "home_logo":
                    home.get("logo"),

                "away_logo":
                    away.get("logo"),

                "league":
                    league.get("name"),

                "league_id":
                    league.get("id"),

                "country":
                    league.get("country"),

                "round":
                    league.get("round"),

                "date":
                    fixture.get("date"),

                "start_time":
                    fixture.get("date"),

                "timezone":
                    fixture.get("timezone"),

                "status":
                    status.get("long"),

                "status_short":
                    status.get("short"),

                "elapsed":
                    status.get("elapsed"),

                "venue":
                    fixture.get(
                        "venue",
                        {}
                    ).get("name"),

                "referee":
                    fixture.get("referee"),

                "home_score":
                    goals.get("home"),

                "away_score":
                    goals.get("away"),

                "raw":
                    item
            })

        jogos.sort(
            key=lambda x: x.get(
                "start_time"
            ) or ""
        )

        return jogos

    # ========================================================
    # COMPATIBILIDADE COM APP ANTIGO
    # ========================================================

    def buscar_jogos_reais_api(
        self,
        data_selecionada: str
    ) -> List[Dict]:

        return self.get_scheduled_events(
            data_selecionada
        )

    # ========================================================
    # PESQUISAR EQUIPA
    # ========================================================

    def procurar_equipa(
        self,
        nome: str
    ) -> Optional[Dict]:

        nome = str(nome).strip()

        if not nome:
            return None

        data = self._get(
            "/teams",
            {
                "search": nome
            }
        )

        if not data:
            return None

        resposta = data.get(
            "response",
            []
        )

        if not resposta:
            return None

        nome_lower = nome.lower()

        # Primeiro tenta correspondência exata
        for item in resposta:

            team = item.get(
                "team",
                {}
            )

            nome_api = str(
                team.get("name", "")
            )

            if nome_api.lower() == nome_lower:

                return team

        # Depois procura parcialmente
        for item in resposta:

            team = item.get(
                "team",
                {}
            )

            nome_api = str(
                team.get("name", "")
            )

            if nome_lower in nome_api.lower():

                return team

        return resposta[0].get(
            "team"
        )

    # ========================================================
    # H2H
    # ========================================================

    def pesquisar_h2h(
        self,
        equipa_casa: str,
        equipa_fora: str,
        ultimos: int = 10
    ) -> List[Dict]:

        casa = self.procurar_equipa(
            equipa_casa
        )

        fora = self.procurar_equipa(
            equipa_fora
        )

        if not casa or not fora:

            return []

        casa_id = casa.get("id")
        fora_id = fora.get("id")

        if not casa_id or not fora_id:

            return []

        data = self._get(
            "/fixtures/headtohead",
            {
                "h2h": f"{casa_id}-{fora_id}",
                "last": ultimos
            }
        )

        if not data:

            return []

        resposta = data.get(
            "response",
            []
        )

        confrontos = []

        for item in resposta:

            fixture = item.get(
                "fixture",
                {}
            )

            teams = item.get(
                "teams",
                {}
            )

            goals = item.get(
                "goals",
                {}
            )

            home = teams.get(
                "home",
                {}
            )

            away = teams.get(
                "away",
                {}
            )

            hg = goals.get("home")
            ag = goals.get("away")

            confrontos.append({

                "fixture_id":
                    fixture.get("id"),

                "date":
                    fixture.get("date"),

                "home_team":
                    home.get("name"),

                "away_team":
                    away.get("name"),

                "home_team_id":
                    home.get("id"),

                "away_team_id":
                    away.get("id"),

                "home_score":
                    hg,

                "away_score":
                    ag,

                "placar":
                    (
                        f"{hg} - {ag}"
                        if hg is not None and ag is not None
                        else "? - ?"
                    )
            })

        return confrontos

    # ========================================================
    # ALIAS
    # ========================================================

    def buscar_h2h(
        self,
        equipa_casa: str,
        equipa_fora: str,
        ultimos: int = 10
    ) -> List[Dict]:

        return self.pesquisar_h2h(
            equipa_casa,
            equipa_fora,
            ultimos
        )

    # ========================================================
    # ÚLTIMOS JOGOS
    # ========================================================

    def get_team_recent_matches(
        self,
        team_id: int,
        last: int = 5
    ) -> List[Dict]:

        data = self._get(
            "/fixtures",
            {
                "team": team_id,
                "last": last
            }
        )

        if not data:

            return []

        jogos = []

        for item in data.get(
            "response",
            []
        ):

            fixture = item.get(
                "fixture",
                {}
            )

            teams = item.get(
                "teams",
                {}
            )

            goals = item.get(
                "goals",
                {}
            )

            jogos.append({

                "fixture_id":
                    fixture.get("id"),

                "date":
                    fixture.get("date"),

                "home_team":
                    teams.get(
                        "home",
                        {}
                    ).get("name"),

                "away_team":
                    teams.get(
                        "away",
                        {}
                    ).get("name"),

                "home_score":
                    goals.get("home"),

                "away_score":
                    goals.get("away")
            })

        return jogos

    # ========================================================
    # ESTATÍSTICAS
    # ========================================================

    def get_team_statistics(
        self,
        team_id: int
    ) -> Dict:

        data = self._get(
            "/teams/statistics",
            {
                "league": self.league_id,
                "season": self.season,
                "team": team_id
            }
        )

        if not data:
            return {}

        return data.get(
            "response",
            {}
        )

    # ========================================================
    # ESTATÍSTICAS PARA IA
    # ========================================================

    def get_team_stats_for_ai(
        self,
        equipa_nome: str
    ) -> Dict[str, Any]:

        equipa = self.procurar_equipa(
            equipa_nome
        )

        if not equipa:

            return {
                "erro": "Equipa não encontrada",
                "dados_disponiveis": False
            }

        team_id = equipa.get(
            "id"
        )

        stats = self.get_team_statistics(
            team_id
        )

        if not stats:

            return {
                "team_id": team_id,
                "team_name": equipa.get("name"),
                "dados_disponiveis": False
            }

        return {

            "team_id":
                team_id,

            "team_name":
                equipa.get("name"),

            "jogos":
                stats.get(
                    "fixtures",
                    {}
                ),

            "vitorias":
                stats.get(
                    "fixtures",
                    {}
                ).get(
                    "wins",
                    {}
                ),

            "empates":
                stats.get(
                    "fixtures",
                    {}
                ).get(
                    "draws",
                    {}
                ),

            "derrotas":
                stats.get(
                    "fixtures",
                    {}
                ).get(
                    "loses",
                    {}
                ),

            "golos":
                stats.get(
                    "goals",
                    {}
                ),

            "clean_sheet":
                stats.get(
                    "clean_sheet",
                    {}
                ),

            "failed_to_score":
                stats.get(
                    "failed_to_score",
                    {}
                ),

            "dados_disponiveis":
                True,

            "raw":
                stats
        }

    # ========================================================
    # PREDICTION OFICIAL DA API
    # ========================================================

    def get_prediction(
        self,
        fixture_id: int
    ) -> Dict:

        data = self._get(
            "/predictions",
            {
                "fixture": fixture_id
            }
        )

        if not data:
            return {}

        resposta = data.get(
            "response",
            []
        )

        if not resposta:
            return {}

        return resposta[0]

    # ========================================================
    # ODDS
    # ========================================================

    def get_odds(
        self,
        fixture_id: int
    ) -> Dict:

        data = self._get(
            "/odds",
            {
                "fixture": fixture_id
            }
        )

        if not data:
            return {}

        resposta = data.get(
            "response",
            []
        )

        return resposta[0] if resposta else {}

    # ========================================================
    # ESCALAÇÕES
    # ========================================================

    def get_lineups(
        self,
        fixture_id: int
    ) -> List[Dict]:

        data = self._get(
            "/fixtures/lineups",
            {
                "fixture": fixture_id
            }
        )

        if not data:
            return []

        return data.get(
            "response",
            []
        )

    # ========================================================
    # ANÁLISE COMPLETA
    # ========================================================

    def analisar_confronto_completo(
        self,
        equipa_casa: str,
        equipa_fora: str
    ) -> Dict:

        h2h = self.pesquisar_h2h(
            equipa_casa,
            equipa_fora,
            10
        )

        mercados = self.calcular_mercados(
            h2h,
            equipa_casa,
            equipa_fora
        )

        melhor = self.obter_melhor_mercado(
            mercados
        )

        chance = mercados.get(
            melhor,
            0
        )

        return {

            "casa":
                equipa_casa,

            "fora":
                equipa_fora,

            "h2h":
                h2h,

            "mercados":
                mercados,

            "melhor_mercado":
                melhor,

            "melhor_chance":
                chance,

            "combinada_1":
                melhor,

            "pct_combinada_1":
                chance,

            "combinada_2":
                self.segunda_melhor_mercado(
                    mercados
                ),

            "pct_combinada_2":
                self.segunda_melhor_chance(
                    mercados
                )
        }

    # ========================================================
    # CÁLCULO DOS MERCADOS
    # ========================================================

    def calcular_mercados(
        self,
        h2h: List[Dict],
        equipa_casa: str = "Time 1",
        equipa_fora: str = "Time 2"
    ) -> Dict[str, float]:

        mercados = {

            "Ambas marcam": 0.0,

            "Mais de 1,5 golos": 0.0,

            "Mais de 2,5 golos": 0.0,

            "Menos de 3,5 golos": 0.0,

            "Menos de 4,5 golos": 0.0,

            f"{equipa_casa} ganha ou empata": 0.0,

            f"{equipa_fora} ganha ou empata": 0.0,

            f"{equipa_casa} ganha direto": 0.0,

            f"{equipa_fora} ganha direto": 0.0
        }

        jogos_validos = []

        for jogo in h2h:

            hg = jogo.get(
                "home_score"
            )

            ag = jogo.get(
                "away_score"
            )

            if hg is None or ag is None:
                continue

            try:

                hg = int(hg)
                ag = int(ag)

            except:

                continue

            jogos_validos.append(
                jogo
            )

        total = len(
            jogos_validos
        )

        if total == 0:
            return mercados

        contagem = {
            chave: 0
            for chave in mercados
        }

        casa_lower = equipa_casa.lower()
        fora_lower = equipa_fora.lower()

        for jogo in jogos_validos:

            hg = int(
                jogo["home_score"]
            )

            ag = int(
                jogo["away_score"]
            )

            total_golos = hg + ag

            home_name = str(
                jogo.get(
                    "home_team",
                    ""
                )
            ).lower()

            away_name = str(
                jogo.get(
                    "away_team",
                    ""
                )
            ).lower()

            # ------------------------------------------------
            # GOLOS
            # ------------------------------------------------

            if hg > 0 and ag > 0:

                contagem[
                    "Ambas marcam"
                ] += 1

            if total_golos >= 2:

                contagem[
                    "Mais de 1,5 golos"
                ] += 1

            if total_golos >= 3:

                contagem[
                    "Mais de 2,5 golos"
                ] += 1

            if total_golos <= 3:

                contagem[
                    "Menos de 3,5 golos"
                ] += 1

            if total_golos <= 4:

                contagem[
                    "Menos de 4,5 golos"
                ] += 1

            # ------------------------------------------------
            # RESULTADO DA EQUIPA 1
            #
            # Corrigido: H2H alterna quem é mandante.
            # ------------------------------------------------

            equipa1_em_casa = (
                casa_lower in home_name
            )

            equipa1_fora = (
                casa_lower in away_name
            )

            equipa2_em_casa = (
                fora_lower in home_name
            )

            equipa2_fora = (
                fora_lower in away_name
            )

            if equipa1_em_casa:

                if hg >= ag:
                    contagem[
                        f"{equipa_casa} ganha ou empata"
                    ] += 1

                if hg > ag:
                    contagem[
                        f"{equipa_casa} ganha direto"
                    ] += 1

                if ag >= hg:
                    contagem[
                        f"{equipa_fora} ganha ou empata"
                    ] += 1

                if ag > hg:
                    contagem[
                        f"{equipa_fora} ganha direto"
                    ] += 1

            elif equipa1_fora:

                if ag >= hg:
                    contagem[
                        f"{equipa_casa} ganha ou empata"
                    ] += 1

                if ag > hg:
                    contagem[
                        f"{equipa_casa} ganha direto"
                    ] += 1

                if hg >= ag:
                    contagem[
                        f"{equipa_fora} ganha ou empata"
                    ] += 1

                if hg > ag:
                    contagem[
                        f"{equipa_fora} ganha direto"
                    ] += 1

        # ----------------------------------------------------
        # PERCENTAGENS
        # ----------------------------------------------------

        for mercado in mercados:

            mercados[mercado] = round(
                (
                    contagem[mercado]
                    / total
                ) * 100,
                1
            )

        return mercados

    # ========================================================
    # MELHOR MERCADO
    # ========================================================

    def obter_melhor_mercado(
        self,
        mercados: Dict[str, float]
    ) -> str:

        validos = {
            k: v
            for k, v in mercados.items()
            if v > 0
        }

        if not validos:

            return "Sem dados suficientes"

        return max(
            validos,
            key=validos.get
        )

    # ========================================================
    # SEGUNDO MELHOR
    # ========================================================

    def segunda_melhor_mercado(
        self,
        mercados: Dict[str, float]
    ) -> str:

        ordenados = sorted(
            mercados.items(),
            key=lambda x: x[1],
            reverse=True
        )

        if len(ordenados) < 2:

            return "Sem dados suficientes"

        return ordenados[1][0]

    # ========================================================
    # SEGUNDA CHANCE
    # ========================================================

    def segunda_melhor_chance(
        self,
        mercados: Dict[str, float]
    ) -> float:

        ordenados = sorted(
            mercados.values(),
            reverse=True
        )

        if len(ordenados) < 2:

            return 0.0

        return ordenados[1]

    # ========================================================
    # PALPITES DO DIA
    # ========================================================

    def gerar_palpites_do_dia(
        self,
        data_str: str,
        minimo: int = 5
    ) -> List[Dict]:

        jogos = self.get_scheduled_events(
            data_str
        )

        palpites = []

        for jogo in jogos:

            casa = jogo.get(
                "home_team"
            )

            fora = jogo.get(
                "away_team"
            )

            fixture_id = jogo.get(
                "fixture_id"
            )

            if not casa or not fora:
                continue

            # ------------------------------------------------
            # Para não consumir chamadas excessivas,
            # usamos o H2H para criar a análise.
            # ------------------------------------------------

            try:

                analise = (
                    self.analisar_confronto_completo(
                        casa,
                        fora
                    )
                )

            except Exception as e:

                print(
                    f"Erro analisando "
                    f"{casa} x {fora}: {e}"
                )

                continue

            palpites.append({

                "fixture_id":
                    fixture_id,

                "home":
                    casa,

                "away":
                    fora,

                "data":
                    jogo.get(
                        "start_time"
                    ),

                "status":
                    jogo.get(
                        "status"
                    ),

                "league":
                    jogo.get(
                        "league"
                    ),

                "melhor_mercado":
                    analise.get(
                        "melhor_mercado"
                    ),

                "melhor_chance":
                    analise.get(
                        "melhor_chance",
                        0
                    ),

                "mercados":
                    analise.get(
                        "mercados",
                        {}
                    ),

                "h2h":
                    analise.get(
                        "h2h",
                        []
                    )
            })

        # ----------------------------------------------------
        # MAIOR CONFIANÇA PRIMEIRO
        # ----------------------------------------------------

        palpites.sort(
            key=lambda x: x.get(
                "melhor_chance",
                0
            ),
            reverse=True
        )

        # ----------------------------------------------------
        # 10 OU MAIS QUANDO EXISTIREM
        # ----------------------------------------------------

        if len(palpites) >= 10:

            return palpites[:10]

        # Se houver 5, 6, 7, 8 ou 9,
        # retorna todos.
        return palpites

    # ========================================================
    # TODAS AS EQUIPAS
    # ========================================================

    def obter_todas_equipas(
        self
    ) -> List[str]:

        data = self._get(
            "/teams",
            {
                "league": self.league_id,
                "season": self.season
            }
        )

        if not data:

            return []

        nomes = []

        for item in data.get(
            "response",
            []
        ):

            nome = item.get(
                "team",
                {}
            ).get("name")

            if nome:

                nomes.append(nome)

        return sorted(
            list(set(nomes))
        )
