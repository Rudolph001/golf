"""
Arccos Smart Sensors Integration Module
Handles automatic scorecard population from Arccos shot tracking data
"""

import json
import requests
from datetime import datetime, timedelta
from models import db, Player, Round, Score, ArccosPlayerData, ArccosRoundData
from flask import current_app


class ArccosAPI:
    """Arccos API client for fetching shot tracking data"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or current_app.config.get('ARCCOS_API_KEY')
        self.base_url = "https://api.arccosgolf.com/v2"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_user_rounds(self, user_id, start_date=None, end_date=None):
        """Fetch all rounds for a user within date range"""
        endpoint = f"{self.base_url}/users/{user_id}/rounds"
        params = {}
        
        if start_date:
            params['start_date'] = start_date.strftime('%Y-%m-%d')
        if end_date:
            params['end_date'] = end_date.strftime('%Y-%m-%d')
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching rounds for user {user_id}: {e}")
            return None
    
    def get_round_details(self, round_id):
        """Fetch detailed shot data for a specific round"""
        endpoint = f"{self.base_url}/rounds/{round_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching round details for {round_id}: {e}")
            return None
    
    def get_hole_by_hole_data(self, round_id):
        """Get hole-by-hole shot data with detailed analytics"""
        endpoint = f"{self.base_url}/rounds/{round_id}/holes"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching hole data for round {round_id}: {e}")
            return None


def sync_arccos_data_for_tournament(tournament_id):
    """Sync Arccos data for all connected players in tournament"""
    tournament_players = ArccosPlayerData.query.filter_by(
        tournament_id=tournament_id,
        sync_status='connected'
    ).all()
    
    api = ArccosAPI()
    results = {
        'success': [],
        'errors': [],
        'total_rounds_synced': 0
    }
    
    for arccos_player in tournament_players:
        try:
            player_result = sync_player_arccos_data(arccos_player, api)
            if player_result['success']:
                results['success'].append({
                    'player_name': arccos_player.player.name,
                    'rounds_synced': player_result['rounds_synced']
                })
                results['total_rounds_synced'] += player_result['rounds_synced']
            else:
                results['errors'].append({
                    'player_name': arccos_player.player.name,
                    'error': player_result['error']
                })
        except Exception as e:
            results['errors'].append({
                'player_name': arccos_player.player.name,
                'error': str(e)
            })
    
    return results


def sync_player_arccos_data(arccos_player, api=None):
    """Sync Arccos data for a single player"""
    if not api:
        api = ArccosAPI()
    
    # Get tournament date range for filtering rounds
    tournament = arccos_player.tournament
    tournament_start = tournament.start_date
    tournament_end = tournament_start + timedelta(days=2)  # 3-day tournament
    
    # Fetch rounds from Arccos within tournament dates
    rounds_data = api.get_user_rounds(
        arccos_player.arccos_user_id,
        start_date=tournament_start,
        end_date=tournament_end
    )
    
    if not rounds_data:
        return {'success': False, 'error': 'Failed to fetch rounds from Arccos API'}
    
    rounds_synced = 0
    
    for round_data in rounds_data.get('rounds', []):
        try:
            # Get detailed hole-by-hole data
            hole_data = api.get_hole_by_hole_data(round_data['id'])
            if not hole_data:
                continue
            
            # Match round to tournament day based on date
            round_date = datetime.strptime(round_data['date'], '%Y-%m-%d').date()
            tournament_day = (round_date - tournament_start).days + 1
            
            if tournament_day < 1 or tournament_day > 3:
                continue  # Skip rounds outside tournament dates
            
            # Find corresponding tournament round
            tournament_round = Round.query.filter_by(
                tournament_id=arccos_player.tournament_id,
                day=tournament_day
            ).first()
            
            if not tournament_round:
                continue
            
            # Create or update score record with Arccos data
            score = Score.query.filter_by(
                player_id=arccos_player.player_id,
                round_id=tournament_round.id
            ).first()
            
            if not score:
                score = Score()
                score.player_id = arccos_player.player_id
                score.round_id = tournament_round.id
                db.session.add(score)
            
            # Populate hole scores from Arccos data
            populate_scorecard_from_arccos(score, hole_data['holes'])
            
            # Store detailed round analytics
            store_arccos_round_analytics(
                arccos_player.player_id,
                tournament_round.id,
                round_data,
                hole_data
            )
            
            rounds_synced += 1
            
        except Exception as e:
            print(f"Error processing round {round_data.get('id', 'unknown')}: {e}")
            continue
    
    # Update sync timestamp
    arccos_player.last_sync = datetime.utcnow()
    db.session.commit()
    
    return {'success': True, 'rounds_synced': rounds_synced}


def populate_scorecard_from_arccos(score, holes_data):
    """Fill scorecard with hole-by-hole scores from Arccos data"""
    for hole in holes_data:
        hole_number = hole['hole_number']
        if 1 <= hole_number <= 18:
            # Get total strokes for this hole from Arccos
            total_strokes = hole.get('strokes', 0)
            if total_strokes > 0:
                score.set_hole_score(hole_number, total_strokes)
    
    # Calculate totals after populating all holes
    score.calculate_totals()


def store_arccos_round_analytics(player_id, round_id, round_data, hole_data):
    """Store detailed Arccos analytics for the round"""
    # Create or update ArccosRoundData record
    arccos_round = ArccosRoundData.query.filter_by(
        player_id=player_id,
        round_id=round_id
    ).first()
    
    if not arccos_round:
        arccos_round = ArccosRoundData()
        arccos_round.player_id = player_id
        arccos_round.round_id = round_id
        db.session.add(arccos_round)
    
    # Store round-level statistics
    arccos_round.arccos_round_id = round_data.get('id')
    arccos_round.total_shots = round_data.get('total_shots')
    arccos_round.total_putts = round_data.get('total_putts')
    arccos_round.fairways_hit = round_data.get('fairways_hit')
    arccos_round.fairway_attempts = round_data.get('fairway_attempts')
    arccos_round.greens_in_regulation = round_data.get('greens_in_regulation')
    arccos_round.longest_drive = round_data.get('longest_drive')
    arccos_round.avg_drive_distance = round_data.get('avg_drive_distance')
    
    # Store detailed shot data as JSON
    shot_details = extract_shot_details(hole_data['holes'])
    arccos_round.shot_data = json.dumps(shot_details)


def extract_shot_details(holes_data):
    """Extract detailed shot information for each hole"""
    shot_details = {}
    
    for hole in holes_data:
        hole_number = hole['hole_number']
        shots = []
        
        for shot in hole.get('shots', []):
            shot_info = {
                'shot_number': shot.get('shot_number'),
                'club': shot.get('club'),
                'distance': shot.get('distance'),
                'lie': shot.get('lie'),
                'result': shot.get('result'),
                'coordinates': {
                    'lat': shot.get('latitude'),
                    'lng': shot.get('longitude')
                }
            }
            shots.append(shot_info)
        
        shot_details[str(hole_number)] = {
            'par': hole.get('par'),
            'strokes': hole.get('strokes'),
            'putts': hole.get('putts'),
            'shots': shots,
            'fairway_hit': hole.get('fairway_hit'),
            'green_in_regulation': hole.get('green_in_regulation')
        }
    
    return shot_details


def get_arccos_shot_analysis(player_id, round_id):
    """Get detailed shot analysis for display"""
    arccos_round = ArccosRoundData.query.filter_by(
        player_id=player_id,
        round_id=round_id
    ).first()
    
    if not arccos_round or not arccos_round.shot_data:
        return None
    
    try:
        return json.loads(arccos_round.shot_data)
    except json.JSONDecodeError:
        return None


def auto_sync_all_tournament_data(tournament_id):
    """Automatically sync all Arccos data for tournament (run daily)"""
    print(f"Starting auto-sync for tournament {tournament_id}")
    
    results = sync_arccos_data_for_tournament(tournament_id)
    
    print(f"Sync completed: {len(results['success'])} players synced, {results['total_rounds_synced']} rounds")
    if results['errors']:
        print(f"Errors: {len(results['errors'])} players had sync issues")
        for error in results['errors']:
            print(f"  - {error['player_name']}: {error['error']}")
    
    return results


def get_multi_day_shot_data(player_id, tournament_id):
    """Get shot data for all tournament days for a player"""
    rounds = Round.query.filter_by(tournament_id=tournament_id).order_by(Round.day).all()
    multi_day_data = {}
    
    for round_obj in rounds:
        shot_data = get_arccos_shot_analysis(player_id, round_obj.id)
        if shot_data:
            multi_day_data[f"day_{round_obj.day}"] = {
                'date': round_obj.date.strftime('%Y-%m-%d'),
                'format': round_obj.format,
                'shot_data': shot_data
            }
    
    return multi_day_data