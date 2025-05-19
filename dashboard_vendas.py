import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output

vendas_df = pd.read_excel("https://raw.githubusercontent.com/07leonam/dash/main/base_vendas.xlsx", engine='openpyxl')
clientes_raw = pd.read_excel("https://raw.githubusercontent.com/07leonam/dash/main/cadastro_clientes.xlsx", engine='openpyxl')
lojas_df = pd.read_excel("https://raw.githubusercontent.com/07leonam/dash/main/cadastro_lojas.xlsx", engine='openpyxl')
produtos_df = pd.read_excel("https://raw.githubusercontent.com/07leonam/dash/main/cadastro_produtos.xlsx", engine='openpyxl')

# Ajustar clientes (cabeçalho está na linha 2)
clientes_df = clientes_raw.iloc[2:].rename(columns={
    "Unnamed: 0": "ID Cliente",
    "Unnamed: 1": "Primeiro Nome",
    "Unnamed: 2": "Sobrenome"
})
clientes_df = clientes_df[["ID Cliente", "Primeiro Nome", "Sobrenome"]]

# Ajustar vendas
vendas_df["Ano"] = pd.DatetimeIndex(vendas_df["Data da Venda"]).year

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

    # Filtros dinâmicos
    html.Div([
        html.Label("Tipo do Produto:"),
        dcc.Dropdown(id="tipo-produto-dropdown",
                     options=[{"label": tp, "value": tp} for tp in sorted(vendas["Tipo do Produto"].dropna().unique())],
                     placeholder="Selecione o tipo"),

        html.Label("Marca:"),
        dcc.Dropdown(id="marca-dropdown", placeholder="Selecione a marca")
    ], style={"width": "40%", "margin": "auto"}),

    # Gráfico com filtros
    dcc.Graph(id="grafico-filtrado"),

    # Outros gráficos
    dcc.Graph(figure=px.histogram(vendas, x="Ano", y="Qtd Vendida", histfunc="sum", title="Vendas por Ano")),

    dcc.Graph(figure=px.bar(vendas.groupby("Nome Cliente")["Qtd Vendida"].sum().nlargest(10).reset_index(),
                             x="Nome Cliente", y="Qtd Vendida", title="Top 10 Clientes")),

    dcc.Graph(figure=px.bar(vendas.groupby("Produto")["Qtd Vendida"].sum().nlargest(10).reset_index(),
                             x="Produto", y="Qtd Vendida", title="Top 10 Produtos")),

    dcc.Graph(figure=px.bar(vendas.groupby("Nome da Loja")["Qtd Vendida"].sum().reset_index(),
                             x="Qtd Vendida", y="Nome da Loja", orientation="h", title="Vendas por Loja")),

    dcc.Graph(figure=px.pie(vendas, names="Marca", values="Qtd Vendida", title="Distribuição por Marca")),

    dcc.Graph(figure=px.area(vendas.groupby("Tipo do Produto")["Qtd Vendida"].sum().reset_index(),
                              x="Tipo do Produto", y="Qtd Vendida", title="Área por Tipo de Produto"))
])

# Callback: atualizar marcas com base no tipo selecionado
@app.callback(
    Output("marca-dropdown", "options"),
    Input("tipo-produto-dropdown", "value")
)
def atualizar_marcas(tipo):
    if tipo is None:
        return []
    marcas = vendas[vendas["Tipo do Produto"] == tipo]["Marca"].dropna().unique()
    return [{"label": m, "value": m} for m in sorted(marcas)]

# Callback: atualizar gráfico com base nos filtros
@app.callback(
    Output("grafico-filtrado", "figure"),
    Input("tipo-produto-dropdown", "value"),
    Input("marca-dropdown", "value")
)
def atualizar_grafico(tipo, marca):
    df = vendas.copy()
    if tipo:
        df = df[df["Tipo do Produto"] == tipo]
    if marca:
        df = df[df["Marca"] == marca]

    if df.empty:
        return px.bar(title="Sem dados para os filtros selecionados")

    return px.line(df.groupby("Produto")["Qtd Vendida"].sum().reset_index(),
                   x="Produto", y="Qtd Vendida", title=f"Vendas por Produto ({tipo or ''} - {marca or ''})")

if __name__ == "__main__":
    app.run_server(debug=True)
