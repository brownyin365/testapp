from requests import session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import sqlite3
from datetime import datetime

# Database setup
def setup_database():
    conn = sqlite3.connect('attendance.db', check_same_thread=False)
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                country TEXT NOT NULL,
                referral_id INTEGER,
                FOREIGN KEY (referral_id) REFERENCES Users(id)
            )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Users(id)
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                FOREIGN KEY (referrer_id) REFERENCES Users(id),
                FOREIGN KEY (referred_id) REFERENCES Users(id)
            );''')

    c.execute('''CREATE TABLE IF NOT EXISTS Ranks (
                    user_id INTEGER PRIMARY KEY, 
                    rank TEXT, 
                    signins INTEGER,
                    global_signins INTEGER DEFAULT 0,
                    global_rank TEXT,
                    bonus_claimed BOOLEAN DEFAULT 0,
                    bonus_amount REAL DEFAULT 0)''')        

    c.execute('''CREATE TABLE IF NOT EXISTS Tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                country TEXT NOT NULL,
                url TEXT,
                completed BOOLEAN DEFAULT 0
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS GlobalTasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                url TEXT,
                completed BOOLEAN DEFAULT 0
            )''')

    c.execute('''CREATE TABLE IF NOT EXISTS UserTasks (
                user_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                globalTask_id INTEGER NOT NULL,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES Users(id),
                FOREIGN KEY (task_id) REFERENCES Tasks(id),
                FOREIGN KEY (globalTask_id) REFERENCES GlobalTasks(id),
                PRIMARY KEY (user_id, task_id, globalTask_id)
            )''')     
    
    conn.commit()
    return conn, c

conn, c = setup_database()

# Menu Builder
# Menu Builder
class MenuBuilder:
    @staticmethod
    def main_menu(user_id):
        signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
        referral_button = InlineKeyboardButton("📨 Get Referral Link", callback_data='referral')
        view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
        # Construct the deep link for the Mini App
        deep_link = f"user_details/{user_id}"
        
        # Use the proper URL scheme for the Telegram Mini App
        dashboard_button = {
                    "text": "📊 View Dashboard",
                    "web_app": {
                        "url": f"https://9218-154-160-14-56.ngrok-free.app/{deep_link}"
                    }
                }

        
        keyboard = [
            [signin_button, referral_button, view_task_button, dashboard_button]
        ]
        
        return InlineKeyboardMarkup(keyboard)

# class MenuBuilder:
#     @staticmethod
#     def main_menu(user_id):
#         signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
#         referral_button = InlineKeyboardButton("📨 Get Referral Link", callback_data='referral')
#         view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
#         # Construct the deep link for the Mini App
#         deep_link = f"user_detail_{user_id}"
        
#         # Use tg://resolve scheme for Telegram deep link
#         dashboard_button = InlineKeyboardButton(
#             "📊 View Dashboard",
#             url=f"https://8b1a-154-161-39-89.ngrok-free.app=beibayeebot&start={deep_link}"
#         )
        
#         keyboard = [
#             [signin_button, referral_button, view_task_button, dashboard_button]
#         ]
        
#         return InlineKeyboardMarkup(keyboard)


# class MenuBuilder:
#     @staticmethod
#     def main_menu(user_id):
#         signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
#         referral_button = InlineKeyboardButton("📨 Get Referral Link", callback_data='referral')
#         view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
#         # Telegram deep link to the mini app
#         # dashboard_url = f"https://8b1a-154-161-39-89.ngrok-free.app=beibayeebot&start=user_detail_{user_id}"
#         dashboard_url = f"https://8b1a-154-161-39-89.ngrok-free.app/user_details/{user_id}"

        
#         dashboard_button = InlineKeyboardButton("📊 View Dashboard", url=dashboard_url)
        
#         keyboard = [
#             [signin_button, referral_button, view_task_button, dashboard_button]
#         ]
        
#         return InlineKeyboardMarkup(keyboard)

# class MenuBuilder:
#     @staticmethod
#     def main_menu(user_id):
#         signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
#         referral_button = InlineKeyboardButton("📨 Get Referral Link", callback_data='referral')
#         view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
#         # Generate the URL for the user's dashboard
#         dashboard_url = f"https://8b1a-154-161-39-89.ngrok-free.app/user_details/{user_id}"
        
#         # Create a button that links to the dashboard URL
#         dashboard_button = InlineKeyboardButton("📊 View Dashboard", url=dashboard_url)
        
#         # Add the buttons to the keyboard layout
#         keyboard = [
#             [signin_button, referral_button, view_task_button, dashboard_button]
#         ]
        
#         return InlineKeyboardMarkup(keyboard)
# class MenuBuilder:
#     @staticmethod
#     def main_menu(user_id):
#         signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
#         referral_button = InlineKeyboardButton("📨 Get Referral Link", callback_data='referral')
#         view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
#         # Add dashboard button
#         dashboard_url = f"https://8b1a-154-161-39-89.ngrok-free.app/user_details/{user_id}"
#         dashboard_button = InlineKeyboardButton("📊 View Dashboard", url=dashboard_url)
        
#         keyboard = [
#             [signin_button, referral_button, view_task_button, dashboard_button]  # All buttons in one row
#         ]
        
#         return InlineKeyboardMarkup(keyboard)

# Task Handler
async def assign_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    # Fetch the user's country
    c.execute("SELECT country FROM Users WHERE id = ?", (user_id,))
    user_country = c.fetchone()[0]

    # Fetch available tasks for the user's country
    try:
        c.execute('''
            SELECT task_id FROM UserTasks 
            JOIN Tasks ON UserTasks.task_id = Tasks.id 
            WHERE user_id = ? AND UserTasks.completed = 0
        ''', (user_id,))
        task = c.fetchone()
        
        if not task:
            c.execute('''
                SELECT id, task, url FROM Tasks 
                WHERE completed = 0 AND country = ? 
                LIMIT 1
            ''', (user_country,))
            new_task = c.fetchone()
            
            if new_task:
                task_id, task_text, task_url = new_task
                c.execute('''
                    INSERT INTO UserTasks (user_id, task_id, globalTask_id) 
                    VALUES (?, ?, NULL)
                ''', (user_id, task_id))
                conn.commit()
                await update.message.reply_text(f"Task assigned: {task_text}")
            else:
                await update.message.reply_text("No tasks are currently available.")
        else:
            await update.message.reply_text("You already have an active task.")
    except sqlite3.OperationalError as e:
        await update.message.reply_text(f"Database error: {e}")
    finally:
        conn.close()

async def view_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    if query:
        await query.answer()
        
        user = query.from_user
        user_id = user.id
        
        with sqlite3.connect('attendance.db') as conn:
            c = conn.cursor()
            try:
                c.execute("SELECT Tasks.id, Tasks.task, Tasks.url FROM Tasks JOIN UserTasks ON Tasks.id = UserTasks.task_id WHERE UserTasks.user_id = ? AND UserTasks.completed = 0", (user_id,))
                tasks = c.fetchall()
                
                if tasks:
                    keyboard = []
                    for task_id, task_text, task_url in tasks:
                        task_button = InlineKeyboardButton(f"{task_text}", url=task_url)
                        complete_button = InlineKeyboardButton("Mark as Completed", callback_data=f'complete_task_{task_id}')
                        keyboard.append([task_button, complete_button])
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text("Here are your active tasks:", reply_markup=reply_markup)
                else:
                    await query.edit_message_text("You have no active tasks.")
            except sqlite3.OperationalError as e:
                await query.edit_message_text(f"Database error: {e}")
    else:
        await update.message.reply_text("Error: No callback query found. Please try again.")

async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    task_id = int(query.data.split('_')[-1])
    
    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        try:
            c.execute("UPDATE UserTasks SET completed = 1 WHERE user_id = ? AND task_id = ?", (user_id, task_id))
            conn.commit()
            
            c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
            conn.commit()
            
            await query.edit_message_text("Task completed! Your progress has been recorded.")
        except sqlite3.OperationalError as e:
            await query.edit_message_text(f"Database error: {e}")

# Registration form for country selection
async def registration_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    countries = ["Country1", "Country2"]  # Replace with actual country list
    buttons = [InlineKeyboardButton(country, callback_data=f"select_country_{country}") for country in countries]
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]  # Arrange buttons in rows of 2
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Please select your country:", reply_markup=reply_markup)

# Handle country selection
async def select_country_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    selected_country = query.data.split('_')[-1]  # Extract the selected country from callback data
    
    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        try:
            # Update the user's country
            c.execute("UPDATE Users SET country = ? WHERE id = ?", (selected_country, user_id))
            
            # Award the user with 5 additional sign-ins
            c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
            
            conn.commit()
            await query.edit_message_text(f"Country updated to: {selected_country}. You have been awarded 5 sign-ins. You can now proceed to the main menu with /menu.")
        except sqlite3.OperationalError as e:
            await query.edit_message_text(f"Database error: {e}")

# Update the start command to include registration form

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    
    # Construct the deep link URL for your Mini App
    deep_link = f"user_detail_{user_id}"
    
    # Send a message with a button that opens the Mini App page
    keyboard = [
        [InlineKeyboardButton("📊 View Your Dashboard", url=f"https://t.me/m2e2bot?start={deep_link}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Click below to view your dashboard:", reply_markup=reply_markup)


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
#     username = user.username
#     args = context.args

#     if args and args[0].startswith('dashboard_'):
#         # Handle dashboard deep link
#         dashboard_user_id = args[0].split('_')[-1]
#         await dashboard_callback(update, context)
#         return
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("INSERT OR IGNORE INTO Users (id, username, country) VALUES (?, ?, '')", (user_id, username))
#             c.execute("INSERT OR IGNORE INTO Ranks (user_id, rank, signins) VALUES (?, ?, ?)", (user_id, 'Unranked', 0))
#             conn.commit()
            
#             await update.message.reply_text(
#                 f"Hello {username}! Welcome to the bot. Please complete your registration by selecting your country."
#             )
            
#             await registration_form(update, context)
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
#     username = user.username
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             # Insert user into the Users table if not already present
#             c.execute("INSERT OR IGNORE INTO Users (id, username, country) VALUES (?, ?, '')", (user_id, username))
#             c.execute("INSERT OR IGNORE INTO Ranks (user_id, rank, signins) VALUES (?, ?, ?)", (user_id, 'Unranked', 0))
#             conn.commit()
            
#             await update.message.reply_text(
#                 f"Hello {username}! Welcome to the bot. Please complete your registration by selecting your country."
#             )
            
#             # Instead of sending the URL, directly show the registration form
#             await registration_form(update, context)
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
#     username = user.username
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             # Insert user into the Users table if not already present
#             c.execute("INSERT OR IGNORE INTO Users (id, username, country) VALUES (?, ?, '')", (user_id, username))
#             c.execute("INSERT OR IGNORE INTO Ranks (user_id, rank, signins) VALUES (?, ?, ?)", (user_id, 'Unranked', 0))
#             conn.commit()
            
#             await update.message.reply_text(
#                 f"Hello {username}! Welcome to the bot. Please complete your registration by selecting your country."
#             )
            
#             user_details_url = f"https://8b1a-154-161-39-89.ngrok-free.app/user_details/{user_id}"
#             await update.message.reply_text(
#                 f"You can view your details here: {user_details_url}"
#             )
            
#             await registration_form(update, context)
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

async def signin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M:%S')
    
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    try:
        # Check if the user has already signed in today
        c.execute("SELECT id FROM Attendance WHERE user_id = ? AND date = ?", (user_id, date))
        existing_entry = c.fetchone()
        
        if existing_entry:
            await query.edit_message_text("You have already signed in today.")
        else:
            # Insert sign-in record
            c.execute("INSERT INTO Attendance (user_id, date, time) VALUES (?, ?, ?)", (user_id, date, time))
            conn.commit()
            
            # Update rank or other relevant data
            c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            
            await query.edit_message_text("Sign-in successful! Your progress has been recorded.")
    except sqlite3.OperationalError as e:
        await query.edit_message_text(f"Database error: {e}")
    finally:
        conn.close()

async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    referral_link = f"https://t.me/m2e3bot_bot/register/{user_id}"
    
    await query.edit_message_text(f"Your referral link: {referral_link}")

# Main menu command
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id

    # Build the main menu with the user's ID
    reply_markup = MenuBuilder.main_menu(user_id)
    
    # Send the menu to the user
    await update.message.reply_text("Main Menu", reply_markup=reply_markup)

# async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id

#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         c.execute("SELECT country FROM Users WHERE id = ?", (user_id,))
#         user_country = c.fetchone()[0]

#         if not user_country:
#             await registration_form(update, context)
#         else:
#             reply_markup = MenuBuilder.main_menu(user_id)
#             await update.message.reply_text("Main Menu", reply_markup=reply_markup)

# async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
    
#     # Construct the URL for the user's dashboard
#     dashboard_url = f"https://8b1a-154-161-39-89.ngrok-free.app/user_details/{user_id}"
    
#     # Send the dashboard URL to the user
#     await query.edit_message_text(f"View your dashboard here: {dashboard_url}")




async def send_dashboard_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    
    # Construct the deep link URL for your Mini App
    deep_link = f"user_detail_{user_id}"
    
    # Send a message with a button that opens the Mini App page
    keyboard = [
        [InlineKeyboardButton("📊 View Your Dashboard", url=f"https://t.me/m2e2bot?start={deep_link}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Click below to view your dashboard:", reply_markup=reply_markup)

# This function sends the dashboard link when the user interacts with the bot, without using a callback query


# async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
    
#     # Construct the deep link URL for your Mini App
#     deep_link = f"user_detail_{user_id}"
    
#     # Send a message with a button that opens the Mini App page
#     keyboard = [
#         [InlineKeyboardButton("📊 View Your Dashboard", url=f"tg://resolve?https://8b1a-154-161-39-89.ngrok-free.app=beibayeebot&start={deep_link}")]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await query.edit_message_text("Click below to view your dashboard:", reply_markup=reply_markup)


# Command handlers setup
def main():
    application = Application.builder().token("7308553019:AAHKVgixYmGnXPkq4mQpcK9bUmwkH604BP8").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CallbackQueryHandler(signin_callback, pattern="signin"))
    application.add_handler(CallbackQueryHandler(referral_callback, pattern="referral"))
    application.add_handler(CallbackQueryHandler(view_task_callback, pattern="view_task"))
    application.add_handler(CallbackQueryHandler(complete_task_callback, pattern="complete_task_"))
    application.add_handler(CallbackQueryHandler(select_country_callback, pattern="select_country_"))
    # application.add_handler(CallbackQueryHandler(dashboard_callback, pattern="dashboard"))
    
    application.run_polling()

if __name__ == "__main__":
    main()










from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, timedelta
from flask.json import jsonify



app = Flask(__name__)
app.secret_key = '136bbad7ffbcea6d3b679dbaefc108aeab09f3f7c9c6d332'


def calculate_rank(signins):
    """Calculate the rank of a user based on the number of sign-ins."""
    RANKS = {
        'Member': 1,
        'Bonk': 120,
        'Dorm': 200,
        'Area': 250,
        'City': 320,
        'State': 400,
        'Zonal': 500,
        'National': 600,
        'Regional': 700,
        'Global': 1000,
        'Universal': 1500
    }
    for rank, threshold in sorted(RANKS.items(), key=lambda x: x[1], reverse=True):
        if signins >= threshold:
            return rank
    return 'Unranked'

# Database connection
def get_db_connection():
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_current_user_id():
    """Retrieve the current user's ID from the session."""
    return session.get('user_id')


# @app.route('/')
# def index():
#     """Main index route that redirects to the user's details page."""
#     user_id = session.get('user_id')
#     if user_id:
#         return redirect(url_for('user_detail', user_id=user_id))
#     else:
#         return "User not found", 404

@app.route('/')
def index():
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, country FROM Users').fetchall()
    conn.close()
    return render_template('index.html', users=users)


@app.route('/user_details/<int:user_id>')
def user_detail(user_id):
    """Display the user details, their rank, tasks, and the remaining time for sign-in if applicable."""
    conn = get_db_connection()
    
    # Fetch user details
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
    if user is None:
        conn.close()
        return "User not found", 404
    
    # Fetch user rank
    rank = conn.execute('SELECT * FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()
    referral_link = f"https://yourdomain.com/register/{user_id}"
    
    # Calculate remaining time for sign-in
    last_signin = conn.execute(
        "SELECT date, time FROM Attendance WHERE user_id = ? ORDER BY date DESC, time DESC LIMIT 1", 
        (user_id,)
    ).fetchone()

    if last_signin:
        last_signin_time = datetime.strptime(f"{last_signin['date']} {last_signin['time']}", "%Y-%m-%d %H:%M:%S")
        time_diff = datetime.now() - last_signin_time
        if time_diff < timedelta(hours=12):
            remaining_time = timedelta(hours=12) - time_diff
            remaining_time_str = str(remaining_time).split('.')[0]  # Format the remaining time as "H:MM:SS"
        else:
            remaining_time_str = None
    else:
        remaining_time_str = None
    
    # Fetch the user's tasks
    tasks = conn.execute('''
        SELECT task, url FROM Tasks
        JOIN UserTasks ON Tasks.id = UserTasks.task_id
        WHERE UserTasks.user_id = ? AND UserTasks.completed = 0
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    return render_template('user_detail.html', user=user, rank=rank, tasks=tasks, remaining_time=remaining_time_str, referral_link=referral_link,)


