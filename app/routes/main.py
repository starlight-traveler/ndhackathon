from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask import current_app as app
import sqlite3
import json
from openai import OpenAI
import os
from flask import Response, stream_with_context
import re

main_bp = Blueprint('main', __name__)

# Hard-coded password
VALID_USERNAME = "onetable"
VALID_PASSWORD = "flask123"

@main_bp.route('/')
def base():
    return render_template('intro.html')
#@main_bp.route()
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        app.logger.info("Login attempt for user: %s", username)
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session['user'] = username  # Set the user session
            flash(f"Successfully logged in as {username}.")
            return redirect(url_for('main.home'))
        else:
            flash("Invalid credentials. Please try again.")
            return render_template('login.html')
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.")
    return redirect(url_for('main.login'))

@main_bp.route('/home')
def home():
    if not session.get('user'):
        flash("Please log in to access your homepage.")
        return redirect(url_for('main.login'))
    # Initialize baseline personal info if not set
    user_info = session.get('user_info', {
        'age': 30,
        'weight': 70,   # kg
        'height': 175,  # cm
        'gender': 'male'
    })
    # Initialize tracker if not set
    tracker = session.get('tracker', {
        'calories': 0,
        'total_fat': 0,
        'protein': 0,
        'cholesterol': 0,
        'carbohydrates': 0,
        'dietary_fiber': 0,
        'sodium': 0,
    })
    # Calculate daily recommended values based on personal info:
    age = user_info.get('age', 30)
    weight = user_info.get('weight', 70)
    height = user_info.get('height', 175)
    gender = user_info.get('gender', 'male')
    if gender.lower() == 'male':
        calories_rec = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        calories_rec = 10 * weight + 6.25 * height - 5 * age - 161
    protein_rec = weight * 0.8  # grams
    total_fat_rec = (calories_rec * 0.3) / 9  # grams
    # Fixed recommendations for other nutrients:
    daily_values = {
        'calories': calories_rec,
        'total_fat': total_fat_rec,
        'protein': protein_rec,
        'cholesterol': 300,       # mg
        'carbohydrates': 275,     # grams
        'dietary_fiber': 28,      # grams
        'sodium': 2300            # mg
    }
    return render_template('home.html', user_info=user_info, tracker=tracker, daily_values=daily_values)

@main_bp.route('/update_tracker', methods=['POST'])
def update_tracker():
    # Get personal data from the form
    try:
        age = int(request.form.get('age'))
        weight = float(request.form.get('weight'))
        height = float(request.form.get('height'))
    except (TypeError, ValueError):
        flash("Invalid personal information provided.")
        return redirect(url_for('main.home'))
    gender = request.form.get('gender')
    food = request.form.get('food')
    quantity = request.form.get('quantity')
    try:
        quantity = float(quantity) if quantity else 0
    except (TypeError, ValueError):
        quantity = 0

    # Update session personal info
    session['user_info'] = {
        'age': age,
        'weight': weight,
        'height': height,
        'gender': gender
    }

    # Get or initialize the tracker
    tracker = session.get('tracker', {
        'calories': 0,
        'total_fat': 0,
        'protein': 0,
        'cholesterol': 0,
        'carbohydrates': 0,
        'dietary_fiber': 0,
        'sodium': 0,
    })

    # If a food entry is provided, update tracker with baseline nutrient values
    if food and quantity > 0:
        food_lower = food.lower()
        if "chicken" in food_lower:
            # Baseline for chicken breast (per 100g)
            baseline = {
                'calories': 151,
                'protein': 30.54,
                'total_fat': 3.17,
                'cholesterol': 104,
                'carbohydrates': 0,
                'dietary_fiber': 0,
                'sodium': 52
            }
        else:
            # Default baseline values for unknown food
            baseline = {
                'calories': 200,
                'protein': 10,
                'total_fat': 5,
                'cholesterol': 0,
                'carbohydrates': 30,
                'dietary_fiber': 5,
                'sodium': 300
            }
        # Scale the nutrient values based on quantity (assuming per 100g)
        factor = quantity / 100.0
        for nutrient in baseline:
            tracker[nutrient] = tracker.get(nutrient, 0) + baseline[nutrient] * factor

    session['tracker'] = tracker
    flash("Tracker updated!")
    return redirect(url_for('main.home'))

