import pandas as pd
import re

INPUT_FILE = "/Users/loulou/Desktop/Stage/depenses_clean_avant_nettoyage.csv"
OUTPUT_FILE = "/Users/loulou/Desktop/Stage/depenses_clean_final.csv"

print("Chargement :", INPUT_FILE)
df = pd.read_csv(INPUT_FILE)
print("Lignes initiales :", len(df))

# ===========================================================================
# MAPPINGS ET RÉFÉRENTIELS
# ===========================================================================

REMAP_FOURNISSEURS = {
    "NIKOLOVA ROSITSA": "COM INTO BLOSSOM",
    "PELLEGRIN ENRICK SEO": "PE CONSULTANT SEO",
    "MEUNIER MOUCHVOZ LAURA": "LAURA MEUNIER",
    "FASTRP": "ELEPHORM",
    "A WORLD FOR US": "A WORLD FOR US",
}

FAUX_FOURNISSEURS = {
    "INTERNE", "STUDIO", "JEANDOMINIQUE ROCHETAING ACTI", "ACTI",
    "FACTURE", "INVOICE", "DOCUMENT", "CLIENT", "SALES", "MARS",
    "MAJ", "RECEIPT",
}

MAPPINGS_FOURNISSEURS_NOM_FICHIER = [
    ("fr001058", "MAAVA CONSULTING"),
    ("facture_23640", "A WORLD FOR US"),
    ("invoice.pdf", "FNAC DIRECT"),
    ("rochetaing", "JEAN-DOMINIQUE ROCHETAING"),
    ("jeandominique", "JEAN-DOMINIQUE ROCHETAING"),
    ("studio87", "STUDIO87"),
    ("studiographique87", "STUDIO87"),
    ("activaj", "ACTIVAJ"),
    ("sales - invoice", "HELLOWORK"),
    ("facture_2023060001", "COM INTO BLOSSOM"),
    ("facture_2023050002", "COM INTO BLOSSOM"),
    ("facture_2025010002", "COM INTO BLOSSOM"),
    ("1503642376", "SNCF"),
    ("fastrp", "ELEPHORM"),
    ("elephorm", "ELEPHORM"),
    ("pellegrin", "PE CONSULTANT SEO"),
    ("meunier", "LAURA MEUNIER"),
    ("nikolova", "COM INTO BLOSSOM"),
    ("xiaomi", "XIAOMI"),
    ("micrologik", "MICROLOGIK"),
    ("ecri", "ECRI"),
    ("facture jg_mars", "JULIAN GUILLEN"),
    ("facture jg-activmedia-maj", "JULIAN GUILLEN"),
    ("2025_06_06_82047677", "THOMANN"),
    ("f2300203", "ARNAUD DEGRAVE"),
    ("facture-activmedia", "BRAINYUP"),
    ("003625f", "FRANCOIS MAESTRATI"),
    ("c2c7c6b59fa48f7ad06a31afab46e3c2", "DARTY"),
    ("invoice2023-10-17", "MABEX"),
    ("receipt-2542-8330", "YAMM"),
    ("receipt-2378-5970", "YAMM"),
    ("0000144081", "JIMMY FAIRLY"),
    ("8575", "APSI"),
    ("6717", "APSI"),
    ("m113424919", "WEEZEVENT"),
    ("c104e1118047o489704", "WEEZEVENT"),
    ("facture_c104e1118047o489704", "WEEZEVENT"),
    ("a86c31f2", "MHR CONSULT"),
    ("2378-5970", "MHR CONSULT"),
    ("2023-11-007938", "IKEA"),
    ("facture.pdf", "IKEA"),
    ("invoice_7211588807", "ADOBE"),
    ("invoice_7162318129", "ADOBE"),
    ("invoice_7118086123", "ADOBE"),
    ("invoice_7080153344", "ADOBE"),
    ("adobe invoice", "ADOBE"),
]

