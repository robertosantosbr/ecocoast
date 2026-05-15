# EcoCoast - Streamlit + PostgreSQL + OpenStreetMap

## Estrutura

```text
ecocoast_streamlit_app/
├── app.py
├── requirements.txt
├── images/
│   └── residuos/
└── .streamlit/
    └── secrets.toml.example
```

As imagens usadas nas colunas `imagem_residuo` e `imagem_residuo_box` devem ficar em:

```text
images/residuos/
```

Exemplo:

```text
images/residuos/550e8400-e29b-41d4-a716-446655440000.jpg
images/residuos/550e8400-e29b-41d4-a716-446655440000_box.jpg
```

## Rodar localmente

```bash
pip install -r requirements.txt
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

Edite `.streamlit/secrets.toml` com os dados reais do banco.

## Publicar no Streamlit Community Cloud

1. Crie um repositório no GitHub e envie estes arquivos.
2. Não envie `.streamlit/secrets.toml` para o GitHub.
3. No Streamlit Cloud, crie um novo app apontando para `app.py`.
4. Em **Settings > Secrets**, adicione:

```toml
DB_HOST = "dpg-d83it3pkh4rs73alm290-a.oregon-postgres.render.com"
DB_PORT = "5432"
DB_NAME = "ecocoast"
DB_USER = "usr_admin"
DB_PASSWORD = "SUA_SENHA"
DB_SSLMODE = "require"
```

5. Faça o deploy.
