import math
import os
from flask import Flask, render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
import datetime
from werkzeug.utils import secure_filename
from flask_mail import Mail
import json
import pymysql
pymysql.install_as_MySQLdb()

local_server = True
with open('config.json','r') as c:
    params = json.load(c)["params"]


app = Flask(__name__)
app.secret_key='mysecretkey'

app.config['UPLOAD_FOLDER']=params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['mail_user'],
    MAIL_PASSWORD = params['mail_password']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(20), nullable=False)
    msg = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(25), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    subtitle = db.Column(db.String(50),nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(25), nullable=False)
    date = db.Column(db.String(10),nullable=True)

app.debug = True

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    # [0:params['posts_num']]

    page = request.args.get('page')
    last = math.ceil(len(posts)/params['posts_num'])


    if(not str(page).isnumeric()):
        page=1
    page = int(page)
    posts = posts[(page - 1) * params['posts_num']:(page - 1) * params['posts_num'] + params['posts_num']]
    if(page==1):
        prev = "#"
        next = "/?page="+str(page+1)
    elif(page==last):
        next = "#"
        prev = "/?page=" + str(page - 1)
    else:
        next = "/?page=" + str(page + 1)
        prev = "/?page=" + str(page - 1)


    return render_template('index.html', params = params, posts = posts, prev = prev,next=next)

@app.route("/upload",methods=['GET','POST'])
def upload():
    if 'user' in session and session['user']==params['admin-email']:
        if request.method == 'POST':
            f = request.files['inp_file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully"

# @app.route("/older-posts")
# def olderposts():
#     posts = Posts.query.filter_by().all()
#     return render_template('index.html', params = params, posts = posts)
# @app.route("/edit/")
# def success():
#     posts = Posts.query.filter_by().all()
#     return render_template('dashboard.html', params = params, posts = posts)

@app.route("/edit/<string:sno>",methods=['GET','POST'])
def edit(sno):
    if('user' in session and session['user']==params['admin-email']):
        if request.method=='POST':
            new_title = request.form.get('title')
            new_subtitle = request.form.get('subtitle')
            new_slug = request.form.get('slug')
            new_author = request.form.get('author')
            new_content = request.form.get('content')
            date = datetime.datetime.now()

            if sno == '0':
                posts = Posts(title = new_title,subtitle=new_subtitle,slug=new_slug,author=new_author,content=new_content,date=date)
                db.session.add(posts)
                db.session.commit()
                return redirect('/edit/' + str(posts.sno))
            else:
                posts = Posts.query.filter_by(sno=sno).first()
                posts.title = new_title
                posts.subtitle=new_subtitle
                posts.slug = new_slug
                posts.author = new_author
                posts.content = new_content
                db.session.commit()
                return redirect('/edit/'+sno)

        if sno == '0':
            posts = Posts(sno=0, title='',subtitle='', slug='', author='', content='',date = '')
        else:
            posts = Posts.query.filter_by(sno=sno).first()

        return render_template('edit.html', params=params,posts=posts)

@app.route("/delete/<string:sno>",methods=['GET','POST'])
def delete(sno):
    if 'user' in session and session['user']==params['admin-email']:
        posts = Posts.query.filter_by(sno=sno).first()
        db.session.delete(posts)
        db.session.commit()
    return redirect('/dashboard')


@app.route("/about")
def about():
    return render_template('about.html',params = params)

@app.route("/dashboard", methods = ['GET','POST'])
def dashboard():

    if 'user' in session and session['user']== params['admin-email']:
        posts = Posts.query.all()

        return render_template('dashboard.html', params=params, posts=posts);

    if(request.method=='POST'):
        username = request.form.get('uname')
        password = request.form.get('password')
        if (username == params['admin-email']) and (password == params['admin-password']):
            session['user']=username;
            posts = Posts.query.all()

            return render_template('dashboard.html', params=params, posts=posts)

    return render_template('login.html',params = params)

@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_fun(post_slug):

    post = Posts.query.filter_by(slug=post_slug).first()

    return render_template('post.html',params = params,post = post)

@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user',None)
        return redirect('/dashboard')


@app.route("/post")
def post_f():

    post = Posts.query.filter_by().first()

    return render_template('post.html',params = params,post=post)


@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name, phone_num = phone, msg = message,email = email )
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from '+ email,
                          sender=email,
                          recipients = [params['mail_user']],
                          body = message + "\n" + phone
                          )

    return render_template('contact.html',params = params)

app.run()