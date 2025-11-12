import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# =====================================================================
# 1. LEITURA E TRATAMENTO DOS DADOS
# =====================================================================
try:
    # Tenta ler o CSV com o encoding padrao
    df = pd.read_csv('data/dados.csv', sep=';')
except UnicodeDecodeError:
    # Se falhar, tenta com um encoding diferente, comum no Brasil
    df = pd.read_csv('data/dados.csv', sep=';', encoding='latin1')

# Converte as colunas de data para datetime, tratando erros
df['Recrutamento e Seleção'] = pd.to_datetime(df['Recrutamento e Seleção'], format='%d/%m/%Y', errors='coerce')

# Remove linhas onde a data de 'Recrutamento e Seleção' não pôde ser convertida
df.dropna(subset=['Recrutamento e Seleção'], inplace=True)

# Limpeza de dados: remove espaços em branco extras dos nomes das colunas
df.columns = df.columns.str.strip()

# Limpeza da coluna STATUS: preenche valores vazios e remove espaços
df['STATUS'] = df['STATUS'].str.strip().fillna('Não especificado')
df.loc[df['STATUS'] == '', 'STATUS'] = 'Não especificado'

# =====================================================================
# 2. INICIALIZACAO DO APP DASH
# =====================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server

# Opções para os filtros Dropdown, com todos os valores pré-selecionados
status_vaga_options = sorted(df['Status da Vaga'].unique())
status_interno_options = sorted(df['STATUS'].unique())

