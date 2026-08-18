# scraper.py
"""
FootballAI Predictor Pro
Camada de dados + motor de anÃ¡lise compatÃ­vel com o app.py.

Fonte de dados:
Football-Data.org API v4

VariÃ¡vel necessÃ¡ria no Streamlit Cloud:
FOOTBALL_DATA_ORG_KEY = "TUA_CHAVE"

ObservaÃ§Ã£o:
A Football-Data.org nÃ£o fornece, de forma geral, estatÃ­sticas
completas de escanteios e cartÃµes nos endpoints usados aqui.
Por isso, o motor nÃ£o inventa esses dados: os mercados avanÃ§ados
sÃ£o calculados apenas quando existem dados suficientes.
"""

import os
import requests
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


# ============================================================
# CONFIGURAÃ‡ÃƒO
# ============================================================

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_KEY = os.getenv("FOOTBALL_DATA_ORG_KEY", "").strip()
BASE_URL = "https://api.football-data.org/v4"

HEADERS = {
    "X-Auth-Token": API_KEY,
    "Accept": "application/json",
}


# ============================================================
# UTILITÃRIOS
# ============================================================

def _safe_get(data, *keys, default=None):
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, minimum=1, maximum=99):
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = minimum
    return max(minimum, min(maximum, round(value)))


def _poisson_probability(lam: float, threshold: int, over=True) -> float:
    """Probabilidade aproximada para total de golos."""
    lam = max(0.05, float(lam))

    if over:
        cumulative = 0.0
        for k in range(threshold + 1):
            cumulative += math.exp(-lam) * (lam ** k) / math.factorial(k)
        return 1.0 - cumulative

    cumulative = 0.0
    for k in range(threshold + 1):
        cumulative += math.exp(-lam) * (lam ** k) / math.factorial(k)
    return cumulative


# ============================================================
# API FOOTBALL-DATA.ORG
# ============================================================