CATEGORIES_PAR_FOURNISSEUR = {
    "LAB": "travaux",
    "RT RENOVATION": "travaux",

    "STUDIO87": "prestations",
    "JEAN-DOMINIQUE ROCHETAING": "prestations",
    "MAAVA CONSULTING": "prestations",
    "ACTIVAJ": "prestations",
    "COM INTO BLOSSOM": "prestations",
    "PE CONSULTANT SEO": "prestations",
    "LAURA MEUNIER": "prestations",
    "PEPITE": "prestations",
    "ECRI": "prestations",
    "JULIAN GUILLEN": "prestations",
    "BRAINYUP": "prestations",
    "ARNAUD DEGRAVE": "prestations",
    "FRANCOIS MAESTRATI": "prestations",

    "DIGIFORMA": "logiciels_abonnements",
    "ELEPHORM": "logiciels_abonnements",
    "GOOGLE": "logiciels_abonnements",
    "ADOBE": "logiciels_abonnements",
    "OPENAI": "logiciels_abonnements",
    "MAKE": "logiciels_abonnements",
    "MICROSOFT": "logiciels_abonnements",
    "ZOOM": "logiciels_abonnements",
    "WPROCKET": "logiciels_abonnements",
    "YAMM": "logiciels_abonnements",
    "MHR CONSULT": "logiciels_abonnements",

    "FNAC DIRECT": "materiel_achats",
    "APPLE": "materiel_achats",
    "AMAZON": "materiel_achats",
    "FOXWAY": "materiel_achats",
    "OVIALA": "materiel_achats",
    "ICASQUE": "materiel_achats",
    "DARTY": "materiel_achats",
    "XIAOMI": "materiel_achats",
    "XIAOMI PAD": "materiel_achats",
    "MICROLOGIK": "materiel_achats",
    "THOMANN": "materiel_achats",
    "MABEX": "materiel_achats",
    "JIMMY FAIRLY": "materiel_achats",
    "IKEA": "materiel_achats",
    "LINKUMA LKM": "materiel_achats",

    "FREE": "telecom",
    "ORANGE": "telecom",
    "SFR": "telecom",
    "HELLOWORK": "telecom",
    "JMBFR": "telecom",

    "EDF": "energie",
    "ENGIE": "energie",

    # CORRECTION : TICKET PITCHOUN REPAS → restauration (était classé materiel_achats)
    "ROSSINI": "restauration",
    "PEDRO SAS": "restauration",
    "NESPRESSO": "restauration",
    "WEEZEVENT": "restauration",
    "TICKET PITCHOUN REPAS": "restauration",
    "TICKET": "restauration",

    "FEDEX": "transport",
    "SNCF": "transport",

    "APSI": "assurance",
    "A WORLD FOR US": "logiciels_abonnements",
}

CORRECTIONS_DATES_NOM_FICHIER = {
    # Apple
    "ua20438852": "2025-02-18",
    "ua09616502": "2024-02-17",
    "ua08773384": "2024-02-17",
    "ua08796307": "2024-02-17",
    "w1456599413": "2024-02-17",

    # Google Ads
    "google ads": "2023-10-31",
    "4847036834": "2023-10-31",
    "gcfrd0011359686": "2023-10-31",

    # ICASQUE
    "facture24788471": "2024-05-11",
    "facture23762126": "2024-05-11",

    # Amazon
    "amazon invoice": "2024-05-26",
    "ds-ase-inv-fr-2024-75992589": "2024-05-26",

    # IKEA
    "2023-11-007938": "2023-11-25",

    # MABEX
    "invoice2023-10-17": "2023-10-17",

    # Zoom
    "inv309867272": "2025-06-17",
    "inv202456476_a01402361_05172023": "2023-05-17",
    "inv215193517_a01402361_08172023": "2023-08-17",

    # Adobe - commandes 2023
    "invoice_7080153344": "2023-01-10",
    "7080153344": "2023-01-10",

    "invoice_7118086123": "2023-08-10",
    "7118086123": "2023-08-10",

    # Adobe - commande 2024
    "invoice_7162318129": "2024-06-10",
    "7162318129": "2024-06-10",

    # Derniers cas DATE
    "inv202456476": "2023-05-17",
    "inv206799185": "2023-06-17",
    "inv289220224": "2025-01-17",
    "invoice.pdf": "2023-04-04",
}

# ===========================================================================
# FONCTIONS
# ===========================================================================

