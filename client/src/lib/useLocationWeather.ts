import { useState, useEffect } from 'react';

// Capacitor imports - these will be available when running as native app
declare global {
  interface Window {
    Capacitor?: {
      isNativePlatform: () => boolean;
    };
  }
}

interface CapacitorGeolocation {
  requestPermissions: () => Promise<{ location: string }>;
  getCurrentPosition: (options?: any) => Promise<{
    coords: {
      latitude: number;
      longitude: number;
    };
  }>;
}

interface Coordinates {
  latitude: number;
  longitude: number;
}

interface Weather {
  temp: number;
  description: string;
  icon: string;
  humidity: number;
  windSpeed: number;
}

interface LocationWeatherResult {
  coordinates: Coordinates | null;
  weather: Weather | null;
  error: string | null;
  loading: boolean;
}

export default function useLocationWeather(): LocationWeatherResult {
  const [coordinates, setCoordinates] = useState<Coordinates | null>(null);
  const [weather, setWeather] = useState<Weather | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const requestLocationAndWeather = async () => {
      try {
        // Check if running as native app with Capacitor
        const isNative = window.Capacitor?.isNativePlatform?.() || false;
        
        if (isNative) {
          // Use Capacitor for native app
          const CapacitorGeolocation = (window as any).Capacitor?.Plugins?.Geolocation;
          
          if (CapacitorGeolocation) {
            // Request permissions first
            const permissionStatus = await CapacitorGeolocation.requestPermissions();
            console.log("GPS Permission:", permissionStatus);
            
            if (permissionStatus.location === 'granted') {
              const position = await CapacitorGeolocation.getCurrentPosition({
                enableHighAccuracy: true,
                timeout: 10000
              });
              
              const coords = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude
              };
              setCoordinates(coords);
              await fetchWeather(coords);
            } else {
              setError('Location permission denied');
            }
          } else {
            setError('Capacitor Geolocation not available');
          }
        } else {
          // Use browser geolocation API for PWA/web
          if (!navigator.geolocation) {
            setError('Geolocation is not supported by this browser');
            setLoading(false);
            return;
          }

          navigator.geolocation.getCurrentPosition(
            async (position) => {
              const coords = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude
              };
              setCoordinates(coords);
              await fetchWeather(coords);
              setLoading(false);
            },
            (geoError) => {
              console.error('Geolocation error:', geoError);
              let errorMessage = 'Location access denied';
              
              switch (geoError.code) {
                case geoError.PERMISSION_DENIED:
                  errorMessage = 'Location permission denied';
                  break;
                case geoError.POSITION_UNAVAILABLE:
                  errorMessage = 'Location information unavailable';
                  break;
                case geoError.TIMEOUT:
                  errorMessage = 'Location request timed out';
                  break;
              }
              
              setError(errorMessage);
              setLoading(false);
            },
            {
              enableHighAccuracy: true,
              timeout: 15000,
              maximumAge: 300000 // 5 minutes
            }
          );
        }
      } catch (error) {
        setError(`Location setup error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        setLoading(false);
      }
    };

    const fetchWeather = async (coords: Coordinates) => {
      try {
        // Fetch weather data from our backend proxy
        const response = await fetch(`/api/weather?lat=${coords.latitude}&lon=${coords.longitude}`);
        
        if (!response.ok) {
          throw new Error(`Weather API error: ${response.statusText}`);
        }

        const data = await response.json();
        
        setWeather({
          temp: Math.round(data.main.temp),
          description: data.weather[0].description,
          icon: data.weather[0].icon,
          humidity: data.main.humidity,
          windSpeed: data.wind.speed
        });
      } catch (weatherError) {
        console.error('Weather fetch error:', weatherError);
        setError(`Failed to fetch weather: ${weatherError instanceof Error ? weatherError.message : 'Unknown error'}`);
      }
    };

    requestLocationAndWeather();
  }, []);

  return { coordinates, weather, error, loading };
}