# =====================================================================
# 3. LAYOUT DO DASHBOARD
# =====================================================================
app.layout = dbc.Container([
    # --- Linha 1: Titulo ---
    dbc.Row([
        dbc.Col([
            html.H1('Dashboard de Análise de Vagas', className='text-primary mb-0'),
            html.P('Análise de desempenho do processo seletivo', className='text-muted')
        ], width=12)
    ], className='mb-4 mt-4'),

    # --- Linha 2: Filtros ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Filtros Gerais", className="card-title"),
                    dbc.Row([
                        # Filtro de Data
                        dbc.Col(
                            dcc.DatePickerRange(
                                id='filtro-data',
                                min_date_allowed=df['Recrutamento e Seleção'].min().date(),
                                max_date_allowed=df['Recrutamento e Seleção'].max().date(),
                                start_date=df['Recrutamento e Seleção'].min().date(),
                                end_date=df['Recrutamento e Seleção'].max().date(),
                                display_format='DD/MM/YYYY',
                                className='w-100'
                            ), width=4
                        ),
                        # Filtro de Grupo Economico
                        dbc.Col(
                            dcc.Dropdown(
                                id='filtro-grupo',
                                options=[{'label': g, 'value': g} for g in df['Grupo Econômico'].unique()],
                                value=None,
                                placeholder="Selecione o Grupo",
                                multi=True
                            ), width=4
                        ),
                        # Filtro de UF
                        dbc.Col(
                            dcc.Dropdown(
                                id='filtro-uf',
                                options=[{'label': u, 'value': u} for u in df['UF da OI'].unique()],
                                value=None,
                                placeholder="Selecione a UF",
                                multi=True
                            ), width=4
                        )
                    ])
                ])
            ], className='mb-4')
        ])
    ]),

    # --- Abas ---
    dcc.Tabs(id="tabs-principal", value='tab-status-vaga', children=[
        # --- Aba 1: Análise por Status da Vaga (Original) ---
        dcc.Tab(label='Análise por Status da Vaga', value='tab-status-vaga', children=[
            dbc.Card(dbc.CardBody([
                # Filtro Específico da Aba (Estilo Excel)
                dbc.Button("Filtrar por Status da Vaga...", id="filtro-status-btn", className="mb-2 w-100"),
                dbc.Collapse(
                    dbc.Card(dbc.CardBody([
                        dbc.Row([
                            dbc.Col(dbc.Button("Marcar Todos", id="filtro-status-select-all", size="sm", color="primary", outline=True), width="auto"),
                            dbc.Col(dbc.Button("Limpar Todos", id="filtro-status-clear-all", size="sm", color="secondary", outline=True), width="auto"),
                        ], className="mb-2"),
                        dcc.Checklist(
                            id='filtro-status',
                            options=[{'label': s, 'value': s} for s in status_vaga_options],
                            value=status_vaga_options,
                            labelStyle={'display': 'block', 'margin-bottom': '5px'},
                            style={'height': '200px', 'overflow-y': 'auto', 'border': '1px solid #ddd', 'padding': '10px', 'border-radius': '5px'}
                        ),
                    ])),
                    id="filtro-status-collapse",
                    is_open=False
                ),

                # KPIs
                dbc.Row([
                    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-total-vagas')), width=3),
                    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-dias-aberto')), width=3),
                    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-fora-sla')), width=3),
                    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-taxa-fora-sla')), width=3)
                ], className='mb-4 mt-3'),
                # Graficos
                dbc.Row([
                    dbc.Col(dcc.Graph(id='grafico-vagas-status'), width=8),
                    dbc.Col(dcc.Graph(id='grafico-vagas-motivo'), width=4)
                ]),
                # Grafico Top Vagas
                 dbc.Row([
                    dbc.Col([
                        html.Hr(),
                        dcc.Graph(id='grafico-top-vagas-aberto', style={'height': '600px'})
                    ], width=12)
                ], className='mt-4'),
            ]), className='mt-3')
        ]),

        # --- Aba 2: Análise por STATUS (Novo) ---
        dcc.Tab(label='Análise por Status Interno', value='tab-status-interno', children=[
            dbc.Card(dbc.CardBody([
                # Filtro Específico da Aba (Estilo Excel)
                dbc.Button("Filtrar por STATUS Interno...", id="filtro-status-interno-btn", className="mb-2 w-100"),
                dbc.Collapse(
                    dbc.Card(dbc.CardBody([
                        dbc.Row([
                            dbc.Col(dbc.Button("Marcar Todos", id="filtro-status-interno-select-all", size="sm", color="primary", outline=True), width="auto"),
                            dbc.Col(dbc.Button("Limpar Todos", id="filtro-status-interno-clear-all", size="sm", color="secondary", outline=True), width="auto"),
                        ], className="mb-2"),
                        dcc.Checklist(
                            id='filtro-status-interno',
                            options=[{'label': s, 'value': s} for s in status_interno_options],
                            value=status_interno_options,
                            labelStyle={'display': 'block', 'margin-bottom': '5px'},
                            style={'height': '200px', 'overflow-y': 'auto', 'border': '1px solid #ddd', 'padding': '10px', 'border-radius': '5px'}
                        ),
                    ])),
                    id="filtro-status-interno-collapse",
                    is_open=False
                ),

                # KPIs (com IDs diferentes)
                dbc.Row([
                    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-total-vagas-interno')), width=3),
                    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-dias-aberto-interno')), width=3),
                    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-fora-sla-interno')), width=3),
                    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-taxa-fora-sla-interno')), width=3)
                ], className='mb-4 mt-3'),
                # Graficos (com IDs diferentes)
                dbc.Row([
                    dbc.Col(dcc.Graph(id='grafico-vagas-status-interno'), width=8),
                    dbc.Col(dcc.Graph(id='grafico-vagas-motivo-interno'), width=4)
                ]),
                # Grafico Top Vagas (com ID diferente)
                 dbc.Row([
                    dbc.Col([
                        html.Hr(),
                        dcc.Graph(id='grafico-top-vagas-aberto-interno', style={'height': '600px'})
                    ], width=12)
                ], className='mt-4'),
            ]), className='mt-3')
        ]),
    ]),


    # --- Linha 6: Rodape ---
    dbc.Row([
        dbc.Col(html.Hr(), width=12),
        dbc.Col(html.P(f"Dados atualizados em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"), width=12, className='text-center text-muted')
    ])

], fluid=True)


# =====================================================================
# 4. CALLBACKS - A "INTELIGENCIA" DO DASHBOARD
# =====================================================================

# --- Callbacks para interatividade do Filtro 1 (Status da Vaga) ---
@app.callback(
    Output("filtro-status-collapse", "is_open"),
    [Input("filtro-status-btn", "n_clicks")],
    [State("filtro-status-collapse", "is_open")],
)
def toggle_collapse_status(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("filtro-status", "value"),
    [Input("filtro-status-select-all", "n_clicks"),
     Input("filtro-status-clear-all", "n_clicks")]
)
def manage_all_selection_status(select_all, clear_all):
    ctx = dash.callback_context
    if not ctx.triggered:
        return status_vaga_options
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == "filtro-status-select-all":
        return status_vaga_options
    if button_id == "filtro-status-clear-all":
        return []
    return status_vaga_options

