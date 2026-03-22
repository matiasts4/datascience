import { useState, useMemo } from "react";
import { Search, Loader2 } from "lucide-react";
import { useAPIMatches, mapAPIMatchToMockMatch } from "@/lib/api";
import { MatchCard } from "@/components/MatchCard";
import { Input } from "@/components/ui/input";

const Matches = () => {
  const [search, setSearch] = useState("");
  const [dateFilter, setDateFilter] = useState<string>("all");
  const { data: apiMatches, isLoading } = useAPIMatches();

  const matches = useMemo(() => {
    if (!apiMatches) return [];
    return apiMatches.map(mapAPIMatchToMockMatch);
  }, [apiMatches]);

  const dates = [...new Set(matches.map((m) => m.date))];

  const filtered = matches.filter((m) => {
    const matchesSearch =
      m.homeTeam.name.toLowerCase().includes(search.toLowerCase()) ||
      m.awayTeam.name.toLowerCase().includes(search.toLowerCase());
    const matchesDate = dateFilter === "all" || m.date === dateFilter;
    return matchesSearch && matchesDate;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-foreground mb-1">Partidos</h1>
        <p className="text-sm text-muted-foreground">Partidos y predicciones de la Premier League</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar equipos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-card border-border"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setDateFilter("all")}
            className={`rounded-lg px-4 py-2 text-xs font-medium transition-colors ${
              dateFilter === "all" ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
            }`}
          >
            Todas las Fechas
          </button>
          {dates.map((d) => (
            <button
              key={d}
              onClick={() => setDateFilter(d)}
              className={`rounded-lg px-4 py-2 text-xs font-medium transition-colors ${
                dateFilter === d ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              }`}
            >
              {new Date(d).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" })}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          <div className="col-span-full flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          filtered.map((match) => (
            <MatchCard key={match.id} match={match} />
          ))
        )}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          No se encontraron partidos
        </div>
      )}
    </div>
  );
};

export default Matches;
