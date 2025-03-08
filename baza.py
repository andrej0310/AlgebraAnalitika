import pymssql
import pandas as pd


brojac = 0

####### FUNKCIJA ZA DOHVAĆANJE PODATAKA IZ BAZE #######
def fetch_data_from_db(query, params=None):
    """Univerzalna funkcija za dohvaćanje podataka iz baze."""
    try:
        global brojac
        conn = pymssql.connect(
            server="infoeduka.database.windows.net",
            user="domagojRuzak",
            password="Lozink@1234",
            database="infoeduka_view"
        )
        
        df = pd.read_sql(query, conn, params=params)  # ✅ Ako nema params, proći će kao None
        
        conn.close()  # ✅ Obavezno zatvori konekciju
        
        brojac += 1
        print("Broj spajanja na SQL:", brojac)

        return df
    
    except pymssql.InterfaceError as e:
        print(f"⛔ Greška u konekciji s bazom: {e}")
        return None  # ❌ Vraćamo None da znamo da baza nije dostupna

    except pymssql.DatabaseError as e:
        print(f"⚠️ SQL greška: {e}")
        return None  # ❌ Sprječava pad aplikacije

    except Exception as e:
        print(f"❗ Nepoznata greška: {e}")
        return None  # ❌ Ako se dogodi bilo koja druga greška, vraćamo None
    

def akademske_godine():
    query = "SELECT * FROM dbo.analytics_vss_struktura_akad_godine"
    df_akademske = fetch_data_from_db(query)
    if df_akademske.empty:
        akademska_aktualna = "2023/2024"  # 🚀 Postavi sigurnu akademsku godinu ako nema podataka
    else:
        akademska_aktualna = df_akademske.loc[df_akademske['aktualna'] == "1", 'naziv'].values[0] if not df_akademske[df_akademske['aktualna'] == "1"].empty else df_akademske['naziv'].iloc[0]

    return df_akademske, akademska_aktualna
