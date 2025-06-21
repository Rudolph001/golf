import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TrendingDown, Target, Filter } from "lucide-react";
import { Round, Shot, Course } from "@shared/schema";

export default function Stats() {
  const { data: rounds = [] } = useQuery<Round[]>({
    queryKey: ['/api/rounds?userId=1'],
  });

  const { data: courses = [] } = useQuery<Course[]>({
    queryKey: ['/api/courses'],
  });

  // Calculate basic stats
  const completedRounds = rounds.filter(r => r.completed);
  const totalRounds = completedRounds.length;
  const averageScore = totalRounds > 0 
    ? Math.round(completedRounds.reduce((sum, r) => sum + (r.totalScore || 0), 0) / totalRounds)
    : 0;

  const recentRounds = completedRounds.slice(-6);
  const improvement = recentRounds.length >= 2 
    ? (recentRounds[0]?.totalScore || 0) - (recentRounds[recentRounds.length - 1]?.totalScore || 0)
    : 0;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading font-bold text-xl text-slate-800">Performance Stats</h2>
          <Button variant="ghost" size="sm" className="p-2 -mr-2">
            <Filter className="w-6 h-6 text-slate-600" />
          </Button>
        </div>
        
        {/* Time period selector */}
        <Tabs defaultValue="30days" className="mt-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="30days">30 Days</TabsTrigger>
            <TabsTrigger value="90days">90 Days</TabsTrigger>
            <TabsTrigger value="year">Year</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="p-4 space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <Card className="p-4 shadow-sm border border-slate-100">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Average Score</h3>
              <div className="w-8 h-8 bg-golf-green-100 rounded-full flex items-center justify-center">
                <TrendingDown className="w-4 h-4 text-golf-green-600" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-800">
              {averageScore || '--'}
            </div>
            <p className="text-xs text-golf-green-600 font-medium">
              {improvement > 0 ? `↓ ${improvement} improvement` : improvement < 0 ? `↑ ${Math.abs(improvement)} higher` : 'No change'}
            </p>
          </Card>
          
          <Card className="p-4 shadow-sm border border-slate-100">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Handicap</h3>
              <div className="w-8 h-8 bg-golf-gold-100 rounded-full flex items-center justify-center">
                <Target className="w-4 h-4 text-golf-gold-600" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-800">8.4</div>
            <p className="text-xs text-golf-green-600 font-medium">↓ 0.8 improvement</p>
          </Card>
        </div>

        {/* Performance Chart */}
        <Card className="p-4 shadow-sm border border-slate-100">
          <h3 className="font-medium text-slate-800 mb-4">Score Trend</h3>
          {recentRounds.length === 0 ? (
            <div className="h-32 flex items-center justify-center text-slate-500">
              No completed rounds yet
            </div>
          ) : (
            <>
              <div className="h-32 bg-gradient-to-t from-golf-green-50 to-transparent rounded-lg flex items-end justify-between p-4">
                {recentRounds.map((round, index) => {
                  const maxScore = Math.max(...recentRounds.map(r => r.totalScore || 0), 100);
                  const height = ((round.totalScore || 0) / maxScore) * 100;
                  return (
                    <div
                      key={round.id}
                      className="w-2 bg-golf-green-500 rounded-t"
                      style={{ height: `${Math.max(height, 10)}%` }}
                    />
                  );
                })}
              </div>
              <div className="flex justify-between text-xs text-slate-500 mt-2">
                <span>{recentRounds.length} rounds ago</span>
                <span>Latest</span>
              </div>
            </>
          )}
        </Card>

        {/* Shot Analytics */}
        <Card className="p-4 shadow-sm border border-slate-100">
          <h3 className="font-medium text-slate-800 mb-4">Shot Accuracy</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Fairways Hit</span>
              <div className="flex items-center space-x-3">
                <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-golf-green-500 rounded-full" style={{ width: '72%' }} />
                </div>
                <span className="text-sm font-medium text-slate-800">72%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Greens in Regulation</span>
              <div className="flex items-center space-x-3">
                <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-golf-green-500 rounded-full" style={{ width: '65%' }} />
                </div>
                <span className="text-sm font-medium text-slate-800">65%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Up & Down</span>
              <div className="flex items-center space-x-3">
                <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-golf-gold-500 rounded-full" style={{ width: '45%' }} />
                </div>
                <span className="text-sm font-medium text-slate-800">45%</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Club Performance */}
        <Card className="p-4 shadow-sm border border-slate-100">
          <h3 className="font-medium text-slate-800 mb-4">Club Performance</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-golf-green-100 rounded-full flex items-center justify-center">
                  <span className="text-xs font-bold text-golf-green-700">D</span>
                </div>
                <div>
                  <p className="font-medium text-slate-800">Driver</p>
                  <p className="text-xs text-slate-500">Avg 285 yards</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-slate-800">68% Fairway</p>
                <p className="text-xs text-slate-500">24 uses</p>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-golf-green-100 rounded-full flex items-center justify-center">
                  <span className="text-xs font-bold text-golf-green-700">7</span>
                </div>
                <div>
                  <p className="font-medium text-slate-800">7 Iron</p>
                  <p className="text-xs text-slate-500">Avg 155 yards</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-slate-800">74% Green</p>
                <p className="text-xs text-slate-500">31 uses</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Recent Rounds Summary */}
        <Card className="p-4 shadow-sm border border-slate-100">
          <h3 className="font-medium text-slate-800 mb-4">Recent Performance</h3>
          {completedRounds.length === 0 ? (
            <p className="text-slate-500 text-center py-4">No completed rounds yet</p>
          ) : (
            <div className="space-y-3">
              {completedRounds.slice(-3).reverse().map((round) => {
                const course = courses.find(c => c.id === round.courseId);
                return (
                  <div key={round.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div>
                      <p className="font-medium text-slate-800">
                        {course?.name || 'Unknown Course'}
                      </p>
                      <p className="text-xs text-slate-500">
                        {round.date ? new Date(round.date).toLocaleDateString() : 'Unknown date'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-slate-800">
                        {round.totalScore || '--'}
                      </p>
                      {round.totalScore && (
                        <p className="text-xs text-slate-500">
                          {round.totalScore > 0 ? '+' : ''}{round.totalScore}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
