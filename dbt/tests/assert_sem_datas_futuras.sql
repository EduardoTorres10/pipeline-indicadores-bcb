-- Teste singular: falha se alguma série tiver data de referência no futuro.
-- O IPCA é publicado com data do primeiro dia do mês, então a tolerância é de 1 mês.
select *
from {{ ref('stg_bcb__series_sgs') }}
where data_referencia > date_add(current_date('America/Sao_Paulo'), interval 1 month)
