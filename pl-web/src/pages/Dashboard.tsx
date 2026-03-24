import { TrendingUp, Target, Activity, Flame, Loader2, BarChart3, Zap } from "lucide-react";
import { hotPicks } from "@/data/mockData";
import { StatCard } from "@/components/StatCard";
import { MatchCard } from "@/components/MatchCard";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { OddsButton } from "@/components/OddsButton";
import { useAPIStats, useAPIUpcomingMatches, mapAPIUpcomingToMockMatch } from "@/lib/api";

const Dashboard = () => {
  const { data: stats, isLoading: statsLoading } = useAPIStats();
  const { data: matches, isLoading: matchesLoading } = useAPIUpcomingMatches();

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

      {/* Hot Picks */}
      <div className="animate-fade-in" style={{ animationDelay: "100ms" }}>
        <div className="flex items-center gap-2 mb-4">
          <Flame className="h-5 w-5 text-warning" />
          <h2 className="text-lg font-semibold text-foreground tracking-tight">Selecciones Destacadas</h2>
          <span className="text-xs text-muted-foreground">· Las mejores apuestas de hoy</span>
        </div>
        <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
          {hotPicks.map((pick, i) => (
            <div key={i} className="glass-card min-w-[260px] p-4 flex flex-col gap-3 shrink-0 hover:border-primary/20 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">{pick.category.replace("-", " ")}</span>
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
