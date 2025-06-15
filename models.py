from app import db
from datetime import datetime
from sqlalchemy import func

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="The Pinical Point Family Golf Champions Cup")
    start_date = db.Column(db.Date, nullable=False)
    total_prize_pool = db.Column(db.Integer, default=1150000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    players = db.relationship('Player', backref='tournament', lazy=True)
    rounds = db.relationship('Round', backref='tournament', lazy=True)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    handicap = db.Column(db.Integer, default=0)
    prize_eligible = db.Column(db.Boolean, default=True)  # New field for prize eligibility
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    scores = db.relationship('Score', backref='player', lazy=True)

class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    day = db.Column(db.Integer, nullable=False)  # 1, 2, or 3
    format = db.Column(db.String(50), nullable=False)  # 'stroke_play', 'stableford', 'scramble'
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    scores = db.relationship('Score', backref='round', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    
    # Hole-by-hole scores (18 holes)
    hole_1 = db.Column(db.Integer)
    hole_2 = db.Column(db.Integer)
    hole_3 = db.Column(db.Integer)
    hole_4 = db.Column(db.Integer)
    hole_5 = db.Column(db.Integer)
    hole_6 = db.Column(db.Integer)
    hole_7 = db.Column(db.Integer)
    hole_8 = db.Column(db.Integer)
    hole_9 = db.Column(db.Integer)
    hole_10 = db.Column(db.Integer)
    hole_11 = db.Column(db.Integer)
    hole_12 = db.Column(db.Integer)
    hole_13 = db.Column(db.Integer)
    hole_14 = db.Column(db.Integer)
    hole_15 = db.Column(db.Integer)
    hole_16 = db.Column(db.Integer)
    hole_17 = db.Column(db.Integer)
    hole_18 = db.Column(db.Integer)
    
    # Calculated totals
    total_strokes = db.Column(db.Integer)
    stableford_points = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_hole_score(self, hole_number):
        """Get score for a specific hole (1-18)"""
        return getattr(self, f'hole_{hole_number}', None)
    
    def set_hole_score(self, hole_number, score):
        """Set score for a specific hole (1-18)"""
        setattr(self, f'hole_{hole_number}', score)
    
    def calculate_totals(self):
        """Calculate total strokes and stableford points with handicap"""
        hole_scores = []
        for i in range(1, 19):
            score = self.get_hole_score(i)
            if score is not None:
                hole_scores.append(score)
        
        if hole_scores:
            self.total_strokes = sum(hole_scores)
            
            # Calculate Stableford points with handicap
            player_handicap = self.player.handicap
            handicap_strokes = self._distribute_handicap_strokes(player_handicap)
            
            stableford_total = 0
            for i, score in enumerate(hole_scores):
                if i < len(PINACLEPOINT_COURSE['holes']):
                    hole_par = PINACLEPOINT_COURSE['holes'][i]['par']
                    hole_handicap_strokes = handicap_strokes.get(i + 1, 0)
                    
                    # Net score = gross score - handicap strokes for this hole
                    net_score = score - hole_handicap_strokes
                    
                    # Stableford points calculation
                    if net_score <= hole_par - 2:  # Eagle or better
                        points = 4
                    elif net_score == hole_par - 1:  # Birdie
                        points = 3
                    elif net_score == hole_par:  # Par
                        points = 2
                    elif net_score == hole_par + 1:  # Bogey
                        points = 1
                    else:  # Double bogey or worse
                        points = 0
                    
                    stableford_total += points
            
            self.stableford_points = stableford_total
    
    def _distribute_handicap_strokes(self, handicap):
        """Distribute handicap strokes across holes based on hole difficulty"""
        # Initialize handicap strokes for each hole
        handicap_strokes = {}
        for i in range(1, 19):
            handicap_strokes[i] = 0
        
        # If handicap is 0 or negative, no strokes given
        if handicap <= 0:
            return handicap_strokes
        
        # Sort holes by handicap rating (difficulty) - lower number = harder hole
        holes_by_difficulty = sorted(PINACLEPOINT_COURSE['holes'], key=lambda x: x['handicap'])
        
        remaining_strokes = int(handicap)
        
        # First round: Give one stroke to holes based on difficulty
        # Start with hardest holes (lowest handicap rating)
        for hole in holes_by_difficulty:
            if remaining_strokes > 0:
                hole_number = hole['number']
                handicap_strokes[hole_number] = 1
                remaining_strokes -= 1
        
        # Second round: If handicap > 18, give second strokes starting with hardest holes again
        if remaining_strokes > 0:
            for hole in holes_by_difficulty:
                if remaining_strokes > 0:
                    hole_number = hole['number']
                    handicap_strokes[hole_number] = 2
                    remaining_strokes -= 1
        
        # Third round: If handicap > 36, give third strokes (rare case)
        if remaining_strokes > 0:
            for hole in holes_by_difficulty:
                if remaining_strokes > 0:
                    hole_number = hole['number']
                    handicap_strokes[hole_number] = 3
                    remaining_strokes -= 1
        
        return handicap_strokes
    
    def get_net_score(self):
        """Get handicap-adjusted net score"""
        if self.total_strokes:
            return self.total_strokes - self.player.handicap
        return None

class SpecialPrize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    day = db.Column(db.Integer, nullable=False)  # 1, 2, or 3
    prize_type = db.Column(db.String(50), nullable=False)  # 'longest_drive', 'closest_hole', 'most_birdies'
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)
    amount = db.Column(db.Integer, default=10000)  # Prize amount (split equally among tied winners)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    player = db.relationship('Player', backref='special_prizes')
    tournament = db.relationship('Tournament', backref='special_prizes')

class HandicapPlayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    calculated_handicap = db.Column(db.Integer, nullable=True)
    is_applied_to_tournament = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rounds = db.relationship('HandicapRound', backref='player', lazy=True, cascade='all, delete-orphan')

class HandicapRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('handicap_player.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4
    
    # Hole-by-hole scores (18 holes)
    hole_1 = db.Column(db.Integer)
    hole_2 = db.Column(db.Integer)
    hole_3 = db.Column(db.Integer)
    hole_4 = db.Column(db.Integer)
    hole_5 = db.Column(db.Integer)
    hole_6 = db.Column(db.Integer)
    hole_7 = db.Column(db.Integer)
    hole_8 = db.Column(db.Integer)
    hole_9 = db.Column(db.Integer)
    hole_10 = db.Column(db.Integer)
    hole_11 = db.Column(db.Integer)
    hole_12 = db.Column(db.Integer)
    hole_13 = db.Column(db.Integer)
    hole_14 = db.Column(db.Integer)
    hole_15 = db.Column(db.Integer)
    hole_16 = db.Column(db.Integer)
    hole_17 = db.Column(db.Integer)
    hole_18 = db.Column(db.Integer)
    
    # Calculated values
    total_score = db.Column(db.Integer)
    differential = db.Column(db.Float)  # Score differential for handicap calculation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_hole_score(self, hole_number):
        """Get score for a specific hole (1-18)"""
        return getattr(self, f'hole_{hole_number}', None)
    
    def set_hole_score(self, hole_number, score):
        """Set score for a specific hole (1-18)"""
        setattr(self, f'hole_{hole_number}', score)
    
    def calculate_differential(self):
        """Calculate score differential for handicap calculation"""
        hole_scores = []
        for i in range(1, 19):
            score = self.get_hole_score(i)
            if score is not None:
                hole_scores.append(score)
        
        if len(hole_scores) == 18:
            self.total_score = sum(hole_scores)
            # Differential = (Score - Course Rating) × 113 / Slope Rating
            # Using Pinaclepoint: Course Rating = 72, Slope = 113
            course_rating = 72
            slope_rating = 113
            self.differential = (self.total_score - course_rating) * 113 / slope_rating
        
        return self.differential

# Pinaclepoint Golf Estate course data
PINACLEPOINT_COURSE = {
    'holes': [
        # Front Nine - Par 35
        {'number': 1, 'par': 4, 'yards': 369, 'meters': 337, 'handicap': 12, 
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-1.jpg',
         'description': 'A challenging opening hole with ocean views'},
        {'number': 2, 'par': 4, 'yards': 340, 'meters': 311, 'handicap': 8,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-2.jpg',
         'description': 'Strategic placement required off the tee'},
        {'number': 3, 'par': 4, 'yards': 457, 'meters': 418, 'handicap': 16,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-3.jpg',
         'description': 'Long par 4 with prevailing wind'},
        {'number': 4, 'par': 4, 'yards': 439, 'meters': 401, 'handicap': 2,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-4.jpg',
         'description': 'Demanding approach shot to elevated green'},
        {'number': 5, 'par': 5, 'yards': 522, 'meters': 477, 'handicap': 18,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-5.jpg',
         'description': 'Reachable par 5 with risk-reward opportunity'},
        {'number': 6, 'par': 4, 'yards': 355, 'meters': 325, 'handicap': 10,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-6.jpg',
         'description': 'Short par 4 requiring accuracy'},
        {'number': 7, 'par': 3, 'yards': 129, 'meters': 118, 'handicap': 14,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-7.jpg',
         'description': 'Short iron to well-protected green'},
        {'number': 8, 'par': 4, 'yards': 350, 'meters': 320, 'handicap': 6,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-8.jpg',
         'description': 'Dogleg right with bunker protection'},
        {'number': 9, 'par': 3, 'yards': 185, 'meters': 169, 'handicap': 4,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-9.jpg',
         'description': 'Spectacular finishing hole for the front nine'},
        # Back Nine - Par 37
        {'number': 10, 'par': 4, 'yards': 368, 'meters': 337, 'handicap': 11,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-10.jpg',
         'description': 'Opening hole of the back nine'},
        {'number': 11, 'par': 4, 'yards': 374, 'meters': 342, 'handicap': 13,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-11.jpg',
         'description': 'Slight dogleg with strategic bunkering'},
        {'number': 12, 'par': 4, 'yards': 375, 'meters': 343, 'handicap': 5,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-12.jpg',
         'description': 'Challenging mid-length par 4'},
        {'number': 13, 'par': 3, 'yards': 133, 'meters': 122, 'handicap': 15,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-13.jpg',
         'description': 'Short par 3 with water hazard'},
        {'number': 14, 'par': 4, 'yards': 408, 'meters': 373, 'handicap': 9,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-14.jpg',
         'description': 'Long par 4 with ocean backdrop'},
        {'number': 15, 'par': 4, 'yards': 356, 'meters': 326, 'handicap': 17,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-15.jpg',
         'description': 'Scenic hole with coastal views'},
        {'number': 16, 'par': 5, 'yards': 579, 'meters': 529, 'handicap': 1,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-16.jpg',
         'description': 'Signature hole - The most challenging on the course'},
        {'number': 17, 'par': 3, 'yards': 226, 'meters': 207, 'handicap': 3,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-17.jpg',
         'description': 'Long par 3 over dramatic cliff-top terrain'},
        {'number': 18, 'par': 5, 'yards': 495, 'meters': 453, 'handicap': 7,
         'image': 'https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/Hole-18.jpg',
         'description': 'Finishing hole with panoramic ocean views'},
    ]
}
class ArccosPlayerData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    arccos_user_id = db.Column(db.String(100), nullable=True)  # Arccos API user ID
    device_serial = db.Column(db.String(100), nullable=True)   # Link Pro device serial
    last_sync = db.Column(db.DateTime, default=datetime.utcnow)
    sync_status = db.Column(db.String(20), default='connected')  # connected, syncing, error
    
    # Performance metrics from latest round
    avg_drive_distance = db.Column(db.Float, nullable=True)
    fairways_hit_percentage = db.Column(db.Float, nullable=True)
    greens_in_regulation_percentage = db.Column(db.Float, nullable=True)
    average_putts_per_hole = db.Column(db.Float, nullable=True)
    strokes_gained_total = db.Column(db.Float, nullable=True)
    strokes_gained_driving = db.Column(db.Float, nullable=True)
    strokes_gained_approach = db.Column(db.Float, nullable=True)
    strokes_gained_short_game = db.Column(db.Float, nullable=True)
    strokes_gained_putting = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player = db.relationship('Player', backref='arccos_data')
    tournament = db.relationship('Tournament', backref='arccos_players')

class ArccosRoundData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    arccos_round_id = db.Column(db.String(100), nullable=True)  # Arccos API round ID
    
    # Round-level analytics
    total_shots = db.Column(db.Integer, nullable=True)
    total_putts = db.Column(db.Integer, nullable=True)
    fairways_hit = db.Column(db.Integer, nullable=True)
    fairway_attempts = db.Column(db.Integer, nullable=True)
    greens_in_regulation = db.Column(db.Integer, nullable=True)
    scrambling_saves = db.Column(db.Integer, nullable=True)
    scrambling_attempts = db.Column(db.Integer, nullable=True)
    
    # Distance tracking
    longest_drive = db.Column(db.Float, nullable=True)
    avg_drive_distance = db.Column(db.Float, nullable=True)
    total_walking_distance = db.Column(db.Float, nullable=True)  # From Link Pro GPS
    
    # JSON field for detailed hole-by-hole shot data
    shot_data = db.Column(db.Text, nullable=True)  # JSON string with detailed shot information
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    player = db.relationship('Player', backref='arccos_rounds')
    round = db.relationship('Round', backref='arccos_data')
