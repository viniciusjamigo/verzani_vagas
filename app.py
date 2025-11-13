import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import base64
import io

# =====================================================================
# FUNÇÃO DE CARREGAMENTO DE DADOS
# =====================================================================
def load_data():
    """Lê e trata o arquivo de dados, retornando um DataFrame."""
    try:
        df = pd.read_csv('data/dados.csv', sep=';')
    except UnicodeDecodeError:
        df = pd.read_csv('data/dados.csv', sep=';', encoding='latin1')
    
    df['Recrutamento e Seleção'] = pd.to_datetime(df['Recrutamento e Seleção'], format='%d/%m/%Y', errors='coerce')
    df.dropna(subset=['Recrutamento e Seleção'], inplace=True)
    df.columns = df.columns.str.strip()
    df['STATUS'] = df['STATUS'].str.strip().fillna('Não especificado')
    df.loc[df['STATUS'] == '', 'STATUS'] = 'Não especificado'
    return df

# =====================================================================
# INICIALIZAÇÃO E CONFIGURAÇÕES GERAIS
# =====================================================================
df = load_data() # Carga inicial dos dados
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG], suppress_callback_exceptions=True)
server = app.server

# =====================================================================
# USUÁRIOS E PERMISSÕES
# =====================================================================
USERS = {
    "verzani": {"password": "vagas123", "role": "admin"},
    "visitante": {"password": "vagas_visitante", "role": "guest"}
}

# =====================================================================
# OPÇÕES PARA FILTROS (BASEADO NA CARGA INICIAL)
# =====================================================================
status_vaga_options = sorted(df['Status da Vaga'].unique())
status_interno_options = sorted(df['STATUS'].unique())

# =====================================================================
# LAYOUTS (PÁGINA DE LOGIN E PÁGINA DO DASHBOARD)
# =====================================================================

# --- Layout da Página de Login ---
login_layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            dbc.Card([
                html.H3("Dashboard de Vagas", className="card-title text-center mt-4"),
                dbc.CardBody([
                    dbc.Alert("Por favor, insira suas credenciais para continuar.", color="secondary"),
                    dbc.Alert(id="output-state", color="danger", is_open=False),
                    dbc.Input(id="username", type="text", placeholder="Usuário", className="mb-3"),
                    dbc.Input(id="password", type="password", placeholder="Senha", className="mb-3"),
                    dbc.Button("Fazer login", id="login-button", color="primary", className="w-100"),
                ])
            ], className="mt-5", style={"maxWidth": "500px"}),
            width=12,
            className="d-flex justify-content-center"
        )
    )
], fluid=True)


# --- Layout Principal do Dashboard (seu código original com adições) ---
dashboard_layout = dbc.Container([
    # Adicionando Botão de Logout e Nome do Usuário
    dbc.Row([
        dbc.Col(html.Div(id='user-name-display', className='text-muted text-start'), width=6),
        dbc.Col(dbc.Button("Sair", id="logout_button", color="danger", size="sm", className="float-end"), width=6),
    ], className="mt-3 mb-2"),

    # Container para a funcionalidade de Upload (visível apenas para admin)
    html.Div(id='upload-container', children=[
        dbc.Row([
            dbc.Col([
                html.Hr(),
                html.H5("Atualizar Base de Dados (Admin)", className="text-info"),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div(['Arraste e solte ou ', html.A('selecione um arquivo .csv')]),
                    style={
                        'width': '100%', 'height': '60px', 'lineHeight': '60px',
                        'borderWidth': '1px', 'borderStyle': 'dashed',
                        'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
                    },
                    multiple=False
                ),
                html.Div(id='output-data-upload'),
                html.Hr()
            ])
        ], className='mb-4')
    ], style={'display': 'none'}), # Oculto por padrão

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
# LAYOUT PRINCIPAL (CONTROLA QUAL PÁGINA MOSTRAR)
# =====================================================================
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session', storage_type='session'),
    dcc.Store(id='data-update-signal'), # Sinalizador para atualização de dados
    html.Div(id='page-content')
])


