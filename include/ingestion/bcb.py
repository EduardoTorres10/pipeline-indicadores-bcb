"""
Ingestão de séries temporais do SGS (Sistema Gerenciador de Séries) do Banco Central.

Extrai as séries configuradas em SERIES pela API pública do BCB e carrega os dados
brutos (sem transformação) no BigQuery. Toda transformação acontece depois, no dbt.

Estratégia de carga: full refresh (WRITE_TRUNCATE) via load job.
- É idempotente: rodar duas vezes produz o mesmo resultado.
- É compatível com o BigQuery Sandbox, que não aceita DML (INSERT/MERGE) nem streaming.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, date, datetime, timedelta

import requests

# --------------------------------------------------------------------------- #
# CONFIG
# --------------------------------------------------------------------------- #
SERIES: dict[int, str] = {
    432: "selic_meta",       # Taxa Selic definida pelo Copom (% a.a.)
    433: "ipca_mensal",      # IPCA - variação mensal (%)
    1: "dolar_venda",        # Dólar americano (venda), taxa livre (R$)
}
DATA_INICIAL = date(2015, 1, 1)
JANELA_ANOS = 5              # a API limita consultas de séries diárias a 10 anos
URL_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
TIMEOUT_S = 60
TENTATIVAS = 3

TABELA_RAW = "series_sgs"

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Extração
# --------------------------------------------------------------------------- #
def _janelas(inicio: date, fim: date, anos: int) -> list[tuple[date, date]]:
    """Divide o período em janelas de até `anos` anos."""
    janelas = []
    atual = inicio
    while atual <= fim:
        proxima = date(atual.year + anos, atual.month, atual.day)
        janelas.append((atual, min(fim, proxima - timedelta(days=1))))
        atual = proxima
    return janelas


def _get_com_retentativa(url: str, params: dict) -> list[dict]:
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT_S)
            if resp.status_code == 404:
                return []  # período sem dados
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            if tentativa == TENTATIVAS:
                raise
            espera = 2**tentativa
            log.warning("Falha na tentativa %s (%s). Nova tentativa em %ss", tentativa, exc, espera)
            time.sleep(espera)
    return []


def extrair_serie(codigo: int, inicio: date = DATA_INICIAL, fim: date | None = None) -> list[dict]:
    """Retorna os registros brutos de uma série, como vêm da API."""
    fim = fim or date.today()
    registros: list[dict] = []
    for ini, fi in _janelas(inicio, fim, JANELA_ANOS):
        params = {
            "formato": "json",
            "dataInicial": ini.strftime("%d/%m/%Y"),
            "dataFinal": fi.strftime("%d/%m/%Y"),
        }
        registros.extend(_get_com_retentativa(URL_SGS.format(codigo=codigo), params))
    log.info("Série %s: %s registros extraídos", codigo, len(registros))
    return registros


def extrair_todas() -> list[dict]:
    """Extrai todas as séries e adiciona metadados de linhagem."""
    carregado_em = datetime.now(UTC).isoformat()
    linhas = []
    for codigo, nome in SERIES.items():
        for r in extrair_serie(codigo):
            linhas.append(
                {
                    "codigo_serie": codigo,
                    "nome_serie": nome,
                    "data": r["data"],        # mantido como texto (dd/mm/aaaa) na raw
                    "valor": r["valor"],      # mantido como texto na raw
                    "_carregado_em": carregado_em,
                }
            )
    if not linhas:
        raise ValueError("Nenhum registro extraído — abortando para não truncar a tabela raw.")
    return linhas


# --------------------------------------------------------------------------- #
# Carga
# --------------------------------------------------------------------------- #
def carregar_bigquery(linhas: list[dict]) -> int:
    from google.cloud import bigquery

    projeto = os.environ["GCP_PROJECT_ID"]
    dataset = os.environ.get("BQ_DATASET_RAW", "raw_bcb")
    location = os.environ.get("BQ_LOCATION", "US")

    client = bigquery.Client(project=projeto, location=location)
    client.create_dataset(f"{projeto}.{dataset}", exists_ok=True)

    schema = [
        bigquery.SchemaField("codigo_serie", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("nome_serie", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("data", "STRING"),
        bigquery.SchemaField("valor", "STRING"),
        bigquery.SchemaField("_carregado_em", "TIMESTAMP"),
    ]
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    destino = f"{projeto}.{dataset}.{TABELA_RAW}"
    job = client.load_table_from_json(linhas, destino, job_config=job_config)
    job.result()
    log.info("Carregadas %s linhas em %s", job.output_rows, destino)
    return job.output_rows


def run() -> int:
    """Ponto de entrada usado pela DAG e pela linha de comando."""
    return carregar_bigquery(extrair_todas())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run()
