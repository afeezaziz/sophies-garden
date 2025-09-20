from flask import Flask, render_template, request, redirect, url_for, flash
import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import pymysql
from sqlalchemy import or_, func
from urllib.parse import quote_plus
from datetime import datetime, timedelta
import csv
from io import StringIO

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

class GardenPlant(db.Model):
    __tablename__ = 'garden_plants'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(100))
    plant_name = db.Column(db.String(100), nullable=False)  # e.g., Tomato
    scientific_name = db.Column(db.String(200))
    category = db.Column(db.String(50), nullable=False)  # flower, fruit, vegetable, herb, tree
    variety = db.Column(db.String(100))
    source = db.Column(db.String(50))  # seed, seedling, cutting
    planting_date = db.Column(db.Date)
    location = db.Column(db.String(120))  # e.g., Bed A, Pot 3
    image_url = db.Column(db.String(300))
    status = db.Column(db.String(30), default='active')  # active, harvested, removed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

    observations = db.relationship('Observation', backref='plant', cascade='all, delete-orphan')
    care_events = db.relationship('CareEvent', backref='plant', cascade='all, delete-orphan')
    harvests = db.relationship('Harvest', backref='plant', cascade='all, delete-orphan')

class Observation(db.Model):
    __tablename__ = 'observations'
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('garden_plants.id'), nullable=False)
    date = db.Column(db.Date, default=db.func.current_date())
    height_cm = db.Column(db.Float)
    leaves = db.Column(db.Integer)
    flowers = db.Column(db.Integer)
    fruits = db.Column(db.Integer)
    pests = db.Column(db.String(200))
    diseases = db.Column(db.String(200))
    photo_url = db.Column(db.String(300))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

class CareEvent(db.Model):
    __tablename__ = 'care_events'
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('garden_plants.id'), nullable=False)
    date = db.Column(db.Date, default=db.func.current_date())
    type = db.Column(db.String(50))  # watering, fertilizing, pruning, weeding, transplanting, spray
    amount = db.Column(db.String(100))  # e.g., 500ml or 10-10-10 5g
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

class Harvest(db.Model):
    __tablename__ = 'harvests'
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('garden_plants.id'), nullable=False)
    date = db.Column(db.Date, default=db.func.current_date())
    quantity = db.Column(db.Float)
    unit = db.Column(db.String(20))  # g, kg, count
    quality = db.Column(db.String(50))
    notes = db.Column(db.Text)
    photo_url = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=db.func.now())

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

# ---- Garden Logbook ----

@app.route('/logbook')
def logbook():
    q = (request.args.get('q') or '').strip()
    category = (request.args.get('category') or 'all').lower()
    status = (request.args.get('status') or 'active').lower()

    query = GardenPlant.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            GardenPlant.plant_name.ilike(like),
            GardenPlant.nickname.ilike(like),
            GardenPlant.variety.ilike(like),
            GardenPlant.location.ilike(like),
        ))
    if category != 'all':
        query = query.filter(func.lower(GardenPlant.category) == category)
    if status != 'all':
        query = query.filter(func.lower(GardenPlant.status) == status)

    plants = query.order_by(GardenPlant.created_at.desc()).all()

    # Compute watering schedule info per plant
    due_map = {}
    today = datetime.utcnow().date()
    for p in plants:
        cat = (p.category or 'other').lower()
        water_interval = {
            'flower': 3,
            'fruit': 2,
            'vegetable': 2,
            'herb': 2,
            'tree': 4,
            'other': 3,
        }.get(cat, 3)
        # last watering
        dates = [ce.date for ce in (p.care_events or []) if ce.date and (ce.type or '').lower() == 'watering']
        last_water = max(dates) if dates else None
        next_water = (last_water + timedelta(days=water_interval)) if last_water else (today if p.planting_date is None else p.planting_date + timedelta(days=water_interval))
        water_due = next_water <= today if next_water else False
        water_soon = (next_water - today).days == 1 if next_water else False
        due_map[p.id] = {
            'next_water': next_water,
            'last_water': last_water,
            'water_due': water_due,
            'water_soon': water_soon,
            'water_interval_days': water_interval,
        }

    totals = {
        'plants': db.session.query(func.count(GardenPlant.id)).scalar() or 0,
        'observations': db.session.query(func.count(Observation.id)).scalar() or 0,
        'care': db.session.query(func.count(CareEvent.id)).scalar() or 0,
        'harvests': db.session.query(func.count(Harvest.id)).scalar() or 0,
    }

    categories = db.session.query(func.lower(GardenPlant.category)).distinct().all()
    categories = [c[0] for c in categories]

    return render_template('logbook.html', plants=plants, q=q, category=category, status=status, totals=totals, categories=categories, due_map=due_map)