def nettoyer_fournisseur(f):
    if pd.isna(f):
        return None
    f = str(f).upper().strip()
    f = re.sub(r"\s*FC$", "", f)
    f = re.sub(r"\s+", " ", f).strip()
    if re.fullmatch(r"[A-F0-9]{6,}", f):
        return None
    if len(f) < 3:
        return None
    if f in FAUX_FOURNISSEURS:
        return None
    if "JEANDOMINIQUE" in f or f.endswith(" ACTI"):
        return None
    return f


def corriger_fournisseur_depuis_nom_fichier(row):
    fournisseur = row.get("fournisseur")
    nom_fichier = str(row.get("nom_fichier") or "").lower().strip()

    for motif, valeur in MAPPINGS_FOURNISSEURS_NOM_FICHIER:
        if motif.lower() in nom_fichier:
            return valeur

    if pd.notna(fournisseur) and str(fournisseur).strip() not in {"", "A_VERIFIER", "None", "nan"}:
        return fournisseur

    return fournisseur


def corriger_date_depuis_nom_fichier(row):
    if pd.notna(row["date_document"]):
        return row["date_document"]

    nom = str(row.get("nom_fichier") or "").lower().strip()

    for motif, date in CORRECTIONS_DATES_NOM_FICHIER.items():
        if motif.lower() in nom:
            return pd.to_datetime(date, errors="coerce")

    match = re.search(r"(20\d{2})[-_](\d{2})[-_](\d{2})", nom)
    if match:
        annee, mois, jour = match.groups()
        return pd.to_datetime(f"{annee}-{mois}-{jour}", errors="coerce")

    match = re.search(r"(\d{2})(\d{2})(20\d{2})", nom)
    if match:
        mois, jour, annee = match.groups()
        return pd.to_datetime(f"{annee}-{mois}-{jour}", errors="coerce")

    return row["date_document"]


def est_interne(row):
    fournisseur = str(row.get("fournisseur") or "").upper()
    nom_fichier = str(row.get("nom_fichier") or "").lower()

    if fournisseur == "INTERNE":
        return True

    if "activmedia" in nom_fichier and "rochetaing" not in nom_fichier and "studio87" not in nom_fichier:
        if "facture_activmedia" in nom_fichier or "facture activmedia" in nom_fichier:
            return True

    return False


def extraire_date_depuis_nom(nom):
    if pd.isna(nom):
        return None
    nom = str(nom).lower()
    patterns = [
        r"(20\d{2})[-_](\d{2})[-_](\d{2})",
        r"(\d{2})[-_](\d{2})[-_](20\d{2})",
        r"(\d{2})\.(\d{2})\.(20\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, nom)
        if match:
            try:
                return pd.to_datetime(match.group(0), errors="coerce")
            except:
                pass

    mois_en = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12"
    }
    match = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2}),\s+(20\d{2})", nom)
    if match:
        mois = mois_en[match.group(1)]
        jour = match.group(2).zfill(2)
        annee = match.group(3)
        return pd.to_datetime(f"{annee}-{mois}-{jour}", errors="coerce")

    mois_fr = {
        "jan": "01", "fév": "02", "fev": "02", "mar": "03", "avr": "04",
        "mai": "05", "jun": "06", "jui": "07", "aoû": "08", "aou": "08",
        "sep": "09", "oct": "10", "nov": "11", "déc": "12", "dec": "12"
    }
    match = re.search(r"(\d{1,2})[-_](jan|fév|fev|mar|avr|mai|jun|jui|aoû|aou|sep|oct|nov|déc|dec)[-_](20\d{2})", nom)
    if match:
        jour = match.group(1).zfill(2)
        mois = mois_fr[match.group(2)]
        annee = match.group(3)
        return pd.to_datetime(f"{annee}-{mois}-{jour}", errors="coerce")

    return None


def determiner_probleme(row):
    problemes = []
    fournisseur = str(row.get("fournisseur") or "").strip()
    categorie = str(row.get("categorie_depense") or "").strip().lower()

    if pd.isna(row.get("fournisseur")) or fournisseur in {"", "A_VERIFIER", "None", "nan"}:
        problemes.append("FOURNISSEUR")
    if pd.isna(row.get("date_document")):
        problemes.append("DATE")
    if pd.isna(row.get("montant_ttc")) or float(row.get("montant_ttc")) <= 0:
        problemes.append("MONTANT")
    if pd.isna(row.get("categorie_depense")) or categorie in {"", "autre", "nan"}:
        problemes.append("CATEGORIE")

    return ";".join(problemes)


