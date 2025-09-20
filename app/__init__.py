from flask import Flask, render_template, request, redirect, url_for, flash
import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import pymysql
from sqlalchemy import or_, func
from urllib.parse import quote_plus

load_dotenv()

# Fix for MySQLdb compatibility
pymysql.install_as_MySQLdb()

app = Flask(
    __name__,
    template_folder='../templates',
    static_folder='../static',
    static_url_path='/static',
)
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

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True)
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text)
    author = db.Column(db.String(120))
    cover_image_url = db.Column(db.String(300))
    tags = db.Column(db.String(300))  # comma-separated
    is_published = db.Column(db.Boolean, default=True)
    published_at = db.Column(db.DateTime, default=db.func.now(), index=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

# Ensure tables exist (safe no-ops for existing tables)
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        # Avoid crashing the app if DB user has no DDL privileges
        print(f"Warning: could not create tables automatically: {e}")

@app.route('/')
def index():
    featured_plants = Plant.query.filter_by(in_stock=True).order_by(Plant.created_at.desc()).limit(6).all()
    recent_posts = []
    try:
        recent_posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.published_at.desc()).limit(3).all()
    except Exception:
        # If blog table isn't present yet, fail gracefully
        recent_posts = []
    return render_template('index.html', plants=featured_plants, posts=recent_posts)

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

@app.route('/dashboard')
def dashboard():
    # Stats
    total_plants = Plant.query.count()
    in_stock_count = Plant.query.filter_by(in_stock=True).count()
    categories_count = db.session.query(Plant.category).distinct().count()
    total_messages = ContactMessage.query.count()
    unread_count = ContactMessage.query.filter_by(is_read=False).count()

    # Message search/filter
    q_msg = (request.args.get('q_msg') or '').strip()
    msg_query = ContactMessage.query
    if q_msg:
        like = f"%{q_msg}%"
        msg_query = msg_query.filter(
            or_(
                ContactMessage.name.ilike(like),
                ContactMessage.email.ilike(like),
                ContactMessage.subject.ilike(like),
                ContactMessage.message.ilike(like),
            )
        )
    messages = msg_query.order_by(ContactMessage.created_at.desc()).limit(50).all()

    # Plant search/filter
    q_plant = (request.args.get('q_plant') or '').strip()
    only_in_stock = request.args.get('in_stock') == '1'
    plant_query = Plant.query
    if q_plant:
        like = f"%{q_plant}%"
        plant_query = plant_query.filter(
            or_(
                Plant.name.ilike(like),
                Plant.scientific_name.ilike(like),
                Plant.category.ilike(like),
            )
        )
    if only_in_stock:
        plant_query = plant_query.filter_by(in_stock=True)
    plants = plant_query.order_by(Plant.created_at.desc()).limit(100).all()

    return render_template(
        'dashboard.html',
        messages=messages,
        plants=plants,
        total_plants=total_plants,
        in_stock_count=in_stock_count,
        categories_count=categories_count,
        total_messages=total_messages,
        unread_count=unread_count,
        q_msg=q_msg,
        q_plant=q_plant,
        only_in_stock=only_in_stock,
    )

@app.route('/admin')
def admin_legacy():
    return redirect(url_for('dashboard'))

@app.route('/dashboard/mark-read/<int:message_id>')
def dashboard_mark_read(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.is_read = True
    db.session.commit()
    flash('Message marked as read.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/dashboard/delete-message/<int:message_id>')
def dashboard_delete_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/plants')
def plants():
    category = (request.args.get('category', 'all') or 'all').lower()
    query = Plant.query.filter_by(in_stock=True)
    if category != 'all':
        alias_map = {
            'flower': ['flower', 'flowers'],
            'fruit': ['fruit', 'fruits'],
            'vegetable': ['vegetable', 'vegetables', 'veggies'],
        }
        aliases = alias_map.get(category, [category])
        query = query.filter(func.lower(Plant.category).in_(aliases))
    plants = query.all()

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
    page = request.args.get('page', 1, type=int)
    per_page = 6
    q = (request.args.get('q') or '').strip()
    tag = (request.args.get('tag') or '').strip()

    query = BlogPost.query.filter_by(is_published=True)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(BlogPost.title.ilike(like),
                                 BlogPost.excerpt.ilike(like),
                                 BlogPost.content.ilike(like)))
    if tag:
        query = query.filter(BlogPost.tags.ilike(f"%{tag}%"))

    pagination = (query
                  .order_by(BlogPost.published_at.desc())
                  .paginate(page=page, per_page=per_page, error_out=False))
    posts = pagination.items

    # Build a simple tag cloud list (top 12 by frequency)
    all_tags = {}
    for p in BlogPost.query.filter_by(is_published=True).all():
        for t in (p.tags or '').split(','):
            t = t.strip()
            if not t:
                continue
            all_tags[t] = all_tags.get(t, 0) + 1
    tags = [t for t, _ in sorted(all_tags.items(), key=lambda kv: kv[1], reverse=True)[:12]]

    return render_template('blog.html', posts=posts, pagination=pagination, q=q, tag=tag, tags=tags)

@app.route('/blog/<int:post_id>')
def blog_detail(post_id):
    post = BlogPost.query.get_or_404(post_id)
    # Read time estimate
    words = len((post.content or '').split())
    read_minutes = max(1, int(round(words / 200.0)))
    # Related posts by tags
    related = []
    tags = [t.strip() for t in (post.tags or '').split(',') if t.strip()]
    if tags:
        tag_filters = [BlogPost.tags.like(f"%{t}%") for t in tags]
        related = (BlogPost.query
                   .filter(BlogPost.id != post.id, BlogPost.is_published == True)
                   .filter(or_(*tag_filters))
                   .order_by(BlogPost.published_at.desc())
                   .limit(3)
                   .all())
    # Prev/Next by publish date
    prev_post = (BlogPost.query
                 .filter(BlogPost.is_published == True, BlogPost.published_at < post.published_at)
                 .order_by(BlogPost.published_at.desc())
                 .first())
    next_post = (BlogPost.query
                 .filter(BlogPost.is_published == True, BlogPost.published_at > post.published_at)
                 .order_by(BlogPost.published_at.asc())
                 .first())
    # Share URLs
    current_url = request.url
    share_twitter = f"https://twitter.com/intent/tweet?text={quote_plus(post.title or '')}&url={quote_plus(current_url)}"
    share_facebook = f"https://www.facebook.com/sharer/sharer.php?u={quote_plus(current_url)}"
    return render_template('blog_detail.html', post=post, read_minutes=read_minutes, related=related, prev_post=prev_post, next_post=next_post, share_twitter=share_twitter, share_facebook=share_facebook)

if __name__ == '__main__':
    app.run(debug=True)