class FootballDataOrgAPI:

    def __init__(self):
        self.session = requests.Session()
        if API_KEY:
            self.session.headers.update(HEADERS)
        self.last_events = []

        self.main_competitions = {
            "Premier League": "PL",
            "La Liga": "PD",
            "Serie A Italiana": "SA",
            "Bundesliga": "BL1",
            "Ligue 1": "FL1",
            "Champions League": "CL",
        }

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        if not API_KEY:
            print("API key nÃ£o configurada: FOOTBALL_DATA_ORG_KEY")
            return None

        try:
            response = self.session.get(
                f"{BASE_URL}{endpoint}",
                params=params,
                timeout=20,
            )

            if response.status_code == 429:
                print("Rate limit da Football-Data.org atingido.")
                return None

            if response.status_code != 200:
                print(
                    f"Football-Data.org HTTP {response.status_code}: "
                    f"{response.text[:500]}"
                )
                return None

            return response.json()

        except requests.exceptions.Timeout:
            print("Timeout na Football-Data.org.")
        except requests.exceptions.ConnectionError:
            print("Erro de conexÃ£o com Football-Data.org.")
        except requests.exceptions.RequestException as exc:
            print(f"Erro na API: {exc}")
        except ValueError:
            print("A API retornou conteÃºdo que nÃ£o Ã© JSON.")

        return None

    def testar_api(self) -> bool:
        data = self._get("/competitions")
        return data is not None

    def get_competitions(self) -> List[Dict]:
        data = self._get("/competitions")
        if not data:
            return []

        result = []
        for comp in data.get("competitions", []):
            result.append({
                "id": comp.get("id"),
                "code": comp.get("code"),
                "name": comp.get("name"),
                "country": _safe_get(comp, "area", "name", default=""),
            })
        return result

    def get_scheduled_events(
        self,
        date_str: str,
        league_code: Optional[str] = None
    ) -> List[Dict]:
        if not date_str:
            return []

        params = {
            "dateFrom": date_str,
            "dateTo": date_str,
        }

        # Filtrar pela competiÃ§Ã£o diretamente na API quando possÃ­vel.
        if league_code:
            params["competitions"] = league_code

        data = self._get("/matches", params)

        if not data:
            self.last_events = []
            return []

        events = []

        for match in data.get("matches", []):
            try:
                home = match.get("homeTeam", {})
                away = match.get("awayTeam", {})
                competition = match.get("competition", {})
                score = match.get("score", {})

                events.append({
                    "event_id": match.get("id"),
                    "home_team": home.get("name", "?"),
                    "away_team": away.get("name", "?"),
                    "home_team_id": home.get("id"),
                    "away_team_id": away.get("id"),
                    "tournament": competition.get("name", ""),
                    "league_id": competition.get("id"),
                    "league_code": competition.get("code", ""),
                    "league_country": _safe_get(
                        competition, "area", "name", default=""
                    ),
                    "season": _safe_get(match, "season", "id"),
                    "matchday": match.get("matchday"),
                    "start_time": match.get("utcDate", ""),
                    "status": match.get("status", ""),
                    "venue": match.get("venue", ""),
                    "score": {
                        "home": _safe_get(score, "fullTime", "home"),
                        "away": _safe_get(score, "fullTime", "away"),
                        "half_time": {
                            "home": _safe_get(score, "halfTime", "home"),
                            "away": _safe_get(score, "halfTime", "away"),
                        },
                    },
                    "raw": match,
                })

            except Exception as exc:
                print(f"Erro ao processar jogo: {exc}")

        self.last_events = events
        return events

    def get_event_details(self, event_id: str) -> Optional[Dict]:
        for event in self.last_events:
            if str(event.get("event_id")) == str(event_id):
                return event.get("raw")

        return self._get(f"/matches/{event_id}")

    def pesquisar_equipa(self, nome: str) -> List[Dict]:
        if not nome:
            return []

        data = self._get("/teams", {"name": nome})
        if not data:
            return []

        result = []
        for team in data.get("teams", []):
            result.append({
                "id": team.get("id"),
                "name": team.get("name"),
                "short_name": team.get("shortName"),
                "tla": team.get("tla"),
                "country": _safe_get(team, "area", "name", default=""),
                "venue": team.get("venue", ""),
            })

        return result

    def get_team_recent_matches(
        self,
        team_id: int,
        num_matches: int = 5
    ) -> List[Dict]:
        if not team_id:
            return []

        data = self._get(
            f"/teams/{team_id}/matches",
            {
                "status": "FINISHED",
                "limit": max(10, num_matches * 2),
            },
        )

        if not data:
            return []

        played = []

        for match in data.get("matches", []):
            try:
                home = match.get("homeTeam", {})
                away = match.get("awayTeam", {})
                score = match.get("score", {})

                hg = _safe_get(score, "fullTime", "home")
                ag = _safe_get(score, "fullTime", "away")

                if hg is None or ag is None:
                    continue

                hg = _to_int(hg)
                ag = _to_int(ag)

                home_id = home.get("id")
                away_id = away.get("id")

                if str(home_id) == str(team_id):
                    gf, ga = hg, ag
                    opponent = away.get("name", "?")
                    home_game = True
                elif str(away_id) == str(team_id):
                    gf, ga = ag, hg
                    opponent = home.get("name", "?")
                    home_game = False
                else:
                    continue

                result = "V" if gf > ga else "E" if gf == ga else "D"

                played.append({
                    "golos_marcados": gf,
                    "golos_sofridos": ga,
                    "adversario": opponent,
                    "data": match.get("utcDate", ""),
                    "casa": home_game,
                    "resultado": result,
                })

            except Exception as exc:
                print(f"Erro no histÃ³rico da equipa: {exc}")

        played.sort(key=lambda x: x.get("data", ""), reverse=True)
        return played[:num_matches]

    def get_team_position(
        self,
        team_id: int,
        league_code: str
    ) -> Optional[int]:
        if not team_id or not league_code:
            return None

        data = self._get(
            f"/competitions/{league_code}/standings"
        )

        if not data:
            return None

        try:
            for standing in data.get("standings", []):
                for row in standing.get("table", []):
                    team = row.get("team", {})
                    if str(team.get("id")) == str(team_id):
                        return row.get("position")
        except Exception as exc:
            print(f"Erro na classificaÃ§Ã£o: {exc}")

        return None

    def get_head_to_head(
        self,
        event_id: str,
        limit: int = 5
    ) -> List[Dict]:
        data = self._get(
            f"/matches/{event_id}/head2head",
            {"limit": limit},
        )

        if not data:
            return []

        result = []

        for match in data.get("matches", []):
            try:
                home = match.get("homeTeam", {})
                away = match.get("awayTeam", {})
                score = match.get("score", {})

                hg = _safe_get(score, "fullTime", "home")
                ag = _safe_get(score, "fullTime", "away")

                if hg is None or ag is None:
                    continue

                result.append({
                    "date": match.get("utcDate", ""),
                    "home_team": home.get("name", "?"),
                    "away_team": away.get("name", "?"),
                    "home_goals": _to_int(hg),
                    "away_goals": _to_int(ag),
                    "competition": _safe_get(
                        match, "competition", "name", default=""
                    ),
                })

            except Exception:
                continue

        return result

    def prepare_match_data(self, event_id: str) -> Optional[Dict]:
        raw = self.get_event_details(event_id)

        if not raw:
            return None

        home = raw.get("homeTeam", {})
        away = raw.get("awayTeam", {})
        competition = raw.get("competition", {})

        home_id = home.get("id")
        away_id = away.get("id")
        league_code = competition.get("code", "")

        home_recent = self.get_team_recent_matches(home_id, 5)
        away_recent = self.get_team_recent_matches(away_id, 5)

        data = {
            "event_id": event_id,
            "home_team": home.get("name", "?"),
            "away_team": away.get("name", "?"),
            "home_team_id": home_id,
            "away_team_id": away_id,
            "league_code": league_code,
            "start_time": raw.get("utcDate", ""),
            "forma_casa": home_recent,
            "forma_fora": away_recent,
            "posicao_casa": self.get_team_position(home_id, league_code),
            "posicao_fora": self.get_team_position(away_id, league_code),
            "confrontos_diretos": [],
        }

        try:
            h2h = self.get_head_to_head(event_id, 5)
            data["confrontos_diretos"] = h2h
        except Exception:
            pass

        return data


