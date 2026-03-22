import { useState } from "react";
import { useAPITeamList, fetchPrediction, APIPredictResponse } from "@/lib/api";
import { Loader2, Zap, Brain, Activity, ShieldAlert, CheckCircle2, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import { Calendar as CalendarIcon } from "lucide-react";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";

const Predictor = () => {
  const { data: teamList, isLoading: loadingTeams } = useAPITeamList();
  
  const [homeTeam, setHomeTeam] = useState("");
  const [awayTeam, setAwayTeam] = useState("");
  const [homeMissingKey, setHomeMissingKey] = useState(false);
  const [awayMissingKey, setAwayMissingKey] = useState(false);
  const [matchDate, setMatchDate] = useState<Date | undefined>(undefined);
  
  const [prediction, setPrediction] = useState<APIPredictResponse | null>(null);
  const [loadingPred, setLoadingPred] = useState(false);
  const [error, setError] = useState("");

  const handlePredict = async () => {
    if (!homeTeam || !awayTeam) {
      setError("Por favor selecciona ambos equipos");
      return;
    }
    if (homeTeam === awayTeam) {
      setError("Los equipos local y visitante no pueden ser el mismo");
      return;
    }
    
    setError("");
    setLoadingPred(true);
    setPrediction(null);
    try {
      const payload: any = { homeTeam, awayTeam, homeMissingKey, awayMissingKey };
      if (matchDate) payload.date = format(matchDate, "yyyy-MM-dd");
      const res = await fetchPrediction(payload);
      setPrediction(res);
    } catch (err) {
      setError("Error al obtener la predicción. Asegúrate de que el motor ML esté en ejecución.");
    } finally {
      setLoadingPred(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground mb-1 tracking-tight flex items-center gap-2">
          <Brain className="h-6 w-6 text-primary" />
          Predictor Neuronal
        </h1>
        <p className="text-sm text-muted-foreground">Simula cualquier enfrentamiento usando el Motor de IA V2.</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <div className="glass-card p-6 space-y-6">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Activity className="h-5 w-5 text-info" />
            Configuración del Partido
          </h2>

          <div className="space-y-4">
            {/* Home Team */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Equipo Local</label>
              <Select value={homeTeam} onValueChange={setHomeTeam}>
                <SelectTrigger className="w-full bg-secondary/50 border-border h-12">
                  <SelectValue placeholder="-- Seleccionar --" />
                </SelectTrigger>
                <SelectContent>
                  {teamList?.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
              <label className="flex items-center gap-2 mt-2 cursor-pointer text-sm">
                <input type="checkbox" checked={homeMissingKey} onChange={e => setHomeMissingKey(e.target.checked)} className="rounded bg-secondary border-border" />
                <span className={homeMissingKey ? "text-warning font-medium" : "text-muted-foreground"}>¿Falta jugador clave?</span>
              </label>
            </div>

            {/* Away Team */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Equipo Visitante</label>
              <Select value={awayTeam} onValueChange={setAwayTeam}>
                <SelectTrigger className="w-full bg-secondary/50 border-border h-12">
                  <SelectValue placeholder="-- Seleccionar --" />
                </SelectTrigger>
                <SelectContent>
                  {teamList?.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
              <label className="flex items-center gap-2 mt-2 cursor-pointer text-sm">
                <input type="checkbox" checked={awayMissingKey} onChange={e => setAwayMissingKey(e.target.checked)} className="rounded bg-secondary border-border" />
                <span className={awayMissingKey ? "text-warning font-medium" : "text-muted-foreground"}>¿Falta jugador clave?</span>
              </label>
            </div>

            {/* Date Time Machine */}
            <div className="space-y-2 pt-2 border-t border-border/50">
              <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider text-primary">Viaje en el Tiempo (Opcional)</label>
              <p className="text-xs text-muted-foreground mb-2">Simula como si estuvieras en una fecha pasada. El modelo solo usará información hasta ese momento exacto.</p>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal bg-secondary/50 border-border h-12 hover:bg-secondary/70 hover:text-foreground",
                      !matchDate && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {matchDate ? format(matchDate, "PPP", { locale: es }) : <span>Selecciona una fecha del pasado...</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0 bg-background border-border" align="start">
                  <Calendar
                    mode="single"
                    selected={matchDate}
                    onSelect={setMatchDate}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          {error && <p className="text-destructive text-sm font-medium bg-destructive/10 p-3 rounded-md">{error}</p>}

          <button
            onClick={handlePredict}
            disabled={loadingPred || loadingTeams}
            className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary/20 hover:shadow-primary/40"
          >
            {loadingPred ? <Loader2 className="h-5 w-5 animate-spin" /> : <Zap className="h-5 w-5" />}
            {loadingPred ? "Analizando Redes Neuronales..." : "Generar Predicción"}
          </button>
        </div>

        {/* Output Panel */}
        <div className="glass-card p-6 flex flex-col">
          {prediction ? (
            <div className="space-y-6 animate-fade-in flex-1">
              <div className="text-center pb-6 border-b border-border/50">
                <h2 className="text-xl font-bold text-foreground">Análisis Completo</h2>
                <div className="flex justify-center items-center gap-6 mt-4">
                  <div className="text-center">
                    <p className="text-sm font-semibold">{prediction.homeTeam}</p>
                    <p className="text-xs text-muted-foreground">Elo: {prediction.homeElo.toFixed(1)}</p>
                  </div>
                  <span className="text-muted-foreground font-mono text-sm px-2 py-1 bg-secondary rounded">VS</span>
                  <div className="text-center">
                    <p className="text-sm font-semibold">{prediction.awayTeam}</p>
                    <p className="text-xs text-muted-foreground">Elo: {prediction.awayElo.toFixed(1)}</p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-success" /> Mercados de Valor (Ventaja)
                </h3>
                {prediction.predictions.map((p, i) => (
                  <div key={i} className="bg-secondary/40 border border-border/50 rounded-lg p-4 flex flex-col gap-2 relative overflow-hidden group">
                    <div className="flex justify-between items-center z-10">
                      <span className="font-semibold text-foreground text-sm">{p.Market}</span>
                      <ConfidenceBadge confidence={p.Confidence === "High" ? 85 : p.Confidence === "Medium" ? 65 : 45} />
                    </div>
                    <p className="text-[10px] text-muted-foreground z-10 mb-1">
                      Probabilidad combinada (Softmax/Isotónica) pura calculada por la red.
                    </p>
                    <div className="flex items-center gap-3 z-10">
                      <div className="flex-1 h-2 bg-background rounded-full overflow-hidden border border-border relative">
                        <div 
                          className="h-full bg-primary transition-all duration-1000 ease-out"
                          style={{ width: `${(p.Probability * 100).toFixed(0)}%` }}
                        />
                      </div>
                      <span className="text-sm mono text-primary font-bold">{(p.Probability * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                ))}
                {prediction.predictions.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground flex flex-col items-center gap-2">
                    <ShieldAlert className="h-8 w-8 text-muted-foreground/50" />
                    <p>El modelo no encontró apuestas con suficiente valor (ventaja) para este partido específico.</p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 opacity-50 space-y-4">
              <Bot className="h-16 w-16 text-muted-foreground/30" />
              <div className="space-y-1">
                <p className="text-lg font-medium text-foreground">Esperando Datos</p>
                <p className="text-sm text-muted-foreground">Selecciona dos equipos y presiona "Generar Predicción" para iniciar el análisis.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Predictor;
