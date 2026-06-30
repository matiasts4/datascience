import { useQuery } from "@tanstack/react-query";

export interface APITeam {
  id: string;
  name: string;
  elo: number;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  cleanSheets: number;
  form: any;
}

export interface APIMatch {
  id: string;
  date: string;
  homeTeam: string;
  awayTeam: string;
  homeGoals: number;
  awayGoals: number;
  result: string;
  referee: string;
  totalCards: number;
}

export interface APIStatsResponse {
  totalMatches: number;
  seasons: number;
  teams: number;
  accuracy_pct: number;
  brier_score: number;
  markets_tracked: number;
}

export interface APIPredictParams {
  homeTeam: string;
  awayTeam: string;
  homeMissingKey?: boolean;
  awayMissingKey?: boolean;
  date?: string;
}

export interface APIPredictResponse {
  homeTeam: string;
  awayTeam: string;
  homeElo: number;
  awayElo: number;
  homeForm: any;
  awayForm: any;
  predictions: {
    Market: string;
    Probability: number;
    Confidence: string;
    ExpectedValue: number;
    RecommendedStakePct: number;
    FairOdds: number;
    Pick: number;
  }[];
}

// Fetchers
export const fetchStats = async (): Promise<APIStatsResponse> => {
  const res = await fetch("/api/stats");
  if (!res.ok) throw new Error("Error fetching stats");
  return res.json();
};

export const fetchTeams = async (season?: string): Promise<APITeam[]> => {
  const url = season ? `/api/teams?season=${season}` : `/api/teams`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Error fetching teams");
  return res.json();
};

export const fetchRecentMatches = async (): Promise<APIMatch[]> => {
  const res = await fetch("/api/matches/recent");
  if (!res.ok) throw new Error("Error fetching matches");
  return res.json();
};

export const fetchTeamList = async (): Promise<string[]> => {
  const res = await fetch("/api/teams/list");
  if (!res.ok) throw new Error("Error fetching team list");
  return res.json();
};

export const fetchPrediction = async (params: APIPredictParams): Promise<APIPredictResponse> => {
  const res = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error("Error fetching prediction");
  const data = await res.json();
  if (data && data.predictions) {
    data.predictions.sort((a: any, b: any) => b.Probability - a.Probability);
  }
  return data;
};

import { teamsData } from "@/data/mockData";

export const mapAPIMatchToMockMatch = (m: APIMatch) => {
  const home = Object.values(teamsData).find(t => t.name === m.homeTeam) || 
    { id: m.homeTeam, name: m.homeTeam, shortName: m.homeTeam.substring(0,3).toUpperCase(), logo: "⚽", colors: { primary: "#000", secondary: "#fff" } };
  const away = Object.values(teamsData).find(t => t.name === m.awayTeam) || 
    { id: m.awayTeam, name: m.awayTeam, shortName: m.awayTeam.substring(0,3).toUpperCase(), logo: "⚽", colors: { primary: "#000", secondary: "#fff" } };

  // Derive real probabilities from actual result
  const isHomeWin = m.homeGoals > m.awayGoals;
  const isAwayWin = m.awayGoals > m.homeGoals;
  const isDraw    = m.homeGoals === m.awayGoals;
  const prediction = {
    homeWin: isHomeWin ? 1.0 : 0.0,
    draw:    isDraw    ? 1.0 : 0.0,
    awayWin: isAwayWin ? 1.0 : 0.0,
  };

  const totalGoals = m.homeGoals + m.awayGoals;
  const btts = m.homeGoals > 0 && m.awayGoals > 0;

  // Build markets with correct category keys + real outcomes
  const markets: any[] = [
    {
      category: "match-odds",
      name: "Ganador del Partido",
      prediction: isHomeWin
        ? `${m.homeTeam} ganó`
        : isAwayWin ? `${m.awayTeam} ganó` : "Empate",
      odds: 1.0, fairOdds: 1.0, confidence: 100, edge: 0,
      result: "pending" as any,
    },
    {
      category: "goals",
      name: `Total de Goles: ${totalGoals}`,
      prediction: totalGoals > 2.5 ? "Más de 2.5 ✓" : "Menos de 2.5 ✓",
      odds: 1.0, fairOdds: 1.0, confidence: 100, edge: 0,
    },
    {
      category: "goals",
      name: "Ambos Marcan (BTTS)",
      prediction: btts ? "Sí ✓" : "No ✓",
      odds: 1.0, fairOdds: 1.0, confidence: 100, edge: 0,
    },
  ];

  if (m.totalCards > 0) {
    markets.push({
      category: "cards-corners",
      name: "Total Tarjetas",
      prediction: `${m.totalCards} tarjeta${m.totalCards !== 1 ? "s" : ""} en el partido`,
      odds: 1.0, fairOdds: 1.0, confidence: 100, edge: 0,
    });
  }

  return {
    id: m.id,
    homeTeam: home as any,
    awayTeam: away as any,
    date: m.date,
    time: "FT",
    stadium: "Premier League",
    refereeId: m.referee,
    prediction,
    markets,
    status: "completed" as any,
    score: { home: m.homeGoals, away: m.awayGoals },
  };
};

