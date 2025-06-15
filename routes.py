from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Tournament, Player, Round, Score, SpecialPrize, HandicapPlayer, HandicapRound, PINACLEPOINT_COURSE
from datetime import datetime, date
from sqlalchemy import func

def get_golf_score_symbol(score, par):
    """Return HTML for traditional golf scoring symbols"""
    diff = score - par
    
    if diff <= -3:  # Albatross or better
        return f'<div class="scoring-symbol triangle" data-score="{score}"></div>'
    elif diff == -2:  # Eagle
        return f'<div class="scoring-symbol double-circle" data-score="{score}">{score}</div>'
    elif diff == -1:  # Birdie
        return f'<div class="scoring-symbol circle" data-score="{score}">{score}</div>'
    elif diff == 0:  # Par
        return f'<div class="scoring-symbol par" data-score="{score}">{score}</div>'
    elif diff == 1:  # Bogey
        return f'<div class="scoring-symbol square" data-score="{score}">{score}</div>'
    elif diff == 2:  # Double Bogey
        return f'<div class="scoring-symbol double-square" data-score="{score}">{score}</div>'
    else:  # Triple Bogey or worse
        return f'<div class="scoring-symbol triple-square" data-score="{score}">{score}</div>'

# Make the function available in templates
app.jinja_env.globals.update(get_golf_score_symbol=get_golf_score_symbol)

