"""Testes unitários da ingestão (não acessam a API nem o BigQuery)."""

from datetime import date
from itertools import pairwise
from unittest.mock import patch

import pytest

from include.ingestion import bcb


def test_janelas_cobrem_periodo_sem_sobreposicao():
    janelas = bcb._janelas(date(2015, 1, 1), date(2026, 10, 20), anos=5)
    assert janelas[0][0] == date(2015, 1, 1)
    assert janelas[-1][1] == date(2026, 10, 20)
    for (_, fim), (inicio_seguinte, _) in pairwise(janelas):
        assert (inicio_seguinte - fim).days == 1


def test_janelas_respeitam_limite_de_10_anos_da_api():
    for inicio, fim in bcb._janelas(date(2000, 1, 1), date(2026, 1, 1), anos=bcb.JANELA_ANOS):
        assert (fim - inicio).days < 10 * 366


def test_extrair_todas_adiciona_metadados():
    fake = [{"data": "02/01/2025", "valor": "6.19"}]
    with patch.object(bcb, "extrair_serie", return_value=fake):
        linhas = bcb.extrair_todas()
    assert len(linhas) == len(bcb.SERIES)
    assert {"codigo_serie", "nome_serie", "data", "valor", "_carregado_em"} <= linhas[0].keys()


def test_extrair_todas_falha_sem_dados():
    with patch.object(bcb, "extrair_serie", return_value=[]), pytest.raises(ValueError):
        bcb.extrair_todas()