@app.route('/logbook/new', methods=['GET', 'POST'])
def logbook_new():
    if request.method == 'POST':
        plant_name = (request.form.get('plant_name') or '').strip()
        category = (request.form.get('category') or '').strip().lower()
        nickname = (request.form.get('nickname') or '').strip()
        scientific_name = (request.form.get('scientific_name') or '').strip()
        variety = (request.form.get('variety') or '').strip()
        source = (request.form.get('source') or '').strip()
        planting_date_str = (request.form.get('planting_date') or '').strip()
        location = (request.form.get('location') or '').strip()
        image_url = (request.form.get('image_url') or '').strip()
        notes = (request.form.get('notes') or '').strip()

        if not plant_name or not category:
            flash('Please provide at least the plant name and category.', 'error')
            return redirect(url_for('logbook_new'))

        planting_date = None
        if planting_date_str:
            try:
                planting_date = datetime.strptime(planting_date_str, '%Y-%m-%d').date()
            except Exception:
                flash('Invalid planting date format. Use YYYY-MM-DD.', 'error')
                return redirect(url_for('logbook_new'))

        gp = GardenPlant(
            plant_name=plant_name,
            category=category,
            nickname=nickname or None,
            scientific_name=scientific_name or None,
            variety=variety or None,
            source=source or None,
            planting_date=planting_date,
            location=location or None,
            image_url=image_url or None,
            notes=notes or None,
        )
        db.session.add(gp)
        db.session.commit()
        flash('Plant added to your logbook!', 'success')
        return redirect(url_for('logbook_detail', plant_id=gp.id))

    return render_template('logbook_new.html')


