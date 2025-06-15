from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Tournament, Player, Round, Score, SpecialPrize, PINACLEPOINT_COURSE
from datetime import datetime, date
from sqlalchemy import func

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
                'longest_drive': 10000, 
                'closest_hole': 10000, 
                'most_birdies': 10000,
                'straightest_drive': 10000,
                'most_pars': 10000
            },
            'day_2': {
                'longest_drive': 10000, 
                'closest_hole': 10000, 
                'most_birdies': 10000,
                'straightest_drive': 10000,
                'most_pars': 10000
            },
            'day_3': {
                'longest_drive': 10000, 
                'closest_hole': 10000, 
                'most_birdies': 10000,
                'straightest_drive': 10000,
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
    """Manage daily special prizes (most pars front 9, most pars back 9, beat handicap)"""
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('player_setup'))
    
    players = Player.query.filter_by(tournament_id=tournament.id).all()
    rounds = Round.query.filter_by(tournament_id=tournament.id).order_by(Round.day).all()
    
    # Get existing special prize winners organized by day
    daily_special_prizes = {}
    for day in [1, 2, 3]:
        daily_special_prizes[day] = {}
        for prize_type in ['most_pars_front', 'most_pars_back', 'beat_handicap', 'straightest_drive', 'most_pars']:
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
    
    # 1. Longest Drive - lowest total strokes (best overall performance proxy)
    longest_drive_winner = min(scores_with_data, key=lambda x: x.total_strokes)
    winners['longest_drive'] = [longest_drive_winner.player_id]
    
    # 2. Most Birdies - highest stableford points
    if scores_with_data[0].stableford_points is not None:
        max_points = max(scores_with_data, key=lambda x: x.stableford_points or 0).stableford_points or 0
        most_birdies_winners = [s.player_id for s in scores_with_data if (s.stableford_points or 0) == max_points]
        winners['most_birdies'] = most_birdies_winners
    else:
        winners['most_birdies'] = []
    
    # 3. Closest to Hole - second best score
    sorted_scores = sorted(scores_with_data, key=lambda x: x.total_strokes)
    if len(sorted_scores) >= 2:
        winners['closest_hole'] = [sorted_scores[1].player_id]
    else:
        winners['closest_hole'] = []
    
    # 4. Straightest Drive - third best score (if exists)
    if len(sorted_scores) >= 3:
        winners['straightest_drive'] = [sorted_scores[2].player_id]
    else:
        winners['straightest_drive'] = []
    
    # 5. Most Pars - middle performer (median score)
    if len(sorted_scores) >= 1:
        median_index = len(sorted_scores) // 2
        winners['most_pars'] = [sorted_scores[median_index].player_id]
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
        
        # Calculate special prizes won by this player (both manual and automatic)
        special_prizes_total = 0
        special_prizes_detail = []
        
        try:
            # Manual special prizes from database
            manual_special_prizes = SpecialPrize.query.filter_by(
                tournament_id=tournament_id, 
                player_id=player.id
            ).all()
            for prize in manual_special_prizes:
                special_prizes_total += 10000  # R10,000 per manual special prize
                special_prizes_detail.append(f"Day {prize.day} {prize.prize_type.replace('_', ' ').title()}")
        except Exception:
            # Handle case where day column doesn't exist yet
            pass
        
        # Automatic special prizes based on performance
        for day in [1, 2, 3]:
            daily_winners = calculate_daily_special_prizes(tournament_id, day)
            for prize_type, winner_ids in daily_winners.items():
                if player.id in winner_ids and len(winner_ids) > 0:
                    # Split prize money among tied winners
                    prize_amount = 10000 // len(winner_ids)  # R10,000 split among winners
                    special_prizes_total += prize_amount
                    if len(winner_ids) > 1:
                        special_prizes_detail.append(f"Day {day} {prize_type.replace('_', ' ').title()} (Split {len(winner_ids)} ways)")
                    else:
                        special_prizes_detail.append(f"Day {day} {prize_type.replace('_', ' ').title()}")
        
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