# ===========================================================================
# DÉTECTION DES DOUBLONS
# Logique en 3 niveaux, du plus évident au plus subtil
# ===========================================================================

def detecter_doublons(df):
    """
    Détecte 3 types de doublons et retourne une colonne 'doublon_detecte'.
    La ligne conservée est marquée False, les doublons True.
    """
    df = df.copy()
    df["doublon_detecte"] = False
    df["motif_doublon"] = ""

    # --- NIVEAU 1 : même fichier, même numéro de document, même montant ---
    # Cas EDF : même facture téléchargée N fois sous des noms différents
    # Cas ZOOM : facture avec et sans suffixe _A01402361_...
    # On garde la première occurrence (nom_fichier le plus court = original)
    df["_nom_len"] = df["nom_fichier"].str.len().fillna(999)
    masque_n1 = (
        df["numero_document"].notna()
        & (df["numero_document"].astype(str).str.strip() != "")
        & (df["numero_document"].astype(str).str.strip() != "nan")
        & df["montant_ttc"].notna()
    )
    cles_n1 = ["fournisseur", "numero_document", "montant_ttc"]
    idx_garder_n1 = (
        df[masque_n1]
        .sort_values("_nom_len")
        .groupby(cles_n1, dropna=False)
        .head(1)
        .index
    )
    doublons_n1 = df[masque_n1].index.difference(idx_garder_n1)
    df.loc[doublons_n1, "doublon_detecte"] = True
    df.loc[doublons_n1, "motif_doublon"] = "DOUBLON_MEME_NUMERO"

    # --- NIVEAU 2 : même fournisseur, même montant, même mois ---
    # Cas ADOBE récapitulatif : un PDF unique qui liste 12 mois → extrait en 12 lignes
    # Cas GOOGLE ADS : PDF dupliqué avec/sans numéro dans le nom
    # On ne conserve qu'une ligne par (fournisseur, montant, mois)
    df["_mois"] = pd.to_datetime(df["date_document"], errors="coerce").dt.to_period("M").astype(str)
    masque_n2 = ~df["doublon_detecte"]  # ne retraiter que les non-déjà-marqués
    cles_n2 = ["fournisseur", "montant_ttc", "_mois"]
    idx_garder_n2 = (
        df[masque_n2]
        .sort_values("_nom_len")
        .groupby(cles_n2, dropna=False)
        .head(1)
        .index
    )
    doublons_n2 = df[masque_n2].index.difference(idx_garder_n2)
    df.loc[doublons_n2, "doublon_detecte"] = True
    df.loc[doublons_n2, "motif_doublon"] = "DOUBLON_MEME_MOIS"

    # --- NIVEAU 3 : même nom de fichier de base (suffixe _2 ou légère variation) ---
    # Cas MAKE : Invoice-5D1BC43C-0001.pdf et Invoice-5D1BC43C-00012.pdf
    # On extrait la racine du nom (sans extension, sans chiffre final isolé)
    def racine_nom(nom):
        if pd.isna(nom):
            return ""
        nom = str(nom).lower()
        nom = re.sub(r"\.(pdf|xlsx|csv|png|jpg)$", "", nom)
        nom = re.sub(r"[-_ ]?(copy|copie|\d)$", "", nom)
        return nom.strip()

    df["_racine_nom"] = df["nom_fichier"].apply(racine_nom)
    masque_n3 = ~df["doublon_detecte"] & (df["_racine_nom"] != "")
    cles_n3 = ["fournisseur", "montant_ttc", "_racine_nom"]
    idx_garder_n3 = (
        df[masque_n3]
        .sort_values("_nom_len")
        .groupby(cles_n3, dropna=False)
        .head(1)
        .index
    )
    doublons_n3 = df[masque_n3].index.difference(idx_garder_n3)
    df.loc[doublons_n3, "doublon_detecte"] = True
    df.loc[doublons_n3, "motif_doublon"] = "DOUBLON_NOM_SIMILAIRE"

    # Nettoyage colonnes temporaires
    df = df.drop(columns=["_nom_len", "_mois", "_racine_nom"])

    return df


