import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowLeft, Play, DollarSign, TrendingUp, Activity, BarChart2 } from "lucide-react";
import { fetchSimulation, APISimulateParams, APISimulateResponse } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const Simulator = () => {
  const [params, setParams] = useState<APISimulateParams>({
    initialBankroll: 100000,
    stake: 10000,
    nMatches: 60,
    strategy: "fixed",
    season: "all",
    minOdds: 1.00,
  });

  const mutation = useMutation({
    mutationFn: (p: APISimulateParams) => fetchSimulation(p),
  });

  const handleSimulate = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(params);
  };

  const data = mutation.data as APISimulateResponse | undefined;

  return (
    <div className="space-y-6 max-w-6xl mx-auto animate-fade-in pb-10">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Simulador de Estrategia</h1>
        <p className="text-muted-foreground">
          Simula el comportamiento de tu capital usando datos 100% reales del modelo predictivo sobre partidos históricos.
        </p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        {/* Controls Panel */}
        <div className="lg:col-span-1 glass-card p-6 h-fit sticky top-6">
          <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-primary" /> Parámetros
          </h2>
          <form onSubmit={handleSimulate} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">Capital Inicial ($)</label>
              <input
                type="number"
                min="1"
                className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                value={params.initialBankroll}
                onChange={(e) => setParams({ ...params, initialBankroll: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">Estrategia de Gestión</label>
              <select
                className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                value={params.strategy || "fixed"}
                onChange={(e) => setParams({ 
                  ...params, 
                  strategy: e.target.value as any,
                  stake: e.target.value === "variable" ? 5 : 10000
                })}
              >
                <option value="fixed">Fija Estándar</option>
                <option value="variable">Criterio de Kelly (Dinámica)</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">
                {params.strategy === "variable" ? "Límite Máximo de Apuesta (%)" : "Apuesta Fija ($)"}
              </label>
              <input
                type="number"
                min="1"
                className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                value={params.stake}
                onChange={(e) => setParams({ ...params, stake: Number(e.target.value) })}
              />
              {params.strategy === "variable" && (
                <p className="text-xs text-muted-foreground leading-tight">Ej: 5 = arriesgar máx. 5% del capital por apuesta. La IA calculará la fracción óptima en base al <i>edge</i>.</p>
              )}
            </div>
            {/* Season Filtering */}
            <div className="space-y-2 pt-4 border-t border-border/50">
              <label className="text-sm font-medium text-muted-foreground">Filtro de Tiempo</label>
              <select
                className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                value={params.season || "all"}
                onChange={(e) => setParams({ ...params, season: e.target.value })}
              >
                <option value="all">Últimos {params.nMatches} partidos</option>
                <option value="2324">Temporada 2023/2024</option>
                <option value="2223">Temporada 2022/2023</option>
                <option value="2021">Temporada 2020/2021</option>
                <option value="1920">Temporada 2019/2020</option>
                <option value="1819">Temporada 2018/2019</option>
              </select>
              {params.season !== "all" && (
                <p className="text-xs text-muted-foreground leading-tight">
                  Se simularán todos los partidos de esta temporada. El valor "Cantidad" será ignorado.
                </p>
              )}
            </div>

            {/* Strategy Optimization */}
            <div className="space-y-2 pt-4 border-t border-border/50">
              <label className="text-sm font-medium text-foreground">Optimización Estratégica</label>
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground">Cuota Mínima (Filtro EV)</label>
                <input
                  type="number"
                  step="0.05"
                  min="1.0"
                  max="10.0"
                  className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  value={params.minOdds || 1.0}
                  onChange={(e) => setParams({ ...params, minOdds: Number(e.target.value) })}
                />
                <p className="text-xs text-muted-foreground leading-tight">
                  Ignora predicciones cuya cuota (simulada o real) sea menor a este valor, filtrando apuestas de alto riesgo y bajo retorno. Recomendado: 1.50
                </p>
              </div>
            </div>

            {params.season === "all" && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Cantidad de Partidos Recientes</label>
                <input
                  type="number"
                  min="10"
                  max="1000"
                  className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  value={params.nMatches}
                  onChange={(e) => setParams({ ...params, nMatches: Number(e.target.value) })}
                />
              </div>
            )}
            <button
              type="submit"
              disabled={mutation.isPending}
              className="w-full mt-4 bg-primary text-primary-foreground font-semibold py-2.5 rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {mutation.isPending ? "Simulando..." : <><Play className="w-4 h-4" /> Ejecutar Simulación</>}
            </button>
          </form>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-3 space-y-6">
          {mutation.isPending && (
            <div className="glass-card h-64 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          )}

          {data && !mutation.isPending && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-card p-4">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Capital Final</p>
                  <p className="text-2xl font-bold flex items-center gap-2">
                    <DollarSign className="w-5 h-5 text-muted-foreground" />
                    {data.performanceSummary.finalBankroll.toLocaleString()}
                  </p>
                </div>
                <div className="glass-card p-4">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Beneficio Neto</p>
                  <p className={`text-2xl font-bold flex items-center gap-2 ${data.performanceSummary.netProfit >= 0 ? "text-success" : "text-destructive"}`}>
                    <TrendingUp className="w-5 h-5" />
                    {data.performanceSummary.netProfit >= 0 ? "+" : ""}{data.performanceSummary.netProfit.toLocaleString()}
                  </p>
                </div>
                <div className="glass-card p-4">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Tasa de Acierto</p>
                  <p className="text-2xl font-bold flex items-center gap-2">
                    <Activity className="w-5 h-5 text-primary" />
                    {data.performanceSummary.winRate}%
                  </p>
                </div>
                <div className="glass-card p-4">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Apuestas (V - D)</p>
                  <p className="text-2xl font-bold flex items-center gap-2">
                    <BarChart2 className="w-5 h-5 text-muted-foreground" />
                    {data.performanceSummary.wins} - {data.performanceSummary.losses}
                  </p>
                </div>
              </div>

              {/* Chart */}
              <div className="glass-card p-6">
                <h2 className="text-sm font-semibold text-foreground mb-4">
                  Evolución del Capital {data.performanceSummary.period && <span className="text-xs text-primary font-normal ml-2">({data.performanceSummary.period})</span>}
                </h2>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data.profitChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 25% 15%)" vertical={false} />
                      <XAxis dataKey="name" stroke="hsl(215 20% 55%)" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="hsl(215 20% 55%)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
                      <Tooltip
                        contentStyle={{ backgroundColor: "hsl(220 40% 9%)", border: "1px solid hsl(220 25% 18%)", borderRadius: "8px", color: "hsl(213 31% 91%)" }}
                        formatter={(value: number) => [`$${value.toLocaleString()}`, "Capital"]}
                      />
                      <Line
                        type="monotone"
                        dataKey="bankroll"
                        stroke="hsl(217 91% 60%)"
                        strokeWidth={3}
                        dot={false}
                        activeDot={{ r: 6, fill: "hsl(217 91% 60%)" }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* History Table */}
              <div className="glass-card overflow-hidden">
                <div className="p-4 border-b border-border/50">
                  <h2 className="text-sm font-semibold text-foreground">Registro de Apuestas</h2>
                </div>
                <div className="overflow-x-auto max-h-96 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-background/95 backdrop-blur z-10 border-b border-border/50">
                      <tr className="text-xs text-muted-foreground uppercase tracking-wider">
                        <th className="text-left p-4 font-medium">Fecha</th>
                        <th className="text-left p-4 font-medium">Partido</th>
                        <th className="text-left p-4 font-medium">Mercado</th>
                        <th className="text-right p-4 font-medium">Cuota</th>
                        <th className="text-center p-4 font-medium">Resultado</th>
                        <th className="text-right p-4 font-medium">P/L</th>
                        <th className="text-right p-4 font-medium">Balance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.historyData.map((row, i) => (
                        <tr key={i} className="border-b border-border/50 last:border-0 hover:bg-secondary/20 transition-colors">
                          <td className="p-4 text-muted-foreground">{row.date}</td>
                          <td className="p-4 font-medium text-foreground">{row.match}</td>
                          <td className="p-4 text-primary">{row.prediction}</td>
                          <td className="p-4 text-right">{row.odds.toFixed(2)}</td>
                          <td className="p-4 text-center">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              row.result === "Won" ? "bg-success/20 text-success" : "bg-destructive/20 text-destructive"
                            }`}>
                              {row.result === "Won" ? "Ganada" : "Perdida"}
                            </span>
                          </td>
                          <td className={`p-4 text-right font-medium ${row.profit >= 0 ? "text-success" : "text-destructive"}`}>
                            {row.profit >= 0 ? "+" : ""}{row.profit.toLocaleString()}
                          </td>
                          <td className="p-4 text-right font-bold text-foreground">
                            ${row.balance.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}

          {!data && !mutation.isPending && (
            <div className="glass-card h-64 flex flex-col items-center justify-center text-muted-foreground">
              <BarChart2 className="w-12 h-12 mb-3 opacity-20" />
              <p>Haz clic en "Ejecutar Simulación" para ver resultados.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Simulator;
