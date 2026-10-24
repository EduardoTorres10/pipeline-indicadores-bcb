# Relatório Power BI

Relatório no formato **Power BI Project (.pbip)**, com o relatório em **PBIR** e o modelo semântico em **TMDL**. Os dois são arquivos de texto, que o Git versiona e compara, ao contrário do `.pbix`, que é binário.

```
powerbi/
├── indicadores_bcb.pbip                 abre o projeto no Power BI Desktop
├── indicadores_bcb.SemanticModel/       modelo: tabelas, relacionamentos e medidas (TMDL)
├── indicadores_bcb.Report/              páginas e visuais (PBIR)
└── medidas.dax                          medidas documentadas
```

## Modelo

Esquema estrela com filtro em direção única:

- `dim_calendario[data]` 1 → * `fct_indicadores_diarios[data]`
- `dim_calendario[data]` 1 → * `fct_inflacao_juro_real_mensal[mes]`

`dim_calendario` está marcada como tabela de datas, e a data/hora automática está desativada. As medidas ficam na tabela `_Medidas`, organizadas em pastas (Taxas, Inflação, Câmbio).

## Páginas

| Página | Conteúdo |
|---|---|
| Visão geral | Selic, IPCA 12 meses, juro real e dólar; Selic × IPCA 12 meses; juro real mensal |
| Câmbio | Fechamento, média e variações; cotação diária com média móvel de 21 dias úteis; variação mensal |
| Inflação | IPCA do mês, 12 meses e acumulado; IPCA mensal; matriz ano × mês em mapa de calor |

A segmentação por ano é sincronizada entre as páginas.

## Como abrir

1. Abra `indicadores_bcb.pbip` no Power BI Desktop.
2. Clique em **Atualizar**. Na primeira vez, entre com a conta Google que tem acesso ao projeto `portfolio-dados-512321`.

O cache de dados (`.pbi/cache.abf`) e as configurações locais (`.pbi/localSettings.json`) ficam fora do Git. Nenhuma credencial é gravada nos arquivos do projeto.
