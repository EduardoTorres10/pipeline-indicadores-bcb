FROM astrocrpublic.azurecr.io/runtime:3.1

# dbt fica num ambiente virtual separado para não conflitar
# com as dependências do próprio Airflow.
RUN python -m venv dbt_venv && \
    dbt_venv/bin/pip install --no-cache-dir "dbt-bigquery==1.12.*"
