import dash
from dash import dcc, html, dash_table, Input, Output
import pandas as pd
import pymssql
from dash.dash_table.Format import Format, Scheme
from sqlalchemy import create_engine
import warnings



dash.register_page(__name__, path="/ProsjekStudenti")  # ✅ Ispravno

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy*")

# 🔹 Povezivanje sa SQL Serverom
def get_student_data():
    conn = pymssql.connect(
        server="infoeduka.database.windows.net",
        user="domagojRuzak",
        password="Lozink@1234",
        database="infoeduka_view"
    )
    
    # 🔹 Izvršavanje SQL upita
    query = """
    SELECT * FROM dbo.analytics_final_statusi_studenata
    WHERE godina = '1. godina' AND status_semestra = 'U'
    """
    df = pd.read_sql(query, conn)
    
    # 🔹 Zatvaranje konekcije
    conn.close()
    
    return df

# 🔹 Dohvati podatke i kreiraj DataFrame sa studentima (jedinstveni OIB)
df_students = get_student_data()
df_students_unique = df_students.drop_duplicates(subset=['oib'])

# 🔹 Dohvati jedinstvene akademske godine i sortiraj ih opadajuće (najnovija prva)
akademske_godine = sorted(df_students_unique["ak_god_naziv"].unique(), reverse=True)


# Kreiranje Dash aplikacije
app = dash.get_app()

