from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import current_app as app
import sqlite3
import json

main_bp = Blueprint('main', __name__)

# Hard-coded password
VALID_USERNAME = "onetable"
VALID_PASSWORD = "flask123"

@main_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        app.logger.info("Login attempt for user: %s", username)
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            return redirect(url_for('main.questions'))
        else:
            flash("Invalid credentials. Please try again.")
            return render_template('login.html')
    return render_template('login.html')

@main_bp.route('/questions', methods=['GET', 'POST'])
def questions():
    if request.method == 'POST':
        # Collect answers from the form; using placeholders if none provided.
        answers = {
            'favorite_food': request.form.get('favorite_food', 'Placeholder answer'),
            'cuisine_preference': request.form.get('cuisine_preference', 'Placeholder answer'),
            'dietary_restrictions': request.form.get('dietary_restrictions', 'Placeholder answer')
        }
        app.logger.info("Received answers: %s", answers)
        # In a real application, you would store these in a database.
        return render_template('thankyou.html', answers=answers)
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

    return render_template('food_detail.html', food=food_data)

