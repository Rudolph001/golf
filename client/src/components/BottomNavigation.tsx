import { Home, Edit3, Map, BarChart2, User } from "lucide-react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";

const navItems = [
  { path: "/", icon: Home, label: "Home" },
  { path: "/scorecard", icon: Edit3, label: "Round" },
  { path: "/courses", icon: Map, label: "Courses" },
  { path: "/stats", icon: BarChart2, label: "Stats" },
  { path: "/profile", icon: User, label: "Profile" },
];

export default function BottomNavigation() {
  const [location, setLocation] = useLocation();

  return (
    <div className="fixed bottom-0 left-1/2 transform -translate-x-1/2 w-full max-w-md bg-white border-t border-slate-200 px-4 py-2 safe-area-inset-bottom">
      <div className="flex items-center justify-around">
        {navItems.map(({ path, icon: Icon, label }) => {
          const isActive = location === path;
          return (
            <Button
              key={path}
              variant="ghost"
              size="sm"
              className={`flex flex-col items-center space-y-1 p-2 ${
                isActive ? 'text-golf-green-600' : 'text-slate-400'
              }`}
              onClick={() => setLocation(path)}
            >
              <Icon className="w-6 h-6" />
              <span className="text-xs font-medium">{label}</span>
            </Button>
          );
        })}
      </div>
    </div>
  );
}
