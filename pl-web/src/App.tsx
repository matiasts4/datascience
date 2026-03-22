import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppLayout } from "@/components/AppLayout";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import Matches from "./pages/Matches";
import MatchDetail from "./pages/MatchDetail";
import Performance from "./pages/Performance";
import TeamProfile from "./pages/TeamProfile";
import PlayerProfile from "./pages/PlayerProfile";
import RefereeProfile from "./pages/RefereeProfile";
import History from "./pages/History";
import Predictor from "./pages/Predictor";
import DetailedHistory from "./pages/DetailedHistory";
import Simulator from "./pages/Simulator";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          {/* Landing page without sidebar */}
          <Route path="/" element={<Landing />} />

          {/* App routes with sidebar */}
          <Route path="/dashboard" element={<AppLayout><Dashboard /></AppLayout>} />
          <Route path="/matches" element={<AppLayout><Matches /></AppLayout>} />
          <Route path="/match/:id" element={<AppLayout><MatchDetail /></AppLayout>} />
          <Route path="/performance" element={<AppLayout><Performance /></AppLayout>} />
          <Route path="/predictor" element={<AppLayout><Predictor /></AppLayout>} />
          <Route path="/history" element={<AppLayout><History /></AppLayout>} />
          <Route path="/detailed-history" element={<AppLayout><DetailedHistory /></AppLayout>} />
          <Route path="/simulator" element={<AppLayout><Simulator /></AppLayout>} />
          <Route path="/team/:id" element={<AppLayout><TeamProfile /></AppLayout>} />
          <Route path="/player/:id" element={<AppLayout><PlayerProfile /></AppLayout>} />
          <Route path="/referee/:id" element={<AppLayout><RefereeProfile /></AppLayout>} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