# User details page
# @app.route('/user_details/<int:user_id>')
# def user_detail(user_id):
#     conn = get_db_connection()
#     user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
#     rank = conn.execute('SELECT * FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()
#     tasks = conn.execute('''
#         SELECT task, url FROM Tasks
#         JOIN UserTasks ON Tasks.id = UserTasks.task_id
#         WHERE UserTasks.user_id = ? AND UserTasks.completed = 0
#     ''', (user_id,)).fetchall()
    
#     conn.close()
    
#     if user is None:
#         return "User not found", 404
    
#     return render_template('user_detail.html', user=user, rank=rank, tasks=tasks)




@app.route('/update_country/<int:user_id>', methods=['GET', 'POST'])
def update_country(user_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        new_country = request.form['country']
        
        # Update the user's country
        conn.execute('UPDATE Users SET country = ? WHERE id = ?', (new_country, user_id))
        
        # Increment the user's sign-ins by 5
        conn.execute('UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('user_detail', user_id=user_id))
    
    # Fetch current country for display and any other needed information
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user is None:
        return "User not found", 404

    countries = ["USA", "Canada", "UK", "Germany", "France", "India"]  # Add more as needed
    return render_template('update_country.html', user_id=user_id, user=user, countries=countries, current_country=user['country'])


# @app.route('/update_country/<int:user_id>', methods=['GET', 'POST'])
# def update_country(user_id):
#     conn = get_db_connection()
    
#     if request.method == 'POST':
#         new_country = request.form['country']
#         conn.execute('UPDATE Users SET country = ? WHERE id = ?', (new_country, user_id))
#         conn.commit()
#         conn.close()
#         return redirect(url_for('user_detail', user_id=user_id))
    
#     # Fetch current country for display and any other needed information
#     user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
#     conn.close()
    
#     if user is None:
#         return "User not found", 404

#     countries = ["USA", "Canada", "UK", "Germany", "France", "India"]  # Add more as needed
#     return render_template('update_country.html', user_id=user_id, countries=countries, current_country=user['country'])



# -----------------------
# Routes: Task Management
# -----------------------

@app.route('/assign_task/<int:user_id>', methods=['POST'])
def assign_task(user_id):
    """Assign a new task to the user based on their country if they do not have an active task."""
    with get_db_connection() as conn:
        # Fetch the user's country
        user_country = conn.execute("SELECT country FROM Users WHERE id = ?", (user_id,)).fetchone()['country']

        # Check for existing tasks for this user
        task = conn.execute("SELECT task_id FROM UserTasks WHERE user_id = ?", (user_id,)).fetchone()

        if not task:
            # Fetch available tasks for the user's country
            new_task = conn.execute('''
                SELECT id, task, url FROM Tasks 
                WHERE completed = 0 AND country = ? 
                LIMIT 1
            ''', (user_country,)).fetchone()
            
            if new_task:
                task_id, task_text, task_url = new_task
                conn.execute('''
                    INSERT INTO UserTasks (user_id, task_id) 
                    VALUES (?, ?)
                ''', (user_id, task_id))
                conn.commit()
                return jsonify({"message": f"Task assigned: {task_text}", "task_url": task_url})
            else:
                return jsonify({"message": "No tasks are currently available for your country."}), 404
        else:
            return jsonify({"message": "You already have an active task."}), 400


@app.route('/user/<int:user_id>/tasks')
def user_tasks(user_id):
    """Display all available tasks for the user based on their country."""
    with get_db_connection() as conn:
        # Fetch user information
        user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return "User not found.", 404

        user_country = user['country']
        
        # Fetch country-specific tasks
        tasks = conn.execute('SELECT * FROM Tasks WHERE completed = 0 AND country = ?', (user_country,)).fetchall()
        
        # Fetch global tasks
        global_tasks = conn.execute('SELECT * FROM GlobalTasks WHERE completed = 0').fetchall()
        
        # Fetch user rank and sign-ins
        rank = conn.execute('SELECT rank, signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()

    return render_template('tasks.html', user=user, tasks=tasks, rank=rank, global_tasks=global_tasks)


@app.route('/user/<int:user_id>/task/<int:task_id>/complete', methods=['POST'])
def complete_task(user_id, task_id):
    """Mark a task as completed and update the user's rank."""
    with get_db_connection() as conn:
        conn.execute("UPDATE Tasks SET completed = 1 WHERE id = ?", (task_id,))
        conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        
        # Update the user's sign-ins by 5
        conn.execute("UPDATE Ranks SET signins = signins + 2 WHERE user_id = ?", (user_id,))
        signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
        rank = calculate_rank(signins)
        conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

        conn.commit()

    return redirect(url_for('user_tasks', user_id=user_id))


@app.route('/user/<int:user_id>/globalTask/<int:globalTask_id>/complete', methods=['POST'])
def complete_global_task(user_id, globalTask_id):
    """Mark a task as completed and update the user's rank."""
    with get_db_connection() as conn:
        conn.execute("UPDATE GlobalTasks SET completed = 1 WHERE id = ?", (globalTask_id,))
        conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND globalTask_id = ?", (user_id, globalTask_id))
        
        # Update the user's sign-ins by 5
        conn.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
        signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
        rank = calculate_rank(signins)
        conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

        conn.commit()

    return redirect(url_for('user_tasks', user_id=user_id))




# -----------------------
# Routes: Sign-In Management
# -----------------------

@app.route('/signin/<int:user_id>', methods=['POST'])
def signin(user_id):
    """Handle user sign-ins and update their national and global rank."""
    current_time = datetime.now()

    with get_db_connection() as conn:
        last_signin = conn.execute(
            "SELECT date, time FROM Attendance WHERE user_id = ? ORDER BY date DESC, time DESC LIMIT 1", 
            (user_id,)
        ).fetchone()

        if last_signin:
            last_signin_time = datetime.strptime(f"{last_signin['date']} {last_signin['time']}", "%Y-%m-%d %H:%M:%S")
            time_diff = current_time - last_signin_time

            if time_diff < timedelta(hours=12):
                remaining_time = timedelta(hours=12) - time_diff
                return jsonify({"message": f"You can sign in again in {remaining_time}."}), 400

        # Update Attendance
        date = current_time.strftime("%Y-%m-%d")
        time = current_time.strftime("%H:%M:%S")
        conn.execute("INSERT INTO Attendance (user_id, date, time) VALUES (?, ?, ?)", (user_id, date, time))
        
        # Update National Sign-ins
        conn.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
        
        # Update Global Sign-ins
        conn.execute("UPDATE Ranks SET global_signins = global_signins + 5 WHERE user_id = ?", (user_id,))

        # Retrieve updated sign-ins
        rank_info = conn.execute("SELECT signins, global_signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()
        
        if rank_info is None:
            return jsonify({"error": "Rank information not found for the user."}), 404

        signins = rank_info['signins']
        global_signins = rank_info['global_signins']
        
        # Calculate rank based on national sign-ins
        national_rank = calculate_rank(signins)
        # Calculate global rank based on global sign-ins
        global_rank = calculate_rank(global_signins)
        
        conn.execute("UPDATE Ranks SET rank = ?, global_rank = ? WHERE user_id = ?", (national_rank, global_rank, user_id))

        conn.commit()

    return redirect(url_for('user_detail', user_id=user_id,))



# Route to serve the task setup page
@app.route('/tasks')
def tasks():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Retrieve all tasks from the database
    c.execute("SELECT id, task, url FROM Tasks WHERE completed = 0")
    tasks = c.fetchall()
    conn.close()
    
    return render_template('task_setup.html', tasks=tasks)


@app.route('/submit_task', methods=['POST'])
def submit_task():
    """Submit a new task to the database."""
    task_name = request.form['task_name']
    task_url = request.form['task_url']
    country = request.form['country']  # Ensure country is provided

    with get_db_connection() as conn:
        conn.execute("INSERT INTO Tasks (task, url, country) VALUES (?, ?, ?)", (task_name, task_url, country))
        conn.commit()

    return redirect(url_for('tasks'))  # Redirect back to the task setup page


# Route to serve the task setup page
@app.route('/globaltasks')
def globaltasks():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Retrieve all tasks from the database
    c.execute("SELECT id, task, url FROM GlobalTasks WHERE completed = 0")
    globaltasks = c.fetchall()
    conn.close()
    
    return render_template('global_setup.html', globaltasks=globaltasks)

# Route to handle task submission
@app.route('/submit_global_task', methods=['POST'])
def submit_global_task():
    task_name = request.form['task_name']
    task_description = request.form['task_description']
    task_url = request.form['task_url']

    conn = get_db_connection()
    conn.execute("INSERT INTO GlobalTasks (task, url) VALUES (?, ?)", (task_name, task_url))
    conn.commit()
    conn.close()

    return redirect(url_for('globaltasks'))  # Redirect back to the task setup page


@app.route('/user/<int:user_id>/referral_link')
def referral_link(user_id):
    """Generate and display the referral link for the user."""
    with get_db_connection() as conn:  
        # Fetch user details
        user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
        
        if user is None:
            return "User not found", 404
        
        # Generate referral link
        referral_link = f"https://t.me/m2e2bot?={user_id}"  # Replace YOUR_BOT_USERNAME with your bot's username

        # Render the template with the user and referral link
        return render_template('referral_link.html', user=user, user_id=user_id, referral_link=referral_link)
    


# Flask route to display user information and referral link
@app.route('/user/<int:user_id>')
def user_profile(user_id):
    # Use get_db_connection to manage the database connection
    with get_db_connection() as conn:
        c = conn.cursor()  # Create a cursor from the connection
        c.execute("SELECT username, country FROM Users WHERE id = ?", (user_id,))
        user = c.fetchone()

        if user:
            username, country = user
            referral_link = url_for('generate_referral', user_id=user_id, _external=True)
            return render_template('user_profile.html', username=username, country=country, referral_link=referral_link)
        else:
            return "User not found", 404
        # No need to explicitly commit unless you're modifying the database



@app.route('/user_stats/<int:user_id>')
def user_stats(user_id):
    conn = get_db_connection()

    # Fetch total referrals
    total_referrals = conn.execute('''
        SELECT COUNT(*) FROM Referrals WHERE referrer_id = ?
    ''', (user_id,)).fetchone()[0]

    # Fetch total sign-ins
    total_signins = conn.execute('''
        SELECT SUM(signins) FROM Ranks WHERE user_id = ?
    ''', (user_id,)).fetchone()[0]

    conn.close()

    return render_template('referral_link.html', total_referrals=total_referrals, total_signins=total_signins, user_id=user_id)

    


@app.route('/user_signins/<int:user_id>')
def user_signins(user_id):
    with get_db_connection() as conn:
        c = conn.cursor()

        # Fetch user's username and country
        c.execute("SELECT username, country FROM Users WHERE id = ?", (user_id,))
        user = c.fetchone()

        if user:
            username = user[0]
            user_country = user[1]

            # Fetch national sign-ins (sign-ins from the user's country)
            c.execute("""
                SELECT SUM(Ranks.signins) 
                FROM Ranks 
                JOIN Users ON Ranks.user_id = Users.id 
                WHERE Users.country = ?
            """, (user_country,))
            national_signins = c.fetchone()[0] or 0

            # Fetch total sign-ins (sign-ins from all countries)
            c.execute("""
                SELECT SUM(Ranks.signins) 
                FROM Ranks
            """)
            total_signins = c.fetchone()[0] or 0

            # Fetch total number of national users
            c.execute("""
                SELECT COUNT(*) 
                FROM Users 
                WHERE country = ?
            """, (user_country,))
            total_national_users = c.fetchone()[0] or 0

            # Fetch total number of global users (including the user's country)
            c.execute("""
                SELECT COUNT(*) 
                FROM Users
            """)
            total_global_users = c.fetchone()[0] or 0

            return render_template(
                'user_signins.html',
                user=user,
                user_id=user_id,
                username=username,
                user_country=user_country,
                national_signins=national_signins,
                total_signins=total_signins,
                total_national_users=total_national_users,
                total_global_users=total_global_users
            )
        else:
            return "User not found", 404



if __name__ == "__main__":
    app.run(debug=True)






















# from flask import Flask, render_template, redirect, url_for, request, jsonify, session
# import sqlite3
# from datetime import datetime, timedelta

# import requests

# app = Flask(__name__)
# app.secret_key = 'b80474db0f29807a5689a622fe95d2794c8f8e6f871d1fdc'  # Replace with a secure key in production

# # -----------------------
# # Database Helper Functions
# # -----------------------

# def get_db_connection():
#     """Create a connection to the SQLite database."""
#     conn = sqlite3.connect('attendance.db')
#     conn.row_factory = sqlite3.Row
#     return conn


# def calculate_rank(signins):
#     """Calculate the rank of a user based on the number of sign-ins."""
#     RANKS = {
#         'Member': 1,
#         'Bonk': 120,
#         'Dorm': 200,
#         'Area': 250,
#         'City': 320,
#         'State': 400,
#         'Zonal': 500,
#         'National': 600,
#         'Regional': 700,
#         'Global': 1000,
#         'Universal': 1500
#     }
#     for rank, threshold in sorted(RANKS.items(), key=lambda x: x[1], reverse=True):
#         if signins >= threshold:
#             return rank
#     return 'Unranked'


# def get_current_user_id():
#     """Retrieve the current user's ID from the session."""
#     return session.get('user_id')

# # -----------------------
# # Routes: User Management
# # -----------------------

# @app.route('/')
# def index():
#     """Display all users."""
#     with get_db_connection() as conn:
#         users = conn.execute('SELECT * FROM Users').fetchall()
#     return render_template('index.html', users=users)

# @app.route('/start_bot')
# def start_bot():
#     """Display the  bot page."""
#     return render_template('start_bot.html')

# @app.route('/user/<int:user_id>')
# def user_detail(user_id):
#     """Display details for a specific user."""
#     with get_db_connection() as conn:
#         user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
#         rank = conn.execute('SELECT rank, signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()
#         referral_link = f"https://yourdomain.com/register/{user_id}"

#         last_signin = conn.execute('''
#             SELECT date, time 
#             FROM Attendance 
#             WHERE user_id = ? 
#             ORDER BY date DESC, time DESC 
#             LIMIT 1
#         ''', (user_id,)).fetchone()

#         if last_signin:
#             last_signin_time = datetime.strptime(f"{last_signin['date']} {last_signin['time']}", "%Y-%m-%d %H:%M:%S")
#             time_diff = datetime.now() - last_signin_time
#             if time_diff < timedelta(hours=12):
#                 remaining_time_str = str(timedelta(hours=12) - time_diff).split('.')[0]
#             else:
#                 remaining_time_str = None
#         else:
#             remaining_time_str = None

#         tasks = conn.execute('''
#             SELECT t.id, t.task, ut.completed 
#             FROM Tasks t
#             LEFT JOIN UserTasks ut ON t.id = ut.task_id
#             WHERE ut.user_id = ? OR ut.user_id IS NULL
#         ''', (user_id,)).fetchall()

#     return render_template('user_detail.html', 
#                            user=user, 
#                            rank=rank, 
#                            referral_link=referral_link,
#                            remaining_time=remaining_time_str,
#                            tasks=tasks)

# @app.route('/display_user/<int:user_id>')
# def display_user(user_id):
#     """Display user information and redirect to user details page."""
#     with get_db_connection() as conn:
#         user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
#     if user:
#         return render_template('display_user.html', user=user)
#     else:
#         return "User not found.", 404

# # -----------------------
# # Routes: Task Management
# # -----------------------

# @app.route('/assign_task/<int:user_id>', methods=['POST'])
# def assign_task(user_id):
#     """Assign a new task to the user based on their country if they do not have an active task."""
#     with get_db_connection() as conn:
#         # Fetch the user's country
#         user_country = conn.execute("SELECT country FROM Users WHERE id = ?", (user_id,)).fetchone()['country']

#         # Check for existing tasks for this user
#         task = conn.execute("SELECT task_id FROM UserTasks WHERE user_id = ?", (user_id,)).fetchone()

#         if not task:
#             # Fetch available tasks for the user's country
#             new_task = conn.execute('''
#                 SELECT id, task, url FROM Tasks 
#                 WHERE completed = 0 AND country = ? 
#                 LIMIT 1
#             ''', (user_country,)).fetchone()
            
#             if new_task:
#                 task_id, task_text, task_url = new_task
#                 conn.execute('''
#                     INSERT INTO UserTasks (user_id, task_id) 
#                     VALUES (?, ?)
#                 ''', (user_id, task_id))
#                 conn.commit()
#                 return jsonify({"message": f"Task assigned: {task_text}", "task_url": task_url})
#             else:
#                 return jsonify({"message": "No tasks are currently available for your country."}), 404
#         else:
#             return jsonify({"message": "You already have an active task."}), 400


# @app.route('/user/<int:user_id>/tasks')
# def user_tasks(user_id):
#     """Display all available tasks for the user based on their country."""
#     with get_db_connection() as conn:
#         user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
#         if not user:
#             return "User not found.", 404

#         user_country = user['country']
#         tasks = conn.execute('SELECT * FROM Tasks WHERE completed = 0 AND country = ?', (user_country,)).fetchall()
#         rank = conn.execute('SELECT rank, signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()
#         globaltasks = conn.execute('SELECT * FROM GlobalTasks WHERE completed = 0').fetchall()
#                 # tasks = conn.execute('SELECT * FROM Tasks WHERE completed = 0').fetchall()

#         # WHERE completed = 0').fetchall()

#     return render_template('tasks.html', user=user, tasks=tasks, rank=rank, globaltasks=globaltasks)


# @app.route('/user/<int:user_id>/task/<int:task_id>/complete', methods=['POST'])
# def complete_task(user_id, task_id):
#     """Mark a task as completed and update the user's rank."""
#     with get_db_connection() as conn:
#         conn.execute("UPDATE Tasks SET completed = 1 WHERE id = ?", (task_id,))
#         conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        
#         # Update the user's sign-ins by 5
#         conn.execute("UPDATE Ranks SET signins = signins + 2 WHERE user_id = ?", (user_id,))
#         signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
#         rank = calculate_rank(signins)
#         conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

#         conn.commit()

#     return redirect(url_for('user_tasks', user_id=user_id))


# @app.route('/user/<int:user_id>/globalTask/<int:globalTask_id>/complete', methods=['POST'])
# def complete_global_task(user_id, globalTask_id):
#     """Mark a task as completed and update the user's rank."""
#     with get_db_connection() as conn:
#         conn.execute("UPDATE GlobalTasks SET completed = 1 WHERE id = ?", (globalTask_id,))
#         conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND globalTask_id = ?", (user_id, globalTask_id))
        
#         # Update the user's sign-ins by 5
#         conn.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
#         signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
#         rank = calculate_rank(signins)
#         conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

#         conn.commit()

#     return redirect(url_for('user_tasks', user_id=user_id))

# # -----------------------
# # Routes: Sign-In Management
# # -----------------------

# @app.route('/signin/<int:user_id>', methods=['POST'])
# def signin(user_id):
#     """Handle user sign-ins and update their national and global rank."""
#     current_time = datetime.now()

#     with get_db_connection() as conn:
#         last_signin = conn.execute(
#             "SELECT date, time FROM Attendance WHERE user_id = ? ORDER BY date DESC, time DESC LIMIT 1", 
#             (user_id,)
#         ).fetchone()

#         if last_signin:
#             last_signin_time = datetime.strptime(f"{last_signin['date']} {last_signin['time']}", "%Y-%m-%d %H:%M:%S")
#             time_diff = current_time - last_signin_time

#             if time_diff < timedelta(hours=12):
#                 remaining_time = timedelta(hours=12) - time_diff
#                 return jsonify({"message": f"You can sign in again in {remaining_time}."}), 400

#         # Update Attendance
#         date = current_time.strftime("%Y-%m-%d")
#         time = current_time.strftime("%H:%M:%S")
#         conn.execute("INSERT INTO Attendance (user_id, date, time) VALUES (?, ?, ?)", (user_id, date, time))
        
#         # Update National Sign-ins
#         conn.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
        
#         # Update Global Sign-ins
#         conn.execute("UPDATE Ranks SET global_signins = global_signins + 5 WHERE user_id = ?", (user_id,))

#         # Retrieve updated sign-ins
#         rank_info = conn.execute("SELECT signins, global_signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()
        
#         if rank_info is None:
#             return jsonify({"error": "Rank information not found for the user."}), 404

#         signins = rank_info['signins']
#         global_signins = rank_info['global_signins']
        
#         # Calculate rank based on national sign-ins
#         national_rank = calculate_rank(signins)
#         # Calculate global rank based on global sign-ins
#         global_rank = calculate_rank(global_signins)
        
#         conn.execute("UPDATE Ranks SET rank = ?, global_rank = ? WHERE user_id = ?", (national_rank, global_rank, user_id))

#         conn.commit()

#     return redirect(url_for('user_detail', user_id=user_id))

# # -----------------------
# # Routes: Referral Management
# # -----------------------




# @app.route('/referral_callback', methods=['POST'])
# def referral_callback():
#     """Handle the referral callback from the Telegram bot."""
#     data = request.get_json()

#     if 'callback_query' not in data:
#         return jsonify({"error": "Invalid request"}), 400

#     callback_query = data['callback_query']
#     user = callback_query['from']
#     user_id = user['id']

#     referral_link = f"https://t.me/m2e3bot_bot?={user_id}"

#     # Simulate sending the referral link back to the user
#     # In practice, this would be handled by your Telegram bot
#     # You may need to use Telegram Bot API to send a message to the user
#     # Example:
#     requests.post(
#         'https://api.telegram.org/bot/7308553019:AAHKVgixYmGnXPkq4mQpcK9bUmwkH604BP8/sendMessage',
#         json={'chat_id': user_id, 'text': f"Here is your referral link: {referral_link}"}
#     )

#     return jsonify({"message": f"Referral link for user {user_id} generated successfully."})




# def increment_signins(user_id, increment=10):
#     with get_db_connection() as conn:
#         conn.execute(
#             'UPDATE Ranks SET signins = signins + ? WHERE user_id = ?',
#             (increment, user_id)
#         )
#         conn.commit()



# @app.route('/user/<int:user_id>/referral')
# def user_referral(user_id):
#     """Display the referral link for the user."""
#     with get_db_connection() as conn:
#         user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
#         rank = conn.execute('SELECT rank, signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()

#     # Generate the referral link using the user ID
#     referral_link = f"https://t.me/m2e2bot?={user_id}"
#     return render_template('referral.html', user=user, rank=rank, referral_link=referral_link)


# # @app.route('/user/<int:user_id>/referral')
# # def user_referral(user_id):
# #     """Display the referral link for the user."""
# #     with get_db_connection() as conn:
# #         user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
# #         rank = conn.execute('SELECT rank, signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()

# #     # Generate the referral link using the user ID
# #     referral_link = f"https://t.me/m2e3bot_bot?={user_id}"
# #     return render_template('referral.html', user=user, rank=rank, referral_link=referral_link)

# @app.route('/get_referral/<int:user_id>', methods=['GET'])
# def get_referral(user_id):
#     """Generate and return a referral link for the user."""
#     referral_link = f"https://t.me/m2e2bot?={user_id}"
#     return jsonify({"referral_link": referral_link})

# @app.route('/register/<int:referrer_id>', methods=['POST'])
# def register(referrer_id):
#     """Handle the registration of a new user via a referral link."""
#     # Here you would add the logic for registering the new user.
#     # Once the user is registered successfully, increment the referrer's signins.
#     increment_signins(referrer_id)

#     return "User registered successfully and 10 sign-ins added to the referrer!"


# # # Add a route to generate and display the referral link in Flask
# # @app.route('/user/<int:user_id>/referral')
# # def user_referral(user_id):
# #     """Display the referral link for the user."""
# #     with get_db_connection() as conn:
# #         user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
# #         rank = conn.execute('SELECT rank, signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()

# #     # Generate the referral link using the user ID
# #     referral_link = f"https://t.me/m2e3bot_bot?={user_id}"
# #     return render_template('referral.html', user=user, rank=rank, referral_link=referral_link)

# # @app.route('/get_referral/<int:user_id>', methods=['GET'])
# # def get_referral(user_id):
# #     """Generate and return a referral link for the user."""
# #     referral_link = f"https://t.me/m2e3bot_bot?={user_id}"
# #     return jsonify({"referral_link": referral_link})




# # @app.route('/user/<int:user_id>/referral')
# # def user_referral(user_id):
# #     """Display the referral link for the user."""
# #     with get_db_connection() as conn:
# #         user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
# #         rank = conn.execute('SELECT rank, signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()
# #     referral_link = f"https://3fbf-197-251-193-137.ngrok-free.app/register/{user_id}"
# #     return render_template('referral.html', user=user, rank=rank, referral_link=referral_link)

# # @app.route('/get_referral/<int:user_id>', methods=['GET'])
# # def get_referral(user_id):
# #     """Generate and return a referral link for the user."""
# #     referral_link = f"https://3fbf-197-251-193-137.ngrok-free.app/register/{user_id}"
#     return jsonify({"referral_link": referral_link})


# @app.route('/register_form')
# def register_form():
#     """Render the registration form."""
#     return render_template('register_form.html')


# @app.route('/register', methods=['POST'])
# def register_user():
#     """Register a new user and assign default rank."""
#     # username = request.form['username']
#     country = request.form['country']
#     # age = int(request.form['age'])
    
#     # Generate a unique user ID, assuming user_id is provided or managed elsewhere
#     user_id = generate_user_id()  # Define this function to generate a unique ID

#     with get_db_connection() as conn:
#         c = conn.cursor()
        
#         # Insert user details into the Users table
#         c.execute('''
#             INSERT OR REPLACE INTO Users (id, country)
#             VALUES (?, ?)
#         ''', (user_id, country))

#         # Assign the user the default rank "Member" with 0 sign-ins
#         c.execute('''
#             INSERT INTO Ranks (user_id, rank, signins)
#             VALUES (?, ?, ?)
#         ''', (user_id, 'Member', 0))
        
#         conn.commit()
    
#     return redirect(url_for('user_detail', user_id=user_id))

# def generate_user_id():
#     """Generate a unique user ID."""
#     with get_db_connection() as conn:
#         c = conn.cursor()
#         c.execute('SELECT MAX(id) FROM Users')
#         max_id = c.fetchone()[0]
#         return (max_id or 0) + 1

# # Route to serve the task setup page
# @app.route('/tasks')
# def tasks():
#     conn = get_db_connection()
#     c = conn.cursor()
    
#     # Retrieve all tasks from the database
#     c.execute("SELECT id, task, url FROM Tasks WHERE completed = 0")
#     tasks = c.fetchall()
#     conn.close()
    
#     return render_template('task_setup.html', tasks=tasks)


# @app.route('/submit_task', methods=['POST'])
# def submit_task():
#     """Submit a new task to the database."""
#     task_name = request.form['task_name']
#     task_url = request.form['task_url']
#     country = request.form['country']  # Ensure country is provided

#     with get_db_connection() as conn:
#         conn.execute("INSERT INTO Tasks (task, url, country) VALUES (?, ?, ?)", (task_name, task_url, country))
#         conn.commit()

#     return redirect(url_for('tasks'))  # Redirect back to the task setup page


# # Route to serve the task setup page
# @app.route('/globaltasks')
# def globaltasks():
#     conn = get_db_connection()
#     c = conn.cursor()
    
#     # Retrieve all tasks from the database
#     c.execute("SELECT id, task, url FROM GlobalTasks WHERE completed = 0")
#     globaltasks = c.fetchall()
#     conn.close()
    
#     return render_template('global_setup.html', globaltasks=globaltasks)

# # Route to handle task submission
# @app.route('/submit_global_task', methods=['POST'])
# def submit_global_task():
#     task_name = request.form['task_name']
#     task_description = request.form['task_description']
#     task_url = request.form['task_url']

#     conn = get_db_connection()
#     conn.execute("INSERT INTO GlobalTasks (task, url) VALUES (?, ?)", (task_name, task_url))
#     conn.commit()
#     conn.close()

#     return redirect(url_for('globaltasks'))  # Redirect back to the task setup page
    
# if __name__ == '__main__':
#     app.run(debug=True)




from requests import session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import sqlite3
from datetime import datetime

# Database setup
def setup_database():
    conn = sqlite3.connect('attendance.db', check_same_thread=False)
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                country TEXT NOT NULL,
                referral_id INTEGER,
                FOREIGN KEY (referral_id) REFERENCES Users(id)
            )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Users(id)
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                FOREIGN KEY (referrer_id) REFERENCES Users(id),
                FOREIGN KEY (referred_id) REFERENCES Users(id)
            );''')

    c.execute('''CREATE TABLE IF NOT EXISTS Ranks (
                    user_id INTEGER PRIMARY KEY, 
                    rank TEXT, 
                    signins INTEGER,
                    global_signins INTEGER DEFAULT 0,
                    global_rank TEXT,
                    bonus_claimed BOOLEAN DEFAULT 0,
                    bonus_amount REAL DEFAULT 0)''')        

    c.execute('''CREATE TABLE IF NOT EXISTS Tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                country TEXT NOT NULL,
                url TEXT,
                completed BOOLEAN DEFAULT 0
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS GlobalTasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                url TEXT,
                completed BOOLEAN DEFAULT 0
            )''')

    c.execute('''CREATE TABLE IF NOT EXISTS UserTasks (
                user_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                globalTask_id INTEGER NOT NULL,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES Users(id),
                FOREIGN KEY (task_id) REFERENCES Tasks(id),
                FOREIGN KEY (globalTask_id) REFERENCES GlobalTasks(id),
                PRIMARY KEY (user_id, task_id, globalTask_id)
            )''')     
    
    conn.commit()
    return conn, c

conn, c = setup_database()

# Menu Builder
class MenuBuilder:
    @staticmethod
    def main_menu(user_id):
        signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
        referral_button = InlineKeyboardButton("📨 Get Referral Link", callback_data='referral')
        view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
        # Generate the URL for the user's dashboard
        dashboard_url = f"https://8b1a-154-161-39-89.ngrok-free.app/user_details/{user_id}"
        
        # Create a button that links to the dashboard URL
        dashboard_button = InlineKeyboardButton("📊 View Dashboard", url=dashboard_url)
        
        # Add the buttons to the keyboard layout
        keyboard = [
            [signin_button, referral_button, view_task_button, dashboard_button]
        ]
        
        return InlineKeyboardMarkup(keyboard)
# class MenuBuilder:
#     @staticmethod
#     def main_menu(user_id):
#         signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
#         referral_button = InlineKeyboardButton("📨 Get Referral Link", callback_data='referral')
#         view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
#         # Add dashboard button
#         dashboard_url = f"https://8b1a-154-161-39-89.ngrok-free.app/user_details/{user_id}"
#         dashboard_button = InlineKeyboardButton("📊 View Dashboard", url=dashboard_url)
        
#         keyboard = [
#             [signin_button, referral_button, view_task_button, dashboard_button]  # All buttons in one row
#         ]
        
#         return InlineKeyboardMarkup(keyboard)

# Task Handler
async def assign_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    # Fetch the user's country
    c.execute("SELECT country FROM Users WHERE id = ?", (user_id,))
    user_country = c.fetchone()[0]

    # Fetch available tasks for the user's country
    try:
        c.execute('''
            SELECT task_id FROM UserTasks 
            JOIN Tasks ON UserTasks.task_id = Tasks.id 
            WHERE user_id = ? AND UserTasks.completed = 0
        ''', (user_id,))
        task = c.fetchone()
        
        if not task:
            c.execute('''
                SELECT id, task, url FROM Tasks 
                WHERE completed = 0 AND country = ? 
                LIMIT 1
            ''', (user_country,))
            new_task = c.fetchone()
            
            if new_task:
                task_id, task_text, task_url = new_task
                c.execute('''
                    INSERT INTO UserTasks (user_id, task_id, globalTask_id) 
                    VALUES (?, ?, NULL)
                ''', (user_id, task_id))
                conn.commit()
                await update.message.reply_text(f"Task assigned: {task_text}")
            else:
                await update.message.reply_text("No tasks are currently available.")
        else:
            await update.message.reply_text("You already have an active task.")
    except sqlite3.OperationalError as e:
        await update.message.reply_text(f"Database error: {e}")
    finally:
        conn.close()

async def view_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    if query:
        await query.answer()
        
        user = query.from_user
        user_id = user.id
        
        with sqlite3.connect('attendance.db') as conn:
            c = conn.cursor()
            try:
                c.execute("SELECT Tasks.id, Tasks.task, Tasks.url FROM Tasks JOIN UserTasks ON Tasks.id = UserTasks.task_id WHERE UserTasks.user_id = ? AND UserTasks.completed = 0", (user_id,))
                tasks = c.fetchall()
                
                if tasks:
                    keyboard = []
                    for task_id, task_text, task_url in tasks:
                        task_button = InlineKeyboardButton(f"{task_text}", url=task_url)
                        complete_button = InlineKeyboardButton("Mark as Completed", callback_data=f'complete_task_{task_id}')
                        keyboard.append([task_button, complete_button])
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text("Here are your active tasks:", reply_markup=reply_markup)
                else:
                    await query.edit_message_text("You have no active tasks.")
            except sqlite3.OperationalError as e:
                await query.edit_message_text(f"Database error: {e}")
    else:
        await update.message.reply_text("Error: No callback query found. Please try again.")

async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    task_id = int(query.data.split('_')[-1])
    
    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        try:
            c.execute("UPDATE UserTasks SET completed = 1 WHERE user_id = ? AND task_id = ?", (user_id, task_id))
            conn.commit()
            
            c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
            conn.commit()
            
            await query.edit_message_text("Task completed! Your progress has been recorded.")
        except sqlite3.OperationalError as e:
            await query.edit_message_text(f"Database error: {e}")

# Registration form for country selection
async def registration_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    countries = ["Country1", "Country2"]  # Replace with actual country list
    buttons = [InlineKeyboardButton(country, callback_data=f"select_country_{country}") for country in countries]
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]  # Arrange buttons in rows of 2
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Please select your country:", reply_markup=reply_markup)

# Handle country selection
async def select_country_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    selected_country = query.data.split('_')[-1]  # Extract the selected country from callback data
    
    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        try:
            # Update the user's country
            c.execute("UPDATE Users SET country = ? WHERE id = ?", (selected_country, user_id))
            
            # Award the user with 5 additional sign-ins
            c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
            
            conn.commit()
            await query.edit_message_text(f"Country updated to: {selected_country}. You have been awarded 5 sign-ins. You can now proceed to the main menu with /menu.")
        except sqlite3.OperationalError as e:
            await query.edit_message_text(f"Database error: {e}")

# Update the start command to include registration form
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    username = user.username
    
    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        try:
            # Insert user into the Users table if not already present
            c.execute("INSERT OR IGNORE INTO Users (id, username, country) VALUES (?, ?, '')", (user_id, username))
            c.execute("INSERT OR IGNORE INTO Ranks (user_id, rank, signins) VALUES (?, ?, ?)", (user_id, 'Unranked', 0))
            conn.commit()
            
            await update.message.reply_text(
                f"Hello {username}! Welcome to the bot. Please complete your registration by selecting your country."
            )
            
            # Instead of sending the URL, directly show the registration form
            await registration_form(update, context)
        except sqlite3.OperationalError as e:
            await update.message.reply_text(f"Database error: {e}")

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
#     username = user.username
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             # Insert user into the Users table if not already present
#             c.execute("INSERT OR IGNORE INTO Users (id, username, country) VALUES (?, ?, '')", (user_id, username))
#             c.execute("INSERT OR IGNORE INTO Ranks (user_id, rank, signins) VALUES (?, ?, ?)", (user_id, 'Unranked', 0))
#             conn.commit()
            
#             await update.message.reply_text(
#                 f"Hello {username}! Welcome to the bot. Please complete your registration by selecting your country."
#             )
            
#             user_details_url = f"https://8b1a-154-161-39-89.ngrok-free.app/user_details/{user_id}"
#             await update.message.reply_text(
#                 f"You can view your details here: {user_details_url}"
#             )
            
#             await registration_form(update, context)
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

async def signin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M:%S')
    
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    try:
        # Check if the user has already signed in today
        c.execute("SELECT id FROM Attendance WHERE user_id = ? AND date = ?", (user_id, date))
        existing_entry = c.fetchone()
        
        if existing_entry:
            await query.edit_message_text("You have already signed in today.")
        else:
            # Insert sign-in record
            c.execute("INSERT INTO Attendance (user_id, date, time) VALUES (?, ?, ?)", (user_id, date, time))
            conn.commit()
            
            # Update rank or other relevant data
            c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            
            await query.edit_message_text("Sign-in successful! Your progress has been recorded.")
    except sqlite3.OperationalError as e:
        await query.edit_message_text(f"Database error: {e}")
    finally:
        conn.close()

async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    referral_link = f"https://t.me/m2e3bot_bot/register/{user_id}"
    
    await query.edit_message_text(f"Your referral link: {referral_link}")

# Main menu command
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id

    # Build the main menu with the user's ID
    reply_markup = MenuBuilder.main_menu(user_id)
    
    # Send the menu to the user
    await update.message.reply_text("Main Menu", reply_markup=reply_markup)

# async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id

#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         c.execute("SELECT country FROM Users WHERE id = ?", (user_id,))
#         user_country = c.fetchone()[0]

#         if not user_country:
#             await registration_form(update, context)
#         else:
#             reply_markup = MenuBuilder.main_menu(user_id)
#             await update.message.reply_text("Main Menu", reply_markup=reply_markup)

async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    # Construct the URL for the user's dashboard
    dashboard_url = f"https://8b1a-154-161-39-89.ngrok-free.app/user_details/{user_id}"
    
    # Send the dashboard URL to the user
    await query.edit_message_text(f"View your dashboard here: {dashboard_url}")

# Command handlers setup
def main():
    application = Application.builder().token("7308553019:AAHKVgixYmGnXPkq4mQpcK9bUmwkH604BP8").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CallbackQueryHandler(signin_callback, pattern="signin"))
    application.add_handler(CallbackQueryHandler(referral_callback, pattern="referral"))
    application.add_handler(CallbackQueryHandler(view_task_callback, pattern="view_task"))
    application.add_handler(CallbackQueryHandler(complete_task_callback, pattern="complete_task_"))
    application.add_handler(CallbackQueryHandler(select_country_callback, pattern="select_country_"))
    application.add_handler(CallbackQueryHandler(dashboard_callback, pattern="dashboard"))
    
    application.run_polling()

if __name__ == "__main__":
    main()




from requests import session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, Defaults
import sqlite3
from datetime import datetime

# Increase the Telegram API timeout to 60 seconds
# defaults = Defaults(timeout=60)

# Database setup
def setup_database():
    conn = sqlite3.connect('attendance.db', check_same_thread=False)
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                country TEXT NOT NULL,
                referral_id INTEGER,
                FOREIGN KEY (referral_id) REFERENCES Users(id)
            )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Users(id)
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                FOREIGN KEY (referrer_id) REFERENCES Users(id),
                FOREIGN KEY (referred_id) REFERENCES Users(id)
            );''')

    c.execute('''CREATE TABLE IF NOT EXISTS Ranks (
                    user_id INTEGER PRIMARY KEY, 
                    rank TEXT, 
                    signins INTEGER,
                    global_signins INTEGER DEFAULT 0,
                    global_rank TEXT,
                    bonus_claimed BOOLEAN DEFAULT 0,
                    bonus_amount REAL DEFAULT 0)''')        

    c.execute('''CREATE TABLE IF NOT EXISTS Tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                country TEXT NOT NULL,
                url TEXT,
                completed BOOLEAN DEFAULT 0
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS GlobalTasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                url TEXT,
                completed BOOLEAN DEFAULT 0
            )''')

    c.execute('''CREATE TABLE IF NOT EXISTS UserTasks (
                user_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                globalTask_id INTEGER NOT NULL,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES Users(id),
                FOREIGN KEY (task_id) REFERENCES Tasks(id),
                FOREIGN KEY (globalTask_id) REFERENCES GlobalTasks(id),
                PRIMARY KEY (user_id, task_id, globalTask_id)
            )''')     
    
    conn.commit()
    return conn, c

