from flask import Flask, render_template, g, request, session, url_for, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, connect_db
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']
        db = get_db()
        db.execute('select * from users where name=%s', (user, ))
        user_result = db.fetchone()
    
    return user_result


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'postgres_db_cursor'):
        g.postgres_db_cursor.close()

    if hasattr(g, 'postgres_db_conn') :
        g.postgres_db_conn.close()

@app.route('/')
def index():
    user = get_current_user()
    db = get_db()
    db.execute('''select 
                                    questions.id as question_id, 
                                    questions.question_text, 
                                    asker.name as asker_name, 
                                    expert.name as expert_name
                                 from questions 
                                 join users as asker on questions.asked_by_id = asker.id
                                 join users as expert on questions.expert_id = expert.id 
                                 where questions.answer_text is not null ''') 
    question_result = db.fetchall()
    return render_template('home.html', user=user, questions=question_result)

@app.route('/login', methods=['Get', 'Post'])
def login():
    user = get_current_user()

    error = None

    if request.method == 'POST':
        db = get_db()
        name = request.form['name']
        password = request.form['password']

        db.execute('select id, name, password from users where name=%s', (name, ))
        usr_result = db.fetchone()
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

        db.execute('select name from users where name = %s', (request.form['name'], ))
        existing_user = db.fetchone()

        if existing_user:
            return render_template('register.html', user=user, error="The user name is already used.")

        hash_pass = generate_password_hash( request.form['password'], method='sha256')
        db.execute('insert into users (name, password, expert, admin) values(%s, %s, %s, %s)', (request.form['name'], hash_pass, '0', '0'))
        return redirect(url_for('index'))
    return render_template('register.html', user=user)

@app.route('/ask', methods=['POST', 'GET'])
def ask():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    db = get_db()

    if request.method =='POST':
        db.execute('insert into questions (question_text, asked_by_id, expert_id) values(%s, %s, %s)',\
                     (request.form['question'], user['id'], request.form['expert']))

        return redirect(url_for('index'))
    
    db.execute('select id, name from users where expert = True')
    expert_result = db.fetchall()
    return render_template('ask.html', user=user, experts=expert_result)

@app.route('/answer/<question_id>', methods=['POST', 'GET'])
def answer(question_id):
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    if not user['expert']:
        return redirect(url_for('index'))

    db = get_db()

    if request.method == 'POST':
        db.execute('update questions set answer_text=%s where id = %s',( request.form['answer'], question_id))
        return redirect(url_for('unanswered'))
    db.execute('select id, question_text from questions where id = %s ', (question_id, ))
    question_result = db.fetchone()
    return render_template('answer.html', user=user, question=question_result)

@app.route('/question/<question_id>')
def question(question_id):
    user = get_current_user()
    db = get_db()

    db.execute('''select questions.answer_text, questions.question_text, questions.answer_text,
                                 asker.name as asker_name, 
                                 expert.name as expert_name
                                 from questions 
                                 join users as asker on questions.asked_by_id = asker.id
                                 join users as expert on questions.expert_id = expert.id 
                                 where questions.id = %s''', (question_id, ))
    question_result = db.fetchone()
    
    return render_template('question.html', user=user, question=question_result)

@app.route('/unanswered')
def unanswered():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    if not user['expert'] :
        return redirect(url_for('index'))

    db = get_db()
    db.execute('''select users.name, questions.id, questions.question_text, questions.asked_by_id 
                                 from questions join users on users.id = questions.asked_by_id
                                 where answer_text is null and expert_id = %s''', (user['id'], ) )
    question_result = db.fetchall()

    return render_template('unanswered.html', user=user, questions=question_result )

@app.route('/users')
def users():
    user = get_current_user()
    
    if not user:
        return redirect(url_for('login'))

    if not user['admin'] :
        return redirect(url_for('index'))
        
    db = get_db()
    db.execute('select id, name, expert from users ')
    users_result = db.fetchall()
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

    if not user['admin'] :
        return redirect(url_for('index'))

    db = get_db()
    db.execute('update users set expert= True where id=%s',(user_id, ))
    return redirect(url_for('users'))

if __name__=='__main__':
    app.run(debug=True)