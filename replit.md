# Pinaclepoint Golf Tournament Management System

## Overview

This is a Flask-based web application for managing a family golf tournament at Pinaclepoint Golf Estate. The application handles player registration, score tracking across multiple tournament formats, and provides both admin and public-facing interfaces for tournament management.

## System Architecture

### Backend Architecture
- **Framework**: Flask 3.1.1 with Python 3.11
- **Database**: SQLAlchemy 2.0+ with SQLite (default) or PostgreSQL support
- **Database Models**: Traditional SQLAlchemy models using DeclarativeBase
- **Session Management**: Flask built-in sessions with configurable secret key
- **Deployment**: Gunicorn WSGI server with autoscale deployment target

### Frontend Architecture
- **Templates**: Jinja2 templating with Bootstrap 5 dark theme
- **Styling**: Bootstrap CSS with custom golf-themed styling
- **JavaScript**: Vanilla JavaScript for scorecard calculations and mobile-friendly inputs
- **Icons**: Font Awesome 6.4.0 for UI iconography

### Database Schema
- **Tournament**: Stores tournament metadata (name, dates, prize pool)
- **Player**: Player information linked to tournaments with handicap tracking
- **Round**: Individual tournament rounds with different formats (stroke play, stableford, scramble)
- **Score**: Hole-by-hole scoring data with calculated totals

## Key Components

### Models (models.py)
- Tournament management with configurable prize pools
- Player registration with handicap support
- Round configuration for different tournament formats
- Score tracking with individual hole data storage

### Routes (routes.py)
- Tournament overview and leaderboard display
- Player setup and registration with dynamic prize preview
- Admin panel for score management with clear/reset functionality
- Scorecard entry interface with hole-by-hole tracking
- Public scoreboard for TV display with real-time updates
- Dynamic prize distribution calculation based on player count

### Templates
- **Base template**: Consistent navigation and Bootstrap theming
- **Index**: Tournament overview with leaderboard
- **Admin**: Score management interface
- **Scorecard**: Individual player score entry
- **Scoreboard**: Public display optimized for TV viewing

## Data Flow

1. **Tournament Setup**: Admin creates tournament and registers players
2. **Round Management**: System supports 3-day tournament with different formats:
   - Day 1: Stroke Play (traditional scoring)
   - Day 2: Stableford (points-based scoring)
   - Day 3: Scramble (team format)
3. **Score Entry**: Hole-by-hole score tracking through admin interface
4. **Leaderboard Calculation**: Real-time standings based on tournament format
5. **Prize Distribution**: Dynamic prize pool allocation ensuring all players win money, adjusting based on actual player count

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **Gunicorn**: Production WSGI server
- **psycopg2-binary**: PostgreSQL adapter
- **email-validator**: Input validation utilities

### Frontend Dependencies
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome**: Icon library
- **Custom CSS**: Golf-themed styling enhancements

## Deployment Strategy

### Replit Configuration
- **Runtime**: Python 3.11 with Nix package management
- **Database**: PostgreSQL and OpenSSL packages available
- **Deployment**: Autoscale deployment with Gunicorn binding
- **Development**: Hot reload enabled for development workflow

### Environment Variables
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `SESSION_SECRET`: Flask session encryption key
- Port binding: 0.0.0.0:5000 for external access

### Production Considerations
- Database connection pooling with 300-second recycle
- Proxy fix middleware for deployment behind reverse proxy
- Automatic table creation on application startup

## Recent Changes
- June 14, 2025: Initial setup with R600,000 prize pool
- June 14, 2025: Updated to R1,000,000 prize pool as requested
- June 14, 2025: Implemented dynamic prize distribution system that adjusts based on actual number of players registered
- June 14, 2025: Fixed admin panel button functionality for clearing scores and resetting tournaments
- June 14, 2025: Tournament name updated to "The Pinicalpoint Family Champions Cup"

## Changelog
- June 14, 2025. Initial tournament system setup
- June 14, 2025. Prize pool increased to R1,000,000 with dynamic distribution
- June 14, 2025. Admin functionality enhanced with working buttons

## User Preferences

Preferred communication style: Simple, everyday language.