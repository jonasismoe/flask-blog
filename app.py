# Import Flask Stuff
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
# Flask-MySQLDB
from flask_mysqldb import MySQL
# Flask-WTF
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
# Passlib
from passlib.hash import sha256_crypt
# Wraps
from functools import wraps

# Initialize Flask
app = Flask(__name__,
            # Template folder location
            template_folder='templates/')

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask-blog'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# Initialize MySQL
mysql = MySQL(app)

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.', 'danger')
            return redirect(url_for('login'))
    return wrap

# Check if user is not logged in
def is_not_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You can't access this area while logged in.", 'danger')
            return redirect(url_for('dashboard'))
    return wrap

# Index
@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html', title='Home')

# Articles
@app.route('/articles')
def articles():
     # Create Cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute('SELECT * FROM articles ORDER BY id DESC')

    # Fetch articles
    articles = cur.fetchall()

    # If there is an result...
    if result > 0:
        return render_template('articles.html', title='Articles', articles=articles)
    else:
        msg = 'No Articles Found!'
        return render_template('articles.html', title="Articles", msg=msg)
    
    # Close connection
    cur.close()


# Article View
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute('SELECT * from articles WHERE id = %s', [id])

    # Fetch result
    article = cur.fetchone()

    # Close cursor
    cur.close()

    return render_template('article.html', title='Articles', article=article)

# About
@app.route('/about')
def about():
    return render_template('about.html', title='About')

# Login
@app.route('/login', methods=['GET', 'POST'])
@is_not_logged_in
def login():
    # if request is POST...
    if request.method == 'POST':
        # Get Fields from Form
        username = request.form['username']
        # Saved as candidate to check with real password
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute('SELECT * FROM users WHERE username = %s', [username])
        
        # If username exists...
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # If password matches...
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in!', 'success')
                return redirect(url_for('dashboard'))
            # ... if they don't match...
            else:#
                # ... error.
                error = 'Invalid login! Check your credentials.'
                return render_template('login.html', title="Login", error=error)
            
            # Close connection
            cur.close()

        # ... if username doesn't exist...
        else:
            # .. error.
            error = 'Invalid login! Check your credentials.'
            return render_template('login.html', title="Login", error=error)

    # ... else GET...
    else:
        return render_template('login.html', title="Login")

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    # Log user out
    session.clear()
    flash('You are now logged out!', 'success')
    return redirect(url_for('index'))

# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=320)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match!')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
@is_not_logged_in
def register():
    # Register Form
    form = RegisterForm(request.form)
    # If request POST and form ist validated...
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in!', 'success')

        return redirect(url_for('login'))

    # ... else GET...
    else:
        return render_template('register.html', title="Register", form=form)

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get articles from user
    result = cur.execute('SELECT * FROM articles WHERE author = %s ORDER BY id DESC', [session['username']])

    # Fetch articles
    articles = cur.fetchall()

    # If there is an result...
    if result > 0:
        return render_template('dashboard.html', title='Dashboard', articles=articles)
    else:
        msg = 'No Articles Found!'
        return render_template('dashboard.html', title="Dashboard", msg=msg)
    
    # Close connection
    cur.close()

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=85)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add-article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    # If request is POST and form is validated...
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Query
        cur.execute('INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)', (title, body, session['username']))

        # Commit
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Article Created!', 'success')

        return redirect(url_for('dashboard'))

    # ... else GET request.
    else:
        return render_template('add-article.html', title='Add Article', form=form)



# Activate Debugging Tools
if __name__ == '__main__':
    app.secret_key='secretkey123'
    app.run(debug=True)