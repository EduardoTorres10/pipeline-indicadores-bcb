-- Fato diário: Selic e câmbio com métricas derivadas para análise e BI.
with base as (

    select * from {{ ref('int_indicadores__diarios') }}

),

dias_uteis as (

    -- métricas de câmbio calculadas só sobre dias com cotação
    select
        data,
        dolar_venda_observado,
        lag(dolar_venda_observado) over (order by data) as dolar_dia_util_anterior,
        avg(dolar_venda_observado) over (
            order by data rows between 20 preceding and current row
        ) as dolar_media_movel_21du
    from base
    where teve_cotacao_dolar

)

select
    b.data,
    extract(year from b.data)                                   as ano,
    date_trunc(b.data, month)                                   as mes,
    b.teve_cotacao_dolar                                        as dia_util,
    b.selic_meta_aa,
    b.dolar_venda,
    round(
        safe_divide(d.dolar_venda_observado - d.dolar_dia_util_anterior, d.dolar_dia_util_anterior) * 100,
        4
    )                                                           as dolar_variacao_diaria_pct,
    round(d.dolar_media_movel_21du, 4)                          as dolar_media_movel_21du
from base b
left join dias_uteis d
    on d.data = b.data