# ===========================================================================
# PIPELINE DE NETTOYAGE
# ===========================================================================

# 1. Nettoyage fournisseur
df["fournisseur"] = df["fournisseur"].apply(nettoyer_fournisseur)

# 2. Correction fournisseur depuis nom_fichier
df["fournisseur"] = df.apply(corriger_fournisseur_depuis_nom_fichier, axis=1)

# 3. Remap final
df["fournisseur"] = df["fournisseur"].replace(REMAP_FOURNISSEURS)

# 4. Exclusion interne
avant = len(df)
df = df[~df.apply(est_interne, axis=1)].copy()
print("Après exclusion interne :", len(df), "| supprimés :", avant - len(df))

# 5. Dates et montants
df["date_document"] = pd.to_datetime(df["date_document"], errors="coerce")
df["date_document"] = df.apply(corriger_date_depuis_nom_fichier, axis=1)
df["date_document"] = pd.to_datetime(df["date_document"], errors="coerce")
df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce")

# 6. Fournisseur manquant
df["fournisseur"] = df["fournisseur"].fillna("A_VERIFIER")

# 7. Catégories
df["categorie_depense"] = df["categorie_depense"].fillna("autre")
df["categorie_depense"] = df["categorie_depense"].astype(str).str.strip().str.lower()

for fournisseur, categorie in CATEGORIES_PAR_FOURNISSEUR.items():
    df.loc[df["fournisseur"] == fournisseur, "categorie_depense"] = categorie

# 8. Déduplication de base sur nom_fichier (inchangée, filet de sécurité)
if "page" in df.columns:
    df["page_cle"] = df["page"].fillna(0).astype(int).astype(str)
else:
    df["page_cle"] = "0"

df["date_cle"] = df["date_document"].dt.strftime("%Y-%m-%d").fillna("DATE_VIDE")
df["montant_cle"] = df["montant_ttc"].round(2)

avant = len(df)
df = df.drop_duplicates(
    subset=["nom_fichier", "page_cle", "montant_cle", "date_cle"],
    keep="first"
).copy()
print("Doublons nom_fichier stricts supprimés :", avant - len(df))
df = df.drop(columns=["page_cle", "date_cle", "montant_cle"])

# 9. Détection avancée des doublons (EDF, ADOBE, ZOOM, GOOGLE, MAKE...)
print("\nDétection avancée des doublons...")
df = detecter_doublons(df)
nb_doublons = df["doublon_detecte"].sum()
print(f"Doublons détectés : {nb_doublons}")
if nb_doublons > 0:
    print(df[df["doublon_detecte"]][["fournisseur", "montant_ttc", "date_document", "nom_fichier", "motif_doublon"]]
          .sort_values(["fournisseur", "montant_ttc"])
          .to_string(index=False))

# Les doublons sont MARQUÉS mais pas supprimés → traçabilité complète
# Pour l'analyse, on travaille uniquement sur les lignes non-doublons
df_propre = df[~df["doublon_detecte"]].copy()
print(f"\nLignes après exclusion doublons : {len(df_propre)}")

# 10. Tri
df_propre = df_propre.sort_values(by=["date_document", "nom_fichier"], ascending=[False, True])

# 11. Qualité des données + problèmes
df_propre["probleme"] = df_propre.apply(determiner_probleme, axis=1)
df_propre["qualite_data"] = "OK"
df_propre.loc[df_propre["probleme"] != "", "qualite_data"] = "A_VERIFIER"

# 12. Score de fiabilité
df_propre["score_fiabilite"] = 100
df_propre.loc[df_propre["probleme"].str.contains("FOURNISSEUR", na=False), "score_fiabilite"] -= 40
df_propre.loc[df_propre["probleme"].str.contains("DATE", na=False), "score_fiabilite"] -= 30
df_propre.loc[df_propre["probleme"].str.contains("MONTANT", na=False), "score_fiabilite"] -= 30
df_propre.loc[df_propre["probleme"].str.contains("CATEGORIE", na=False), "score_fiabilite"] -= 10

