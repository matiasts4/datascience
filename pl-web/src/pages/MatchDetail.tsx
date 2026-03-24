import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Calendar, MapPin, User, Loader2, Shield, Target, CreditCard, TrendingUp } from "lucide-react";
import { matches, getRefereeName } from "@/data/mockData";
import { WinProbabilityBar } from "@/components/WinProbabilityBar";
import { OddsButton } from "@/components/OddsButton";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { useAPIUpcomingMatches, mapAPIUpcomingToMockMatch, useAPIMatches, mapAPIMatchToMockMatch } from "@/lib/api";
import { EntityLink } from "@/components/EntityLink";
import { TeamLogo } from "@/components/TeamLogo";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

const predictionCategories = [
  { key: "match-odds", label: "Cuotas" },
  { key: "goals", label: "Goles" },
  { key: "player-props", label: "Especiales" },
  { key: "cards-corners", label: "Tarjetas" },
] as const;

const MatchDetail = () => {
  const { id } = useParams();

  let match = matches.find((m) => m.id === id);

  const { data: upcomingMatches, isLoading: upcomingLoading } = useAPIUpcomingMatches();
  const { data: recentAPIMatches, isLoading: recentLoading } = useAPIMatches();
  const isLoading = upcomingLoading || recentLoading;

  if (!match && upcomingMatches) {
    const liveMatch = upcomingMatches.find((m) => m.id === id);
    if (liveMatch) match = mapAPIUpcomingToMockMatch(liveMatch);
  }

  if (!match && recentAPIMatches) {
    const historical = recentAPIMatches.find((m) => m.id === id);
    if (historical) match = mapAPIMatchToMockMatch(historical);
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

  const isCompleted = match.status === "completed";
  const homeWon = match.score && match.score.home > match.score.away;
  const awayWon = match.score && match.score.away > match.score.home;
  const isDraw  = match.score && match.score.home === match.score.away;

  // Find the total cards market entry
  const cardsMarket = match.markets.find((m: any) => m.category === "cards-corners");
  const goalsTotal = match.score ? match.score.home + match.score.away : null;
  const btts = match.score ? match.score.home > 0 && match.score.away > 0 : false;

  return (
    <div className="space-y-6 max-w-4xl mx-auto animate-fade-in">
      <Link to="/matches" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="h-4 w-4" /> Volver a Partidos
      </Link>

      {/* Header card — teams + score/vs */}
      <div className="glass-card p-6 text-center space-y-4 gradient-blue">
        <div className="flex items-center justify-center gap-8 md:gap-16">
          <EntityLink type="team" id={match.homeTeam.id} className="flex flex-col items-center gap-2 no-underline">
            <TeamLogo name={match.homeTeam.name} colors={match.homeTeam.colors} size="lg" />
            <span className={cn("text-lg font-bold mt-2", homeWon && "text-success")}>{match.homeTeam.name}</span>
          </EntityLink>

          {/* Score or VS */}
          <div className="flex flex-col items-center gap-1">
            {isCompleted && match.score ? (
              <>
                <div className="flex items-center gap-3">
                  <span className={cn("text-5xl font-black mono", homeWon ? "text-success" : "text-foreground")}>{match.score.home}</span>
                  <span className="text-2xl text-muted-foreground font-light">–</span>
                  <span className={cn("text-5xl font-black mono", awayWon ? "text-success" : "text-foreground")}>{match.score.away}</span>
                </div>
                <span className={cn(
                  "text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full mt-1",
                  homeWon ? "bg-success/15 text-success" :
                  awayWon ? "bg-info/15 text-info" :
                  "bg-warning/15 text-warning"
                )}>
                  {homeWon ? `Gana ${match.homeTeam.shortName}` : awayWon ? `Gana ${match.awayTeam.shortName}` : "Empate"}
                </span>
                <span className="text-[10px] text-muted-foreground mt-0.5">Partido Finalizado</span>
              </>
            ) : (
              <span className="text-2xl font-bold text-muted-foreground">VS</span>
            )}
          </div>

          <EntityLink type="team" id={match.awayTeam.id} className="flex flex-col items-center gap-2 no-underline">
            <TeamLogo name={match.awayTeam.name} colors={match.awayTeam.colors} size="lg" />
            <span className={cn("text-lg font-bold mt-2", awayWon && "text-success")}>{match.awayTeam.name}</span>
          </EntityLink>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{match.date} · {match.time}</span>
          <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{match.stadium}</span>
          {match.refereeId && match.refereeId !== "tbd" && (
            <span className="flex items-center gap-1">
              <User className="h-3 w-3" />
              <EntityLink type="referee" id={match.refereeId}>{getRefereeName(match.refereeId)}</EntityLink>
            </span>
          )}
        </div>

        {/* Win probability bar — only for upcoming */}
        {!isCompleted && (
          <WinProbabilityBar
            homeWin={match.prediction.homeWin}
            draw={match.prediction.draw}
            awayWin={match.prediction.awayWin}
            homeLabel={match.homeTeam.shortName}
            awayLabel={match.awayTeam.shortName}
          />
        )}
      </div>

      {/* COMPLETED MATCH: show real stats grid */}
      {isCompleted && match.score && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="glass-card p-4 text-center">
            <Target className="h-5 w-5 text-primary mx-auto mb-2" />
            <p className="text-2xl font-black mono text-foreground">{goalsTotal}</p>
            <p className="text-[11px] text-muted-foreground uppercase tracking-wide mt-1">Total Goles</p>
          </div>
          <div className="glass-card p-4 text-center">
            <TrendingUp className="h-5 w-5 text-success mx-auto mb-2" />
            <p className="text-2xl font-black mono text-foreground">{goalsTotal !== null && goalsTotal > 2.5 ? "Sí" : "No"}</p>
            <p className="text-[11px] text-muted-foreground uppercase tracking-wide mt-1">Más de 2.5</p>
          </div>
          <div className="glass-card p-4 text-center">
            <Shield className="h-5 w-5 text-info mx-auto mb-2" />
            <p className="text-2xl font-black mono text-foreground">{btts ? "Sí" : "No"}</p>
            <p className="text-[11px] text-muted-foreground uppercase tracking-wide mt-1">Ambos Marcan</p>
          </div>
          <div className="glass-card p-4 text-center">
            <CreditCard className="h-5 w-5 text-warning mx-auto mb-2" />
            <p className="text-2xl font-black mono text-foreground">
              {cardsMarket ? cardsMarket.prediction.split(" ")[0] : "—"}
            </p>
            <p className="text-[11px] text-muted-foreground uppercase tracking-wide mt-1">Tarjetas</p>
          </div>
        </div>
      )}

      {/* COMPLETED MATCH: detailed result rows */}
      {isCompleted && match.score && (
        <div className="glass-card overflow-hidden">
          <div className="p-4 border-b border-border/50">
            <h2 className="text-sm font-semibold text-foreground">Resumen del Partido</h2>
          </div>
          <div className="divide-y divide-border/50">
            {[
              { label: "Resultado", value: `${match.homeTeam.shortName} ${match.score.home} – ${match.score.away} ${match.awayTeam.shortName}` },
              { label: "Vencedor", value: homeWon ? match.homeTeam.name : awayWon ? match.awayTeam.name : "Empate" },
              { label: "Total de Goles", value: `${goalsTotal} gol${goalsTotal !== 1 ? "es" : ""}` },
              { label: "Ambos Marcan", value: btts ? "Sí" : "No" },
              { label: "Más de 2.5 Goles", value: goalsTotal !== null && goalsTotal > 2.5 ? "Sí" : "No" },
              ...(cardsMarket ? [{ label: "Total Tarjetas", value: cardsMarket.prediction }] : []),
              ...(match.refereeId && match.refereeId !== "tbd" ? [{ label: "Árbitro", value: getRefereeName(match.refereeId) }] : []),
              { label: "Fecha", value: match.date },
            ].map((row, i) => (
              <div key={i} className="flex items-center justify-between px-4 py-3">
                <span className="text-sm text-muted-foreground">{row.label}</span>
                <span className="text-sm font-medium text-foreground">{row.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* UPCOMING MATCH: show prediction tabs */}
      {!isCompleted && (
        <>
          <WinProbabilityBar
            homeWin={match.prediction.homeWin}
            draw={match.prediction.draw}
            awayWin={match.prediction.awayWin}
            homeLabel={match.homeTeam.shortName}
            awayLabel={match.awayTeam.shortName}
          />
          <Tabs defaultValue="match-odds" className="w-full">
            <TabsList className="w-full bg-card border border-border grid grid-cols-2 md:grid-cols-4">
              {predictionCategories.map((c) => (
                <TabsTrigger key={c.key} value={c.key} className="text-xs data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                  {c.label}
                </TabsTrigger>
              ))}
            </TabsList>
            {predictionCategories.map((c) => {
              const categoryMarkets = match.markets.filter((m: any) => m.category === c.key);
              return (
                <TabsContent key={c.key} value={c.key} className="mt-4 space-y-3">
                  {categoryMarkets.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">Aún no hay predicciones para este mercado.</p>
                  ) : (
                    categoryMarkets.map((market: any, i: number) => (
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
        </>
      )}
    </div>
  );
};

export default MatchDetail;

