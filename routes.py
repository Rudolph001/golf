from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Tournament, Player, Round, Score, SpecialPrize, PINACLEPOINT_COURSE
from datetime import datetime, date
from sqlalchemy import func

def get_prize_distribution(player_count):
    """Calculate dynamic prize distribution with strict descending order and round values"""
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
    
    # Define round prize amounts based on player count
    if player_count == 1:
        prizes = {1: 550000}
    elif player_count == 2:
        prizes = {1: 350000, 2: 200000}
    elif player_count == 3:
        prizes = {1: 250000, 2: 175000, 3: 125000}
    elif player_count == 4:
        prizes = {1: 200000, 2: 150000, 3: 125000, 4: 75000}
    elif player_count == 5:
        prizes = {1: 175000, 2: 135000, 3: 100000, 4: 75000, 5: 65000}
    elif player_count == 6:
        prizes = {1: 150000, 2: 120000, 3: 90000, 4: 75000, 5: 65000, 6: 50000}
    elif player_count == 7:
        prizes = {1: 140000, 2: 110000, 3: 85000, 4: 70000, 5: 60000, 6: 50000, 7: 35000}
    elif player_count == 8:
        prizes = {1: 140000, 2: 100000, 3: 75000, 4: 65000, 5: 50000, 6: 45000, 7: 40000, 8: 35000}
    else:
        # For more than 8 players: predefined amounts for top 8, then descending amounts
        base_prizes = {1: 140000, 2: 100000, 3: 75000, 4: 65000, 5: 50000, 6: 45000, 7: 40000, 8: 35000}
        prizes = base_prizes.copy()
        
        # Calculate remaining prize money
        used_prize_money = sum(base_prizes.values())
        remaining_prize_money = total_main_prize - used_prize_money
        remaining_players = player_count - 8
        
        if remaining_players > 0:
            # Start at 30000 and decrease by 2500 for each position
            current_amount = 30000
            for position in range(9, player_count + 1):
                prizes[position] = max(15000, current_amount)  # Minimum R15,000
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
                'longest_drive': 30000, 
                'closest_hole': 30000, 
                'most_birdies': 30000,
                'straightest_drive': 30000,
                'most_pars': 30000
            },
            'day_2': {
                'longest_drive': 30000, 
                'closest_hole': 30000, 
                'most_birdies': 30000,
                'straightest_drive': 30000,
                'most_pars': 30000
            },
            'day_3': {
                'longest_drive': 30000, 
                'closest_hole': 30000, 
                'most_birdies': 30000,
                'straightest_drive': 30000,
                'most_pars': 30000
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
            name="The Pinical Point Family Golf Champions Cup",
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

@app.route('/special_prizes')
def special_prizes():
    """Manage daily special prizes (longest drive, closest to hole, most birdies)"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    players = Player.query.filter_by(tournament_id=tournament.id).all()
    rounds = Round.query.filter_by(tournament_id=tournament.id).order_by(Round.day).all()
    
    # Get existing special prize winners organized by day
    daily_special_prizes = {}
    for day in [1, 2, 3]:
        daily_special_prizes[day] = {}
        for prize_type in ['longest_drive', 'closest_hole', 'most_birdies', 'straightest_drive', 'most_pars']:
            prize = SpecialPrize.query.filter_by(
                tournament_id=tournament.id, 
                day=day, 
                prize_type=prize_type
            ).first()
            daily_special_prizes[day][prize_type] = prize
    
    return render_template('daily_special_prizes.html',
                         tournament=tournament,
                         players=players,
                         rounds=rounds,
                         daily_special_prizes=daily_special_prizes,
                         tournament_formats=TOURNAMENT_FORMATS)

@app.route('/award_special_prize', methods=['POST'])
def award_special_prize():
    """Award a daily special prize to a player"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    day = request.form.get('day')
    prize_type = request.form.get('prize_type')
    player_id = request.form.get('player_id')
    
    if not day or not prize_type or not player_id:
        flash('Please select day, prize type and player.', 'error')
        return redirect(url_for('special_prizes'))
    
    # Remove existing prize of this type for this day
    existing_prize = SpecialPrize.query.filter_by(
        tournament_id=tournament.id, 
        day=int(day), 
        prize_type=prize_type
    ).first()
    if existing_prize:
        db.session.delete(existing_prize)
    
    # Create new prize
    new_prize = SpecialPrize(
        tournament_id=tournament.id,
        day=int(day),
        prize_type=prize_type,
        player_id=int(player_id)
    )
    db.session.add(new_prize)
    db.session.commit()
    
    player = Player.query.get(player_id)
    day_name = TOURNAMENT_FORMATS[int(day)]['name']
    flash(f'Day {day} ({day_name}) {prize_type.replace("_", " ").title()} prize awarded to {player.name}!', 'success')
    
    return redirect(url_for('special_prizes'))

@app.route('/clear_special_prizes', methods=['POST'])
def clear_special_prizes():
    """Clear all special prizes for a specific day or all days"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    day = request.form.get('day')
    
    if day == 'all':
        # Clear all special prizes
        SpecialPrize.query.filter_by(tournament_id=tournament.id).delete()
        flash('All daily special prizes have been cleared!', 'success')
    else:
        # Clear prizes for specific day
        SpecialPrize.query.filter_by(tournament_id=tournament.id, day=int(day)).delete()
        day_name = TOURNAMENT_FORMATS[int(day)]['name']
        flash(f'Day {day} ({day_name}) special prizes have been cleared!', 'success')
    
    db.session.commit()
    return redirect(url_for('special_prizes'))

def calculate_leaderboard(tournament_id):
    """Calculate tournament leaderboard with cumulative scores and net scoring"""
    players = Player.query.filter_by(tournament_id=tournament_id).all()
    leaderboard = []
    
    for player in players:
        player_data = {
            'player': player,
            'day_scores': [None, None, None],
            'total_score': 0,
            'total_points': 0,
            'rounds_completed': 0,
            'special_prizes_won': 0,
            'net_score': None
        }
        
        # Get scores for each day and accumulate net scores
        total_net_score = 0
        has_any_scores = False
        
        for day in range(1, 4):
            round_obj = Round.query.filter_by(tournament_id=tournament_id, day=day).first()
            if round_obj:
                score = Score.query.filter_by(player_id=player.id, round_id=round_obj.id).first()
                if score and score.total_strokes:
                    has_any_scores = True
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
        
        # Set the net score if player has any scores
        if has_any_scores and total_net_score > 0:
            player_data['net_score'] = total_net_score
        else:
            player_data['net_score'] = None
        
        # Calculate special prizes won by this player
        try:
            special_prizes = SpecialPrize.query.filter_by(
                tournament_id=tournament_id, 
                player_id=player.id
            ).all()
            player_data['special_prizes_won'] = len(special_prizes) * 30000  # R30,000 per special prize
        except Exception:
            # Handle case where day column doesn't exist yet
            player_data['special_prizes_won'] = 0
        
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
    player_count = len(players)
    prize_distribution = get_prize_distribution(player_count)
    
    # Handle ties and calculate split prize money
    current_rank = 1
    i = 0
    
    while i < len(leaderboard):
        # Find all players with the same score (tied players)
        tied_players = [leaderboard[i]]
        current_score = leaderboard[i]['net_score']
        current_points = leaderboard[i]['total_points']
        
        # Look for tied players
        j = i + 1
        while j < len(leaderboard) and leaderboard[j]['net_score'] == current_score and leaderboard[j]['total_points'] == current_points:
            tied_players.append(leaderboard[j])
            j += 1
        
        # Calculate prize money for tied positions
        if len(tied_players) > 1:
            # Calculate total prize money for tied positions
            total_tied_prize = 0
            for pos in range(current_rank, current_rank + len(tied_players)):
                total_tied_prize += prize_distribution['main_prizes'].get(pos, 0)
            
            # Split the prize equally among tied players
            split_prize = total_tied_prize // len(tied_players)
            
            # Assign same rank and split prize to all tied players
            for player_data in tied_players:
                player_data['rank'] = current_rank
                player_data['prize'] = split_prize
                player_data['total_winnings'] = player_data['prize'] + player_data['special_prizes_won']
                player_data['is_tied'] = True
        else:
            # Single player at this position
            player_data = tied_players[0]
            player_data['rank'] = current_rank
            player_data['prize'] = prize_distribution['main_prizes'].get(current_rank, 0)
            player_data['total_winnings'] = player_data['prize'] + player_data['special_prizes_won']
            player_data['is_tied'] = False
        
        # Move to next unprocessed position
        current_rank += len(tied_players)
        i = j
    
    return leaderboard