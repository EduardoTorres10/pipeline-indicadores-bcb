-- Limpeza e tipagem: texto -> DATE e NUMERIC, remoção de duplicatas.
with origem as (

    select * from {{ source('bcb', 'series_sgs') }}

),

tipado as (

    select
        codigo_serie,
        nome_serie,
        parse_date('%d/%m/%Y', data)   as data_referencia,
        safe_cast(valor as numeric)    as valor,
        _carregado_em                  as carregado_em
    from origem
    where valor is not null
      and trim(valor) != ''

)

select *
from tipado
qualify row_number() over (
    partition by codigo_serie, data_referencia
    order by carregado_em desc
) = 1
