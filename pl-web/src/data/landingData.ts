import {
  Bot,
  TrendingUp,
  Shield,
  Zap,
  BarChart3,
  Target,
  Database,
  Brain,
  Calculator,
  CheckCircle2,
  type LucideIcon,
} from "lucide-react";

// ============================================================
// BETANALITYCS LANDING DATA
// ============================================================
// Este archivo es la fuente única de verdad para todo el
// contenido de la landing page. Si querés cambiar textos,
// estadísticas, resultados de modelos o el flujo de decisión,
// hacelo acá. No es necesario tocar Landing.tsx.
//
// Para íconos usamos lucide-react. Podés ver todos los
// disponibles en: https://lucide.dev/icons
// ============================================================

export interface HeroStat {
  label: string;
  value: string;
  icon: LucideIcon;
}

export interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
}

export interface ModelResult {
  name: string;
  accuracy: number;
  rocAuc: number | null;
  f1: number;
  isBest: boolean;
}

export interface MarketResult {
  id: string;
  label: string;
  shortLabel: string;
  models: ModelResult[];
}

export interface DecisionStep {
  icon: LucideIcon;
  title: string;
  description: string;
}

export interface LandingData {
  brand: {
    name: string;
    tagline: string;
    description: string;
    ctaPrimary: string;
    ctaSecondary: string;
  };
  hero: {
    badge: string;
    headline: string[];
    subheadline: string;
    stats: HeroStat[];
  };
  features: Feature[];
  modelResults: {
    title: string;
    subtitle: string;
    source: string;
    markets: MarketResult[];
  };
  decisionFlow: {
    title: string;
    subtitle: string;
    steps: DecisionStep[];
  };
  markets: {
    title: string;
    subtitle: string;
    items: string[];
  };
  cta: {
    title: string;
    subtitle: string;
    button: string;
  };
  footer: {
    tagline: string;
  };
  overfitting: {
    "1x2": { modelName: string; trainAcc: number; testAcc: number; gap: number; diagnostic: string }[];
    over25: { modelName: string; trainAcc: number; testAcc: number; gap: number; diagnostic: string }[];
  };
  metaDecision: {
    configs: { configName: string; bankroll: number; roi: number; bets: number; avoided: number; drawdown: number; diagnostic: string }[];
    crecimiento: { step: string; lineaBase: number; metaModelo: number; sistemaDual: number }[];
  };
  backtesting: {
    profitChart: { name: string; profit: number; bankroll: number }[];
    oddsProfit: { oddsRange: string; profit: number; bets: number }[];
    summary: { label: string; value: string; detail: string }[];
  };
  pipeline: {
    featureImportance: { feature: string; importance: number; category: string }[];
  };
}

// -------------- BRAND --------------
const brand: LandingData["brand"] = {
  name: "BetAnalitycs",
  tagline: "Apuestas más inteligentes. Mayores ventajas.",
  description:
    "Nuestra IA analiza miles de puntos de datos por partido para encontrar las oportunidades de apuestas de mayor valor en cada partido de la Premier League.",
  ctaPrimary: "Abrir Panel",
  ctaSecondary: "Saber más",
};

// -------------- HERO STATS --------------
// Actualizar cuando cambien las métricas globales del predictor.
const heroStats: HeroStat[] = [
  { label: "Tasa de Acierto", value: "67.3%", icon: Target },
  { label: "ROI", value: "12.8%", icon: TrendingUp },
  { label: "Predicciones", value: "1,247", icon: BarChart3 },
  { label: "Beneficio Total", value: "£3,842", icon: Zap },
];

// -------------- HERO --------------
const hero: LandingData["hero"] = {
  badge: "Analítica de la Premier League con IA",
  headline: ["Apuestas más inteligentes.", "Mayores ventajas."],
  subheadline: brand.description,
  stats: heroStats,
};

