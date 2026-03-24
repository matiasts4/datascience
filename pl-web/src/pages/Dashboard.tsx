import { TrendingUp, Target, Activity, Flame, Loader2, BarChart3, Zap } from "lucide-react";
import { StatCard } from "@/components/StatCard";
import { MatchCard } from "@/components/MatchCard";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { OddsButton } from "@/components/OddsButton";
import { useAPIStats, useAPIUpcomingMatches, mapAPIUpcomingToMockMatch, APIUpcomingResponse } from "@/lib/api";
import { MarketPrediction } from "@/data/mockData";

// Fallback hot picks — only valid market categories, no player-specific props
const FALLBACK_HOT_PICKS: MarketPrediction[] = [
  { category: "match-odds", name: "Ganador del Partido (1X2)", prediction: "Datos del scraper cargando…", odds: 2.10, fairOdds: 2.00, confidence: 72, edge: 5.0 },
  { category: "goals", name: "Más de 2.5 Goles", prediction: "Mercado de goles predefinido", odds: 1.85, fairOdds: 1.72, confidence: 76, edge: 7.6 },
  { category: "goals", name: "Ambos Marcan (Sí)", prediction: "Mercado BTTS predefinido", odds: 1.72, fairOdds: 1.65, confidence: 74, edge: 5.8 },
  { category: "match-odds", name: "Doble Oportunidad (1X)", prediction: "Local o Empate", odds: 1.45, fairOdds: 1.38, confidence: 80, edge: 5.1 },
  { category: "cards-corners", name: "Total Tarjetas Más 3.5", prediction: "Mercado de tarjetas predefinido", odds: 1.80, fairOdds: 1.70, confidence: 70, edge: 5.9 },
];

// Map API market name to frontend category
function marketToCategory(market: string): MarketPrediction["category"] {
  const m = market.toLowerCase();
  if (m.includes("1x2") || m.includes("winner") || m.includes("double chance") || m.includes("clean sheet")) return "match-odds";
  if (m.includes("goal") || m.includes("btts") || m.includes("over") || m.includes("under")) return "goals";
  if (m.includes("card") || m.includes("corner") || m.includes("foul")) return "cards-corners";
  return "match-odds";
}

// Build hot picks from real upcoming match API data
function buildHotPicksFromAPI(matches: APIUpcomingResponse[]): MarketPrediction[] {
  const picks: MarketPrediction[] = [];

  for (const m of matches) {
    if (!m.topPrediction) continue;
    const prob = m.topPrediction.Probability;
    const fairOdds = prob > 0 ? 1 / prob : 2.0;
    const bookieOdds = Math.round(Math.max(1.01, fairOdds * 0.95) * 100) / 100;
    const edge = Math.round(((1 / bookieOdds - (1 - prob)) * 100) * 10) / 10;

    picks.push({
      category: marketToCategory(m.topPrediction.Market),
      name: m.topPrediction.Market,
      prediction: `${m.homeTeam} vs ${m.awayTeam}`,
      odds: bookieOdds,
      fairOdds: Math.round(fairOdds * 100) / 100,
      confidence: Math.round(prob * 100),
      edge: Math.max(0, edge),
    });

    if (picks.length >= 5) break;
  }

  return picks.length > 0 ? picks : FALLBACK_HOT_PICKS;
}

const Dashboard = () => {
  const { data: stats, isLoading: statsLoading } = useAPIStats();
  const { data: matches, isLoading: matchesLoading } = useAPIUpcomingMatches();

  const hotPicks = matches && matches.length > 0
    ? buildHotPicksFromAPI(matches)
    : FALLBACK_HOT_PICKS;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Hero Stats */}
      <div className="animate-fade-in">
        <h1 className="text-2xl font-bold text-foreground mb-1 tracking-tight">Panel de Control</h1>
        <p className="text-sm text-muted-foreground mb-6">Insights de apuestas de la Premier League con IA</p>
        {statsLoading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="glass-card p-4 h-24 flex items-center justify-center">
                <Loader2 className="h-5 w-5 animate-spin text-primary opacity-50" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <StatCard
              label="TASA DE ACIERTO"
              value={stats ? `${stats.accuracy_pct.toFixed(1)}%` : "—"}
              change="Modelo ML real"
              icon={Target}
              positive
            />
            <StatCard
              label="MERCADOS ACTIVOS"
              value={stats ? stats.markets_tracked.toString() : "—"}
              change="Mercados evaluados"
              icon={Zap}
            />
            <StatCard
              label="PARTIDOS TOTALES"
              value={stats ? stats.totalMatches.toLocaleString() : "—"}
              change="En la base histórica"
              icon={Activity}
              positive
            />
            <StatCard
              label="TEMPORADAS"
              value={stats ? stats.seasons.toString() : "—"}
              change="Temporadas de la PL"
              icon={TrendingUp}
              positive
            />
          </div>
        )}
      </div>

      {/* Hot Picks — derived from real upcoming match predictions */}
      <div className="animate-fade-in" style={{ animationDelay: "100ms" }}>
        <div className="flex items-center gap-2 mb-4">
          <Flame className="h-5 w-5 text-warning" />
          <h2 className="text-lg font-semibold text-foreground tracking-tight">Selecciones Destacadas</h2>
          <span className="text-xs text-muted-foreground">
            · {matches && matches.length > 0 ? "Generadas desde partidos reales" : "Las mejores apuestas de hoy"}
          </span>
        </div>
        <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
          {hotPicks.map((pick, i) => (
            <div key={i} className="glass-card min-w-[260px] p-4 flex flex-col gap-3 shrink-0 hover:border-primary/20 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">{pick.category.replace(/-/g, " ")}</span>
                <ConfidenceBadge confidence={pick.confidence} />
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">{pick.name}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{pick.prediction}</p>
              </div>
              <div className="flex items-center justify-between mt-auto">
                <OddsButton odds={pick.odds} edge={pick.edge} />
                <div className="text-right">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Ventaja</p>
                  <p className="text-sm font-bold mono text-success">+{pick.edge.toFixed(1)}%</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Upcoming Matches */}
      <div className="animate-fade-in" style={{ animationDelay: "200ms" }}>
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground tracking-tight">Próximos Partidos</h2>
          {matches && (
            <span className="text-xs text-muted-foreground ml-auto">
              {matches.length} partido{matches.length !== 1 ? "s" : ""} encontrado{matches.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
        {matchesLoading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : matches && matches.length > 0 ? (
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {matches.slice(0, 9).map((m) => (
              <MatchCard key={m.id} match={mapAPIUpcomingToMockMatch(m)} />
            ))}
          </div>
        ) : (
          <div className="glass-card p-10 flex flex-col items-center justify-center text-center text-muted-foreground gap-2">
            <BarChart3 className="h-10 w-10 opacity-20 mb-1" />
            <p className="text-sm font-medium">No hay partidos próximos disponibles</p>
            <p className="text-xs opacity-60">El scraper no encontró fixtures en los próximos 30 días</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
