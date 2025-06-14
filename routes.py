from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Tournament, Player, Round, Score, PINACLEPOINT_COURSE
from datetime import datetime, date
from sqlalchemy import func

def get_prize_distribution(player_count):
    """Calculate dynamic prize distribution based on player count"""
    total_available = 950000  # Reserve 50K for special prizes (950K + 50K = 1M total)
    
    if player_count <= 4:
        # For 4 or fewer players
        return {
            1: int(total_available * 0.50),  # 50%
            2: int(total_available * 0.30),  # 30%
            3: int(total_available * 0.15),  # 15%
            4: int(total_available * 0.05),  # 5%
        }
    elif player_count <= 8:
        # Original 8-player distribution
        return {
            1: 300000, 2: 200000, 3: 150000, 4: 100000,
            5: 75000, 6: 50000, 7: 40000, 8: 25000,
        }
    else:
        # For more than 8 players, distribute more evenly
        prizes = {}
        # Top 3 get larger portions
        prizes[1] = int(total_available * 0.30)  # 30%
        prizes[2] = int(total_available * 0.20)  # 20%
        prizes[3] = int(total_available * 0.15)  # 15%
        
        # Remaining 35% distributed among other players
        remaining = total_available - sum(prizes.values())
        remaining_players = player_count - 3
        
        if remaining_players > 0:
            # Use diminishing returns for positions 4+
            for pos in range(4, player_count + 1):
                if pos <= player_count // 2:  # Top half gets prizes
                    share = remaining / (remaining_players * 1.5) * (remaining_players - (pos - 4)) / remaining_players
                    prizes[pos] = max(int(share), 5000)  # Minimum R5,000
        
        return prizes

# Special skill prizes
SPECIAL_PRIZES = {
    'longest_drive': 15000,     # Longest drive
    'closest_hole': 15000,      # Closest to the hole
    'most_birdies': 20000,      # Most birdies by player
}

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
            start_date=date.today(),
            total_prize_pool=1000000
        )
        db.session.add(tournament)
        db.session.flush()  # Get tournament ID

        # Create players - dynamic count
        player_names = []
        i = 1
        while True:
            name = request.form.get(f'player_{i}')
            if not name:
                break
            
            handicap = request.form.get(f'handicap_{i}', 18)
            if name.strip():
                try:
                    handicap_value = int(handicap) if handicap else 18
                    handicap_value = max(0, min(36, handicap_value))  # Ensure handicap is between 0-36
                except (ValueError, TypeError):
                    handicap_value = 18

                player = Player(name=name.strip(), tournament_id=tournament.id, handicap=handicap_value)
                db.session.add(player)
                player_names.append(name.strip())
            i += 1

        if len(player_names) < 4:
            flash('Please enter at least 4 player names', 'error')
            return render_template('player_setup.html')
        
        if len(player_names) > 20:
            flash('Maximum 20 players allowed', 'error')
            return render_template('player_setup.html')

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

    return render_template('player_setup.html')

@app.route('/scoreboard')
def scoreboard():
    """TV-optimized scoreboard display"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))

    leaderboard = calculate_leaderboard(tournament.id)
    rounds = Round.query.filter_by(tournament_id=tournament.id).order_by(Round.day).all()

    prize_distribution = get_prize_distribution(len(leaderboard)) if leaderboard else {}
    return render_template('scoreboard.html',
                         tournament=tournament,
                         leaderboard=leaderboard,
                         rounds=rounds,
                         prize_distribution=prize_distribution,
                         special_prizes=SPECIAL_PRIZES,
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

def calculate_leaderboard(tournament_id):
    """Calculate tournament leaderboard with cumulative scores including handicap"""
    players = Player.query.filter_by(tournament_id=tournament_id).all()
    leaderboard = []

    for player in players:
        player_data = {
            'player': player,
            'day_scores': [None, None, None],
            'day_net_scores': [None, None, None],
            'total_score': 0,
            'total_net_score': 0,
            'total_points': 0,
            'rounds_completed': 0
        }

        # Get scores for each day
        for day in range(1, 4):
            round_obj = Round.query.filter_by(tournament_id=tournament_id, day=day).first()
            if round_obj:
                score = Score.query.filter_by(player_id=player.id, round_id=round_obj.id).first()
                if score and score.total_strokes:
                    gross_score = score.total_strokes
                    net_score = score.get_net_score()

                    if round_obj.format == 'stableford':
                        player_data['day_scores'][day-1] = score.stableford_points
                        player_data['total_points'] += score.stableford_points
                    else:
                        player_data['day_scores'][day-1] = gross_score
                        player_data['day_net_scores'][day-1] = net_score
                        player_data['total_score'] += gross_score
                        if net_score:
                            player_data['total_net_score'] += net_score
                    player_data['rounds_completed'] += 1

        leaderboard.append(player_data)

    # Sort leaderboard by net scores for stroke play, points for stableford
    leaderboard.sort(key=lambda x: (-x['total_points'], x['total_net_score'], x['total_score'], -x['rounds_completed']))

    # Assign rankings and prize money
    prize_distribution = get_prize_distribution(len(leaderboard))
    for i, player_data in enumerate(leaderboard):
        player_data['rank'] = i + 1
        player_data['prize'] = prize_distribution.get(i + 1, 0)

    return leaderboard

@app.route('/clear_scorecard/<int:score_id>', methods=['POST'])
def clear_scorecard(score_id):
    """Clear an individual player's scorecard"""
    try:
        score = Score.query.get_or_404(score_id)

        # Clear all hole scores
        for hole in range(1, 19):
            score.set_hole_score(hole, None)

        # Reset totals
        score.total_strokes = None
        score.stableford_points = None
        score.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Scorecard cleared successfully!', 'success')

        return redirect(url_for('scorecard', player_id=score.player_id, round_id=score.round_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing scorecard: {str(e)}', 'error')
        return redirect(url_for('admin'))