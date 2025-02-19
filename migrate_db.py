from app import app, db
from models import UserMedia

def migrate_database():
    with app.app_context():
        # Supprimer la base de données existante
        db.drop_all()
        
        # Créer la nouvelle base de données avec les nouveaux champs
        db.create_all()
        
        print("Base de données migrée avec succès!")

if __name__ == '__main__':
    migrate_database()
