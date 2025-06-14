from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Tournament, Player, Round, Score, PINACLEPOINT_COURSE
from datetime import datetime, date
from sqlalchemy import func

def get_prize_distribution(player_count):
    """Calculate dynamic prize distribution ensuring all players win money"""
    total_prize = 1000000  # R1,000,000 total
    
    if player_count <= 0:
        return {}
    
    # Ensure minimum prize for everyone
    min_prize = max(20000, total_prize // (player_count * 4))  # Minimum R20,000
    
    # Calculate progressive distribution
    prizes = {}
    
    if player_count == 1:
        prizes[1] = total_prize
    elif player_count == 2:
        prizes[1] = int(total_prize * 0.70)  # 70%
        prizes[2] = int(total_prize * 0.30)  # 30%
    elif player_count == 3:
        prizes[1] = int(total_prize * 0.50)  # 50%
        prizes[2] = int(total_prize * 0.30)  # 30%
        prizes[3] = int(total_prize * 0.20)  # 20%
    elif player_count <= 8:
        # For 4-8 players: Winner gets more, but everyone gets substantial amount
        remaining = total_prize
        
        # 1st place gets 25-30% of total
        prizes[1] = int(total_prize * 0.28)
        remaining -= prizes[1]
        
        # 2nd place gets 18-22% of total
        prizes[2] = int(total_prize * 0.20)
        remaining -= prizes[2]
        
        # 3rd place gets 12-15% of total
        prizes[3] = int(total_prize * 0.14)
        remaining -= prizes[3]
        
        # Distribute remaining among all other players equally
        # But ensure minimum prize
        if player_count > 3:
            remaining_players = player_count - 3
            share_per_player = remaining // remaining_players
            share_per_player = max(share_per_player, min_prize)
            
            for pos in range(4, player_count + 1):
                prizes[pos] = share_per_player
                remaining -= share_per_player
            
            # Add any leftover to top positions
            if remaining > 0:
                prizes[1] += remaining // 2
                prizes[2] += remaining - (remaining // 2)
    else:
        # For more than 8 players
        # Top 3 get larger shares, rest split evenly
        prizes[1] = int(total_prize * 0.25)  # 25%
        prizes[2] = int(total_prize * 0.18)  # 18%
        prizes[3] = int(total_prize * 0.12)  # 12%
        
        remaining = total_prize - prizes[1] - prizes[2] - prizes[3]  # 45% left
        remaining_players = player_count - 3
        
        share_per_player = remaining // remaining_players
        share_per_player = max(share_per_player, min_prize)
        
        for pos in range(4, player_count + 1):
            prizes[pos] = share_per_player
    
    return prizes

TOURNAMENT_FORMATS = {
    1: {'name': 'Stroke Play', 'format': 'stroke_play', 'description': 'Count every stroke, lowest total wins'},
    2: {'name': 'Stableford', 'format': 'stableford', 'description': 'Points based on score vs par, highest points wins'},
    3: {'name': 'Scramble', 'format': 'scramble', 'description': 'Team format, best shot from group'}
}

@app.route('/')
def index():
    """Main tournament overview page"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    players = Player.query.filter_by(tournament_id=tournament.id).all()
    rounds = Round.query.filter_by(tournament_id=tournament.id).order_by(Round.day).all()
    
    # Calculate leaderboard
    leaderboard = calculate_leaderboard(tournament.id)
    
    return render_template('index.html', 
                         tournament=tournament, 
                         players=players, 
                         rounds=rounds,
                         leaderboard=leaderboard,
                         tournament_formats=TOURNAMENT_FORMATS)

@app.route('/setup', methods=['GET', 'POST'])
def player_setup():
    """Setup tournament and players"""
    if request.method == 'POST':
        # Create tournament
        tournament = Tournament(
            name="The Pinicalpoint Family Champions Cup",
            start_date=date.today()
        )
        db.session.add(tournament)
        db.session.flush()  # Get tournament ID
        
        # Create players
        player_names = []
        for i in range(1, 9):  # 8 players
            name = request.form.get(f'player_{i}')
            if name and name.strip():
                player = Player(name=name.strip(), tournament_id=tournament.id)
                db.session.add(player)
                player_names.append(name.strip())
        
        if len(player_names) < 2:
            flash('Please enter at least 2 player names', 'error')
            sample_prizes = get_prize_distribution(8)
            return render_template('player_setup.html', sample_prizes=sample_prizes)
        
        if len(player_names) > 20:
            flash('Maximum 20 players allowed', 'error')
            sample_prizes = get_prize_distribution(8)
            return render_template('player_setup.html', sample_prizes=sample_prizes)
        
        # Create rounds for 3 days
        for day in range(1, 4):
            round_format = TOURNAMENT_FORMATS[day]['format']
            round_obj = Round(
                tournament_id=tournament.id,
                day=day,
                format=round_format,
                date=date.today()
            )
            db.session.add(round_obj)
        
        db.session.commit()
        flash('Tournament setup completed successfully!', 'success')
        return redirect(url_for('index'))
    
    # Show dynamic prize distribution for 8 players as example
    sample_prizes = get_prize_distribution(8)
    return render_template('player_setup.html', sample_prizes=sample_prizes)

@app.route('/scoreboard')
def scoreboard():
    """TV-optimized scoreboard display"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    leaderboard = calculate_leaderboard(tournament.id)
    rounds = Round.query.filter_by(tournament_id=tournament.id).order_by(Round.day).all()
    
    # Get dynamic prize distribution based on actual player count
    player_count = len(Player.query.filter_by(tournament_id=tournament.id).all())
    prize_distribution = get_prize_distribution(player_count)
    
    return render_template('scoreboard.html',
                         tournament=tournament,
                         leaderboard=leaderboard,
                         rounds=rounds,
                         prize_distribution=prize_distribution,
                         tournament_formats=TOURNAMENT_FORMATS)

@app.route('/admin')
def admin():
    """Admin panel for score management"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    players = Player.query.filter_by(tournament_id=tournament.id).all()
    rounds = Round.query.filter_by(tournament_id=tournament.id).order_by(Round.day).all()
    
    return render_template('admin.html',
                         tournament=tournament,
                         players=players,
                         rounds=rounds,
                         tournament_formats=TOURNAMENT_FORMATS)

@app.route('/scorecard/<int:player_id>/<int:round_id>')
def scorecard(player_id, round_id):
    """Detailed scorecard entry for a player and round"""
    player = Player.query.get_or_404(player_id)
    round_obj = Round.query.get_or_404(round_id)
    
    # Get or create score record
    score = Score.query.filter_by(player_id=player_id, round_id=round_id).first()
    if not score:
        score = Score(player_id=player_id, round_id=round_id)
        db.session.add(score)
        db.session.commit()
    
    return render_template('scorecard.html',
                         player=player,
                         round=round_obj,
                         score=score,
                         course=PINACLEPOINT_COURSE,
                         tournament_formats=TOURNAMENT_FORMATS)

@app.route('/update_score', methods=['POST'])
def update_score():
    """Update hole-by-hole scores"""
    score_id = request.form.get('score_id')
    score = Score.query.get_or_404(score_id)
    
    # Update hole scores
    for hole in range(1, 19):
        hole_score = request.form.get(f'hole_{hole}')
        if hole_score and hole_score.isdigit():
            score.set_hole_score(hole, int(hole_score))
    
    # Calculate totals
    score.calculate_totals()
    score.updated_at = datetime.utcnow()
    
    db.session.commit()
    flash('Scorecard updated successfully!', 'success')
    
    return redirect(url_for('scorecard', player_id=score.player_id, round_id=score.round_id))

@app.route('/clear_scores', methods=['POST'])
def clear_scores():
    """Clear all scores but keep players and tournament"""
    try:
        # Delete all scores
        Score.query.delete()
        db.session.commit()
        flash('All scores have been cleared successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error clearing scores. Please try again.', 'error')
    
    return redirect(url_for('admin'))

@app.route('/reset_tournament', methods=['POST'])
def reset_tournament():
    """Complete tournament reset - removes all data"""
    try:
        # Delete all data in reverse dependency order
        Score.query.delete()
        Round.query.delete()
        Player.query.delete()
        Tournament.query.delete()
        db.session.commit()
        flash('Tournament has been completely reset!', 'success')
        return redirect(url_for('player_setup'))
    except Exception as e:
        db.session.rollback()
        flash('Error resetting tournament. Please try again.', 'error')
        return redirect(url_for('admin'))

def calculate_leaderboard(tournament_id):
    """Calculate tournament leaderboard with cumulative scores"""
    players = Player.query.filter_by(tournament_id=tournament_id).all()
    leaderboard = []
    
    for player in players:
        player_data = {
            'player': player,
            'day_scores': [None, None, None],
            'total_score': 0,
            'total_points': 0,
            'rounds_completed': 0
        }
        
        # Get scores for each day
        for day in range(1, 4):
            round_obj = Round.query.filter_by(tournament_id=tournament_id, day=day).first()
            if round_obj:
                score = Score.query.filter_by(player_id=player.id, round_id=round_obj.id).first()
                if score and score.total_strokes:
                    if round_obj.format == 'stableford':
                        player_data['day_scores'][day-1] = score.stableford_points
                        player_data['total_points'] += score.stableford_points
                    else:
                        player_data['day_scores'][day-1] = score.total_strokes
                        player_data['total_score'] += score.total_strokes
                    player_data['rounds_completed'] += 1
        
        leaderboard.append(player_data)
    
    # Sort leaderboard (stroke play: lower is better, stableford: higher is better)
    # For mixed formats, we'll use a combined scoring system
    leaderboard.sort(key=lambda x: (-x['total_points'], x['total_score'], -x['rounds_completed']))
    
    # Get dynamic prize distribution and assign rankings
    player_count = len(players)
    prize_distribution = get_prize_distribution(player_count)
    
    for i, player_data in enumerate(leaderboard):
        player_data['rank'] = i + 1
        player_data['prize'] = prize_distribution.get(i + 1, 0)
    
    return leaderboard