from app import app, db, Plant
from datetime import datetime

def init_database():
    with app.app_context():
        print("Creating database tables...")
        db.create_all()

        print("Adding sample plants...")
        sample_plants = [
            {
                'name': 'Garden Rose',
                'scientific_name': 'Rosa hybrida',
                'description': 'Beautiful hybrid tea rose with perfect blooms and lovely fragrance. Ideal for cutting gardens.',
                'price': 24.99,
                'category': 'Flowers',
                'image_url': 'https://via.placeholder.com/300x200/ffcccc/000000?text=Garden+Rose'
            },
            {
                'name': 'Lavender',
                'scientific_name': 'Lavandula angustifolia',
                'description': 'English lavender known for its calming scent and beautiful purple spikes. Perfect for aromatherapy.',
                'price': 18.99,
                'category': 'Herbs',
                'image_url': 'https://via.placeholder.com/300x200/ddccff/000000?text=Lavender'
            },
            {
                'name': 'Snake Plant',
                'scientific_name': 'Sansevieria trifasciata',
                'description': 'Low-maintenance indoor plant that purifies air. Thrives in low light conditions.',
                'price': 32.99,
                'category': 'Indoor Plants',
                'image_url': 'https://via.placeholder.com/300x200/ccffcc/000000?text=Snake+Plant'
            },
            {
                'name': 'Cherry Tomato',
                'scientific_name': 'Solanum lycopersicum',
                'description': 'Sweet cherry tomatoes perfect for container gardening. High yield and easy to grow.',
                'price': 12.99,
                'category': 'Vegetables',
                'image_url': 'https://via.placeholder.com/300x200/ffddaa/000000?text=Cherry+Tomato'
            },
            {
                'name': 'Sunflower',
                'scientific_name': 'Helianthus annuus',
                'description': 'Tall, cheerful sunflowers that attract pollinators and brighten any garden.',
                'price': 8.99,
                'category': 'Flowers',
                'image_url': 'https://via.placeholder.com/300x200/ffffaa/000000?text=Sunflower'
            },
            {
                'name': 'Basil',
                'scientific_name': 'Ocimum basilicum',
                'description': 'Aromatic herb essential for Italian cuisine. Easy to grow in containers or garden beds.',
                'price': 6.99,
                'category': 'Herbs',
                'image_url': 'https://via.placeholder.com/300x200/aaffaa/000000?text=Basil'
            }
        ]

        for plant_data in sample_plants:
            plant = Plant(**plant_data)
            db.session.add(plant)

        db.session.commit()
        print("Database initialized successfully!")
        print(f"Added {len(sample_plants)} sample plants to the database.")

if __name__ == '__main__':
    init_database()