import pandas as pd
import streamlit as st
import plotly.express as px

# Carregar CSV
df = pd.read_csv('Base_de_Vendas_Simulada.csv', parse_dates=['Data'])
df['Mês'] = df['Data'].dt.to_period('M').astype(str)

# Estilo customizado com paleta (250505 → 481212 → EF4E4E)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;500;700&display=swap');
            
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        background-color: #1a1a1a;
        color: #f5f5f5;
    }

    .stApp {
        background-color: #1a1a1a;
    }

    section.main > div {
        background-color: #1a1a1a;
        color: #f5f5f5;
    }

    .stMetric {
        background-color: #25050522;
        border-left: 5px solid #EF4E4E;
        padding: 10px;
        border-radius: 10px;
    }

    h1, h2, h3, h4, h5 {
        color: #EF4E4E;
    }

    .stTextInput > div > div > input,
    .stSelectbox > div > div > div > div,
    .stDateInput > div > div > input {
        background-color: #250505 !important;
        color: #f5f5f5 !important;
    }

    .stMultiSelect > div > div {
        background-color: #250505 !important;
        color: #f5f5f5 !important;
    }

    .stButton > button {
        background-color: #EF4E4E;
        color: white;
        border-radius: 5px;
    }

    .stDataFrame {
        background-color: #1a1a1a !important;
        color: #f5f5f5 !important;
    }
    </style>
