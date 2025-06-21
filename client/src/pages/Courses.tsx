import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Search, MapPin, Star } from "lucide-react";
import { Course } from "@shared/schema";
import { apiRequest, queryClient } from "@/lib/queryClient";
import useLocationWeather from "@/lib/useLocationWeather";
import { useLocation } from "wouter";

export default function Courses() {
  const [, setLocation] = useLocation();
  const { coordinates } = useLocationWeather();
  const [activeTab, setActiveTab] = useState("nearby");

  const { data: allCourses = [] } = useQuery<Course[]>({
    queryKey: ['/api/courses'],
  });

  const { data: nearbyCourses = [] } = useQuery<Course[]>({
    queryKey: ['/api/courses/nearby', { lat: coordinates?.latitude, lng: coordinates?.longitude }],
    enabled: !!coordinates,
  });

  const createRoundMutation = useMutation({
    mutationFn: async (courseId: number) => {
      return apiRequest('POST', '/api/rounds', {
        userId: 1, // Mock user ID
        courseId,
        currentHole: 1,
        totalScore: 0,
        completed: false,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/rounds/current'] });
      setLocation('/scorecard');
    },
  });

  const handleSelectCourse = (courseId: number) => {
    createRoundMutation.mutate(courseId);
  };

  const coursesToShow = activeTab === "nearby" ? nearbyCourses : allCourses;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading font-bold text-xl text-slate-800">Find Courses</h2>
          <Button variant="ghost" size="sm" className="p-2 -mr-2">
            <Search className="w-6 h-6 text-slate-600" />
          </Button>
        </div>
        
        {/* Location indicator */}
        <div className="flex items-center space-x-2 mt-2">
          <MapPin className="w-4 h-4 text-golf-green-600" />
          <span className="text-sm text-slate-600">
            {coordinates 
              ? `${coordinates.latitude.toFixed(2)}, ${coordinates.longitude.toFixed(2)}`
              : "Location not available"
            }
          </span>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="bg-white border-b border-slate-200 p-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="nearby">Nearby</TabsTrigger>
            <TabsTrigger value="favorites">Favorites</TabsTrigger>
            <TabsTrigger value="all">All</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Course List */}
      <div className="p-4 space-y-4">
        {coursesToShow.length === 0 ? (
          <Card className="p-6 text-center">
            <p className="text-slate-500">
              {activeTab === "nearby" && !coordinates
                ? "Enable location services to see nearby courses"
                : "No courses found"
              }
            </p>
          </Card>
        ) : (
          coursesToShow.map((course) => (
            <Card key={course.id} className="shadow-sm border border-slate-100 overflow-hidden">
              {/* Course Image */}
              <div 
                className="h-32 bg-cover bg-center"
                style={{
                  backgroundImage: `url('https://images.unsplash.com/photo-1535131749006-b7f58c99034b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&h=400')`
                }}
              >
                <div className="h-full bg-gradient-to-t from-black/30 to-transparent flex items-end p-4">
                  <div className="flex items-center space-x-2">
                    <div className="bg-golf-gold-500 text-white px-2 py-1 rounded-full text-xs font-bold flex items-center">
                      <Star className="w-3 h-3 mr-1" />
                      4.8
                    </div>
                    {coordinates && course.latitude && course.longitude && (
                      <span className="text-white text-sm font-medium">
                        {/* Calculate rough distance */}
                        {Math.round(
                          Math.sqrt(
                            Math.pow(coordinates.latitude - parseFloat(course.latitude), 2) +
                            Math.pow(coordinates.longitude - parseFloat(course.longitude), 2)
                          ) * 111
                        )} km
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-semibold text-slate-800">{course.name}</h3>
                    <p className="text-sm text-slate-500">
                      {course.holes} holes • Par {course.par}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-golf-green-600">
                      ${course.greenFee ? parseFloat(course.greenFee).toFixed(0) : 'N/A'}
                    </p>
                    <p className="text-xs text-slate-500">Green fee</p>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 text-sm text-slate-600">
                    {course.slope && <span>Slope: {course.slope}</span>}
                    {course.rating && <span>Rating: {course.rating}</span>}
                  </div>
                  <Button 
                    className="bg-golf-green-500 text-white px-4 py-2 rounded-lg font-medium hover:bg-golf-green-600"
                    onClick={() => handleSelectCourse(course.id)}
                    disabled={createRoundMutation.isPending}
                  >
                    {createRoundMutation.isPending ? 'Starting...' : 'Select'}
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
