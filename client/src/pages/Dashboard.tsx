import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlayCircle, BarChart2, MapPin, CloudSun } from "lucide-react";
import useLocationWeather from "@/lib/useLocationWeather";
import { Round, Course } from "@shared/schema";
import { Link } from "wouter";

export default function Dashboard() {
  const { coordinates, weather, error, loading } = useLocationWeather();
  
  const { data: currentRound } = useQuery<Round | null>({
    queryKey: ['/api/rounds/current?userId=1'],
  });

  const { data: recentRounds = [] } = useQuery<Round[]>({
    queryKey: ['/api/rounds?userId=1'],
  });

  const { data: courses = [] } = useQuery<Course[]>({
    queryKey: ['/api/courses'],
  });

  const currentCourse = currentRound && courses.find(c => c.id === currentRound.courseId);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header with course background */}
      <div 
        className="relative h-48 bg-golf-gradient"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1535131749006-b7f58c99034b?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=800&h=400')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-black/20 to-black/60"></div>
        <div className="relative p-4 text-white">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-2xl font-heading font-bold">Good Morning</h1>
              <p className="text-white/80 text-sm">Ready for your round?</p>
            </div>
            <div className="text-right">
              {loading && (
                <div className="text-sm text-white/70">Loading weather...</div>
              )}
              {error && (
                <div className="text-sm text-red-300">Weather unavailable</div>
              )}
              {weather && (
                <div className="flex items-center space-x-2 mb-1">
                  <CloudSun className="w-5 h-5" />
                  <span className="text-sm font-medium">{weather.temp}°F</span>
                </div>
              )}
              {coordinates && (
                <p className="text-xs text-white/70">
                  {coordinates.latitude.toFixed(4)}, {coordinates.longitude.toFixed(4)}
                </p>
              )}
            </div>
          </div>
          
          {/* Current Round Status */}
          <div className="glass-effect rounded-xl p-4 mt-8">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-white/80 text-xs uppercase tracking-wide">Current Round</p>
                {currentRound && currentCourse ? (
                  <>
                    <h3 className="text-lg font-semibold">{currentCourse.name}</h3>
                    <p className="text-sm text-white/70">
                      Hole {currentRound.currentHole} • Par {currentCourse.par}
                    </p>
                  </>
                ) : (
                  <>
                    <h3 className="text-lg font-semibold">No Active Round</h3>
                    <p className="text-sm text-white/70">Start a new round to begin tracking</p>
                  </>
                )}
              </div>
              <div className="text-right">
                {currentRound?.totalScore ? (
                  <>
                    <div className="text-2xl font-bold text-golf-gold-400">
                      {currentRound.totalScore > 0 ? '+' : ''}{currentRound.totalScore}
                    </div>
                    <p className="text-xs text-white/70">Score</p>
                  </>
                ) : (
                  <>
                    <div className="text-2xl font-bold text-golf-gold-400">--</div>
                    <p className="text-xs text-white/70">Score</p>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats Cards */}
      <div className="p-4 -mt-4 relative z-10">
        <div className="grid grid-cols-3 gap-3 mb-6">
          <Card className="p-4 shadow-golf">
            <div className="text-center">
              <div className="text-2xl font-bold text-slate-800">8.4</div>
              <p className="text-xs text-slate-500 uppercase tracking-wide">Handicap</p>
            </div>
          </Card>
          <Card className="p-4 shadow-golf">
            <div className="text-center">
              <div className="text-2xl font-bold text-golf-green-600">78</div>
              <p className="text-xs text-slate-500 uppercase tracking-wide">Avg Score</p>
            </div>
          </Card>
          <Card className="p-4 shadow-golf">
            <div className="text-center">
              <div className="text-2xl font-bold text-golf-gold-600">{recentRounds.length}</div>
              <p className="text-xs text-slate-500 uppercase tracking-wide">Rounds</p>
            </div>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="space-y-3">
          <Link href="/scorecard">
            <Button className="w-full bg-golf-gradient text-white rounded-xl p-4 shadow-lg">
              <div className="flex items-center justify-center space-x-3">
                <PlayCircle className="w-6 h-6" />
                <span className="font-semibold">
                  {currentRound ? 'Continue Round' : 'Start New Round'}
                </span>
              </div>
            </Button>
          </Link>
          
          <div className="grid grid-cols-2 gap-3">
            <Link href="/stats">
              <Button variant="outline" className="border-2 border-golf-green-500 text-golf-green-700 rounded-xl p-3">
                <div className="flex items-center justify-center space-x-2">
                  <BarChart2 className="w-5 h-5" />
                  <span className="font-medium">Stats</span>
                </div>
              </Button>
            </Link>
            <Link href="/courses">
              <Button variant="outline" className="rounded-xl p-3">
                <div className="flex items-center justify-center space-x-2">
                  <MapPin className="w-5 h-5" />
                  <span className="font-medium">Courses</span>
                </div>
              </Button>
            </Link>
          </div>
        </div>

        {/* Recent Rounds */}
        <div className="mt-8">
          <h3 className="font-heading font-semibold text-lg text-slate-800 mb-4">Recent Rounds</h3>
          {recentRounds.length === 0 ? (
            <Card className="p-6 text-center">
              <p className="text-slate-500">No rounds yet. Start your first round!</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {recentRounds.slice(0, 3).map((round) => {
                const course = courses.find(c => c.id === round.courseId);
                return (
                  <Card key={round.id} className="p-4 shadow-sm border border-slate-100">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-medium text-slate-800">
                          {course?.name || 'Unknown Course'}
                        </h4>
                        <p className="text-sm text-slate-500">
                          {round.date ? new Date(round.date).toLocaleDateString() : 'Unknown date'} • 18 holes
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold text-slate-800">
                          {round.totalScore || '--'}
                        </div>
                        {round.totalScore && (
                          <p className="text-xs text-golf-green-600">
                            {round.totalScore > 0 ? '+' : ''}{round.totalScore}
                          </p>
                        )}
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
