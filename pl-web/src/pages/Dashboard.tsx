import { TrendingUp, Target, DollarSign, Zap, Flame, Loader2 } from "lucide-react";
import { hotPicks, teamsData, botStats } from "@/data/mockData";
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
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatCard 
            label="TASA DE ACIERTO" 
            value={`${botStats.winRate}%`} 
            change="+2.1% esta s." icon={Target} positive 
          />
          <StatCard 
            label="ROI" 
            value={`${botStats.roi}%`} 
            change="+1.4%" icon={TrendingUp} positive 
          />
          <StatCard 
            label="BENEFICIO TOTAL" 
            value={`£${botStats.totalProfit}`} 
            change="+£73 hoy" icon={DollarSign} positive 
          />
          <StatCard 
            label="RACHA GANADORA" 
            value={botStats.streak.toString()} 
            icon={Zap} 
          />
        </div>
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

      {/* Recent Matches */}
      <div className="animate-fade-in" style={{ animationDelay: "200ms" }}>
        <h2 className="text-lg font-semibold text-foreground mb-4 tracking-tight">Próximos Partidos</h2>
        {matchesLoading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {matches?.slice(0, 9).map((m) => (
              <MatchCard key={m.id} match={mapAPIUpcomingToMockMatch(m)} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