# --- Callbacks para interatividade do Filtro 2 (STATUS Interno) ---
@app.callback(
    Output("filtro-status-interno-collapse", "is_open"),
    [Input("filtro-status-interno-btn", "n_clicks")],
    [State("filtro-status-interno-collapse", "is_open")],
)
def toggle_collapse_status_interno(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("filtro-status-interno", "value"),
    [Input("filtro-status-interno-select-all", "n_clicks"),
     Input("filtro-status-interno-clear-all", "n_clicks")]
)
def manage_all_selection_status_interno(select_all, clear_all):
    ctx = dash.callback_context
    if not ctx.triggered:
        return status_interno_options
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == "filtro-status-interno-select-all":
        return status_interno_options
    if button_id == "filtro-status-interno-clear-all":
        return []
    return status_interno_options


# --- Callback para a ABA 1: Status da Vaga (Original) ---
@app.callback(
    [
        Output('kpi-total-vagas', 'children'),
        Output('kpi-dias-aberto', 'children'),
        Output('kpi-fora-sla', 'children'),
        Output('kpi-taxa-fora-sla', 'children'),
        Output('grafico-vagas-status', 'figure'),
        Output('grafico-vagas-motivo', 'figure'),
        Output('grafico-top-vagas-aberto', 'figure')
    ],
    [
        Input('filtro-data', 'start_date'),
        Input('filtro-data', 'end_date'),
        Input('filtro-status', 'value'), # Filtro específico desta aba
        Input('filtro-grupo', 'value'),
        Input('filtro-uf', 'value')
    ]
)
def update_dashboard_status_vaga(start_date, end_date, selected_status, selected_grupos, selected_ufs):
    # --- 1. Filtragem dos Dados ---
    start_date_obj = date.fromisoformat(start_date)
    end_date_obj = date.fromisoformat(end_date)
    
    dff = df[(df['Recrutamento e Seleção'].dt.date >= start_date_obj) & (df['Recrutamento e Seleção'].dt.date <= end_date_obj)]
    
    if selected_status:
        dff = dff[dff['Status da Vaga'].isin(selected_status)]
    if selected_grupos:
        dff = dff[dff['Grupo Econômico'].isin(selected_grupos)]
    if selected_ufs:
        dff = dff[dff['UF da OI'].isin(selected_ufs)]

    # --- 2. Calculo dos KPIs ---
    if dff.empty or not selected_status:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            xaxis={"visible": False}, yaxis={"visible": False},
            annotations=[{"text": "Sem dados para os filtros selecionados", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 16}}]
        )
        kpi_vagas_html = [html.H6('Total de Vagas', className='card-subtitle'), html.H4('0', className='card-title')]
        kpi_dias_html = [html.H6('Média de Dias em Aberto', className='card-subtitle'), html.H4('N/A', className='card-title')]
        kpi_fora_sla_html = [html.H6('Vagas Fora do SLA', className='card-subtitle'), html.H4('0', className='card-title text-danger')]
        kpi_taxa_sla_html = [html.H6('Taxa Fora do SLA', className='card-subtitle'), html.H4('N/A', className='card-title')]
        return kpi_vagas_html, kpi_dias_html, kpi_fora_sla_html, kpi_taxa_sla_html, empty_fig, empty_fig, empty_fig

    # Total de Vagas
    total_vagas = len(dff)
    kpi_vagas_html = [
        html.H6('Total de Vagas', className='card-subtitle'),
        html.H4(f'{total_vagas}', className='card-title')
    ]

    # Média de Dias em Aberto
    media_dias_aberto = dff['Dias em Aberto'].mean()
    kpi_dias_html = [
        html.H6('Média de Dias em Aberto', className='card-subtitle'),
        html.H4(f'{media_dias_aberto:.1f} dias', className='card-title')
    ]

    # Vagas Fora do SLA
    vagas_fora_sla = dff[dff['Situação Vagas'] == 'Fora do SLA'].shape[0]
    kpi_fora_sla_html = [
        html.H6('Vagas Fora do SLA', className='card-subtitle'),
        html.H4(f'{vagas_fora_sla}', className='card-title text-danger')
    ]

    # Taxa de Vagas Fora do SLA
    if total_vagas > 0:
        taxa_fora_sla = (vagas_fora_sla / total_vagas) * 100
        kpi_taxa_sla_html = [
            html.H6('Taxa Fora do SLA', className='card-subtitle'),
            html.H4(f'{taxa_fora_sla:.2f}%', className='card-title text-danger')
        ]
    else:
        kpi_taxa_sla_html = [
            html.H6('Taxa Fora do SLA', className='card-subtitle'),
            html.H4('N/A', className='card-title')
        ]

    # --- 3. Criacao dos Graficos ---

    # Grafico de Vagas por Status (Barras)
    vagas_por_status = dff['Status da Vaga'].value_counts().reset_index()
    vagas_por_status.columns = ['Status da Vaga', 'Quantidade']
    fig_status = px.bar(
        vagas_por_status.sort_values(by='Quantidade', ascending=True),
        x='Quantidade',
        y='Status da Vaga',
        title='Quantidade de Vagas por Status',
        orientation='h',
        text='Quantidade'
    )
    fig_status.update_layout(yaxis_title=None, xaxis_title='Quantidade de Vagas')
    fig_status.update_traces(textposition='outside')

    # Grafico de Vagas por Motivo (Rosca)
    vagas_por_motivo = dff['Descrição do Motivo'].value_counts().reset_index()
    vagas_por_motivo.columns = ['Descrição do Motivo', 'Quantidade']
    fig_motivo = px.pie(
        vagas_por_motivo,
        names='Descrição do Motivo',
        values='Quantidade',
        title='Distribuição por Motivo',
        hole=.4
    )
    
    # Grafico de Top 15 Vagas com Mais Tempo em Aberto
    df_abertas = dff[dff['Status da Vaga'] != 'Finalizado - Vaga Preenchida']
    df_top_abertas = df_abertas.sort_values(by='Dias em Aberto', ascending=False).head(15)
    
    # Criando um rótulo mais informativo para o eixo Y
    df_top_abertas['Label'] = df_top_abertas['Código da Vaga'].astype(str) + " (" + df_top_abertas['Título do Cargo'] + ")"

    fig_top_vagas = px.bar(
        df_top_abertas.sort_values(by='Dias em Aberto', ascending=True),
        y='Label',
        x='Dias em Aberto',
        title='Top 15 Vagas com Mais Tempo em Aberto',
        text='Dias em Aberto',
        orientation='h'
    )
    fig_top_vagas.update_layout(
        height=600, # Define uma altura fixa para o gráfico
        yaxis_title=None,
        xaxis_title='Dias em Aberto',
        yaxis=dict(tickfont=dict(size=10)) # Diminui o tamanho da fonte para caber mais texto
    )
    fig_top_vagas.update_traces(textposition='outside')
    
    return kpi_vagas_html, kpi_dias_html, kpi_fora_sla_html, kpi_taxa_sla_html, fig_status, fig_motivo, fig_top_vagas


