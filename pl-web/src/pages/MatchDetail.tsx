import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Calendar, MapPin, User, Loader2 } from "lucide-react";
import { matches, getRefereeName } from "@/data/mockData";
import { WinProbabilityBar } from "@/components/WinProbabilityBar";
import { OddsButton } from "@/components/OddsButton";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { useAPIUpcomingMatches, mapAPIUpcomingToMockMatch } from "@/lib/api";
import { EntityLink } from "@/components/EntityLink";
import { TeamLogo } from "@/components/TeamLogo";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const categories = [
  { key: "match-odds", label: "Cuotas" },
  { key: "goals", label: "Goles" },
  { key: "player-props", label: "Especiales Jugador" },
  { key: "cards-corners", label: "Tarjetas y Córners" },
] as const;

const MatchDetail = () => {
  const { id } = useParams();
  
  // Try to find in static/completed matches first
  let match = matches.find((m) => m.id === id);

  // If not found, fetch live upcoming matches
  const { data: upcomingMatches, isLoading } = useAPIUpcomingMatches();

  if (!match && upcomingMatches) {
    const liveMatch = upcomingMatches.find((m) => m.id === id);
    if (liveMatch) {
      match = mapAPIUpcomingToMockMatch(liveMatch);
    }
  }

  if (isLoading && !match) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p>Cargando detalles del partido...</p>
      </div>
    );
  }

  if (!match) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
        <p>Partido no encontrado</p>
        <Link to="/matches" className="mt-2 text-primary hover:underline text-sm">Volver a Partidos</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto animate-fade-in">
      <Link to="/matches" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="h-4 w-4" /> Volver a Partidos
      </Link>

      <div className="glass-card p-6 text-center space-y-4 gradient-blue">
        <div className="flex items-center justify-center gap-8 md:gap-16">
          <EntityLink type="team" id={match.homeTeam.id} className="flex flex-col items-center gap-2 no-underline">
            <TeamLogo name={match.homeTeam.name} colors={match.homeTeam.colors} size="lg" />
            <span className="text-lg font-bold mt-2">{match.homeTeam.name}</span>
          </EntityLink>
          <span className="text-2xl font-bold text-muted-foreground">VS</span>
          <EntityLink type="team" id={match.awayTeam.id} className="flex flex-col items-center gap-2 no-underline">
            <TeamLogo name={match.awayTeam.name} colors={match.awayTeam.colors} size="lg" />
            <span className="text-lg font-bold mt-2">{match.awayTeam.name}</span>
          </EntityLink>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{match.date} · {match.time}</span>
          <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{match.stadium}</span>
          <span className="flex items-center gap-1">
            <User className="h-3 w-3" />
            <EntityLink type="referee" id={match.refereeId}>{getRefereeName(match.refereeId)}</EntityLink>
          </span>
        </div>
        <WinProbabilityBar
          homeWin={match.prediction.homeWin}
          draw={match.prediction.draw}
          awayWin={match.prediction.awayWin}
          homeLabel={match.homeTeam.shortName}
          awayLabel={match.awayTeam.shortName}
        />
      </div>

      <Tabs defaultValue="match-odds" className="w-full">
        <TabsList className="w-full bg-card border border-border grid grid-cols-2 md:grid-cols-4">
          {categories.map((c) => (
            <TabsTrigger key={c.key} value={c.key} className="text-xs data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              {c.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {categories.map((c) => {
          const categoryMarkets = match.markets.filter((m) => m.category === c.key);
          return (
            <TabsContent key={c.key} value={c.key} className="mt-4 space-y-3">
              {categoryMarkets.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">Aún no hay predicciones para este mercado.</p>
              ) : (
                categoryMarkets.map((market, i) => (
                  <div key={i} className="glass-card p-4 flex flex-col sm:flex-row sm:items-center gap-4 justify-between animate-fade-in" style={{ animationDelay: `${i * 80}ms` }}>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-foreground">{market.name}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{market.prediction}</p>
                    </div>
                    <div className="flex items-center gap-3 flex-wrap">
                      <ConfidenceBadge confidence={market.confidence} />
                      {market.edge > 5 && (
                        <span className="inline-flex items-center rounded-full bg-success/15 px-2.5 py-0.5 text-[10px] font-bold text-success border border-success/20">
                          ALTO VALOR
                        </span>
                      )}
                      <OddsButton odds={market.odds} label="Cuota" />
                      <div className="text-center">
                        <span className="text-[10px] uppercase tracking-wider text-muted-foreground block">Justa</span>
                        <span className="text-sm font-semibold text-foreground">{market.fairOdds.toFixed(2)}</span>
                      </div>
                      <div className="text-center">
                        <span className="text-[10px] uppercase tracking-wider text-muted-foreground block">Ventaja</span>
                        <span className={`text-sm font-bold ${market.edge > 5 ? "text-success" : "text-muted-foreground"}`}>
                          +{market.edge.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </TabsContent>
          );
        })}
      </Tabs>
    </div>
  );
};

export default MatchDetail;
