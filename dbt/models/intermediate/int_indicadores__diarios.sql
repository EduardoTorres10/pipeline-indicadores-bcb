-- Calendário diário contínuo com Selic e dólar lado a lado.
-- Em fins de semana e feriados o dólar não é cotado: guardamos o valor
-- observado (pode ser nulo) e uma versão com o último valor conhecido.
with series as (

    select data_referencia, nome_serie, valor
    from {{ ref('stg_bcb__series_sgs') }}
    where nome_serie in ('selic_meta', 'dolar_venda')

),

limites as (

    -- começa quando AMBAS as séries já têm valor, para não haver nulos no início
    select
        max(data_min) as data_min,
        max(data_max) as data_max
    from (
        select nome_serie, min(data_referencia) as data_min, max(data_referencia) as data_max
        from series
        group by nome_serie
    )

),

calendario as (

    select data
    from limites, unnest(generate_date_array(data_min, data_max)) as data

),

pivotado as (

    select
        data_referencia,
        max(if(nome_serie = 'selic_meta', valor, null))  as selic_meta_aa,
        max(if(nome_serie = 'dolar_venda', valor, null)) as dolar_venda
    from series
    group by data_referencia

)

select
    c.data,
    p.dolar_venda is not null                                    as teve_cotacao_dolar,
    p.dolar_venda                                                as dolar_venda_observado,
    last_value(p.dolar_venda ignore nulls) over w                as dolar_venda,
    last_value(p.selic_meta_aa ignore nulls) over w              as selic_meta_aa
from calendario c
left join pivotado p
    on p.data_referencia = c.data
window w as (order by c.data rows between unbounded preceding and current row)