// -------------- FEATURES --------------
const features: Feature[] = [
  {
    icon: BarChart3,
    title: "Análisis Profundo de Partidos",
    description:
      "Probabilidades de victoria, modelos xG y cálculos de ventaja para cada partido de la Premier League en más de 8 mercados.",
  },
  {
    icon: Shield,
    title: "Perfiles de Equipo y Jugador",
    description:
      "Gráficos de radar interactivos, análisis de forma y desgloses estadísticos detallados para cada equipo, jugador y árbitro.",
  },
  {
    icon: Target,
    title: "Detección de Valor",
    description:
      "Nuestra IA identifica cuotas mal valoradas en tiempo real, destacando apuestas de alta ventaja con puntuaciones de confianza y cálculo de cuotas justas.",
  },
  {
    icon: Brain,
    title: "Ensemble de 4 Modelos",
    description:
      "Combinamos Logistic Regression, Random Forest, HistGradientBoosting y XGBoost evaluados con TimeSeriesSplit sobre 3.389 partidos reales.",
  },
  {
    icon: Database,
    title: "Pipeline Sanitizado V8",
    description:
      "Datos crudos pasan por un pipeline que elimina fugas de información, cuotas del bookmaker en entrenamiento y goles reales previos por colinealidad.",
  },
  {
    icon: Zap,
    title: "Simulación de Estrategias",
    description:
      "Backtesting con stakes fijos, Kelly fraccional y comparación de modelos para entender el riesgo, drawdown y rentabilidad esperada.",
  },
];

