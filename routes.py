from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Tournament, Player, Round, Score, SpecialPrize, PINACLEPOINT_COURSE
from datetime import datetime, date
from sqlalchemy import func

def get_prize_distribution(player_count):
    """Calculate dynamic prize distribution ensuring no one gets the same amount"""
    total_main_prize = 955000  # R955,000 for main prizes (leaving R45,000 for special prizes)
    special_prizes_total = 45000  # R15,000 each for 3 special prizes
    
    if player_count <= 0:
        return {'main_prizes': {}, 'special_prizes': {'longest_drive': 15000, 'closest_hole': 15000, 'most_birdies': 15000}}
    
    prizes = {}
    
    if player_count == 1:
        prizes[1] = total_main_prize
    elif player_count == 2:
        prizes[1] = 573000  # 60%
        prizes[2] = 382000  # 40%
    elif player_count == 3:
        prizes[1] = 477500  # 50%
        prizes[2] = 286500  # 30%
        prizes[3] = 191000  # 20%
    elif player_count == 4:
        prizes[1] = 334250  # 35%
        prizes[2] = 238750  # 25%
        prizes[3] = 191000  # 20%
        prizes[4] = 191000  # 20%
    elif player_count == 5:
        prizes[1] = 286500  # 30%
        prizes[2] = 210375  # 22%
        prizes[3] = 172275  # 18%
        prizes[4] = 143775  # 15%
        prizes[5] = 142075  # 15%
    elif player_count == 6:
        prizes[1] = 267575  # 28%
        prizes[2] = 191000  # 20%
        prizes[3] = 143775  # 15%
        prizes[4] = 124925  # 13%
        prizes[5] = 114375  # 12%
        prizes[6] = 113350  # 12%
    elif player_count == 7:
        prizes[1] = 238750  # 25%
        prizes[2] = 171825  # 18%
        prizes[3] = 124925  # 13%
        prizes[4] = 105575  # 11%
        prizes[5] = 95500   # 10%
        prizes[6] = 91075   # 9.5%
        prizes[7] = 127350  # Rest
    elif player_count == 8:
        prizes[1] = 238750  # 25%
        prizes[2] = 171825  # 18%
        prizes[3] = 124925  # 13%
        prizes[4] = 95500   # 10%
        prizes[5] = 76400   # 8%
        prizes[6] = 66925   # 7%
        prizes[7] = 57450   # 6%
        prizes[8] = 123225  # Rest
    else:
        # For more than 8 players, create descending amounts
        base_amounts = [238750, 171825, 124925, 95500, 76400, 66925, 57450]
        total_used = sum(base_amounts)
        remaining = total_main_prize - total_used
        remaining_players = player_count - 7
        
        # Create descending amounts for remaining players
        for i, amount in enumerate(base_amounts, 1):
            prizes[i] = amount
        
        # Distribute remaining amount in descending order
        step = remaining // (remaining_players * 2)  # Create variation
        for i in range(8, player_count + 1):
            amount = max(20000, remaining - (i - 8) * step)
            prizes[i] = amount
            remaining -= amount
        
        # Adjust if needed
        if remaining > 0:
            prizes[1] += remaining
    
    # Ensure all amounts are different by adding small variations
    amounts_used = set()
    for pos in sorted(prizes.keys()):
        while prizes[pos] in amounts_used:
            prizes[pos] += 25  # Add R25 if duplicate
        amounts_used.add(prizes[pos])
    
    return {
        'main_prizes': prizes,
        'special_prizes': {
            'longest_drive': 15000,
            'closest_hole': 15000, 
            'most_birdies': 15000
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