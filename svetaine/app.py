from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, PasswordField, DateField, FileField, IntegerField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import secrets, os

# Sukuriama aplikacijos konfigūracija
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(25)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.static_folder = 'static'
app.config['TEMPLATES_AUTO_RELOAD'] = True
Bootstrap(app)

# Sukuriamas ryšys su duomenų baze
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Prisijungimo sesijų valdymas
user_login = LoginManager()
user_login.init_app(app)
user_login.login_view = 'login'

# /////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------
#                                              FORMŲ KLASĖS
# -----------------------------------------------------------------------------------------------------
# -- Prisijungimo forma
class LoginForm(FlaskForm):
    email = StringField('El. paštas', validators=[InputRequired(), Length(max=50)])
    password = PasswordField('Slaptažodis', validators=[InputRequired(), Length(max=50)])
# -----------------------------------------------------------------------------------------------------
# -- Duomenų keitimo forma
class ChangeData(FlaskForm):
    email = StringField('El. pašto adresas', validators=[Email(message='Neteisingas el. pašto adresas'), Length(max=50)])
    phone = StringField('Telefono numeris', validators=[Length(min=5)])
# -----------------------------------------------------------------------------------------------------
# -- Nuotraukos keitimo forma
class ChangeImage(FlaskForm):
    image = FileField(u'Nuotrauka')
# -----------------------------------------------------------------------------------------------------
# -- Slaptažodžio keitimo forma
class ChangePass(FlaskForm):
    password = PasswordField('Senas slaptažodis', validators=[Length(min=8, max=50)])
    new_password = PasswordField('Naujas slaptažodis', validators=[Length(min=8, max=50)])
    repeat_password = PasswordField('Pakartokite naują slaptažodį', validators=[Length(min=8, max=50)])
# -----------------------------------------------------------------------------------------------------
# -- Registracijos forma
class RegistrationForm(FlaskForm):
    first_name = StringField('Vardas', validators=[InputRequired(), Length(min=3, max=50)])
    last_name = StringField('Pavardė', validators=[InputRequired(), Length(min=3, max=20)])
    personal_code = StringField('Asmens kodas', validators=[InputRequired(), Length(min=11, max=11)])
    email = StringField('El. pašto adresas', validators=[InputRequired(), Email(message='Neteisingas el. pašto adresas'), Length(max=50)])
    phone = StringField('Telefono numeris', validators=[InputRequired(), Length(min=5)])
    password = PasswordField('Slaptažodis', validators=[InputRequired(), Length(min=8, max=50)])
# -----------------------------------------------------------------------------------------------------
# -- Susitikimo prisijungimo forma
class JoinMeet(FlaskForm):
    patient_id = StringField('Paciento ID', validators=[InputRequired()])
# -----------------------------------------------------------------------------------------------------
# /////////////////////////////////////////////////////////////////////////////////////////////////////
# Vartotojų sesijų paleidimas
@user_login.user_loader
def load_user(user_id):
    return User.query.get(user_id)
# -----------------------------------------------------------------------------------------------------
#                                               KLASĖS
# -----------------------------------------------------------------------------------------------------
# -- Naudotojo duomenų klasė
class User(db.Model, UserMixin):
    unique_id = db.Column(db.String(20), primary_key = True, unique = True)
    first_name = db.Column(db.String(20))
    last_name = db.Column(db.String(20))
    personal_code = db.Column(db.String(11))
    birthday = db.Column(db.String(10))
    email = db.Column(db.String(50))
    phone = db.Column(db.String(15))
    position = db.Column(db.String(50))
    working_hours = db.Column(db.String(300))
    password = db.Column(db.String(50))
    image_url = db.Column(db.String(100))

    def get_id(self):
        return (self.unique_id)
    
