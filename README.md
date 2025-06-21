<<<<<<< HEAD
# golf
=======
# GolfTracker Pro - Professional Golf Analytics PWA

A comprehensive mobile-first Progressive Web App for golf tracking, analytics, and performance monitoring.

## Features

### Core Functionality
- **GPS-Based Weather Integration** - Real-time weather data using location services
- **Course Discovery** - Find golf courses near your location
- **Round Tracking** - Hole-by-hole scoring with club selection and shot results
- **Performance Analytics** - Detailed statistics and performance trends
- **PWA Capabilities** - Installable app with offline support

### Mobile Features
- Touch-optimized interface
- GPS location tracking
- Weather integration with OpenWeatherMap
- Service worker for offline functionality
- Background sync capabilities

## Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Node.js, Express.js, TypeScript
- **Database**: In-memory storage with PostgreSQL schema
- **State Management**: TanStack Query
- **Mobile**: PWA with Capacitor support

## Getting Started

### Prerequisites
- Node.js 20+
- OpenWeatherMap API key

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   - `OPENWEATHERMAP_API_KEY` - Your OpenWeatherMap API key

4. Start the development server:
   ```bash
   npm run dev
   ```

The app will be available at `http://localhost:5000`

## Android App Development

### Capacitor Setup

1. Install Capacitor:
   ```bash
   npm install @capacitor/core @capacitor/cli @capacitor/android
   ```

2. Initialize Capacitor:
   ```bash
   npx cap init
   ```

3. Add Android platform:
   ```bash
   npx cap add android
   ```

4. Add required permissions to `android/app/src/main/AndroidManifest.xml`:
   ```xml
   <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
   <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
   <uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />
   <uses-permission android:name="android.permission.INTERNET" />
   <uses-permission android:name="android.permission.CAMERA" />
   <uses-permission android:name="android.permission.VIBRATE" />
   ```

5. Build and sync:
   ```bash
   npm run build
   npx cap sync
   npx cap open android
   ```

## PWA Features

### Installation
- Automatic install prompt after 3 seconds
- Manifest with app shortcuts
- Service worker for offline functionality

### Offline Support
- Cached resources for offline access
- Background sync for data synchronization
- Push notifications support

## API Endpoints

### Courses
- `GET /api/courses` - Get all courses
- `GET /api/courses/nearby?lat=&lng=` - Get nearby courses
- `GET /api/courses/:id` - Get specific course

### Rounds
- `GET /api/rounds?userId=` - Get user's rounds
- `GET /api/rounds/current?userId=` - Get current active round
- `POST /api/rounds` - Create new round
- `PATCH /api/rounds/:id` - Update round

### Shots
- `GET /api/shots?roundId=` - Get shots for round
- `POST /api/shots` - Create shot
- `PATCH /api/shots/:id` - Update shot

### Weather
- `GET /api/weather?lat=&lon=` - Get weather data

## Database Schema

### Users
- id, username, password, handicap

### Courses  
- id, name, location, par, rating, slope, holes, greenFee, latitude, longitude

### Rounds
- id, userId, courseId, date, totalScore, completed, weather, currentHole

### Shots
- id, roundId, hole, score, club, result, distance

## Performance Features

- Lazy loading of components
- Optimized image loading
- Battery-efficient GPS polling
- Responsive design for all devices

## Deployment

### Replit Deployment
The app is configured for Replit deployment with:
- Express server serving both API and static files
- Environment variable support
- HTTPS ready for PWA installation

### Building for Production
```bash
npm run build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details
>>>>>>> 54d2e8e (Improve app functionality by adding new features and fixing a few bugs)