# =====================================================================
# 4. CALLBACKS - A "INTELIGENCIA" DO DASHBOARD
# =====================================================================

# --- Callback 1: Roteador de Páginas ---
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname'),
     Input('session', 'data')] # MUDANÇA: Agora o callback é acionado quando a sessão muda
)
def display_page(pathname, session_data):
    session_data = session_data or {}
    if session_data.get('authenticated'):
        return dashboard_layout
    else:
        return login_layout

# --- Callback 2: Lógica de Login e Logout (COMBINADOS) ---
@app.callback(
    [Output('session', 'data'),
     Output('output-state', 'children'),
     Output('output-state', 'is_open')],
    [Input('login-button', 'n_clicks'),
     Input('logout_button', 'n_clicks')],
    [State('username', 'value'),
     State('password', 'value')],
     prevent_initial_call=True
)
def manage_session(login_clicks, logout_clicks, username, password):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Lógica de Logout
    if triggered_id == 'logout_button':
        return {}, "", False # Limpa a sessão

    # Lógica de Login
    if triggered_id == 'login-button':
        if username in USERS and password == USERS[username]["password"]:
            session_data = {
                'authenticated': True, 
                'username': username, 
                'role': USERS[username]['role']
            }
            return session_data, "", False
        else:
            error_message = "Usuário ou senha inválidos."
            return dash.no_update, error_message, True
    
    return dash.no_update, "", False

# --- Callback 4: Mostrar/Ocultar Upload com base na permissão ---
@app.callback(
    Output('upload-container', 'style'),
    Input('session', 'data')
)
def show_hide_upload(session_data):
    session_data = session_data or {}
    if session_data.get('role') == 'admin':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


# --- Callback 5: Mostrar nome do usuário logado ---
@app.callback(
    Output('user-name-display', 'children'),
    Input('session', 'data')
)
def display_username(session_data):
    session_data = session_data or {}
    if session_data.get('authenticated'):
        role = "Administrador" if session_data.get('role') == 'admin' else "Visitante"
        return f"Logado como: {session_data.get('username')} ({role})"
    return ""

# --- Callback 6: Processar o Upload do Arquivo ---
@app.callback(
    [Output('output-data-upload', 'children'),
     Output('data-update-signal', 'data')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_output_upload(contents, filename):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            if 'csv' in filename:
                # Salva o novo arquivo
                with open('data/dados.csv', 'wb') as f:
                    f.write(decoded)
                
                # Gera uma mensagem de sucesso
                alert = dbc.Alert(f"Arquivo '{filename}' atualizado com sucesso!", color="success", dismissable=True)
                # Retorna a mensagem e um sinal para os outros callbacks atualizarem
                return alert, datetime.now().isoformat()
            else:
                alert = dbc.Alert("Erro: O arquivo deve ser no formato .csv", color="danger", dismissable=True)
                return alert, dash.no_update

        except Exception as e:
            print(e)
            alert = dbc.Alert(f"Houve um erro ao processar o arquivo: {e}", color="danger", dismissable=True)
            return alert, dash.no_update
            
    return "", dash.no_update


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
        Input('filtro-uf', 'value'),
        Input('data-update-signal', 'data') # Input para o sinal de atualização
    ]
)
def update_dashboard_status_vaga(start_date, end_date, selected_status, selected_grupos, selected_ufs, update_signal):
    # --- 1. Filtragem dos Dados ---
    # Recarrega os dados sempre que a função for chamada
    df = load_data()

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
        Input('filtro-uf', 'value'),
        Input('data-update-signal', 'data') # Input para o sinal de atualização
    ]
)
def update_dashboard_status_interno(start_date, end_date, selected_status, selected_grupos, selected_ufs, update_signal):
    # --- 1. Filtragem dos Dados ---
    # Recarrega os dados sempre que a função for chamada
    df = load_data()

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
