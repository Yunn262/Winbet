import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


# ============================================================
# API-FOOTBALL
# ============================================================

API_KEY = "COLOCA_AQUI_A_TUA_API_KEY"

BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY,
    "Accept": "application/json",
}


class APIFootballAPI:

    def __init__(self):
        self.last_error = ""
        self.last_response = {}

    # ========================================================
    # REQUEST
    # ========================================================

    def _get(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:

        try:

            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=HEADERS,
                params=params or {},
                timeout=25
            )

            self.last_response = {}

            if response.status_code != 200:

                self.last_error = (
                    f"API-Football HTTP "
                    f"{response.status_code}: "
                    f"{response.text[:500]}"
                )

                print(self.last_error)

                return None

            data = response.json()

            self.last_response = data

            errors = data.get("errors")

            if errors:

                self.last_error = str(errors)

                print(
                    "API-Football errors:",
                    errors
                )

                return data

            self.last_error = ""

            return data

        except requests.RequestException as e:

            self.last_error = (
                f"Erro de conexão: {e}"
            )

            print(self.last_error)

            return None

        except Exception as e:

            self.last_error = (
                f"Erro inesperado: {e}"
            )

            print(self.last_error)

            return None

    # ========================================================
    # TESTAR API
    # ========================================================

    def testar_api(self) -> bool:

        data = self._get(
            "/status"
        )

        if not data:
            return False

        response = data.get(
            "response"
        )

        return response is not None

    # ========================================================
    # JOGOS POR DATA
    # ========================================================

    def get_scheduled_events(
        self,
        date_str: str
    ) -> List[Dict]:

        data = self._get(
            "/fixtures",
            {
                "date": date_str
            }
        )

        if not data:

            return []

        eventos = []

        for item in data.get(
            "response",
            []
        ):

            try:

                fixture = item.get(
                    "fixture",
                    {}
                )

                teams = item.get(
                    "teams",
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

                eventos.append({

                    "event_id":
                        fixture.get("id"),

                    "home_team":
                        home.get(
                            "name",
                            "?"
                        ),

                    "away_team":
                        away.get(
                            "name",
                            "?"
                        ),

                    "home_team_id":
                        home.get("id"),

                    "away_team_id":
                        away.get("id"),

                    "tournament":
                        league.get(
                            "name",
                            "?"
                        ),

                    "league_id":
                        league.get("id"),

                    "season":
                        league.get("season"),

                    "country":
                        league.get(
                            "country",
                            ""
                        ),

                    "start_time":
                        fixture.get(
                            "date"
                        ),

                    "status":
                        status.get(
                            "long",
                            ""
                        ),

                    "status_short":
                        status.get(
                            "short",
                            ""
                        ),

                    "venue":
                        (
                            fixture.get(
                                "venue"
                            ) or {}
                        ).get(
                            "name",
                            ""
                        ),

                    "referee":
                        fixture.get(
                            "referee"
                        ),

                    "raw":
                        item

                })

            except Exception as e:

                print(
                    "Erro ao processar jogo:",
                    e
                )

        return eventos

    # ========================================================
    # PRÓXIMOS JOGOS
    # ========================================================

    def get_next_events(
        self,
        days: int = 7
    ) -> List[Dict]:

        hoje = datetime.now().date()

        final = (
            hoje +
            timedelta(days=days)
        )

        data = self._get(
            "/fixtures",
            {
                "from":
                    hoje.strftime(
                        "%Y-%m-%d"
                    ),

                "to":
                    final.strftime(
                        "%Y-%m-%d"
                    ),

                "status":
                    "NS-TBD"
            }
        )

        if not data:

            return []

        eventos = []

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

            league = item.get(
                "league",
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

            eventos.append({

                "event_id":
                    fixture.get("id"),

                "home_team":
                    home.get(
                        "name",
                        "?"
                    ),

                "away_team":
                    away.get(
                        "name",
                        "?"
                    ),

                "home_team_id":
                    home.get("id"),

                "away_team_id":
                    away.get("id"),

                "tournament":
                    league.get(
                        "name",
                        "?"
                    ),

                "league_id":
                    league.get("id"),

                "season":
                    league.get("season"),

                "start_time":
                    fixture.get(
                        "date"
                    ),

                "status_short":
                    (
                        fixture.get(
                            "status",
                            {}
                        )
                    ).get(
                        "short",
                        ""
                    ),

                "raw":
                    item
            })

        return eventos

    # ========================================================
    # PROCURAR EQUIPA
    # ========================================================

    def buscar_equipa(
        self,
        nome: str
    ) -> List[Dict]:

        data = self._get(
            "/teams",
            {
                "search": nome
            }
        )

        if not data:

            return []

        equipes = []

        for item in data.get(
            "response",
            []
        ):

            team = item.get(
                "team",
                {}
            )

            equipes.append({

                "id":
                    team.get("id"),

                "name":
                    team.get(
                        "name",
                        ""
                    ),

                "country":
                    team.get(
                        "country",
                        ""
                    ),

                "logo":
                    team.get(
                        "logo",
                        ""
                    )
            })

        return equipes

    # ========================================================
    # ENCONTRAR ID DA EQUIPA
    # ========================================================

    def encontrar_team_id(
        self,
        nome: str
    ):

        resultados = self.buscar_equipa(
            nome
        )

        if not resultados:

            return None

        nome_limpo = (
            nome.lower()
            .strip()
        )

        # Correspondência exata
        for equipe in resultados:

            if (
                equipe["name"]
                .lower()
                .strip()
                == nome_limpo
            ):

                return equipe["id"]

        # Primeiro resultado
        return resultados[0]["id"]

    # ========================================================
    # ÚLTIMOS JOGOS DA EQUIPA
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

        resultados = []

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

            home = teams.get(
                "home",
                {}
            )

            away = teams.get(
                "away",
                {}
            )

            home_id = home.get(
                "id"
            )

            away_id = away.get(
                "id"
            )

            home_goals = goals.get(
                "home"
            )

            away_goals = goals.get(
                "away"
            )

            if (
                home_goals is None
                or
                away_goals is None
            ):

                continue

            if team_id == home_id:

                marcados = int(
                    home_goals
                )

                sofridos = int(
                    away_goals
                )

                casa = True

            elif team_id == away_id:

                marcados = int(
                    away_goals
                )

                sofridos = int(
                    home_goals
                )

                casa = False

            else:

                continue

            resultados.append({

                "fixture_id":
                    fixture.get("id"),

                "data":
                    fixture.get("date"),

                "adversario":
                    (
                        away
                        if casa
                        else home
                    ).get(
                        "name",
                        "?"
                    ),

                "casa":
                    casa,

                "golos_marcados":
                    marcados,

                "golos_sofridos":
                    sofridos,

                "total_golos":
                    marcados
                    + sofridos,

                "venceu":
                    marcados > sofridos,

                "empatou":
                    marcados == sofridos,

                "perdeu":
                    marcados < sofridos,

                "ambas_marcaram":
                    (
                        marcados > 0
                        and
                        sofridos > 0
                    ),

                "over_1_5":
                    (
                        marcados
                        + sofridos
                    ) >= 2,

                "over_2_5":
                    (
                        marcados
                        + sofridos
                    ) >= 3,

                "under_3_5":
                    (
                        marcados
                        + sofridos
                    ) <= 3,

                "under_4_5":
                    (
                        marcados
                        + sofridos
                    ) <= 4
            })

        return resultados

    # ========================================================
    # H2H
    # ========================================================

    def get_h2h(
        self,
        home_id: int,
        away_id: int,
        last: int = 10
    ) -> List[Dict]:

        data = self._get(
            "/fixtures/headtohead",
            {
                "h2h":
                    f"{home_id}-{away_id}",

                "last":
                    last
            }
        )

        if not data:

            return []

        resultados = []

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

            home = teams.get(
                "home",
                {}
            )

            away = teams.get(
                "away",
                {}
            )

            hg = goals.get(
                "home"
            )

            ag = goals.get(
                "away"
            )

            if (
                hg is None
                or
                ag is None
            ):

                continue

            resultados.append({

                "data":
                    fixture.get(
                        "date"
                    ),

                "home":
                    home.get(
                        "name",
                        "?"
                    ),

                "away":
                    away.get(
                        "name",
                        "?"
                    ),

                "home_goals":
                    int(hg),

                "away_goals":
                    int(ag),

                "total":
                    int(hg)
                    + int(ag),

                "btts":
                    (
                        int(hg) > 0
                        and
                        int(ag) > 0
                    ),

                "over_1_5":
                    (
                        int(hg)
                        + int(ag)
                    ) >= 2,

                "over_2_5":
                    (
                        int(hg)
                        + int(ag)
                    ) >= 3,

                "under_3_5":
                    (
                        int(hg)
                        + int(ag)
                    ) <= 3,

                "under_4_5":
                    (
                        int(hg)
                        + int(ag)
                    ) <= 4
            })

        return resultados

    # ========================================================
    # ESTATÍSTICAS DO JOGO
    # ========================================================

    def get_fixture_statistics(
        self,
        fixture_id: int
    ) -> Dict[str, Any]:

        data = self._get(
            "/fixtures/statistics",
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

        if len(resposta) < 2:

            return {}

        resultado = {}

        for i, equipe in enumerate(
            resposta[:2]
        ):

            team = equipe.get(
                "team",
                {}
            )

            team_id = team.get(
                "id"
            )

            stats = {}

            for item in equipe.get(
                "statistics",
                []
            ):

                tipo = item.get(
                    "type"
                )

                valor = item.get(
                    "value"
                )

                stats[tipo] = valor

            if i == 0:

                resultado[
                    "casa"
                ] = stats

                resultado[
                    "casa_team_id"
                ] = team_id

            else:

                resultado[
                    "fora"
                ] = stats

                resultado[
                    "fora_team_id"
                ] = team_id

        return resultado

    # ========================================================
    # ODDS
    # ========================================================

    def get_event_odds(
        self,
        fixture_id: int
    ) -> Dict:

        data = self._get(
            "/odds",
            {
                "fixture":
                    fixture_id
            }
        )

        return data or {}

    # ========================================================
    # TRANSFORMAR ODDS
    # ========================================================

    def processar_odds(
        self,
        data: Dict
    ) -> Dict:

        odds = {}

        try:

            responses = data.get(
                "response",
                []
            )

            for bookmaker_data in responses:

                for bookmaker in bookmaker_data.get(
                    "bookmakers",
                    []
                ):

                    for bet in bookmaker.get(
                        "bets",
                        []
                    ):

                        nome_bet = (
                            bet.get(
                                "name",
                                ""
                            )
                            .lower()
                        )

                        for value in bet.get(
                            "values",
                            []
                        ):

                            nome = (
                                value.get(
                                    "value",
                                    ""
                                )
                                .lower()
                            )

                            odd = value.get(
                                "odd"
                            )

                            try:

                                odd = float(
                                    odd
                                )

                            except Exception:

                                continue

                            # 1X2
                            if (
                                "match winner"
                                in nome_bet
                                or
                                nome_bet == "winner"
                            ):

                                if nome in (
                                    "home",
                                    "1"
                                ):

                                    odds[
                                        "casa"
                                    ] = odd

                                elif nome in (
                                    "draw",
                                    "x"
                                ):

                                    odds[
                                        "empate"
                                    ] = odd

                                elif nome in (
                                    "away",
                                    "2"
                                ):

                                    odds[
                                        "fora"
                                    ] = odd

                            # Over 1.5
                            if (
                                "goals over/under"
                                in nome_bet
                            ):

                                if (
                                    "over 1.5"
                                    in nome
                                ):

                                    odds[
                                        "over_1_5"
                                    ] = odd

                                elif (
                                    "over 2.5"
                                    in nome
                                ):

                                    odds[
                                        "over_2_5"
                                    ] = odd

                                elif (
                                    "under 3.5"
                                    in nome
                                ):

                                    odds[
                                        "under_3_5"
                                    ] = odd

                                elif (
                                    "under 4.5"
                                    in nome
                                ):

                                    odds[
                                        "under_4_5"
                                    ] = odd

                            # BTTS
                            if (
                                "both teams"
                                in nome_bet
                            ):

                                if nome == "yes":

                                    odds[
                                        "btts_yes"
                                    ] = odd

                                elif nome == "no":

                                    odds[
                                        "btts_no"
                                    ] = odd

        except Exception as e:

            print(
                "Erro ao processar odds:",
                e
            )

        return odds

    # ========================================================
    # MÉDIA / PERCENTAGEM
    # ========================================================

    @staticmethod
    def pct(
        dados: List[Dict],
        campo: str
    ) -> Optional[int]:

        if not dados:

            return None

        validos = [
            x
            for x in dados
            if campo in x
        ]

        if not validos:

            return None

        acertos = sum(
            1
            for x in validos
            if x[campo]
        )

        return round(
            acertos
            /
            len(validos)
            * 100
        )

    # ========================================================
    # ANÁLISE H2H COMPLETA
    # ========================================================

    def analisar_h2h(
        self,
        equipa_casa: str,
        equipa_fora: str
    ) -> Dict[str, Any]:

        casa_id = self.encontrar_team_id(
            equipa_casa
        )

        fora_id = self.encontrar_team_id(
            equipa_fora
        )

        if not casa_id:

            return {
                "erro":
                    f"Equipa não encontrada: {equipa_casa}"
            }

        if not fora_id:

            return {
                "erro":
                    f"Equipa não encontrada: {equipa_fora}"
            }

        forma_casa = (
            self.get_team_recent_matches(
                casa_id,
                10
            )
        )

        forma_fora = (
            self.get_team_recent_matches(
                fora_id,
                10
            )
        )

        h2h = self.get_h2h(
            casa_id,
            fora_id,
            10
        )

        # -----------------------------------------------
        # Mercados individuais
        # -----------------------------------------------

        btts_casa = self.pct(
            forma_casa,
            "ambas_marcaram"
        )

        btts_fora = self.pct(
            forma_fora,
            "ambas_marcaram"
        )

        over15_casa = self.pct(
            forma_casa,
            "over_1_5"
        )

        over15_fora = self.pct(
            forma_fora,
            "over_1_5"
        )

        over25_casa = self.pct(
            forma_casa,
            "over_2_5"
        )

        over25_fora = self.pct(
            forma_fora,
            "over_2_5"
        )

        under35_casa = self.pct(
            forma_casa,
            "under_3_5"
        )

        under35_fora = self.pct(
            forma_fora,
            "under_3_5"
        )

        under45_casa = self.pct(
            forma_casa,
            "under_4_5"
        )

        under45_fora = self.pct(
            forma_fora,
            "under_4_5"
        )

        # -----------------------------------------------
        # Combinar forma das duas equipas
        # -----------------------------------------------

        def media(
            a,
            b
        ):

            valores = [
                x
                for x in (
                    a,
                    b
                )
                if x is not None
            ]

            if not valores:

                return None

            return round(
                sum(valores)
                /
                len(valores)
            )

        mercados = {

            "Ambas marcam":
                media(
                    btts_casa,
                    btts_fora
                ),

            "Mais de 1.5 golos":
                media(
                    over15_casa,
                    over15_fora
                ),

            "Mais de 2.5 golos":
                media(
                    over25_casa,
                    over25_fora
                ),

            "Menos de 3.5 golos":
                media(
                    under35_casa,
                    under35_fora
                ),

            "Menos de 4.5 golos":
                media(
                    under45_casa,
                    under45_fora
                ),
        }

        # -----------------------------------------------
        # H2H reforça os mercados
        # -----------------------------------------------

        if h2h:

            h2h_mercados = {

                "Ambas marcam":
                    self.pct(
                        h2h,
                        "btts"
                    ),

                "Mais de 1.5 golos":
                    self.pct(
                        h2h,
                        "over_1_5"
                    ),

                "Mais de 2.5 golos":
                    self.pct(
                        h2h,
                        "over_2_5"
                    ),

                "Menos de 3.5 golos":
                    self.pct(
                        h2h,
                        "under_3_5"
                    ),

                "Menos de 4.5 golos":
                    self.pct(
                        h2h,
                        "under_4_5"
                    )
            }

            for mercado in mercados:

                a = mercados[mercado]

                b = h2h_mercados.get(
                    mercado
                )

                if (
                    a is not None
                    and
                    b is not None
                ):

                    mercados[mercado] = round(
                        a * 0.70
                        +
                        b * 0.30
                    )

                elif b is not None:

                    mercados[mercado] = b

        # -----------------------------------------------
        # Vitórias
        # -----------------------------------------------

        win_casa = self.pct(
            forma_casa,
            "venceu"
        )

        win_fora = self.pct(
            forma_fora,
            "venceu"
        )

        empate_casa = self.pct(
            forma_casa,
            "empatou"
        )

        empate_fora = self.pct(
            forma_fora,
            "empatou"
        )

        empate = media(
            empate_casa,
            empate_fora
        )

        if win_casa is not None:

            mercados[
                f"{equipa_casa} ganha direto"
            ] = win_casa

            if empate is not None:

                mercados[
                    f"{equipa_casa} ganha ou empata"
                ] = min(
                    100,
                    round(
                        win_casa
                        +
                        empate
                    )
                )

        if win_fora is not None:

            mercados[
                f"{equipa_fora} ganha direto"
            ] = win_fora

            if empate is not None:

                mercados[
                    f"{equipa_fora} ganha ou empata"
                ] = min(
                    100,
                    round(
                        win_fora
                        +
                        empate
                    )
                )

        # -----------------------------------------------
        # Melhor mercado
        # -----------------------------------------------

        validos = {
            k: v
            for k, v
            in mercados.items()
            if v is not None
        }

        if validos:

            ordenados = sorted(
                validos.items(),
                key=lambda x: x[1],
                reverse=True
            )

            melhor_mercado = (
                ordenados[0][0]
            )

            melhor_chance = (
                ordenados[0][1]
            )

        else:

            ordenados = []

            melhor_mercado = (
                "Dados insuficientes"
            )

            melhor_chance = None

        # -----------------------------------------------
        # Resultado
        # -----------------------------------------------

        return {

            "equipa_casa":
                equipa_casa,

            "equipa_fora":
                equipa_fora,

            "home_id":
                casa_id,

            "away_id":
                fora_id,

            "forma_casa":
                forma_casa,

            "forma_fora":
                forma_fora,

            "h2h":
                h2h,

            "mercados":
                mercados,

            "melhor_mercado":
                melhor_mercado,

            "melhor_chance":
                melhor_chance,

            "dados_h2h":
                len(h2h),

            "dados_casa":
                len(forma_casa),

            "dados_fora":
                len(forma_fora)
        }


# ============================================================
# COMPATIBILIDADE
# ============================================================

FootballAIEngine = APIFootballAPI


# ============================================================
# TESTE DIRETO
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("FOOTBALLAI - API-FOOTBALL")
    print("=" * 60)

    if (
        not API_KEY
        or
        API_KEY == "COLOCA_AQUI_A_TUA_API_KEY"
    ):

        print(
            "ERRO: coloque a API key no scraper.py"
        )

    else:

        api = APIFootballAPI()

        hoje = datetime.now().strftime(
            "%Y-%m-%d"
        )

        print(
            f"Procurando jogos de {hoje}..."
        )

        jogos = api.get_scheduled_events(
            hoje
        )

        print(
            f"Jogos encontrados: {len(jogos)}"
        )

        for jogo in jogos[:10]:

            print(
                f"{jogo['home_team']} "
                f"vs "
                f"{jogo['away_team']} "
                f"| "
                f"{jogo['tournament']}"
            )
