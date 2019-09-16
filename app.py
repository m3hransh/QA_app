from flask import Flask, render_template, g, request, session, url_for, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from databse import get_db, connect_db
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']
        db = get_db()
        cur = db.execute('select * from users where name=?', [user])
        user_result = cur.fetchone()
    
    return user_result


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def index():
    user = get_current_user()
    
    return render_template('home.html', user=user)

@app.route('/login', methods=['Get', 'Post'])
def login():
    user = get_current_user()

    if request.method == 'POST':
        db = get_db()
        name = request.form['name']
        password = request.form['password']

        cur = db.execute('select id, name, password from users where name=?', [name])
        usr_result = cur.fetchone()
        if check_password_hash(usr_result['password'], password):
            session['user'] = usr_result['name']
            return  redirect(url_for('index'))
        else:
            return '<h1>your password is incorrect</h1>'

    return render_template('login.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()

    if request.method == 'POST':
        hash_pass = generate_password_hash( request.form['password'], method='sha256')
        db = get_db()
        db.execute('insert into users (name, password, expert, admin) values(?, ?, ?, ?)', [request.form['name'], hash_pass, '0', '0'])
        db.commit()
        return redirect(url_for('index'))
    return render_template('register.html', user=user)

@app.route('/ask')
def ask():
    user = get_current_user()

    return render_template('ask.html', user=user)

@app.route('/answer')
def answer():
    user = get_current_user()

    return render_template('answer.html', user=user)

@app.route('/question')
def question():
    user = get_current_user()

    return render_template('question.html', user=user)

@app.route('/unanswered')
def unanswered():
    user = get_current_user()

    return render_template('unanswered.html', user=user)

@app.route('/users')
def users():
    db = get_db()
    users_cur = db.execute('select id, name, expert from users ')
    users_result = users_cur.fetchall()
    user = get_current_user()

    return render_template('users.html', user=user, users_result = users_result)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/promote/<user_id>')
def promote(user_id):
    db = get_db()
    db.execute('update users set expert=1 where id=?',[user_id])
    db.commit()
    return redirect(url_for('users'))

if __name__=='__main__':
    app.run(debug=True)