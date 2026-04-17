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
- `dashboard.db`
- `data/dashboard.db`
- `Base_dashBoard 1  (1).xlsm`

## Deploy no Streamlit Community Cloud

1. Suba este projeto para um repositório GitHub.
2. Confirme que `data/base.xlsx` foi enviado ao repositório.
3. Acesse o Streamlit Community Cloud.
4. Clique em `Create app`.
5. Selecione o repositório.
6. Defina `Main file path` como `app.py`.
7. Em `Advanced settings`, mantenha Python padrao, a menos que queira fixar outra versao.
8. Publique a aplicacao.

## Observacoes

- O banco SQLite em `data/dashboard.db` e recriado localmente a partir da planilha quando necessario.
- A aplicacao agora exige login antes de liberar a sidebar e a navegacao multipagina.