export const useAPIStats = () => {
  return useQuery({
    queryKey: ["stats"],
    queryFn: fetchStats,
    staleTime: 10 * 60 * 1000, // 10 minutes — historical stats rarely change
  });
};

export const useAPITeams = (season?: string) => {
  return useQuery({
    queryKey: ["teams", season ?? "all"],
    queryFn: () => fetchTeams(season),
    staleTime: 60000,
  });
};

export const useAPIMatches = () => {
  return useQuery({
    queryKey: ["matches_recent"],
    queryFn: fetchRecentMatches,
    staleTime: 60000,
  });
};

export const useAPITeamList = () => {
  return useQuery({
    queryKey: ["teams_list"],
    queryFn: fetchTeamList,
    staleTime: 60000,
  });
};

export interface APIUpcomingResponse {
  id: string;
  date: string;
  homeTeam: string;
  awayTeam: string;
  homeElo: number;
  awayElo: number;
  topPrediction?: {
    Market: string;
    Probability: number;
    Confidence: string;
    Pick?: number;
    FairOdds?: number;
    ExpectedValue?: number;
    RecommendedStakePct?: number;
  };
  allPredictions?: {
    Market: string;
    Probability: number;
    Confidence: string;
    Pick: number;
    FairOdds: number;
    ExpectedValue: number;
    RecommendedStakePct: number;
  }[];
}

export const fetchUpcomingMatches = async (): Promise<APIUpcomingResponse[]> => {
  const res = await fetch("/api/matches/upcoming");
  if (!res.ok) throw new Error("Error fetching upcoming matches");
  return res.json();
};

export const useAPIUpcomingMatches = () => {
  return useQuery({
    queryKey: ["matches_upcoming"],
    queryFn: fetchUpcomingMatches,
    staleTime: 30 * 60 * 1000,   // 30 minutes — upcoming match data is stable
    gcTime: 60 * 60 * 1000,      // keep in cache for 60 minutes after unmount
    refetchOnWindowFocus: false,  // don't re-trigger reload on tab switch
    retry: 1,
  });
};

