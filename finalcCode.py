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
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Signins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                signins INTEGER DEFAULT 10,
                FOREIGN KEY (user_id) REFERENCES Users(id)
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Ranks (
                    user_id INTEGER PRIMARY KEY, 
                    rank TEXT, 
                    signins INTEGER,
                    global_signins INTEGER DEFAULT 0,
                    global_rank TEXT,
                    bonus_claimed BOOLEAN DEFAULT 0,
                    bonus_amount REAL DEFAULT 0
              )''')

    # c.execute('''CREATE TABLE IF NOT EXISTS Tasks (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             task TEXT NOT NULL,
    #             country TEXT NOT NULL,
    #             url TEXT,
    #             completed BOOLEAN DEFAULT 0,
    #             is_completed BOOLEAN DEFAULT 0
    #         )''')
    
    # c.execute('''CREATE TABLE IF NOT EXISTS GlobalTasks (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             task TEXT NOT NULL,
    #             url TEXT,
    #             completed BOOLEAN DEFAULT 0,
    #             is_completed BOOLEAN DEFAULT 0
    #         )''')
    
    # c.execute('''CREATE TABLE IF NOT EXISTS UserGlobalTasks (
    #             user_id INTEGER NOT NULL,
    #             globalTask_id INTEGER NOT NULL,
    #             completed BOOLEAN DEFAULT 0,
    #             FOREIGN KEY (user_id) REFERENCES Users(id),
    #             FOREIGN KEY (globalTask_id) REFERENCES GlobalTasks(id),
    #             PRIMARY KEY (user_id, globalTask_id)
    #         )''')  
    
    # c.execute('''CREATE TABLE IF NOT EXISTS UserTasks (
    #             user_id INTEGER NOT NULL,
    #             task_id INTEGER NOT NULL,
    #             globalTask_id INTEGER NOT NULL,
    #             completed BOOLEAN DEFAULT 0,
    #             FOREIGN KEY (user_id) REFERENCES Users(id),
    #             FOREIGN KEY (task_id) REFERENCES Tasks(id),
    #             PRIMARY KEY (user_id, task_id, globalTask_id)
    #         )''')  
    
    c.execute('''CREATE TABLE IF NOT EXISTS UserCompletedActivities (
                user_id INTEGER,
                activity_id INTEGER,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, activity_id),
                FOREIGN KEY (user_id) REFERENCES Users(id),
                FOREIGN KEY (activity_id) REFERENCES Activities(id)
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                points INTEGER NOT NULL
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS UserCompletedActivitiesNational (
                    user_id INTEGER,
                    nationalactivities_id INTEGER,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, nationalactivities_id),
                    FOREIGN KEY (user_id) REFERENCES Users(id),
                    FOREIGN KEY (nationalactivities_id) REFERENCES NationalActivities(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS NationalActivities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    country TEXT NOT NULL,
                    points INTEGER NOT NULL
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
        # view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        # view_task_button = InlineKeyboardButton(" 📋 View Task ", web_app={"url": f"https://6c55-197-251-193-137.ngrok-free.app/user_tasks/{user_id}"})
        referral_stats_button = InlineKeyboardButton("📊 View Referral Stats", web_app={"url": f"https://6c55-197-251-193-137.ngrok-free.app/referral_stats/{user_id}"})
        

        view_task_button = InlineKeyboardButton(
            "📋 View Task",
            web_app={"url": f"https://6c55-197-251-193-137.ngrok-free.app/user/{user_id}/tasks"}
        )


        # Construct the deep link for the Mini App
        deep_link = f"user_details/{user_id}"
        
        # Use the proper URL scheme for the Telegram Mini App
        dashboard_button = InlineKeyboardButton(
            "📊 View Dashboard",
            web_app={
                "url": f"https://6c55-197-251-193-137.ngrok-free.app/{deep_link}"
            }
        )

        keyboard = [
            [signin_button],
            [referral_button],
            [view_task_button],
            [referral_stats_button],
            [dashboard_button]
        ]
        
        return InlineKeyboardMarkup(keyboard)

# class MenuBuilder:
#     @staticmethod
#     def main_menu(user_id):
#         signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
#         referral_button = InlineKeyboardButton("📨 Get Referral Link", callback_data='referral')
#         view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')

        
#         # Construct the deep link for the Mini App
#         deep_link = f"user_details/{user_id}"
        
#         # Use the proper URL scheme for the Telegram Mini App
#         dashboard_button = InlineKeyboardButton(
#             "📊 View Dashboard",
#             web_app={
#                 "url": f"https://6c55-197-251-193-137.ngrok-free.app/{deep_link}"
#             }
#         )

#         keyboard = [
#             [signin_button],
#             [referral_button],
#             [view_task_button],
#             [dashboard_button]
#         ]
        
#         return InlineKeyboardMarkup(keyboard)

# Task Handler
async def assign_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    
    try:
        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()

        # Fetch the user's country
        c.execute("SELECT country FROM Users WHERE id = ?", (user_id,))
        user_country = c.fetchone()[0]

        # Fetch available tasks for the user's country
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
        
        try:
            with sqlite3.connect('attendance.db') as conn:
                c = conn.cursor()
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
    
    try:
        with sqlite3.connect('attendance.db') as conn:
            c = conn.cursor()
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
    
    try:
        with sqlite3.connect('attendance.db') as conn:
            c = conn.cursor()
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
    
    try:
        with sqlite3.connect('attendance.db') as conn:
            c = conn.cursor()
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

async def signin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M:%S')
    
    try:
        with sqlite3.connect('attendance.db') as conn:
            c = conn.cursor()
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
                c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
                conn.commit()
                
                await query.edit_message_text("Sign-in successful! Your progress has been recorded.")
    except sqlite3.OperationalError as e:
        await query.edit_message_text(f"Database error: {e}")

# Main menu command
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id

    # Build the main menu with the user's ID
    reply_markup = MenuBuilder.main_menu(user_id)
    
    # Send the menu to the user
    await update.message.reply_text("Main Menu", reply_markup=reply_markup)



async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    
    # Create a referral link
    referral_link = f"https://t.me/m2e2bot?start={user_id}"
    
    await update.message.reply_text(
        f"Invite your friends using this link: {referral_link}\nFor each successful referral, you will earn 10 sign-ins."
    )

async def start_with_referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    username = user.username
    
    # Check if there's a referral ID in the start command
    referral_id = context.args[0] if context.args else None
    
    try:
        with sqlite3.connect('attendance.db') as conn:
            c = conn.cursor()
            # Insert user into the Users table if not already present
            c.execute("INSERT OR IGNORE INTO Users (id, username, country, referral_id) VALUES (?, ?, '', ?)", (user_id, username, referral_id))
            c.execute("INSERT OR IGNORE INTO Ranks (user_id, rank, signins) VALUES (?, ?, ?)", (user_id, 'Unranked', 0))
            conn.commit()
            
            # Handle referral bonus
            if referral_id:
                # Check if the referrer exists
                c.execute("SELECT id FROM Users WHERE id = ?", (referral_id,))
                referrer = c.fetchone()
                
                if referrer:
                    # Award 10 sign-ins to the referrer
                    c.execute("INSERT INTO Referrals (referrer_id, referred_id) VALUES (?, ?)", (referral_id, user_id))
                    c.execute("UPDATE Ranks SET signins = signins + 10 WHERE user_id = ?", (referral_id,))
                    conn.commit()
                    
            await update.message.reply_text(
                f"Hello {username}! Welcome to the bot. Please complete your registration by selecting your country."
            )
            
            # Show the registration form
            await registration_form(update, context)
    except sqlite3.OperationalError as e:
        await update.message.reply_text(f"Database error: {e}")



# Command handlers setup
def main():
    application = Application.builder().token("7308553019:AAHKVgixYmGnXPkq4mQpcK9bUmwkH604BP8").build()

    application.add_handler(CommandHandler("start", start_with_referral))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CallbackQueryHandler(signin_callback, pattern="signin"))
    application.add_handler(CallbackQueryHandler(referral_callback, pattern="referral"))
    application.add_handler(CallbackQueryHandler(view_task_callback, pattern="view_task"))
    application.add_handler(CallbackQueryHandler(complete_task_callback, pattern="complete_task_"))
    application.add_handler(CallbackQueryHandler(select_country_callback, pattern="select_country_"))
    
    application.run_polling()

if __name__ == "__main__":
    main()






from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from datetime import datetime, timedelta


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
    
    return render_template('user_detail.html', user=user, rank=rank, tasks=tasks, remaining_time=remaining_time_str, referral_link=referral_link)


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


@app.route('/assign_task/<int:user_id>', methods=['POST'])
def assign_task(user_id):
    """Assign a new task to the user based on their country if they do not have an active task."""
    with get_db_connection() as conn:
        # Fetch the user's country
        user_country = conn.execute("SELECT country FROM Users WHERE id = ?", (user_id,)).fetchone()['country']

        # Check for existing tasks for this user
        existing_task = conn.execute("SELECT task_id FROM UserTasks WHERE user_id = ? AND completed = 0", (user_id,)).fetchone()

        if not existing_task:
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



# @app.route('/user/<int:user_id>/tasks')
# def user_tasks(user_id):
#     """Display all available tasks for the user based on their country."""
    
#     # Assuming `session` contains the currently logged-in user's ID
#     current_user_id = session.get('user_id')
    
#     # Redirect if the user is not logged in or if they are trying to access another user's tasks
#     if not current_user_id or current_user_id != user_id:
#         return "Unauthorized access.", 403

#     with get_db_connection() as conn:
#         # Fetch user information
#         user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
#         if not user:
#             return "User not found.", 404

#         user_country = user['country']
        
#         # Fetch country-specific tasks
#         tasks = conn.execute('SELECT * FROM Tasks WHERE completed = 0 AND country = ?', (user_country,)).fetchall()
        
#         # Fetch global tasks
#         global_tasks = conn.execute('SELECT * FROM GlobalTasks WHERE completed = 0').fetchall()
        
#         # Fetch user rank and sign-ins
#         rank = conn.execute('SELECT rank, signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()

#     return render_template('tasks.html', user=user, tasks=tasks, rank=rank, global_tasks=global_tasks)


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
    """Mark a task as completed for a specific user, update the user's rank, and clear the task for that user."""
    with get_db_connection() as conn:
        # Mark the task as completed for this user only
        conn.execute("UPDATE Tasks SET completed = 1 WHERE id = ?", (task_id,))
        
        # Remove the task from the user's task list
        conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        
        # Update the user's sign-ins by 2
        conn.execute("UPDATE Ranks SET signins = signins + 2 WHERE user_id = ?", (user_id,))
        signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
        rank = calculate_rank(signins)
        conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

        conn.commit()

    return redirect(url_for('user_tasks', user_id=user_id))


@app.route('/user/<int:user_id>/globalTask/<int:globalTask_id>/complete', methods=['POST'])
def complete_global_task(user_id, globalTask_id):
    """Mark a global task as completed for a specific user, update the user's rank, and clear the task for that user."""
    with get_db_connection() as conn:
        # Mark the global task as completed for this user only
        conn.execute("UPDATE GlobalTasks SET completed = 1 WHERE id = ?", (globalTask_id,))
        
        # Remove the global task from the user's task list
        conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND globalTask_id = ?", (user_id, globalTask_id))
        
        # Update the user's sign-ins by 5
        conn.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
        signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
        rank = calculate_rank(signins)
        conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

        conn.commit()

    return redirect(url_for('user_tasks', user_id=user_id))




# @app.route('/user/<int:user_id>/task/<int:task_id>/complete', methods=['POST'])
# def complete_task(user_id, task_id):
#     """Mark a task as completed for a specific user and update the user's rank."""
#     with get_db_connection() as conn:
#         # Mark the task as completed for this user only
#         conn.execute("UPDATE Tasks SET completed = 1 WHERE id = ? AND EXISTS (SELECT 1 FROM UserTasks WHERE user_id = ? AND task_id = ?)", 
#                      (task_id, user_id, task_id))
        
#         # Remove the task from the user's task list
#         conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        
#         # Update the user's sign-ins by 2
#         conn.execute("UPDATE Ranks SET signins = signins + 2 WHERE user_id = ?", (user_id,))
#         signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
#         rank = calculate_rank(signins)
#         conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

#         conn.commit()

#     return redirect(url_for('user_tasks', user_id=user_id))


# @app.route('/user/<int:user_id>/globalTask/<int:globalTask_id>/complete', methods=['POST'])
# def complete_global_task(user_id, globalTask_id):
#     """Mark a global task as completed for a specific user and update the user's rank."""
#     with get_db_connection() as conn:
#         # Mark the global task as completed for this user only
#         conn.execute("UPDATE GlobalTasks SET completed = 1 WHERE id = ? AND EXISTS (SELECT 1 FROM UserTasks WHERE user_id = ? AND globalTask_id = ?)", 
#                      (globalTask_id, user_id, globalTask_id))
        
#         # Remove the global task from the user's task list
#         conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND globalTask_id = ?", (user_id, globalTask_id))
        
#         # Update the user's sign-ins by 5
#         conn.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
#         signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
#         rank = calculate_rank(signins)
#         conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

#         conn.commit()

#     return redirect(url_for('user_tasks', user_id=user_id))


# @app.route('/user/<int:user_id>/task/<int:task_id>/complete', methods=['POST'])
# def complete_task(user_id, task_id):
#     """Mark a task as completed and update the user's rank."""
#     with get_db_connection() as conn:
#         conn.execute("UPDATE Tasks SET completed = 1 WHERE id = ?", (task_id,))
#         conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        
#         # Update the user's sign-ins by 2
#         conn.execute("UPDATE Ranks SET signins = signins + 2 WHERE user_id = ?", (user_id,))
#         signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
#         rank = calculate_rank(signins)
#         conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

#         conn.commit()

#     return redirect(url_for('user_tasks', user_id=user_id))


# @app.route('/user/<int:user_id>/globalTask/<int:globalTask_id>/complete', methods=['POST'])
# def complete_global_task(user_id, globalTask_id):
#     """Mark a global task as completed and update the user's rank."""
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


@app.route('/signin/<int:user_id>', methods=['POST'])
def signin(user_id):
    """Handle user sign-in and manage sign-in limits and bonuses."""
    with get_db_connection() as conn:
        last_signin = conn.execute('''
            SELECT date, time FROM Attendance
            WHERE user_id = ?
            ORDER BY date DESC, time DESC LIMIT 1
        ''', (user_id,)).fetchone()

        if last_signin:
            last_signin_time = datetime.strptime(f"{last_signin['date']} {last_signin['time']}", "%Y-%m-%d %H:%M:%S")
            time_diff = datetime.now() - last_signin_time
            if time_diff < timedelta(hours=12):
                remaining_time = timedelta(hours=12) - time_diff
                remaining_time_str = str(remaining_time).split('.')[0]
                return jsonify({"message": f"Please wait {remaining_time_str} before signing in again."}), 400
        
        # Record the sign-in
        now = datetime.now()
        conn.execute('''
            INSERT INTO Attendance (user_id, date, time)
            VALUES (?, ?, ?)
        ''', (user_id, now.date(), now.strftime("%H:%M:%S")))
        
        # Update sign-ins and rank
        conn.execute('UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?', (user_id,))
        signins = conn.execute('SELECT signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()['signins']
        rank = calculate_rank(signins)
        conn.execute('UPDATE Ranks SET rank = ? WHERE user_id = ?', (rank, user_id))
        
        conn.commit()

    return redirect(url_for('user_detail', user_id=user_id))


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
        



@app.route('/referral_stats/<int:user_id>')
def referral_stats(user_id):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()


    # Fetch referral statistics
    c.execute('''
        SELECT COUNT(*), SUM(R.signins) 
        FROM Referrals AS Rf
        JOIN Ranks AS R ON Rf.referred_id = R.user_id
        WHERE Rf.referrer_id = ?
    ''', (user_id,))
    result = c.fetchone()

    if result is None:
        total_referrals = 0
        total_signins_from_referrals = 0
    else:
        total_referrals, total_signins_from_referrals = result

        # Handle the case where SUM could be None
        total_signins_from_referrals = total_signins_from_referrals or 0

    conn.close()

    referral_link = f"https://t.me/m2e2bot?start={user_id}"
    
    return render_template(
        'referral_stats.html', 
        referral_link=referral_link, 
        total_referrals=total_referrals, 
        total_signins_from_referrals=total_signins_from_referrals
    )






@app.route('/add_activity', methods=['POST'])
def add_activity():
    description = request.form['description']
    points = int(request.form['points'])
    
    with get_db_connection() as conn:
        conn.execute('INSERT INTO Activities (description, points) VALUES (?, ?)', (description, points))
        conn.commit()
    
    return redirect(url_for('admin_dashboard'))





@app.route('/user/<int:user_id>/activities')
def user_activities(user_id):
    with get_db_connection() as conn:
        # Fetch activities that the user has not yet completed
        activities = conn.execute('''
            SELECT * FROM Activities 
            WHERE id NOT IN (
                SELECT activity_id FROM UserCompletedActivities WHERE user_id = ?
            )
        ''', (user_id,)).fetchall()
        
        # Fetch user information for display
        user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()

    return render_template('activities.html', user=user, activities=activities)

@app.route('/user/<int:user_id>/activity/<int:activity_id>/complete', methods=['POST'])
def complete_activity(user_id, activity_id):
    with get_db_connection() as conn:
        # Fetch points for the activity
        activity = conn.execute('SELECT points FROM Activities WHERE id = ?', (activity_id,)).fetchone()
        if activity is None:
            return "Activity not found", 404
        
        points = activity['points']
        
        # Check if the user has already completed the activity
        existing_completion = conn.execute('SELECT * FROM UserCompletedActivities WHERE user_id = ? AND activity_id = ?', (user_id, activity_id)).fetchone()
        
        if existing_completion is None:
            # Record the completion of the activity
            conn.execute('INSERT INTO UserCompletedActivities (user_id, activity_id) VALUES (?, ?)', (user_id, activity_id))
            
            # Update user's sign-ins or rewards
            conn.execute('UPDATE Ranks SET signins = signins + ? WHERE user_id = ?', (points, user_id))
        
        conn.commit()

    return redirect(url_for('user_activities', user_id=user_id))




@app.route('/admin/upload', methods=['GET', 'POST'])
def upload_activity():
    if request.method == 'POST':
        title = request.form['title']
        url = request.form['url']
        points = request.form['points']
        country = request.form['country']

        with get_db_connection() as conn:
            conn.execute('INSERT INTO NationalActivities (title, url, points, country) VALUES (?, ?, ?, ?)',
                         (title, url, points, country))
            conn.commit()

        return redirect(url_for('upload_activity'))  # Redirect back to the form or to an admin dashboard

    return render_template('upload_activity.html')




@app.route('/user/<int:user_id>/nationalactivities/<int:nationalactivities_id>/complete', methods=['POST'])
def complete_national_activity(user_id, nationalactivities_id):
    with get_db_connection() as conn:
        # Fetch the user's country
        user = conn.execute('SELECT country FROM Users WHERE id = ?', (user_id,)).fetchone()
        if user is None:
            return "User not found", 404
        
        user_country = user['country']
        
        # Fetch the activity and ensure it matches the user's country
        nationalactivities = conn.execute('SELECT * FROM NationalActivities WHERE id = ? AND country = ?', (nationalactivities_id, user_country)).fetchone()
        if nationalactivities is None:
            return "Activity not found or not available for your country", 404
        
        points = nationalactivities['points']

        # Update user's sign-ins or rewards
        conn.execute('UPDATE Ranks SET signins = signins + ? WHERE user_id = ?', (points, user_id))

        # Record the completion of the activity
        try:
            conn.execute('INSERT INTO UserCompletedActivitiesNational (user_id, nationalactivities_id) VALUES (?, ?)', (user_id, nationalactivities_id))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Activity already completed", 400

        return redirect(url_for('list_national_activities', user=user, user_id=user_id))



# @app.route('/user/<int:user_id>/nationalactivities/<int:nationalactivities_id>/complete', methods=['POST'])
# def complete_national_activity(user_id, nationalactivities_id):
#     with get_db_connection() as conn:
#         # Fetch the user's country
#         user = conn.execute('SELECT country FROM Users WHERE id = ?', (user_id,)).fetchone()
#         if user is None:
#             return "User not found", 404
        
#         user_country = user['country']
        
#         # Fetch the activity and ensure it matches the user's country
#         nationalactivities = conn.execute('SELECT * FROM NationalActivities WHERE id = ? AND country = ?', (nationalactivities_id, user_country)).fetchone()
#         if nationalactivities is None:
#             return "Activity not found or not available for your country", 404
        
#         points = nationalactivities['points']

#         # Update user's sign-ins or rewards
#         conn.execute('UPDATE Ranks SET signins = signins + ? WHERE user_id = ?', (points, user_id))

#         # Record the completion of the activity
#         try:
#             conn.execute('INSERT INTO UserCompletedActivitiesNational (user_id, nationalactivities_id) VALUES (?, ?)', (user_id, nationalactivities_id))
#             conn.commit()
#         except sqlite3.IntegrityError:
#             return "Activity already completed", 400

#         return redirect(url_for('user_activities', user_id=user_id))
    



# @app.route('/user/<int:user_id>/nationalactivities')
# def user_nationalactivities(user_id):
#     with get_db_connection() as conn:
#         # Fetch user and their country
#         user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
#         if user is None:
#             return "User not found", 404
        
#         user_country = user['country']

#         # Fetch activities available for the user's country and not yet completed by the user
#         activities = conn.execute('''
#             SELECT * FROM Nationalactivities 
#             WHERE country = ? 
#             AND id NOT IN (SELECT nationalactivities_id FROM UserCompletedActivitiesNational WHERE user_id = ?)
#         ''', (user_country, user_id)).fetchall()

#     return render_template('national_activities.html', user=user, activities=activities)




@app.route('/user/<int:user_id>/nationalactivities', methods=['GET'])
def list_national_activities(user_id):
    with get_db_connection() as conn:
        # Fetch the user's country
        user = conn.execute('SELECT country FROM Users WHERE id = ?', (user_id,)).fetchone()
        if user is None:
            return "User not found", 404
        
        user_country = user['country']

        # Fetch all activities available for the user's country
        nationalactivities = conn.execute('SELECT * FROM NationalActivities WHERE country = ?', (user_country,)).fetchall()

        # Fetch activities that the user has already completed
        completed_activities = conn.execute('SELECT nationalactivities_id FROM UserCompletedActivitiesNational WHERE user_id = ?', (user_id,)).fetchall()
        completed_activity_ids = [activity['nationalactivities_id'] for activity in completed_activities]

        user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()


    return render_template('national_activities.html', user=user, nationalactivities=nationalactivities, completed_activity_ids=completed_activity_ids)







# @app.route('/user/<int:user_id>/activities')
# def user_activities(user_id):
#     with get_db_connection() as conn:
#         activities = conn.execute('SELECT * FROM Activities').fetchall()
#         user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
#         if user is None:
#             return "User not found", 404

#     return render_template('activities.html', activities=activities, user=user)




# @app.route('/user/<int:user_id>/activity/<int:activity_id>/complete', methods=['POST'])
# def complete_activity(user_id, activity_id):
#     with get_db_connection() as conn:
#         # Fetch points for the activity
#         activity = conn.execute('SELECT points FROM Activities WHERE id = ?', (activity_id,)).fetchone()
#         if activity is None:
#             return "Activity not found", 404
        
#         points = activity['points']
        
#         # Check if the user has already completed the activity
#         existing_completion = conn.execute('SELECT * FROM UserCompletedActivities WHERE user_id = ? AND activity_id = ?', (user_id, activity_id)).fetchone()
        
#         if existing_completion is None:
#             # Record the completion of the activity
#             conn.execute('INSERT INTO UserCompletedActivities (user_id, activity_id) VALUES (?, ?)', (user_id, activity_id))
            
#             # Update user's sign-ins or rewards
#             conn.execute('UPDATE Ranks SET signins = signins + ? WHERE user_id = ?', (points, user_id))
            
#             # Remove the user from the activity list
#             conn.execute('DELETE FROM UserActivities WHERE user_id = ? AND activity_id = ?', (user_id, activity_id))
            
#             # Optionally, set the activity as completed in the Activities table
#             conn.execute('UPDATE Activities SET is_completed = 1 WHERE id = ?', (activity_id,))
        
#         conn.commit()

#     return redirect(url_for('user_activities', user_id=user_id))

# @app.route('/user/<int:user_id>/activity/<int:activity_id>/complete', methods=['POST'])
# def complete_activity(user_id, activity_id):
#     with get_db_connection() as conn:
#         # Fetch points for the activity
#         activity = conn.execute('SELECT points FROM Activities WHERE id = ?', (activity_id,)).fetchone()
#         if activity is None:
#             return "Activity not found", 404
        
#         points = activity['points']
        
#         # Update user's sign-ins or rewards
#         conn.execute('UPDATE Ranks SET signins = signins + ? WHERE user_id = ?', (points, user_id))
        
#         # Optionally, record the completion of the activity
#         conn.execute('INSERT INTO UserCompletedActivities (user_id, activity_id) VALUES (?, ?)', (user_id, activity_id))
        
#         # Remove the user from the activity list
#         # conn.execute('DELETE FROM Activities WHERE user_id = ? AND activity_id = ?', (user_id, activity_id))
        
#         conn.commit()

#     return redirect(url_for('user_activities', user_id=user_id))



# @app.route('/user/<int:user_id>/activity/<int:activity_id>/complete', methods=['POST'])
# def complete_activity(user_id, activity_id):
#     with get_db_connection() as conn:
#         # Fetch points for the activity
#         activity = conn.execute('SELECT points FROM Activities WHERE id = ?', (activity_id,)).fetchone()
#         if activity is None:
#             return "Activity not found", 404
        
#         points = activity['points']
        
#         # Update user's sign-ins or rewards
#         conn.execute('UPDATE Ranks SET signins = signins + ? WHERE user_id = ?', (points, user_id))
        
#         # Optionally, record the completion of the activity
#         conn.execute('INSERT INTO UserCompletedActivities (user_id, activity_id) VALUES (?, ?)', (user_id, activity_id))
        
#         conn.commit()

#     return redirect(url_for('user_activities', user_id=user_id))


if __name__ == '__main__':
    app.run(debug=True)

































from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from datetime import datetime, timedelta


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
    
    return render_template('user_detail.html', user=user, rank=rank, tasks=tasks, remaining_time=remaining_time_str, referral_link=referral_link)


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


@app.route('/assign_task/<int:user_id>', methods=['POST'])
def assign_task(user_id):
    """Assign a new task to the user based on their country if they do not have an active task."""
    with get_db_connection() as conn:
        # Fetch the user's country
        user_country = conn.execute("SELECT country FROM Users WHERE id = ?", (user_id,)).fetchone()['country']

        # Check for existing tasks for this user
        existing_task = conn.execute("SELECT task_id FROM UserTasks WHERE user_id = ? AND completed = 0", (user_id,)).fetchone()

        if not existing_task:
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
    """Mark a task as completed for a specific user, update the user's rank, and clear the task for that user."""
    with get_db_connection() as conn:
        # Mark the task as completed for this user only
        conn.execute("UPDATE Tasks SET completed = 1 WHERE id = ?", (task_id,))
        
        # Remove the task from the user's task list
        conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        
        # Update the user's sign-ins by 2
        conn.execute("UPDATE Ranks SET signins = signins + 2 WHERE user_id = ?", (user_id,))
        signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
        rank = calculate_rank(signins)
        conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

        conn.commit()

    return redirect(url_for('user_tasks', user_id=user_id))


@app.route('/user/<int:user_id>/globalTask/<int:globalTask_id>/complete', methods=['POST'])
def complete_global_task(user_id, globalTask_id):
    """Mark a global task as completed for a specific user, update the user's rank, and clear the task for that user."""
    with get_db_connection() as conn:
        # Mark the global task as completed for this user only
        conn.execute("UPDATE GlobalTasks SET completed = 1 WHERE id = ?", (globalTask_id,))
        
        # Remove the global task from the user's task list
        conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND globalTask_id = ?", (user_id, globalTask_id))
        
        # Update the user's sign-ins by 5
        conn.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
        signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
        rank = calculate_rank(signins)
        conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

        conn.commit()

    return redirect(url_for('user_tasks', user_id=user_id))




# @app.route('/user/<int:user_id>/task/<int:task_id>/complete', methods=['POST'])
# def complete_task(user_id, task_id):
#     """Mark a task as completed for a specific user and update the user's rank."""
#     with get_db_connection() as conn:
#         # Mark the task as completed for this user only
#         conn.execute("UPDATE Tasks SET completed = 1 WHERE id = ? AND EXISTS (SELECT 1 FROM UserTasks WHERE user_id = ? AND task_id = ?)", 
#                      (task_id, user_id, task_id))
        
#         # Remove the task from the user's task list
#         conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        
#         # Update the user's sign-ins by 2
#         conn.execute("UPDATE Ranks SET signins = signins + 2 WHERE user_id = ?", (user_id,))
#         signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
#         rank = calculate_rank(signins)
#         conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

#         conn.commit()

#     return redirect(url_for('user_tasks', user_id=user_id))


# @app.route('/user/<int:user_id>/globalTask/<int:globalTask_id>/complete', methods=['POST'])
# def complete_global_task(user_id, globalTask_id):
#     """Mark a global task as completed for a specific user and update the user's rank."""
#     with get_db_connection() as conn:
#         # Mark the global task as completed for this user only
#         conn.execute("UPDATE GlobalTasks SET completed = 1 WHERE id = ? AND EXISTS (SELECT 1 FROM UserTasks WHERE user_id = ? AND globalTask_id = ?)", 
#                      (globalTask_id, user_id, globalTask_id))
        
#         # Remove the global task from the user's task list
#         conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND globalTask_id = ?", (user_id, globalTask_id))
        
#         # Update the user's sign-ins by 5
#         conn.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
#         signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
#         rank = calculate_rank(signins)
#         conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

#         conn.commit()

#     return redirect(url_for('user_tasks', user_id=user_id))


# @app.route('/user/<int:user_id>/task/<int:task_id>/complete', methods=['POST'])
# def complete_task(user_id, task_id):
#     """Mark a task as completed and update the user's rank."""
#     with get_db_connection() as conn:
#         conn.execute("UPDATE Tasks SET completed = 1 WHERE id = ?", (task_id,))
#         conn.execute("DELETE FROM UserTasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        
#         # Update the user's sign-ins by 2
#         conn.execute("UPDATE Ranks SET signins = signins + 2 WHERE user_id = ?", (user_id,))
#         signins = conn.execute("SELECT signins FROM Ranks WHERE user_id = ?", (user_id,)).fetchone()['signins']
        
#         rank = calculate_rank(signins)
#         conn.execute("UPDATE Ranks SET rank = ? WHERE user_id = ?", (rank, user_id))

#         conn.commit()

#     return redirect(url_for('user_tasks', user_id=user_id))


# @app.route('/user/<int:user_id>/globalTask/<int:globalTask_id>/complete', methods=['POST'])
# def complete_global_task(user_id, globalTask_id):
#     """Mark a global task as completed and update the user's rank."""
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


@app.route('/signin/<int:user_id>', methods=['POST'])
def signin(user_id):
    """Handle user sign-in and manage sign-in limits and bonuses."""
    with get_db_connection() as conn:
        last_signin = conn.execute('''
            SELECT date, time FROM Attendance
            WHERE user_id = ?
            ORDER BY date DESC, time DESC LIMIT 1
        ''', (user_id,)).fetchone()

        if last_signin:
            last_signin_time = datetime.strptime(f"{last_signin['date']} {last_signin['time']}", "%Y-%m-%d %H:%M:%S")
            time_diff = datetime.now() - last_signin_time
            if time_diff < timedelta(hours=12):
                remaining_time = timedelta(hours=12) - time_diff
                remaining_time_str = str(remaining_time).split('.')[0]
                return jsonify({"message": f"Please wait {remaining_time_str} before signing in again."}), 400
        
        # Record the sign-in
        now = datetime.now()
        conn.execute('''
            INSERT INTO Attendance (user_id, date, time)
            VALUES (?, ?, ?)
        ''', (user_id, now.date(), now.strftime("%H:%M:%S")))
        
        # Update sign-ins and rank
        conn.execute('UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?', (user_id,))
        signins = conn.execute('SELECT signins FROM Ranks WHERE user_id = ?', (user_id,)).fetchone()['signins']
        rank = calculate_rank(signins)
        conn.execute('UPDATE Ranks SET rank = ? WHERE user_id = ?', (rank, user_id))
        
        conn.commit()

    return redirect(url_for('user_', user_id=user_id))


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
        






@app.route('/referral_stats/<int:user_id>')
def referral_stats(user_id):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()

    # Fetch referral statistics
    c.execute('''
        SELECT COUNT(*), SUM(R.signins) 
        FROM Referrals AS Rf
        JOIN Ranks AS R ON Rf.referred_id = R.user_id
        WHERE Rf.referrer_id = ?
    ''', (user_id,))
    result = c.fetchone()

    if result is None:
        total_referrals = 0
        total_signins_from_referrals = 0
    else:
        total_referrals, total_signins_from_referrals = result

        # Handle the case where SUM could be None
        total_signins_from_referrals = total_signins_from_referrals or 0

    conn.close()

    referral_link = f"https://t.me/m2e2bot?start={user_id}"
    
    return render_template(
        'referral_stats.html', 
        user=user,
        referral_link=referral_link, 
        total_referrals=total_referrals, 
        total_signins_from_referrals=total_signins_from_referrals
    )



if __name__ == '__main__':
    app.run(debug=True)




# Final code clean 
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
        # view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
        # Construct the deep link for the Mini App
        deep_link = f"user_details/{user_id}"
        
        # Use the proper URL scheme for the Telegram Mini App
        dashboard_button = {
                    "text": "📊 View Dashboard",
                    "web_app": {
                        "url": f"https://bddf-197-251-193-137.ngrok-free.app/{deep_link}"
                    }
                }

        keyboard = [
            [signin_button],
            [referral_button],
            [dashboard_button]
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
    
    referral_link = f"https://t.me/m2e2bot/register/{user_id}"
    
    await query.edit_message_text(f"Your referral link: {referral_link}")


# Main menu command
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id

    # Build the main menu with the user's ID
    reply_markup = MenuBuilder.main_menu(user_id)
    
    # Send the menu to the user
    await update.message.reply_text("Main Menu", reply_markup=reply_markup)




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


@app.route('/')
def index():
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, country FROM Users').fetchall()
    conn.close()
    return render_template('index.html', users=users)


# @app.route('/')
# def index():
#     """Display all users."""
#     with get_db_connection() as conn:
#         user_id = session.get('user_id')
#         if user_id:
#             user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
#         else:
#             user = None
#     return render_template('index.html', user=user)



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
