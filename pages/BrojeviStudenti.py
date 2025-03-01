
import dash
from dash import dcc, html, Input, Output, callback_context, no_update, State
import pandas as pd
import pymssql
import plotly.express as px
import warnings
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/BrojeviStudenti")  # ✅ Ispravno

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy*")


# Globalna varijabla za akademsku godinu
akademska_godina = "2024/2025"  # Defaultna vrijednost


def get_student_data(akademska_godina):
    """ Dohvati podatke o studentima za određenu akademsku godinu. """
    conn = pymssql.connect(
        server="infoeduka.database.windows.net",
        user="domagojRuzak",
        password="Lozink@1234",
        database="infoeduka_view"
    )

    query = """
    SELECT oib, studij_naziv, smjer_naziv, godina, status_semestra, spol, nacin, status_studija
    FROM dbo.analytics_final_statusi_studenata
    WHERE ak_god_naziv = %s
    """
    
    df = pd.read_sql(query, conn, params=[akademska_godina])

    #print(f"📌 DEBUG: Broj redaka u df ({akademska_godina}): {len(df)}")

    conn.close()
    
    return df

df = get_student_data(akademska_godina)

# Kreiranje Dash aplikacije
app = dash.get_app()

layout = html.Div(style={'background-color': '#F4F4F4', 'padding': '20px'}, children=[
    
    

    # Header naslovom
    html.Div([
        html.H1("Analiza - brojevi studenata", style={"text-align": "center"}),
        
    ]),
   
    # Dropdown filteri

  
    html.Div([
        html.Label("Studij:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id="dropdown-studij", 
                     placeholder="Odaberi studij", 
                     options=[],
                     multi=False,
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown"),

        html.Label("Smjer:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id="dropdown-smjer", 
                     placeholder="Odaberi smjer", 
                     options=[],
                     multi=False,
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown"),

        html.Label("Školska godina", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id="dropdown-godina", 
                     placeholder="Odaberi školsku godinu", 
                     options=[],
                     multi=False,
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown")
    ], style={'display': 'flex', 'justify-content': 'center',  "align-items": "center", "width": "100%"}),

    html.Div([    
        html.Label("Broj studenata (po akademskoj godini)")
    ],className="graph-naslov"),
    

    html.Div([
        dbc.Card([
            dbc.CardBody([
                html.H5("UKUPAN BROJ STUDENATA", className="card-title"),
                html.H2(id="total-students", className="card-text")
            ])
        ], className="student-card")  
    ],style={'display':'flex','justify-content': 'center',  "align-items":'center','margin-bottom':'15px'}),

    html.Div(style={'display': 'flex', 'justify-content': 'center','gap':'15px','margin-bottom':'15px'}, children=[
        dcc.Graph(id="graf-studenti-status", style={'width': '25%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}),
        dcc.Graph(id="graf-studenti-zavrseno", style={'width': '25%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'})
    ]),
    html.Div(style={'display': 'flex', 'justify-content': 'center','gap':'15px'}, children=[ 
        dcc.Graph(id="graf-studenti-nacin", style={'width': '25%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}),
        dcc.Graph(id="graf-studenti-spol", style={'width': '25%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}) 
    ])
    
])


@app.callback(
    Output('dropdown-studij', 'options'),
    Output('dropdown-smjer', 'options'),
    Output('dropdown-godina', 'options'),
    Output('dropdown-studij', 'value'),
    Output('dropdown-smjer', 'value'),
    Output('dropdown-godina', 'value'),
    Input("shared-data", "data"),
    State('dropdown-studij', 'value'),
    State('dropdown-smjer', 'value'),
    State('dropdown-godina', 'value')
)
def update_dropdown_options(share_data, selected_studij, selected_smjer, selected_godina):
    global df   
    print(akademska_godina)
    #akademska_godina = "2024/2025"
    
    df = get_student_data(akademska_godina)
    
    # 🔹 Generiranje opcija za dropdown-e
    studij_options = [{"label": str(s), "value": str(s)} for s in sorted(df["studij_naziv"].dropna().unique())]
    smjer_options = []  # Prazan na početku
    godina_options = [{'label': g, 'value': g} for g in sorted(df['godina'].unique())]

    # Provjera da li su prethodno odabrane vrijednosti još uvijek dostupne
    if selected_studij not in [s["value"] for s in studij_options]:
        selected_studij = None
    if selected_smjer not in [s["value"] for s in smjer_options]:
        selected_smjer = None
    if selected_godina not in [g["value"] for g in godina_options]:
        selected_godina = None

    return studij_options, smjer_options, godina_options, selected_studij, selected_smjer, selected_godina

@app.callback(
    Output('dropdown-smjer', 'options', allow_duplicate=True),  # ✅ Omogućava dupli output
    Output('dropdown-smjer', 'value', allow_duplicate=True),
    Input('dropdown-studij', 'value'),
    State('dropdown-smjer', 'value'),
    prevent_initial_call=True  # ⚠️ Mora biti postavljeno na True
)
def update_smjer_dropdown(selected_studij,selected_smjer):
    if not selected_studij:
        raise PreventUpdate  # ⛔ Sprječava prazno ažuriranje

    filtered_df = df[df['studij_naziv'] == selected_studij]
    smjer_options = [{'label': smjer, 'value': smjer} for smjer in sorted(filtered_df['smjer_naziv'].unique())]

    # Ako prethodno odabrani smjer postoji u novim opcijama, zadrži ga
    if selected_smjer in [s["value"] for s in smjer_options]:
        return smjer_options, selected_smjer
    
    return smjer_options, None
######

@app.callback(
    Output("graf-studenti-status", "figure"),
    Output("graf-studenti-nacin", "figure"),
    Output("graf-studenti-spol", "figure"),
    Output("graf-studenti-zavrseno", "figure"),
    Output("total-students", "children"),
    [Input("dropdown-studij", "value"),
     Input("dropdown-smjer", "value"),
     Input("dropdown-godina", "value")]
)
def update_student_graphs(selected_studij, selected_smjer, selected_godina):
    """Generira tri tortna grafikona:
    1. Broj studenata po statusu (U, P, M)
    2. Broj redovnih i izvanrednih studenata
    3. Broj muških i ženskih studenata
    4. Broj ispis, diplomirao, mobilnost
    """
    
    df = get_student_data(akademska_godina)

    # Primjena filtera
    if selected_studij:
        df = df[df["studij_naziv"] == selected_studij]
    if selected_smjer:
        df = df[df["smjer_naziv"] == selected_smjer]
    if selected_godina:
        df = df[df["godina"] == selected_godina]

    # Makni duplikate po OIB-u
    df = df.drop_duplicates(subset=["oib", "studij_naziv"])
    
    total_students = len(df)

    # Ako nema podataka, vrati prazne grafikone s porukom
    if df.empty:
        return px.pie(title="Nema podataka"), px.pie(title="Nema podataka"), px.pie(title="Nema podataka"), px.pie(title="Nema podataka"), f"{total_students} studenata"

    ### 🔹 1. Tortni grafikon - Broj studenata po statusu
    status_counts = df["status_semestra"].value_counts().reset_index()
    status_counts.columns = ["status", "broj_studenata"]
    status_labels = {"U": "Redovni", "P": "Ponavljači", "M": "Mirovanje"}
    status_counts["status"] = status_counts["status"].map(status_labels)

    fig_status = px.pie(
        status_counts, names="status", values="broj_studenata",
        title="Broj studenata po statusu",
        color="status",
        color_discrete_map={"Redovni": "#1f77b4", "Ponavljači": "#ff7f0e", "Mirovanje": "#2ca02c"},
        hole=0.4
    )
    fig_status.update_traces(textinfo="label+percent+value",textfont_size=16, pull=[0.1] * len(status_counts),textposition="outside",marker=dict(line=dict(color='#000000', width=2)))

    ### 🔹 2. Tortni grafikon - Broj redovnih i izvanrednih studenata
    nacin_counts = df["nacin"].value_counts().reset_index()
    nacin_counts.columns = ["nacin", "broj_studenata"]
    fig_nacin = px.pie(
        nacin_counts, names="nacin", values="broj_studenata",
        title="Redovni vs. Izvanredni",
        color="nacin",
        color_discrete_map={"Redovni": "#636EFA", "Izvanredni": "#EF553B"},
        hole=0.4,
    )
    fig_nacin.update_traces(textinfo="label+percent+value",textfont_size=16, pull=[0.1] * len(nacin_counts),textposition="outside",marker=dict(line=dict(color='#000000', width=2)))

    ### 🔹 3. Tortni grafikon - Broj muških i ženskih studenata
    spol_counts = df["spol"].value_counts().reset_index()
    spol_counts.columns = ["spol", "broj_studenata"]
    fig_spol = px.pie(
        spol_counts, names="spol", values="broj_studenata",
        title="Muški vs. Ženski",
        color="spol",
        color_discrete_map={"Muški": "#FFA07A", "Ženski": "#9400D3"},
        hole=0.4
    )
    fig_spol.update_traces(textinfo="label+percent+value",textfont_size=16, pull=[0.1] * len(spol_counts),textposition="outside",marker=dict(line=dict(color='#000000', width=2)))

    # Dodaj animaciju za glatkiji prijelaz
    fig_status.update_layout(transition_duration=500)
    fig_spol.update_layout(transition_duration=500)
    fig_nacin.update_layout(transition_duration=500)


    ### 🔹 4. Tortni grafikon - Broj diplomirali, ispisani, završena mobilnost
    lista_filter = ["diplomirala/o", "ispis", "završena mobilnost"]
    zavrseno_filter = df[df["status_studija"].isin(lista_filter)]
    zavrseno_counts = zavrseno_filter["status_studija"].value_counts().reset_index()
    zavrseno_counts.columns = ["zavrseno", "broj_studenata"]
    status_l = {
    "diplomirala/o": "Diplomirali",
    "ispis": "Ispisani",
    "završena mobilnost": "Završena mobilnost"
    }
    zavrseno_counts["zavrseno"] = zavrseno_counts["zavrseno"].map(status_l)
    fig_zavrseno = px.pie(
        zavrseno_counts, names="zavrseno", values="broj_studenata",
        title="Diplomirali / Ispisani / Završena mobilnost",
        color="zavrseno",
        color_discrete_map={"Diplomirali": "#3A25BE", "Ispisani": "#BE2556","Završena mobilnost":"#2ca02c"},
        hole=0.4
    )
    fig_zavrseno.update_traces(textinfo="label+value",textfont_size=16, pull=[0.1] * len(spol_counts),textposition="outside",marker=dict(line=dict(color='#000000', width=2)))

    return fig_status, fig_nacin, fig_spol, fig_zavrseno, f"{total_students} studenata"


@app.callback(
    Output("shared-data", "data", allow_duplicate=True),  
    [Input("shared-data", "data"),
     Input("shared-data-local","data")],
    prevent_initial_call='initial_duplicate',
    allow_duplicate=True  # 👈 Omogućava pokretanje callbacka pri učitavanju
)
def update_akademska_godina(shared_data,data):
    global akademska_godina  # ✅ Koristimo globalnu varijablu

    if not shared_data or "akademska_godina" not in shared_data or not data:
        print("⚠️ `shared-data` je prazan! Akademska godina ostaje:", akademska_godina)
        return dash.no_update  # 🚀 Ne mijenja ništa ako nema novih podataka

    akademska_godina = shared_data.get("akademska_godina", "Nema podataka") 
    print(f"✅ Brojevi studenata - akademska godina: {akademska_godina}")

    #return dash.no_update  # 🚀 Ne vraćamo ništa jer ne ažuriramo UI
    #return no_update, f'Broj studenata ({akademska_godina})'

if __name__ == '__main__':
    app.run_server(debug=True)