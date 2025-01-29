# aplikacja glowna
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import random


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///casino.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'supersecretkey'
    return app

app = create_app()
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    birth_date = db.Column(db.Date, nullable=False)
    role = db.Column(db.String(10), default='user')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


def is_adult(birth_date):
    today = datetime.utcnow()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age >= 18


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


        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=hashed_password,
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


    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        flash('Nie znaleziono użytkownika.', 'danger')
        return redirect(url_for('logout'))


    return render_template('casino.html', balance=user.balance)

@app.route('/dice', methods=['GET', 'POST'])
def dice():
    if 'user_id' not in session:
        flash('Musisz się zalogować, aby grać w kości.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if request.method == 'POST':
        bet_amount = int(request.form['amount'])
        range_choice = request.form['range']

        session['bet_amount'] = bet_amount

        dice_roll = random.randint(1, 6)


        if range_choice == "1-3" and dice_roll <= 3 or range_choice == "4-6" and dice_roll > 3:
            outcome_message = f"Wygrałeś {bet_amount} PLN!"
            user.balance += bet_amount
            outcome_class = 'alert-success'


            transaction = Transaction(
                user_id=user.id,
                amount=bet_amount,
                type='win'
            )
            db.session.add(transaction)
        else:
            outcome_message = f"Przegrałeś {bet_amount} PLN."
            user.balance -= bet_amount
            outcome_class = 'alert-danger'


            transaction = Transaction(
                user_id=user.id,
                amount=bet_amount,
                type='loss'
            )
            db.session.add(transaction)

        db.session.commit()
        return render_template('dice.html', dice_roll=dice_roll, outcome_message=outcome_message, outcome_class=outcome_class, balance=user.balance)


    bet_amount = session.get('bet_amount', 1)
    return render_template('dice.html', balance=user.balance, bet_amount=bet_amount)

@app.route('/roulette', methods=['GET', 'POST'])
def roulette():
    if 'user_id' not in session:
        flash('Musisz się zalogować, aby grać w ruletkę.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if request.method == 'POST':
        bet_amount = int(request.form['bet_amount'])
        bet_choice = request.form['bet_choice']

        if bet_amount > user.balance:
            flash('Nie masz wystarczających środków na ten zakład.', 'danger')
            return redirect(url_for('roulette'))

        result_number = random.randint(0, 36)
        result_color = "red" if result_number % 2 != 0 else "black"

        win = False
        payout = 0

        if bet_choice in ['red', 'black'] and bet_choice == result_color:
            win = True
            payout = bet_amount
        elif bet_choice.isdigit() and int(bet_choice) == result_number:
            win = True
            payout = bet_amount * 35

        if win:
            user.balance += payout
            flash(f'Gratulacje! Wygrałeś {payout} PLN.', 'success')


            transaction = Transaction(
                user_id=user.id,
                amount=payout,
                type='win'
            )
            db.session.add(transaction)
        else:
            user.balance -= bet_amount
            flash(f'Niestety, przegrałeś {bet_amount} PLN.', 'danger')


            transaction = Transaction(
                user_id=user.id,
                amount=bet_amount,
                type='loss'
            )
            db.session.add(transaction)

        db.session.commit()

        return render_template('roulette.html',
                               balance=user.balance,
                               bet_amount=bet_amount,
                               bet_choice=bet_choice,
                               result_number=result_number,
                               result_color=result_color,
                               win=win,
                               payout=payout)

    return render_template('roulette.html', balance=user.balance)

@app.route('/blackjack', methods=['GET', 'POST'])
def blackjack():
    if 'user_id' not in session:
        flash('Musisz się zalogować, aby grać w Blackjack.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if request.method == 'POST' and request.form.get('action') == 'reset':
        session.pop('blackjack', None)
        return redirect(url_for('blackjack'))

    if 'blackjack' not in session:
        if request.method == 'POST' and 'bet' in request.form:
            bet = float(request.form.get('bet'))

            if bet > user.balance:
                flash('Nie masz wystarczających środków na ten zakład.', 'danger')
                return redirect(url_for('blackjack'))

            session['blackjack'] = {
                'player_cards': [random.randint(1, 11), random.randint(1, 11)],
                'dealer_cards': [random.randint(1, 11), random.randint(1, 11)],
                'bet': bet,
                'game_over': False
            }
        else:
            return render_template('blackjack.html', balance=user.balance, game=None)

    game = session['blackjack']


    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'hit' and not game['game_over']:
            game['player_cards'].append(random.randint(1, 11))

            if sum(game['player_cards']) > 21:
                game['game_over'] = True
                user.balance -= game['bet']
                db.session.commit()

                transaction = Transaction(
                    user_id=user.id,
                    amount=game['bet'],
                    type='loss'
                )
                db.session.add(transaction)

                flash(f'Przegrałeś {game["bet"]} PLN. Suma kart przekroczyła 21.', 'danger')

        elif action == 'stand' and not game['game_over']:

            while sum(game['dealer_cards']) < 17:
                game['dealer_cards'].append(random.randint(1, 11))

            player_sum = sum(game['player_cards'])
            dealer_sum = sum(game['dealer_cards'])

            if dealer_sum > 21 or player_sum > dealer_sum:
                user.balance += game['bet']

                transaction = Transaction(
                    user_id=user.id,
                    amount=game['bet'],
                    type='win'
                )
                db.session.add(transaction)

                flash(f'Wygrałeś {game["bet"]} PLN!', 'success')
            elif player_sum < dealer_sum:  # Przegrana gracza
                user.balance -= game['bet']

                transaction = Transaction(
                    user_id=user.id,
                    amount=game['bet'],
                    type='loss'
                )
                db.session.add(transaction)

                flash(f'Przegrałeś {game["bet"]} PLN.', 'danger')
            else:  # Remis
                flash('Remis. Stawka zostaje zwrócona.', 'info')

            game['game_over'] = True
            db.session.commit()

        session['blackjack'] = game

    return render_template('blackjack.html', game=game, balance=user.balance)

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

@app.route("/withdraw", methods=["POST"])
def withdraw():
    if 'user_id' not in session:
        flash('Musisz się zalogować, aby wypłacić pieniądze.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        flash('Nie znaleziono użytkownika.', 'danger')
        return redirect(url_for('logout'))

    try:
        amount = float(request.form.get("withdraw_amount", 0))
        if amount > 0:
            if user.balance >= amount:
                user.balance -= amount
                db.session.commit()
                flash(f"Wypłacono {amount} PLN z Twojego konta.", "success")
            else:
                flash("Niewystarczające środki na koncie.", "danger")
        else:
            flash("Kwota musi być większa niż 0.", "danger")
    except ValueError:
        flash("Nieprawidłowa kwota.", "danger")

    return redirect(url_for("account"))

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        flash('Musisz się zalogować, aby zmienić hasło.', 'danger')
        return redirect(url_for('login'))

    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')

    user_id = session['user_id']
    user = User.query.get(user_id)


    if not user or not bcrypt.check_password_hash(user.password, old_password):
        flash('Stare hasło jest nieprawidłowe.', 'danger')
        return redirect(url_for('account'))


    hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.password = hashed_new_password
    db.session.commit()
    flash('Hasło zostało zmienione.', 'success')
    return redirect(url_for('account'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Zostałeś wylogowany.', 'success')
    return redirect(url_for('home'))

@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Brak dostępu!', 'danger')
        return redirect(url_for('home'))


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
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Brak dostępu!', 'danger')
        return redirect(url_for('home'))

    total_wins = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == 'win').scalar() or 0
    total_losses = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == 'loss').scalar() or 0
    casino_profit = total_losses - total_wins


    total_users = User.query.count()
    total_transactions = Transaction.query.count()
    average_balance = db.session.query(db.func.avg(User.balance)).scalar() or 0

    richest_user = User.query.order_by(User.balance.desc()).first()

    return render_template('admin_stats.html',
                           total_wins=total_wins,
                           total_losses=total_losses,
                           casino_profit=casino_profit,
                           total_users=total_users,
                           total_transactions=total_transactions,
                           average_balance=round(average_balance, 2),
                           richest_user=richest_user)

@app.before_request
def setup_database():
    db.create_all()


    if User.query.count() == 0:

        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin_user = User(
            first_name='Admin',
            last_name='Adminowski',
            username='admin',
            password=hashed_password,
            birth_date=datetime(1980, 1, 1),
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print('Dodano domyślnego użytkownika admin')

if __name__ == '__main__':
    app.run(debug=True)