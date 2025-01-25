from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

# Inicjalizacja aplikacji Flask
def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///casino.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'supersecretkey'
    return app

app = create_app()
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Modele
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    birth_date = db.Column(db.Date, nullable=False)
    role = db.Column(db.String(10), default='user')  # user or admin

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # deposit, win, loss
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Funkcja walidująca pełnoletność
def is_adult(birth_date):
    today = datetime.utcnow()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age >= 18

# Trasy
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']
        birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d')

        if not is_adult(birth_date):
            flash('Musisz mieć ukończone 18 lat, aby założyć konto.', 'danger')
            return redirect(url_for('register'))

        # Haszowanie hasła przed zapisaniem w bazie
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=hashed_password,  # Zapisujemy hasło haszowane
            birth_date=birth_date
        )
        db.session.add(user)
        db.session.commit()
        flash('Rejestracja zakończona sukcesem! Możesz się teraz zalogować.', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        # Sprawdzanie, czy użytkownik istnieje i porównanie hasła
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Zalogowano pomyślnie!', 'success')
            return redirect(url_for('casino'))

        flash('Niepoprawny login lub hasło!', 'danger')
    return render_template('login.html')


@app.route('/casino')
def casino():
    if 'user_id' not in session:
        flash('Musisz się zalogować, aby uzyskać dostęp do kasyna.', 'danger')
        return redirect(url_for('login'))

    # Pobranie użytkownika z bazy danych
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        flash('Nie znaleziono użytkownika.', 'danger')
        return redirect(url_for('logout'))

    # Przekazanie balansu do szablonu
    return render_template('casino.html', balance=user.balance)


@app.route('/account')
def account():
    if 'user_id' not in session:
        flash('Musisz się zalogować, aby uzyskać dostęp do swojego konta.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        flash('Nie znaleziono użytkownika.', 'danger')
        return redirect(url_for('logout'))

    return render_template('account.html', user=user)


@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user_id' not in session:
        flash('Musisz się zalogować, aby wpłacić pieniądze.', 'danger')
        return redirect(url_for('login'))

    amount = request.form.get('amount', type=float)
    if amount <= 0:
        flash('Nieprawidłowa kwota.', 'danger')
        return redirect(url_for('account'))

    user_id = session['user_id']
    user = User.query.get(user_id)
    if user:
        user.balance += amount
        db.session.commit()
        flash(f'Wpłacono {amount:.2f} PLN!', 'success')
    else:
        flash('Błąd podczas wpłacania środków.', 'danger')

    return redirect(url_for('account'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        flash('Musisz się zalogować, aby zmienić hasło.', 'danger')
        return redirect(url_for('login'))

    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')

    user_id = session['user_id']
    user = User.query.get(user_id)

    # Porównanie starego hasła z haszem w bazie danych
    if not user or not bcrypt.check_password_hash(user.password, old_password):
        flash('Stare hasło jest nieprawidłowe.', 'danger')
        return redirect(url_for('account'))

    # Haszowanie nowego hasła przed zapisaniem go w bazie
    hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.password = hashed_new_password
    db.session.commit()
    flash('Hasło zostało zmienione.', 'success')
    return redirect(url_for('account'))


@app.route('/logout')
def logout():
    session.clear()  # Usuwa wszystkie dane sesji
    flash('Zostałeś wylogowany.', 'success')
    return redirect(url_for('home'))  # Przekierowanie na stronę główną lub stronę logowania

@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Brak dostępu!', 'danger')
        return redirect(url_for('home'))

    # Tutaj możesz dodać logikę, którą chcesz, żeby była widoczna w panelu admina
    return render_template('admin_panel.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Brak dostępu!', 'danger')
        return redirect(url_for('home'))

    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/change_role/<int:user_id>', methods=['POST'])
def change_role(user_id):
    user = User.query.get(user_id)
    if user:
        user.role = request.form['role']
        db.session.commit()
        flash('Rola użytkownika została zmieniona.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/change_balance/<int:user_id>', methods=['POST'])
def change_balance(user_id):
    user = User.query.get(user_id)
    if user:
        user.balance = request.form['balance']
        db.session.commit()
        flash('Bilans użytkownika został zmieniony.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/change_password_user/<int:user_id>', methods=['POST'])
def change_password_user(user_id):
    user = User.query.get(user_id)
    if user:
        hashed_password = bcrypt.generate_password_hash(request.form['new_password']).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Hasło użytkownika zostało zmienione.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin_users')
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin_stats')
def admin_stats():
    # Tutaj musisz dodać logikę do generowania statystyk kasyna
    # Może to być ogólna suma wygranych, przegranych itp.
    return render_template('admin_stats.html')


# Obsługa bazy danych
@app.before_request
def setup_database():
    db.create_all()

    # Dodanie domyślnego admina, jeśli tabela jest pusta
    if User.query.count() == 0:
        # Tworzenie użytkownika admin
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin_user = User(
            first_name='Admin',
            last_name='Adminowski',
            username='admin',
            password=hashed_password,
            birth_date=datetime(1980, 1, 1),  # ustawienie pełnoletności
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print('Dodano domyślnego użytkownika admin')

if __name__ == '__main__':
    app.run(debug=True)
