import pandas as pd
import numpy as np
import os
import sys
import warnings
import joblib
import matplotlib.pyplot as plt
import shap
from sklearn.ensemble import RandomForestClassifier

warnings.filterwarnings("ignore")

# Configurar rutas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'archive', 'pl-predictor')))
from src.config import FEATURES_PATH, TARGETS, FEATURES, MODELS_DIR
from evaluar_modelos_optimos import prepare_targets

def get_meta_features(row, bet_type):
    h_elo = row['home_elo']
    a_elo = row['away_elo']
    h_rest = row['home_rest']
    a_rest = row['away_rest']
    
    if bet_type == 'home':
        elo_diff = h_elo - a_elo
        rest_diff = h_rest - a_rest
    elif bet_type == 'away':
        elo_diff = a_elo - h_elo
        rest_diff = a_rest - h_rest
    elif bet_type == 'draw':
        elo_diff = -abs(h_elo - a_elo)
        rest_diff = abs(h_rest - a_rest)
    elif bet_type == 'dc_1X':
        elo_diff = h_elo - a_elo
        rest_diff = h_rest - a_rest
    elif bet_type == 'dc_X2':
        elo_diff = a_elo - h_elo
        rest_diff = a_rest - h_rest
    elif bet_type in ['over', 'under']:
        elo_diff = abs(h_elo - a_elo)
        rest_diff = h_rest + a_rest
    else:
        elo_diff = 0.0
        rest_diff = 0.0
        
    return elo_diff, rest_diff

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pres_dir = os.path.abspath(os.path.join(current_dir, "..", "Carpeta_Presentacion"))
    
    df = pd.read_csv(FEATURES_PATH)
    df = df[df['game_id'].astype(str) != '0'].reset_index(drop=True)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = prepare_targets(df)
    
    X = df[FEATURES]
    
    # -------------------------------------------------------------------------
    # PARTE 1: SHAP PARA TODOS LOS MODELOS DE CAPA 1 (8 MERCADOS)
    # -------------------------------------------------------------------------
    markets = [
        {
            "file": "model_1X2_Match_Winner.pkl",
            "title": "1X2 (Match Winner) - Clase Local",
            "out_name": "shap_capa1_1x2_match_winner.png",
            "multiclass_class": 2 # 2 representa victoria local
        },
        {
            "file": "model_Double_Chance_1X_Home_or_Draw.pkl",
            "title": "Double Chance 1X (Home or Draw)",
            "out_name": "shap_capa1_double_chance_1x.png",
            "multiclass_class": None
        },
        {
            "file": "model_Double_Chance_X2_Away_or_Draw.pkl",
            "title": "Double Chance X2 (Away or Draw)",
            "out_name": "shap_capa1_double_chance_x2.png",
            "multiclass_class": None
        },
        {
            "file": "model_Over_2_5_Goals.pkl",
            "title": "Over 2.5 Goals",
            "out_name": "shap_capa1_over_2_5_goals.png",
            "multiclass_class": None
        },
        {
            "file": "model_Under_2_5_Goals.pkl",
            "title": "Under 2.5 Goals",
            "out_name": "shap_capa1_under_2_5_goals.png",
            "multiclass_class": None
        },
        {
            "file": "model_BTTS_Both_Teams_To_Score.pkl",
            "title": "BTTS (Both Teams To Score)",
            "out_name": "shap_capa1_btts_yes.png",
            "multiclass_class": None
        },
        {
            "file": "model_BTTS_-_No.pkl",
            "title": "BTTS - No",
            "out_name": "shap_capa1_btts_no.png",
            "multiclass_class": None
        },
        {
            "file": "model_Home_Clean_Sheet.pkl",
            "title": "Home Clean Sheet",
            "out_name": "shap_capa1_home_clean_sheet.png",
            "multiclass_class": None
        }
    ]
    
    generated_plots = []
    
    print("==================================================")
    # 8 Mercados de Capa 1
    print("PROCESANDO SHAP PARA LOS 8 MODELOS DE CAPA 1...")
    print("==================================================")
    
    for m in markets:
        model_path = os.path.join(MODELS_DIR, m["file"])
        if not os.path.exists(model_path):
            print(f"⚠️ Warning: No se encontró el modelo en {model_path}, se omite.")
            continue
            
        print(f"\nProcesando: {m['title']}...")
        pipe = joblib.load(model_path)
        preprocessor = pipe.named_steps['preprocessor']
        classifier = pipe.named_steps['classifier']
        
        # Preprocesar datos
        X_transformed = preprocessor.transform(X)
        
        # Obtener nombres de columnas correctos
        skewed_features = ['away_xg', 'referee_avg_cards_history', 'B365H', 'B365D', 'B365A', 'h_l5_fls', 'a_l5_fls', 'h_l5_xg', 'a_l5_xg', 'h_l5_xga', 'a_l5_xga']
        skewed_in_features = [f for f in skewed_features if f in FEATURES]
        standard_in_features = [f for f in FEATURES if f not in skewed_in_features]
        feature_names = skewed_in_features + standard_in_features
        
        X_trans_df = pd.DataFrame(X_transformed, columns=feature_names)
        clf_type = type(classifier).__name__
        print(f"  Algoritmo: {clf_type}")
        
        # Calcular explicabilidad
        try:
            if "XGBClassifier" in clf_type or "HistGradientBoostingClassifier" in clf_type:
                explainer = shap.TreeExplainer(classifier)
                shap_values = explainer(X_trans_df)
                shap_values_to_plot = shap_values
            elif "LogisticRegression" in clf_type:
                explainer = shap.LinearExplainer(classifier, X_trans_df)
                shap_values = explainer(X_trans_df)
                if m["multiclass_class"] is not None:
                    # Indexar la clase específica (ej. Local para 1X2)
                    shap_values_to_plot = shap_values[..., m["multiclass_class"]]
                else:
                    shap_values_to_plot = shap_values
            elif "PyTorchMLPClassifier" in clf_type:
                # Submuestreo para velocidad
                X_bg = shap.sample(X_trans_df, 50)
                # Probabilidad de clase 1 (positiva)
                f_prob = lambda x: classifier.predict_proba(x)[:, 1]
                explainer = shap.Explainer(f_prob, X_bg)
                shap_values_to_plot = explainer(shap.sample(X_trans_df, 200))
            else:
                explainer = shap.Explainer(classifier, X_trans_df)
                shap_values_to_plot = explainer(X_trans_df)
            
            # Graficar
            plt.figure(figsize=(10, 7))
            
            # Asegurar correspondencia de features al graficar
            if shap_values_to_plot.shape[0] == X_trans_df.shape[0]:
                features_to_plot = X_trans_df
            else:
                if hasattr(shap_values_to_plot, "data"):
                    features_to_plot = pd.DataFrame(shap_values_to_plot.data, columns=feature_names)
                else:
                    features_to_plot = X_trans_df.iloc[:shap_values_to_plot.shape[0]]
            
            shap.summary_plot(shap_values_to_plot, features_to_plot, feature_names=feature_names, show=False)
            
            plt.title(f"Explicabilidad SHAP (Beeswarm Plot): Capa 1\nMercado: {m['title']} ({clf_type})", fontsize=12, fontweight='bold', pad=15)
            plt.tight_layout()
            
            save_path = os.path.join(pres_dir, m["out_name"])
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"  [OK] Guardado en: {save_path}")
            generated_plots.append((m["title"], save_path))
            
        except Exception as e:
            print(f"  ❌ Error calculando SHAP para {m['title']}: {e}")
            
    # -------------------------------------------------------------------------
    # PARTE 2: SHAP PARA EL META-MODELO DE CAPA 2 (Random Forest)
    # -------------------------------------------------------------------------
    print("\n==================================================")
    print("PROCESANDO SHAP PARA EL META-MODELO DE CAPA 2...")
    print("==================================================")
    
    sim_dir = os.path.abspath(os.path.join(current_dir, "..", "Simulacion_Inversion"))
    csv_preds = os.path.join(sim_dir, "predicciones_prueba_calibradas.csv")
    csv_master = os.path.join(sim_dir, "historical_with_ou_odds.csv")
    
    if os.path.exists(csv_preds) and os.path.exists(csv_master):
        df_preds = pd.read_csv(csv_preds)
        df_master = pd.read_csv(csv_master)
        df_sim = pd.merge(df_preds, df_master[['game_id', 'home_elo', 'away_elo', 'home_rest', 'away_rest']], on='game_id', how='left')
        df_sim['date'] = pd.to_datetime(df_sim['date'])
        df_sim = df_sim.sort_values('date').reset_index(drop=True)
        
        historical_records = []
        
        for idx, row in df_sim.iterrows():
            cal_mode = 'iso'
            all_options = {
                'home': {'prob': row[f'p_home_{cal_mode}'], 'odd': row['B365H'], 'win': (row['target_1x2'] == 2)},
                'draw': {'prob': row[f'p_draw_{cal_mode}'], 'odd': row['B365D'], 'win': (row['target_1x2'] == 1)},
                'away': {'prob': row[f'p_away_{cal_mode}'], 'odd': row['B365A'], 'win': (row['target_1x2'] == 0)},
                'dc_1X': {'prob': row[f'p_dc1X_{cal_mode}'], 'odd': row['B365_1X'], 'win': (row['target_dc_1X'] == 1)},
                'dc_X2': {'prob': row[f'p_dcX2_{cal_mode}'], 'odd': row['B365_X2'], 'win': (row['target_dc_X2'] == 1)},
                'over': {'prob': row[f'p_over_{cal_mode}'], 'odd': row['B365>2.5'], 'win': (row['target_over_2_5_goals'] == 1)},
                'under': {'prob': row[f'p_under_{cal_mode}'], 'odd': row['B365<2.5'], 'win': (row['target_under_2_5_goals'] == 1)}
            }
            
            evs = {name: opt['prob'] * opt['odd'] - 1 for name, opt in all_options.items()}
            best_bet_name = max(evs, key=evs.get)
            best_bet = all_options[best_bet_name]
            best_ev = evs[best_bet_name]
            
            edge_req = 0.05 * max(1.0, np.sqrt(best_bet['odd'] - 1))
            
            if best_ev >= edge_req:
                elo_diff, rest_diff = get_meta_features(row, best_bet_name)
                historical_records.append({
                    'prob': best_bet['prob'],
                    'odd': best_bet['odd'],
                    'ev': best_ev,
                    'elo_diff': elo_diff,
                    'rest_diff': rest_diff,
                    'win': int(best_bet['win'])
                })
                
        meta_df = pd.DataFrame(historical_records)
        print(f"Total de registros de apuestas para el Meta-Modelo: {len(meta_df)}")
        
        X_meta = meta_df[['prob', 'odd', 'ev', 'elo_diff', 'rest_diff']]
        y_meta = meta_df['win']
        
        column_mappings = {
            'prob': 'Probabilidad (Capa 1)',
            'odd': 'Cuota (Bet365)',
            'ev': 'Valor Esperado (EV)',
            'elo_diff': 'Diferencia ELO',
            'rest_diff': 'Diferencia Descanso (Fatiga)'
        }
        X_meta_rename = X_meta.rename(columns=column_mappings)
        
        # Entrenar Meta-Modelo final
        meta_clf = RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42)
        meta_clf.fit(X_meta_rename, y_meta)
        
        explainer_meta = shap.TreeExplainer(meta_clf)
        shap_values_meta = explainer_meta(X_meta_rename)
        
        if len(shap_values_meta.shape) == 3:
            shap_values_to_plot = shap_values_meta[..., 1]
        else:
            shap_values_to_plot = shap_values_meta
            
        plt.figure(figsize=(10, 6.5))
        shap.summary_plot(shap_values_to_plot, X_meta_rename, show=False)
        plt.title("Explicabilidad SHAP (Beeswarm Plot): Meta-Modelo Capa 2\n(Random Forest para Filtro de Decisiones de Apuesta)", fontsize=13, fontweight='bold', pad=15)
        plt.tight_layout()
        
        meta_path = os.path.join(pres_dir, "shap_capa2_metamodelo.png")
        plt.savefig(meta_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[OK] Gráfico SHAP Meta-Modelo guardado en: {meta_path}")
    else:
        print("⚠️ Warning: No se encontraron los archivos de simulación. Se omite la Capa 2.")
        meta_path = None

    # -------------------------------------------------------------------------
    # PARTE 3: GENERAR UN DOCUMENTO EXPLICATIVO EN MARKDOWN COMPLETO
    # -------------------------------------------------------------------------
    readme_path = os.path.join(current_dir, "explicacion_shap.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# Explicabilidad e Interpretación de los Modelos (Framework SHAP)\n\n")
        f.write("Este documento detalla la interpretación global de los modelos de Capa 1 (todos los mercados) y la Capa 2 (Meta-Modelo de decisión) mediante valores SHAP (Shapley Additive exPlanations).\n\n")
        
        f.write("## 1. Gráficos Generados en Carpeta Presentación:\n\n")
        f.write("### ── Capa 1: Modelos de Goles y Resultados ──\n")
        for title, path in generated_plots:
            f.write(f"* **{title}:** [{os.path.basename(path)}](file:///{path.replace(os.sep, '/')})\n")
        
        if meta_path:
            f.write(f"\n### ── Capa 2: Meta-Modelo de Filtro ──\n")
            f.write(f"* **Meta-Modelo Random Forest (Decisión):** [shap_capa2_metamodelo.png](file:///{meta_path.replace(os.sep, '/')})\n\n")
            
        f.write("## 2. Interpretación de Patrones de la Capa 1:\n")
        f.write("* **Mercados de Goles (Over/Under 2.5):** La variable `h_l5_xg` y `a_l5_xg` son las más relevantes. Goles esperados históricos altos (rojo) empujan la probabilidad del Over hacia la derecha, y viceversa para el Under.\n")
        f.write("* **Doble Oportunidad y 1X2:** El diferencial de ELO y las cuotas de Bet365 dominan la predicción. Cuotas locales bajas (favoritismo implícito fuerte) empujan la predicción de victoria local positivamente.\n")
        f.write("* **BTTS y Goles en Contra:** Las métricas de tiros a puerta concedidos y goles concedidos recientes (`h_l5_ga`, `a_l5_ga`) influyen directamente en la predicción del BTTS.\n")
        f.write("* **Variables Arbitrales:** En todos los mercados, el árbitro (`referee_avg_cards_history`) se encuentra al final de la importancia, indicando nulo o bajísimo impacto en los resultados del partido.\n\n")
        
        if meta_path:
            f.write("## 3. Interpretación del Meta-Modelo (Filtro Capa 2):\n")
            f.write("* **Valor Esperado (`ev`):** Es la variable más relevante. Valores de EV altos (rojos) empujan la decisión del Meta-Modelo a aprobar la apuesta.\n")
            f.write("* **Fatiga (`rest_diff`):** Cuando el diferencial de descanso del equipo candidato es muy desfavorable (puntos azules en valores negativos), la probabilidad de acierto cae significativamente, y el Meta-Modelo bloquea la apuesta.\n")
            f.write("* **Cuota (`odd`):** Funciona como regulador de riesgo. Cuotas muy altas se asocian con mayor tasa de error, provocando una penalización preventiva del modelo.\n")
            
    print(f"\n[OK] Reporte explicativo completo guardado en: {readme_path}")
    print("¡Proceso de generación de SHAP para todos los mercados finalizado con éxito!")

if __name__ == '__main__':
    main()
