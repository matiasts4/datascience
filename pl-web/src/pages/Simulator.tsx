import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowLeft, Play, DollarSign, TrendingUp, Activity, BarChart2, Download, AlertTriangle, Percent, Calculator } from "lucide-react";
import { fetchSimulation, APISimulateParams, APISimulateResponse } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend
} from "recharts";

const Simulator = () => {
  const [params, setParams] = useState<APISimulateParams>({
    initialBankroll: 100000,
    stake: 10000,
    nMatches: 60,
    strategy: "fixed",
    season: "all",
    minOdds: 1.00,
    model: "xgboost",
    compareModel: "none"
  });

  const mutation = useMutation({
    mutationFn: (p: APISimulateParams) => fetchSimulation(p),
  });

  const handleSimulate = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(params);
  };

  const handleExportCSV = () => {
    if (!data) return;
    const headers = ["Fecha", "Partido", "Prediccion", "Cuota", "Resultado", "Beneficio", "Balance"];
    const rows = data.historyData.map(r => 
      [r.date, r.match, r.prediction, r.odds, r.result, r.profit, r.balance].join(",")
    );
    const csvContent = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `simulacion_${params.model}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const data = mutation.data as APISimulateResponse | undefined;

  return (
    <div className="space-y-6 max-w-6xl mx-auto animate-fade-in pb-10">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Simulador de Estrategia ML</h1>
        <p className="text-muted-foreground">
          Evalúa y compara el rendimiento de diferentes iteraciones de tus modelos de Machine Learning usando datos reales.
        </p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        {/* Controls Panel */}
        <div className="lg:col-span-1 glass-card p-6 h-fit sticky top-6 space-y-6">
          <div className="flex items-center gap-2 border-b border-border/50 pb-4">
            <Calculator className="w-5 h-5 text-primary" /> 
            <h2 className="text-lg font-semibold text-foreground">Parámetros</h2>
          </div>
          
          <form onSubmit={handleSimulate} className="space-y-5">
            {/* Machine Learning Models */}
            <div className="space-y-3">
              <label className="text-sm font-semibold text-foreground">Modelos Predictivos</label>
              
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Modelo Principal</label>
                <select
                  className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  value={params.model}
                  onChange={(e) => setParams({ ...params, model: e.target.value })}
                >
                  <option value="xgboost">Modelo Avanzado (XGBoost)</option>
                  <option value="random_forest">Modelo Intermedio (Random Forest)</option>
                  <option value="logistic">Modelo Base (Reg. Logística)</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Comparar con...</label>
                <select
                  className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  value={params.compareModel}
                  onChange={(e) => setParams({ ...params, compareModel: e.target.value })}
                >
                  <option value="none">Sin Comparación</option>
                  <option value="logistic">Modelo Base (Reg. Logística)</option>
                  <option value="random_forest">Modelo Intermedio (Random Forest)</option>
                </select>
              </div>
            </div>

            {/* Financial Parameters */}
            <div className="space-y-3 pt-4 border-t border-border/50">
              <label className="text-sm font-semibold text-foreground">Gestión de Riesgo</label>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Capital Inicial ($)</label>
                <input
                  type="number"
                  min="1"
                  className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  value={params.initialBankroll}
                  onChange={(e) => setParams({ ...params, initialBankroll: Number(e.target.value) })}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Estrategia</label>
                <select
                  className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  value={params.strategy || "fixed"}
                  onChange={(e) => setParams({ 
                    ...params, 
                    strategy: e.target.value as any,
                    stake: e.target.value === "variable" ? 5 : 10000
                  })}
                >
                  <option value="fixed">Fija Estándar</option>
                  <option value="variable">Criterio de Kelly</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">
                  {params.strategy === "variable" ? "Límite Apuesta (%)" : "Apuesta Fija ($)"}
                </label>
                <input
                  type="number"
                  min="1"
                  className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  value={params.stake}
                  onChange={(e) => setParams({ ...params, stake: Number(e.target.value) })}
                />
              </div>
            </div>

            {/* Season Filtering */}
            <div className="space-y-3 pt-4 border-t border-border/50">
              <label className="text-sm font-semibold text-foreground">Filtros de Datos</label>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Temporada (Test Set)</label>
                <select
                  className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  value={params.season || "all"}
                  onChange={(e) => setParams({ ...params, season: e.target.value })}
                >
                  <option value="all">Últimos {params.nMatches} partidos</option>
                  <option value="2324">Temporada 2023/2024</option>
                  <option value="2223">Temporada 2022/2023</option>
                  <option value="2021">Temporada 2020/2021</option>
                  <option value="1920">Temporada 2019/2020</option>
                </select>
              </div>

              {params.season === "all" && (
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Cantidad de Partidos</label>
                  <input
                    type="number"
                    min="10"
                    max="1000"
                    className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    value={params.nMatches}
                    onChange={(e) => setParams({ ...params, nMatches: Number(e.target.value) })}
                  />
                </div>
              )}
              
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Cuota Mínima (Filtro EV)</label>
                <input
                  type="number"
                  step="0.05"
                  min="1.0"
                  max="10.0"
                  className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  value={params.minOdds || 1.0}
                  onChange={(e) => setParams({ ...params, minOdds: Number(e.target.value) })}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={mutation.isPending}
              className="w-full mt-2 bg-primary text-primary-foreground font-semibold py-2.5 rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {mutation.isPending ? "Ejecutando..." : <><Play className="w-4 h-4" /> Simular Modelos</>}
            </button>
          </form>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-3 space-y-6">
          {mutation.isPending && (
            <div className="glass-card h-64 flex items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="text-sm text-muted-foreground">Evaluando iteraciones en el dataset de validación...</p>
              </div>
            </div>
          )}

          {data && !mutation.isPending && (
            <>
              {/* Primary Model KPIs */}
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3 px-1 border-l-2 border-primary pl-2">
                  Rendimiento: {params.model.toUpperCase()}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="glass-card p-4">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1"><TrendingUp className="w-3 h-3"/> Yield (ROI)</p>
                    <p className={`text-xl font-bold ${data.performanceSummary.yieldPct >= 0 ? "text-success" : "text-destructive"}`}>
                      {data.performanceSummary.yieldPct > 0 ? "+" : ""}{data.performanceSummary.yieldPct}%
                    </p>
                  </div>
                  <div className="glass-card p-4">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> Max Drawdown</p>
                    <p className="text-xl font-bold text-destructive">
                      -{data.performanceSummary.maxDrawdown}%
                    </p>
                  </div>
                  <div className="glass-card p-4">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1"><Percent className="w-3 h-3"/> Tasa Acierto</p>
                    <p className="text-xl font-bold text-foreground">
                      {data.performanceSummary.winRate}%
                    </p>
                  </div>
                  <div className="glass-card p-4">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1"><DollarSign className="w-3 h-3"/> Beneficio Neto</p>
                    <p className={`text-xl font-bold ${data.performanceSummary.netProfit >= 0 ? "text-success" : "text-destructive"}`}>
                      ${data.performanceSummary.netProfit.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Compare Model KPIs */}
              {data.performanceSummaryB && (
                <div>
                  <h3 className="text-sm font-semibold text-foreground mb-3 px-1 border-l-2 border-warning pl-2">
                    Rendimiento: {params.compareModel?.toUpperCase()} (Comparación)
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="glass-card p-3 border-warning/20">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Yield (ROI)</p>
                      <p className={`text-lg font-bold ${data.performanceSummaryB.yieldPct >= 0 ? "text-warning" : "text-destructive"}`}>
                        {data.performanceSummaryB.yieldPct > 0 ? "+" : ""}{data.performanceSummaryB.yieldPct}%
                      </p>
                    </div>
                    <div className="glass-card p-3 border-warning/20">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Max Drawdown</p>
                      <p className="text-lg font-bold text-destructive">
                        -{data.performanceSummaryB.maxDrawdown}%
                      </p>
                    </div>
                    <div className="glass-card p-3 border-warning/20">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Tasa Acierto</p>
                      <p className="text-lg font-bold text-foreground">
                        {data.performanceSummaryB.winRate}%
                      </p>
                    </div>
                    <div className="glass-card p-3 border-warning/20">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Beneficio Neto</p>
                      <p className={`text-lg font-bold ${data.performanceSummaryB.netProfit >= 0 ? "text-warning" : "text-destructive"}`}>
                        ${data.performanceSummaryB.netProfit.toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Main Comparison Chart */}
              <div className="glass-card p-6">
                <h2 className="text-sm font-semibold text-foreground mb-4">
                  Evolución del Capital (Curva de Aprendizaje) {data.performanceSummary.period && <span className="text-xs text-primary font-normal ml-2">({data.performanceSummary.period})</span>}
                </h2>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data.profitChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 25% 15%)" vertical={false} />
                      <XAxis dataKey="name" stroke="hsl(215 20% 55%)" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="hsl(215 20% 55%)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
                      <Tooltip
                        contentStyle={{ backgroundColor: "hsl(220 40% 9%)", border: "1px solid hsl(220 25% 18%)", borderRadius: "8px", color: "hsl(213 31% 91%)" }}
                      />
                      <Legend verticalAlign="top" height={36} />
                      <Line
                        name={`Capital - ${params.model}`}
                        type="monotone"
                        dataKey="bankrollA"
                        stroke="hsl(217 91% 60%)"
                        strokeWidth={3}
                        dot={false}
                        activeDot={{ r: 6 }}
                      />
                      {data.performanceSummaryB && (
                        <Line
                          name={`Capital - ${params.compareModel}`}
                          type="monotone"
                          dataKey="bankrollB"
                          stroke="hsl(35 91% 60%)"
                          strokeWidth={2}
                          strokeDasharray="5 5"
                          dot={false}
                        />
                      )}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Error Analysis Chart */}
              <div className="glass-card p-6">
                <h2 className="text-sm font-semibold text-foreground mb-1">Análisis de Errores por Rango de Cuota</h2>
                <p className="text-xs text-muted-foreground mb-4">Muestra en qué rangos de probabilidad el modelo principal pierde o gana dinero.</p>
                <div className="h-60">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.profitByOddsData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 25% 15%)" vertical={false} />
                      <XAxis dataKey="oddsRange" stroke="hsl(215 20% 55%)" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="hsl(215 20% 55%)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
                      <Tooltip
                        cursor={{fill: 'hsl(220 25% 15%)'}}
                        contentStyle={{ backgroundColor: "hsl(220 40% 9%)", border: "1px solid hsl(220 25% 18%)", borderRadius: "8px", color: "hsl(213 31% 91%)" }}
                      />
                      <Bar 
                        name="Beneficio Neto ($)" 
                        dataKey="profit" 
                        fill="hsl(217 91% 60%)" 
                        radius={[4, 4, 0, 0]}
                        activeBar={{ stroke: 'hsl(217 91% 70%)', strokeWidth: 2 }}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* History Table */}
              <div className="glass-card overflow-hidden">
                <div className="p-4 border-b border-border/50 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-foreground">Registro de Validaciones</h2>
                  <button 
                    onClick={handleExportCSV}
                    className="flex items-center gap-2 text-xs font-medium bg-secondary text-foreground px-3 py-1.5 rounded-md hover:bg-secondary/80 transition-colors"
                  >
                    <Download className="w-3 h-3" /> Exportar Notebook CSV
                  </button>
                </div>
                <div className="overflow-x-auto max-h-96 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-background/95 backdrop-blur z-10 border-b border-border/50">
                      <tr className="text-xs text-muted-foreground uppercase tracking-wider">
                        <th className="text-left p-4 font-medium">Fecha</th>
                        <th className="text-left p-4 font-medium">Partido</th>
                        <th className="text-left p-4 font-medium">Predicción</th>
                        <th className="text-right p-4 font-medium">Cuota</th>
                        <th className="text-center p-4 font-medium">Status</th>
                        <th className="text-right p-4 font-medium">P/L ($)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.historyData.map((row, i) => (
                        <tr key={i} className="border-b border-border/50 last:border-0 hover:bg-secondary/20 transition-colors">
                          <td className="p-4 text-muted-foreground">{row.date}</td>
                          <td className="p-4 font-medium text-foreground">{row.match}</td>
                          <td className="p-4 text-primary">{row.prediction}</td>
                          <td className="p-4 text-right tabular-nums">{row.odds.toFixed(2)}</td>
                          <td className="p-4 text-center">
                            <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                              row.result === "Won" ? "bg-success/20 text-success" : "bg-destructive/20 text-destructive"
                            }`}>
                              {row.result === "Won" ? "Acertada" : "Fallada"}
                            </span>
                          </td>
                          <td className={`p-4 text-right font-medium tabular-nums ${row.profit >= 0 ? "text-success" : "text-destructive"}`}>
                            {row.profit >= 0 ? "+" : ""}{row.profit.toLocaleString()}
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
              <p>Selecciona tus modelos de ML y ejecuta la simulación para evaluar sus métricas.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Simulator;