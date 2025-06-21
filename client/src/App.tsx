import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import Dashboard from "@/pages/Dashboard";
import Scorecard from "@/pages/Scorecard";
import Courses from "@/pages/Courses";
import Stats from "@/pages/Stats";
import BottomNavigation from "@/components/BottomNavigation";
import PWAInstallPrompt from "@/components/PWAInstallPrompt";

function Router() {
  return (
    <div className="pb-20"> {/* Add padding for bottom navigation */}
      <Switch>
        <Route path="/" component={Dashboard} />
        <Route path="/scorecard" component={Scorecard} />
        <Route path="/courses" component={Courses} />
        <Route path="/stats" component={Stats} />
        <Route path="/profile" component={() => <div className="p-4">Profile page coming soon!</div>} />
        <Route component={NotFound} />
      </Switch>
      <BottomNavigation />
      <PWAInstallPrompt />
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
