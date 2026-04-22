# logBrida

Aplicacao Streamlit multipaginas para analise logistica.

## Estrutura para deploy

Arquivos que devem ir para o repositório:
- `app.py`
- `pages/`
- `utils/`
- `data/base.xlsx`
- `requirements.txt`
- `.streamlit/config.toml`
- `README.md`

Arquivos que nao devem ir para o repositório:
- `.venv/`
- `Base_dashBoard 1  (1).xlsm`
- `.streamlit/secrets.toml`

## Deploy no Streamlit Community Cloud

1. Suba este projeto para um repositório GitHub.
2. Confirme que `data/base.xlsx` foi enviado ao repositório.
3. Crie um banco PostgreSQL no Supabase.
4. No Streamlit Cloud, adicione as chaves do arquivo `.streamlit/secrets.toml.example` em `Settings > Secrets`.
5. Clique em `Create app`.
6. Selecione o repositório.
7. Defina `Main file path` como `app.py`.
8. Publique a aplicacao.

## Persistencia remota

- A aplicacao usa PostgreSQL externo como fonte de verdade.
- O arquivo `data/base.xlsx` passa a servir apenas para carga inicial quando o banco remoto estiver vazio.
- Uploads feitos pela sidebar sobrescrevem todo o conteudo persistido no banco remoto.
- Credenciais do banco sao lidas de variaveis de ambiente ou de `.streamlit/secrets.toml`.

## Estrutura recomendada no PostgreSQL

```sql
create table public.metadata (
	key text primary key,
	value text not null
);

create table public.sheet_registry (
	sheet_name text primary key,
	table_name text not null,
	row_count integer not null
);

create table public.sales (
	"Data" timestamp without time zone not null,
	"CodProduto" integer not null,
	"Produto" text not null,
	"QuantidadeTotal" double precision not null,
	"ValorTotal" double precision not null,
	"PesoUnitario" double precision not null,
	"PesoTotal" double precision not null,
	"TIPO" text not null
);
```

## Exemplos adaptados

INSERT com upsert de metadata:

```sql
insert into public.metadata (key, value)
values ('source_name', 'base.xlsx')
on conflict (key) do update
set value = excluded.value;
```

SELECT de preview de aba importada:

```sql
select *
from public.sales
limit 200;
```

## Observacoes

- O modulo `utils/db.py` concentra a conexao SQLAlchemy com Supabase/PostgreSQL.
- O modulo `utils/load_data.py` continua sendo a API de dados consumida pelas paginas.
- A aplicacao agora exige login antes de liberar a sidebar e a navegacao multipagina.
