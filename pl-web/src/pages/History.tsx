import { useState } from "react";
import { Calendar, TrendingUp, Target, Trophy, ChevronDown } from "lucide-react";
import { historicalSeasons, allTimeProfitData, type SeasonData } from "@/data/mockData";
import { cn } from "@/lib/utils";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
} from "recharts";

const seasons = Object.keys(historicalSeasons).sort().reverse();

const History = () => {
  const [selectedSeason, setSelectedSeason] = useState<string>(seasons[0]);
  const data: SeasonData = historicalSeasons[selectedSeason];
  const s = data.summary;

  // All-time totals
  const allTimeProfit = allTimeProfitData.reduce((sum, d) => sum + d.profit, 0);
  const allTimePredictions = Object.values(historicalSeasons).reduce((sum, d) => sum + d.summary.totalPredictions, 0);

  return (
    <div className="space-y-8 max-w-7xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground mb-1">Rendimiento Histórico</h1>
          <p className="text-sm text-muted-foreground">Analíticas multi-temporada sobre {allTimePredictions.toLocaleString()} predicciones</p>
        </div>

        {/* Season Selector */}
        <div className="relative">
          <select
            value={selectedSeason}
            onChange={(e) => setSelectedSeason(e.target.value)}
            className="appearance-none rounded-lg bg-secondary border border-border px-5 py-2.5 pr-10 text-sm font-semibold text-foreground cursor-pointer hover:bg-secondary/80 transition-colors focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {seasons.map((season) => (
              <option key={season} value={season}>Temporada {season}</option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        </div>
      </div>

      {/* All-time overview bar */}
      <div className="glass-card p-5 gradient-blue">
        <div className="flex items-center gap-2 mb-4">
          <Trophy className="h-4 w-4 text-warning" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Resumen Histórico</h2>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-foreground">£{allTimeProfit.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground mt-1">Beneficio Total</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-foreground">{allTimePredictions.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground mt-1">Predicciones</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-success">4</p>
            <p className="text-xs text-muted-foreground mt-1">Temporadas</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-primary">↑ Mejorando</p>
            <p className="text-xs text-muted-foreground mt-1">Tendencia de Acierto</p>
          </div>
        </div>
      </div>

      {/* Profit by Season Chart */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-semibold text-foreground mb-4">Beneficio y ROI por Temporada</h2>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={allTimeProfitData} barCategoryGap="25%">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 25% 15%)" />
              <XAxis dataKey="season" tick={{ fontSize: 12, fill: "hsl(215 20% 50%)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "hsl(215 20% 50%)" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: "hsl(220 40% 9%)", border: "1px solid hsl(220 25% 18%)", borderRadius: "8px", fontSize: "12px", color: "hsl(213 31% 91%)" }} />
              <Bar dataKey="profit" name="Profit (£)" radius={[6, 6, 0, 0]}>
                {allTimeProfitData.map((entry, i) => (
                  <Cell key={i} fill={entry.season === selectedSeason.slice(2, 4) + "-" + selectedSeason.slice(7) ? "hsl(217 91% 60%)" : "hsl(220 30% 25%)"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Selected Season Stats */}
      <div>
        <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <Calendar className="h-5 w-5 text-primary" />
          Temporada {selectedSeason}
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 mb-6">
          {[
            { label: "Predicciones", value: s.totalPredictions },
            { label: "Victorias", value: s.wins, color: "text-success" },
            { label: "Derrotas", value: s.losses, color: "text-destructive" },
            { label: "Tasa de Acierto", value: `${s.winRate}%`, color: "text-success" },
            { label: "ROI", value: `${s.roi}%`, color: "text-primary" },
            { label: "Beneficio", value: `£${s.totalProfit}`, color: "text-success" },
          ].map((stat, i) => (
            <div key={i} className="glass-card p-4 text-center">
              <p className="text-xs text-muted-foreground uppercase tracking-wider">{stat.label}</p>
              <p className={cn("text-xl font-bold mt-1", stat.color || "text-foreground")}>{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Extra info row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <div className="glass-card p-4">
            <p className="text-xs text-muted-foreground">Mejor Mes</p>
            <p className="text-sm font-semibold text-success mt-1">{s.bestMonth}</p>
          </div>
          <div className="glass-card p-4">
            <p className="text-xs text-muted-foreground">Peor Mes</p>
            <p className="text-sm font-semibold text-destructive mt-1">{s.worstMonth}</p>
          </div>
          <div className="glass-card p-4">
            <p className="text-xs text-muted-foreground">Cuota Media</p>
            <p className="text-sm font-semibold text-foreground mt-1">{s.avgOdds.toFixed(2)}</p>
          </div>
          <div className="glass-card p-4">
            <p className="text-xs text-muted-foreground">Mejor Mercado</p>
            <p className="text-sm font-semibold text-primary mt-1">{s.topMarket} ({s.topMarketWinRate}%)</p>
          </div>
        </div>
      </div>

      {/* Monthly Performance Chart */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-semibold text-foreground mb-4">Beneficio Acumulado Mensual</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.monthly}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 25% 15%)" />
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: "hsl(215 20% 50%)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "hsl(215 20% 50%)" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: "hsl(220 40% 9%)", border: "1px solid hsl(220 25% 18%)", borderRadius: "8px", fontSize: "12px", color: "hsl(213 31% 91%)" }} />
              <Line type="monotone" dataKey="cumulative" name="Acumulado £" stroke="hsl(217 91% 60%)" strokeWidth={2} dot={{ r: 4, fill: "hsl(217 91% 60%)" }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Monthly Breakdown Table */}
      <div className="glass-card overflow-hidden">
        <div className="p-4 border-b border-border">
          <h2 className="text-sm font-semibold text-foreground">Desglose Mensual</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-xs text-muted-foreground uppercase tracking-wider">
                <th className="text-left p-3 font-medium">Mes</th>
                <th className="text-center p-3 font-medium">Predicciones</th>
                <th className="text-center p-3 font-medium">V</th>
                <th className="text-center p-3 font-medium">D</th>
                <th className="text-right p-3 font-medium">ROI</th>
                <th className="text-right p-3 font-medium">Beneficio</th>
                <th className="text-right p-3 font-medium">Acumulado</th>
              </tr>
            </thead>
            <tbody>
              {data.monthly.map((m, i) => (
                <tr key={i} className="border-b border-border/50 hover:bg-secondary/30 transition-colors">
                  <td className="p-3 font-medium text-foreground">{m.month}</td>
                  <td className="p-3 text-center text-muted-foreground">{m.predictions}</td>
                  <td className="p-3 text-center text-success font-semibold">{m.wins}</td>
                  <td className="p-3 text-center text-destructive">{m.losses}</td>
                  <td className={cn("p-3 text-right font-semibold", m.roi >= 0 ? "text-success" : "text-destructive")}>
                    {m.roi >= 0 ? "+" : ""}{m.roi}%
                  </td>
                  <td className={cn("p-3 text-right font-bold", m.profit >= 0 ? "text-success" : "text-destructive")}>
                    {m.profit >= 0 ? "+" : ""}£{m.profit}
                  </td>
                  <td className="p-3 text-right text-foreground font-semibold">£{m.cumulative}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Season Highlights */}
      {data.highlights.length > 0 && (
        <div className="glass-card overflow-hidden">
          <div className="p-4 border-b border-border flex items-center gap-2">
            <Trophy className="h-4 w-4 text-warning" />
            <h2 className="text-sm font-semibold text-foreground">Momentos Destacados</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-xs text-muted-foreground uppercase tracking-wider">
                  <th className="text-left p-3 font-medium">Fecha</th>
                  <th className="text-left p-3 font-medium">Partido</th>
                  <th className="text-left p-3 font-medium">Mercado</th>
                  <th className="text-right p-3 font-medium">Cuota</th>
                  <th className="text-right p-3 font-medium">B/P</th>
                </tr>
              </thead>
              <tbody>
                {data.highlights.map((h) => (
                  <tr key={h.id} className="border-b border-border/50 hover:bg-secondary/30 transition-colors">
                    <td className="p-3 text-muted-foreground">{h.date}</td>
                    <td className="p-3 text-foreground font-medium">{h.match}</td>
                    <td className="p-3 text-muted-foreground">{h.market}</td>
                    <td className="p-3 text-right font-semibold text-foreground">{h.odds.toFixed(2)}</td>
                    <td className="p-3 text-right font-bold text-success">+£{h.profit.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default History;
