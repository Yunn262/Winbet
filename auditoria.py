"""
FootballAI Bot - Auditoria e HistÃ³rico de Palpites

Regista palpites offline e permite liquidÃ¡-los quando existe
um placar real. A validaÃ§Ã£o nunca usa a confianÃ§a do modelo
para fabricar um Green/Red: sem resultado real, fica Pendente.
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd


FICHEIRO_HISTORICO = "historico_palpites.json"


class AuditoriaPalpites:

    def __init__(self):
        self.historico = self._carregar_historico()

    # ========================================================
    # ARQUIVO
    # ========================================================

    def _carregar_historico(self) -> List[Dict[str, Any]]:
        if not os.path.exists(FICHEIRO_HISTORICO):
            return []

        try:
            with open(
                FICHEIRO_HISTORICO,
                "r",
                encoding="utf-8",
            ) as f:
                dados = json.load(f)

            if not isinstance(dados, list):
                return []

            return dados

        except Exception:
            return []

    def _salvar_historico(self):
        try:
            with open(
                FICHEIRO_HISTORICO,
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(
                    self.historico,
                    f,
                    indent=4,
                    ensure_ascii=False,
                )
        except Exception as exc:
            print(f"Erro ao salvar histÃ³rico: {exc}")

    # ========================================================
    # REGISTAR PALPITE
    # ========================================================

    def registrar_palpite(
        self,
        casa: str,
        fora: str,
        mercado: str,
        chance: float,
        combinada: str,
    ):
        """
        Regista um palpite prÃ©-jogo.

        Evita duplicar a mesma partida no mesmo dia.
        """

        data_hoje = datetime.now().strftime("%Y-%m-%d")

        casa = str(casa).strip()
        fora = str(fora).strip()
        mercado = str(mercado).strip()
        combinada = str(combinada).strip()

        # Evita duplicaÃ§Ã£o.
        for palpite in self.historico:
            if (
                str(palpite.get("casa", "")).strip().lower()
                == casa.lower()
                and
                str(palpite.get("fora", "")).strip().lower()
                == fora.lower()
                and
                palpite.get("data_registro") == data_hoje
            ):
                return

        novo_id = (
            max(
                [
                    int(p.get("id", 0))
                    for p in self.historico
                    if str(p.get("id", "")).isdigit()
                ],
                default=0,
            )
            + 1
        )

        novo_palpite = {
            "id": novo_id,
            "data_registro": data_hoje,
            "casa": casa,
            "fora": fora,
            "mercado_sugerido": mercado,
            "chance_calculada": float(chance or 0),
            "combinada_sugerida": combinada,
            "status_liquidacao": "Pendente",
            "placar_real": "? - ?",
        }

        self.historico.append(novo_palpite)
        self._salvar_historico()

    # ========================================================
    # UTILITÃRIOS DE NORMALIZAÃ‡ÃƒO
    # ========================================================

    @staticmethod
    def _normalizar(texto: Any) -> str:
        texto = str(texto or "").lower().strip()

        substituicoes = {
            "Ã¡": "a",
            "Ã ": "a",
            "Ã£": "a",
            "Ã¢": "a",
            "Ã©": "e",
            "Ãª": "e",
            "Ã­": "i",
            "Ã³": "o",
            "Ã´": "o",
            "Ãµ": "o",
            "Ãº": "u",
            "Ã§": "c",
        }

        for antigo, novo in substituicoes.items():
            texto = texto.replace(antigo, novo)

        return re.sub(r"\s+", " ", texto)

    @staticmethod
    def _valor_numerico(valor: Any) -> Optional[float]:
        try:
            if pd.isna(valor):
                return None
            return float(valor)
        except (TypeError, ValueError):
            return None

    # ========================================================
    # VALIDAR MERCADO
    # ========================================================

    def _validar_mercado(
        self,
        mercado: str,
        gols_casa: int,
        gols_fora: int,
    ) -> Optional[bool]:

        m = self._normalizar(mercado)

        total_gols = gols_casa + gols_fora

        # ----------------------------------------------------
        # MAIS DE 1.5
        # ----------------------------------------------------

        if (
            "mais de 1.5" in m
            or "mais 1.5" in m
        ):
            return total_gols >= 2

        # ----------------------------------------------------
        # MAIS DE 2.5
        # ----------------------------------------------------

        if (
            "mais de 2.5" in m
            or "mais 2.5" in m
        ):
            return total_gols >= 3

        # ----------------------------------------------------
        # MENOS DE 3.5
        # ----------------------------------------------------

        if (
            "menos de 3.5" in m
            or "menos 3.5" in m
        ):
            return total_gols <= 3

        # ----------------------------------------------------
        # AMBAS MARCAM
        # ----------------------------------------------------

        if (
            "ambas marcam" in m
            or "ambas marcaram" in m
        ):
            return gols_casa >= 1 and gols_fora >= 1

        # ----------------------------------------------------
        # CASA OU EMPATE
        # ----------------------------------------------------

        if (
            "casa ou empate" in m
            or "1x" in m
        ):
            return gols_casa >= gols_fora

        # ----------------------------------------------------
        # FORA OU EMPATE
        # ----------------------------------------------------

        if (
            "fora ou empate" in m
            or "x2" in m
        ):
            return gols_fora >= gols_casa

        # ----------------------------------------------------
        # VITÃ“RIA CASA
        # ----------------------------------------------------

        if (
            "vitoria casa" in m
            or "vitoria da casa" in m
            or "ganha casa" in m
        ):
            return gols_casa > gols_fora

        # ----------------------------------------------------
        # VITÃ“RIA FORA
        # ----------------------------------------------------

        if (
            "vitoria fora" in m
            or "vitoria visitante" in m
            or "ganha fora" in m
        ):
            return gols_fora > gols_casa

        # ----------------------------------------------------
        # EMPATE
        # ----------------------------------------------------

        if (
            m == "empate"
            or "empate" in m and "ou" not in m
        ):
            return gols_casa == gols_fora

        # Mercado desconhecido.
        # NÃ£o inventar resultado.
        return None

    # ========================================================
    # LIQUIDAÃ‡ÃƒO
    # ========================================================

    def liquidar_palpites_com_base_dados(
        self,
        df_jogos_realizados: pd.DataFrame,
    ):
        """
        Cruza o histÃ³rico com resultados reais.

        Aceita DataFrames que tenham:
            home_team / away_team
            home_score / away_score

        TambÃ©m aceita:
            home / away
            home_goals / away_goals

        Palpites de mercados nÃ£o suportados permanecem Pendente.
        """

        if (
            df_jogos_realizados is None
            or df_jogos_realizados.empty
            or not self.historico
        ):
            return

        df_jogos = df_jogos_realizados.copy()

        # ----------------------------------------------------
        # Nomes alternativos de colunas
        # ----------------------------------------------------

        mapa = {
            "home": "home_team",
            "away": "away_team",
            "home_goals": "home_score",
            "away_goals": "away_score",
            "home_goal": "home_score",
            "away_goal": "away_score",
        }

        df_jogos = df_jogos.rename(
            columns={
                origem: destino
                for origem, destino in mapa.items()
                if origem in df_jogos.columns
                and destino not in df_jogos.columns
            }
        )

        colunas_obrigatorias = {
            "home_team",
            "away_team",
            "home_score",
            "away_score",
        }

        if not colunas_obrigatorias.issubset(
            set(df_jogos.columns)
        ):
            print(
                "Auditoria: DataFrame sem as colunas necessÃ¡rias "
                "para liquidaÃ§Ã£o."
            )
            return

        # ----------------------------------------------------
        # Normalizar nomes
        # ----------------------------------------------------

        df_jogos["_home_norm"] = (
            df_jogos["home_team"]
            .astype(str)
            .map(self._normalizar)
        )

        df_jogos["_away_norm"] = (
            df_jogos["away_team"]
            .astype(str)
            .map(self._normalizar)
        )

        for palpite in self.historico:

            if palpite.get("status_liquidacao") != "Pendente":
                continue

            casa = self._normalizar(
                palpite.get("casa", "")
            )

            fora = self._normalizar(
                palpite.get("fora", "")
            )

            partida = df_jogos[
                (df_jogos["_home_norm"] == casa)
                &
                (df_jogos["_away_norm"] == fora)
            ]

            if partida.empty:
                continue

            row = partida.iloc[0]

            gols_casa_val = self._valor_numerico(
                row.get("home_score")
            )

            gols_fora_val = self._valor_numerico(
                row.get("away_score")
            )

            # Sem placar final nÃ£o liquidar.
            if (
                gols_casa_val is None
                or gols_fora_val is None
            ):
                continue

            gols_casa = int(gols_casa_val)
            gols_fora = int(gols_fora_val)

            palpite["placar_real"] = (
                f"{gols_casa} - {gols_fora}"
            )

            resultado = self._validar_mercado(
                palpite.get("mercado_sugerido", ""),
                gols_casa,
                gols_fora,
            )

            # Mercado ainda nÃ£o suportado:
            # mantÃ©m Pendente em vez de fabricar Green/Red.
            if resultado is None:
                palpite["status_liquidacao"] = "Pendente"
                continue

            palpite["status_liquidacao"] = (
                "Green" if resultado else "Red"
            )

        self._salvar_historico()

    # ========================================================
    # LIQUIDAÃ‡ÃƒO DIRETA DE UM RESULTADO
    # ========================================================

    def liquidar_palpite(
        self,
        palpite_id: int,
        gols_casa: int,
        gols_fora: int,
    ) -> bool:

        for palpite in self.historico:

            if int(palpite.get("id", -1)) != int(palpite_id):
                continue

            if (
                palpite.get("status_liquidacao")
                != "Pendente"
            ):
                return False

            resultado = self._validar_mercado(
                palpite.get("mercado_sugerido", ""),
                int(gols_casa),
                int(gols_fora),
            )

            if resultado is None:
                return False

            palpite["placar_real"] = (
                f"{int(gols_casa)} - {int(gols_fora)}"
            )

            palpite["status_liquidacao"] = (
                "Green" if resultado else "Red"
            )

            self._salvar_historico()
            return True

        return False

    # ========================================================
    # ESTATÃSTICAS
    # ========================================================

    def obter_estatisticas_gerais(
        self,
    ) -> Dict[str, Any]:

        total = len(self.historico)

        greens = sum(
            1
            for p in self.historico
            if p.get("status_liquidacao") == "Green"
        )

        reds = sum(
            1
            for p in self.historico
            if p.get("status_liquidacao") == "Red"
        )

        pendentes = sum(
            1
            for p in self.historico
            if p.get("status_liquidacao") == "Pendente"
        )

        validados = greens + reds

        win_rate = (
            greens / validados * 100
            if validados > 0
            else 0.0
        )

        return {
            "total": total,
            "greens": greens,
            "reds": reds,
            "pendentes": pendentes,
            "win_rate": round(win_rate, 1),
        }

    # ========================================================
    # LIMPAR HISTÃ“RICO
    # ========================================================

    def limpar_historico(self):
        self.historico = []
        self._salvar_historico()