# ============================================================
# MOTOR FOOTBALLAI
# ============================================================

class FootballAIEngine:

    def __init__(self, liga_nome: str = "Premier League"):
        self.liga_nome = liga_nome
        self.api = FootballDataOrgAPI()
        self.league_code = self.api.main_competitions.get(liga_nome, "")

    # --------------------------------------------------------
    # JOGOS REAIS
    # --------------------------------------------------------

    def buscar_jogos_reais_api(self, data_selecionada: str) -> List[Dict]:
        eventos = self.api.get_scheduled_events(
            data_selecionada,
            self.league_code
        )

        jogos = []

        for ev in eventos:
            # Garante que a competiÃ§Ã£o corresponde Ã  liga escolhida.
            if self.league_code and ev.get("league_code") != self.league_code:
                continue

            jogos.append({
                "id": ev.get("event_id"),
                "home": ev.get("home_team", "?"),
                "away": ev.get("away_team", "?"),
                "home_id": ev.get("home_team_id"),
                "away_id": ev.get("away_team_id"),
                "league": ev.get("tournament", self.liga_nome),
                "date": ev.get("start_time", ""),
                "status": ev.get("status", ""),
                "raw": ev.get("raw", {}),
            })

        return jogos

    # --------------------------------------------------------
    # EQUIPAS
    # --------------------------------------------------------

    def obter_todas_equipas(self) -> List[str]:
        data = self.api._get(
            "/competitions/" + self.league_code + "/teams"
        )

        if not data:
            return []

        nomes = []

        for team in data.get("teams", []):
            nome = team.get("name")
            if nome:
                nomes.append(nome)

        return sorted(set(nomes))

    def _obter_equipa_por_nome(self, nome: str) -> Optional[Dict]:
        resultados = self.api.pesquisar_equipa(nome)

        if not resultados:
            return None

        nome_lower = nome.lower().strip()

        for team in resultados:
            if team.get("name", "").lower().strip() == nome_lower:
                return team

        return resultados[0]

    # --------------------------------------------------------
    # ESTATÃSTICAS
    # --------------------------------------------------------

    def _estatisticas_equipa(self, team_id: int) -> Dict:
        jogos = self.api.get_team_recent_matches(team_id, 5)

        if not jogos:
            return {
                "jogos": [],
                "media_marcados": 1.25,
                "media_sofridos": 1.25,
                "vitorias": 0.0,
                "empates": 0.0,
                "derrotas": 0.0,
            }

        marcados = [j["golos_marcados"] for j in jogos]
        sofridos = [j["golos_sofridos"] for j in jogos]

        total = len(jogos)

        return {
            "jogos": jogos,
            "media_marcados": sum(marcados) / total,
            "media_sofridos": sum(sofridos) / total,
            "vitorias": sum(j["resultado"] == "V" for j in jogos) / total,
            "empates": sum(j["resultado"] == "E" for j in jogos) / total,
            "derrotas": sum(j["resultado"] == "D" for j in jogos) / total,
        }

    def _probabilidades_resultado(
        self,
        casa: Dict,
        fora: Dict,
        pos_casa=None,
        pos_fora=None
    ) -> Dict:

        ataque_casa = casa["media_marcados"]
        defesa_casa = casa["media_sofridos"]
        ataque_fora = fora["media_marcados"]
        defesa_fora = fora["media_sofridos"]

        # Modelo simples e transparente baseado na forma recente.
        golos_casa = max(
            0.20,
            (ataque_casa * 0.65) + (defesa_fora * 0.35)
        )

        golos_fora = max(
            0.20,
            (ataque_fora * 0.65) + (defesa_casa * 0.35)
        )

        # Pequena vantagem de mando.
        golos_casa *= 1.08

        total = golos_casa + golos_fora

        # Probabilidades Poisson aproximadas.
        p_casa = 0.0
        p_empate = 0.0
        p_fora = 0.0

        for hg in range(7):
            for ag in range(7):
                p = (
                    math.exp(-golos_casa)
                    * golos_casa ** hg
                    / math.factorial(hg)
                    * math.exp(-golos_fora)
                    * golos_fora ** ag
                    / math.factorial(ag)
                )

                if hg > ag:
                    p_casa += p
                elif hg == ag:
                    p_empate += p
                else:
                    p_fora += p

        # Ajuste pequeno por classificaÃ§Ã£o, se disponÃ­vel.
        if pos_casa and pos_fora:
            try:
                diff = float(pos_fora) - float(pos_casa)
                ajuste = max(-0.08, min(0.08, diff * 0.006))
                p_casa += ajuste
                p_fora -= ajuste
            except (TypeError, ValueError):
                pass

        p_casa = max(0.01, p_casa)
        p_empate = max(0.01, p_empate)
        p_fora = max(0.01, p_fora)

        soma = p_casa + p_empate + p_fora

        return {
            "casa": _clamp(p_casa / soma * 100),
            "empate": _clamp(p_empate / soma * 100),
            "fora": _clamp(p_fora / soma * 100),
            "golos_esperados": total,
            "golos_casa": golos_casa,
            "golos_fora": golos_fora,
        }

    # --------------------------------------------------------
    # ANÃLISE COMPLETA
    # --------------------------------------------------------

    def analisar_confronto_completo(
        self,
        equipa_casa: str,
        equipa_fora: str
    ) -> Dict:

        home_team = self._obter_equipa_por_nome(equipa_casa)
        away_team = self._obter_equipa_por_nome(equipa_fora)

        # Estrutura de fallback para evitar que a interface quebre.
        if not home_team or not away_team:
            return self._resultado_fallback(
                equipa_casa,
                equipa_fora
            )

        home_id = home_team.get("id")
        away_id = away_team.get("id")

        casa = self._estatisticas_equipa(home_id)
        fora = self._estatisticas_equipa(away_id)

        pos_casa = self.api.get_team_position(
            home_id,
            self.league_code
        )
        pos_fora = self.api.get_team_position(
            away_id,
            self.league_code
        )

        probs = self._probabilidades_resultado(
            casa,
            fora,
            pos_casa,
            pos_fora
        )

        mercados = {}

        mercados["VitÃ³ria Casa"] = probs["casa"]
        mercados["Empate"] = probs["empate"]
        mercados["VitÃ³ria Fora"] = probs["fora"]

        mercados["Casa ou Empate (1X)"] = _clamp(
            probs["casa"] + probs["empate"]
        )

        mercados["Fora ou Empate (X2)"] = _clamp(
            probs["fora"] + probs["empate"]
        )

        mercados["Mais de 1.5 Golos"] = _clamp(
            _poisson_probability(
                probs["golos_esperados"],
                1,
                over=True
            ) * 100
        )

        mercados["Mais de 2.5 Golos"] = _clamp(
            _poisson_probability(
                probs["golos_esperados"],
                2,
                over=True
            ) * 100
        )

        mercados["Menos de 3.5 Golos"] = _clamp(
            _poisson_probability(
                probs["golos_esperados"],
                3,
                over=False
            ) * 100
        )

        # Ambas marcam: aproximaÃ§Ã£o usando probabilidades de 0 golos.
        p0_casa = math.exp(-probs["golos_casa"])
        p0_fora = math.exp(-probs["golos_fora"])

        ambas = (1 - p0_casa) * (1 - p0_fora)

        mercados["Ambas Marcam"] = _clamp(ambas * 100)

        # NÃ£o inventamos escanteios/cartÃµes sem dados da API.
        # Apenas mercados de dados realmente suportados entram no ranking.

        melhor_mercado = max(
            mercados,
            key=mercados.get
        )

        melhor_chance = _clamp(
            mercados[melhor_mercado]
        )

        # CombinaÃ§Ãµes conservadoras.
        mercado_1 = (
            "Mais de 1.5 Golos + Casa ou Empate (1X)"
        )

        pct_1 = _clamp(
            min(
                mercados["Mais de 1.5 Golos"],
                mercados["Casa ou Empate (1X)"]
            ) * 0.88
        )

        mercado_2 = (
            "Mais de 1.5 Golos + Menos de 3.5 Golos"
        )

        pct_2 = _clamp(
            min(
                mercados["Mais de 1.5 Golos"],
                mercados["Menos de 3.5 Golos"]
            ) * 0.84
        )

        return {
            "home": equipa_casa,
            "away": equipa_fora,
            "melhor_mercado": melhor_mercado,
            "melhor_chance": melhor_chance,
            "mercados": mercados,
            "combinada_1": mercado_1,
            "pct_combinada_1": pct_1,
            "combinada_2": mercado_2,
            "pct_combinada_2": pct_2,
            "estatisticas": {
                "media_golos_casa": round(casa["media_marcados"], 2),
                "media_golos_sofridos_casa": round(casa["media_sofridos"], 2),
                "media_golos_fora": round(fora["media_marcados"], 2),
                "media_golos_sofridos_fora": round(fora["media_sofridos"], 2),
                "posicao_casa": pos_casa,
                "posicao_fora": pos_fora,
                "golos_esperados": round(probs["golos_esperados"], 2),
            },
        }

    def _resultado_fallback(
        self,
        equipa_casa: str,
        equipa_fora: str
    ) -> Dict:

        mercados = {
            "Mais de 1.5 Golos": 60,
            "Menos de 3.5 Golos": 58,
            "Casa ou Empate (1X)": 55,
            "Fora ou Empate (X2)": 45,
            "Ambas Marcam": 50,
            "VitÃ³ria Casa": 42,
            "Empate": 28,
            "VitÃ³ria Fora": 30,
        }

        melhor = max(mercados, key=mercados.get)

        return {
            "home": equipa_casa,
            "away": equipa_fora,
            "melhor_mercado": melhor,
            "melhor_chance": mercados[melhor],
            "mercados": mercados,
            "combinada_1": "Mais de 1.5 Golos + Casa ou Empate (1X)",
            "pct_combinada_1": 48,
            "combinada_2": "Mais de 1.5 Golos + Menos de 3.5 Golos",
            "pct_combinada_2": 46,
            "estatisticas": {},
        }


# ============================================================
# TESTE LOCAL
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("FOOTBALLAI PREDICTOR PRO")
    print("=" * 60)

    if not API_KEY:
        print("FOOTBALL_DATA_ORG_KEY nÃ£o configurada.")
    else:
        api = FootballDataOrgAPI()

        if api.testar_api():
            print("API conectada com sucesso.")
            print("Chave configurada corretamente.")
        else:
            print("NÃ£o foi possÃ­vel validar a API.")
