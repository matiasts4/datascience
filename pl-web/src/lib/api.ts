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
  return res.json();
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
  };
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
    staleTime: 30 * 60 * 1000,   // 30 minutes — scraper data is stable
    gcTime: 60 * 60 * 1000,      // keep in cache for 60 minutes after unmount
    refetchOnWindowFocus: false,  // don't re-trigger scraper on tab switch
    retry: 1,
  });
};

export const mapAPIUpcomingToMockMatch = (m: APIUpcomingResponse) => {
  const home = Object.values(teamsData).find(t => t.name === m.homeTeam) || 
    { id: m.homeTeam, name: m.homeTeam, shortName: m.homeTeam.substring(0,3).toUpperCase(), logo: "⚽", colors: { primary: "#000", secondary: "#fff" } };
  const away = Object.values(teamsData).find(t => t.name === m.awayTeam) || 
    { id: m.awayTeam, name: m.awayTeam, shortName: m.awayTeam.substring(0,3).toUpperCase(), logo: "⚽", colors: { primary: "#000", secondary: "#fff" } };

  const markets = [];
  if (m.topPrediction) {
    markets.push({
      category: "match-odds",
      name: m.topPrediction.Market,
      prediction: m.topPrediction.Confidence,
      odds: 1.0, 
      fairOdds: 1.0, 
      confidence: m.topPrediction.Probability * 100,
      edge: 0
    });
  }

  return {
    id: m.id,
    homeTeam: home as any,
    awayTeam: away as any,
    date: m.date,
    time: "TBD", 
    stadium: "Premier League",
    refereeId: "tbd",
    prediction: { homeWin: 0.33, draw: 0.33, awayWin: 0.33 }, 
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
  };
  profitChartData: {
    name: string;
    bankroll: number;
  }[];
  historyData: {
    date: string;
    match: string;
    prediction: string;
    odds: number;
    result: string;
    profit: number;
    balance: number;
  }[];
}

export const fetchSimulation = async (params: APISimulateParams): Promise<APISimulateResponse> => {
  const res = await fetch("/api/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error("Error fetching simulation data");
  return res.json();
};

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

