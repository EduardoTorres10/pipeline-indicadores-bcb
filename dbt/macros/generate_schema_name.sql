{#
    Por padrão o dbt gera schemas como "<dataset>_<schema>" (ex.: analytics_marts).
    Aqui usamos o nome da camada direto em prod (marts, staging...) e mantemos
    o prefixo em dev para cada desenvolvedor ter seu próprio espaço.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- elif target.name == 'prod' -%}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {{ target.schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
