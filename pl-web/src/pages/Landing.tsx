import { Link } from "react-router-dom";
import { Bot, TrendingUp, Shield, Zap, BarChart3, Target, ArrowRight, ChevronRight } from "lucide-react";
import { botStats } from "@/data/mockData";

const Landing = () => {
  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Bot className="h-6 w-6 text-primary" />
            <span className="text-lg font-bold text-foreground">BetBot <span className="text-primary">AI</span></span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
            <a href="#features" className="hover:text-foreground transition-colors">Características</a>
            <a href="#stats" className="hover:text-foreground transition-colors">Estadísticas</a>
            <a href="#markets" className="hover:text-foreground transition-colors">Mercados</a>
          </div>
          <Link
            to="/dashboard"
            className="rounded-md bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Abrir App
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-24 px-6">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-primary/6 blur-[120px] pointer-events-none" />

        <div className="max-w-4xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-muted px-4 py-1.5 text-xs font-medium text-muted-foreground mb-8 animate-fade-in">
            <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
            Analítica de la Premier League con IA
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-black tracking-tighter mb-6 animate-fade-in text-foreground" style={{ animationDelay: "100ms", letterSpacing: "-0.04em" }}>
            Apuestas más inteligentes.
            <br />
            <span className="text-primary">Mayores ventajas.</span>
          </h1>

          <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto mb-10 animate-fade-in leading-relaxed" style={{ animationDelay: "200ms" }}>
            Nuestra IA analiza miles de puntos de datos por partido para encontrar las oportunidades de apuestas de mayor valor en cada partido de la Premier League.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 animate-fade-in" style={{ animationDelay: "300ms" }}>
            <Link
              to="/dashboard"
              className="group flex items-center gap-2 rounded-md bg-primary px-8 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-all"
            >
              Abrir Panel
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <a
              href="#features"
              className="flex items-center gap-2 rounded-md border border-border px-8 py-3 text-sm font-medium text-foreground hover:bg-muted transition-colors"
            >
              Saber más
            </a>
          </div>
        </div>

        {/* Stats bar */}
        <div id="stats" className="max-w-3xl mx-auto mt-20 grid grid-cols-2 md:grid-cols-4 gap-3 animate-slide-up" style={{ animationDelay: "400ms" }}>
          {[
            { label: "Tasa de Acierto", value: `${botStats.winRate}%`, icon: Target },
            { label: "ROI", value: `${botStats.roi}%`, icon: TrendingUp },
            { label: "Predicciones", value: botStats.totalPredictions.toLocaleString(), icon: BarChart3 },
            { label: "Beneficio Total", value: `£${botStats.totalProfit.toLocaleString()}`, icon: Zap },
          ].map((s, i) => (
            <div key={i} className="glass-card p-5 text-center">
              <s.icon className="h-4 w-4 text-primary mx-auto mb-2" />
              <p className="text-xl font-bold text-foreground mono">{s.value}</p>
              <p className="text-[11px] text-muted-foreground mt-1 uppercase tracking-wide">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 px-6 border-t border-border">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-foreground mb-3 tracking-tight">Plataforma de Analítica Premium</h2>
            <p className="text-sm text-muted-foreground max-w-xl mx-auto">Todas las herramientas que necesitas para tomar decisiones de apuestas basadas en datos, impulsadas por modelos avanzados de aprendizaje automático.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            {[
              {
                icon: BarChart3,
                title: "Análisis Profundo de Partidos",
                description: "Probabilidades de victoria, modelos xG y cálculos de ventaja para cada partido de la Premier League en más de 8 mercados.",
              },
              {
                icon: Shield,
                title: "Perfiles de Equipo y Jugador",
                description: "Gráficos de radar interactivos, análisis de forma y desgloses estadísticos detallados para cada equipo, jugador y árbitro.",
              },
              {
                icon: Target,
                title: "Detección de Valor",
                description: "Nuestra IA identifica cuotas mal valoradas en tiempo real, destacando apuestas de alta ventaja con puntuaciones de confianza y cálculo de cuotas justas.",
              },
            ].map((f, i) => (
              <div key={i} className="glass-card p-7 hover:border-primary/20 transition-colors">
                <div className="rounded-md bg-primary/10 p-2.5 w-fit mb-5">
                  <f.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="text-base font-semibold text-foreground mb-2">{f.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Markets Section */}
      <section id="markets" className="py-24 px-6 border-t border-border">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-foreground mb-3 tracking-tight">Todos los Mercados Cubiertos</h2>
            <p className="text-sm text-muted-foreground">Desde ganadores del partido hasta tarjetas de jugador: nuestros modelos lo cubren todo.</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              "Ganador del Partido (1X2)", "Hándicap Asiático", "Más/Menos Goles", "Ambos Marcan",
              "Anota en Cualquier Momento", "Tiros a Puerta (Jugador)", "Total Tarjetas", "Total Córners",
            ].map((market, i) => (
              <div key={i} className="glass-card p-4 flex items-center gap-3 group hover:border-primary/20 transition-colors">
                <ChevronRight className="h-4 w-4 text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                <span className="text-sm font-medium text-foreground">{market}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center glass-card p-12">
          <h2 className="text-2xl font-bold text-foreground mb-3 tracking-tight">¿Listo para Encontrar tu Ventaja?</h2>
          <p className="text-sm text-muted-foreground mb-8">Comienza a explorar predicciones con IA para cada partido de la Premier League.</p>
          <Link
            to="/dashboard"
            className="group inline-flex items-center gap-2 rounded-md bg-primary px-10 py-3.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-all"
          >
            Abrir Panel
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            <span className="text-sm font-semibold text-foreground">BetBot <span className="text-primary">AI</span></span>
          </div>
          <p className="text-xs text-muted-foreground">Analíticas de apuestas de la Premier League impulsadas por inteligencia artificial.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