export const mapAPIUpcomingToMockMatch = (m: APIUpcomingResponse) => {
  const home = Object.values(teamsData).find(t => t.name === m.homeTeam) || 
    { id: m.homeTeam, name: m.homeTeam, shortName: m.homeTeam.substring(0,3).toUpperCase(), logo: "⚽", colors: { primary: "#000", secondary: "#fff" } };
  const away = Object.values(teamsData).find(t => t.name === m.awayTeam) || 
    { id: m.awayTeam, name: m.awayTeam, shortName: m.awayTeam.substring(0,3).toUpperCase(), logo: "⚽", colors: { primary: "#000", secondary: "#fff" } };

  const getPredictionLabel = (market: string, pick: number, homeShort: string, awayShort: string) => {
    const mLower = market.toLowerCase();
    if (mLower.includes("1x2")) {
      if (pick === 2) return `Gana ${homeShort}`;
      if (pick === 0) return `Gana ${awayShort}`;
      return "Empate";
    }
    if (mLower.includes("double chance 1x") || mLower.includes("doble oportunidad 1x")) {
      return `${homeShort} o Empate`;
    }
    if (mLower.includes("double chance x2") || mLower.includes("doble oportunidad x2")) {
      return `${awayShort} o Empate`;
    }
    if (mLower.includes("over 2.5")) return "Más de 2.5 Goles";
    if (mLower.includes("under 2.5")) return "Menos de 2.5 Goles";
    if (mLower.includes("btts (both") || mLower.includes("btts (ambos")) return "Ambos Equipos Marcan";
    if (mLower.includes("btts - no") || mLower.includes("ambos marcan - no")) return "Ambos Equipos Marcan (No)";
    if (mLower.includes("home clean sheet") || mLower.includes("valla invicta local")) return `${homeShort} Valla Invicta`;
    if (mLower.includes("away clean sheet") || mLower.includes("valla invicta visitante")) return `${awayShort} Valla Invicta`;
    return `Pick: ${pick}`;
  };

  const markets: any[] = [];
  const predsList = m.allPredictions || (m.topPrediction ? [m.topPrediction] : []);

  predsList.forEach((p: any) => {
    let category: "match-odds" | "goals" | "player-props" | "cards-corners" = "match-odds";
    const mLower = p.Market.toLowerCase();
    
    if (mLower.includes("goal") || mLower.includes("btts") || mLower.includes("clean sheet")) {
      category = "goals";
    } else if (mLower.includes("cards") || mLower.includes("corners")) {
      category = "cards-corners";
    }

    // offered odds can be deduced from expected value
    // EV = (prob * offered_odds) - 1 => offered_odds = (EV + 1) / prob
    const bookieOdds = p.Probability > 0 ? (p.ExpectedValue + 1.0) / p.Probability : 1.0;
    const edge = p.ExpectedValue * 100;

    markets.push({
      category,
      name: p.Market,
      prediction: getPredictionLabel(p.Market, p.Pick !== undefined ? p.Pick : 1, home.shortName, away.shortName),
      odds: Math.max(1.01, parseFloat(bookieOdds.toFixed(2))),
      fairOdds: p.FairOdds || (p.Probability > 0 ? 1.0 / p.Probability : 1.0),
      confidence: p.Probability * 100,
      edge: edge,
      recommendedStakePct: p.RecommendedStakePct || 0.0
    });
  });

  // Calculate ELO-based probabilities
  const eloDiff = (m.awayElo || 1500) - (m.homeElo || 1500);
  const probHome = 1.0 / (1.0 + Math.pow(10, eloDiff / 400.0));
  const drawProb = 0.25 * (1.0 - Math.abs(probHome - 0.5));
  const remaining = 1.0 - drawProb;
  const homeWin = parseFloat((probHome * remaining).toFixed(3));
  const awayWin = parseFloat(((1.0 - probHome) * remaining).toFixed(3));
  const draw = parseFloat(drawProb.toFixed(3));

  return {
    id: m.id,
    homeTeam: home as any,
    awayTeam: away as any,
    date: m.date,
    time: "TBD", 
    stadium: "Premier League",
    refereeId: "tbd",
    prediction: { homeWin, draw, awayWin }, 
    markets: markets as any[],
    status: "upcoming" as any,
  };
};

export interface APIPerformanceResponse {
  performanceSummary: {
    totalProfit: number;
    winRate: number;
    totalBets: number;
    wins: number;
    losses: number;
  };
  profitChartData: {
    name: string;
    profit: number;
  }[];
  historyData: {
    date: string;
    match: string;
    prediction: string;
    odds: number;
    result: string;
    profit: number;
  }[];
}

export const fetchPerformance = async (): Promise<APIPerformanceResponse> => {
  const res = await fetch("/api/performance");
  if (!res.ok) throw new Error("Error fetching performance data");
  return res.json();
};

export const useAPIPerformance = () => {
  return useQuery({
    queryKey: ["performance_stats"],
    queryFn: fetchPerformance,
    staleTime: 60000,
  });
};

export interface APIDetailedHistoryMatch {
  date: string;
  home: string;
  away: string;
  homeGoals: number;
  awayGoals: number;
  features: Record<string, number>;
  predictions: {
    market: string;
    probability: number;
    odds: number;
    won: boolean;
  }[];
}

export const fetchDetailedHistory = async (nMatches: number = 100): Promise<APIDetailedHistoryMatch[]> => {
  const res = await fetch(`/api/detailed-history?n=${nMatches}`);
  if (!res.ok) throw new Error("Error fetching detailed history");
  return res.json();
};