def get_prize_distribution(player_count):
    """Calculate dynamic prize distribution with strict descending order and round values"""
    # Total R1,150,000 - R150,000 for daily special prizes
    total_main_prize = 1000000  # R1,000,000 for main tournament prizes
    daily_special_prizes = 150000  # R150,000 for daily special prizes
    
    if player_count <= 0:
        return {
            'main_prizes': {}, 
            'daily_special_prizes': {
                'day_1': {'longest_drive': 50000, 'closest_hole': 50000, 'most_birdies': 50000},
                'day_2': {'longest_drive': 50000, 'closest_hole': 50000, 'most_birdies': 50000},
                'day_3': {'longest_drive': 50000, 'closest_hole': 50000, 'most_birdies': 50000}
            }
        }
    
    # Define round prize amounts based on player count - first place always R250,000
    if player_count == 1:
        prizes = {1: 1000000}  # Single player gets all main prize money
    elif player_count == 2:
        prizes = {1: 700000, 2: 300000}
    elif player_count == 3:
        prizes = {1: 500000, 2: 300000, 3: 200000}
    elif player_count == 4:
        prizes = {1: 400000, 2: 250000, 3: 200000, 4: 150000}
    elif player_count == 5:
        prizes = {1: 300000, 2: 225000, 3: 175000, 4: 150000, 5: 150000}
    elif player_count == 6:
        prizes = {1: 250000, 2: 175000, 3: 150000, 4: 125000, 5: 150000, 6: 150000}
    else:
        # For 7+ players: first place R250,000, then descending amounts
        prizes = {1: 250000, 2: 175000, 3: 125000, 4: 100000, 5: 75000, 6: 65000, 7: 55000, 8: 50000}
        
        if player_count > 8:
            # For more than 8 players: remaining money distributed to additional players
            used_prize_money = sum(prizes.values())
            remaining_prize_money = total_main_prize - used_prize_money
            remaining_players = player_count - 8
            
            if remaining_players > 0:
                # Start at 45000 and decrease by 2500 for each position
                current_amount = 45000
                for position in range(9, player_count + 1):
                    prizes[position] = max(20000, current_amount)  # Minimum R20,000
                    current_amount -= 2500
    
    def round_to_nearest_500(amount):
        """Round amounts to nearest R500 for cleaner values"""
        return round(amount / 500) * 500
    
    # Round all amounts to nearest R500
    for position in prizes:
        prizes[position] = round_to_nearest_500(prizes[position])
        # Ensure minimum of R15,000
        prizes[position] = max(15000, prizes[position])
    
    # Ensure strict descending order
    previous_amount = None
    for position in sorted(prizes.keys()):
        if previous_amount is not None and prizes[position] >= previous_amount:
            prizes[position] = previous_amount - 2500  # R2,500 less than previous
            prizes[position] = round_to_nearest_500(prizes[position])
        previous_amount = prizes[position]
        
        # Final check for minimum
        prizes[position] = max(15000, prizes[position])
    
    return {
        'main_prizes': prizes,
        'daily_special_prizes': {
            'day_1': {
                'most_pars_front': 10000, 
                'most_pars_back': 10000, 
                'beat_handicap': 10000,
                'most_birdies': 10000,
                'most_pars': 10000
            },
            'day_2': {
                'most_pars_front': 10000, 
                'most_pars_back': 10000, 
                'beat_handicap': 10000,
                'most_birdies': 10000,
                'most_pars': 10000
            },
            'day_3': {
                'most_pars_front': 10000, 
                'most_pars_back': 10000, 
                'beat_handicap': 10000,
                'most_birdies': 10000,
                'most_pars': 10000
            }
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
            name="Family Masters Invitational",
            start_date=date.today()
        )
        db.session.add(tournament)
        db.session.flush()  # Get tournament ID
        
        # Create players - handle dynamic player count
        player_names = []
        for i in range(1, 21):  # Check up to 20 players
            name = request.form.get(f'player_{i}')
            handicap = request.form.get(f'handicap_{i}', 18)
            if name and name.strip():
                try:
                    handicap_value = int(handicap) if handicap else 18
                    handicap_value = max(0, min(36, handicap_value))  # Ensure handicap is between 0-36
                except (ValueError, TypeError):
                    handicap_value = 18
                
                player = Player(
                    name=name.strip(), 
                    tournament_id=tournament.id,
                    handicap=handicap_value
                )
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
    
    return render_template('scoreboard.html',
                         tournament=tournament,
                         leaderboard=leaderboard,
                         rounds=rounds,
                         tournament_formats=TOURNAMENT_FORMATS)

@app.route('/prize_money')
def prize_money():
    """Prize money dashboard showing winnings and distribution"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    leaderboard = calculate_leaderboard(tournament.id)
    
    # Get dynamic prize distribution based on actual player count
    player_count = len(Player.query.filter_by(tournament_id=tournament.id).all())
    prize_distribution = get_prize_distribution(player_count)
    
    return render_template('prize_money.html',
                         tournament=tournament,
                         leaderboard=leaderboard,
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
    
    # Automatically recalculate and award daily special prizes for this round's day
    tournament_id = score.round.tournament_id
    day = score.round.day
    auto_award_daily_special_prizes(tournament_id, day)
    
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

@app.route('/add_player', methods=['POST'])
def add_player():
    """Add a new player to the existing tournament"""
    tournament = Tournament.query.first()
    if not tournament:
        flash('No tournament found. Please setup the tournament first.', 'error')
        return redirect(url_for('player_setup'))
    
    player_name = request.form.get('player_name')
    handicap = request.form.get('handicap', 18)
    
    if not player_name or not player_name.strip():
        flash('Player name is required.', 'error')
        return redirect(url_for('admin'))
    
    # Check if player name already exists
    existing_player = Player.query.filter_by(
        tournament_id=tournament.id, 
        name=player_name.strip()
    ).first()
    
    if existing_player:
        flash(f'Player "{player_name}" already exists in this tournament.', 'error')
        return redirect(url_for('admin'))
    
    # Check maximum player limit
    current_player_count = Player.query.filter_by(tournament_id=tournament.id).count()
    if current_player_count >= 20:
        flash('Maximum 20 players allowed per tournament.', 'error')
        return redirect(url_for('admin'))
    
    try:
        # Create new player
        new_player = Player(
            name=player_name.strip(),
            tournament_id=tournament.id,
            handicap=int(handicap)
        )
        db.session.add(new_player)
        
        # Create empty score records for existing rounds
        rounds = Round.query.filter_by(tournament_id=tournament.id).all()
        for round_obj in rounds:
            score = Score(player_id=new_player.id, round_id=round_obj.id)
            db.session.add(score)
        
        db.session.commit()
        flash(f'Player "{player_name}" has been added to the tournament successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding player. Please try again.', 'error')
    
    return redirect(url_for('admin'))

@app.route('/remove_player', methods=['POST'])
def remove_player():
    """Remove a player from the tournament"""
    tournament = Tournament.query.first()
    if not tournament:
        flash('No tournament found.', 'error')
        return redirect(url_for('admin'))
    
    player_id = request.form.get('player_id')
    if not player_id:
        flash('Please select a player to remove.', 'error')
        return redirect(url_for('admin'))
    
    try:
        player = Player.query.get_or_404(player_id)
        player_name = player.name
        
        # Delete all scores for this player
        Score.query.filter_by(player_id=player_id).delete()
        
        # Delete any special prizes for this player
        SpecialPrize.query.filter_by(player_id=player_id).delete()
        
        # Delete the player
        db.session.delete(player)
        db.session.commit()
        
        flash(f'Player "{player_name}" has been removed from the tournament.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error removing player. Please try again.', 'error')
    
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

@app.route('/day_board/<int:day>')
def day_scorecard_board(day):
    """Professional tournament scorecard board for a specific day"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    if day not in [1, 2, 3]:
        flash('Invalid day. Please select day 1, 2, or 3.', 'error')
        return redirect(url_for('scoreboard'))
    
    # Get the round for this day
    round_obj = Round.query.filter_by(tournament_id=tournament.id, day=day).first()
    if not round_obj:
        flash(f'Day {day} round not found.', 'error')
        return redirect(url_for('scoreboard'))
    
    # Get leaderboard data
    leaderboard = calculate_leaderboard(tournament.id)
    
    # Get scores for this specific day, organized by player
    scores_by_player = {}
    scores = Score.query.filter_by(round_id=round_obj.id).all()
    for score in scores:
        scores_by_player[score.player_id] = score
    
    return render_template('day_scorecard_board.html',
                         tournament=tournament,
                         day=day,
                         round=round_obj,
                         leaderboard=leaderboard,
                         scores_by_player=scores_by_player,
                         course=PINACLEPOINT_COURSE,
                         tournament_formats=TOURNAMENT_FORMATS)

@app.route('/special_prizes')
def special_prizes():
    """View automatically calculated daily special prizes"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    # Get existing special prize winners organized by day (automatically calculated)
    daily_special_prizes = {}
    for day in [1, 2, 3]:
        daily_special_prizes[day] = {}
        for prize_type in ['most_pars_front', 'most_pars_back', 'beat_handicap', 'most_birdies', 'most_pars']:
            prize = SpecialPrize.query.filter_by(
                tournament_id=tournament.id, 
                day=day, 
                prize_type=prize_type
            ).first()
            daily_special_prizes[day][prize_type] = prize
    
    return render_template('daily_special_prizes_view.html',
                         tournament=tournament,
                         daily_special_prizes=daily_special_prizes,
                         tournament_formats=TOURNAMENT_FORMATS)

@app.route('/toggle_prize_eligibility', methods=['POST'])
def toggle_prize_eligibility():
    """Toggle a player's prize money eligibility"""
    tournament = Tournament.query.first()
    if not tournament:
        flash('No tournament found.', 'error')
        return redirect(url_for('admin'))
    
    player_id = request.form.get('player_id')
    action = request.form.get('action')
    
    if not player_id:
        flash('Please select a player.', 'error')
        return redirect(url_for('admin'))
    
    try:
        player = Player.query.get_or_404(player_id)
        
        if action == 'exclude':
            player.prize_eligible = False
            flash(f'{player.name} is now excluded from prize money but will still appear in rankings.', 'warning')
        elif action == 'include':
            player.prize_eligible = True
            flash(f'{player.name} is now eligible for prize money.', 'success')
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('Error updating player eligibility. Please try again.', 'error')
    
    return redirect(url_for('admin'))

def auto_award_daily_special_prizes(tournament_id, day):
    """Automatically calculate and award daily special prizes for a specific day"""
    # Calculate winners based on current scores
    winners = calculate_daily_special_prizes(tournament_id, day)
    
    # Clear existing special prizes for this day
    SpecialPrize.query.filter_by(tournament_id=tournament_id, day=day).delete()
    
    # Award new special prizes with split amounts for ties
    for prize_type, player_ids in winners.items():
        if player_ids:  # Only award if there are actual winners
            # Split the R10,000 prize equally among all winners
            total_prize = 10000
            split_amount = total_prize // len(player_ids)  # Integer division to avoid cents
            
            for player_id in player_ids:
                special_prize = SpecialPrize(
                    tournament_id=tournament_id,
                    day=day,
                    prize_type=prize_type,
                    player_id=player_id,
                    amount=split_amount
                )
                db.session.add(special_prize)
    
    db.session.commit()

def calculate_daily_special_prizes(tournament_id, day):
    """Calculate who wins daily special prizes automatically based on performance - only eligible players"""
    from collections import defaultdict
    
    # Get the round for this day
    round_obj = Round.query.filter_by(tournament_id=tournament_id, day=day).first()
    if not round_obj:
        return {}
    
    # Get all scores for this day, but only for prize-eligible players
    scores = Score.query.filter_by(round_id=round_obj.id).join(Player).filter(Player.prize_eligible == True).all()
    scores_with_data = [s for s in scores if s.total_strokes and s.total_strokes > 0]
    
    if not scores_with_data:
        return {}
    
    winners = {}
    
    # 1. Most Pars Front 9 (holes 1-9) - count actual pars based on course data
    front_nine_pars = defaultdict(int)
    for score in scores_with_data:
        par_count = 0
        for hole in range(1, 10):  # holes 1-9
            hole_score = score.get_hole_score(hole)
            if hole_score and hole < len(PINACLEPOINT_COURSE['holes']):
                hole_par = PINACLEPOINT_COURSE['holes'][hole-1]['par']
                if hole_score == hole_par:
                    par_count += 1
        front_nine_pars[score.player_id] = par_count
    
    if front_nine_pars and max(front_nine_pars.values()) > 0:
        max_front_pars = max(front_nine_pars.values())
        winners['most_pars_front'] = [pid for pid, count in front_nine_pars.items() if count == max_front_pars]
    else:
        winners['most_pars_front'] = []
    
    # 2. Most Pars Back 9 (holes 10-18) - count actual pars based on course data
    back_nine_pars = defaultdict(int)
    for score in scores_with_data:
        par_count = 0
        for hole in range(10, 19):  # holes 10-18
            hole_score = score.get_hole_score(hole)
            if hole_score and hole-1 < len(PINACLEPOINT_COURSE['holes']):
                hole_par = PINACLEPOINT_COURSE['holes'][hole-1]['par']
                if hole_score == hole_par:
                    par_count += 1
        back_nine_pars[score.player_id] = par_count
    
    if back_nine_pars and max(back_nine_pars.values()) > 0:
        max_back_pars = max(back_nine_pars.values())
        winners['most_pars_back'] = [pid for pid, count in back_nine_pars.items() if count == max_back_pars]
    else:
        winners['most_pars_back'] = []
    
    # 3. Beat Handicap - player who performed best relative to their handicap
    handicap_performance = []
    for score in scores_with_data:
        player = score.player
        if score.total_strokes and player.handicap is not None:
            net_score = score.get_net_score()  # handicap-adjusted score
            if net_score is not None:
                expected_score = 72  # course par without handicap adjustment
                performance = expected_score - net_score  # positive means beat expected net score
                handicap_performance.append((score.player_id, performance))
    
    if handicap_performance and len(handicap_performance) > 0:
        best_performance = max(handicap_performance, key=lambda x: x[1])[1]
        # Only award if someone actually beat their expected score
        if best_performance > 0:
            winners['beat_handicap'] = [pid for pid, perf in handicap_performance if perf == best_performance]
        else:
            winners['beat_handicap'] = []
    else:
        winners['beat_handicap'] = []
    
    # 4. Most Birdies - count birdies (scores under par) based on actual hole pars
    birdie_count = defaultdict(int)
    for score in scores_with_data:
        birdies = 0
        for hole in range(1, 19):  # holes 1-18
            hole_score = score.get_hole_score(hole)
            if hole_score and hole-1 < len(PINACLEPOINT_COURSE['holes']):
                hole_par = PINACLEPOINT_COURSE['holes'][hole-1]['par']
                if hole_score < hole_par:  # birdie or better
                    birdies += 1
        birdie_count[score.player_id] = birdies
    
    if birdie_count and max(birdie_count.values()) > 0:
        max_birdies = max(birdie_count.values())
        winners['most_birdies'] = [pid for pid, count in birdie_count.items() if count == max_birdies]
    else:
        winners['most_birdies'] = []
    
    # 5. Most Pars Overall - player with most pars across all 18 holes using actual course pars
    total_pars = defaultdict(int)
    for score in scores_with_data:
        par_count = 0
        for hole in range(1, 19):  # holes 1-18
            hole_score = score.get_hole_score(hole)
            if hole_score and hole-1 < len(PINACLEPOINT_COURSE['holes']):
                hole_par = PINACLEPOINT_COURSE['holes'][hole-1]['par']
                if hole_score == hole_par:
                    par_count += 1
        total_pars[score.player_id] = par_count
    
    if total_pars and max(total_pars.values()) > 0:
        max_total_pars = max(total_pars.values())
        winners['most_pars'] = [pid for pid, count in total_pars.items() if count == max_total_pars]
    else:
        winners['most_pars'] = []
    
    return winners

def calculate_leaderboard(tournament_id):
    """Calculate tournament leaderboard with cumulative scores and net scoring"""
    players = Player.query.filter_by(tournament_id=tournament_id).all()
    leaderboard = []
    
    # Get players who don't qualify for prize money but still show in rankings
    non_prize_eligible_players = [p.name for p in players if not p.prize_eligible]
    
    for player in players:
        player_data = {
            'player': player,
            'day_scores': [None, None, None],
            'total_score': 0,
            'total_points': 0,
            'rounds_completed': 0,
            'special_prizes_won': 0,
            'net_score': None,
            'par_score': None
        }
        
        # Get scores for each day and accumulate net scores
        total_net_score = 0
        has_any_scores = False
        days_with_scores = 0
        
        for day in range(1, 4):
            round_obj = Round.query.filter_by(tournament_id=tournament_id, day=day).first()
            if round_obj:
                score = Score.query.filter_by(player_id=player.id, round_id=round_obj.id).first()
                if score and score.total_strokes:
                    has_any_scores = True
                    days_with_scores += 1
                    if round_obj.format == 'stableford':
                        player_data['day_scores'][day-1] = score.stableford_points
                        player_data['total_points'] += score.stableford_points
                    else:
                        player_data['day_scores'][day-1] = score.total_strokes
                        player_data['total_score'] += score.total_strokes
                    
                    # Add net score for this round
                    net_score = score.get_net_score()
                    if net_score is not None:
                        total_net_score += net_score
                    
                    player_data['rounds_completed'] += 1
        
        # Set the net score and par score if player has any scores
        if has_any_scores and total_net_score > 0:
            player_data['net_score'] = total_net_score
            # Calculate par score based on actual days with scores (72 par per day)
            total_par = 72 * days_with_scores
            par_difference = total_net_score - total_par
            if par_difference == 0:
                player_data['par_score'] = "E"  # Even par
            elif par_difference > 0:
                player_data['par_score'] = f"+{par_difference}"  # Over par
            else:
                player_data['par_score'] = str(par_difference)  # Under par (negative sign included)
        else:
            player_data['net_score'] = None
            player_data['par_score'] = None
        
        # Calculate special prizes won by this player
        special_prizes_total = 0
        special_prizes_detail = []
        
        # Get automatic special prizes from database (not calculated on-the-fly to avoid duplicates)
        auto_special_prizes = SpecialPrize.query.filter_by(
            tournament_id=tournament_id, 
            player_id=player.id
        ).all()
        
        for prize in auto_special_prizes:
            special_prizes_total += prize.amount  # Use actual amount from database
            special_prizes_detail.append(f"Day {prize.day} {prize.prize_type.replace('_', ' ').title()}")
        
        player_data['special_prizes_won'] = special_prizes_total
        player_data['special_prizes_detail'] = special_prizes_detail
        
        leaderboard.append(player_data)
    
    # Sort leaderboard by net score (lower is better), then by stableford points (higher is better)
    # Players with no scores go to the bottom
    def sort_key(x):
        if x['net_score'] is not None:
            return (0, x['net_score'], -x['total_points'])  # 0 = has score, sort by net score ascending, then points descending
        else:
            return (1, 999, -x['total_points'])  # 1 = no score, goes to bottom
    
    leaderboard.sort(key=sort_key)
    
    # Get dynamic prize distribution and assign rankings with tie handling
    # Count only prize-eligible players for prize distribution
    prize_eligible_players = [p for p in leaderboard if p['player'].prize_eligible]
    player_count = len(prize_eligible_players)
    prize_distribution = get_prize_distribution(player_count)
    
    # Debug: Print prize distribution
    print(f"Prize eligible players: {player_count}")
    print(f"Prize distribution: {prize_distribution['main_prizes']}")
    
    # Handle ties and calculate split prize money
    current_rank = 1
    current_prize_rank = 1  # Separate counter for prize distribution
    i = 0
    
    while i < len(leaderboard):
        # Find all players with the same net score (tied players)
        tied_players = [leaderboard[i]]
        current_score = leaderboard[i]['net_score']
        
        # Look for tied players - only check net score, and handle None values properly
        if current_score is not None:
            j = i + 1
            while (j < len(leaderboard) and 
                   leaderboard[j]['net_score'] is not None and
                   leaderboard[j]['net_score'] == current_score):
                tied_players.append(leaderboard[j])
                j += 1
        else:
            # If current player has no score, don't look for ties
            j = i + 1
        
        # Separate prize-eligible and non-eligible players in this tie group
        prize_eligible_tied = [p for p in tied_players if p['player'].prize_eligible]
        non_eligible_tied = [p for p in tied_players if not p['player'].prize_eligible]
        
        # Calculate prize money for tied positions (only for eligible players)
        if len(prize_eligible_tied) > 1 and current_score is not None:
            # Calculate total prize money for tied positions
            total_tied_prize = 0
            positions_involved = []
            for pos in range(current_prize_rank, current_prize_rank + len(prize_eligible_tied)):
                if pos in prize_distribution['main_prizes']:
                    total_tied_prize += prize_distribution['main_prizes'][pos]
                    positions_involved.append(pos)
            
            # Split the prize equally among tied eligible players
            if total_tied_prize > 0:
                split_prize = total_tied_prize // len(prize_eligible_tied)
            else:
                split_prize = 0
            
            # Assign same rank and split prize to all tied eligible players
            for player_data in prize_eligible_tied:
                player_data['rank'] = current_rank
                player_data['prize'] = split_prize
                player_data['total_winnings'] = player_data['prize'] + player_data['special_prizes_won']
                player_data['is_tied'] = len(tied_players) > 1
                player_data['tied_positions'] = positions_involved
                player_data['prize_position'] = current_prize_rank
        elif len(prize_eligible_tied) == 1 and current_score is not None:
            # Single eligible player at this position
            player_data = prize_eligible_tied[0]
            player_data['rank'] = current_rank
            player_data['prize'] = prize_distribution['main_prizes'].get(current_prize_rank, 0)
            player_data['total_winnings'] = player_data['prize'] + player_data['special_prizes_won']
            player_data['is_tied'] = len(tied_players) > 1
            player_data['prize_position'] = current_prize_rank
        elif len(prize_eligible_tied) >= 1:
            # Eligible players with no score
            for player_data in prize_eligible_tied:
                player_data['rank'] = current_rank
                player_data['prize'] = 0
                player_data['total_winnings'] = player_data['prize'] + player_data['special_prizes_won']
                player_data['is_tied'] = len(tied_players) > 1 if len(tied_players) > 1 else False
                player_data['prize_position'] = None
        
        # Handle non-eligible players (show rank but no prize money)
        for player_data in non_eligible_tied:
            player_data['rank'] = current_rank
            player_data['prize'] = 0  # No prize money for non-eligible players
            player_data['total_winnings'] = player_data['special_prizes_won']  # Only special prizes if any
            player_data['is_tied'] = len(tied_players) > 1
            player_data['is_non_eligible'] = True  # Flag for display purposes
            player_data['prize_position'] = None
        
        # Move to next unprocessed position
        current_rank += len(tied_players)
        # Only advance prize rank counter for eligible players with scores
        if prize_eligible_tied and current_score is not None:
            current_prize_rank += len(prize_eligible_tied)
        i = j
    
    return leaderboard

@app.route('/handicap_dashboard')
def handicap_dashboard():
    """Handicap calculation dashboard"""
    handicap_players = HandicapPlayer.query.all()
    
    # Calculate data for each player
    players_data = []
    for player in handicap_players:
        rounds = HandicapRound.query.filter_by(player_id=player.id).order_by(HandicapRound.round_number).all()
        
        # Calculate handicap if enough rounds
        calculated_handicap = calculate_handicap_for_player(player.id)
        
        # Prepare round data
        rounds_data = []
        for round_obj in rounds:
            rounds_data.append({
                'round_number': round_obj.round_number,
                'score': round_obj.total_score,
                'differential': round_obj.differential
            })
        
        players_data.append({
            'player': player,
            'rounds': rounds_data,
            'rounds_count': len(rounds),
            'calculated_handicap': calculated_handicap
        })
    
    return render_template('handicap_dashboard.html', handicap_players=players_data)

@app.route('/add_handicap_player', methods=['POST'])
def add_handicap_player():
    """Add a new player for handicap calculation"""
    player_name = request.form.get('player_name')
    
    if not player_name or not player_name.strip():
        flash('Player name is required.', 'error')
        return redirect(url_for('handicap_dashboard'))
    
    # Check if player already exists
    existing_player = HandicapPlayer.query.filter_by(name=player_name.strip()).first()
    if existing_player:
        flash(f'Player "{player_name}" already exists.', 'error')
        return redirect(url_for('handicap_dashboard'))
    
    try:
        new_player = HandicapPlayer(name=player_name.strip())
        db.session.add(new_player)
        db.session.commit()
        flash(f'Player "{player_name}" added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding player. Please try again.', 'error')
    
    return redirect(url_for('handicap_dashboard'))

@app.route('/handicap_scorecard/<int:player_id>')
def handicap_scorecard(player_id):
    """Enter scores for handicap calculation round"""
    player = HandicapPlayer.query.get_or_404(player_id)
    
    # Check if player already has 4 rounds
    existing_rounds = HandicapRound.query.filter_by(player_id=player_id).count()
    if existing_rounds >= 4:
        flash('Player already has 4 rounds completed.', 'warning')
        return redirect(url_for('handicap_dashboard'))
    
    next_round_number = existing_rounds + 1
    
    return render_template('handicap_scorecard.html',
                         player=player,
                         next_round_number=next_round_number,
                         course=PINACLEPOINT_COURSE)

@app.route('/save_handicap_round', methods=['POST'])
def save_handicap_round():
    """Save handicap calculation round scores"""
    player_id = request.form.get('player_id')
    round_number = request.form.get('round_number')
    
    player = HandicapPlayer.query.get_or_404(player_id)
    
    # Check if this round already exists
    existing_round = HandicapRound.query.filter_by(
        player_id=player_id, 
        round_number=round_number
    ).first()
    
    if existing_round:
        flash('This round already exists for this player.', 'error')
        return redirect(url_for('handicap_dashboard'))
    
    try:
        # Create new handicap round
        handicap_round = HandicapRound(
            player_id=player_id,
            round_number=int(round_number)
        )
        
        # Save hole scores
        for hole in range(1, 19):
            hole_score = request.form.get(f'hole_{hole}')
            if hole_score and hole_score.isdigit():
                handicap_round.set_hole_score(hole, int(hole_score))
        
        # Calculate differential
        handicap_round.calculate_differential()
        
        db.session.add(handicap_round)
        db.session.commit()
        
        # Recalculate player's handicap
        new_handicap = calculate_handicap_for_player(player_id)
        if new_handicap is not None:
            player.calculated_handicap = new_handicap
            db.session.commit()
        
        flash(f'Round {round_number} saved successfully for {player.name}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error saving round. Please try again.', 'error')
    
    return redirect(url_for('handicap_dashboard'))

@app.route('/apply_handicap', methods=['POST'])
def apply_handicap():
    """Apply calculated handicap to tournament player"""
    player_id = request.form.get('player_id')
    handicap = request.form.get('handicap')
    
    handicap_player = HandicapPlayer.query.get_or_404(player_id)
    tournament = Tournament.query.first()
    
    if not tournament:
        flash('No tournament found. Please set up the tournament first.', 'error')
        return redirect(url_for('handicap_dashboard'))
    
    try:
        # Check if player already exists in tournament
        existing_tournament_player = Player.query.filter_by(
            tournament_id=tournament.id,
            name=handicap_player.name
        ).first()
        
        if existing_tournament_player:
            # Update existing player's handicap
            existing_tournament_player.handicap = int(handicap)
            flash(f'Updated {handicap_player.name}\'s handicap to {handicap} in tournament.', 'success')
        else:
            # Add new player to tournament with calculated handicap
            new_tournament_player = Player(
                name=handicap_player.name,
                tournament_id=tournament.id,
                handicap=int(handicap)
            )
            db.session.add(new_tournament_player)
            
            # Create empty score records for existing rounds
            rounds = Round.query.filter_by(tournament_id=tournament.id).all()
            for round_obj in rounds:
                score = Score(player_id=new_tournament_player.id, round_id=round_obj.id)
                db.session.add(score)
            
            flash(f'Added {handicap_player.name} to tournament with handicap {handicap}.', 'success')
        
        # Mark as applied
        handicap_player.is_applied_to_tournament = True
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash('Error applying handicap to tournament. Please try again.', 'error')
    
    return redirect(url_for('handicap_dashboard'))

def calculate_handicap_for_player(player_id):
    """Calculate handicap based on best rounds"""
    rounds = HandicapRound.query.filter_by(player_id=player_id).all()
    
    if len(rounds) < 3:
        return None  # Need at least 3 rounds
    
    # Calculate differentials for all rounds
    differentials = []
    for round_obj in rounds:
        if round_obj.differential is not None:
            differentials.append(round_obj.differential)
    
    if len(differentials) < 3:
        return None
    
    # Sort differentials and take best ones
    differentials.sort()
    
    if len(differentials) >= 4:
        # Use best 3 out of 4+ rounds
        best_differentials = differentials[:3]
    else:
        # Use all available (minimum 3)
        best_differentials = differentials
    
    # Calculate handicap: average of best differentials × 0.96
    average_differential = sum(best_differentials) / len(best_differentials)
    handicap = round(average_differential * 0.96)
    
    # Cap handicap at reasonable limits (0-36)
    return max(0, min(36, handicap))