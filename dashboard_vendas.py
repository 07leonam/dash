import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import requests
from io import BytesIO


def read_excel_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return pd.read_excel(BytesIO(response.content), engine='openpyxl')

# Leitura dos arquivos
vendas_df = read_excel_url("https://raw.githubusercontent.com/07leonam/dash/main/base_vendas.xlsx")
clientes_raw = read_excel_url("https://raw.githubusercontent.com/07leonam/dash/main/cadastro_clientes.xlsx")
lojas_df = read_excel_url("https://raw.githubusercontent.com/07leonam/dash/main/cadastro_lojas.xlsx")
produtos_df = read_excel_url("https://raw.githubusercontent.com/07leonam/dash/main/cadastro_produtos.xlsx")

# Ajustar clientes
clientes_df = clientes_raw.iloc[2:].rename(columns={
    "Unnamed: 0": "ID Cliente",
    "Unnamed: 1": "Primeiro Nome",
    "Unnamed: 2": "Sobrenome"
})
clientes_df = clientes_df[["ID Cliente", "Primeiro Nome", "Sobrenome"]]

# Ajustar vendas
vendas_df["Ano"] = pd.DatetimeIndex(vendas_df["Data da Venda"]).year.astype(int)

# Unir dados
vendas = vendas_df.merge(produtos_df, on="SKU", how="left") \
                    .merge(clientes_df, on="ID Cliente", how="left") \
                    .merge(lojas_df[["ID Loja", "Nome da Loja"]], on="ID Loja", how="left")

vendas["Nome Cliente"] = vendas["Primeiro Nome"].fillna('') + " " + vendas["Sobrenome"].fillna('')

app = dash.Dash(__name__)
app.title = "Dashboard de Vendas"

# Função para gerar filtros
def gerar_filtros(id_prefixo):
    return html.Div([
        dcc.Dropdown(
            id=f"{id_prefixo}-produto",
            options=[{"label": i, "value": i} for i in sorted(vendas["Produto"].dropna().unique())],
            placeholder="Produto"
        ),
        dcc.Dropdown(
            id=f"{id_prefixo}-loja",
            options=[{"label": i, "value": i} for i in sorted(vendas["Nome da Loja"].dropna().unique())],
            placeholder="Loja"
        ),
        dcc.Dropdown(
            id=f"{id_prefixo}-cliente",
            options=[{"label": i, "value": i} for i in sorted(vendas["Nome Cliente"].dropna().unique())],
            placeholder="Cliente"
        ),
        dcc.Dropdown(
            id=f"{id_prefixo}-marca",
            options=[{"label": i, "value": i} for i in sorted(vendas["Marca"].dropna().unique())],
            placeholder="Marca"
        ),
        dcc.Dropdown(
            id=f"{id_prefixo}-tipo",
            options=[{"label": i, "value": i} for i in sorted(vendas["Tipo do Produto"].dropna().unique())],
            placeholder="Tipo do Produto"
        )
    ], style={"width": "40%", "margin": "auto"})

# Layout
app.layout = html.Div([
    html.H1("Dashboard de Vendas", style={"textAlign": "center", "color": "darkblue"}),

    html.H3("Vendas por Ano"),
    gerar_filtros("ano"),
    dcc.Graph(id="grafico-ano"),

    html.H3("Top 10 Clientes"),
    gerar_filtros("clientes"),
    dcc.Graph(id="grafico-clientes"),

    html.H3("Top 10 Produtos"),
    gerar_filtros("produtos"),
    dcc.Graph(id="grafico-produtos"),

    html.H3("Vendas por Loja"),
    gerar_filtros("lojas"),
    dcc.Graph(id="grafico-lojas"),

    html.H3("Distribuição por Marca"),
    gerar_filtros("marcas"),
    dcc.Graph(id="grafico-marcas"),

    html.H3("Área por Tipo de Produto"),
    gerar_filtros("tipo"),
    dcc.Graph(id="grafico-tipo")
])

# Callback genérico para atualizar gráficos com filtros

def registrar_callback(id_prefixo, grafico_id, func_plot):
    @app.callback(
        Output(grafico_id, "figure"),
        Input(f"{id_prefixo}-produto", "value"),
        Input(f"{id_prefixo}-loja", "value"),
        Input(f"{id_prefixo}-cliente", "value"),
        Input(f"{id_prefixo}-marca", "value"),
        Input(f"{id_prefixo}-tipo", "value")
    )
    def atualizar(produto, loja, cliente, marca, tipo):
        df = vendas.copy()
        if produto: df = df[df["Produto"] == produto]
        if loja: df = df[df["Nome da Loja"] == loja]
        if cliente: df = df[df["Nome Cliente"] == cliente]
        if marca: df = df[df["Marca"] == marca]
        if tipo: df = df[df["Tipo do Produto"] == tipo]
        return func_plot(df)

registrar_callback("ano", "grafico-ano", lambda df: px.histogram(df, x="Ano", y="Qtd Vendida", histfunc="sum", title="Vendas por Ano"))
registrar_callback("clientes", "grafico-clientes", lambda df: px.bar(df.groupby("Nome Cliente")["Qtd Vendida"].sum().nlargest(10).reset_index(), x="Nome Cliente", y="Qtd Vendida", title="Top 10 Clientes"))
registrar_callback("produtos", "grafico-produtos", lambda df: px.bar(df.groupby("Produto")["Qtd Vendida"].sum().nlargest(10).reset_index(), x="Produto", y="Qtd Vendida", title="Top 10 Produtos"))
registrar_callback("lojas", "grafico-lojas", lambda df: px.bar(df.groupby("Nome da Loja")["Qtd Vendida"].sum().reset_index(), x="Qtd Vendida", y="Nome da Loja", orientation="h", title="Vendas por Loja"))
registrar_callback("marcas", "grafico-marcas", lambda df: px.pie(df, names="Marca", values="Qtd Vendida", title="Distribuição por Marca"))
registrar_callback("tipo", "grafico-tipo", lambda df: px.area(df.groupby("Tipo do Produto")["Qtd Vendida"].sum().reset_index(), x="Tipo do Produto", y="Qtd Vendida", title="Área por Tipo de Produto"))

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
