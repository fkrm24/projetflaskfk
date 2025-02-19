from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import requests
from models import db, User, UserMedia
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_clé_secrète_ici'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation des extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Définir l'API Key de TMDb
TMDB_API_KEY = '8d4fc893b858ab88c9e7a389648f2b69'
BASE_URL = "https://api.themoviedb.org/3"

# Fonction pour récupérer les films récemment sortis
def get_recently_released_films():
    url = f"{BASE_URL}/movie/now_playing?api_key={TMDB_API_KEY}&language=fr-FR"
    response = requests.get(url)
    data = response.json()
    # Limiter à 10 films
    return data['results'][:10]

# Fonction pour récupérer les films les mieux notés
def get_top_rated_films():
    url = f"{BASE_URL}/movie/top_rated?api_key={TMDB_API_KEY}&language=fr-FR"
    response = requests.get(url)
    data = response.json()
    # Limiter à 10 films
    return data['results'][:10]

# Fonction pour rechercher des films
def search_movies(query):
    url = f"{BASE_URL}/search/movie?api_key={TMDB_API_KEY}&language=fr-FR&query={query}"
    response = requests.get(url)
    data = response.json()
    return data['results']

@app.route('/')
@app.route('/index')
def index():
    # Récupérer les films récemment sortis
    recent_films = get_recently_released_films()
    
    # Récupérer les films les mieux notés
    top_rated_films = get_top_rated_films()
    
    return render_template('index.html', 
                         recent_films=recent_films, 
                         top_rated_films=top_rated_films)

@app.route('/recherche')
@login_required
def recherche():
    query = request.args.get('query')
    if query:
        search_results = search_movies(query)
        return render_template('recherche.html', search_results=search_results, search_query=query)
    return render_template('recherche.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Inscription réussie ! Vous pouvez maintenant vous connecter.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
            
        flash('Nom d\'utilisateur ou mot de passe incorrect')
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/ma-collection')
@login_required
def ma_collection():
    a_voir = UserMedia.query.filter_by(
        user_id=current_user.id, 
        to_watch=True
    ).all()
    
    vu = UserMedia.query.filter_by(
        user_id=current_user.id, 
        watched=True
    ).all()
    
    # Ajouter les attributs data pour le tri
    for media in a_voir + vu:
        media.date_added_str = media.date_added.isoformat() if media.date_added else ''
        media.date_watched_str = media.date_watched.isoformat() if media.date_watched else ''
        if not media.rating:
            media.rating = 0
        
    return render_template('ma_collection.html', a_voir=a_voir, vu=vu)

@app.route('/ajouter-media', methods=['POST'])
@login_required
def ajouter_media():
    tmdb_id = request.form.get('tmdb_id')
    media_type = request.form.get('media_type')
    status = request.form.get('status', 'A_VOIR')
    
    # Vérifier si le média existe déjà
    existing = UserMedia.query.filter_by(
        user_id=current_user.id,
        tmdb_id=tmdb_id,
        media_type=media_type
    ).first()
    
    if existing:
        flash('Ce média est déjà dans votre collection!')
        return redirect(url_for('ma_collection'))
    
    # Récupérer les détails depuis TMDB
    url = f"{BASE_URL}/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}&language=fr-FR"
    response = requests.get(url)
    data = response.json()
    
    media = UserMedia(
        user_id=current_user.id,
        tmdb_id=tmdb_id,
        title=data.get('title') or data.get('name'),
        media_type=media_type,
        status=status,
        poster_path=data.get('poster_path')
    )
    
    db.session.add(media)
    db.session.commit()
    flash('Média ajouté avec succès!')
    return redirect(url_for('ma_collection'))

@app.route('/modifier-media/<int:media_id>', methods=['POST'])
@login_required
def modifier_media(media_id):
    media = UserMedia.query.get_or_404(media_id)
    if media.user_id != current_user.id:
        return jsonify({'error': 'Non autorisé'}), 403
        
    if 'status' in request.form:
        media.status = request.form['status']
        if media.status == 'VU' and not media.date_watched:
            media.date_watched = datetime.utcnow()
            
    if 'rating' in request.form:
        media.rating = int(request.form['rating'])
    if 'comment' in request.form:
        media.comment = request.form['comment']
    if 'is_favorite' in request.form:
        media.is_favorite = request.form['is_favorite'] == 'true'
    if 'tier' in request.form:
        media.tier = request.form['tier']
        
    db.session.commit()
    return jsonify(media.to_dict())

@app.route('/supprimer-media/<int:media_id>', methods=['POST'])
@login_required
def supprimer_media(media_id):
    media = UserMedia.query.get_or_404(media_id)
    if media.user_id != current_user.id:
        return jsonify({'error': 'Non autorisé'}), 403
        
    db.session.delete(media)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/favoris')
@login_required
def favoris():
    favoris = UserMedia.query.filter_by(
        user_id=current_user.id,
        favorite=True
    ).all()
    return render_template('favoris.html', favoris=favoris)

@app.route('/tier-list')
@login_required
def tier_list():
    medias = UserMedia.query.filter_by(
        user_id=current_user.id,
        watched=True
    ).order_by(UserMedia.tier).all()
    
    tiers = {
        'S': [],
        'A': [],
        'B': [],
        'C': [],
        'D': [],
        'F': []
    }
    
    # Organiser les médias par tier
    for media in medias:
        if media.tier:
            tiers[media.tier].append(media)
        
    return render_template('tier_list.html', tiers=tiers)

@app.route('/film/<int:film_id>')
def film_details(film_id):
    # Récupérer les détails du film
    url = f"{BASE_URL}/movie/{film_id}?api_key={TMDB_API_KEY}&language=fr-FR&append_to_response=credits,videos"
    response = requests.get(url)
    film = response.json()
    
    # Vérifier si le film est dans la collection de l'utilisateur
    user_media = None
    if current_user.is_authenticated:
        user_media = UserMedia.query.filter_by(
            user_id=current_user.id,
            tmdb_id=film_id,
            media_type='movie'
        ).first()
    
    return render_template('film_details.html', film=film, user_media=user_media)

@app.route('/ajouter-statut', methods=['POST'])
@login_required
def ajouter_statut():
    data = request.get_json()
    tmdb_id = data.get('tmdb_id')
    media_type = data.get('media_type')
    status = data.get('status')  # 'to_watch', 'watched', 'favorite'
    
    # Récupérer les détails du film depuis l'API TMDb
    url = f"{BASE_URL}/movie/{tmdb_id}?api_key={TMDB_API_KEY}&language=fr-FR"
    response = requests.get(url)
    film_data = response.json()
    
    user_media = UserMedia.query.filter_by(
        user_id=current_user.id,
        tmdb_id=tmdb_id,
        media_type=media_type
    ).first()
    
    if not user_media:
        user_media = UserMedia(
            user_id=current_user.id,
            tmdb_id=tmdb_id,
            media_type=media_type,
            title=film_data.get('title'),
            poster_path=film_data.get('poster_path'),
            date_added=datetime.utcnow()
        )
        db.session.add(user_media)
    
    if status == 'to_watch':
        user_media.to_watch = not user_media.to_watch
        if user_media.to_watch:
            user_media.watched = False
    elif status == 'watched':
        user_media.watched = not user_media.watched
        if user_media.watched:
            user_media.to_watch = False
            user_media.date_watched = datetime.utcnow()
    elif status == 'favorite':
        user_media.favorite = not user_media.favorite
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'status': status,
        'to_watch': user_media.to_watch,
        'watched': user_media.watched,
        'favorite': user_media.favorite
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
