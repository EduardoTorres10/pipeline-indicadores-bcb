"""
DAG: pipeline_indicadores_bcb

Fluxo (ELT):
    1. extrair_e_carregar  -> API do BCB  -> BigQuery (dataset raw)
    2. dbt_deps            -> instala pacotes do dbt
    3. dbt_build           -> roda modelos + testes (staging -> intermediate -> marts)

Roda em dias úteis às 9h (horário de Brasília), depois da divulgação das taxas do dia anterior.
"""

from __future__ import annotations

import subprocess
from datetime import timedelta

import pendulum
from airflow.sdk import dag, task

AIRFLOW_HOME = "/usr/local/airflow"
DBT_DIR = f"{AIRFLOW_HOME}/dbt"
DBT_BIN = f"{AIRFLOW_HOME}/dbt_venv/bin/dbt"
DBT_TARGET = "prod"


def _rodar_dbt(*args: str) -> None:
    """Executa um comando do dbt e falha a task se o dbt falhar."""
    cmd = [DBT_BIN, *args, "--project-dir", DBT_DIR, "--profiles-dir", DBT_DIR, "--target", DBT_TARGET]
    print("Executando:", " ".join(cmd))
    resultado = subprocess.run(cmd, capture_output=True, text=True)
    print(resultado.stdout)
    if resultado.returncode != 0:
        print(resultado.stderr)
        raise RuntimeError(f"dbt {' '.join(args)} falhou (código {resultado.returncode})")


@dag(
    dag_id="pipeline_indicadores_bcb",
    schedule="0 9 * * 1-5",
    start_date=pendulum.datetime(2026, 1, 1, tz="America/Sao_Paulo"),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "dados",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["bcb", "dbt", "bigquery"],
    doc_md=__doc__,
)
def pipeline_indicadores_bcb():
    @task
    def extrair_e_carregar() -> int:
        from include.ingestion import bcb

        return bcb.run()

    @task
    def dbt_deps() -> None:
        _rodar_dbt("deps")

    @task
    def dbt_build() -> None:
        _rodar_dbt("build")

    extrair_e_carregar() >> dbt_deps() >> dbt_build()


pipeline_indicadores_bcb()
