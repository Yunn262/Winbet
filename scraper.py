import os
from typing import Optional

import requests
import streamlit as st


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


def obter_token():
    try:
        token = st.secrets.get("FOOTBALL_DATA_ORG_KEY", "")
        if token:
            return str(token).strip()
    except Exception:
        pass

    return os.getenv("FOOTBALL_DATA_ORG_KEY", "").strip()


class SoccerDataScraper:

    def __init__(
        self,
        league_name="Premier League",
        season=None
    ):
        self.league_name = league_name
        self.competition = COMPETICOES.get(
            league_name,
            "PL"
        )

        self.season = season
        self.token = obter_token()

        self.last_events = []
        self.last_error = ""

    # ======================================================
    # API
    # ======================================================

    def request_api(
        self,
        endpoint,
        params=None
    ):

        if not self.token:

            self.last_error = (
                "FOOTBALL_DATA_ORG_KEY não encontrada."
            )

            return None

        try:

            response = requests.get(
                BASE_URL + endpoint,
                headers={
                    "X-Auth-Token": self.token,
                    "Accept": "application/json"
                },
                params=params or {},
                timeout=25
            )

            if response.status_code == 200:

                self.last_error = ""

                return response.json()

            erros = {
                400: "Pedido inválido.",
                401: "API Key inválida.",
                403: "Acesso recusado pela API.",
                404: "Recurso não encontrado.",
                429: "Limite da API atingido."
            }

            self.last_error = erros.get(
                response.status_code,
                f"Erro HTTP {response.status_code}"
            )

        except requests.RequestException as e:

            self.last_error = (
                f"Erro de conexão: {e}"
            )

        return None

    # ======================================================
    # TESTE
    # ======================================================

    def testar_api(self):

        data = self.request_api(
            f"/competitions/{self.competition}"
        )

        return data is not None

    # ======================================================
    # SCORE
    # ======================================================

    @staticmethod
    def extrair_score(match):

        score = match.get("score") or {}

        full_time = (
            score.get("fullTime") or {}
        )

        return (
            full_time.get("home"),
            full_time.get("away")
        )

    # ======================================================
    # JOGOS DE UMA DATA
    # ======================================================

    def get_scheduled_events(
        self,
        date_str
    ):

        data = self.request_api(
            f"/competitions/{self.competition}/matches",
            {
                "dateFrom": date_str,
                "dateTo": date_str
            }
        )

        if not data:

            self.last_events = []

            return []

        eventos = []

        for match in data.get(
            "matches",
            []
        ):

            home = (
                match.get("homeTeam")
                or {}
            )

            away = (
                match.get("awayTeam")
                or {}
            )

            home_score, away_score = (
                self.extrair_score(match)
            )

            eventos.append({

                "event_id":
                    match.get("id"),

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
                        match.get(
                            "competition"
                        )
                        or {}
                    ).get(
                        "name",
                        self.league_name
                    ),

                "start_time":
                    match.get(
                        "utcDate",
                        ""
                    ),

                "status":
                    match.get(
                        "status",
                        ""
                    ),

                "home_score":
                    home_score,

                "away_score":
                    away_score,

                "raw":
                    match
            })

        self.last_events = eventos

        return eventos

    # ======================================================
    # ENCONTRAR ID DA EQUIPA
    # ======================================================

    def obter_id_equipa(
        self,
        nome
    ):

        data = self.request_api(
            f"/competitions/{self.competition}/teams"
        )

        if not data:
            return None

        alvo = nome.strip().lower()

        equipes = data.get(
            "teams",
            []
        )

        # Primeiro tenta nome exato
        for equipe in equipes:

            nome_api = str(
                equipe.get(
                    "name",
                    ""
                )
            ).strip().lower()

            short = str(
                equipe.get(
                    "shortName",
                    ""
                )
            ).strip().lower()

            tla = str(
                equipe.get(
                    "tla",
                    ""
                )
            ).strip().lower()

            if alvo in (
                nome_api,
                short,
                tla
            ):

                return equipe.get(
                    "id"
                )

        # Depois procura parcialmente
        for equipe in equipes:

            nome_api = str(
                equipe.get(
                    "name",
                    ""
                )
            ).lower()

            if (
                alvo in nome_api
                or nome_api in alvo
            ):

                return equipe.get(
                    "id"
                )

        return None

    # ======================================================
    # JOGOS DA EQUIPA
    # ======================================================

    def obter_jogos_equipa(
        self,
        team_id,
        limit=20
    ):

        data = self.request_api(
            f"/teams/{team_id}/matches",
            {
                "status": "FINISHED",
                "limit": limit,
                "competitions":
                    self.competition
            }
        )

        if not data:
            return []

        return data.get(
            "matches",
            []
        )

    # ======================================================
    # TRANSFORMAR RESULTADOS
    # ======================================================

    def _resultados(
        self,
        nome,
        jogos
    ):

        alvo = nome.lower().strip()

        resultados = []

        for jogo in jogos:

            home = (
                jogo.get(
                    "homeTeam"
                )
                or {}
            ).get(
                "name",
                ""
            )

            away = (
                jogo.get(
                    "awayTeam"
                )
                or {}
            ).get(
                "name",
                ""
            )

            home_score, away_score = (
                self.extrair_score(jogo)
            )

            if (
                home_score is None
                or away_score is None
            ):
                continue

            if alvo in home.lower():

                gols_feitos = int(
                    home_score
                )

                gols_sofridos = int(
                    away_score
                )

            elif alvo in away.lower():

                gols_feitos = int(
                    away_score
                )

                gols_sofridos = int(
                    home_score
                )

            else:
                continue

            total = (
                gols_feitos
                + gols_sofridos
            )

            resultados.append({

                "gf":
                    gols_feitos,

                "ga":
                    gols_sofridos,

                "total":
                    total,

                "btts":
                    (
                        gols_feitos > 0
                        and gols_sofridos > 0
                    ),

                "win":
                    gols_feitos
                    > gols_sofridos,

                "draw":
                    gols_feitos
                    == gols_sofridos,

                "loss":
                    gols_feitos
                    < gols_sofridos
            })

        return resultados

    # ======================================================
    # PORCENTAGEM
    # ======================================================

    @staticmethod
    def _pct(
        resultados,
        condicao
    ):

        if not resultados:
            return 0.0

        acertos = sum(
            1
            for resultado in resultados
            if condicao(resultado)
        )

        return round(
            acertos
            / len(resultados)
            * 100,
            1
        )

    # ======================================================
    # ESTATÍSTICAS
    # ======================================================

    def get_team_stats_for_ai(
        self,
        equipa_nome
    ):

        team_id = self.obter_id_equipa(
            equipa_nome
        )

        if not team_id:

            return {
                "team_name":
                    equipa_nome,

                "jogos_analisados":
                    0
            }

        jogos = self.obter_jogos_equipa(
            team_id,
            20
        )

        resultados = self._resultados(
            equipa_nome,
            jogos
        )

        if not resultados:

            return {
                "team_name":
                    equipa_nome,

                "jogos_analisados":
                    0
            }

        n = len(resultados)

        return {

            "team_name":
                equipa_nome,

            "jogos_analisados":
                n,

            "media_golos_marcados":
                round(
                    sum(
                        x["gf"]
                        for x in resultados
                    ) / n,
                    2
                ),

            "media_golos_sofridos":
                round(
                    sum(
                        x["ga"]
                        for x in resultados
                    ) / n,
                    2
                ),

            "over_1_5_pct":
                self._pct(
                    resultados,
                    lambda x:
                        x["total"] >= 2
                ),

            "over_2_5_pct":
                self._pct(
                    resultados,
                    lambda x:
                        x["total"] >= 3
                ),

            "under_3_5_pct":
                self._pct(
                    resultados,
                    lambda x:
                        x["total"] <= 3
                ),

            "under_4_5_pct":
                self._pct(
                    resultados,
                    lambda x:
                        x["total"] <= 4
                ),

            "btts_pct":
                self._pct(
                    resultados,
                    lambda x:
                        x["btts"]
                ),

            "vitorias_pct":
                self._pct(
                    resultados,
                    lambda x:
                        x["win"]
                ),

            "empates_pct":
                self._pct(
                    resultados,
                    lambda x:
                        x["draw"]
                ),

            "derrotas_pct":
                self._pct(
                    resultados,
                    lambda x:
                        x["loss"]
                )
        }

    # ======================================================
    # H2H
    # ======================================================

    def pesquisar_jogo(
        self,
        equipa_casa,
        equipa_fora
    ):

        team_id = self.obter_id_equipa(
            equipa_casa
        )

        if not team_id:
            return []

        jogos = self.obter_jogos_equipa(
            team_id,
            100
        )

        alvo = equipa_fora.lower().strip()

        confrontos = []

        for jogo in jogos:

            home = (
                jogo.get(
                    "homeTeam"
                )
                or {}
            ).get(
                "name",
                ""
            )

            away = (
                jogo.get(
                    "awayTeam"
                )
                or {}
            ).get(
                "name",
                ""
            )

            if (
                alvo not in home.lower()
                and alvo not in away.lower()
            ):
                continue

            hs, aws = (
                self.extrair_score(
                    jogo
                )
            )

            confrontos.append({

                "date":
                    jogo.get(
                        "utcDate",
                        ""
                    ),

                "home_team":
                    home,

                "away_team":
                    away,

                "score":
                    f"{hs if hs is not None else '?'}-"
                    f"{aws if aws is not None else '?'}",

                "home_score":
                    hs,

                "away_score":
                    aws,

                "status":
                    jogo.get(
                        "status",
                        ""
                    )
            })

        return confrontos

    # ======================================================
    # ANÁLISE COMPLETA
    # ======================================================

    def analisar_confronto_completo(
        self,
        equipa_casa,
        equipa_fora
    ):

        id_casa = self.obter_id_equipa(
            equipa_casa
        )

        id_fora = self.obter_id_equipa(
            equipa_fora
        )

        if (
            not id_casa
            or not id_fora
        ):

            return {

                "melhor_mercado":
                    "Dados insuficientes",

                "melhor_chance":
                    0,

                "mercados":
                    {},

                "combinada_1":
                    "",

                "pct_combinada_1":
                    0,

                "combinada_2":
                    "",

                "pct_combinada_2":
                    0,

                "estatisticas":
                    {},

                "h2h":
                    []
            }

        jogos_casa = (
            self.obter_jogos_equipa(
                id_casa,
                20
            )
        )

        jogos_fora = (
            self.obter_jogos_equipa(
                id_fora,
                20
            )
        )

        rc = self._resultados(
            equipa_casa,
            jogos_casa
        )

        rf = self._resultados(
            equipa_fora,
            jogos_fora
        )

        h2h = self.pesquisar_jogo(
            equipa_casa,
            equipa_fora
        )

        # ================================================
        # H2H
        # ================================================

        rh = []

        for jogo in h2h:

            hs = jogo.get(
                "home_score"
            )

            aws = jogo.get(
                "away_score"
            )

            if (
                hs is None
                or aws is None
            ):
                continue

            home = str(
                jogo.get(
                    "home_team",
                    ""
                )
            ).lower()

            if equipa_casa.lower() in home:

                gols_casa = int(hs)
                gols_fora = int(aws)

            else:

                gols_casa = int(aws)
                gols_fora = int(hs)

            rh.append({

                "total":
                    gols_casa + gols_fora,

                "btts":
                    (
                        gols_casa > 0
                        and gols_fora > 0
                    ),

                "casa_win":
                    gols_casa > gols_fora,

                "fora_win":
                    gols_fora > gols_casa,

                "draw":
                    gols_casa == gols_fora
            })

        # ================================================
        # FUNÇÕES DE CÁLCULO
        # ================================================

        def recente(condicao):

            total = len(rc) + len(rf)

            if total == 0:
                return 0

            acertos = sum(
                1
                for x in rc
                if condicao(x)
            )

            acertos += sum(
                1
                for x in rf
                if condicao(x)
            )

            return (
                acertos
                / total
                * 100
            )

        def h2h_pct(condicao):

            return self._pct(
                rh,
                condicao
            )

        def combinar(
            valor_recente,
            valor_h2h
        ):

            if len(rh) >= 3:

                return round(
                    (
                        valor_recente
                        * 0.55
                    )
                    +
                    (
                        valor_h2h
                        * 0.45
                    ),
                    1
                )

            return round(
                valor_recente,
                1
            )

        # ================================================
        # MERCADOS DE GOLOS
        # ================================================

        over_15 = combinar(
            recente(
                lambda x:
                    x["total"] >= 2
            ),
            h2h_pct(
                lambda x:
                    x["total"] >= 2
            )
        )

        over_25 = combinar(
            recente(
                lambda x:
                    x["total"] >= 3
            ),
            h2h_pct(
                lambda x:
                    x["total"] >= 3
            )
        )

        under_35 = combinar(
            recente(
                lambda x:
                    x["total"] <= 3
            ),
            h2h_pct(
                lambda x:
                    x["total"] <= 3
            )
        )

        under_45 = combinar(
            recente(
                lambda x:
                    x["total"] <= 4
            ),
            h2h_pct(
                lambda x:
                    x["total"] <= 4
            )
        )

        btts = combinar(
            recente(
                lambda x:
                    x["btts"]
            ),
            h2h_pct(
                lambda x:
                    x["btts"]
            )
        )

        # ================================================
        # RESULTADOS
        # ================================================

        win_casa = self._pct(
            rc,
            lambda x:
                x["win"]
        )

        win_fora = self._pct(
            rf,
            lambda x:
                x["win"]
        )

        draw_casa = self._pct(
            rc,
            lambda x:
                x["draw"]
        )

        draw_fora = self._pct(
            rf,
            lambda x:
                x["draw"]
        )

        empate = (
            draw_casa
            + draw_fora
        ) / 2

        casa_direto = combinar(
            (
                win_casa
                * 0.65
            )
            +
            (
                (100 - win_fora)
                * 0.35
            ),

            h2h_pct(
                lambda x:
                    x["casa_win"]
            )
        )

        fora_direto = combinar(
            (
                win_fora
                * 0.65
            )
            +
            (
                (100 - win_casa)
                * 0.35
            ),

            h2h_pct(
                lambda x:
                    x["fora_win"]
            )
        )

        empate = combinar(
            empate,
            h2h_pct(
                lambda x:
                    x["draw"]
            )
        )

        casa_ou_empate = min(
            99,
            casa_direto + empate
        )

        fora_ou_empate = min(
            99,
            fora_direto + empate
        )

        # ================================================
        # MERCADOS FINAIS
        # ================================================

        mercados = {

            "Ambas Marcam":
                self.limitar(
                    btts
                ),

            "Mais de 1.5 golos":
                self.limitar(
                    over_15
                ),

            "Mais de 2.5 golos":
                self.limitar(
                    over_25
                ),

            "Menos de 3.5 golos":
                self.limitar(
                    under_35
                ),

            "Menos de 4.5 golos":
                self.limitar(
                    under_45
                ),

            f"{equipa_casa} ganha ou empata (1X)":
                self.limitar(
                    casa_ou_empate
                ),

            f"{equipa_fora} ganha ou empata (X2)":
                self.limitar(
                    fora_ou_empate
                ),

            f"{equipa_casa} ganha direto":
                self.limitar(
                    casa_direto
                ),

            f"{equipa_fora} ganha direto":
                self.limitar(
                    fora_direto
                )
        }

        # ================================================
        # MELHOR MERCADO
        # ================================================

        ordenados = sorted(
            mercados.items(),
            key=lambda x:
                x[1],
            reverse=True
        )

        if ordenados:

            melhor_mercado = (
                ordenados[0][0]
            )

            melhor_chance = (
                ordenados[0][1]
            )

        else:

            melhor_mercado = (
                "Dados insuficientes"
            )

            melhor_chance = 0

        # ================================================
        # COMBINAÇÕES
        # ================================================

        if len(ordenados) >= 2:

            segunda = ordenados[1]

            combinada_1 = (
                f"{melhor_mercado} + "
                f"{segunda[0]}"
            )

            pct_combinada_1 = (
                min(
                    melhor_chance,
                    segunda[1]
                )
                * 0.85
            )

        else:

            combinada_1 = (
                melhor_mercado
            )

            pct_combinada_1 = (
                melhor_chance
            )

        combinada_2 = (
            "Mais de 1.5 golos + "
            "Menos de 4.5 golos"
        )

        pct_combinada_2 = (
            min(
                over_15,
                under_45
            )
            * 0.88
        )

        # ================================================
        # ESTATÍSTICAS
        # ================================================

        stats_casa = (
            self.get_team_stats_for_ai(
                equipa_casa
            )
        )

        stats_fora = (
            self.get_team_stats_for_ai(
                equipa_fora
            )
        )

        estatisticas = {

            "media_golos_casa":
                stats_casa.get(
                    "media_golos_marcados",
                    0
                ),

            "media_golos_sofridos_casa":
                stats_casa.get(
                    "media_golos_sofridos",
                    0
                ),

            "media_golos_fora":
                stats_fora.get(
                    "media_golos_marcados",
                    0
                ),

            "media_golos_sofridos_fora":
                stats_fora.get(
                    "media_golos_sofridos",
                    0
                ),

            "jogos_casa":
                len(rc),

            "jogos_fora":
                len(rf),

            "h2h_encontrados":
                len(rh)
        }

        return {

            "melhor_mercado":
                melhor_mercado,

            "melhor_chance":
                self.limitar(
                    melhor_chance
                ),

            "mercados":
                mercados,

            "combinada_1":
                combinada_1,

            "pct_combinada_1":
                self.limitar(
                    pct_combinada_1
                ),

            "combinada_2":
                combinada_2,

            "pct_combinada_2":
                self.limitar(
                    pct_combinada_2
                ),

            "estatisticas":
                estatisticas,

            "h2h":
                h2h
        }

    # ======================================================
    # LIMITADOR
    # ======================================================

    @staticmethod
    def limitar(valor):

        try:

            return int(
                max(
                    0,
                    min(
                        99,
                        round(
                            float(valor)
                        )
                    )
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return 0


# Compatibilidade com o app.py
FootballAIEngine = SoccerDataScraper
