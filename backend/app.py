from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'a_very_secret_key' # Replace with a strong secret key
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
CORS(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    cultural_context = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Recipe('{self.title}', '{self.date_posted}')"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)

    def __repr__(self):
        return f"Comment('{self.content}', '{self.date_posted}')"

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Login successful!', 'username': user.username}), 200
    return jsonify({'message': 'Login failed. Check email and password.'}), 401

@app.route('/recipes', methods=['POST'])
def create_recipe():
    data = request.get_json()
    recipe = Recipe(
        title=data['title'],
        ingredients=data['ingredients'],
        instructions=data['instructions'],
        cultural_context=data.get('cultural_context'),
        image_url=data.get('image_url'),
        user_id=data['user_id'] # In a real app, this would come from the authenticated user
    )
    db.session.add(recipe)
    db.session.commit()
    return jsonify({'message': 'Recipe created successfully!'}), 201

@app.route('/recipes', methods=['GET'])
def get_recipes():
    recipes = Recipe.query.all()
    output = []
    for recipe in recipes:
        output.append({
            'id': recipe.id,
            'title': recipe.title,
            'ingredients': recipe.ingredients,
            'instructions': recipe.instructions,
            'cultural_context': recipe.cultural_context,
            'image_url': recipe.image_url,
            'date_posted': recipe.date_posted.isoformat(),
            'user_id': recipe.user_id
        })
    return jsonify({'recipes': output}), 200

@app.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return jsonify({
        'id': recipe.id,
        'title': recipe.title,
        'ingredients': recipe.ingredients,
        'instructions': recipe.instructions,
        'cultural_context': recipe.cultural_context,
        'image_url': recipe.image_url,
        'date_posted': recipe.date_posted.isoformat(),
        'user_id': recipe.user_id
    }), 200

@app.route('/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    data = request.get_json()
    recipe.title = data.get('title', recipe.title)
    recipe.ingredients = data.get('ingredients', recipe.ingredients)
    recipe.instructions = data.get('instructions', recipe.instructions)
    recipe.cultural_context = data.get('cultural_context', recipe.cultural_context)
    recipe.image_url = data.get('image_url', recipe.image_url)
    db.session.commit()
    return jsonify({'message': 'Recipe updated successfully!'}), 200

@app.route('/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    return jsonify({'message': 'Recipe deleted successfully!'}), 200

@app.route('/recipes/<int:recipe_id>/comments', methods=['POST'])
def add_comment(recipe_id):
    data = request.get_json()
    comment = Comment(
        content=data['content'],
        user_id=data['user_id'], # From authenticated user
        recipe_id=recipe_id
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify({'message': 'Comment added successfully!'}), 201

@app.route('/recipes/<int:recipe_id>/comments', methods=['GET'])
def get_comments(recipe_id):
    comments = Comment.query.filter_by(recipe_id=recipe_id).all()
    output = []
    for comment in comments:
        output.append({
            'id': comment.id,
            'content': comment.content,
            'date_posted': comment.date_posted.isoformat(),
            'user_id': comment.user_id,
            'recipe_id': comment.recipe_id
        })
    return jsonify({'comments': output}), 200

@app.route('/recipes/<int:recipe_id>/like', methods=['POST'])
def like_recipe(recipe_id):
    # This is a simplistic implementation. In a real app, you would track which user liked which recipe.
    # For now, it just returns a success message.
    recipe = Recipe.query.get_or_404(recipe_id)
    return jsonify({'message': f'Recipe {recipe.title} liked!'}), 200


@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