# -----------------------------------------------------------------------------------------------------
# -- Vizitų duomenų klasė
class Visits(db.Model):
    __tablename__ = 'user_visits'
    visit_id = db.Column(db.Integer, primary_key = True, unique = True)
    user_unique_id = db.Column(db.String(20))
    doctor_unique_id = db.Column(db.String(20))
    time = db.Column(db.String(16))
    url_link = db.Column(db.String(100), unique = True)

    def set_visits(self, user):
        return db.query().filter_by(user_unique_id = user.get_id()).all()

# -----------------------------------------------------------------------------------------------------
# -- Vizitų duomenų klasė
class PatientsHistory(db.Model):
    __tablename__ = 'patients_history'
    id = db.Column(db.Integer, primary_key = True, unique = True)
    date = db.Column(db.String(16))
    user_unique_id = db.Column(db.String(20))
    prescription = db.Column(db.String(50))
    comments = db.Column(db.String(100))
    diagnose = db.Column(db.String(30))
# /////////////////////////////////////////////////////////////////////////////////////////////////////
#papildomi metodai duomenims gauti
def getPatientsHistoryList():
    return PatientsHistory.query.filter_by(user_unique_id = current_user.unique_id).all()


# /////////////////////////////////////////////////////////////////////////////////////////////////////
@app.route("/")
def home():
    return render_template('index.html')

@app.route("/informacija")
def info():
    return render_template('info.html')

@app.route("/kontaktai")
def contacts():
    return render_template('contacts.html')

@app.route("/prisijungimas", methods=['GET', 'POST'])
def login():
    form=LoginForm()
    if(current_user.is_authenticated):
        return redirect(url_for('account'))
    else:
        if request.method == 'POST' and form.validate_on_submit():
            user = User.query.filter_by(email = form.email.data).first()
            # Checking if user exists
            if user:
                # Checking if the password is correct
                if check_password_hash(user.password, form.password.data):
                    login_user(user)
                    return redirect(url_for('account'))
                else:
                    message = 'Neteisingas slaptažodis.'
                    msg_color = 'darkred'
                    return render_template('login.html', form = form, message = message, msg_color = msg_color)
            else:
                message = 'Paskyra nerasta.'
                msg_color = 'darkred'
                return render_template('login.html', form = form, message = message, msg_color = msg_color)

    return render_template('login.html', form = form)

