# CLAUDE.md

Contexto para assistentes de IA que trabalham neste repositório.

## Projeto
Pipeline ELT de portfólio: API SGS do Banco Central → BigQuery → dbt → Power BI, orquestrado por Airflow (Astro CLI).
Ambiente do dono: Windows, PowerShell, Docker Desktop + WSL 2, GitHub Desktop. Iniciante em Git, avançado em Power BI.
Explicações e mensagens de commit em português.

## Estrutura
- `include/ingestion/bcb.py`: extrai as séries 432 (Selic meta), 433 (IPCA mensal) e 1 (dólar venda) desde 2015, em janelas de 5 anos, e grava em `raw_bcb.series_sgs` com full refresh (`WRITE_TRUNCATE`). Os valores ficam como texto.
- `dags/pipeline_indicadores_bcb.py`: DAG do Airflow 3, `extrair_e_carregar → dbt_deps → dbt_build`, em dias úteis às 9h (America/Sao_Paulo).
- `dbt/`: dbt Core 1.12 com dbt-bigquery. Targets `dev` (oauth) e `prod` (service account). Em prod os datasets se chamam `staging`, `intermediate` e `marts` (macro `generate_schema_name`).
  - `stg_bcb__series_sgs` → `int_indicadores__diarios` → `dim_calendario`, `fct_indicadores_diarios` (1 linha por dia), `fct_inflacao_juro_real_mensal` (1 linha por mês; `mes` = 1º dia do mês).
  - As taxas estão em pontos percentuais (4.5 = 4,5%).
- `powerbi/`: relatório em formato PBIP (PBIR + TMDL) e `medidas.dax`.
- `.github/workflows/ci.yml`: ruff, pytest, `dbt parse`; `dbt build` na main se houver o segredo `GCP_SA_KEY`.

## Restrições
- BigQuery **Sandbox** (projeto `portfolio-dados-512321`, location US): sem DML (`INSERT`/`MERGE`), então nada de modelos incrementais. As tabelas expiram em 60 dias; rodar a DAG de novo recria tudo.
- **Nunca** ler, exibir nem versionar `.env` ou `include/gcp/service_account.json`.
- Mudanças em `dbt/` exigem `astro dev restart`, porque o dbt fica dentro da imagem. `dags/` e `include/` são lidos direto do disco.
- Ao editar arquivos do PBIP, o Power BI Desktop precisa estar **fechado**.

## Comandos
- Airflow: `astro dev start` | `astro dev restart` | `astro dev stop` (UI em localhost:8080)
- Testes da ingestão: `python -m pytest`

## Power BI
- Conexão: Google BigQuery, modo Importar, BillingProject `portfolio-dados-512321`. Se a Storage API falhar no sandbox: `GoogleBigQuery.Database([BillingProject="portfolio-dados-512321", UseStorageApi=false])`.
- Modelo: `dim_calendario[data]` 1→* `fct_indicadores_diarios[data]` e 1→* `fct_inflacao_juro_real_mensal[mes]`, com filtro em direção única. `dim_calendario` marcada como tabela de datas. `mes_ano` ordenado por `mes_ano_ordem`, `mes_nome` por `mes_numero`, `dia_semana_nome` por `dia_semana_numero`. Ocultar `ano` e `mes` da tabela diária.
- As medidas ficam numa tabela `_Medidas` (fonte: `powerbi/medidas.dax`). As taxas são divididas por 100 e formatadas como %.
- Páginas: **Visão geral** (cartões Selic, IPCA 12m, juro real, dólar; linha Selic × IPCA 12m; segmentação por ano), **Câmbio** (dólar + média móvel 21 du; variação mensal), **Inflação** (colunas do IPCA mensal; matriz ano × mês em mapa de calor).
- Não há Publicar na Web (conta Gmail). O dashboard é mostrado por prints em `docs/img` e um GIF no README.

## Próximos passos
1. Montar o modelo e as páginas no PBIP.
2. Prints e GIF em `docs/img`; atualizar o README com imagens e uma seção de resultados.
