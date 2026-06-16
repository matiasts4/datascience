import pandas as pd
import numpy as np
import os
import sys
import warnings
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    confusion_matrix, ConfusionMatrixDisplay, classification_report, 
    accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
)

warnings.filterwarnings("ignore")

# Configurar rutas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'archive', 'pl-predictor')))
from src.config import FEATURES_PATH, TARGETS, FEATURES, MODELS_DIR
from evaluar_modelos_optimos import prepare_targets

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pres_dir = os.path.abspath(os.path.join(current_dir, "..", "Carpeta_Presentacion"))
    
    if not os.path.exists(FEATURES_PATH):
        print(f"❌ Error: No se encontró el dataset en {FEATURES_PATH}")
        return
        
    df = pd.read_csv(FEATURES_PATH)
    df = df[df['game_id'].astype(str) != '0'].reset_index(drop=True)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = prepare_targets(df)
    
    X = df[FEATURES]
    tscv = TimeSeriesSplit(n_splits=5)
    
    # Obtener índices del último split (Test Set)
    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        
    print(f"Tamaño del conjunto de Test final: {len(X_test)} muestras")
    
    # Definir modelos a evaluar
    models_config = [
        {
            "file": "model_1X2_Match_Winner.pkl",
            "title": "1X2 (Match Winner)",
            "target": "target_1x2",
            "labels": ["Visitante", "Empate", "Local"],
            "multiclass": True
        },
        {
            "file": "model_Double_Chance_1X_Home_or_Draw.pkl",
            "title": "Double Chance 1X",
            "target": "target_dc_1X",
            "labels": ["Otro", "1X"],
            "multiclass": False
        },
        {
            "file": "model_Double_Chance_X2_Away_or_Draw.pkl",
            "title": "Double Chance X2",
            "target": "target_dc_X2",
            "labels": ["Otro", "X2"],
            "multiclass": False
        },
        {
            "file": "model_Over_2_5_Goals.pkl",
            "title": "Over 2.5 Goals",
            "target": "target_over_2_5_goals",
            "labels": ["Under 2.5", "Over 2.5"],
            "multiclass": False
        },
        {
            "file": "model_Under_2_5_Goals.pkl",
            "title": "Under 2.5 Goals",
            "target": "target_under_2_5_goals",
            "labels": ["Over 2.5", "Under 2.5"],
            "multiclass": False
        },
        {
            "file": "model_BTTS_Both_Teams_To_Score.pkl",
            "title": "BTTS (Both Teams To Score)",
            "target": "target_btts",
            "labels": ["No BTTS", "BTTS"],
            "multiclass": False
        },
        {
            "file": "model_BTTS_-_No.pkl",
            "title": "BTTS - No",
            "target": "target_btts_no",
            "labels": ["BTTS", "No BTTS"],
            "multiclass": False
        },
        {
            "file": "model_Home_Clean_Sheet.pkl",
            "title": "Home Clean Sheet",
            "target": "target_home_clean_sheet",
            "labels": ["Gol Concedido", "Valla Invicta"],
            "multiclass": False
        }
    ]
    
    fig, axes = plt.subplots(4, 2, figsize=(15, 24), dpi=300)
    axes = axes.flatten()
    
    # Estructura del reporte Markdown
    markdown_report = []
    markdown_report.append("# Reporte de Matrices de Confusión y Métricas de Clasificación (Capa 1)\n\n")
    markdown_report.append("Este documento presenta el desglose detallado de las matrices de confusión y métricas asociadas evaluadas sobre el conjunto de test final (último fold de TimeSeriesSplit 5-folds).\n\n")
    
    # Tabla resumen inicial
    markdown_report.append("## Resumen Ejecutivo de Métricas\n\n")
    markdown_report.append("| Mercado | Algoritmo | AUC-ROC | Accuracy | Precision | Recall | F1-Score |\n")
    markdown_report.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
    
    rows_data = []
    detailed_sections = []
    
    for idx, config in enumerate(models_config):
        model_path = os.path.join(MODELS_DIR, config["file"])
        if not os.path.exists(model_path):
            print(f"⚠️ Warning: No se encontró el modelo en {model_path}, se omite.")
            continue
            
        print(f"Evaluando {config['title']}...")
        pipe = joblib.load(model_path)
        classifier = pipe.named_steps['classifier']
        clf_type = type(classifier).__name__
        
        # Obtener valores reales de test para este target
        y_test = df[config["target"]].iloc[test_idx]
        
        # Predecir clases y probabilidades
        y_pred = pipe.predict(X_test)
        y_pred_proba = pipe.predict_proba(X_test)
        
        # Calcular métricas básicas según dimensionalidad
        acc = accuracy_score(y_test, y_pred)
        
        if config["multiclass"]:
            # Multiclase (1X2 Match Winner)
            auc_score = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
            precision = precision_score(y_test, y_pred, average='weighted')
            recall = recall_score(y_test, y_pred, average='weighted')
            f1 = f1_score(y_test, y_pred, average='weighted')
        else:
            # Binarios
            # Probabilidad de la clase 1 (positiva)
            y_pred_proba_pos = y_pred_proba[:, 1]
            auc_score = roc_auc_score(y_test, y_pred_proba_pos)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
        # Generar classification report en texto
        cls_report_str = classification_report(y_test, y_pred, target_names=config["labels"], zero_division=0)
        
        # Agregar fila a la tabla resumen
        markdown_report.append(f"| {config['title']} | {clf_type} | {auc_score:.4f} | {acc:.4f} | {precision:.4f} | {recall:.4f} | {f1:.4f} |\n")
        
        # Calcular matriz de confusión para graficar
        cm = confusion_matrix(y_test, y_pred)
        
        # Estructurar la sección de desglose detallado
        detailed_sections.append(f"\n---\n\n## Detalle de Clasificación: {config['title']}\n")
        detailed_sections.append(f"* **Algoritmo:** `{clf_type}`\n")
        detailed_sections.append(f"* **Métricas Generales:**\n")
        detailed_sections.append(f"  * **AUC-ROC:** `{auc_score:.4f}`\n")
        detailed_sections.append(f"  * **Accuracy:** `{acc:.4f}`\n")
        detailed_sections.append(f"  * **Precision:** `{precision:.4f}`\n")
        detailed_sections.append(f"  * **Recall:** `{recall:.4f}`\n")
        detailed_sections.append(f"  * **F1-Score:** `{f1:.4f}`\n\n")
        
        # Desglosar matriz en texto si es binaria
        if not config["multiclass"]:
            tn, fp, fn, vp = cm.ravel()
            detailed_sections.append(f"* **Matriz de Confusión (Desglose):**\n")
            detailed_sections.append(f"  * Verdaderos Negativos (TN): `{tn}`\n")
            detailed_sections.append(f"  * Falsos Positivos (FP - Apuestas Perdidas): `{fp}`\n")
            detailed_sections.append(f"  * Falsos Negativos (FN): `{fn}`\n")
            detailed_sections.append(f"  * Verdaderos Positivos (VP - Apuestas Ganadas): `{vp}`\n\n")
            
        detailed_sections.append("### Classification Report Completo:\n")
        detailed_sections.append("```\n")
        detailed_sections.append(cls_report_str)
        detailed_sections.append("```\n")
            
        # Graficar en el subplot correspondiente
        ax = axes[idx]
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=config["labels"])
        cmap = plt.cm.Greens if "Goals" in config["title"] or "BTTS" in config["title"] else plt.cm.Blues
        
        disp.plot(ax=ax, cmap=cmap, values_format='d', colorbar=False)
        ax.set_title(f"{config['title']}\n({clf_type})", fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel('Predicción del Modelo', fontweight='bold', fontsize=10)
        ax.set_ylabel('Resultado Real', fontweight='bold', fontsize=10)
        
    plt.suptitle("Matrices de Confusión de los 8 Modelos de Producción de Capa 1\n(Evaluados en el Conjunto de Test Final)", fontsize=16, fontweight='bold', y=0.99)
    plt.tight_layout()
    plt.subplots_adjust(top=0.96)
    
    save_path = os.path.join(pres_dir, "52_Matrices_Confusion_Capa1.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Unir la tabla resumen con las secciones detalladas
    markdown_report.extend(detailed_sections)
    
    # Escribir reporte markdown completo
    report_path = os.path.join(current_dir, "matrices_confusion_reporte.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.writelines(markdown_report)
        
    print(f"\n[OK] Gráfico combinado guardado en: {save_path}")
    print(f"[OK] Reporte Markdown detallado guardado en: {report_path}")

if __name__ == '__main__':
    main()
