from flask import Flask, render_template, request, redirect, url_for, flash
import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='../templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sophies_garden.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    is_read = db.Column(db.Boolean, default=False)

class Plant(db.Model):
    __tablename__ = 'plants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    scientific_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(300))
    in_stock = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.now())

@app.route('/')
def index():
    featured_plants = Plant.query.filter_by(in_stock=True).limit(6).all()
    return render_template('index.html', plants=featured_plants)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if name and email and subject and message:
            contact_message = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            db.session.add(contact_message)
            db.session.commit()
            flash('Thank you for your message! We\'ll get back to you soon.', 'success')
            return redirect(url_for('contact'))
        else:
            flash('Please fill in all fields.', 'error')

    return render_template('contact.html')

@app.route('/admin')
def admin():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    plants = Plant.query.all()
    return render_template('admin.html', messages=messages, plants=plants)

@app.route('/admin/mark-read/<int:message_id>')
def mark_read(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.is_read = True
    db.session.commit()
    flash('Message marked as read.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete-message/<int:message_id>')
def delete_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(url_for('admin'))

@app.route('/plants')
def plants():
    category = request.args.get('category', 'all')
    if category == 'all':
        plants = Plant.query.filter_by(in_stock=True).all()
    else:
        plants = Plant.query.filter_by(category=category, in_stock=True).all()

    categories = db.session.query(Plant.category).distinct().all()
    categories = [cat[0] for cat in categories]

    return render_template('plants.html', plants=plants, categories=categories, current_category=category)

@app.route('/plant/<int:plant_id>')
def plant_detail(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    return render_template('plant_detail.html', plant=plant)

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

if __name__ == '__main__':
    app.run(debug=True)