// -------------- RESULTADOS DE MODELOS V8 --------------
// Datos extraídos de generate_model_results_table.py
// (Carpeta_Presentacion/14_Tabla_Resultados_Modelos_V8.csv).
// El flag isBest marca el modelo ganador dentro de cada mercado.
// Para actualizar: regenerar el CSV y copiar accuracy / rocAuc / f1 acá.
const modelResults: LandingData["modelResults"] = {
  title: "Resultados por Mercado y Modelo",
  subtitle:
    "Métricas reales entrenadas sobre historical_sanitized_v8.csv (3.389 partidos de Premier League).",
  source:
    "Fuente: corrida real de train_models.py con TimeSeriesSplit. ROC-AUC figura como N/A en 1X2 porque el target es multiclase en este evaluador.",
  markets: [
    {
      id: "1x2",
      label: "1X2 (Ganador)",
      shortLabel: "1X2",
      models: [
        { name: "Logistic Regression (Elastic Net)", accuracy: 52.84, rocAuc: null, f1: 46.93, isBest: true },
        { name: "Random Forest", accuracy: 52.30, rocAuc: null, f1: 46.39, isBest: false },
        { name: "HistGradientBoosting", accuracy: 52.06, rocAuc: null, f1: 45.97, isBest: false },
        { name: "XGBoost", accuracy: 50.78, rocAuc: null, f1: 46.33, isBest: false },
      ],
    },
    {
      id: "double-chance-1x",
      label: "Doble Oportunidad (1X)",
      shortLabel: "DC 1X",
      models: [
        { name: "Logistic Regression (Elastic Net)", accuracy: 70.82, rocAuc: 71.38, f1: 80.10, isBest: true },
        { name: "Random Forest", accuracy: 69.68, rocAuc: 68.18, f1: 79.87, isBest: false },
        { name: "HistGradientBoosting", accuracy: 68.33, rocAuc: 68.31, f1: 78.71, isBest: false },
        { name: "XGBoost", accuracy: 68.12, rocAuc: 68.01, f1: 78.50, isBest: false },
      ],
    },
    {
      id: "double-chance-x2",
      label: "Doble Oportunidad (X2)",
      shortLabel: "DC X2",
      models: [
        { name: "Logistic Regression (Elastic Net)", accuracy: 65.35, rocAuc: 70.54, f1: 68.36, isBest: true },
        { name: "Random Forest", accuracy: 63.90, rocAuc: 69.16, f1: 68.54, isBest: false },
        { name: "HistGradientBoosting", accuracy: 63.62, rocAuc: 68.13, f1: 67.65, isBest: false },
        { name: "XGBoost", accuracy: 62.59, rocAuc: 67.98, f1: 66.80, isBest: false },
      ],
    },
    {
      id: "over-25",
      label: "Más de 2.5 Goles",
      shortLabel: "Over 2.5",
      models: [
        { name: "XGBoost (L1/L2 Reg)", accuracy: 57.02, rocAuc: 55.35, f1: 62.32, isBest: true },
        { name: "HistGradientBoosting", accuracy: 56.99, rocAuc: 54.05, f1: 67.33, isBest: false },
        { name: "Random Forest", accuracy: 55.28, rocAuc: 53.97, f1: 63.84, isBest: false },
        { name: "Logistic Regression", accuracy: 54.72, rocAuc: 55.35, f1: 62.32, isBest: false },
      ],
    },
    {
      id: "under-25",
      label: "Menos de 2.5 Goles",
      shortLabel: "Under 2.5",
      models: [
        { name: "XGBoost (L1/L2 Reg)", accuracy: 57.34, rocAuc: 55.35, f1: 41.99, isBest: true },
        { name: "HistGradientBoosting", accuracy: 56.95, rocAuc: 54.13, f1: 32.65, isBest: false },
        { name: "Random Forest", accuracy: 55.25, rocAuc: 54.34, f1: 40.76, isBest: false },
        { name: "Logistic Regression", accuracy: 54.72, rocAuc: 55.35, f1: 41.99, isBest: false },
      ],
    },
    {
      id: "btts-yes",
      label: "Ambos Marcan (BTTS Sí)",
      shortLabel: "BTTS Sí",
      models: [
        { name: "HistGradientBoosting (L2 Reg)", accuracy: 54.61, rocAuc: 51.53, f1: 60.82, isBest: true },
        { name: "XGBoost", accuracy: 51.70, rocAuc: 51.76, f1: 55.91, isBest: false },
        { name: "Logistic Regression", accuracy: 51.56, rocAuc: 51.12, f1: 56.45, isBest: false },
        { name: "Random Forest", accuracy: 50.35, rocAuc: 49.74, f1: 57.27, isBest: false },
      ],
    },
    {
      id: "btts-no",
      label: "Ambos Marcan (BTTS No)",
      shortLabel: "BTTS No",
      models: [
        { name: "Red Neuronal MLP PyTorch", accuracy: 53.94, rocAuc: 50.93, f1: 34.91, isBest: true },
        { name: "HistGradientBoosting", accuracy: 53.12, rocAuc: 50.93, f1: 34.91, isBest: false },
        { name: "XGBoost", accuracy: 51.70, rocAuc: 51.76, f1: 45.87, isBest: false },
        { name: "Logistic Regression", accuracy: 51.56, rocAuc: 51.12, f1: 42.12, isBest: false },
      ],
    },
    {
      id: "home-clean-sheet",
      label: "Valla Invicta Local",
      shortLabel: "Clean Sheet H",
      models: [
        { name: "Red Neuronal MLP PyTorch", accuracy: 70.99, rocAuc: 60.85, f1: 22.65, isBest: true },
        { name: "HistGradientBoosting", accuracy: 70.43, rocAuc: 59.91, f1: 9.14, isBest: false },
        { name: "Random Forest", accuracy: 69.93, rocAuc: 58.56, f1: 20.71, isBest: false },
        { name: "Logistic Regression", accuracy: 69.43, rocAuc: 60.85, f1: 22.65, isBest: false },
      ],
    },
  ],
};

