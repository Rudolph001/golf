import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MapPin, Navigation, AlertCircle } from "lucide-react";

interface LocationPermissionPromptProps {
  onPermissionGranted: () => void;
}

export default function LocationPermissionPrompt({ onPermissionGranted }: LocationPermissionPromptProps) {
  const [requesting, setRequesting] = useState(false);

  const handleRequestPermission = async () => {
    setRequesting(true);

    try {
      // Check if Capacitor is available (native app)
      const isNative = window.Capacitor?.isNativePlatform?.() || false;
      
      if (isNative) {
        const CapacitorGeolocation = (window as any).Capacitor?.Plugins?.Geolocation;
        if (CapacitorGeolocation) {
          const result = await CapacitorGeolocation.requestPermissions();
          console.log('Native permission result:', result);
          // Always dismiss the modal regardless of result
          onPermissionGranted();
        } else {
          console.error('Capacitor Geolocation not available');
          onPermissionGranted();
        }
      } else {
        // For web/PWA, request location permission
        if (navigator.geolocation) {
          // Use a promise-based approach for better handling
          const requestLocation = () => {
            return new Promise((resolve, reject) => {
              navigator.geolocation.getCurrentPosition(
                (position) => resolve(position),
                (error) => reject(error),
                { 
                  enableHighAccuracy: true, 
                  timeout: 8000, 
                  maximumAge: 300000 
                }
              );
            });
          };

          try {
            const position = await requestLocation();
            console.log('Location permission granted:', position);
          } catch (error) {
            console.log('Location permission denied or failed:', error);
          }
          
          // Always dismiss the modal after attempt
          onPermissionGranted();
        } else {
          console.error('Geolocation not supported');
          onPermissionGranted();
        }
      }
    } catch (error) {
      console.error('Permission request error:', error);
      onPermissionGranted();
    } finally {
      setRequesting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <Card className="max-w-md w-full bg-white p-6">
        <div className="text-center">
          <div className="w-16 h-16 bg-golf-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <MapPin className="w-8 h-8 text-golf-green-600" />
          </div>
          
          <h3 className="text-xl font-heading font-bold text-slate-800 mb-2">
            Enable Location Access
          </h3>
          
          <p className="text-slate-600 mb-6">
            GolfTracker Pro needs access to your location to provide weather updates and find nearby golf courses for the best experience.
          </p>
          
          <div className="space-y-3 mb-6">
            <div className="flex items-center space-x-3 text-sm text-slate-600">
              <Navigation className="w-4 h-4 text-golf-green-500" />
              <span>Real-time weather on the course</span>
            </div>
            <div className="flex items-center space-x-3 text-sm text-slate-600">
              <MapPin className="w-4 h-4 text-golf-green-500" />
              <span>Find nearby golf courses</span>
            </div>
            <div className="flex items-center space-x-3 text-sm text-slate-600">
              <AlertCircle className="w-4 h-4 text-golf-green-500" />
              <span>Track your rounds accurately</span>
            </div>
          </div>
          
          <div className="space-y-3">
            <Button
              onClick={handleRequestPermission}
              disabled={requesting}
              className="w-full bg-golf-gradient text-white font-medium"
            >
              {requesting ? 'Requesting Permission...' : 'Allow Location Access'}
            </Button>
            
            <Button
              variant="outline"
              onClick={onPermissionGranted}
              className="w-full"
            >
              Skip for Now
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}