layout = html.Div(style={'background-color': '#F4F4F4', 'padding': '20px'}, children=[
    
    # Header naslovom
    html.Div([
        html.H1("Studenti - Prosječne ocjene")
    ]),
    
    # Dropdown filteri

    html.Div([
            html.Label("Generacija:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
            dcc.Dropdown(
            id="filter_akademska_godina",
            options=[{"label": godina, "value": godina} for godina in akademske_godine],
            placeholder="Odaberi akademsku godinu",
            multi=False,
            style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
            className="my-dropdown"
    ),
            html.Label("Studij:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
            dcc.Dropdown(
            id="filter_studij",
            placeholder="Odaberi studij",
            multi=False,
            style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
            className="my-dropdown"
    ),
            html.Label("Smjer:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
            dcc.Dropdown(
            id="filter_smjer",
            placeholder="Odaberi smjer",
            multi=False,
            style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
            className="my-dropdown"
    )
    ],style={'display': 'flex', 'justify-content': 'center',  "align-items": "center", "width": "100%"}),

# 🔹 CheckList filter za "način studiranja"
    html.Div([
        html.Div([
            html.Label("Filtriraj po načinu studiranja:"),
            dcc.Checklist(
                id="filter_nacin",
                options=[],  # Automatski generirano
                inline=True,
                className="dash-checklist"
            )
        ], className="checklist-container"),
        
        html.Div([
            html.Label("Filtriraj po trenutnoj godini:"),
                dcc.Checklist(
                    id="filter_trenutna",
                    options=[],  # Automatski generirano
                    inline=True,
                    className="dash-checklist"
                )
        ], className="checklist-container"),  
    ],style={'display': 'flex', 'justify-content': 'center',  "align-items": "center", "width": "100%", "gap":'40px'}),
    
 
 # Tabela sa podacima
    html.Div([    
        dash_table.DataTable(
            id="student_table",
            columns=[
                {"name": "Redni broj", "id": "redni_broj", "type": "numeric"},
                {"name": "Ime i prezime", "id": "ime_prezime"},
                {"name": "JMBAG", "id": "jmbag"},
                {"name": "Redovni/Izvanredni", "id": "nacin"},
                {"name": "Prosječna ocjena", "id": "prosjek_ocjena",
                "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed),}, #Klasičan prosjek
                {"name": "Težinski prosjek", "id": "tezinski_prosjek",
                "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)},  # Težinski prosjek
                {"name": "Trenutna godina", "id": "trenutna_godina"} #Trenutna godina
            ],
               # ✅ Stilizacija zaglavlja tablice
            data=[],
            sort_action="native",
            style_header={
                'backgroundColor': '#be1e67',  # Roza zaglavlje
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'border': '1px solid #ddd'
            },
            # ✅ Povezivanje CSS-a
            css=[
                {"selector": ".dash-table", "rule": "width: 70%; margin: auto; padding: 20px;"},
                {"selector": ".dash-spreadsheet", "rule": "border-collapse: collapse !important;"}
            ]   
        )
    ])
])

#ažuriranje studija na temelju akademske
@app.callback(
    Output("filter_studij", "options"),
    Input("filter_akademska_godina", "value")
)
def update_studij_options(selected_godina):
    if not selected_godina:
        return []
    filtered_df = df_students_unique[df_students_unique["ak_god_naziv"] == selected_godina]
    studiji_options = [{"label": s, "value": s} for s in filtered_df["studij_naziv"].unique()]
    return studiji_options

#ažuriranje smjera na temelju studija
@app.callback(
    Output("filter_smjer", "options"),
    [Input("filter_akademska_godina", "value"),
     Input("filter_studij", "value")]
)
def update_smjer_options(selected_godina, selected_studij):
    if not selected_godina or not selected_studij:
        return []
    filtered_df = df_students_unique[
        (df_students_unique["ak_god_naziv"] == selected_godina) &
        (df_students_unique["studij_naziv"] == selected_studij)
    ]
    smjer_options = [{"label": smjer, "value": smjer} for smjer in filtered_df["smjer_naziv"].unique()]
    return smjer_options

#dohvaćanje prosječnih ocjena iz baze
def get_student_grades(jmbags):
    if not jmbags:
        return pd.DataFrame(columns=["jmbag", "kolegij_sifra", "ocjena"])

    conn = pymssql.connect(
        server="infoeduka.database.windows.net",
        user="domagojRuzak",
        password="Lozink@1234",
        database="infoeduka_view"
    )

    query = f"""
    SELECT jmbag, kolegij_sifra, ocjena
    FROM dbo.analytics_final_studentipredmeti
    WHERE ocjena > 1 AND kolegij_naziv != 'Praksa' AND jmbag IN ({','.join(["'" + j + "'" for j in jmbags])})
    """

    df_grades = pd.read_sql(query, conn)
    conn.close()
    
    return df_grades

#dohvaćanje ects-a
def get_ects_data():
    """ Dohvaća ECTS bodove za kolegije. """
    
    conn = pymssql.connect(
        server="infoeduka.database.windows.net",
        user="domagojRuzak",
        password="Lozink@1234",
        database="infoeduka_view"
    )

    query = "select sifra, ects from dbo.analytics_vss_predmeti"
    
    df_ects = pd.read_sql(query, conn)

    conn.close()
    
    return df_ects

#dohvaćanje trenutne godine studenta
def get_student_godina(jmbags):
    if not jmbags:
        return pd.DataFrame(columns=["jmbag", "trenutna_godina"])  # 🔹 DODANO: Definiran novi stupac

    conn = pymssql.connect(
        server="infoeduka.database.windows.net",
        user="domagojRuzak",
        password="Lozink@1234",
        database="infoeduka_view"
    )

    # 🔹 DODANO: Ispravljeni SQL upit za dohvat najveće godine po studentu
    query = f"""
    SELECT jmbag, MAX(godina) AS trenutna_godina
    FROM dbo.analytics_final_statusi_studenata
    WHERE jmbag IN ({','.join(["'" + j + "'" for j in jmbags])})
    GROUP BY jmbag;
    """

    df_godina = pd.read_sql(query, conn)  # 🔹 DODANO: Promijenjeno iz df_grades u df_godina
    conn.close()
    
    return df_godina


#ažuriranje tablice sa studentima i prosjecima
@app.callback(
    Output("student_table", "data"),
    [
     Input("filter_akademska_godina", "value"),
     Input("filter_studij", "value"),
     Input("filter_smjer", "value"),
     Input("filter_nacin", "value"),
     Input("filter_trenutna", "value")
    ]
)
def update_student_table(selected_godina, selected_studij, selected_smjer, selected_nacin, selected_trenutna):
    if not selected_godina or not selected_studij or not selected_smjer:
        return []

    # 🔹 Filtriranje studenata
    filtered_students = df_students_unique[
        (df_students_unique["ak_god_naziv"] == selected_godina) &
        (df_students_unique["studij_naziv"] == selected_studij) &
        (df_students_unique["smjer_naziv"] == selected_smjer)
    ]

    # 🔹 Dohvati ocjene studenata
    jmbags = filtered_students["jmbag"].astype(str).tolist()
    df_grades = get_student_grades(jmbags)

    # 🔹 Dohvati ECTS podatke za kolegije
    df_ects = get_ects_data()

    #print(df_ects.head(10))
    #print(df_ects.loc[df_ects["sifra"] == "22-06-500"])

    # 🔹 Spajanje ocjena s ECTS bodovima (preko "kolegij_sifra" u jednoj i "sifra" u drugoj tablici)
    df_grades = df_grades.merge(df_ects, left_on="kolegij_sifra", right_on="sifra", how="left")

    #print(df_grades.loc[df_grades["jmbag"] == "0321021511"])

    # 🔹 Izračun težinskog prosjeka
    df_weighted = df_grades.groupby("jmbag").apply(
        lambda x: (x["ocjena"] * x["ects"]).sum() / x["ects"].sum() if x["ects"].sum() > 0 else 0
    ).reset_index(name="tezinski_prosjek")

    # 🔹 Izračun klasičnog prosjeka ocjena
    df_avg = df_grades.groupby("jmbag")["ocjena"].mean().reset_index(name="prosjek_ocjena")

    # 🔹 Dohvati najveću godinu studenta i dodaj kao novi stupac
    df_godina = get_student_godina(jmbags)  # 🔹 DODANO: Dohvat najveće godine

    # 🔹 Spajanje sa studentima
    df_final = filtered_students.merge(df_avg, on="jmbag", how="left").fillna(0)
    df_final = df_final.merge(df_weighted, on="jmbag", how="left").fillna(0)
    df_final = df_final.merge(df_godina, on="jmbag", how="left").fillna(0)

    # 🔹 Zaokruživanje na 2 decimale
    df_final["prosjek_ocjena"] = df_final["prosjek_ocjena"].astype(float).round(2)
    df_final["tezinski_prosjek"] = df_final["tezinski_prosjek"].astype(float).round(2)

    # 🔹 Sortiranje od najveće prema najmanjoj ocjeni
    df_final = df_final.sort_values(by="prosjek_ocjena", ascending=False)

    # 🔹 Spajamo ime i prezime u jedan stupac
    df_final["ime_prezime"] = df_final["prezime"] + " " + df_final["ime"]

    # 🔹 Ako su odabrane opcije u `CheckList - nacin studiranja`, filtriraj tablicu
    if selected_nacin:
        df_final = df_final[df_final["nacin"].isin(selected_nacin)]

      # 🔹 Ako su odabrane opcije u `CheckList - trenutna godina`, filtriraj tablicu
    if selected_trenutna:
        df_final = df_final[df_final["trenutna_godina"].isin(selected_trenutna)]

     # 🔹 Dodavanje rednog broja
    df_final = df_final.reset_index(drop=True)
    df_final["redni_broj"] = df_final.index + 1

    # 🔹 Vraćanje podataka u Dash tablicu
    return df_final[["redni_broj", "ime_prezime", "jmbag", "prosjek_ocjena", "tezinski_prosjek", "nacin", "trenutna_godina"]].to_dict("records")


@app.callback(
    Output("filter_nacin", "options"),
    [Input("filter_akademska_godina", "value"),
     Input("student_table", "data")
     ]
)
def update_nacin_options(selected_godina, student_data):
    if not student_data:
        return []

    df = pd.DataFrame(student_data)
    unique_nacini = df["nacin"].unique()

    return [{"label": n, "value": n} for n in unique_nacini]

@app.callback(
    Output("filter_trenutna", "options"),
    [Input("filter_akademska_godina", "value"),
     Input("student_table", "data")
     ]
)
def update_trenutna_options(selected_godina, student_data):
    if not student_data:
        return []

    df = pd.DataFrame(student_data)
    unique_trenutna = sorted(df["trenutna_godina"].unique())

    return [{"label": n, "value": n} for n in unique_trenutna]

if __name__ == '__main__':
    app.run_server(debug=True)
