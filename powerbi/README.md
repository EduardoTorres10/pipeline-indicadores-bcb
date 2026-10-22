# Relatório Power BI

Salve aqui o relatório no formato **Power BI Project (.pbip)**: *Arquivo → Salvar como → Arquivos do Power BI Project (\*.pbip)*.
O PBIP grava o relatório e o modelo semântico como arquivos de texto, que o Git consegue versionar e comparar, ao contrário do `.pbix`, que é binário.

O cache de dados (`.pbi/cache.abf`) e as configurações locais (`.pbi/localSettings.json`) já estão no `.gitignore`. Nenhuma credencial do Google é gravada nos arquivos do projeto.

As medidas DAX estão documentadas em [`medidas.dax`](medidas.dax).

## Conexão

- Fonte: **Google BigQuery**, modo **Importar**
- Projeto de cobrança: `portfolio-dados-512321`
- Tabelas: `marts.dim_calendario`, `marts.fct_indicadores_diarios`, `marts.fct_inflacao_juro_real_mensal`