conn, c = setup_database()


# Menu Builder
class MenuBuilder:
    @staticmethod
    def main_menu(user_id):
        signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
        referral_button = InlineKeyboardButton("📨 Get Referral Link", callback_data='referral')
        view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
        # Add dashboard button
        dashboard_url = f"https://8b1a-154-161-39-89.ngrok-free.app/user_details/{user_id}"
        dashboard_button = InlineKeyboardButton("📊 View Dashboard", url=dashboard_url)
        
        keyboard = [
            [signin_button, referral_button],
            [view_task_button] 
             [dashboard_button]  # Include the new dashboard button
        ]
        
        return InlineKeyboardMarkup(keyboard)


# Task Handler
async def assign_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    # Fetch the user's country
    c.execute("SELECT country FROM Users WHERE id = ?", (user_id,))
    user_country = c.fetchone()[0]

    # Fetch available tasks for the user's country
    try:
        c.execute('''
            SELECT task_id FROM UserTasks 
            JOIN Tasks ON UserTasks.task_id = Tasks.id 
            WHERE user_id = ? AND UserTasks.completed = 0
        ''', (user_id,))
        task = c.fetchone()
        
        if not task:
            c.execute('''
                SELECT id, task, url FROM Tasks 
                WHERE completed = 0 AND country = ? 
                LIMIT 1
            ''', (user_country,))
            new_task = c.fetchone()
            
            if new_task:
                task_id, task_text, task_url = new_task
                c.execute('''
                    INSERT INTO UserTasks (user_id, task_id, globalTask_id) 
                    VALUES (?, ?, NULL)
                ''', (user_id, task_id))
                conn.commit()
                await update.message.reply_text(f"Task assigned: {task_text}")
            else:
                await update.message.reply_text("No tasks are currently available.")
        else:
            await update.message.reply_text("You already have an active task.")
    except sqlite3.OperationalError as e:
        await update.message.reply_text(f"Database error: {e}")
    finally:
        conn.close()