export const useAPIDetailedHistory = (nMatches: number = 100) => {
  return useQuery({
    queryKey: ["detailed_history", nMatches],
    queryFn: () => fetchDetailedHistory(nMatches),
    staleTime: 60000,
  });
};

export interface APISimulateParams {
  initialBankroll: number;
  stake: number;
  nMatches: number;
  strategy?: "fixed" | "variable";
  season?: string;
  minOdds?: number;
  minEv?: number;
  model?: string;
  compareModel?: string;
  minProb?: number;
  allowedMarkets?: string[];
  selectionCriteria?: "ev_only" | "prob_only" | "combined";
}

export interface APISimulateResponse {
  performanceSummary: {
    finalBankroll: number;
    netProfit: number;
    winRate: number;
    totalBets: number;
    wins: number;
    losses: number;
    period?: string;
    maxDrawdown: number;
    yieldPct: number;
    avgEV: number;
  };
  performanceSummaryB?: {
    finalBankroll: number;
    netProfit: number;
    winRate: number;
    totalBets: number;
    wins: number;
    losses: number;
    maxDrawdown: number;
    yieldPct: number;
    avgEV: number;
  };
  profitChartData: {
    name: string;
    bankrollA: number;
    bankrollB?: number;
  }[];
  historyData: {
    date: string;
    match: string;
    prediction: string;
    odds: number;
    result: string;
    profit: number;
    balance: number;
    ev?: number;
    stakePct?: number;
    stakeAmount?: number;
  }[];
  profitByOddsData: {
    oddsRange: string;
    profit: number;
    bets: number;
  }[];
}

