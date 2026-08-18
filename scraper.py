# ============================================================
# scraper.py
# FOOTBALL AI BOT - API-FOOTBALL
# ============================================================

import requests
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_URL = "https://v3.football.api-sports.io"


def obter_api_key() -> str:
    """
    Lê a API Key dos Secrets do Streamlit.
    Secret esperado:

    API_FOOTBALL_KEY = "SUA_CHAVE"
    """

    try:
        chave = st.secrets.get("API_FOOTBALL_KEY", "")
    except Exception:
        chave = ""

    return str(chave).strip()


# ============================================================
# CLASSE PRINCIPAL
# ============================================================

class FootballAIEngine:

    def __init__(self, liga_nome: str = "Premier League"):

        self.liga_nome = liga_nome
        self.api_key = obter_api_key()

        self.headers = {
            "x-apisports-key": self.api_key,
            "Accept": "application/json"
        }

        # IDs das principais ligas da API-Football
        self.ligas = {
            "Premier League": 39,
            "La Liga": 140,
            "Serie A Italiana": 135,
            "Bundesliga": 78,
            "Ligue 1": 61,
            "Champions League": 2,
            "Brasileirao Serie A": 71,
            "Liga Portugal": 94,
            "Eredivisie": 88,
            "Primeira Liga": 94,
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

    # ========================================================
    # TEMPORADA
    # ========================================================

    def _obter_temporada(self) -> int:

        hoje = datetime.now()

        # Temporada europeia:
        # agosto/dezembro -> ano atual
        # janeiro/julho -> ano anterior

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
    ) -> Optional[Dict]:

        if not self.api_key:

            print("ERRO: API_FOOTBALL_KEY não configurada.")

            return None

        url = f"{BASE_URL}{endpoint}"

        try:

            response = requests.get(
                url,
                headers=self.headers,
                params=params or {},
                timeout=25
            )

            if response.status_code != 200:

                print(
                    f"API-Football HTTP {response.status_code}: "
                    f"{response.text[:500]}"
                )

                return None

            data = response.json()

            # Erros enviados pela própria API
            if data.get("errors"):

                print(
                    "API-Football errors:",
                    data.get("errors")
                )

            return data

        except requests.Timeout:

            print("Timeout ao contactar a API-Football.")

            return None

        except requests.RequestException as e:

            print(
                f"Erro de conexão com API-Football: {e}"
            )

            return None

        except Exception as e:

            print(
                f"Erro inesperado na API-Football: {e}"
            )

            return None

    # ========================================================
    # TESTE DA API
    # ========================================================

    def testar_api(self) -> Dict[str, Any]:

        data = self._get(
            "/status"
        )

        if not data:

            return {
                "ok": False,
                "mensagem": "Não foi possível contactar a API."
            }

        erros = data.get("errors", {})

        if erros:

            return {
                "ok": False,
                "mensagem": str(erros)
            }

        return {
            "ok": True,
            "mensagem": "API-Football conectada."
        }

    # ========================================================
    # JOGOS DE UMA DATA
    # ========================================================

    def get_scheduled_events(
        self,
        date_str: str
    ) -> List[Dict]:

        """
        Busca todos os jogos da liga selecionada
        numa determinada data.

        date_str:
            YYYY-MM-DD
        """

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

            jogos.append({

                "fixture_id":
                    fixture.get("id"),

                "event_id":
                    fixture.get("id"),

                "home_team":
                    teams.get("home", {}).get(
                        "name",
                        "?"
                    ),

                "away_team":
                    teams.get("away", {}).get(
                        "name",
                        "?"
                    ),

                "home_team_id":
                    teams.get("home", {}).get(
                        "id"
                    ),

                "away_team_id":
                    teams.get("away", {}).get(
                        "id"
                    ),

                "home_logo":
                    teams.get("home", {}).get(
                        "logo"
                    ),

                "away_logo":
                    teams.get("away", {}).get(
                        "logo"
                    ),

                "league":
                    league.get("name"),

                "country":
                    league.get("country"),

                "round":
                    league.get("round"),

                "date":
                    fixture.get("date"),

                "start_time":
                    fixture.get("date"),

                "status":
                    status.get("long"),

                "status_short":
                    status.get("short"),

                "venue":
                    fixture.get(
                        "venue",
                        {}
                    ).get(
                        "name"
                    ),

                "referee":
                    fixture.get(
                        "referee"
                    ),

                "home_score":
                    goals.get("home"),

                "away_score":
                    goals.get("away"),

                "raw":
                    item
            })

        # Ordenar por horário
        jogos.sort(
            key=lambda x: x.get(
                "start_time"
            ) or ""
        )

        print(
            f"API-Football: "
            f"{len(jogos)} jogos encontrados "
            f"para {date_str}"
        )

        return jogos

    # ========================================================
    # ALIAS COMPATIBILIDADE
    # ========================================================

    def buscar_jogos_reais_api(
        self,
        data_selecionada: str
    ) -> List[Dict]:

        return self.get_scheduled_events(
            data_selecionada
        )

    # ========================================================
    # PROCURAR EQUIPA
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

        equipes = data.get(
            "response",
            []
        )

        if not equipes:
            return None

        # Primeiro tenta encontrar correspondência
        # aproximada pelo nome
        nome_lower = nome.lower()

        for item in equipes:

            team = item.get(
                "team",
                {}
            )

            nome_api = str(
                team.get("name", "")
            )

            if nome_lower in nome_api.lower():

                return team

        return equipes[0].get(
            "team"
        )

    # ========================================================
    # PESQUISA H2H
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

            confrontos.append({

                "fixture_id":
                    fixture.get("id"),

                "date":
                    fixture.get("date"),

                "home_team":
                    teams.get("home", {}).get(
                        "name"
                    ),

                "away_team":
                    teams.get("away", {}).get(
                        "name"
                    ),

                "home_team_id":
                    teams.get("home", {}).get(
                        "id"
                    ),

                "away_team_id":
                    teams.get("away", {}).get(
                        "id"
                    ),

                "home_score":
                    goals.get("home"),

                "away_score":
                    goals.get("away"),

                "placar":
                    f"{goals.get('home', 0)} - "
                    f"{goals.get('away', 0)}"
            })

        return confrontos

    # ========================================================
    # ALIAS H2H
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
    # ÚLTIMOS JOGOS DE UMA EQUIPA
    # ========================================================

    def get_team_recent_matches(
        self,
        team_id: int,
        last: int = 10
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

            jogos.append({

                "fixture_id":
                    fixture.get("id"),

                "date":
                    fixture.get("date"),

                "home_team":
                    teams.get("home", {}).get(
                        "name"
                    ),

                "away_team":
                    teams.get("away", {}).get(
                        "name"
                    ),

                "home_score":
                    goals.get("home"),

                "away_score":
                    goals.get("away")
            })

        return jogos

    # ========================================================
    # ESTATÍSTICAS DA EQUIPA
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
                "erro": "Equipa não encontrada"
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

        fixtures = stats.get(
            "fixtures",
            {}
        )

        goals = stats.get(
            "goals",
            {}
        )

        clean_sheets = stats.get(
            "clean_sheet",
            {}
        )

        failed_to_score = stats.get(
            "failed_to_score",
            {}
        )

        return {

            "team_id":
                team_id,

            "team_name":
                equipa.get("name"),

            "jogos":
                fixtures.get(
                    "played",
                    {}
                ),

            "vitorias":
                fixtures.get(
                    "wins",
                    {}
                ),

            "empates":
                fixtures.get(
                    "draws",
                    {}
                ),

            "derrotas":
                fixtures.get(
                    "loses",
                    {}
                ),

            "golos":
                goals,

            "clean_sheet":
                clean_sheets,

            "failed_to_score":
                failed_to_score,

            "dados_disponiveis":
                True,

            "raw":
                stats
        }

    # ========================================================
    # ODDS DO JOGO
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

        if not resposta:

            return {}

        return resposta[0]

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
    # EVENTOS DO JOGO
    # ========================================================

    def get_fixture_events(
        self,
        fixture_id: int
    ) -> List[Dict]:

        data = self._get(
            "/fixtures/events",
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
    # ANÁLISE COMPLETA DO CONFRONTO
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

        stats_casa = self.get_team_stats_for_ai(
            equipa_casa
        )

        stats_fora = self.get_team_stats_for_ai(
            equipa_fora
        )

        mercados = self.calcular_mercados(
            h2h
        )

        melhor_mercado = self.obter_melhor_mercado(
            mercados
        )

        melhor_chance = mercados.get(
            melhor_mercado,
            0
        )

        combinada_1 = (
            f"{melhor_mercado}"
        )

        combinada_2 = (
            "Ambas marcam"
        )

        return {

            "casa":
                equipa_casa,

            "fora":
                equipa_fora,

            "h2h":
                h2h,

            "stats_casa":
                stats_casa,

            "stats_fora":
                stats_fora,

            "mercados":
                mercados,

            "melhor_mercado":
                melhor_mercado,

            "melhor_chance":
                melhor_chance,

            "combinada_1":
                combinada_1,

            "pct_combinada_1":
                melhor_chance,

            "combinada_2":
                combinada_2,

            "pct_combinada_2":
                mercados.get(
                    "Ambas marcam",
                    0
                )
        }

    # ========================================================
    # CÁLCULO DOS MERCADOS BASEADO NO H2H
    # ========================================================

    def calcular_mercados(
        self,
        h2h: List[Dict]
    ) -> Dict[str, float]:

        if not h2h:

            return {
                "Ambas marcam": 0.0,
                "Mais de 1,5 golos": 0.0,
                "Mais de 2,5 golos": 0.0,
                "Menos de 3,5 golos": 0.0,
                "Menos de 4,5 golos": 0.0,
                "Time 1 ganha ou empata": 0.0,
                "Time 2 ganha ou empata": 0.0,
                "Time 1 ganha direto": 0.0,
                "Time 2 ganha direto": 0.0
            }

        total = 0

        ambas = 0
        over15 = 0
        over25 = 0
        under35 = 0
        under45 = 0

        # Como o H2H pode ter os mandantes
        # alternados, contamos também os resultados
        # das duas equipas.

        time1_nao_perde = 0
        time2_nao_perde = 0
        time1_ganha = 0
        time2_ganha = 0

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

            total_golos = hg + ag

            total += 1

            if hg > 0 and ag > 0:
                ambas += 1

            if total_golos >= 2:
                over15 += 1

            if total_golos >= 3:
                over25 += 1

            if total_golos <= 3:
                under35 += 1

            if total_golos <= 4:
                under45 += 1

            # Estes valores são usados de forma
            # neutra porque o H2H alterna o mandante.
            if hg >= ag:
                time1_nao_perde += 1

            if ag >= hg:
                time2_nao_perde += 1

            if hg > ag:
                time1_ganha += 1

            if ag > hg:
                time2_ganha += 1

        if total == 0:

            return {
                "Ambas marcam": 0.0,
                "Mais de 1,5 golos": 0.0,
                "Mais de 2,5 golos": 0.0,
                "Menos de 3,5 golos": 0.0,
                "Menos de 4,5 golos": 0.0,
                "Time 1 ganha ou empata": 0.0,
                "Time 2 ganha ou empata": 0.0,
                "Time 1 ganha direto": 0.0,
                "Time 2 ganha direto": 0.0
            }

        def pct(valor):

            return round(
                (valor / total) * 100,
                1
            )

        return {

            "Ambas marcam":
                pct(ambas),

            "Mais de 1,5 golos":
                pct(over15),

            "Mais de 2,5 golos":
                pct(over25),

            "Menos de 3,5 golos":
                pct(under35),

            "Menos de 4,5 golos":
                pct(under45),

            "Time 1 ganha ou empata":
                pct(time1_nao_perde),

            "Time 2 ganha ou empata":
                pct(time2_nao_perde),

            "Time 1 ganha direto":
                pct(time1_ganha),

            "Time 2 ganha direto":
                pct(time2_ganha)
        }

    # ========================================================
    # MELHOR MERCADO
    # ========================================================

    def obter_melhor_mercado(
        self,
        mercados: Dict[str, float]
    ) -> str:

        if not mercados:

            return "Sem dados suficientes"

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
    # PALPITES DIÁRIOS
    # ========================================================

    def gerar_palpites_do_dia(
        self,
        data_str: str,
        minimo: int = 5
    ) -> List[Dict]:

        """
        Busca os jogos reais do dia e gera uma análise
        para cada partida.

        Se houver 10 ou mais:
            retorna pelo menos 10.

        Se houver menos:
            utiliza todos os jogos disponíveis.
        """

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

            if not casa or not fora:
                continue

            try:

                analise = (
                    self.analisar_confronto_completo(
                        casa,
                        fora
                    )
                )

                palpites.append({

                    "fixture_id":
                        jogo.get("fixture_id"),

                    "home":
                        casa,

                    "away":
                        fora,

                    "data":
                        jogo.get("start_time"),

                    "status":
                        jogo.get("status"),

                    "melhor_mercado":
                        analise.get(
                            "melhor_mercado"
                        ),

                    "melhor_chance":
                        analise.get(
                            "melhor_chance"
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

            except Exception as e:

                print(
                    f"Erro ao analisar "
                    f"{casa} x {fora}: {e}"
                )

        # Ordena pela maior confiança
        palpites.sort(
            key=lambda x: x.get(
                "melhor_chance",
                0
            ),
            reverse=True
        )

        return palpites

    # ========================================================
    # OBTER TODAS AS EQUIPAS DA LIGA
    # ========================================================

    def obter_todas_equipas(self) -> List[str]:

        data = self._get(
            "/teams",
            {
                "league": self.league_id,
                "season": self.season
            }
        )

        if not data:

            return []

        resposta = data.get(
            "response",
            []
        )

        nomes = []

        for item in resposta:

            nome = item.get(
                "team",
                {}
            ).get(
                "name"
            )

            if nome:

                nomes.append(nome)

        return sorted(
            list(set(nomes))
        )
