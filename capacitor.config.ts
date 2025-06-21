import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.golftracker.pro',
  appName: 'GolfTracker Pro',
  webDir: 'client/dist',
  server: {
    androidScheme: 'https'
  },
  plugins: {
    Geolocation: {
      permissions: {
        location: "always"
      },
      enableHighAccuracy: true
    },
    Camera: {
      permissions: {
        camera: "prompt",
        photos: "prompt"
      }
    },
    PushNotifications: {
      presentationOptions: ["badge", "sound", "alert"]
    }
  }
};

export default config;