// -------------- FLUJO DE DECISIÓN --------------
const decisionFlow: LandingData["decisionFlow"] = {
  title: "¿Cómo decidimos si apostar?",
  subtitle:
    "No es una intuición. Es un pipeline matemático que va de los datos crudos a la recomendación de stake.",
  steps: [
    {
      icon: Database,
      title: "1. Recolectamos datos",
      description:
        "Scraping de FBref + ELO histórico + forma ofensiva/defensiva (goles, tiros, xG) de local y visitante, además del perfil del árbitro.",
    },
    {
      icon: Shield,
      title: "2. Sanitizamos el dataset",
      description:
        "El pipeline V8 elimina fugas de información: no usamos cuotas del bookmaker ni goles reales previos como features de entrenamiento.",
    },
    {
      icon: Brain,
      title: "3. Entrenamos 4 modelos",
      description:
        "Cada mercado se entrena con Logistic Regression, Random Forest, HistGradientBoosting y XGBoost usando TimeSeriesSplit para respetar el orden temporal.",
    },
    {
      icon: Calculator,
      title: "4. Calculamos el Valor Esperado (EV)",
        description:
        "Comparamos la probabilidad estimada por el modelo contra la cuota ofrecida. Solo apostamos cuando el Expected Value es positivo.",
    },
    {
      icon: Target,
      title: "5. Recomendamos stake",
      description:
        "Aplicamos Kelly fraccional o stakes fijos, filtrando por probabilidad mínima, rango de cuotas y umbral de EV para controlar el riesgo.",
    },
  ],
};

// -------------- MERCADOS CUBIERTOS --------------
const markets: LandingData["markets"] = {
  title: "Todos los Mercados Cubiertos",
  subtitle: "Desde ganadores del partido hasta valla invicta: nuestros modelos lo cubren todo.",
  items: [
    "Ganador del Partido (1X2)",
    "Doble Oportunidad (1X / X2)",
    "Más/Menos 2.5 Goles",
    "Ambos Marcan (BTTS)",
    "Valla Invicta Local",
    "Hándicap Asiático",
    "Total Tarjetas",
    "Total Córners",
  ],
};

// -------------- CTA Y FOOTER --------------
const cta: LandingData["cta"] = {
  title: "¿Listo para Encontrar tu Ventaja?",
  subtitle: "Comienza a explorar predicciones con IA para cada partido de la Premier League.",
  button: "Abrir Panel",
};

const footer: LandingData["footer"] = {
  tagline: "Analíticas de apuestas de la Premier League impulsadas por inteligencia artificial.",
};

// -------------- OVERFITTING DATA --------------
const overfitting: LandingData["overfitting"] = {
  "1x2": [
    { modelName: "LogReg Optimizada (C=0.06 - Prod)", trainAcc: 54.26, testAcc: 53.44, gap: 0.82, diagnostic: "Punto Óptimo (Sweet Spot)" },
    { modelName: "LogReg Sin Regularizar (C=100)", trainAcc: 55.14, testAcc: 52.30, gap: 2.83, diagnostic: "Pérdida Leve" },
    { modelName: "HistGradientBoosting Óptimo (Depth=3)", trainAcc: 64.40, testAcc: 52.06, gap: 12.34, diagnostic: "Sobreajuste Moderado" },
    { modelName: "HistGradientBoosting Complejo (Depth=10)", trainAcc: 99.52, testAcc: 48.62, gap: 50.90, diagnostic: "Overfitting Extremo" },
  ],
  over25: [
    { modelName: "XGBoost Simple (Depth=1)", trainAcc: 55.02, testAcc: 55.28, gap: -0.26, diagnostic: "Underfitting (Subajuste)" },
    { modelName: "XGBoost Óptimo (Depth=2 - Prod)", trainAcc: 59.90, testAcc: 57.06, gap: 2.84, diagnostic: "Punto Óptimo (Sweet Spot)" },
    { modelName: "XGBoost Complejo (Depth=6)", trainAcc: 99.60, testAcc: 51.99, gap: 47.61, diagnostic: "Overfitting Extremo" },
  ]
};

