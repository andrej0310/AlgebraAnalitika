import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Dash, no_update
from dash.dependencies import Input, Output, State
import requests
from io import BytesIO
from dash.exceptions import PreventUpdate
from dash import dash_table
from dash.dash_table.Format import Group
import os



dash.register_page(__name__, path="/ProsjekPredmeti")  # ✅ Ispravno



html.Img(src='/content/logo.svg', style={'height': '80px', 'margin-right': '20px'})

# Globalna varijabla u koju spremamo podatke iz `dcc.Store`
akademska_godina = None

# Učitavanje podataka
#file_path = "/content/2023_2024_SVE.xlsx"


#SQL
import pymssql

# 🔹 Povezivanje sa SQL Serverom
conn = pymssql.connect(
    server="infoeduka.database.windows.net",
    user="domagojRuzak",
    password="Lozink@1234",
    database="infoeduka_view"
)

# 🔹 Izvršavanje SQL upita
query = "SELECT * FROM dbo.analytics_final_studentipredmeti WHERE akademska_godina = '2023/2024'"
cursor = conn.cursor()

# 🔹 Dohvaćanje podataka
cursor.execute(query)
rows = cursor.fetchall()

# 🔹 Dohvaćanje naziva stupaca
columns = [col[0] for col in cursor.description]

# 🔹 Kreiranje Pandas DataFrame-a
df = pd.DataFrame(rows, columns=columns)

# 🔹 Zatvaranje konekcije
conn.close()


#df = pd.read_excel(file_path, sheet_name="Sheet1")

# Grupisanje podataka
df_total = df.groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
df_total.rename(columns={'ocjena': 'broj_studenata'}, inplace=True)

df_passed = df[df["ocjena"] > 1].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
df_passed.rename(columns={'ocjena': 'broj_studenata_prosli'}, inplace=True)

df_avg = df[df["ocjena"] > 1].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].mean().reset_index()
df_avg.rename(columns={'ocjena': 'prosjek_ocjena'}, inplace=True)

df_ponavljaci_total = df[df["priznat_ponavlja"] == "Ponavlja"].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
df_ponavljaci_total.rename(columns={'ocjena': 'broj_ponavljaca'}, inplace=True)

df_ponavljaci_passed = df[(df["ocjena"] > 1) & (df["priznat_ponavlja"] == "Ponavlja")].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
df_ponavljaci_passed.rename(columns={'ocjena': 'broj_ponavljaca_prosli'}, inplace=True)


df_priznati_total = df[df["priznat_ponavlja"] == "Priznat"].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
df_priznati_total.rename(columns={'ocjena': 'broj_priznatih'}, inplace=True)