@app.route('/logbook/<int:plant_id>')
def logbook_detail(plant_id):
    plant = GardenPlant.query.get_or_404(plant_id)

    observations = Observation.query.filter_by(plant_id=plant.id).order_by(Observation.date.desc(), Observation.created_at.desc()).all()
    care = CareEvent.query.filter_by(plant_id=plant.id).order_by(CareEvent.date.desc(), CareEvent.created_at.desc()).all()
    harvests = Harvest.query.filter_by(plant_id=plant.id).order_by(Harvest.date.desc(), Harvest.created_at.desc()).all()

    # Build unified timeline sorted by date (desc)
    timeline = []
    for o in observations:
        timeline.append({
            'kind': 'obs',
            'date': o.date or (o.created_at.date() if o.created_at else datetime.utcnow().date()),
            'obj': o,
        })
    for c in care:
        timeline.append({
            'kind': 'care',
            'date': c.date or (c.created_at.date() if c.created_at else datetime.utcnow().date()),
            'obj': c,
        })
    for h in harvests:
        timeline.append({
            'kind': 'harvest',
            'date': h.date or (h.created_at.date() if h.created_at else datetime.utcnow().date()),
            'obj': h,
        })
    timeline.sort(key=lambda x: x['date'], reverse=True)

    # Insights & schedules
    cat = (plant.category or 'other').lower()
    WATER_INTERVAL = {
        'flower': 3,
        'fruit': 2,
        'vegetable': 2,
        'herb': 2,
        'tree': 4,
        'other': 3,
    }.get(cat, 3)
    FERT_INTERVAL = {
        'flower': 14,
        'fruit': 14,
        'vegetable': 14,
        'herb': 21,
        'tree': 30,
        'other': 14,
    }.get(cat, 14)

    def _latest_date(events, predicate=lambda e: True):
        dts = [e.date for e in events if e.date and predicate(e)]
        return max(dts) if dts else None

    last_water = _latest_date(care, lambda e: (e.type or '').lower() == 'watering')
    last_fert = _latest_date(care, lambda e: (e.type or '').lower() == 'fertilizing')
    next_water = (last_water + timedelta(days=WATER_INTERVAL)) if last_water else (datetime.utcnow().date() if plant.planting_date is None else plant.planting_date + timedelta(days=WATER_INTERVAL))
    next_fert = (last_fert + timedelta(days=FERT_INTERVAL)) if last_fert else (datetime.utcnow().date() if plant.planting_date is None else plant.planting_date + timedelta(days=FERT_INTERVAL))

    first_flower = None
    first_fruit = None
    if observations:
        for o in sorted(observations, key=lambda x: (x.date or datetime.utcnow().date())):
            if first_flower is None and o.flowers and o.flowers > 0:
                first_flower = o.date
            if first_fruit is None and o.fruits and o.fruits > 0:
                first_fruit = o.date
            if first_flower and first_fruit:
                break

    first_harvest = _latest_date(harvests, lambda h: True)
    if harvests:
        first_harvest = min([h.date for h in harvests if h.date]) if any(h.date for h in harvests) else None

    days_since_planting = (datetime.utcnow().date() - plant.planting_date).days if plant.planting_date else None
    days_since_water = (datetime.utcnow().date() - last_water).days if last_water else None
    days_since_fert = (datetime.utcnow().date() - last_fert).days if last_fert else None

    # Growth series for chart
    series = []
    for o in sorted(observations, key=lambda x: (x.date or datetime.utcnow().date())):
        if o.height_cm is not None and o.date is not None:
            series.append({'d': o.date.isoformat(), 'h': o.height_cm})

    # Harvest totals per unit
    harvest_totals = {}
    for h in harvests:
        if h.quantity is not None and h.unit:
            harvest_totals[h.unit] = harvest_totals.get(h.unit, 0.0) + float(h.quantity)

    # Companion planting suggestions (simple mapping)
    companions = {
        'tomato': {
            'good': ['Basil', 'Marigold', 'Chives', 'Carrot'],
            'avoid': ['Fennel', 'Cabbage'],
        },
        'cucumber': {
            'good': ['Dill', 'Nasturtium', 'Radish'],
            'avoid': ['Potato', 'Sage'],
        },
        'pepper': {
            'good': ['Basil', 'Onion', 'Spinach'],
            'avoid': ['Fennel'],
        },
    }
    pn = (plant.plant_name or '').strip().lower()
    comp = companions.get(pn, None)

    # Suggested actions
    suggestions = []
    if days_since_water is None or days_since_water >= WATER_INTERVAL:
        suggestions.append({'kind': 'water', 'title': 'Water today', 'severity': 'high'})
    elif days_since_water is not None and days_since_water >= max(0, WATER_INTERVAL - 1):
        suggestions.append({'kind': 'water', 'title': 'Water soon', 'severity': 'medium'})

    if days_since_fert is None or days_since_fert >= FERT_INTERVAL:
        suggestions.append({'kind': 'fertilize', 'title': 'Fertilize this week', 'severity': 'medium'})

    recent_pest = None
    for o in observations:
        if o.date and (datetime.utcnow().date() - o.date).days <= 7 and (o.pests or o.diseases):
            recent_pest = True
            break
    if recent_pest:
        recent_treat = _latest_date(care, lambda e: (e.type or '').lower() in ['spray', 'treatment'])
        if not recent_treat or (datetime.utcnow().date() - recent_treat).days > 7:
            suggestions.append({'kind': 'pest', 'title': 'Inspect for pests/disease', 'severity': 'high'})

    insights = {
        'first_flower': first_flower,
        'first_fruit': first_fruit,
        'first_harvest': first_harvest,
        'days_since_planting': days_since_planting,
        'last_water': last_water,
        'next_water': next_water,
        'last_fert': last_fert,
        'next_fert': next_fert,
        'water_interval_days': WATER_INTERVAL,
        'fert_interval_days': FERT_INTERVAL,
    }

    return render_template(
        'logbook_detail.html',
        plant=plant,
        observations=observations,
        care=care,
        harvests=harvests,
        timeline=timeline,
        series=series,
        harvest_totals=harvest_totals,
        suggestions=suggestions,
        companions=comp,
        insights=insights,
    )