async def view_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    if query:
        await query.answer()
        
        user = query.from_user
        user_id = user.id
        
        with sqlite3.connect('attendance.db') as conn:
            c = conn.cursor()
            try:
                c.execute("SELECT Tasks.id, Tasks.task, Tasks.url FROM Tasks JOIN UserTasks ON Tasks.id = UserTasks.task_id WHERE UserTasks.user_id = ? AND UserTasks.completed = 0", (user_id,))
                tasks = c.fetchall()
                
                if tasks:
                    keyboard = []
                    for task_id, task_text, task_url in tasks:
                        task_button = InlineKeyboardButton(f"{task_text}", url=task_url)
                        complete_button = InlineKeyboardButton("Mark as Completed", callback_data=f'complete_task_{task_id}')
                        keyboard.append([task_button, complete_button])
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text("Here are your active tasks:", reply_markup=reply_markup)
                else:
                    await query.edit_message_text("You have no active tasks.")
            except sqlite3.OperationalError as e:
                await query.edit_message_text(f"Database error: {e}")
    else:
        await update.message.reply_text("Error: No callback query found. Please try again.")



async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    task_id = int(query.data.split('_')[-1])
    
    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        try:
            c.execute("UPDATE UserTasks SET completed = 1 WHERE user_id = ? AND task_id = ?", (user_id, task_id))
            conn.commit()
            
            c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
            conn.commit()
            
            await query.edit_message_text("Task completed! Your progress has been recorded.")
        except sqlite3.OperationalError as e:
            await query.edit_message_text(f"Database error: {e}")



# Registration form for country selection
async def registration_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    countries = [""]  # Add more as needed
    buttons = [InlineKeyboardButton(country, callback_data=f"select_country_{country}") for country in countries]
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]  # Arrange buttons in rows of 2
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Please select your country:", reply_markup=reply_markup)



# Handle country selection
async def select_country_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    selected_country = query.data.split('_')[-1]  # Extract the selected country from callback data
    
    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        try:
            # Update the user's country
            c.execute("UPDATE Users SET country = ? WHERE id = ?", (selected_country, user_id))
            
            # Award the user with 5 additional sign-ins
            c.execute("UPDATE Users SET signins = signins + 5 WHERE id = ?", (user_id,))
            
            conn.commit()
            await query.edit_message_text(f"Country updated to: {selected_country}. You have been awarded 5 sign-ins. You can now proceed to the main menu with /menu.")
        except sqlite3.OperationalError as e:
            await query.edit_message_text(f"Database error: {e}")


