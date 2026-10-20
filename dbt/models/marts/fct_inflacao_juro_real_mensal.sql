-- Fato mensal: IPCA (mês, ano e 12 meses), Selic média e juro real ex-post.
with ipca as (

    select
        date_trunc(data_referencia, month) as mes,
        valor                               as ipca_mensal_pct
    from {{ ref('stg_bcb__series_sgs') }}
    where nome_serie = 'ipca_mensal'

),

selic_mensal as (

    select
        mes,
        avg(selic_meta_aa) as selic_meta_media_aa
    from {{ ref('fct_indicadores_diarios') }}
    group by mes

),

acumulados as (

    select
        mes,
        ipca_mensal_pct,

        -- acumulado composto: produto de (1 + taxa) via exp(soma de logs)
        (exp(sum(ln(1 + ipca_mensal_pct / 100)) over (
            order by mes rows between 11 preceding and current row
        )) - 1) * 100                                          as ipca_12m_pct,

        count(*) over (
            order by mes rows between 11 preceding and current row
        )                                                      as meses_na_janela,

        (exp(sum(ln(1 + ipca_mensal_pct / 100)) over (
            partition by extract(year from mes) order by mes
        )) - 1) * 100                                          as ipca_acumulado_ano_pct

    from ipca

)

select
    a.mes,
    round(a.ipca_mensal_pct, 2)                                as ipca_mensal_pct,
    round(a.ipca_acumulado_ano_pct, 2)                         as ipca_acumulado_ano_pct,
    -- só publica o acumulado em 12 meses quando a janela está completa
    if(a.meses_na_janela = 12, round(a.ipca_12m_pct, 2), null) as ipca_12m_pct,
    round(s.selic_meta_media_aa, 2)                            as selic_meta_media_aa,
    -- juro real ex-post (equação de Fisher): (1 + nominal) / (1 + inflação) - 1
    if(
        a.meses_na_janela = 12,
        round(((1 + s.selic_meta_media_aa / 100) / (1 + a.ipca_12m_pct / 100) - 1) * 100, 2),
        null
    )                                                          as juro_real_ex_post_aa
from acumulados a
left join selic_mensal s
    on s.mes = a.mes
