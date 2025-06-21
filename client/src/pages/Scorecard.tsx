import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, MoreVertical } from "lucide-react";
import { Round, Course, Shot } from "@shared/schema";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Link } from "wouter";

const CLUBS = ["Driver", "3 Wood", "5 Wood", "3 Iron", "4 Iron", "5 Iron", "6 Iron", "7 Iron", "8 Iron", "9 Iron", "PW", "SW", "LW", "Putter"];
const RESULTS = ["Fairway", "Rough", "Bunker", "Green"];

export default function Scorecard() {
  const [currentHole, setCurrentHole] = useState(1);
  const [selectedScore, setSelectedScore] = useState<number | null>(null);
  const [selectedClub, setSelectedClub] = useState<string | null>(null);
  const [selectedResult, setSelectedResult] = useState<string | null>(null);

  const { data: currentRound } = useQuery<Round | null>({
    queryKey: ['/api/rounds/current?userId=1'],
  });

  const { data: courses = [] } = useQuery<Course[]>({
    queryKey: ['/api/courses'],
  });

  const { data: shots = [] } = useQuery<Shot[]>({
    queryKey: ['/api/shots', { roundId: currentRound?.id }],
    enabled: !!currentRound?.id,
  });

  const currentCourse = currentRound && courses.find(c => c.id === currentRound.courseId);
  const currentShot = shots.find(s => s.hole === currentHole);

  const createShotMutation = useMutation({
    mutationFn: async (shotData: any) => {
      return apiRequest('POST', '/api/shots', shotData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/shots'] });
      queryClient.invalidateQueries({ queryKey: ['/api/rounds/current'] });
    },
  });

  const updateShotMutation = useMutation({
    mutationFn: async ({ id, ...data }: any) => {
      return apiRequest('PATCH', `/api/shots/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/shots'] });
      queryClient.invalidateQueries({ queryKey: ['/api/rounds/current'] });
    },
  });

  const updateRoundMutation = useMutation({
    mutationFn: async ({ id, ...data }: any) => {
      return apiRequest('PATCH', `/api/rounds/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/rounds/current'] });
    },
  });

  const handleSaveShot = () => {
    if (!currentRound || !selectedScore) return;

    const shotData = {
      roundId: currentRound.id,
      hole: currentHole,
      score: selectedScore,
      club: selectedClub,
      result: selectedResult,
    };

    if (currentShot) {
      updateShotMutation.mutate({ id: currentShot.id, ...shotData });
    } else {
      createShotMutation.mutate(shotData);
    }
  };

  const handleNextHole = () => {
    handleSaveShot();
    
    if (currentHole < 18) {
      setCurrentHole(currentHole + 1);
      // Update round's current hole
      if (currentRound) {
        updateRoundMutation.mutate({
          id: currentRound.id,
          currentHole: currentHole + 1
        });
      }
    } else {
      // Complete the round
      if (currentRound) {
        const totalScore = shots.reduce((sum, shot) => sum + (shot.score || 0), 0) + (selectedScore || 0);
        updateRoundMutation.mutate({
          id: currentRound.id,
          completed: true,
          totalScore
        });
      }
    }

    // Reset form
    setSelectedScore(null);
    setSelectedClub(null);
    setSelectedResult(null);
  };

  if (!currentRound || !currentCourse) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <Card className="p-6 text-center">
          <h2 className="text-xl font-bold mb-4">No Active Round</h2>
          <p className="text-slate-600 mb-4">You need to start a round first.</p>
          <Link href="/courses">
            <Button className="bg-golf-gradient text-white">Select Course</Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-golf-gradient text-white p-4">
        <div className="flex items-center justify-between mb-4">
          <Link href="/">
            <Button variant="ghost" size="sm" className="p-2 -ml-2 text-white hover:bg-white/20">
              <ArrowLeft className="w-6 h-6" />
            </Button>
          </Link>
          <div className="text-center">
            <h2 className="font-heading font-bold text-lg">{currentCourse.name}</h2>
            <p className="text-white/80 text-sm">Round in Progress</p>
          </div>
          <Button variant="ghost" size="sm" className="p-2 -mr-2 text-white hover:bg-white/20">
            <MoreVertical className="w-6 h-6" />
          </Button>
        </div>
        
        {/* Round Stats */}
        <div className="grid grid-cols-4 gap-4 bg-white/10 rounded-xl p-3">
          <div className="text-center">
            <div className="text-lg font-bold">{currentHole}</div>
            <p className="text-xs text-white/70">Hole</p>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-golf-gold-400">
              {currentRound.totalScore || 0}
            </div>
            <p className="text-xs text-white/70">Total</p>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold">{currentCourse.par}</div>
            <p className="text-xs text-white/70">Par</p>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold">--</div>
            <p className="text-xs text-white/70">Yards</p>
          </div>
        </div>
      </div>

      {/* Hole Navigation */}
      <div className="p-4 border-b border-slate-200">
        <div className="flex space-x-2 overflow-x-auto hide-scrollbar pb-2">
          {Array.from({ length: 18 }, (_, i) => i + 1).map((hole) => {
            const holeShot = shots.find(s => s.hole === hole);
            const isCompleted = !!holeShot;
            const isCurrent = hole === currentHole;
            
            return (
              <button
                key={hole}
                onClick={() => setCurrentHole(hole)}
                className={`flex-shrink-0 w-12 h-12 rounded-full font-bold flex items-center justify-center ${
                  isCurrent
                    ? 'bg-golf-gold-500 text-white ring-4 ring-golf-gold-200'
                    : isCompleted
                    ? 'bg-golf-green-500 text-white'
                    : 'bg-slate-300 text-slate-600'
                }`}
              >
                {hole}
              </button>
            );
          })}
        </div>
      </div>

      {/* Current Hole Scoring */}
      <div className="p-4">
        <Card className="shadow-lg p-6 mb-6">
          <div className="text-center mb-6">
            <h3 className="text-2xl font-heading font-bold text-slate-800">Hole {currentHole}</h3>
            <div className="flex justify-center items-center space-x-4 mt-2">
              <span className="text-slate-600">Par {Math.round(currentCourse.par / 18)}</span>
              <span className="text-slate-400">•</span>
              <span className="text-slate-600">-- yards</span>
            </div>
          </div>

          {/* Score Input */}
          <div className="mb-6">
            <p className="text-sm font-medium text-slate-700 mb-3">Score</p>
            <div className="grid grid-cols-7 gap-2">
              {[1, 2, 3, 4, 5, 6, 7].map((score) => (
                <Button
                  key={score}
                  variant={selectedScore === score ? "default" : "outline"}
                  className={`h-12 rounded-lg font-bold ${
                    selectedScore === score
                      ? 'bg-golf-green-500 text-white ring-4 ring-golf-green-200'
                      : ''
                  }`}
                  onClick={() => setSelectedScore(score)}
                >
                  {score}
                </Button>
              ))}
            </div>
          </div>

          {/* Club Selection */}
          <div className="mb-6">
            <p className="text-sm font-medium text-slate-700 mb-3">Club Used</p>
            <div className="grid grid-cols-4 gap-2 max-h-32 overflow-y-auto">
              {CLUBS.map((club) => (
                <Button
                  key={club}
                  variant={selectedClub === club ? "default" : "outline"}
                  className={`h-10 rounded-lg text-sm font-medium ${
                    selectedClub === club
                      ? 'bg-golf-green-500 text-white ring-2 ring-golf-green-200'
                      : ''
                  }`}
                  onClick={() => setSelectedClub(club)}
                >
                  {club}
                </Button>
              ))}
            </div>
          </div>

          {/* Shot Result */}
          <div className="mb-6">
            <p className="text-sm font-medium text-slate-700 mb-3">Shot Result</p>
            <div className="grid grid-cols-2 gap-2">
              {RESULTS.map((result) => (
                <Button
                  key={result}
                  variant={selectedResult === result ? "default" : "outline"}
                  className={`h-10 rounded-lg text-sm font-medium ${
                    selectedResult === result
                      ? 'bg-golf-green-500 text-white ring-2 ring-golf-green-200'
                      : ''
                  }`}
                  onClick={() => setSelectedResult(result)}
                >
                  {result}
                </Button>
              ))}
            </div>
          </div>
        </Card>

        {/* Action Buttons */}
        <div className="space-y-3">
          <Button 
            className="w-full bg-golf-gradient text-white rounded-xl p-4 font-semibold shadow-lg"
            onClick={handleNextHole}
            disabled={!selectedScore}
          >
            {currentHole === 18 ? 'Finish Round' : 'Next Hole'}
          </Button>
          <Link href="/">
            <Button 
              variant="outline" 
              className="w-full rounded-xl p-4 font-semibold"
            >
              Save & Exit
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
