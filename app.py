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
    db = get_db()
    question_cur = db.execute('''select questions.id as question_id, questions.question_text, asker.name as asker_name, expert.name as expert_name
                                 from questions join users as asker on questions.asked_by_id = asker.id
                                  join users as expert on questions.expert_id = expert.id 
                                  where questions.answer_text is not null ''') 
    question_result = question_cur.fetchall()
    return render_template('home.html', user=user, questions=question_result)

@app.route('/login', methods=['Get', 'Post'])
def login():
    user = get_current_user()

    error = None

    if request.method == 'POST':
        db = get_db()
        name = request.form['name']
        password = request.form['password']

        cur = db.execute('select id, name, password from users where name=?', [name])
        usr_result = cur.fetchone()
        if usr_result :
            
            if check_password_hash(usr_result['password'], password):
                session['user'] = usr_result['name']
                return  redirect(url_for('index'))
            else:
                error =  'your password is incorrect.'
        else:
            error = 'your username is incorrect.'

    return render_template('login.html', user=user, error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()

    if request.method == 'POST':
        db = get_db()

        existing_user_cur = db.execute('select name from users where name = ?', [request.form['name']])
        existing_user = existing_user_cur.fetchone()

        if existing_user:
            return render_template('register.html', user=user, error="The user name is already used.")

        hash_pass = generate_password_hash( request.form['password'], method='sha256')
        db.execute('insert into users (name, password, expert, admin) values(?, ?, ?, ?)', [request.form['name'], hash_pass, '0', '0'])
        db.commit()
        return redirect(url_for('index'))
    return render_template('register.html', user=user)

@app.route('/ask', methods=['POST', 'GET'])
def ask():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    db = get_db()

    if request.method =='POST':
        db.execute('insert into questions (question_text, asked_by_id, expert_id) values(?, ?, ?)',\
                     [request.form['question'], user['id'], request.form['expert']])
        db.commit()

        return redirect(url_for('index'))
    
    exper_cur = db.execute('select id, name from users where expert = 1')
    expert_result = exper_cur.fetchall()
    return render_template('ask.html', user=user, experts=expert_result)

@app.route('/answer/<question_id>', methods=['POST', 'GET'])
def answer(question_id):
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    if user['expert'] == 0 :
        return redirect(url_for('index'))

    db = get_db()

    if request.method == 'POST':
        db.execute('update questions set answer_text=? where id = ?', [request.form['answer'], question_id])
        db.commit()
        return redirect(url_for('unanswered'))
    question_cur = db.execute('select id, question_text from questions where id = ? ', [question_id])
    question_result = question_cur.fetchone()
    return render_template('answer.html', user=user, question=question_result)

@app.route('/question/<question_id>')
def question(question_id):
    user = get_current_user()
    db = get_db()

    question_cur = db.execute('''select questions.answer_text, questions.question_text, questions.answer_text,
                                asker.name as asker_name, expert.name as expert_name
                                from questions join users as asker on questions.asked_by_id = asker.id
                                join users as expert on questions.expert_id = expert.id 
                                where questions.id = ?''', [question_id])
    question_result = question_cur.fetchone()
    
    return render_template('question.html', user=user, question=question_result)

@app.route('/unanswered')
def unanswered():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    if user['expert'] == 0 :
        return redirect(url_for('index'))

    db = get_db()
    question_cur = db.execute('''select users.name, questions.id, questions.question_text, questions.asked_by_id 
                                 from questions join users on users.id = questions.asked_by_id
                                 where answer_text is null and expert_id = ?''', [user['id']])
    question_result = question_cur.fetchall()

    return render_template('unanswered.html', user=user, questions=question_result )

@app.route('/users')
def users():
    user = get_current_user()
    
    if not user:
        return redirect(url_for('login'))

    if user['admin'] == 0 :
        return redirect(url_for('index'))
        
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
    user = get_current_user()
    
    if not user:
        return redirect(url_for('login'))

    if user['admin'] == 0 :
        return redirect(url_for('index'))

    db = get_db()
    db.execute('update users set expert=1 where id=?',[user_id])
    db.commit()
    return redirect(url_for('users'))

if __name__=='__main__':
    app.run(debug=True)