@app.route('/logbook/<int:plant_id>/add-observation', methods=['POST'])
def add_observation(plant_id):
    plant = GardenPlant.query.get_or_404(plant_id)
    date_str = (request.form.get('date') or '').strip()
    height_cm = request.form.get('height_cm')
    leaves = request.form.get('leaves')
    flowers = request.form.get('flowers')
    fruits = request.form.get('fruits')
    pests = (request.form.get('pests') or '').strip() or None
    diseases = (request.form.get('diseases') or '').strip() or None
    photo_url = (request.form.get('photo_url') or '').strip() or None
    notes = (request.form.get('notes') or '').strip() or None

    date = None
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            flash('Invalid date format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('logbook_detail', plant_id=plant.id))

    obs = Observation(
        plant_id=plant.id,
        date=date or datetime.utcnow().date(),
        height_cm=float(height_cm) if height_cm else None,
        leaves=int(leaves) if leaves else None,
        flowers=int(flowers) if flowers else None,
        fruits=int(fruits) if fruits else None,
        pests=pests,
        diseases=diseases,
        photo_url=photo_url,
        notes=notes,
    )
    db.session.add(obs)
    db.session.commit()
    flash('Observation added.', 'success')
    return redirect(url_for('logbook_detail', plant_id=plant.id))


@app.route('/logbook/<int:plant_id>/add-care', methods=['POST'])
def add_care(plant_id):
    plant = GardenPlant.query.get_or_404(plant_id)
    date_str = (request.form.get('date') or '').strip()
    type_ = (request.form.get('type') or '').strip()
    amount = (request.form.get('amount') or '').strip() or None
    notes = (request.form.get('notes') or '').strip() or None

    if not type_:
        flash('Please choose a care type.', 'error')
        return redirect(url_for('logbook_detail', plant_id=plant.id))

    date = None
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            flash('Invalid date format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('logbook_detail', plant_id=plant.id))

    ce = CareEvent(
        plant_id=plant.id,
        date=date or datetime.utcnow().date(),
        type=type_,
        amount=amount,
        notes=notes,
    )
    db.session.add(ce)
    db.session.commit()
    flash('Care event logged.', 'success')
    return redirect(url_for('logbook_detail', plant_id=plant.id))


@app.route('/logbook/<int:plant_id>/add-harvest', methods=['POST'])
def add_harvest(plant_id):
    plant = GardenPlant.query.get_or_404(plant_id)
    date_str = (request.form.get('date') or '').strip()
    quantity = request.form.get('quantity')
    unit = (request.form.get('unit') or '').strip()
    quality = (request.form.get('quality') or '').strip() or None
    notes = (request.form.get('notes') or '').strip() or None
    photo_url = (request.form.get('photo_url') or '').strip() or None

    if not quantity or not unit:
        flash('Please provide harvest quantity and unit.', 'error')
        return redirect(url_for('logbook_detail', plant_id=plant.id))

    date = None
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            flash('Invalid date format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('logbook_detail', plant_id=plant.id))

    hv = Harvest(
        plant_id=plant.id,
        date=date or datetime.utcnow().date(),
        quantity=float(quantity),
        unit=unit,
        quality=quality,
        notes=notes,
        photo_url=photo_url,
    )
    db.session.add(hv)
    db.session.commit()
    flash('Harvest recorded.', 'success')
    return redirect(url_for('logbook_detail', plant_id=plant.id))


@app.route('/logbook/<int:plant_id>/quick/water', methods=['POST'])
def quick_water(plant_id):
    plant = GardenPlant.query.get_or_404(plant_id)
    amount = (request.form.get('amount') or '').strip() or '500ml'
    ce = CareEvent(plant_id=plant.id, date=datetime.utcnow().date(), type='watering', amount=amount, notes='Quick action')
    db.session.add(ce)
    db.session.commit()
    flash('Watered successfully.', 'success')
    return redirect(url_for('logbook_detail', plant_id=plant.id))


@app.route('/logbook/<int:plant_id>/quick/fertilize', methods=['POST'])
def quick_fertilize(plant_id):
    plant = GardenPlant.query.get_or_404(plant_id)
    amount = (request.form.get('amount') or '').strip() or 'NPK 10-10-10 5g'
    ce = CareEvent(plant_id=plant.id, date=datetime.utcnow().date(), type='fertilizing', amount=amount, notes='Quick action')
    db.session.add(ce)
    db.session.commit()
    flash('Fertilizing logged.', 'success')
    return redirect(url_for('logbook_detail', plant_id=plant.id))


@app.route('/logbook/quick/water', methods=['POST'])
def quick_water_bulk():
    ids_str = (request.form.get('plant_ids') or '').strip()
    amount = (request.form.get('amount') or '').strip() or '500ml'
    if not ids_str:
        flash('No plants selected for watering.', 'error')
        return redirect(url_for('logbook'))
    ids = []
    for tok in ids_str.split(','):
        tok = tok.strip()
        if tok.isdigit():
            ids.append(int(tok))
    plants = GardenPlant.query.filter(GardenPlant.id.in_(ids)).all()
    for p in plants:
        db.session.add(CareEvent(plant_id=p.id, date=datetime.utcnow().date(), type='watering', amount=amount, notes='Bulk quick action'))
    db.session.commit()
    flash(f'Watered {len(plants)} plant(s).', 'success')
    return redirect(url_for('logbook'))


@app.route('/logbook/quick/fertilize', methods=['POST'])
def quick_fertilize_bulk():
    ids_str = (request.form.get('plant_ids') or '').strip()
    amount = (request.form.get('amount') or '').strip() or 'NPK 10-10-10 5g'
    if not ids_str:
        flash('No plants selected for fertilizing.', 'error')
        return redirect(url_for('logbook'))
    ids = []
    for tok in ids_str.split(','):
        tok = tok.strip()
        if tok.isdigit():
            ids.append(int(tok))
    plants = GardenPlant.query.filter(GardenPlant.id.in_(ids)).all()
    for p in plants:
        db.session.add(CareEvent(plant_id=p.id, date=datetime.utcnow().date(), type='fertilizing', amount=amount, notes='Bulk quick action'))
    db.session.commit()
    flash(f'Fertilized {len(plants)} plant(s).', 'success')
    return redirect(url_for('logbook'))


@app.route('/logbook/<int:plant_id>/export.csv')
def export_log_csv(plant_id):
    plant = GardenPlant.query.get_or_404(plant_id)
    observations = Observation.query.filter_by(plant_id=plant.id).all()
    care = CareEvent.query.filter_by(plant_id=plant.id).all()
    harvests = Harvest.query.filter_by(plant_id=plant.id).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['type', 'date', 'notes', 'height_cm', 'leaves', 'flowers', 'fruits', 'pests', 'diseases', 'care_type', 'care_amount', 'harvest_quantity', 'harvest_unit', 'harvest_quality'])
    for o in observations:
        writer.writerow(['observation', o.date, (o.notes or ''), o.height_cm, o.leaves, o.flowers, o.fruits, (o.pests or ''), (o.diseases or ''), '', '', '', '', ''])
    for ce in care:
        writer.writerow(['care', ce.date, (ce.notes or ''), '', '', '', '', '', '', (ce.type or ''), (ce.amount or ''), '', '', ''])
    for h in harvests:
        writer.writerow(['harvest', h.date, (h.notes or ''), '', '', '', '', '', '', '', '', h.quantity, (h.unit or ''), (h.quality or '')])

    csv_data = output.getvalue()
    return app.response_class(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=plant_{plant.id}_log.csv'}
    )

if __name__ == '__main__':
    app.run(debug=True)