# 13. Export du fichier propre (sans doublons)
df_propre.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

# Export optionnel du fichier complet avec colonne doublon_detecte (utile pour audit)
OUTPUT_AUDIT = OUTPUT_FILE.replace(".csv", "_avec_doublons.csv")
df.to_csv(OUTPUT_AUDIT, index=False, encoding="utf-8-sig")
print(f"\nFichier audit (avec doublons marqués) : {OUTPUT_AUDIT}")

# ===========================================================================
# RAPPORT FINAL
# ===========================================================================

print("\n" + "="*60)
print("NETTOYAGE TERMINÉ ✅")
print("="*60)
print("Lignes finales (fichier propre) :", len(df_propre))
print("Doublons exclus :", nb_doublons)

print("\nTop fournisseurs :")
print(df_propre.groupby("fournisseur")["montant_ttc"].sum().sort_values(ascending=False).head(15))

print("\nTop catégories :")
print(df_propre.groupby("categorie_depense")["montant_ttc"].sum().sort_values(ascending=False))

print("\nQualité des données :")
print(df_propre["qualite_data"].value_counts())

print("\nProblèmes restants :")
if (df_propre["probleme"] != "").sum() == 0:
    print("Aucun problème détecté ✅")
else:
    print(df_propre[df_propre["probleme"] != ""]["probleme"].value_counts())

print("\nRépartition des motifs de doublons :")
print(df[df["doublon_detecte"]]["motif_doublon"].value_counts())

print("\n📊 ANALYSE DES DÉPENSES")
total_depenses = df_propre["montant_ttc"].sum()
print(f"\n💰 Total dépenses : {round(total_depenses, 2)} €")

df_propre["mois"] = df_propre["date_document"].dt.to_period("M")
depenses_mensuelles = df_propre.groupby("mois")["montant_ttc"].sum().sort_index()
print("\n📅 Dépenses mensuelles :")
print(depenses_mensuelles.tail(12))

print("\n🏆 Top 10 fournisseurs :")
print(df_propre.groupby("fournisseur")["montant_ttc"].sum().sort_values(ascending=False).head(10))

print("\n📂 Répartition catégories (%) :")
repartition = (
    df_propre.groupby("categorie_depense")["montant_ttc"].sum() / total_depenses * 100
).round(2)
print(repartition.sort_values(ascending=False))

seuil = df_propre["montant_ttc"].quantile(0.95)
anomalies = df_propre[df_propre["montant_ttc"] > seuil]
print("\n⚠️ Dépenses élevées (top 5%) :")
print(
    anomalies[["fournisseur", "montant_ttc"]]
    .sort_values(by="montant_ttc", ascending=False)
    .head(10)
)

print("\n🔁 Fournisseurs les plus fréquents :")
print(df_propre["fournisseur"].value_counts().head(10))

print("\n🔎 Fournisseurs encore classés en autre :")
autres = df_propre[df_propre["categorie_depense"] == "autre"]
if len(autres) == 0:
    print("Aucun fournisseur en autre ✅")
else:
    print(
        autres[["fournisseur", "montant_ttc"]]
        .groupby("fournisseur")
        .sum()
        .sort_values(by="montant_ttc", ascending=False)
    )

print("\n⚠️ Lignes encore à vérifier :")
a_verifier = df_propre[df_propre["qualite_data"] == "A_VERIFIER"]
if len(a_verifier) == 0:
    print("Aucune ligne à vérifier ✅")
else:
    colonnes_affichage = [c for c in [
        "fournisseur", "categorie_depense", "nom_fichier",
        "montant_ttc", "date_document", "probleme", "score_fiabilite"
    ] if c in a_verifier.columns]
    print(
        a_verifier[colonnes_affichage]
        .sort_values(by="montant_ttc", ascending=False)
        .head(30)
        .to_string(index=False)
    )

print(
    df_propre[df_propre["fournisseur"] == "JEAN-DOMINIQUE ROCHETAING"][
        ["nom_fichier", "montant_ttc", "date_document", "type_flux"]
    ].to_string(index=False)
)