# Update the start command to include registration form

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    username = user.username
    
    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        try:
            # Insert user into the Users table if not already present
            c.execute("INSERT OR IGNORE INTO Users (id, username, country) VALUES (?, ?, '')", (user_id, username))
            c.execute("INSERT OR IGNORE INTO Ranks (user_id, rank, signins) VALUES (?, ?, ?)", (user_id, 'Unranked', 0))
            conn.commit()
            
            # Set the user_id in the session
            # session['user_id'] = user_id
            
            await update.message.reply_text(
                f"Hello {username}! Welcome to the bot. Please complete your registration by selecting your country."
            )
            
            user_details_url = f"https://8b1a-154-161-39-89.ngrok-free.app/user_details/{user_id}"
            await update.message.reply_text(
                f"You can view your details here: {user_details_url}"
            )
            
            await registration_form(update, context)
        except sqlite3.OperationalError as e:
            await update.message.reply_text(f"Database error: {e}")



async def signin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M:%S')
    
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    try:
        # Check if the user has already signed in today
        c.execute("SELECT id FROM Attendance WHERE user_id = ? AND date = ?", (user_id, date))
        existing_entry = c.fetchone()
        
        if existing_entry:
            await query.edit_message_text("You have already signed in today.")
        else:
            # Insert sign-in record
            c.execute("INSERT INTO Attendance (user_id, date, time) VALUES (?, ?, ?)", (user_id, date, time))
            conn.commit()
            
            # Update rank or other relevant data
            c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            
            await query.edit_message_text("Sign-in successful! Your progress has been recorded.")
    except sqlite3.OperationalError as e:
        await query.edit_message_text(f"Database error: {e}")
    finally:
        conn.close()


async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    referral_link = f"https://t.me/m2e3bot_bot/register/{user_id}"
    
    await query.edit_message_text(f"Your referral link: {referral_link}")

# Main menu command
# Main menu command
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id

    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        c.execute("SELECT country FROM Users WHERE id = ?", (user_id,))
        user_country = c.fetchone()[0]

        if not user_country:
            await registration_form(update, context)
        else:
            reply_markup = MenuBuilder.main_menu(user_id)
            await update.message.reply_text("Main Menu", reply_markup=reply_markup)


# Command handlers setup
def main():
    application = Application.builder().token("7308553019:AAHKVgixYmGnXPkq4mQpcK9bUmwkH604BP8").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CallbackQueryHandler(signin_callback, pattern="signin"))
    application.add_handler(CallbackQueryHandler(referral_callback, pattern="referral"))
    application.add_handler(CallbackQueryHandler(view_task_callback, pattern="view_task"))
    application.add_handler(CallbackQueryHandler(complete_task_callback, pattern="complete_task_"))
    application.add_handler(CallbackQueryHandler(select_country_callback, pattern="select_country_"))
    
    application.run_polling()

if __name__ == "__main__":
    main()
















from flask import Flask, render_template, redirect, url_for, request, jsonify, session
import sqlite3
from datetime import datetime, timedelta

from psutil import users
import requests

app = Flask(__name__)
app.secret_key = 'b80474db0f29807a5689a622fe95d2794c8f8e6f871d1fdc'  # Replace with a secure key in production

# -----------------------
# Database Helper Functions
# -----------------------

def get_db_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    return conn


def calculate_rank(signins):
    """Calculate the rank of a user based on the number of sign-ins."""
    RANKS = {
        'Member': 1,
        'Bonk': 120,
        'Dorm': 200,
        'Area': 250,
        'City': 320,
        'State': 400,
        'Zonal': 500,
        'National': 600,
        'Regional': 700,
        'Global': 1000,
        'Universal': 1500
    }
    for rank, threshold in sorted(RANKS.items(), key=lambda x: x[1], reverse=True):
        if signins >= threshold:
            return rank
    return 'Unranked'


def get_current_user_id():
    """Retrieve the current user's ID from the session."""
    return session.get('user_id')

# -----------------------
# Routes: User Management
# -----------------------

@app.route('/')
def index():
    """Display all users."""
    with get_db_connection() as conn:
        users = conn.execute('SELECT * FROM Users').fetchall()
    return render_template('index.html', users=users)

@app.route('/start_bot')
def start_bot():
    """Display the start bot page."""
    return render_template('start_bot.html')

