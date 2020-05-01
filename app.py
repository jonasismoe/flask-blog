# Import Flask Stuff
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
# Articles Test Import
from data import Articles
# Flask-MySQLDB
from flask_mysqldb import MySQL
# Flask-WTF
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
# Passlib
from passlib.hash import sha256_crypt

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

Articles = Articles()

# Index
@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html', title='Home')

# Articles
@app.route('/articles')
def articles():
    return render_template('articles.html', title='Articles', articles = Articles)

# Article View
@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', title='Articles', id=id)

# About
@app.route('/about')
def about():
    return render_template('about.html', title='About')

# Register Form
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

        return redirect(url_for('index'))
    # ... else GET...
    else:
        return render_template('register.html', form=form)

# Activate Debugging Tools
if __name__ == '__main__':
    app.secret_key='secretkey123'
    app.run(debug=True)