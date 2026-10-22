-- Dimensão de datas contínua, em anos completos, para o modelo estrela no Power BI.
-- Liga com fct_indicadores_diarios[data] e fct_inflacao_juro_real_mensal[mes].
with limites as (

    select
        date_trunc(min(data_referencia), year)  as data_min,
        last_day(max(data_referencia), year)    as data_max
    from {{ ref('stg_bcb__series_sgs') }}

),

datas as (

    select data
    from limites, unnest(generate_date_array(data_min, data_max)) as data

)

select
    data,
    extract(year from data)                                         as ano,
    extract(quarter from data)                                      as trimestre,
    concat(cast(extract(year from data) as string), '-T',
           cast(extract(quarter from data) as string))               as ano_trimestre,
    extract(month from data)                                        as mes_numero,
    ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
     'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        [offset(extract(month from data) - 1)]                      as mes_nome,
    concat(
        ['jan', 'fev', 'mar', 'abr', 'mai', 'jun',
         'jul', 'ago', 'set', 'out', 'nov', 'dez'][offset(extract(month from data) - 1)],
        '/', format_date('%y', data)
    )                                                               as mes_ano,
    -- chave numérica para ordenar mes_ano no Power BI (Classificar por coluna)
    extract(year from data) * 100 + extract(month from data)        as mes_ano_ordem,
    date_trunc(data, month)                                         as inicio_mes,
    extract(dayofweek from data)                                    as dia_semana_numero,
    ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
        [offset(extract(dayofweek from data) - 1)]                  as dia_semana_nome,
    extract(dayofweek from data) in (1, 7)                          as fim_de_semana
from datas