@main_bp.route('/order', methods=['GET','POST'])
# request syntax for html forms and sqlite queries helped with AI
def order():
    if not session.get('user'):
        flash("Log in to make request")
        return redirect(url_for('main.login'))
    
    
    # Collect answers from the form; using placeholders if none provided.
    if request.method == 'POST':
        answers = {
            'user':session.get('user'),
            'children': request.form.get('children'),
            'adults': request.form.get('adults'),
            'diet_restrictions': request.form.get('dietary_restrictions'),
            'address': request.form.get('address'),
        }
        app.logger.info("Received answers: %s", answers)
        # connect to orders db
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (username, children, adults, address, restrictions)
            VALUES (?, ?, ?, ?, ?)
            ''', (answers.get('user'), 
                   int(answers.get('children')), 
                   int(answers.get('adults')), 
                   answers.get('diet_restrictions'), 
                   answers.get('address')
            ))
        conn.commit()
        conn.close()
        app.logger.info("Added %s to orders.db", answers)
        return render_template('questions.html')

    return render_template('questions.html')

@main_bp.route('/indexer', methods=['GET', 'POST'])
def indexer():
    results = []
    query = ''
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        app.logger.info("Indexer search query: %s", query)
        if query:
            conn = sqlite3.connect('food.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description FROM food WHERE name LIKE ?", ('%' + query + '%',))
            results = cursor.fetchall()
            conn.close()
            if not results:
                flash("No results found.")
        else:
            flash("Please enter a search term.")
    return render_template('indexer.html', results=results, query=query)

# Helper function to retrieve quick nutritional facts
def get_food_facts(food_id):
    conn = sqlite3.connect('food.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nutrition_100g FROM food WHERE id=?", (food_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        nutrition = json.loads(row[0])
        return {
            'calories': nutrition.get('calories', 'N/A'),
            'protein': nutrition.get('protein', 'N/A'),
            'total_fat': nutrition.get('total_fat', 'N/A')
        }
    return None

# Make the helper function available in all templates
@main_bp.app_context_processor
def utility_processor():
    return dict(get_food_facts=get_food_facts)

@main_bp.route('/food/<food_id>')
def food_detail(food_id):
    conn = sqlite3.connect('food.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM food WHERE id=?", (food_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        flash("Food item not found.")
        return redirect(url_for('main.indexer'))

    keys = ["id","name","alternate_names","description","type","source","serving",
            "nutrition_100g","ean_13","labels","package_size","ingredients","ingredient_analysis"]
    food_data = dict(zip(keys, row))
    food_data['nutrition_100g'] = json.loads(food_data['nutrition_100g']) if food_data['nutrition_100g'] else {}
    food_data['source'] = json.loads(food_data['source']) if food_data['source'] else []

    daily_values = {
    'calories': 2500,
    'total_fat': 70,          # grams
    'protein': 56,            # grams
    'cholesterol': 300,       # mg
    'carbohydrates': 275,     # grams
    'dietary_fiber': 28,      # grams
    'sodium': 2300            # mg
}

    return render_template('food_detail.html', food=food_data, daily_values=daily_values)

client = OpenAI()

@main_bp.route('/foody-ai', methods=['GET', 'POST'])
def foody_ai():
    if request.method == 'POST':
        prompt = request.form.get('prompt', '').strip()

        # Regex to check if the prompt is food based
        if not re.search(r'\b(food|chicken|pizza|burger|taco|pasta|recipe|cook|ingredient|restaurant)\b', prompt, re.IGNORECASE):
            return Response("data: Please ask a food-based query.\n\n", mimetype='text/event-stream')

        def generate_response():
            stream = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a foody ai assistant, you give food based advice, respond in the negative if anything is not food based."},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield f"data: {chunk.choices[0].delta.content}\n\n"

        return Response(stream_with_context(generate_response()), mimetype='text/event-stream')

    return render_template('foody_ai.html')

@main_bp.route('/foody-ai-stream')
def foody_ai_stream():
    prompt = request.args.get('prompt', '').strip()

    # Regex to check if the prompt is food based
    if not re.search(r'\b(food|chicken|pizza|burger|taco|pasta|recipe|cook|ingredient|restaurant|chicken)\b', prompt, re.IGNORECASE):
        return Response("data: Please ask a food-based query.\n\n", mimetype='text/event-stream')

    def stream():
        response_stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a foody ai assistant, you give food based advice"},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        for chunk in response_stream:
            if chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\n\n"
    return Response(stream_with_context(stream()), mimetype='text/event-stream')

@main_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # Placeholder for saving settings.
        flash("Settings saved (not really, this is just a placeholder).")
        return redirect(url_for('main.settings'))
    return render_template('settings.html')
