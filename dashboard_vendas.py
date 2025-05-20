import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import requests
from io import BytesIO

# Cores personalizadas
colors = {
    'background': '#f4f4f4',
    'text': '#333333',
    'accent': '#007bff'
}

# Estilo geral da aplicação
app_style = {
    'backgroundColor': colors['background'],
    'padding': '20px',
    'fontFamily': 'Arial, sans-serif',
    'color': colors['text']
}

title_style = {
    'textAlign': 'center',
    'color': colors['accent'],
    'marginBottom': '30px'
}

graph_title_style = {
    'color': colors['text']
}

filter_style = {
    'width': '80%',
    'margin': '20px auto',
    'padding': '15px',
    'border': f'1px solid {colors["accent"]}',
    'borderRadius': '5px',
    'backgroundColor': 'white'
}

dropdown_style = {
    'width': '100%',
    'marginBottom': '10px'
}

graph_style = {
    'backgroundColor': 'white',
    'padding': '15px',
    'borderRadius': '5px',
    'marginBottom': '20px'
}


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

# Função para gerar filtros específicos
def gerar_filtros(id_prefixo, colunas):
    filtros = []
    for col in colunas:
        options = sorted(vendas[col].dropna().unique())
        if options:
            filtros.append(
                dcc.Dropdown(
                    id=f"{id_prefixo}-{col.lower().replace(' ', '-')}",
                    options=[{"label": i, "value": i} for i in options],
                    placeholder=col,
                    style=dropdown_style
                )
            )
    return html.Div(filtros, style=filter_style)

# Layout
app.layout = html.Div(style=app_style, children=[
    html.H1("Dashboard de Vendas", style=title_style),

    html.Div([
        html.H3("Vendas por Ano", style=graph_title_style),
        gerar_filtros("ano", ["Produto", "Nome da Loja", "Nome Cliente", "Marca", "Tipo do Produto"]),
        dcc.Graph(id="grafico-ano", style=graph_style),
    ]),

    html.Div([
        html.H3("Top 10 Clientes", style=graph_title_style),
        gerar_filtros("clientes", ["Produto", "Nome da Loja", "Marca", "Tipo do Produto"]),
        dcc.Graph(id="grafico-clientes", style=graph_style),
    ]),

    html.Div([
        html.H3("Top 10 Produtos", style=graph_title_style),
        gerar_filtros("produtos", ["Nome da Loja", "Nome Cliente", "Marca", "Tipo do Produto"]),
        dcc.Graph(id="grafico-produtos", style=graph_style),
    ]),

    html.Div([
        html.H3("Vendas por Loja", style=graph_title_style),
        gerar_filtros("lojas", ["Produto", "Nome Cliente", "Marca", "Tipo do Produto"]),
        dcc.Graph(id="grafico-lojas", style=graph_style),
    ]),

    html.Div([
        html.H3("Distribuição por Marca", style=graph_title_style),
        gerar_filtros("marcas", ["Produto", "Nome da Loja", "Nome Cliente", "Tipo do Produto"]),
        dcc.Graph(id="grafico-marcas", style=graph_style),
    ]),

    html.Div([
        html.H3("Área por Tipo de Produto", style=graph_title_style),
        gerar_filtros("tipo", ["Produto", "Nome da Loja", "Nome Cliente", "Marca"]),
        dcc.Graph(id="grafico-tipo", style=graph_style)
    ])
])

# Callback genérico para atualizar gráficos com filtros
def registrar_callback(id_prefixo, grafico_id, func_plot, colunas_filtro):
    inputs = [Input(f"{id_prefixo}-{col.lower().replace(' ', '-')}", "value") for col in colunas_filtro]

    @app.callback(
        Output(grafico_id, "figure"),
        *inputs
    )
    def atualizar(*args):
        df = vendas.copy()
        for i, col in enumerate(colunas_filtro):
            if args[i]:
                df = df[df[col] == args[i]]
        return func_plot(df)

registrar_callback("ano", "grafico-ano", lambda df: px.histogram(df, x="Ano", y="Qtd Vendida", histfunc="sum", title="Vendas por Ano", color_discrete_sequence=[colors['accent']]), ["Produto", "Nome da Loja", "Nome Cliente", "Marca", "Tipo do Produto"])
registrar_callback("clientes", "grafico-clientes", lambda df: px.bar(df.groupby("Nome Cliente")["Qtd Vendida"].sum().nlargest(10).reset_index(), x="Nome Cliente", y="Qtd Vendida", title="Top 10 Clientes", color_discrete_sequence=[colors['accent']]), ["Produto", "Nome da Loja", "Marca", "Tipo do Produto"])
registrar_callback("produtos", "grafico-produtos", lambda df: px.bar(df.groupby("Produto")["Qtd Vendida"].sum().nlargest(10).reset_index(), x="Produto", y="Qtd Vendida", title="Top 10 Produtos", color_discrete_sequence=[colors['accent']]), ["Nome da Loja", "Nome Cliente", "Marca", "Tipo do Produto"])
registrar_callback("lojas", "grafico-lojas", lambda df: px.bar(df.groupby("Nome da Loja")["Qtd Vendida"].sum().reset_index(), x="Qtd Vendida", y="Nome da Loja", orientation="h", title="Vendas por Loja", color_discrete_sequence=[colors['accent']]), ["Produto", "Nome Cliente", "Marca", "Tipo do Produto"])
registrar_callback("marcas", "grafico-marcas", lambda df: px.pie(df, names="Marca", values="Qtd Vendida", title="Distribuição por Marca", color_discrete_sequence=px.colors.qualitative.Pastel), ["Produto", "Nome da Loja", "Nome Cliente", "Tipo do Produto"])
registrar_callback("tipo", "grafico-tipo", lambda df: px.area(df.groupby("Tipo do Produto")["Qtd Vendida"].sum().reset_index(), x="Tipo do Produto", y="Qtd Vendida", title="Área por Tipo de Produto", color_discrete_sequence=[colors['accent']]), ["Produto", "Nome da Loja", "Nome Cliente", "Marca"])


server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