# Spajanje podataka
df_grouped = df_total.merge(df_passed, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
df_grouped = df_grouped.merge(df_avg, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
df_grouped = df_grouped.merge(df_ponavljaci_total, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
df_grouped = df_grouped.merge(df_ponavljaci_passed, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
df_grouped = df_grouped.merge(df_priznati_total, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
#df_grouped = df_grouped.merge(df[['kolegij_sifra', 'semestar']], on='kolegij_sifra', how='left')
df_semestar = df[['kolegij_sifra', 'semestar']].drop_duplicates()  # Makni duplikate
df_grouped = df_grouped.merge(df_semestar, on='kolegij_sifra', how='left')


df_grouped.fillna(0, inplace=True)

df_grouped["prolaznost"] = (df_grouped["broj_studenata_prosli"] / df_grouped["broj_studenata"]) * 100
df_grouped["prolaznost_ponavljaca"] = (df_grouped["broj_ponavljaca_prosli"] / df_grouped["broj_ponavljaca"]) * 100

df_grouped["kolegij_full"] = df_grouped["kolegij_naziv"] + " (" + df_grouped["kolegij_sifra"].astype(str) + ")"

app = dash.get_app()
#server = app.server  # Ovo je potrebno za Render!

sorted_studiji = sorted(df_grouped['studij'].unique())

image_id = "1IVYXW6Ye48OeHt6Xo89gJPp7NRySHwFH"  # Zameni svojim ID-om
image_url = f"https://lh3.googleusercontent.com/d/{image_id}"


layout = html.Div(style={'background-color': '#F4F4F4', 'padding': '20px'}, children=[

    # Header naslovom
    html.Div([
        html.H1("Kolegij - Prosječne ocjene i prolaznost")
    ]),

    # Dropdown filteri
    html.Div([
        html.Label("Studij:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id='studij_dropdown', 
                     options=[{'label': studij, 'value': studij} for studij in sorted(df_grouped['studij'].unique())],
                     placeholder="Odaberi studij",
                     #value=sorted(df_grouped['studij'].unique()),
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown"),

        html.Label("Smjer:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id='smjer_dropdown', 
                     options=[],
                     placeholder="Odaberi smjer",
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown"),

        html.Label("Školska godina:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id='godina_dropdown', 
                     options=[{'label': 'Sve', 'value': 'Sve'}] +
                     [{'label': str(godina), 'value': godina} for godina in df_grouped['skolska_godina'].unique()],
                     placeholder="Odaberi školsku godinu",
                     #value='Sve',
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown")
    ], style={'display': 'flex', 'justify-content': 'center',  "align-items": "center", "width": "100%"}),

    # Grafovi
    dcc.Graph(id='graf'),
    dcc.Graph(id='prolaznost_graf'),
    dcc.Graph(id='prolaznost_ponavljaci_graf'),

    html.Div([
        html.H3("Broj studenata koji nisu položili kolegij", className="table-title"),
        
        dash_table.DataTable(
            id="pivot-tablica-nepolozeni",
            style_table={'overflowX': 'auto'},

            # ✅ Stilizacija zaglavlja tablice
            style_header={
                'backgroundColor': '#be1e67',  # Roza zaglavlje
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'border': '1px solid #ddd'
            },

            # ✅ Stilizacija ćelija podataka
            style_data={
                'textAlign': 'center',
                'padding': '8px',
                'border': '1px solid #ddd'
            },

            # ✅ Dodaj CSS pravila kako bi omogućili hover efekt
            css=[
                {"selector": "tbody tr:hover td", "rule": "background-color: #dd6519 !important; color: white !important;"},
                {"selector": ".dash-spreadsheet", "rule": "border-collapse: collapse !important;"}
            ]
        )
    ]),

    #Preuzimanje pivot excelice sa nepoloženima
    html.Div([
        html.Label("Preuzimanje Excel pivot tablice sa brojem studenata koji nisu položili, a imaju potpis (svi studiji):",
            className="excel-label"
        )
    ],className="excel-container"
    ),
    html.Div([
        html.Label("Filtriraj po semestru:", className="semester-label"),  # ✅ Dodana klasa

        dcc.Dropdown(
            id="filter_semestar",
            options=[
                {"label": "Zimski semestar", "value": "Zimski semestar"},
                {"label": "Ljetni semestar", "value": "Ljetni semestar"}
            ],
            placeholder="Odaberi semestar",
            clearable=True,
            className="semester-dropdown"  # ✅ Dodana klasa
        ),

        html.Button("📥 Preuzmi Excel", id="download-btn", n_clicks=0, className="excel-button"),  # ✅ Dodana klasa
        dcc.Download(id="download-excel")

    ], className="semester-filter-container")  # ✅ Glavna klasa za poravnanje lijevo    

])

@app.callback(
    Output('smjer_dropdown', 'options', allow_duplicate=True),  # ✅ Omogućava dupli output
    Input('studij_dropdown', 'value'),
    prevent_initial_call=True  # ⚠️ Mora biti postavljeno na True
)
def update_smjer_dropdown(selected_studij):
    if not selected_studij:
        raise PreventUpdate  # ⛔ Sprječava prazno ažuriranje

    filtered_df = df_grouped[df_grouped['studij'] == selected_studij]
    smjer_options = [{'label': smjer, 'value': smjer} for smjer in sorted(filtered_df['smjer'].unique())]

    return smjer_options


@app.callback(
    [Output('graf', 'figure'),
     Output('prolaznost_graf', 'figure'),
     Output('prolaznost_ponavljaci_graf', 'figure'),
     Output('graf', 'style'),
     Output('prolaznost_graf', 'style'),
     Output('prolaznost_ponavljaci_graf', 'style')],
    [Input('studij_dropdown', 'value'),
     Input('smjer_dropdown', 'value'),
     Input('godina_dropdown', 'value')]
)
def update_graph(selected_studij, selected_smjer, selected_godina):
    filtered_df = df_grouped[
        (df_grouped['studij'] == selected_studij) &
        (df_grouped['smjer'] == selected_smjer if selected_smjer else True) &
        ((df_grouped['skolska_godina'] == selected_godina) if selected_godina != 'Sve' else True)
    ]

    num_kolegija = len(filtered_df)
    height = 300 + num_kolegija * 30

     # 🔹 Definiraj prilagođene boje za semestar
    semestar_colors = {"Zimski semestar": "#1f77b4", "Ljetni semestar": "#ff7f0e"}  # Plava za zimski, narančasta za ljetni


    fig1 = px.bar(filtered_df,
                  x="prosjek_ocjena",
                  y="kolegij_full",
                  orientation="h",
                  title="Prosječna ocjena po kolegiju",
                  text=filtered_df["prosjek_ocjena"].round(2),
                  hover_data={"broj_studenata": True, "broj_studenata_prosli":True, "broj_ponavljaca": True, "broj_priznatih": True},
                  color="semestar",  # 🔹 Dodana boja prema semestru
                  color_discrete_map=semestar_colors,  # Prilagođene boje
    )
    fig2 = px.bar(filtered_df,
                  x="prolaznost",
                  y="kolegij_full",
                  orientation="h",
                  title="Prolaznost po kolegiju (%)",
                  text=filtered_df["prolaznost"].round(2),
                  hover_data={"broj_studenata": True, "broj_studenata_prosli":True},
                  color="semestar",  # 🔹 Dodana boja prema semestru
                  color_discrete_map=semestar_colors,  # Prilagođene boje
    )
    fig3 = px.bar(filtered_df,
                  x="prolaznost_ponavljaca",
                  y="kolegij_full",
                  orientation="h",
                  title="Prolaznost ponavljača (%)",
                  text=filtered_df["prolaznost_ponavljaca"].round(2),
                  hover_data={"broj_ponavljaca": True, "broj_ponavljaca_prosli":True},
                  color="semestar",  # 🔹 Dodana boja prema semestru
                  color_discrete_map=semestar_colors,  # Prilagođene boje
    )

    for fig in [fig1, fig2, fig3]:
        fig.update_traces(marker=dict(line=dict(width=2)), textposition='outside', textfont_size=12)
        fig.update_layout(yaxis_title="Naziv kolegija (Šifra)", 
                          height=height,
                          title={
                                "font": {
                                "family": "Arial",
                                "size": 30,
                                "color": "darkblue",
                                "weight": "bold"
                                },
                                "x": 0.5,
                                "xanchor": "center"
    })

    fig1.update_layout(xaxis_title="Prosječna ocjena")
    fig2.update_layout(xaxis_title="Prolaznost (%)")
    fig3.update_layout(xaxis_title="Prolaznost ponavljača (%)")

    return fig1, fig2, fig3, {'height': f'{height}px'}, {'height': f'{height}px'}, {'height': f'{height}px'}

# 🔹 PRINUDNO Pokretanje callbacka pri prvom učitavanju
@app.callback(
    Output("shared-data", "data",allow_duplicate=True),
    Input("shared-data", "data"),  
    prevent_initial_call='initial_duplicate',
    allow_duplicate=True  # 👈 Omogućava pokretanje callbacka pri učitavanju
)
def load_static_value(shared_data):
    if not shared_data:
        return no_update  # 🚀 Sprječavamo resetiranje
    global akademska_godina  
    akademska_godina = shared_data.get("akademska_godina", "Nema podataka")  
    #print(f"ProsjekPredmeti {akademska_godina}")  

#OSVJEŽAVANJE DF-a
@app.callback(
    Output('studij_dropdown', 'options'),
    Output('smjer_dropdown', 'options'),
    Output('godina_dropdown', 'options'),
    Input("shared-data", "data")
)
def update_data(shared_data):
    global akademska_godina
    #akademska_godina = shared_data.get("akademska_godina", "Nema podataka")
    
    # 🔹 Povezivanje sa SQL Serverom
    conn = pymssql.connect(
        server="infoeduka.database.windows.net",
        user="domagojRuzak",
        password="Lozink@1234",
        database="infoeduka_view"
    )

    # 🔹 Dinamički SQL upit
    query = f"SELECT * FROM dbo.analytics_final_studentipredmeti WHERE akademska_godina = '{akademska_godina}'"
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    
    # 🔹 Kreiranje Pandas DataFrame-a
    global df_grouped
    global df
    df = pd.DataFrame(rows, columns=columns)
    conn.close()

    # 🔹 Osvježavanje df_grouped
    df_total = df.groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
    df_total.rename(columns={'ocjena': 'broj_studenata'}, inplace=True)

    df_passed = df[df["ocjena"] > 1].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
    df_passed.rename(columns={'ocjena': 'broj_studenata_prosli'}, inplace=True)

    df_avg = df[df["ocjena"] > 1].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].mean().reset_index()
    df_avg.rename(columns={'ocjena': 'prosjek_ocjena'}, inplace=True)

    df_ponavljaci_total = df[df["priznat_ponavlja"] == "Ponavlja"].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
    df_ponavljaci_total.rename(columns={'ocjena': 'broj_ponavljaca'}, inplace=True)

    df_ponavljaci_passed = df[(df["ocjena"] > 1) & (df["priznat_ponavlja"] == "Ponavlja")].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
    df_ponavljaci_passed.rename(columns={'ocjena': 'broj_ponavljaca_prosli'}, inplace=True)


    df_priznati_total = df[df["priznat_ponavlja"] == "Priznat"].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
    df_priznati_total.rename(columns={'ocjena': 'broj_priznatih'}, inplace=True)

    # Spajanje podataka
    df_grouped = df_total.merge(df_passed, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
    df_grouped = df_grouped.merge(df_avg, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
    df_grouped = df_grouped.merge(df_ponavljaci_total, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
    df_grouped = df_grouped.merge(df_ponavljaci_passed, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
    df_grouped = df_grouped.merge(df_priznati_total, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
    #df_grouped = df_grouped.merge(df[['kolegij_sifra', 'semestar']], on='kolegij_sifra', how='left')
    df_semestar = df[['kolegij_sifra', 'semestar']].drop_duplicates()  # Makni duplikate
    df_grouped = df_grouped.merge(df_semestar, on='kolegij_sifra', how='left')


    df_grouped.fillna(0, inplace=True)

    df_grouped["prolaznost"] = (df_grouped["broj_studenata_prosli"] / df_grouped["broj_studenata"]) * 100
    df_grouped["prolaznost_ponavljaca"] = (df_grouped["broj_ponavljaca_prosli"] / df_grouped["broj_ponavljaca"]) * 100

    df_grouped["kolegij_full"] = df_grouped["kolegij_naziv"] + " (" + df_grouped["kolegij_sifra"].astype(str) + ")"

    # 🔹 Ažuriranje dropdown opcija
    studiji_options = [{'label': s, 'value': s} for s in sorted(df_grouped['studij'].unique())]
    smjer_options = []  # Prazan na početku
    godina_options = [{'label': g, 'value': g} for g in sorted(df_grouped['skolska_godina'].unique())]

    return studiji_options, smjer_options, godina_options

#### PIVOT ###
@app.callback(
    Output("pivot-tablica-nepolozeni", "columns"),
    Output("pivot-tablica-nepolozeni", "data"),
    [
        Input("studij_dropdown", "value"),
        Input("smjer_dropdown", "value"),
        Input("godina_dropdown", "value")
    ]
)
def update_pivot_table(selected_studij, selected_smjer, selected_godina):
    # Filtriranje podataka prema odabranim kriterijima
    filtered_df = df[
        (df["studij"] == selected_studij) &
        (df["smjer"] == selected_smjer if selected_smjer else True) &
        (df["skolska_godina"] == selected_godina if selected_godina != 'Sve' else True)
    ]

    # Filtriranje samo studenata koji nisu položili (ocjena = 0 i potpis = 1)
    df_failed = filtered_df[(filtered_df["ocjena"] == 0) & (filtered_df["potpis"] == 1)].copy()

    # Dodavanje stupca s kombinacijom kolegij_naziv + kolegij_sifra
    df_failed["kolegij_full"] = df_failed["kolegij_naziv"] + " (" + df_failed["kolegij_sifra"].astype(str) + ")"

    # Grupiranje i pivotiranje podataka
    df_pivot = df_failed.groupby(["kolegij_full", "semestar", "grupa"])["ocjena"].count().reset_index()
    df_pivot_table = df_pivot.pivot(index=["kolegij_full", "semestar"], columns="grupa", values="ocjena").fillna(0)

    # Resetiranje indeksa za prikaz u Dash tablici
    df_pivot_table.reset_index(inplace=True)

    # **Sortiranje prema semestru** → Prvo "Zimski", zatim "Ljetni"
    df_pivot_table["semestar"] = pd.Categorical(df_pivot_table["semestar"], categories=["Zimski semestar", "Ljetni semestar"], ordered=True)
    df_pivot_table = df_pivot_table.sort_values(by="semestar")

    # Priprema podataka za prikaz u Dash tablici
    columns = [{"name": col, "id": col} for col in df_pivot_table.columns]
    data = df_pivot_table.to_dict("records")

    return columns, data


#GENERIRANJE PIVOT TABLICE SA NEPOLOŽENIMA - SVI STUDIJI TE AKADEMKSE
def get_student_data(akademska_godina):
    """ Dohvaća podatke iz SQL baze na temelju akademske godine. """
    
    conn = pymssql.connect(
        server="infoeduka.database.windows.net",
        user="domagojRuzak",
        password="Lozink@1234",
        database="infoeduka_view"
    )

    query = f"""
        SELECT kolegij_naziv, kolegij_sifra, jmbag, grupa, semestar
        FROM dbo.analytics_final_studentipredmeti
        WHERE akademska_godina = '{akademska_godina}' 
        AND ocjena = 0 AND potpis = 1
    """

    df = pd.read_sql(query, conn)
    conn.close()
    
    return df

def create_pivot_table(df,selected_semestar=None):
    """ Kreira pivot tablicu na temelju preuzetih podataka i filtrira po semestru. """

    # ✅ Ako je korisnik odabrao semestar, filtriraj podatke
    if selected_semestar:
        df = df[df["semestar"] == selected_semestar].copy()

    # ✅ Spajanje naziva kolegija i šifre u jedan stupac
    df["kolegij_full"] = df["kolegij_naziv"] + " (" + df["kolegij_sifra"].astype(str) + ")"

    # ✅ Kreiranje pivot tablice
    pivot_df = df.pivot_table(
        index=["kolegij_full"],  # Redovi -> Spojeni naziv i šifra kolegija
        columns=["grupa"],        # Stupci -> Grupe
        values="jmbag",           # Vrijednosti -> Brojanje JMBAG-a
        aggfunc="count"           # Brojanje broja JMBAG-a
    )

    return pivot_df

def save_pivot_to_excel(df_pivot):
    """ Sprema pivot tablicu u Excel i vraća putanju do datoteke. """
    
    file_path = "pivot_table.xlsx"

    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df_pivot.to_excel(writer, sheet_name="PivotTablica")

    return file_path

@app.callback(
    Output("download-excel", "data"),
    [Input("download-btn", "n_clicks"),
     State("filter_semestar", "value")],  # ✅ Dodan semestar filter
    prevent_initial_call=True
)
def generate_and_download_pivot(n_clicks, selected_semestar):
    if n_clicks is None:
        raise PreventUpdate  # ⛔ Sprječava callback ako nije kliknut gumb
    
    # ✅ Dohvati podatke iz SQL baze
    df = get_student_data(akademska_godina)

    # ✅ Generiraj pivot tablicu s filtriranim semestrom
    df_pivot = create_pivot_table(df, selected_semestar)

    # ✅ Spremi pivot tablicu u Excel
    file_path = save_pivot_to_excel(df_pivot)

    # ✅ Omogući preuzimanje datoteke
    return dcc.send_file(file_path)


if __name__ == '__main__':
    app.run_server(debug=True)
