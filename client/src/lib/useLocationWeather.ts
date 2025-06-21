import { useState, useEffect } from 'react';

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
          setError(`Failed to fetch weather: ${weatherError.message}`);
        }

        setLoading(false);
      },
      (geoError) => {
        setError(`Location error: ${geoError.message}`);
        setLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000 // 5 minutes
      }
    );
  }, []);

  return { coordinates, weather, error, loading };
}
