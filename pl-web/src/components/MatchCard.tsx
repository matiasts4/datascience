import { Link } from "react-router-dom";
import { Calendar, MapPin } from "lucide-react";
import { Match, getRefereeName } from "@/data/mockData";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { EntityLink } from "./EntityLink";
import { TeamLogo } from "./TeamLogo";

interface MatchCardProps {
  match: Match;
}

export function MatchCard({ match }: MatchCardProps) {
  const topMarket = match.markets.reduce((a, b) => a.edge > b.edge ? a : b);

  return (
    <Link to={`/match/${match.id}`} className="glass-card-hover block p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Calendar className="h-3.5 w-3.5" />
          <span>{match.date} · {match.time}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <MapPin className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">{match.stadium}</span>
        </div>
      </div>

      <div className="flex items-center justify-between mb-3">
        <div className="flex flex-col items-center gap-1 flex-1">
          <EntityLink type="team" id={match.homeTeam.id} className="no-underline">
            <TeamLogo name={match.homeTeam.name} colors={match.homeTeam.colors} size="md" />
          </EntityLink>
          <span className="text-sm font-semibold text-foreground mt-1">{match.homeTeam.shortName}</span>
        </div>
        <div className="flex flex-col items-center gap-1 px-4">
          <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide">vs</span>
          <div className="flex gap-2 text-xs mono">
            <span className="text-primary font-semibold">{(match.prediction.homeWin * 100).toFixed(0)}%</span>
            <span className="text-muted-foreground">{(match.prediction.draw * 100).toFixed(0)}%</span>
            <span className="text-info font-semibold">{(match.prediction.awayWin * 100).toFixed(0)}%</span>
          </div>
        </div>
        <div className="flex flex-col items-center gap-1 flex-1">
          <EntityLink type="team" id={match.awayTeam.id} className="no-underline">
            <TeamLogo name={match.awayTeam.name} colors={match.awayTeam.colors} size="md" />
          </EntityLink>
          <span className="text-sm font-semibold text-foreground mt-1">{match.awayTeam.shortName}</span>
        </div>
      </div>

      <div className="text-[11px] text-muted-foreground text-center mb-3">
        Árb: <EntityLink type="referee" id={match.refereeId} className="text-[11px]">{getRefereeName(match.refereeId)}</EntityLink>
      </div>

      <div className="flex items-center justify-between rounded-md bg-muted px-3 py-2.5">
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Mejor Pick</span>
          <span className="text-xs font-medium text-foreground">{topMarket.name}: {topMarket.prediction}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold mono text-success">{topMarket.odds.toFixed(2)}</span>
          <ConfidenceBadge confidence={topMarket.confidence} />
        </div>
      </div>
    </Link>
  );
}