""", unsafe_allow_html=True)


st.title("💪 Dashboard de Vendas - Suplementos")

# Filtros
produtos = df['Produto'].unique()
metodos = df['Método de Pagamento'].unique()

with st.sidebar:
    st.header("🎛️ Filtros")
    produto_sel = st.multiselect("Produto", produtos, default=list(produtos))
    metodo_sel = st.multiselect("Método de Pagamento", metodos, default=list(metodos))
    data_sel = st.date_input("Período", [df['Data'].min(), df['Data'].max()])

# Aplicar filtro
df_filtrado = df[
    (df['Produto'].isin(produto_sel)) &
    (df['Método de Pagamento'].isin(metodo_sel)) &
    (df['Data'] >= pd.to_datetime(data_sel[0])) &
    (df['Data'] <= pd.to_datetime(data_sel[1]))
]

# KPIs com comparação entre último e penúltimo mês
st.subheader("📊 Indicadores de Desempenho (Mês Atual vs Mês Anterior)")

# Extrair os dois últimos meses disponíveis no filtro
meses_ordenados = sorted(df_filtrado['Mês'].unique())
if len(meses_ordenados) < 2:
    st.warning("É necessário ter pelo menos dois meses de dados para mostrar o delta.")
else:
    mes_atual = meses_ordenados[-1]
    mes_anterior = meses_ordenados[-2]

    df_mes_atual = df_filtrado[df_filtrado['Mês'] == mes_atual]
    df_mes_anterior = df_filtrado[df_filtrado['Mês'] == mes_anterior]

    # KPIs
    receita_atual = df_mes_atual['Valor Total'].sum()
    receita_anterior = df_mes_anterior['Valor Total'].sum()
    delta_receita = receita_atual - receita_anterior

    vendas_atual = len(df_mes_atual)
    vendas_anterior = len(df_mes_anterior)
    delta_vendas = vendas_atual - vendas_anterior

    ticket_medio_atual = receita_atual / vendas_atual if vendas_atual > 0 else 0
    ticket_medio_anterior = receita_anterior / vendas_anterior if vendas_anterior > 0 else 0
    delta_ticket = ticket_medio_atual - ticket_medio_anterior

    # Mostrar métricas com delta
    col1, col2, col3 = st.columns(3)
    col1.metric("Receita", f"R$ {receita_atual:,.2f}", delta=f"R$ {delta_receita:,.2f}")
    col2.metric("Vendas", f"{vendas_atual} transações", delta=f"{delta_vendas:+}")
    col3.metric("Ticket Médio", f"R$ {ticket_medio_atual:,.2f}", delta=f"R$ {delta_ticket:+.2f}")

# Gasto mensal fixo simulado
gasto_padrao_mensal = 500
gastos_mensais = pd.DataFrame(df["Mês"].unique(), columns=["Mês"])
gastos_mensais["Gasto Operacional"] = gasto_padrao_mensal

# Receita por mês
receita_mensal = df_filtrado.groupby("Mês").agg({"Valor Total": "sum"}).reset_index()
receita_mensal = receita_mensal.merge(gastos_mensais, on="Mês", how="left")
receita_mensal["Lucro Líquido"] = receita_mensal["Valor Total"] - receita_mensal["Gasto Operacional"]
receita_mensal["Margem Líquida (%)"] = (receita_mensal["Lucro Líquido"] / receita_mensal["Valor Total"]) * 100

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Receita Total", f"R$ {receita_mensal['Valor Total'].sum():,.2f}")
col2.metric("Lucro Líquido", f"R$ {receita_mensal['Lucro Líquido'].sum():,.2f}")
col3.metric("Margem Líquida Média", f"{receita_mensal['Margem Líquida (%)'].mean():.1f}%")

# Gráfico comparativo
fig_financas = px.line(
    receita_mensal,
    x="Mês",
    y=["Valor Total", "Gasto Operacional", "Lucro Líquido"],
    markers=True,
    title="📈 Receita, Gastos e Lucro Líquido por Mês",
    labels={"value": "Valor (R$)", "variable": "Indicador"},
    color_discrete_sequence=["#EF4E4E", "#481212", "#5cb85c"]
)
st.plotly_chart(fig_financas, use_container_width=True)

# Margem líquida
fig_margem = px.line(
    receita_mensal,
    x="Mês",
    y="Margem Líquida (%)",
    title="📈 Margem Líquida por Mês",
    markers=True,
    color_discrete_sequence=["#EF4E4E"]
)
st.plotly_chart(fig_margem, use_container_width=True)

# Método de pagamento
st.subheader("💳 Participação por Método de Pagamento")
pagamento = df_filtrado.groupby('Método de Pagamento').sum(numeric_only=True).reset_index()
fig2 = px.pie(pagamento, values='Valor Total', names='Método de Pagamento',
              title="Distribuição por Método de Pagamento", color_discrete_sequence=["#250505", "#481212", "#EF4E4E"])
st.plotly_chart(fig2, use_container_width=True)

# Vendas por estado
st.subheader("🗺️ Receita por Estado")
estado = df_filtrado.groupby('Estado').sum(numeric_only=True).reset_index()
fig3 = px.bar(estado, x='Estado', y='Valor Total', title="Receita por Estado", color='Estado',
              color_discrete_sequence=px.colors.sequential.Reds)
st.plotly_chart(fig3, use_container_width=True)

# Agrupar a quantidade vendida por produto e mês
df_qtd_mensal = df_filtrado.groupby(["Mês", "Produto"]).agg({"Quantidade": "sum"}).reset_index()

# Gráfico de linha por produto
fig_qtd = px.line(
    df_qtd_mensal,
    x="Mês",
    y="Quantidade",
    color="Produto",
    markers=True,
    title="📦 Quantidade Vendida por Produto por Mês",
    color_discrete_sequence=px.colors.sequential.Reds
)

fig_qtd.update_layout(xaxis_title="Mês", yaxis_title="Quantidade Vendida")

# Mostrar no Streamlit
st.subheader("📦 Evolução Mensal de Vendas por Produto")
st.plotly_chart(fig_qtd, use_container_width=True)

# Receita por produto
st.subheader("🧃 Receita por Produto")
produto_vendas = df_filtrado.groupby('Produto').sum(numeric_only=True).reset_index()
fig4 = px.bar(produto_vendas, x='Produto', y='Valor Total', color='Produto', title="Receita por Produto",
              color_discrete_sequence=px.colors.sequential.Reds)
st.plotly_chart(fig4, use_container_width=True)

# Tabela de dados
st.subheader("📋 Base de Dados")
st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True)
