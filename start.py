from flask import Flask , request , render_template , session , redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug import secure_filename
from flask_mail import Mail
import json
import math
import os

print("hiii")
with open('config.json' , 'r') as c:
    params = json.load(c)["params"]
local_server = True

app = Flask(__name__)

app.secret_key = 'super-secret-key'
app.config['uploader'] = params['uploader_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT =   '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-pass']
)
mail = Mail(app)
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)

class Contacts(db.Model):
    srno    = db.Column(db.Integer , primary_key = True)
    name    = db.Column(db.String(20) , nullable = False)
    email   = db.Column(db.String(20) ,  nullable = False)
    phno    = db.Column(db.String(15) , nullable =False)
    msg     = db.Column(db.String(100) , nullable = False)
    date    = db.Column(db.String(20) , nullable = True)

class Posts(db.Model):
    srno        = db.Column(db.Integer , primary_key = True)
    title       = db.Column(db.String(30) , nullable = False)
    content     = db.Column(db.String(150) , nullable = False)
    slugs       = db.Column(db.String(20) , nullable = False)
    date        = db.Column(db.String(15) , nullable = True)
    img_file    = db.Column(db.String(20) , nullable = False)
    tagline     = db.Column(db.String(50) , nullable = False)




@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['number_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['number_posts']) :  ((page-1)*int(params['number_posts']))+int(params['number_posts'])]

    if page == 1:
        prev="#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page-1)
        next = "#"
    else:
        prev = "/?page="+str(page-1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params , posts = posts , prev=prev , next=next)

@app.route("/dashboard" , methods=['GET','POST'])
def dashboard():

    if ('user' in session and session['user'] == params['admin_name']):
        posts = Posts.query.filter_by().all()
        return render_template('dashboard.html', params=params , posts = posts)


    if request.method == 'POST':
        username = request.form.get('email')
        password = request.form.get('pass')
        if (username == params['admin_name'] and password == params['admin_password']):
            session['user'] = username
            posts = Posts.query.filter_by().all()
            return render_template('dashboard.html', params=params , posts = posts)


    return render_template('login.html', params=params)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/contact" , methods = ['GET', 'POST'])
def contact():
    if request.method == 'POST':
    #     add entry to database...
        name = request.form.get('name')
        email = request.form.get('email')
        phno = request.form.get('phno')
        msg = request.form.get('msg')

        entry = Contacts(name=name , email=email , phno=phno , msg=msg , date = datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('this is blog message from '+ name ,
                          sender = email ,
                          recipients = [params['gmail-user']],
                          body = msg + '\n' + phno
                          )

    return render_template('contact.html', params=params)

@app.route("/post/<string:slug>" , methods=['GET'])
def post(slug):
    post = Posts.query.filter_by(slugs = slug).first()

    return render_template('post.html', params=params ,post = post)


@app.route("/post" , methods=['GET'])
def sample_post(slug=params['sample_post']):
    post = Posts.query.filter_by(slugs = slug).first()

    return render_template('post.html', params=params ,post = post)


@app.route("/edit/<string:srno>" , methods=['GET','POST'])
def edit(srno):
    if ('user' in session and session['user'] == params['admin_name']):
        if (request.method == 'POST'):
            title = request.form.get('title')
            tagline = request.form.get('tagline')
            content = request.form.get('content')
            slug = request.form.get('slug')
            img_file = request.form.get('img_file')
            date = datetime.now()



            if (srno == '0'):
                post = Posts(title = title , slugs = slug , content=content , img_file=img_file , tagline=tagline , date = date)
                db.session.add(post)
                db.session.commit()


            else:
                post = Posts.query.filter_by(srno = srno).first()
                post.title = title
                post.tagline = tagline
                post.content = content
                post.slugs = slug
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+srno)
        post = Posts.query.filter_by(srno = srno).first()
        return render_template('edit.html' , params=params , post = post , srno = srno)

@app.route("/uploader" , methods = ["GET" , "POST"])
def uploader():
    if ('user' in session and session['user'] == params['admin_name']):
        if request.method == 'POST':
            f = request.files['uploaded_file']
            f.save(os.path.join(app.config['uploader'] , secure_filename(f.filename) ))
            return("Uploaded Successfully")

@app.route("/delete/<string:srno>" , methods=['GET','POST'])
def delete(srno):
    if ('user' in session and session['user'] == params['admin_name']):
        post = Posts.query.filter_by(srno=srno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')



@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

app.run(debug=True)