@app.route("/registracija", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST' and form.validate_on_submit():
        # Creating unique_id
        uid = secrets.token_hex(20)
        # Encypting the password
        passhash = generate_password_hash(form.password.data, method='sha256')
        new_user = User(unique_id = uid,
                        first_name = form.first_name.data,
                        last_name = form.last_name.data,
                        personal_code = form.personal_code.data,
                        phone = form.phone.data,
                        email = form.email.data,
                        position = 'Pacientas',
                        image_url = 'default.png',
                        password = passhash)
        email_exists = User.query.filter_by(email = form.email.data).first()
        # Checking if the email is already used
        if email_exists:
            msg_color = 'darkred'
            message = 'El. pašto adresas užimtas.'
            return render_template('register.html', form = form, message = message, msg_color = msg_color)
        # Adding a new user to the database
        else:
            db.session.add(new_user)
            db.session.commit()
            message = "Registracija sėkminga. Galite prisijungti."
            msg_color = 'lightgreen'
            return render_template('login.html', form = LoginForm(), message = message, msg_color = msg_color)
    else:
        return render_template('register.html', form = form)

@login_required
@app.route("/atsijungti")
def logout():
    logout_user()
    form = LoginForm()
    message = 'Sėkmingai atsijungta.'
    msg_color = 'lightgreen'
    return render_template('login.html', form = form, message = message, msg_color = msg_color)



@login_required
@app.route("/paskyra", methods=['GET','POST'])
def account():
    # Kintamieji
    user = User.query.filter_by(unique_id = current_user.unique_id).first()
    vizitas = Visits.query.filter_by(user_unique_id = current_user.unique_id).first()
    changepass = ChangePass()
    changedata = ChangeData()
    changeimage = ChangeImage()
    message = ''
    msg_color = 'white'

    # Tikrinama naudotojo rolė
    if user.position == 'Pacientas':
        load = 'account_patient.html'
    elif user.position == 'Administratorius':
        load = 'account_admin.html'
    else:
        load = 'account_doctor.html'

    # Asmeninių duomenų keitimo forma
    if request.method == 'POST' and changedata.validate_on_submit():
        user.email = changedata.email.data
        user.phone = changedata.phone.data
        db.session.commit()
        msg_color = 'lightgreen'
        message = 'Duomenys atnaujinti.'
        return render_template(load, user = current_user, changepass = changepass, changedata = changedata, changeimage = changeimage, message = message, msg_color = msg_color)

    # Nuotraukos keitimo forma
    if request.method == 'POST' and changeimage.validate_on_submit() and user.position != 'Pacientas' and user.position != 'Administratorius':
        file = changeimage.image.data
        if file:
            file_name = file.filename
            print(file_name)
            if file_name.endswith('.png'):
                file.save(os.path.join(app.root_path, 'static/user_images/' + user.unique_id + '.png'))
                user.image_url = user.unique_id + '.png'
                db.session.commit()
                message = 'Nuotrauka atnaujinta.'
                msg_color = 'lightgreen'
                return render_template(load, user = current_user, changepass = changepass, changedata = changedata, changeimage = changeimage, message = message, msg_color = msg_color)
            else:
                message = 'Netinkamas nuotraukos formatas (ne .png).'
                msg_color = 'lightgreen'
                return render_template(load, user = current_user, changepass = changepass, changedata = changedata, changeimage = changeimage, message = message, msg_color = msg_color)
        else:
            message = 'Neįkeltas nuotraukos failas.'
            msg_color = 'darkred'
            return render_template(load, user = current_user, changepass = changepass, changedata = changedata, changeimage = changeimage, message = message, msg_color = msg_color)

    # Slaptažodžio keitimo forma
    if request.method == 'POST' and changepass.validate_on_submit():
        if check_password_hash(current_user.password, changepass.password.data):

            if changepass.new_password.data == changepass.repeat_password.data:

                passhash = generate_password_hash(changepass.new_password.data, method='sha256')
                user.password = passhash
                db.session.commit()
                msg_color = 'lightgreen'
                message = 'Slaptažodis pakeistas.'
                return render_template(load, user = current_user, changepass = changepass, changedata = changedata, changeimage = changeimage, message = message, msg_color = msg_color)
            else:
                msg_color = 'darkred'
                message = 'Naujas slaptažodis nesutampa.'
                return render_template(load, user = current_user, changepass = changepass, changedata = changedata, changeimage = changeimage, message = message, msg_color = msg_color)
        else:
            msg_color = 'darkred'
            message = 'Senas slaptažodis įvestas neteisingai.'
            return render_template(load, user = current_user, changepass = changepass, changedata = changedata, changeimage = changeimage, message = message, msg_color = msg_color)
    return render_template(load, user = current_user, changepass = changepass, changedata = changedata, changeimage = changeimage)

@login_required
@app.route('/ligu-istorija')
def patient_history():
    return render_template('patient_history.html', user = current_user, visits = getPatientsHistoryList(), len = len(getPatientsHistoryList()))

@app.route('/e-susitikimas', methods=['GET', 'POST'])
def meet():
    form = JoinMeet()
    message = ''
    msg_color = ''
    if request.method == 'POST' and form.validate_on_submit():
        if form.patient_id.data:
            return redirect('https://meet.ktuligonine.lt/' + form.patient_id.data)
        else:
            message = 'Įveskite paciento ID'
            msg_color = 'darkred'
            return render_template('meet.html', user = current_user, form = form, message = message, msg_color = msg_color)
    else:
        return render_template('meet.html', user = current_user, form = form, message = message, msg_color = msg_color)

if __name__ == "__main__":
    app.run(debug = True)