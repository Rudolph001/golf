from app import db
from datetime import datetime
from sqlalchemy import func

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="The Pinical Point Family Golf Champions Cup")
    start_date = db.Column(db.Date, nullable=False)
    total_prize_pool = db.Column(db.Integer, default=1000000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    players = db.relationship('Player', backref='tournament', lazy=True)
    rounds = db.relationship('Round', backref='tournament', lazy=True)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    handicap = db.Column(db.Integer, default=0)
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
        handicap_strokes = {}
        
        # Sort holes by handicap rating (difficulty)
        holes_by_difficulty = sorted(PINACLEPOINT_COURSE['holes'], key=lambda x: x['handicap'])
        
        # Distribute strokes starting with most difficult holes
        remaining_strokes = handicap
        for hole in holes_by_difficulty:
            if remaining_strokes > 0:
                hole_number = hole['number']
                handicap_strokes[hole_number] = 1
                remaining_strokes -= 1
                
                # If handicap > 18, give second stroke to most difficult holes
                if remaining_strokes > 0 and handicap > 18:
                    handicap_strokes[hole_number] = 2
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
    amount = db.Column(db.Integer, default=6667)  # R6,667 for each special prize
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    player = db.relationship('Player', backref='special_prizes')
    tournament = db.relationship('Tournament', backref='special_prizes')

# Pinaclepoint Golf Estate course data
PINACLEPOINT_COURSE = {
    'holes': [
        {'number': 1, 'par': 4, 'yards': 350, 'handicap': 9},
        {'number': 2, 'par': 3, 'yards': 165, 'handicap': 17},
        {'number': 3, 'par': 5, 'yards': 520, 'handicap': 3},
        {'number': 4, 'par': 4, 'yards': 380, 'handicap': 11},
        {'number': 5, 'par': 4, 'yards': 410, 'handicap': 5},
        {'number': 6, 'par': 3, 'yards': 145, 'handicap': 15},
        {'number': 7, 'par': 4, 'yards': 395, 'handicap': 7},
        {'number': 8, 'par': 5, 'yards': 485, 'handicap': 1},
        {'number': 9, 'par': 4, 'yards': 425, 'handicap': 13},
        {'number': 10, 'par': 4, 'yards': 365, 'handicap': 10},
        {'number': 11, 'par': 3, 'yards': 175, 'handicap': 18},
        {'number': 12, 'par': 5, 'yards': 545, 'handicap': 2},
        {'number': 13, 'par': 4, 'yards': 400, 'handicap': 12},
        {'number': 14, 'par': 4, 'yards': 385, 'handicap': 6},
        {'number': 15, 'par': 3, 'yards': 155, 'handicap': 16},
        {'number': 16, 'par': 4, 'yards': 435, 'handicap': 4},
        {'number': 17, 'par': 5, 'yards': 510, 'handicap': 8},
        {'number': 18, 'par': 4, 'yards': 445, 'handicap': 14},
    ]
}
