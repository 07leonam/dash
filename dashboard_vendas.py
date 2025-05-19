
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html

# Carregar os dados
vendas_df = pd.read_excel("base vendas unificada.xlsx")
clientes_df = pd.read_excel("Cadastro Clientes.xlsx")
lojas_df = pd.read_excel("Cadastro Lojas.xlsx")
produtos_df = pd.read_excel("Cadastro Produtos.xlsx")

# Preprocessamento
vendas_df["Ano"] = pd.DatetimeIndex(vendas_df["Data da Venda"]).year

# Padronização dos dados de clientes
clientes_df = clientes_df.iloc[2:].rename(columns={
    "Unnamed: 0": "ID Cliente",
    "Unnamed: 1": "Primeiro Nome",
    "Unnamed: 2": "Sobrenome"
})[["ID Cliente", "Primeiro Nome", "Sobrenome"]]

# Unir dados
vendas_completa = vendas_df.merge(produtos_df, on="SKU", how="left") \
                           .merge(clientes_df, on="ID Cliente", how="left") \
                           .merge(lojas_df[["ID Loja", "Nome da Loja"]], on="ID Loja", how="left")

vendas_completa["Nome Cliente"] = vendas_completa["Primeiro Nome"].fillna('') + " " + vendas_completa["Sobrenome"].fillna('')

# Gráficos
fig_ano = px.histogram(vendas_completa, x="Ano", y="Qtd Vendida", histfunc="sum", title="Vendas por Ano")

fig_cliente = px.bar(vendas_completa.groupby("Nome Cliente")["Qtd Vendida"].sum().nlargest(10).reset_index(),
                     x="Nome Cliente", y="Qtd Vendida", title="Top 10 Clientes por Quantidade Vendida")

fig_produto = px.bar(vendas_completa.groupby("Produto")["Qtd Vendida"].sum().nlargest(10).reset_index(),
                     x="Produto", y="Qtd Vendida", title="Top 10 Produtos por Quantidade Vendida")

fig_loja = px.bar(vendas_completa.groupby("Nome da Loja")["Qtd Vendida"].sum().reset_index(),
                  x="Nome da Loja", y="Qtd Vendida", title="Vendas por Loja")

fig_marca = px.pie(vendas_completa, names="Marca", values="Qtd Vendida", title="Distribuição de Vendas por Marca")

fig_tipo = px.bar(vendas_completa.groupby("Tipo do Produto")["Qtd Vendida"].sum().reset_index(),
                  x="Tipo do Produto", y="Qtd Vendida", title="Vendas por Tipo de Produto")

# Aplicativo Dash
app = dash.Dash(__name__)
app.title = "Dashboard Vendas"

app.layout = html.Div([
    html.H1("Dashboard de Vendas", style={"textAlign": "center", "color": "darkblue"}),

    dcc.Graph(figure=fig_ano),
    dcc.Graph(figure=fig_cliente),
    dcc.Graph(figure=fig_produto),
    dcc.Graph(figure=fig_loja),
    dcc.Graph(figure=fig_marca),
    dcc.Graph(figure=fig_tipo)
])

if __name__ == "__main__":
    app.run(debug=True)
