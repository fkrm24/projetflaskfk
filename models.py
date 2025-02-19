from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    medias = db.relationship('UserMedia', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tmdb_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    media_type = db.Column(db.String(10))  # 'movie' ou 'series'
    to_watch = db.Column(db.Boolean, default=False)
    watched = db.Column(db.Boolean, default=False)
    favorite = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Integer)  # Note sur 5
    comment = db.Column(db.Text)
    tier = db.Column(db.String(1))  # 'S', 'A', 'B', 'C', 'D', 'F'
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_watched = db.Column(db.DateTime)
    poster_path = db.Column(db.String(200))
    
    def to_dict(self):
        return {
            'id': self.id,
            'tmdb_id': self.tmdb_id,
            'title': self.title,
            'media_type': self.media_type,
            'to_watch': self.to_watch,
            'watched': self.watched,
            'favorite': self.favorite,
            'rating': self.rating,
            'comment': self.comment,
            'tier': self.tier,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'date_watched': self.date_watched.isoformat() if self.date_watched else None,
            'poster_path': self.poster_path
        }