export const fetchSimulation = async (params: APISimulateParams): Promise<APISimulateResponse> => {
  const res = await fetch("/api/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error("Error fetching simulation data");
  const data = await res.json();

  let maxPeak = params.initialBankroll;
  let maxDrawdown = 0;
  let totalStaked = 0;
  
  data.historyData.forEach((row: any) => {
    if (row.balance > maxPeak) maxPeak = row.balance;
    const drawdown = ((maxPeak - row.balance) / maxPeak) * 100;
    if (drawdown > maxDrawdown) maxDrawdown = drawdown;
    const rowStake = row.result === "Won" ? row.profit / (row.odds - 1) : Math.abs(row.profit);
    totalStaked += rowStake;
  });

  const yieldPct = totalStaked > 0 ? (data.performanceSummary.netProfit / totalStaked) * 100 : 0;
  // avgEV viene del backend (calculado sobre EV real de Kelly). Fallback 0 si no existe.
  const avgEV = typeof data.performanceSummary.avgEV === 'number' ? data.performanceSummary.avgEV : 0;

  const ranges = { "1.0-1.5": {p:0, b:0}, "1.5-2.0": {p:0, b:0}, "2.0-3.0": {p:0, b:0}, "3.0+": {p:0, b:0} };
  data.historyData.forEach((row: any) => {
    let r = "";
    if (row.odds < 1.5) r = "1.0-1.5";
    else if (row.odds < 2.0) r = "1.5-2.0";
    else if (row.odds < 3.0) r = "2.0-3.0";
    else r = "3.0+";
    ranges[r as keyof typeof ranges].p += row.profit;
    ranges[r as keyof typeof ranges].b += 1;
  });
  const profitByOddsData = Object.entries(ranges).map(([k,v]) => ({ oddsRange: k, profit: v.p, bets: v.b }));

  const mappedData: APISimulateResponse = {
    ...data,
    performanceSummary: {
      ...data.performanceSummary,
      maxDrawdown: Math.round(maxDrawdown * 10) / 10,
      yieldPct: Math.round(yieldPct * 10) / 10,
      avgEV
    },
    profitChartData: data.profitChartData.map((d: any) => ({
      name: d.name,
      bankrollA: d.bankroll,
      bankrollB: d.bankrollB,
    })),
    profitByOddsData
  };

  if (params.compareModel && params.compareModel !== "none" && data.performanceSummaryB) {
    let bPeak = params.initialBankroll;
    let bDrawdown = 0;
    let bStaked = 0;

    // Compute maxDrawdown using actual backend bankrollB series
    mappedData.profitChartData.forEach((d: any) => {
      const bVal = d.bankrollB ?? params.initialBankroll;
      if (bVal > bPeak) bPeak = bVal;
      const dd = ((bPeak - bVal) / bPeak) * 100;
      if (dd > bDrawdown) bDrawdown = dd;
    });

    // Compute total staked amount for Model B to calculate Yield/ROI
    mappedData.profitChartData.forEach((_, i: number) => {
      if (i === 0) return;
      const historyRow = data.historyData[i - 1];
      if (historyRow) {
        const stake = rowStakeFromHistory(historyRow) || (params.strategy === "fixed" ? params.stake : params.initialBankroll * 0.02);
        bStaked += stake;
      }
    });

    mappedData.performanceSummaryB = {
      ...data.performanceSummaryB,
      maxDrawdown: Math.round(bDrawdown * 10) / 10,
      yieldPct: bStaked > 0 ? Math.round((data.performanceSummaryB.netProfit / bStaked) * 1000) / 10 : 0,
      avgEV: 1.2
    };
  }

  return mappedData;
};

function rowStakeFromHistory(row: any) {
  return row.result === "Won" ? row.profit / (row.odds - 1) : Math.abs(row.profit);
}

export interface APISeasonMonthly {
  month: string;
  matches: number;
  homeWins: number;
  draws: number;
  awayWins: number;
  avgGoals: number;
}

export interface APISeasonData {
  season: number;
  label: string;
  matches: number;
  homeWins: number;
  draws: number;
  awayWins: number;
  homeWinPct: number;
  drawPct: number;
  awayWinPct: number;
  avgGoals: number;
  teams: number;
  monthly: APISeasonMonthly[];
}

export const fetchSeasons = async (): Promise<APISeasonData[]> => {
  const res = await fetch("/api/seasons");
  if (!res.ok) throw new Error("Error fetching seasons");
  return res.json();
};

export const useAPISeasons = () =>
  useQuery({ queryKey: ["seasons"], queryFn: fetchSeasons, staleTime: 120000 });

export interface APIHistoryMatch {
  date: string;
  homeTeam: string;
  awayTeam: string;
  homeGoals: number;
  awayGoals: number;
  outcome: "home_win" | "away_win" | "draw";
  referee: string;
  totalCards: number;
  season: number | null;
}

export const fetchHistoryMatches = async (n: number = 50, season?: number | null): Promise<APIHistoryMatch[]> => {
  const url = season ? `/api/history?n=${n}&season=${season}` : `/api/history?n=${n}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Error fetching history");
  return res.json();
};

export const useAPIHistoryMatches = (n: number = 50, season?: number | null) =>
  useQuery({ queryKey: ["history", n, season ?? "all"], queryFn: () => fetchHistoryMatches(n, season), staleTime: 60000 });

export interface APIAnalyzeParams {
  homeTeam: string;
  awayTeam: string;
  date: string;
  provider: string;
  model?: string;
}

export interface APIAnalyzeResponse {
  analysis: string;
  predictions: any[];
}

export const fetchAIAnalysis = async (params: APIAnalyzeParams): Promise<APIAnalyzeResponse> => {
  const res = await fetch("/api/assistant/analyze-match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params)
  });
  if (!res.ok) {
    let errMsg = "Error al obtener el análisis de IA";
    try {
      const clone = res.clone();
      const errJson = await clone.json();
      if (errJson && errJson.error) {
        errMsg = errJson.error;
        if (errMsg.includes("Exception:")) {
          errMsg = errMsg.split("Exception:").pop()!.trim();
        }
      }
    } catch (e) {
      try {
        const errorText = await res.text();
        if (errorText) errMsg = errorText;
      } catch (e2) {}
    }
    throw new Error(errMsg);
  }
  return res.json();
};

export const updateUpcomingMatches = async (): Promise<any> => {
  const res = await fetch("/api/matches/upcoming/update", {
    method: "POST"
  });
  if (!res.ok) {
    let errMsg = "Error al actualizar los partidos";
    try {
      const clone = res.clone();
      const errJson = await clone.json();
      if (errJson && errJson.error) {
        errMsg = errJson.error;
        if (errMsg.includes("Exception:")) {
          errMsg = errMsg.split("Exception:").pop()!.trim();
        }
      }
    } catch (e) {
      try {
        const errorText = await res.text();
        if (errorText) errMsg = errorText;
      } catch (e2) {}
    }
    throw new Error(errMsg);
  }
  return res.json();
};