# --- Callback para a ABA 2: STATUS Interno (Nova) ---
@app.callback(
    [
        Output('kpi-total-vagas-interno', 'children'),
        Output('kpi-dias-aberto-interno', 'children'),
        Output('kpi-fora-sla-interno', 'children'),
        Output('kpi-taxa-fora-sla-interno', 'children'),
        Output('grafico-vagas-status-interno', 'figure'),
        Output('grafico-vagas-motivo-interno', 'figure'),
        Output('grafico-top-vagas-aberto-interno', 'figure')
    ],
    [
        Input('filtro-data', 'start_date'),
        Input('filtro-data', 'end_date'),
        Input('filtro-status-interno', 'value'), # Filtro específico desta aba
        Input('filtro-grupo', 'value'),
        Input('filtro-uf', 'value')
    ]
)
def update_dashboard_status_interno(start_date, end_date, selected_status, selected_grupos, selected_ufs):
    # --- 1. Filtragem dos Dados ---
    start_date_obj = date.fromisoformat(start_date)
    end_date_obj = date.fromisoformat(end_date)
    
    dff = df[(df['Recrutamento e Seleção'].dt.date >= start_date_obj) & (df['Recrutamento e Seleção'].dt.date <= end_date_obj)]
    
    if selected_status:
        dff = dff[dff['STATUS'].isin(selected_status)] # << MUDANÇA AQUI
    if selected_grupos:
        dff = dff[dff['Grupo Econômico'].isin(selected_grupos)]
    if selected_ufs:
        dff = dff[dff['UF da OI'].isin(selected_ufs)]

    # --- 2. Calculo dos KPIs (lógica idêntica, mas aplicada aos dados filtrados) ---
    if dff.empty or not selected_status:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            xaxis={"visible": False}, yaxis={"visible": False},
            annotations=[{"text": "Sem dados para os filtros selecionados", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 16}}]
        )
        kpi_vagas_html = [html.H6('Total de Vagas', className='card-subtitle'), html.H4('0', className='card-title')]
        kpi_dias_html = [html.H6('Média de Dias em Aberto', className='card-subtitle'), html.H4('N/A', className='card-title')]
        kpi_fora_sla_html = [html.H6('Vagas Fora do SLA', className='card-subtitle'), html.H4('0', className='card-title text-danger')]
        kpi_taxa_sla_html = [html.H6('Taxa Fora do SLA', className='card-subtitle'), html.H4('N/A', className='card-title')]
        return kpi_vagas_html, kpi_dias_html, kpi_fora_sla_html, kpi_taxa_sla_html, empty_fig, empty_fig, empty_fig

    total_vagas = len(dff)
    kpi_vagas_html = [
        html.H6('Total de Vagas', className='card-subtitle'),
        html.H4(f'{total_vagas}', className='card-title')
    ]

    media_dias_aberto = dff['Dias em Aberto'].mean()
    kpi_dias_html = [
        html.H6('Média de Dias em Aberto', className='card-subtitle'),
        html.H4(f'{media_dias_aberto:.1f} dias', className='card-title')
    ]

    vagas_fora_sla = dff[dff['Situação Vagas'] == 'Fora do SLA'].shape[0]
    kpi_fora_sla_html = [
        html.H6('Vagas Fora do SLA', className='card-subtitle'),
        html.H4(f'{vagas_fora_sla}', className='card-title text-danger')
    ]

    if total_vagas > 0:
        taxa_fora_sla = (vagas_fora_sla / total_vagas) * 100
        kpi_taxa_sla_html = [
            html.H6('Taxa Fora do SLA', className='card-subtitle'),
            html.H4(f'{taxa_fora_sla:.2f}%', className='card-title text-danger')
        ]
    else:
        kpi_taxa_sla_html = [
            html.H6('Taxa Fora do SLA', className='card-subtitle'),
            html.H4('N/A', className='card-title')
        ]

    # --- 3. Criacao dos Graficos ---

    # Grafico de Vagas por Status (Barras) - USANDO A COLUNA 'STATUS'
    vagas_por_status = dff['STATUS'].value_counts().reset_index() # << MUDANÇA AQUI
    vagas_por_status.columns = ['STATUS', 'Quantidade']
    fig_status = px.bar(
        vagas_por_status.sort_values(by='Quantidade', ascending=True),
        x='Quantidade',
        y='STATUS', # << MUDANÇA AQUI
        title='Quantidade de Vagas por STATUS Interno', # << MUDANÇA AQUI
        orientation='h',
        text='Quantidade'
    )
    fig_status.update_layout(yaxis_title=None, xaxis_title='Quantidade de Vagas')
    fig_status.update_traces(textposition='outside')

    # Grafico de Vagas por Motivo (Rosca) - Lógica idêntica
    vagas_por_motivo = dff['Descrição do Motivo'].value_counts().reset_index()
    vagas_por_motivo.columns = ['Descrição do Motivo', 'Quantidade']
    fig_motivo = px.pie(
        vagas_por_motivo,
        names='Descrição do Motivo',
        values='Quantidade',
        title='Distribuição por Motivo',
        hole=.4
    )
    
    # Grafico de Top 15 Vagas com Mais Tempo em Aberto - Lógica idêntica
    df_abertas = dff[dff['Status da Vaga'] != 'Finalizado - Vaga Preenchida']
    df_top_abertas = df_abertas.sort_values(by='Dias em Aberto', ascending=False).head(15)
    
    df_top_abertas['Label'] = df_top_abertas['Código da Vaga'].astype(str) + " [" + df_top_abertas['STATUS'] + "] (" + df_top_abertas['Título do Cargo'] + ")"

    fig_top_vagas = px.bar(
        df_top_abertas.sort_values(by='Dias em Aberto', ascending=True),
        y='Label',
        x='Dias em Aberto',
        title='Top 15 Vagas com Mais Tempo em Aberto',
        text='Dias em Aberto',
        orientation='h'
    )
    fig_top_vagas.update_layout(
        height=600,
        yaxis_title=None,
        xaxis_title='Dias em Aberto',
        yaxis=dict(tickfont=dict(size=10))
    )
    fig_top_vagas.update_traces(textposition='outside')
    
    return kpi_vagas_html, kpi_dias_html, kpi_fora_sla_html, kpi_taxa_sla_html, fig_status, fig_motivo, fig_top_vagas


# =====================================================================
# 5. EXECUCAO DO SERVIDOR
# =====================================================================
if __name__ == '__main__':
    # Em um ambiente de produção, o Gunicorn ou outro servidor WSGI
    # irá importar a variável 'server' e rodar a aplicação.
    # A linha abaixo é útil apenas para testes locais.
    app.run(debug=True, host='0.0.0.0')