@app.route('/user/<int:user_id>')
def user_detail(user_id):
    """Display details for a specific user."""
    with get_db_connection() as conn:
        user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
        rank = conn.execute('SELECT rank, signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()
        referral_link = f"https://yourdomain.com/register/{user_id}"

        last_signin = conn.execute('''
            SELECT date, time 
            FROM Attendance 
            WHERE user_id = ? 
            ORDER BY date DESC, time DESC 
            LIMIT 1
        ''', (user_id,)).fetchone()

        if last_signin:
            last_signin_time = datetime.strptime(f"{last_signin['date']} {last_signin['time']}", "%Y-%m-%d %H:%M:%S")
            time_diff = datetime.now() - last_signin_time
            if time_diff < timedelta(hours=12):
                remaining_time_str = str(timedelta(hours=12) - time_diff).split('.')[0]
            else:
                remaining_time_str = None
        else:
            remaining_time_str = None

        tasks = conn.execute('''
            SELECT t.id, t.task, ut.completed 
            FROM Tasks t
            LEFT JOIN UserTasks ut ON t.id = ut.task_id
            WHERE ut.user_id = ? OR ut.user_id IS NULL
        ''', (user_id,)).fetchall()

    return render_template('user_detail.html', 
                           user=user, 
                           rank=rank, 
                           referral_link=referral_link,
                           remaining_time=remaining_time_str,
                           tasks=tasks)

@app.route('/display_user/<int:user_id>')
def display_user(user_id):
    """Display user information and redirect to user details page."""
    with get_db_connection() as conn:
        user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
    if user:
        return render_template('display_user.html', user=user)
    else:
        return "User not found.", 404

# -----------------------
# Routes: Task Management
# -----------------------

@app.route('/assign_task/<int:user_id>', methods=['POST'])
def assign_task(user_id):
    """Assign a new task to the user based on their country if they do not have an active task."""
    with get_db_connection() as conn:
        # Fetch the user's country
        user_country = conn.execute("SELECT country FROM Users WHERE id = ?", (user_id,)).fetchone()['country']

        # Check for existing tasks for this user
        task = conn.execute("SELECT task_id FROM UserTasks WHERE user_id = ?", (user_id,)).fetchone()

        if not task:
            # Fetch available tasks for the user's country
            new_task = conn.execute('''
                SELECT id, task, url FROM Tasks 
                WHERE completed = 0 AND country = ? 
                LIMIT 1
            ''', (user_country,)).fetchone()
            
            if new_task:
                task_id, task_text, task_url = new_task
                conn.execute('''
                    INSERT INTO UserTasks (user_id, task_id) 
                    VALUES (?, ?)
                ''', (user_id, task_id))
                conn.commit()
                return jsonify({"message": f"Task assigned: {task_text}", "task_url": task_url})
            else:
                return jsonify({"message": "No tasks are currently available for your country."}), 404
        else:
            return jsonify({"message": "You already have an active task."}), 400


@app.route('/user/<int:user_id>/tasks')
def user_tasks(user_id):
    """Display all available tasks for the user based on their country."""
    with get_db_connection() as conn:
        user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return "User not found.", 404

        user_country = user['country']
        tasks = conn.execute('SELECT * FROM Tasks WHERE completed = 0 AND country = ?', (user_country,)).fetchall()
        rank = conn.execute('SELECT rank, signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()
        globaltasks = conn.execute('SELECT * FROM GlobalTasks WHERE completed = 0').fetchall()
                # tasks = conn.execute('SELECT * FROM Tasks WHERE completed = 0').fetchall()

        # WHERE completed = 0').fetchall()

    return render_template('tasks.html', user=user, tasks=tasks, rank=rank, globaltasks=globaltasks)


@app.route('/user/<int:user_id>/task/<int:task_id>/complete', methods=['POST'])
def complete_task(user_id, task_id):
    """Mark a task as completed and update the user's rank."""
    with get_db_connection() as conn:
        conn.execute("UPDATE Tasks SET completed = 1 WHERE id = ?", (task_id,))
        conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        
        # Update the user's sign-ins by 5
        conn.execute("UPDATE Ranks SET signins = signins + 2 WHERE user_id = ?", (user_id,))
        signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
        rank = calculate_rank(signins)
        conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

        conn.commit()

    return redirect(url_for('user_tasks', user_id=user_id))


@app.route('/user/<int:user_id>/globalTask/<int:globalTask_id>/complete', methods=['POST'])
def complete_global_task(user_id, globalTask_id):
    """Mark a task as completed and update the user's rank."""
    with get_db_connection() as conn:
        conn.execute("UPDATE GlobalTasks SET completed = 1 WHERE id = ?", (globalTask_id,))
        conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND globalTask_id = ?", (user_id, globalTask_id))
        
        # Update the user's sign-ins by 5
        conn.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
        signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
        rank = calculate_rank(signins)
        conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

        conn.commit()

    return redirect(url_for('user_tasks', user_id=user_id))

# -----------------------
# Routes: Sign-In Management
# -----------------------

@app.route('/signin/<int:user_id>', methods=['POST'])
def signin(user_id):
    """Handle user sign-ins and update their national and global rank."""
    current_time = datetime.now()

    with get_db_connection() as conn:
        last_signin = conn.execute(
            "SELECT date, time FROM Attendance WHERE user_id = ? ORDER BY date DESC, time DESC LIMIT 1", 
            (user_id,)
        ).fetchone()

        if last_signin:
            last_signin_time = datetime.strptime(f"{last_signin['date']} {last_signin['time']}", "%Y-%m-%d %H:%M:%S")
            time_diff = current_time - last_signin_time

            if time_diff < timedelta(hours=12):
                remaining_time = timedelta(hours=12) - time_diff
                return jsonify({"message": f"You can sign in again in {remaining_time}."}), 400

        # Update Attendance
        date = current_time.strftime("%Y-%m-%d")
        time = current_time.strftime("%H:%M:%S")
        conn.execute("INSERT INTO Attendance (user_id, date, time) VALUES (?, ?, ?)", (user_id, date, time))
        
        # Update National Sign-ins
        conn.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
        
        # Update Global Sign-ins
        conn.execute("UPDATE Ranks SET global_signins = global_signins + 5 WHERE user_id = ?", (user_id,))

        # Retrieve updated sign-ins
        rank_info = conn.execute("SELECT signins, global_signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()
        
        if rank_info is None:
            return jsonify({"error": "Rank information not found for the user."}), 404

        signins = rank_info['signins']
        global_signins = rank_info['global_signins']
        
        # Calculate rank based on national sign-ins
        national_rank = calculate_rank(signins)
        # Calculate global rank based on global sign-ins
        global_rank = calculate_rank(global_signins)
        
        conn.execute("UPDATE Ranks SET rank = ?, global_rank = ? WHERE user_id = ?", (national_rank, global_rank, user_id))

        conn.commit()

    return redirect(url_for('user_detail', user_id=user_id))

# -----------------------
# Routes: Referral Management
# -----------------------


def increment_signins(user_id, increment=10):
    with get_db_connection() as conn:
        conn.execute(
            'UPDATE Ranks SET signins = signins + ? WHERE user_id = ?',
            (increment, user_id)
        )
        conn.commit()


@app.route('/user/<int:user_id>/referral')
def user_referral(user_id):
    """Display the referral link for the user."""
    with get_db_connection() as conn:
        user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
        rank = conn.execute('SELECT rank, signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()

    # Generate the referral link using the user ID
    referral_link = f"https://t.me/m2e2bot?start={user_id}"
    return render_template('referral.html', user=user, rank=rank, referral_link=referral_link)


@app.route('/get_referral/<int:user_id>', methods=['GET'])
def get_referral(user_id):
    """Generate and return a referral link for the user."""
    referral_link = f"https://t.me/m2e2bot?start={user_id}"
    return jsonify({"referral_link": referral_link})

@app.route('/register/<int:referrer_id>', methods=['POST'])
def register(referrer_id):
    """Handle the registration of a new user via a referral link."""
    # Here you would add the logic for registering the new user.
    # Once the user is registered successfully, increment the referrer's signins.
    increment_signins(referrer_id)

    return "User registered successfully and 10 sign-ins added to the referrer!"



@app.route('/register_form')
def register_form():
    """Render the registration form."""
    return render_template('register_form.html')


@app.route('/register', methods=['POST'])
def register_user():
    """Register a new user and assign default rank."""
    username = request.form['username']
    country = request.form['country']
    # age = int(request.form['age'])
    
    # Generate a unique user ID, assuming user_id is provided or managed elsewhere
    user_id = generate_user_id()  # Define this function to generate a unique ID

    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Insert user details into the Users table
        c.execute('''
            INSERT OR REPLACE INTO Users (id, username, country)
            VALUES (?, ?, ?)
        ''', (user_id, username, country))

        # Assign the user the default rank "Member" with 0 sign-ins
        c.execute('''
            INSERT INTO Ranks (user_id, rank, signins)
            VALUES (?, ?, ?)
        ''', (user_id, 'Member', 0))
        
        conn.commit()
    
    return redirect(url_for('user_detail', user_id=user_id))

def generate_user_id():
    """Generate a unique user ID."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT MAX(id) FROM Users')
        max_id = c.fetchone()[0]
        return (max_id or 0) + 1

# Route to serve the task setup page
@app.route('/tasks')
def tasks():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Retrieve all tasks from the database
    c.execute("SELECT id, task, url FROM Tasks WHERE completed = 0")
    tasks = c.fetchall()
    conn.close()
    
    return render_template('task_setup.html', tasks=tasks)


@app.route('/submit_task', methods=['POST'])
def submit_task():
    """Submit a new task to the database."""
    task_name = request.form['task_name']
    task_url = request.form['task_url']
    country = request.form['country']  # Ensure country is provided

    with get_db_connection() as conn:
        conn.execute("INSERT INTO Tasks (task, url, country) VALUES (?, ?, ?)", (task_name, task_url, country))
        conn.commit()

    return redirect(url_for('tasks'))  # Redirect back to the task setup page


# Route to serve the task setup page
@app.route('/globaltasks')
def globaltasks():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Retrieve all tasks from the database
    c.execute("SELECT id, task, url FROM GlobalTasks WHERE completed = 0")
    globaltasks = c.fetchall()
    conn.close()
    
    return render_template('global_setup.html', globaltasks=globaltasks)

# Route to handle task submission
@app.route('/submit_global_task', methods=['POST'])
def submit_global_task():
    task_name = request.form['task_name']
    task_description = request.form['task_description']
    task_url = request.form['task_url']

    conn = get_db_connection()
    conn.execute("INSERT INTO GlobalTasks (task, url) VALUES (?, ?)", (task_name, task_url))
    conn.commit()
    conn.close()

    return redirect(url_for('globaltasks'))  # Redirect back to the task setup page


@app.route('/user_signins/<int:user_id>')
def user_signins(user_id):
    with get_db_connection() as conn:
        c = conn.cursor()

        # Fetch user's country
        c.execute("SELECT country FROM Users WHERE id = ?", (user_id,))
        user_country_row = c.fetchone()

        if user_country_row:
            user_country = user_country_row[0]

            # Fetch national sign-ins (sign-ins from the user's country)
            c.execute("""
                SELECT SUM(Ranks.signins) 
                FROM Ranks 
                JOIN Users ON Ranks.user_id = Users.id 
                WHERE Users.country = ?
            """, (user_country,))
            national_signins = c.fetchone()[0] or 0

            # Fetch global sign-ins (sign-ins from other countries)
            c.execute("""
                SELECT SUM(Ranks.signins) 
                FROM Ranks 
                JOIN Users ON Ranks.user_id = Users.id 
                WHERE Users.country != ?
            """, (user_country,))
            global_signins = c.fetchone()[0] or 0

            # Fetch total number of national users
            c.execute("""
                SELECT COUNT(*) 
                FROM Users 
                WHERE country = ?
            """, (user_country,))
            total_national_users = c.fetchone()[0] or 0

            # Fetch total number of global users
            c.execute("""
                SELECT COUNT(*) 
                FROM Users 
                WHERE country != ?
            """, (user_country,))
            total_global_users = c.fetchone()[0] or 0

            return render_template(
                'user_signins.html',
                user=users,
                user_id=user_id,
                user_country=user_country,
                national_signins=national_signins,
                global_signins=global_signins,
                total_national_users=total_national_users,
                total_global_users=total_global_users,
            )
        else:
            return "User not found", 404




    
if __name__ == '__main__':
    app.run(debug=True)















    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import sqlite3
from datetime import datetime

# Database setup
def setup_database():
    conn = sqlite3.connect('attendance.db', check_same_thread=False)
    c = conn.cursor()

    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    country TEXT NOT NULL,
                    referral_id INTEGER,
                    FOREIGN KEY (referral_id) REFERENCES Users(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES Users(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Referrals (
                    user_id INTEGER, 
                    referred_by INTEGER,
                    FOREIGN KEY (user_id) REFERENCES Users(id),
                    FOREIGN KEY (referred_by) REFERENCES Users(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Ranks (
                    user_id INTEGER PRIMARY KEY, 
                    rank TEXT, 
                    signins INTEGER,
                    global_signins INTEGER DEFAULT 0,
                    global_rank TEXT,
                    bonus_claimed BOOLEAN DEFAULT 0,
                    bonus_amount REAL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES Users(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    country TEXT NOT NULL,
                    url TEXT,
                    completed BOOLEAN DEFAULT 0
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS GlobalTasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    url TEXT,
                    completed BOOLEAN DEFAULT 0
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS UserTasks (
                    user_id INTEGER NOT NULL,
                    task_id INTEGER NOT NULL,
                    globalTask_id INTEGER NOT NULL,
                    completed BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES Users(id),
                    FOREIGN KEY (task_id) REFERENCES Tasks(id),
                    FOREIGN KEY (globalTask_id) REFERENCES GlobalTasks(id),
                    PRIMARY KEY (user_id, task_id, globalTask_id)
                )''')

    conn.commit()
    return conn, c

conn, c = setup_database()

# Menu Builder
class MenuBuilder:
    @staticmethod
    def main_menu():
        keyboard = [
            [InlineKeyboardButton("🔑 Sign In", callback_data='signin'),
             InlineKeyboardButton("📨 Get Link", callback_data='referral')],
            [InlineKeyboardButton("📋 View Task", callback_data='view_task')]
        ]
        return InlineKeyboardMarkup(keyboard)

# Task Handler
async def assign_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id

    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    c.execute("SELECT country FROM Users WHERE id = ?", (user_id,))
    user_country = c.fetchone()[0]

    c.execute('''
        SELECT task_id FROM UserTasks 
        JOIN Tasks ON UserTasks.task_id = Tasks.id 
        WHERE user_id = ? AND UserTasks.completed = 0
    ''', (user_id,))
    task = c.fetchone()

    if not task:
        c.execute('''
            SELECT id, task, url FROM Tasks 
            WHERE completed = 0 AND country = ? 
            LIMIT 1
        ''', (user_country,))
        new_task = c.fetchone()

        if new_task:
            task_id, task_text, task_url = new_task
            c.execute('''
                INSERT INTO UserTasks (user_id, task_id, globalTask_id) 
                VALUES (?, ?, 0)
            ''', (user_id, task_id))
            conn.commit()
            await update.message.reply_text(f"Task assigned: {task_text}")
        else:
            await update.message.reply_text("No tasks are currently available.")
    else:
        await update.message.reply_text("You already have an active task.")
    conn.close()

# Task Viewing Handler
async def view_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id

    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        c.execute('''
            SELECT Tasks.id, Tasks.task, Tasks.url 
            FROM Tasks 
            JOIN UserTasks ON Tasks.id = UserTasks.task_id 
            WHERE UserTasks.user_id = ? AND UserTasks.completed = 0
        ''', (user_id,))
        tasks = c.fetchall()

        if tasks:
            keyboard = [
                [InlineKeyboardButton(f"{task_text}", url=task_url),
                 InlineKeyboardButton("Mark as Completed", callback_data=f'complete_task_{task_id}')]
                for task_id, task_text, task_url in tasks
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Here are your active tasks:", reply_markup=reply_markup)
        else:
            await query.edit_message_text("You have no active tasks.")

# Task Completion Handler
async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    task_id = int(query.data.split('_')[-1])

    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE UserTasks SET completed = 1 WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
        conn.commit()

# Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    username = user.username

    referred_by = int(context.args[0]) if context.args else None

    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()

        if referred_by:
            c.execute("INSERT OR IGNORE INTO Referrals (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
            c.execute("UPDATE Ranks SET signins = signins + 3 WHERE user_id = ?", (referred_by,))
            c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
            conn.commit()

        c.execute("INSERT OR IGNORE INTO Users (id, username) VALUES (?, ?)", (user_id, username))
        c.execute("INSERT OR IGNORE INTO Ranks (user_id, rank, signins) VALUES (?, ?, ?)", (user_id, 'Unranked', 0))
        conn.commit()

    await update.message.reply_text(f"Hello {username}! Welcome to the bot. Use /menu to see available options.")

# Sign-in Callback Handler
async def signin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id

    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M:%S")

    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM Attendance WHERE user_id = ? AND date = ?", (user_id, date))
        result = c.fetchone()

        if not result:
            c.execute("INSERT INTO Attendance (user_id, date, time) VALUES (?, ?, ?)", (user_id, date, time))
            c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
            conn.commit()
            await query.edit_message_text("You have successfully signed in.")
        else:
            await query.edit_message_text("You have already signed in today.")

# Referral Callback Handler
async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id

    referral_link = f"https://t.me/m2e2bot?start={user_id}"
    await query.edit_message_text(f"Here is your referral link: {referral_link}")

# Menu Command Handler
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Main Menu:", reply_markup=MenuBuilder.main_menu())

# Task Addition Helper Function
def add_task(task_text, task_url, country):
    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        c.execute('INSERT INTO Tasks (task, url, country) VALUES (?, ?, ?)', (task_text, task_url, country))
        conn.commit()

# Setting up the bot
application = Application.builder().token("7308553019:AAHKVgixYmGnXPkq4mQpcK9bUmwkH604BP8").build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("menu", menu))
application.add_handler(CommandHandler("task", assign_task))

application.add_handler(CallbackQueryHandler(signin_callback, pattern='signin'))
application.add_handler(CallbackQueryHandler(referral_callback, pattern='referral'))
application.add_handler(CallbackQueryHandler(view_task_callback, pattern='view_task'))
application.add_handler(CallbackQueryHandler(complete_task_callback, pattern=r'complete_task_\d+'))

application.run_polling()


















from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
def get_db_connection():
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, country FROM Users').fetchall()
    conn.close()
    return render_template('index.html', users=users)



# User details page
@app.route('/user_details/<int:user_id>')
def user_detail(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
    rank = conn.execute('SELECT * FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()
    tasks = conn.execute('''
        SELECT task, url FROM Tasks
        JOIN UserTasks ON Tasks.id = UserTasks.task_id
        WHERE UserTasks.user_id = ? AND UserTasks.completed = 0
    ''', (user_id,)).fetchall()
    conn.close()
    
    if user is None:
        return "User not found", 404
    
    return render_template('user_detail.html', user=user, rank=rank, tasks=tasks)


# Update user country page
@app.route('/update_country/<int:user_id>', methods=['GET', 'POST'])
def update_country(user_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        new_country = request.form['country']
        conn.execute('UPDATE Users SET country = ? WHERE id = ?', (new_country, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('user_detail', user_id=user_id))
    
    # Fetch current country for display and any other needed information
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user is None:
        return "User not found", 404

    countries = ["USA", "Canada", "UK", "Germany", "France", "India"]  # Add more as needed
    return render_template('update_country.html', user_id=user_id, countries=countries, current_country=user['country'])


if __name__ == "__main__":
    app.run(debug=True)







# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
# import sqlite3
# from datetime import datetime, timedelta

# # Database setup
# def setup_database():
#     conn = sqlite3.connect('attendance.db', check_same_thread=False)
#     c = conn.cursor()
    
#     # Create tables if they don't exist
#     c.execute('''CREATE TABLE IF NOT EXISTS Users (
#                     id INTEGER PRIMARY KEY, 
#                     username TEXT,
#                     country TEXT,
#                     age INTEGER)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Attendance (
#                     user_id INTEGER, 
#                     date TEXT, 
#                     time TEXT)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Ranks (
#                     user_id INTEGER PRIMARY KEY, 
#                     rank TEXT, 
#                     signins INTEGER,
#                     global_signins INTEGER DEFAULT 0,
#                     global_rank TEXT,
#                     bonus_claimed BOOLEAN DEFAULT 0,
#                     bonus_amount REAL DEFAULT 0)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Referrals (
#                     user_id INTEGER, 
#                     referred_by INTEGER)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Tasks (
#                     id INTEGER PRIMARY KEY, 
#                     task TEXT, 
#                     url TEXT, 
#                     completed INTEGER DEFAULT 0)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS UserTasks (
#                     user_id INTEGER, 
#                     task_id INTEGER, 
#                     completed INTEGER DEFAULT 0,
#                     FOREIGN KEY (task_id) REFERENCES Tasks (id),
#                     FOREIGN KEY (user_id) REFERENCES Users (id))''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS RankThresholds (
#                     rank TEXT PRIMARY KEY, 
#                     threshold INTEGER)''')
    



#     c.execute('''
#                CREATE TABLE IF NOT EXISTS BonusTask (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     user_id INTEGER NOT NULL,
#     country TEXT NOT NULL,
#     age INTEGER NOT NULL,
#     bonus REAL NOT NULL,
#     FOREIGN KEY (user_id) REFERENCES Users(id)
# );

#            ''')

    
    
#     conn.commit()
    
#     return conn, c

# conn, c = setup_database()

# # Rank thresholds
# RANKS = {
#     'Member': 1,
#     'Bonk': 120,
#     'Dorm': 200,
#     'Area': 250,
#     'City': 320,
#     'State': 400,
#     'Zonal': 500,
#     'National': 600,
#     'Regional': 700,
#     'Global': 1000,
#     'Universal': 1500
# }

# def calculate_rank(signins):
#     """Determine the user's rank based on the number of sign-ins."""
#     for rank, threshold in sorted(RANKS.items(), key=lambda x: x[1], reverse=True):
#         if signins >= threshold:
#             return rank
#     return 'Unranked'

# # Menu Builder
# class MenuBuilder:
#     @staticmethod
#     def main_menu():
#         signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
#         referral_button = InlineKeyboardButton("📨 Get  Link", callback_data='')
#         view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
#         keyboard = [
#             [signin_button, referral_button],
#             [view_task_button]
#         ]
        
#         return InlineKeyboardMarkup(keyboard)

# # Task Handler
# async def assign_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("SELECT task_id FROM UserTasks JOIN Tasks ON UserTasks.task_id = Tasks.id WHERE user_id = ? AND UserTasks.completed = 0", (user_id,))
#             task = c.fetchone()
            
#             if not task:
#                 c.execute("SELECT id, task, url FROM Tasks WHERE completed = 0 LIMIT 1")
#                 new_task = c.fetchone()
                
#                 if new_task:
#                     task_id, task_text, task_url = new_task
#                     c.execute("INSERT INTO UserTasks (user_id, task_id) VALUES (?, ?)", (user_id, task_id))
#                     conn.commit()
#                     await update.message.reply_text(f"Task assigned: {task_text}")
#                 else:
#                     await update.message.reply_text("No tasks are currently available.")
#             else:
#                 await update.message.reply_text(f"You already have an active task.")
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

# async def view_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
    
#     if query:
#         await query.answer()
        
#         user = query.from_user
#         user_id = user.id
        
#         with sqlite3.connect('attendance.db') as conn:
#             c = conn.cursor()
#             try:
#                 c.execute("SELECT Tasks.id, Tasks.task, Tasks.url FROM Tasks JOIN UserTasks ON Tasks.id = UserTasks.task_id WHERE UserTasks.user_id = ? AND UserTasks.completed = 0", (user_id,))
#                 tasks = c.fetchall()
                
#                 if tasks:
#                     keyboard = []
#                     for task_id, task_text, task_url in tasks:
#                         task_button = InlineKeyboardButton(f"{task_text}", url=task_url)
#                         complete_button = InlineKeyboardButton("Mark as Completed", callback_data=f'complete_task_{task_id}')
#                         keyboard.append([task_button, complete_button])
                    
#                     reply_markup = InlineKeyboardMarkup(keyboard)
#                     await query.edit_message_text("Here are your active tasks:", reply_markup=reply_markup)
#                 else:
#                     await query.edit_message_text("You have no active tasks.")
#             except sqlite3.OperationalError as e:
#                 await query.edit_message_text(f"Database error: {e}")
#     else:
#         await update.message.reply_text("Error: No callback query found. Please try again.")

# async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
    
#     task_id = int(query.data.split('_')[-1])
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("UPDATE UserTasks SET completed = 1 WHERE user_id = ? AND task_id = ?", (user_id, task_id))
#             conn.commit()
            
#             c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
#             c.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,))
#             signins = c.fetchone()[0]
#             rank = calculate_rank(signins)
#             c.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))
#             conn.commit()
            
#             await query.edit_message_text(f"Task completed! Your rank has been upgraded to '{rank}'.")
#         except sqlite3.OperationalError as e:
#             await query.edit_message_text(f"Database error: {e}")

# # View current rank handler
# async def view_rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("SELECT rank, signins, bonus_claimed, bonus_amount FROM Ranks WHERE user_id = ?", (user_id,))
#             rank_data = c.fetchone()
            
#             if rank_data:
#                 rank, signins, bonus_claimed, bonus_amount = rank_data
#                 bonus_message = f"Bonus claimed: {'Yes' if bonus_claimed else 'No'}, Bonus amount: {bonus_amount}" if bonus_claimed else "No bonus claimed."
#                 await update.message.reply_text(f"Your current rank is '{rank}' with {signins} sign-ins. {bonus_message}")
#             else:
#                 await update.message.reply_text("You have not signed in yet. Please sign in to receive your rank.")
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

# # Handler functions
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
#     username = user.username
    
#     referred_by = None
#     if context.args:
#         try:
#             referred_by = int(context.args[0])
#             with sqlite3.connect('attendance.db') as conn:
#                 c = conn.cursor()
#                 c.execute("INSERT OR IGNORE INTO Referrals (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
                
#                 if referred_by:
#                     c.execute("UPDATE Ranks SET signins = signins + 3 WHERE user_id = ?", (referred_by,))
#                     c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
#                     conn.commit()
#                     await update.message.reply_text(
#                         f"Hello {username}! You registered through a  and have received a bonus. "
#                         f"Your referrer has also been rewarded."
#                     )
#         except ValueError:
#             await update.message.reply_text("Invalid  ID. Please use a valid numeric ID.")

#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("INSERT OR IGNORE INTO Users (id, username) VALUES (?, ?)", (user_id, username))
#             c.execute("INSERT OR IGNORE INTO Ranks (user_id, rank, signins) VALUES (?, ?, ?)", (user_id, 'Unranked', 0))
#             conn.commit()
#             await assign_task(update, context)
#             await update.message.reply_text(
#                 f"Hello {username}! You are now registered.",
#                 reply_markup=MenuBuilder.main_menu()
#             )
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

# async def signin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
#     now = datetime.now()
#     today = now.date().isoformat()
#     time = now.strftime("%H:%M:%S")
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("SELECT * FROM Attendance WHERE user_id = ? AND date = ?", (user_id, today))
#             result = c.fetchone()
            
#             if not result:
#                 c.execute("INSERT INTO Attendance (user_id, date, time) VALUES (?, ?, ?)", (user_id, today, time))
#                 c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
#                 c.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,))
#                 signins = c.fetchone()[0]
#                 rank = calculate_rank(signins)
#                 c.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))
#                 conn.commit()
                
#                 await query.edit_message_text(
#                     f"✅ {user.username} signed in successfully at {time} on {today}. Your rank is now '{rank}'."
#                 )
#             else:
#                 await query.edit_message_text(f"⚠️ {user.username}, you have already signed in today.")
#         except sqlite3.OperationalError as e:
#             await query.edit_message_text(f"Database error: {e}")

# async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
    
#     referral_link = f"/start {user_id}"
    
#     await query.edit_message_text(f"Share this link to refer others: {referral_link}")

# # Main function
# def main():
#     app = Application.builder().token('7399507070:AAHqLQH5iqkpoJ4IZjJCm1X7Qb28RwrUTwI').build()
    
#     app.add_handler(CommandHandler('start', start))
#     app.add_handler(CommandHandler('rank', view_rank))
#     app.add_handler(CallbackQueryHandler(signin_callback, pattern='signin'))
#     app.add_handler(CallbackQueryHandler(referral_callback, pattern=''))
#     app.add_handler(CallbackQueryHandler(view_task_callback, pattern='view_task'))
#     app.add_handler(CallbackQueryHandler(complete_task_callback, pattern='complete_task_'))
    
#     app.run_polling()

# if __name__ == '__main__':
#     main()
















# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
# import sqlite3
# from datetime import datetime, timedelta

# # Database setup
# def setup_database():
#     conn = sqlite3.connect('attendance.db', check_same_thread=False)
#     c = conn.cursor()
    
#     # Create tables if they don't exist
#     c.execute('''CREATE TABLE IF NOT EXISTS Users (
#                     id INTEGER PRIMARY KEY, 
#                     username TEXT)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Attendance (
#                     user_id INTEGER, 
#                     date TEXT, 
#                     time TEXT)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Ranks (
#                     user_id INTEGER PRIMARY KEY, 
#                     rank TEXT, 
#                     signins INTEGER)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Referrals (
#                     user_id INTEGER, 
#                     referred_by INTEGER)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Tasks (
#                     id INTEGER PRIMARY KEY, 
#                     task TEXT, 
#                     url TEXT, 
#                     completed INTEGER DEFAULT 0)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS UserTasks (
#                     user_id INTEGER, 
#                     task_id INTEGER, 
#                     completed INTEGER DEFAULT 0,
#                     FOREIGN KEY (task_id) REFERENCES Tasks (id),
#                     FOREIGN KEY (user_id) REFERENCES Users (id))''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS RankThresholds (
#                     rank TEXT PRIMARY KEY, 
#                     threshold INTEGER)''')
    
#     # Alter tables to add new columns
#     try:
#         c.execute("ALTER TABLE Users ADD COLUMN country TEXT;")
#         c.execute("ALTER TABLE Ranks ADD COLUMN global_signins INTEGER DEFAULT 0;")
#         c.execute("ALTER TABLE Ranks ADD COLUMN global_rank TEXT;")  # Adding global_rank if needed
#     except sqlite3.OperationalError:
#         pass  # Ignore if the column already exists
    
#     conn.commit()
    
#     return conn, c


# conn, c = setup_database()

# # Rank thresholds
# RANKS = {
#         'Member': 1,
#         'Bonk': 120,
#         'Dorm': 200,
#         'Area': 250,
#         'City': 320,
#         'State': 400,
#         'Zonal': 500,
#         'National': 600,
#         'Regional': 700,
#         'Global': 1000,
#         'Universal': 1500
# }

# def calculate_rank(signins):
#     """Determine the user's rank based on the number of sign-ins."""
#     for rank, threshold in sorted(RANKS.items(), key=lambda x: x[1], reverse=True):
#         if signins >= threshold:
#             return rank
#     return 'Unranked'

# # Menu Builder
# class MenuBuilder:
#     @staticmethod
#     def main_menu():
#         signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
#         referral_button = InlineKeyboardButton("📨 Get  Link", callback_data='')
#         view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
#         keyboard = [
#             [signin_button, referral_button],
#             [view_task_button]
#         ]
        
#         return InlineKeyboardMarkup(keyboard)

# # Task Handler
# async def assign_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("SELECT task_id FROM UserTasks JOIN Tasks ON UserTasks.task_id = Tasks.id WHERE user_id = ? AND UserTasks.completed = 0", (user_id,))
#             task = c.fetchone()
            
#             if not task:
#                 c.execute("SELECT id, task, url FROM Tasks WHERE completed = 0 LIMIT 1")
#                 new_task = c.fetchone()
                
#                 if new_task:
#                     task_id, task_text, task_url = new_task
#                     c.execute("INSERT INTO UserTasks (user_id, task_id) VALUES (?, ?)", (user_id, task_id))
#                     conn.commit()
#                     await update.message.reply_text(f"Task assigned: {task_text}")
#                 else:
#                     await update.message.reply_text("No tasks are currently available.")
#             else:
#                 await update.message.reply_text(f"You already have an active task.")
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

# async def view_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
    
#     if query:
#         await query.answer()
        
#         user = query.from_user
#         user_id = user.id
        
#         with sqlite3.connect('attendance.db') as conn:
#             c = conn.cursor()
#             try:
#                 c.execute("SELECT Tasks.id, Tasks.task, Tasks.url FROM Tasks JOIN UserTasks ON Tasks.id = UserTasks.task_id WHERE UserTasks.user_id = ? AND UserTasks.completed = 0", (user_id,))
#                 tasks = c.fetchall()
                
#                 if tasks:
#                     keyboard = []
#                     for task_id, task_text, task_url in tasks:
#                         task_button = InlineKeyboardButton(f"{task_text}", url=task_url)
#                         complete_button = InlineKeyboardButton("Mark as Completed", callback_data=f'complete_task_{task_id}')
#                         keyboard.append([task_button, complete_button])
                    
#                     reply_markup = InlineKeyboardMarkup(keyboard)
#                     await query.edit_message_text("Here are your active tasks:", reply_markup=reply_markup)
#                 else:
#                     await query.edit_message_text("You have no active tasks.")
#             except sqlite3.OperationalError as e:
#                 await query.edit_message_text(f"Database error: {e}")
#     else:
#         await update.message.reply_text("Error: No callback query found. Please try again.")

# async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
    
#     task_id = int(query.data.split('_')[-1])
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("UPDATE UserTasks SET completed = 1 WHERE user_id = ? AND task_id = ?", (user_id, task_id))
#             conn.commit()
            
#             c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
#             c.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,))
#             signins = c.fetchone()[0]
#             rank = calculate_rank(signins)
#             c.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))
#             conn.commit()
            
#             await query.edit_message_text(f"Task completed! Your rank has been upgraded to '{rank}'.")
#         except sqlite3.OperationalError as e:
#             await query.edit_message_text(f"Database error: {e}")

# # View current rank handler
# async def view_rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("SELECT rank, signins FROM Ranks WHERE user_id = ?", (user_id,))
#             rank_data = c.fetchone()
            
#             if rank_data:
#                 rank, signins = rank_data
#                 await update.message.reply_text(f"Your current rank is '{rank}' with {signins} sign-ins.")
#             else:
#                 await update.message.reply_text("You have not signed in yet. Please sign in to receive your rank.")
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

# # Handler functions
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
#     username = user.username
    
#     referred_by = None
#     if context.args:
#         try:
#             referred_by = int(context.args[0])
#             with sqlite3.connect('attendance.db') as conn:
#                 c = conn.cursor()
#                 c.execute("INSERT OR IGNORE INTO Referrals (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
                
#                 if referred_by:
#                     c.execute("UPDATE Ranks SET signins = signins + 3 WHERE user_id = ?", (referred_by,))
#                     c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
#                     conn.commit()
#                     await update.message.reply_text(
#                         f"Hello {username}! You registered through a  and have received a bonus. "
#                         f"Your referrer has also been rewarded."
#                     )
#         except ValueError:
#             await update.message.reply_text("Invalid  ID. Please use a valid numeric ID.")

#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("INSERT OR IGNORE INTO Users (id, username) VALUES (?, ?)", (user_id, username))
#             c.execute("INSERT OR IGNORE INTO Ranks (user_id, rank, signins) VALUES (?, ?, ?)", (user_id, 'Unranked', 0))
#             conn.commit()
#             await assign_task(update, context)
#             await update.message.reply_text(
#                 f"Hello {username}! You are now registered.",
#                 reply_markup=MenuBuilder.main_menu()
#             )
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

# async def signin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
#     now = datetime.now()
#     today = now.date().isoformat()
#     time = now.strftime("%H:%M:%S")
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("SELECT * FROM Attendance WHERE user_id = ? AND date = ?", (user_id, today))
#             result = c.fetchone()
            
#             if not result:
#                 c.execute("INSERT INTO Attendance (user_id, date, time) VALUES (?, ?, ?)", (user_id, today, time))
#                 c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
#                 c.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,))
#                 signins = c.fetchone()[0]
#                 rank = calculate_rank(signins)
#                 c.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))
#                 conn.commit()
                
#                 await query.edit_message_text(
#                     f"✅ {user.username} signed in successfully at {time} on {today}. Your rank is now '{rank}'."
#                 )
#             else:
#                 await query.edit_message_text(f"⚠️ {user.username}, you have already signed in today.")
#         except sqlite3.OperationalError as e:
#             await query.edit_message_text(f"Database error: {e}")

# async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
    
#     referral_link = f"/start {user_id}"
    
#     await query.edit_message_text(f"Share this link to refer others: {referral_link}")

# # Main function
# def main():
#     app = Application.builder().token('7399507070:AAHqLQH5iqkpoJ4IZjJCm1X7Qb28RwrUTwI').build()
    
#     app.add_handler(CommandHandler('start', start))
#     app.add_handler(CommandHandler('rank', view_rank))
#     app.add_handler(CallbackQueryHandler(signin_callback, pattern='signin'))
#     app.add_handler(CallbackQueryHandler(referral_callback, pattern=''))
#     app.add_handler(CallbackQueryHandler(view_task_callback, pattern='view_task'))
#     app.add_handler(CallbackQueryHandler(complete_task_callback, pattern='complete_task_'))
    
#     app.run_polling()

# if __name__ == '__main__':
#     main()

































# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
# import sqlite3
# from datetime import datetime, timedelta

# # Database setup
# def setup_database():
#     conn = sqlite3.connect('attendance.db', check_same_thread=False)
#     c = conn.cursor()
    
#     # Create tables if they don't exist
#     c.execute('''CREATE TABLE IF NOT EXISTS Users (
#                     id INTEGER PRIMARY KEY, 
#                     username TEXT)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Attendance (
#                     user_id INTEGER, 
#                     date TEXT, 
#                     time TEXT)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Ranks (
#                     user_id INTEGER PRIMARY KEY, 
#                     rank TEXT, 
#                     signins INTEGER)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Referrals (
#                     user_id INTEGER, 
#                     referred_by INTEGER)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Tasks (
#                     id INTEGER PRIMARY KEY, 
#                     task TEXT, 
#                     url TEXT, 
#                     completed INTEGER DEFAULT 0)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS UserTasks (
#                     user_id INTEGER, 
#                     task_id INTEGER, 
#                     completed INTEGER DEFAULT 0,
#                     FOREIGN KEY (task_id) REFERENCES Tasks (id),
#                     FOREIGN KEY (user_id) REFERENCES Users (id))''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS RankThresholds (
#                     rank TEXT PRIMARY KEY, 
#                     threshold INTEGER)''')
    
#     conn.commit()
    
#     return conn, c

# conn, c = setup_database()

# # Rank thresholds
# RANKS = {
#         'Member': 1,
#         'Bonk': 120,
#         'Dorm': 200,
#         'Area': 250,
#         'City': 320,
#         'State': 400,
#         'Zonal': 500,
#         'National': 600,
#         'Regional': 700,
#         'Global': 1000,
#         'Universal': 1500
# }

# def calculate_rank(signins):
#     """Determine the user's rank based on the number of sign-ins."""
#     for rank, threshold in sorted(RANKS.items(), key=lambda x: x[1], reverse=True):
#         if signins >= threshold:
#             return rank
#     return 'Unranked'

# # Menu Builder
# class MenuBuilder:
#     @staticmethod
#     def main_menu():
#         signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
#         referral_button = InlineKeyboardButton("📨 Get  Link", callback_data='')
#         view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
#         keyboard = [
#             [signin_button, referral_button],
#             [view_task_button]
#         ]
        
#         return InlineKeyboardMarkup(keyboard)

# # Task Handler
# async def assign_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("SELECT task_id FROM UserTasks JOIN Tasks ON UserTasks.task_id = Tasks.id WHERE user_id = ? AND UserTasks.completed = 0", (user_id,))
#             task = c.fetchone()
            
#             if not task:
#                 c.execute("SELECT id, task, url FROM Tasks WHERE completed = 0 LIMIT 1")
#                 new_task = c.fetchone()
                
#                 if new_task:
#                     task_id, task_text, task_url = new_task
#                     c.execute("INSERT INTO UserTasks (user_id, task_id) VALUES (?, ?)", (user_id, task_id))
#                     conn.commit()
#                     await update.message.reply_text(f"Task assigned: {task_text}")
#                 else:
#                     await update.message.reply_text("No tasks are currently available.")
#             else:
#                 await update.message.reply_text(f"You already have an active task.")
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

# async def view_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
    
#     if query:
#         await query.answer()
        
#         user = query.from_user
#         user_id = user.id
        
#         with sqlite3.connect('attendance.db') as conn:
#             c = conn.cursor()
#             try:
#                 c.execute("SELECT Tasks.id, Tasks.task, Tasks.url FROM Tasks JOIN UserTasks ON Tasks.id = UserTasks.task_id WHERE UserTasks.user_id = ? AND UserTasks.completed = 0", (user_id,))
#                 tasks = c.fetchall()
                
#                 if tasks:
#                     keyboard = []
#                     for task_id, task_text, task_url in tasks:
#                         task_button = InlineKeyboardButton(f"{task_text}", url=task_url)
#                         complete_button = InlineKeyboardButton("Mark as Completed", callback_data=f'complete_task_{task_id}')
#                         keyboard.append([task_button, complete_button])
                    
#                     reply_markup = InlineKeyboardMarkup(keyboard)
#                     await query.edit_message_text("Here are your active tasks:", reply_markup=reply_markup)
#                 else:
#                     await query.edit_message_text("You have no active tasks.")
#             except sqlite3.OperationalError as e:
#                 await query.edit_message_text(f"Database error: {e}")
#     else:
#         await update.message.reply_text("Error: No callback query found. Please try again.")

# async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
    
#     task_id = int(query.data.split('_')[-1])
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("UPDATE UserTasks SET completed = 1 WHERE user_id = ? AND task_id = ?", (user_id, task_id))
#             conn.commit()
            
#             c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
#             c.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,))
#             signins = c.fetchone()[0]
#             rank = calculate_rank(signins)
#             c.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))
#             conn.commit()
            
#             await query.edit_message_text(f"Task completed! Your rank has been upgraded to '{rank}'.")
#         except sqlite3.OperationalError as e:
#             await query.edit_message_text(f"Database error: {e}")

# # View current rank handler
# async def view_rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("SELECT rank, signins FROM Ranks WHERE user_id = ?", (user_id,))
#             rank_data = c.fetchone()
            
#             if rank_data:
#                 rank, signins = rank_data
#                 await update.message.reply_text(f"Your current rank is '{rank}' with {signins} sign-ins.")
#             else:
#                 await update.message.reply_text("You have not signed in yet. Please sign in to receive your rank.")
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

# # Handler functions
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
#     username = user.username
    
#     referred_by = None
#     if context.args:
#         try:
#             referred_by = int(context.args[0])
#             with sqlite3.connect('attendance.db') as conn:
#                 c = conn.cursor()
#                 c.execute("INSERT OR IGNORE INTO Referrals (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
                
#                 if referred_by:
#                     c.execute("UPDATE Ranks SET signins = signins + 3 WHERE user_id = ?", (referred_by,))
#                     c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
#                     conn.commit()
#                     await update.message.reply_text(
#                         f"Hello {username}! You registered through a  and have received a bonus. "
#                         f"Your referrer has also been rewarded."
#                     )
#         except ValueError:
#             await update.message.reply_text("Invalid  ID. Please use a valid numeric ID.")

#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("INSERT OR IGNORE INTO Users (id, username) VALUES (?, ?)", (user_id, username))
#             c.execute("INSERT OR IGNORE INTO Ranks (user_id, rank, signins) VALUES (?, ?, ?)", (user_id, 'Unranked', 0))
#             conn.commit()
#             await assign_task(update, context)
#             await update.message.reply_text(
#                 f"Hello {username}! You are now registered.",
#                 reply_markup=MenuBuilder.main_menu()
#             )
#         except sqlite3.OperationalError as e:
#             await update.message.reply_text(f"Database error: {e}")

# async def signin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
#     current_time = datetime.now()
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             c.execute("SELECT date, time FROM Attendance WHERE user_id = ? ORDER BY date DESC, time DESC LIMIT 1", (user_id,))
#             last_signin = c.fetchone()
            
#             if last_signin:
#                 last_signin_time = datetime.strptime(f"{last_signin[0]} {last_signin[1]}", "%Y-%m-%d %H:%M:%S")
#                 time_diff = current_time - last_signin_time
                
#                 if time_diff < timedelta(hours=12):
#                     remaining_time = timedelta(hours=12) - time_diff
#                     await query.edit_message_text(f"You can sign in again in {remaining_time}.")
#                     return
            
#             date = current_time.strftime("%Y-%m-%d")
#             time = current_time.strftime("%H:%M:%S")
#             c.execute("INSERT INTO Attendance (user_id, date, time) VALUES (?, ?, ?)", (user_id, date, time))
            
#             c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
#             c.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,))
#             signins = c.fetchone()[0]
#             rank = calculate_rank(signins)
#             c.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))
#             conn.commit()
            
#             await query.edit_message_text(f"Attendance recorded for {date} at {time}. You now have {signins} sign-ins and your rank is '{rank}'.")
#         except sqlite3.OperationalError as e:
#             await query.edit_message_text(f"Database error: {e}")

# async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
#     referral_link = f"https://t.me/m2e2bot?start={user_id}"
#     await query.edit_message_text(f"Share this  link with your friends: {referral_link}")

# # Main function
# def main():
#     # Initialize the Application with your bot's token
#     application = Application.builder().token("7399507070:AAHqLQH5iqkpoJ4IZjJCm1X7Qb28RwrUTwI").build()
    
#     # Register command handlers
#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CommandHandler("view_rank", view_rank))
#     application.add_handler(CommandHandler("view_task", view_task_callback))
#     application.add_handler(CallbackQueryHandler(signin_callback, pattern='signin'))
#     application.add_handler(CallbackQueryHandler(referral_callback, pattern=''))
#     application.add_handler(CallbackQueryHandler(view_task_callback, pattern='view_task'))
#     application.add_handler(CallbackQueryHandler(complete_task_callback, pattern='complete_task_'))
    
#     # Run the bot until manually stopped
#     application.run_polling()

# if __name__ == '__main__':
#     main()













# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
# import sqlite3
# from datetime import datetime, timedelta

# # Set up database connection
# def setup_database():
#     conn = sqlite3.connect('attendance.db', check_same_thread=False)
#     c = conn.cursor()

#     # Create tables if they don't exist
#     c.execute('''CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY, username TEXT)''')
#     c.execute('''CREATE TABLE IF NOT EXISTS Attendance (user_id INTEGER, date TEXT, time TEXT)''')
#     c.execute('''CREATE TABLE IF NOT EXISTS Ranks (user_id INTEGER PRIMARY KEY, rank TEXT, signins INTEGER)''')
#     c.execute('''CREATE TABLE IF NOT EXISTS Referrals (user_id INTEGER, referred_by INTEGER)''')
#     c.execute('''CREATE TABLE IF NOT EXISTS Tasks (id INTEGER PRIMARY KEY, task TEXT, url TEXT, completed INTEGER DEFAULT 0)''')
#     c.execute('''CREATE TABLE IF NOT EXISTS UserTasks (user_id INTEGER, task_id INTEGER, FOREIGN KEY (task_id) REFERENCES Tasks (id))''')
#     c.execute('''CREATE TABLE IF NOT EXISTS RankThresholds (rank TEXT PRIMARY KEY, threshold INTEGER)''')
#     conn.commit()

#     return conn, c

# conn, c = setup_database()

# # Rank thresholds
# RANKS = {
#     'Bronze': 50,
#     'Silver': 100,
#     'Gold': 200,
#     'Platinum': 600
# }

# def calculate_rank(signins):
#     """Determine the user's rank based on the number of sign-ins."""
#     for rank, threshold in sorted(RANKS.items(), key=lambda x: x[1], reverse=True):
#         if signins >= threshold:
#             return rank
#     return 'Unranked'

# # Menu Builder
# class MenuBuilder:
#     @staticmethod
#     def main_menu():
#         # Create buttons
#         signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
#         referral_button = InlineKeyboardButton("📨 Get  Link", callback_data='')
#         view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')

#         # Arrange buttons in rows
#         keyboard = [
#             [signin_button, referral_button],  # Row 1
#             [view_task_button]  # Row 2
#         ]
        
#         # Create the markup
#         return InlineKeyboardMarkup(keyboard)

# # Task Handler
# async def assign_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id

#     # Check if the user already has an assigned task
#     c.execute("SELECT task_id FROM UserTasks JOIN Tasks ON UserTasks.task_id = Tasks.id WHERE user_id = ? AND completed = 0", (user_id,))
#     task = c.fetchone()

#     if not task:
#         # Assign a new task
#         c.execute("SELECT id, task, url FROM Tasks WHERE completed = 0 LIMIT 1")  # Get an available task
#         new_task = c.fetchone()

#         if new_task:
#             task_id, task_text, task_url = new_task
#             c.execute("INSERT INTO UserTasks (user_id, task_id) VALUES (?, ?)", (user_id, task_id))
#             conn.commit()
#             await update.message.reply_text(f"Task assigned: {task_text}")
#         else:
#             await update.message.reply_text("No tasks are currently available.")
#     else:
#         await update.message.reply_text(f"You already have an active task.")

# # Modified view_task_callback to list all available tasks
# async def view_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
    
#     if query is not None:
#         await query.answer()

#         user = query.from_user
#         user_id = user.id

#         # Retrieve all tasks for the user
#         c.execute("SELECT Tasks.id, Tasks.task, Tasks.url FROM Tasks JOIN UserTasks ON Tasks.id = UserTasks.task_id WHERE UserTasks.user_id = ? AND Tasks.completed = 0", (user_id,))
#         tasks = c.fetchall()

#         if tasks:
#             keyboard = []
#             for task_id, task_text, task_url in tasks:
#                 # Button to view the task URL
#                 task_button = InlineKeyboardButton(f"{task_text}", url=task_url)
#                 # Button to mark the task as completed
#                 complete_button = InlineKeyboardButton("Mark as Completed", callback_data=f'complete_task_{task_id}')
#                 # Add buttons to the keyboard layout
#                 keyboard.append([task_button, complete_button])

#             reply_markup = InlineKeyboardMarkup(keyboard)
#             await query.edit_message_text("Here are your active tasks:", reply_markup=reply_markup)
#         else:
#             await query.edit_message_text("You have no active tasks.")
#     else:
#         # Log the issue or inform the user in another way
#         await update.message.reply_text("Error: No callback query found. Please try again.")


# # async def view_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
# #     query = update.callback_query
# #     await query.answer()

# #     user = query.from_user
# #     user_id = user.id

# #     # Retrieve all tasks for the user
# #     c.execute("SELECT Tasks.id, Tasks.task, Tasks.url FROM Tasks JOIN UserTasks ON Tasks.id = UserTasks.task_id WHERE UserTasks.user_id = ? AND Tasks.completed = 0", (user_id,))
# #     tasks = c.fetchall()

# #     if tasks:
# #         keyboard = []
# #         for task_id, task_text, task_url in tasks:
# #             # Button to view the task URL
# #             task_button = InlineKeyboardButton(f"{task_text}", url=task_url)
# #             # Button to mark the task as completed
# #             complete_button = InlineKeyboardButton("Mark as Completed", callback_data=f'complete_task_{task_id}')
# #             # Add buttons to the keyboard layout
# #             keyboard.append([task_button, complete_button])

# #         reply_markup = InlineKeyboardMarkup(keyboard)
# #         await query.edit_message_text("Here are your active tasks:", reply_markup=reply_markup)
# #     else:
# #         await query.edit_message_text("You have no active tasks.")

# async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()

#     user = query.from_user
#     user_id = user.id

#     # Extract the task ID from the callback data
#     task_id = int(query.data.split('_')[-1])

#     # Mark the task as completed
#     c.execute("UPDATE Tasks SET completed = 1 WHERE id = ?", (task_id,))
#     c.execute("DELETE FROM UserTasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
#     conn.commit()

#     # Reward the user by upgrading their rank
#     c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
#     c.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,))
#     signins = c.fetchone()[0]
#     rank = calculate_rank(signins)
#     c.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))
#     conn.commit()

#     await query.edit_message_text(f"Task completed! Your rank has been upgraded to '{rank}'.")

# # View current rank handler
# async def view_rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id

#     # Retrieve the current rank and sign-ins for the user
#     c.execute("SELECT rank, signins FROM Ranks WHERE user_id = ?", (user_id,))
#     rank_data = c.fetchone()

#     if rank_data:
#         rank, signins = rank_data
#         await update.message.reply_text(f"Your current rank is '{rank}' with {signins} sign-ins.")
#     else:
#         await update.message.reply_text("You have not signed in yet. Please sign in to receive your rank.")

# # Handler functions
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
#     username = user.username

#     # Handle 
#     referred_by = None
#     if context.args:
#         referred_by = int(context.args[0])
#         c.execute("INSERT OR IGNORE INTO Referrals (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))

#     # Register user
#     c.execute("INSERT OR IGNORE INTO Users (id, username) VALUES (?, ?)", (user_id, username))
#     c.execute("INSERT OR IGNORE INTO Ranks (user_id, rank, signins) VALUES (?, ?, ?)", (user_id, 'Unranked', 0))
   
#     # Reward referrer and referred user
#     if referred_by:
#         c.execute("UPDATE Ranks SET signins = signins + 3 WHERE user_id = ?", (referred_by,))
#         c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
#         conn.commit()
#         await update.message.reply_text(
#             f"Hello {username}! You registered through a  and have received a bonus. "
#             f"Your referrer has also been rewarded."
#         )

#     # Assign a task to the new user
#     await assign_task(update, context)

#     # Send welcome message with the main menu
#     await update.message.reply_text(
#         f"Hello {username}! You are now registered.",
#         reply_markup=MenuBuilder.main_menu()
#     )

# async def signin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()

#     user = query.from_user
#     user_id = user.id
#     current_time = datetime.now()

#     # Check last sign-in time
#     c.execute("SELECT date, time FROM Attendance WHERE user_id = ? ORDER BY date DESC, time DESC LIMIT 1", (user_id,))
#     last_signin = c.fetchone()

#     if last_signin:
#         last_signin_time = datetime.strptime(f"{last_signin[0]} {last_signin[1]}", "%Y-%m-%d %H:%M:%S")
#         time_diff = current_time - last_signin_time

#         if time_diff < timedelta(hours=12):
#             remaining_time = timedelta(hours=12) - time_diff
#             await query.edit_message_text(f"You can sign in again in {remaining_time}.")
#             return

#     # Record sign-in
#     date = current_time.strftime("%Y-%m-%d")
#     time = current_time.strftime("%H:%M:%S")
#     c.execute("INSERT INTO Attendance (user_id, date, time) VALUES (?, ?, ?)", (user_id, date, time))
    
#     # Update sign-ins and rank
#     c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
#     c.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,))
#     signins = c.fetchone()[0]
#     rank = calculate_rank(signins)
#     c.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))
    
#     conn.commit()
#     await query.edit_message_text(f"Attendance recorded for {date} at {time}. You now have {signins} sign-ins and your rank is '{rank}'.")

# async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()

#     user = query.from_user
#     user_id = user.id
#     referral_link = f"https://t.me/m2e2bot?start={user_id}"
#     await query.edit_message_text(f"Share this  link with your friends: {referral_link}")

# # Main function
# def main():
#     # Initialize the Application with your bot's token
#     application = Application.builder().token("7399507070:AAHqLQH5iqkpoJ4IZjJCm1X7Qb28RwrUTwI").build()

#     # Register command handlers
#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CommandHandler("view_rank", view_rank))
#     application.add_handler(CommandHandler("view_task", view_task_callback))  # Ensure this command is registered
#     application.add_handler(CallbackQueryHandler(signin_callback, pattern='signin'))
#     application.add_handler(CallbackQueryHandler(referral_callback, pattern=''))
#     application.add_handler(CallbackQueryHandler(view_task_callback, pattern='view_task'))
#     application.add_handler(CallbackQueryHandler(complete_task_callback, pattern='complete_task_'))

#     # Run the bot until manually stopped
#     application.run_polling()

# if __name__ == '__main__':
#     main()






from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
def get_db_connection():
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    return conn

# User details page
@app.route('/user_details/<int:user_id>')
def user_details(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
    rank = conn.execute('SELECT * FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()
    tasks = conn.execute('''
        SELECT task, url FROM Tasks
        JOIN UserTasks ON Tasks.id = UserTasks.task_id
        WHERE UserTasks.user_id = ? AND UserTasks.completed = 0
    ''', (user_id,)).fetchall()
    conn.close()
    
    if user is None:
        return "User not found", 404
    
    return render_template('user_detail.html', user=user, rank=rank, tasks=tasks)

# # Update user country page
# @app.route('/update_country/<int:user_id>', methods=['GET', 'POST'])
# def update_country(user_id):
#     conn = get_db_connection()
    
#     if request.method == 'POST':
#         new_country = request.form['country']
#         conn.execute('UPDATE Users SET country = ? WHERE id = ?', (new_country, user_id))
#         conn.commit()
#         conn.close()
#         return redirect(url_for('user_details', user_id=user_id))
    
#     countries = ["USA", "Canada", "UK", "Germany", "France", "India"]  # Add more as needed
#     return render_template('update_country.html', user_id=user_id, countries=countries)



# Update user country page
@app.route('/update_country/<int:user_id>', methods=['GET', 'POST'])
def update_country(user_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        new_country = request.form['country']
        conn.execute('UPDATE Users SET country = ? WHERE id = ?', (new_country, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('user_details', user_id=user_id))
    
    # Fetch current country for display and any other needed information
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user is None:
        return "User not found", 404

    countries = ["USA", "Canada", "UK", "Germany", "France", "India"]  # Add more as needed
    return render_template('update_country.html', user_id=user_id, countries=countries, current_country=user['country'])


if __name__ == "__main__":
    app.run(debug=True)
