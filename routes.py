from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Tournament, Player, Round, Score, SpecialPrize, PINACLEPOINT_COURSE
from datetime import datetime, date
from sqlalchemy import func

def get_prize_distribution(player_count):
    """Calculate dynamic prize distribution with strict descending order"""
    # Total R1,000,000 - R450,000 for daily special prizes (R50k x 3 prizes x 3 days)
    total_main_prize = 550000  # R550,000 for main tournament prizes
    daily_special_prizes = 450000  # R450,000 for daily special prizes (R150k per day)
    
    if player_count <= 0:
        return {
            'main_prizes': {}, 
            'daily_special_prizes': {
                'day_1': {'longest_drive': 50000, 'closest_hole': 50000, 'most_birdies': 50000},
                'day_2': {'longest_drive': 50000, 'closest_hole': 50000, 'most_birdies': 50000},
                'day_3': {'longest_drive': 50000, 'closest_hole': 50000, 'most_birdies': 50000}
            }
        }
    
    # Define percentage distribution that ensures descending order
    if player_count == 1:
        percentages = [100]
    elif player_count == 2:
        percentages = [60, 40]
    elif player_count == 3:
        percentages = [50, 30, 20]
    elif player_count == 4:
        percentages = [35, 25, 22, 18]
    elif player_count == 5:
        percentages = [30, 22, 18, 16, 14]
    elif player_count == 6:
        percentages = [28, 20, 16, 14, 12, 10]
    elif player_count == 7:
        percentages = [25, 18, 15, 13, 11, 10, 8]
    elif player_count == 8:
        percentages = [25, 18, 13, 11, 9, 8, 7, 9]
    else:
        # For more than 8 players: top positions get fixed percentages, rest descend
        percentages = [25, 18, 13, 10, 8, 7, 6, 5]  # Top 8 positions
        remaining_percentage = 8  # 8% for remaining players
        
        # Distribute remaining percentage in descending order
        remaining_players = player_count - 8
        if remaining_players > 0:
            base_percentage = remaining_percentage / remaining_players
            for i in range(remaining_players):
                # Each position gets slightly less than the previous
                reduction = i * 0.2  # 0.2% reduction per position
                percentages.append(max(1, int(base_percentage - reduction)))
    
    # Calculate actual prize amounts
    prizes = {}
    for i in range(player_count):
        position = i + 1
        percentage = percentages[i] if i < len(percentages) else 0.5
        amount = int(total_main_prize * percentage / 100)
        prizes[position] = amount
    
    # Force strict descending order - sort amounts and reassign
    sorted_amounts = sorted(prizes.values(), reverse=True)
    final_prizes = {}
    
    for i in range(player_count):
        position = i + 1
        final_prizes[position] = sorted_amounts[i]
    
    # Ensure no duplicates by reducing subsequent amounts slightly
    previous_amount = None
    for position in sorted(final_prizes.keys()):
        if previous_amount is not None and final_prizes[position] >= previous_amount:
            final_prizes[position] = previous_amount - 500  # R500 less than previous
        previous_amount = final_prizes[position]
        
        # Ensure minimum prize of R15,000
        final_prizes[position] = max(15000, final_prizes[position])
    
    return {
        'main_prizes': final_prizes,
        'daily_special_prizes': {
            'day_1': {'longest_drive': 50000, 'closest_hole': 50000, 'most_birdies': 50000},
            'day_2': {'longest_drive': 50000, 'closest_hole': 50000, 'most_birdies': 50000},
            'day_3': {'longest_drive': 50000, 'closest_hole': 50000, 'most_birdies': 50000}
        }
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

@app.route('/day/<int:day>')
def day_scorecard(day):
    """Show scorecard entry for a specific day"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    round_obj = Round.query.filter_by(tournament_id=tournament.id, day=day).first()
    if not round_obj:
        flash(f'Day {day} round not found. Please setup the tournament first.', 'error')
        return redirect(url_for('admin'))
    
    players = Player.query.filter_by(tournament_id=tournament.id).all()
    
    return render_template('admin.html',
                         tournament=tournament,
                         players=players,
                         rounds=[round_obj],
                         tournament_formats=TOURNAMENT_FORMATS,
                         selected_day=day)

@app.route('/special_prizes')
def special_prizes():
    """Manage special prizes (longest drive, closest to hole, most birdies)"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    players = Player.query.filter_by(tournament_id=tournament.id).all()
    
    # Get existing special prize winners
    special_prizes = {}
    for prize_type in ['longest_drive', 'closest_hole', 'most_birdies']:
        prize = SpecialPrize.query.filter_by(tournament_id=tournament.id, prize_type=prize_type).first()
        special_prizes[prize_type] = prize
    
    return render_template('special_prizes.html',
                         tournament=tournament,
                         players=players,
                         special_prizes=special_prizes)

@app.route('/award_special_prize', methods=['POST'])
def award_special_prize():
    """Award a special prize to a player"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    prize_type = request.form.get('prize_type')
    player_id = request.form.get('player_id')
    
    if not prize_type or not player_id:
        flash('Please select both prize type and player.', 'error')
        return redirect(url_for('special_prizes'))
    
    # Remove existing prize of this type
    existing_prize = SpecialPrize.query.filter_by(tournament_id=tournament.id, prize_type=prize_type).first()
    if existing_prize:
        db.session.delete(existing_prize)
    
    # Create new prize
    new_prize = SpecialPrize(
        tournament_id=tournament.id,
        prize_type=prize_type,
        player_id=int(player_id)
    )
    db.session.add(new_prize)
    db.session.commit()
    
    player = Player.query.get(player_id)
    flash(f'{prize_type.replace("_", " ").title()} prize awarded to {player.name}!', 'success')
    
    return redirect(url_for('special_prizes'))

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
        player_data['prize'] = prize_distribution['main_prizes'].get(i + 1, 0)
    
    return leaderboard