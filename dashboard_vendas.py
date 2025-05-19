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

# App
app = dash.Dash(__name__)
app.title = "Dashboard de Vendas"

# Layout
app.layout = html.Div([
    html.H1("Dashboard de Vendas", style={"textAlign": "center", "color": "darkblue"}),

    # Filtros dinâmicos globais
    html.Div([
        html.Label("Produto:"),
        dcc.Dropdown(id="filtro-produto", options=[{"label": p, "value": p} for p in sorted(vendas["Produto"].dropna().unique())], placeholder="Selecione o produto"),

        html.Label("Loja:"),
        dcc.Dropdown(id="filtro-loja", options=[{"label": l, "value": l} for l in sorted(vendas["Nome da Loja"].dropna().unique())], placeholder="Selecione a loja"),

        html.Label("Cliente:"),
        dcc.Dropdown(id="filtro-cliente", options=[{"label": c, "value": c} for c in sorted(vendas["Nome Cliente"].dropna().unique())], placeholder="Selecione o cliente"),

        html.Label("Marca:"),
        dcc.Dropdown(id="filtro-marca", options=[{"label": m, "value": m} for m in sorted(vendas["Marca"].dropna().unique())], placeholder="Selecione a marca"),

        html.Label("Tipo do Produto:"),
        dcc.Dropdown(id="filtro-tipo", options=[{"label": t, "value": t} for t in sorted(vendas["Tipo do Produto"].dropna().unique())], placeholder="Selecione o tipo")
    ], style={"width": "60%", "margin": "auto"}),

    # Gráficos
    dcc.Graph(id="grafico-vendas-ano"),
    dcc.Graph(id="grafico-top-clientes"),
    dcc.Graph(id="grafico-top-produtos"),
    dcc.Graph(id="grafico-vendas-loja"),
    dcc.Graph(id="grafico-distribuicao-marca"),
    dcc.Graph(id="grafico-area-tipo")
])

# Função de filtro

def aplicar_filtros(df, produto, loja, cliente, marca, tipo):
    if produto:
        df = df[df["Produto"] == produto]
    if loja:
        df = df[df["Nome da Loja"] == loja]
    if cliente:
        df = df[df["Nome Cliente"] == cliente]
    if marca:
        df = df[df["Marca"] == marca]
    if tipo:
        df = df[df["Tipo do Produto"] == tipo]
    return df

# Callback genérico para cada gráfico

def registrar_callback_grafico(id_grafico, func_plot):
    @app.callback(
        Output(id_grafico, "figure"),
        Input("filtro-produto", "value"),
        Input("filtro-loja", "value"),
        Input("filtro-cliente", "value"),
        Input("filtro-marca", "value"),
        Input("filtro-tipo", "value")
    )
    def atualizar_grafico(produto, loja, cliente, marca, tipo):
        df_filtrado = aplicar_filtros(vendas.copy(), produto, loja, cliente, marca, tipo)
        if df_filtrado.empty:
            return px.bar(title="Sem dados para os filtros selecionados")
        return func_plot(df_filtrado)

# Gráficos
registrar_callback_grafico("grafico-vendas-ano", lambda df: px.histogram(df, x=df["Ano"].astype(str), y="Qtd Vendida", histfunc="sum", title="Vendas por Ano"))

registrar_callback_grafico("grafico-top-clientes", lambda df: px.bar(df.groupby("Nome Cliente")["Qtd Vendida"].sum().nlargest(10).reset_index(),
                                                                      x="Nome Cliente", y="Qtd Vendida", title="Top 10 Clientes"))

registrar_callback_grafico("grafico-top-produtos", lambda df: px.bar(df.groupby("Produto")["Qtd Vendida"].sum().nlargest(10).reset_index(),
                                                                      x="Produto", y="Qtd Vendida", title="Top 10 Produtos"))

registrar_callback_grafico("grafico-vendas-loja", lambda df: px.bar(df.groupby("Nome da Loja")["Qtd Vendida"].sum().reset_index(),
                                                                     x="Qtd Vendida", y="Nome da Loja", orientation="h", title="Vendas por Loja"))

registrar_callback_grafico("grafico-distribuicao-marca", lambda df: px.pie(df, names="Marca", values="Qtd Vendida", title="Distribuição por Marca"))

registrar_callback_grafico("grafico-area-tipo", lambda df: px.area(df.groupby("Tipo do Produto")["Qtd Vendida"].sum().reset_index(),
                                                                    x="Tipo do Produto", y="Qtd Vendida", title="Área por Tipo de Produto"))

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
