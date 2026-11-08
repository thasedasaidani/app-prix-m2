"""
Application Flask : estimer le prix au m² d'une commune avec le modèle entraîné (model.pkl).

Lancement :
    pip install flask scikit-learn pandas
    python app.py
Puis ouvrir http://127.0.0.1:5000
"""
import pickle

import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

# ---------- Chargement du modèle (une seule fois, au démarrage) ----------
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

# Les colonnes dans l'ordre exact utilisé à l'entraînement
# (scikit-learn les enregistre quand le modèle est entraîné sur un DataFrame)
COLONNES = list(model.feature_names_in_)

# Noms lisibles pour le formulaire (une colonne absente de cette liste garde son nom)
LIBELLES = {
    "population": "Population (habitants)",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "prix_m2_median_departement": "Prix médian au m² du département (€, ex. 1 800)",
    "part_passoires_dpe_pct": "Part de passoires énergétiques (%)",
    "surface_mediane_m2": "Surface médiane des logements (m²)",
    "nb_ventes": "Nombre de ventes",
    "nb_maisons": "Nombre de maisons vendues",
    "nb_appartements": "Nombre d'appartements vendus",
    "fiabilite_num": "Fiabilité (1 = indicative, 2 = bonne, 3 = élevée)",
    "duree_jours": "Durée de la période (jours)",
    "annee_fin": "Année",
}

# Les colonnes 0/1 créées par get_dummies (ex. nom_departement_Gironde, fiabilite_bonne)
# sont regroupées en une liste déroulante par variable
GROUPES = {
    "nom_departement_": "Département",
    "fiabilite_": "Fiabilité de l'estimation",
}
LISTES = []   # [(préfixe, libellé, [options])]
for prefixe, libelle in GROUPES.items():
    options = [c[len(prefixe):] for c in COLONNES if c.startswith(prefixe)]
    if options:
        LISTES.append((prefixe, libelle, options))
CHAMPS = [c for c in COLONNES if not any(c.startswith(p) for p, _, _ in LISTES)]


@app.route("/", methods=["GET", "POST"])
def index():
    prediction, erreur = None, None
    valeurs = request.form.to_dict() if request.method == "POST" else {}

    if request.method == "POST":
        try:
            ligne = {}
            for col in CHAMPS:
                ligne[col] = float(request.form[col].replace(",", "."))
            # une seule option vaut 1 dans chaque groupe, les autres valent 0
            for prefixe, _, options in LISTES:
                choix = request.form.get(prefixe)
                for option in options:
                    ligne[prefixe + option] = 1 if option == choix else 0

            X = pd.DataFrame([ligne])[COLONNES]   # même ordre de colonnes qu'à l'entraînement
            prediction = round(float(model.predict(X)[0]))
        except (KeyError, ValueError):
            erreur = "Merci de remplir tous les champs avec des nombres."

    return render_template(
        "index.html",
        champs=[(c, LIBELLES.get(c, c)) for c in CHAMPS],
        listes=LISTES,
        valeurs=valeurs,
        prediction=prediction,
        erreur=erreur,
    )


if __name__ == "__main__":
    app.run(debug=True)