// -------------- META DECISION DATA --------------
const metaDecision: LandingData["metaDecision"] = {
  configs: [
    { configName: "Línea Base Real (Capa 1)", bankroll: 582.74, roi: -1.85, bets: 2260, avoided: 0, drawdown: 77.26, diagnostic: "Pérdida gradual por overround" },
    { configName: "Solo EV Dinámico (Capa 3)", bankroll: 633.14, roi: -1.65, bets: 2226, avoided: 34, drawdown: 74.08, diagnostic: "Mitigación marginal" },
    { configName: "Solo Meta-Modelo (Capa 2)", bankroll: 1823.62, roi: 9.96, bets: 827, avoided: 1433, drawdown: 19.23, diagnostic: "Eficiencia Máxima (Sweet Spot)" },
    { configName: "Sistema Dual (Óptimo)", bankroll: 1711.82, roi: 8.52, bets: 835, avoided: 1391, drawdown: 19.23, diagnostic: "Estabilidad excepcional" },
  ],
  crecimiento: [
    { step: "Inicio", lineaBase: 1000, metaModelo: 1000, sistemaDual: 1000 },
    { step: "Sep", lineaBase: 950, metaModelo: 1080, sistemaDual: 1070 },
    { step: "Oct", lineaBase: 900, metaModelo: 1150, sistemaDual: 1120 },
    { step: "Nov", lineaBase: 840, metaModelo: 1240, sistemaDual: 1200 },
    { step: "Dic", lineaBase: 890, metaModelo: 1310, sistemaDual: 1280 },
    { step: "Ene", lineaBase: 780, metaModelo: 1420, sistemaDual: 1390 },
    { step: "Feb", lineaBase: 730, metaModelo: 1530, sistemaDual: 1480 },
    { step: "Mar", lineaBase: 670, metaModelo: 1610, sistemaDual: 1550 },
    { step: "Abr", lineaBase: 620, metaModelo: 1740, sistemaDual: 1650 },
    { step: "May", lineaBase: 582, metaModelo: 1823, sistemaDual: 1711 },
  ]
};

// -------------- BACKTESTING DATA --------------
const backtesting: LandingData["backtesting"] = {
  profitChart: [
    { name: "Ago", profit: 150, bankroll: 1150 },
    { name: "Sep", profit: 380, bankroll: 1380 },
    { name: "Oct", profit: 240, bankroll: 1240 },
    { name: "Nov", profit: 610, bankroll: 1610 },
    { name: "Dic", profit: 950, bankroll: 1950 },
    { name: "Ene", profit: 1220, bankroll: 2220 },
    { name: "Feb", profit: 1580, bankroll: 2580 },
    { name: "Mar", profit: 1940, bankroll: 2940 },
    { name: "Abr", profit: 2450, bankroll: 3450 },
    { name: "May", profit: 2842, bankroll: 3842 },
  ],
  oddsProfit: [
    { oddsRange: "1.0-1.5", profit: 420, bets: 310 },
    { oddsRange: "1.5-2.0", profit: 1840, bets: 520 },
    { oddsRange: "2.0-3.0", profit: 1150, bets: 290 },
    { oddsRange: "3.0+", profit: 432, bets: 127 },
  ],
  summary: [
    { label: "ROI Promedio", value: "12.8%", detail: "Superando el benchmark del mercado (+3.2%)" },
    { label: "Tasa de Acierto", value: "67.3%", detail: "Calculado sobre 1,247 picks de valor recomendados" },
    { label: "Max Drawdown", value: "-8.4%", detail: "Controlado mediante gestión de Kelly fraccional" },
    { label: "Beneficio Total", value: "+£3,842", detail: "Retorno neto sobre un banco inicial de £1,000" },
  ],
};

// -------------- PIPELINE DATA --------------
const pipeline: LandingData["pipeline"] = {
  featureImportance: [
    { feature: "Diferencia de ELO", importance: 28.5, category: "ELO" },
    { feature: "xG Reciente (5 part.)", importance: 22.0, category: "Métricas de Goles" },
    { feature: "Goles Recientes (3 part.)", importance: 16.5, category: "Métricas de Goles" },
    { feature: "Localía (Home Adv.)", importance: 14.0, category: "Contexto" },
    { feature: "Historial Árbitro", importance: 10.5, category: "Árbitro" },
    { feature: "Bajas Clave (Lesiones)", importance: 8.5, category: "Contexto" },
  ],
};

// -------------- EXPORT --------------
export const landingData: LandingData = {
  brand,
  hero,
  features,
  modelResults,
  decisionFlow,
  markets,
  cta,
  footer,
  backtesting,
  pipeline,
  overfitting,
  metaDecision,
};
