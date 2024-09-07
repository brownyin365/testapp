import secrets

# Generate a random key
secret_key = secrets.token_hex(24)  # 48 characters long, hex-encoded
print(secret_key)


# import sqlite3

# def check_user(user_id):
#     conn = sqlite3.connect('attendance.db')
#     conn.row_factory = sqlite3.Row
#     user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
#     print("User:", user)  # Check if user is found
#     conn.close()

# check_user(7047683797)  # Replace 1 with the actual user_id you want to test






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
                    bonus_amount REAL DEFAULT 0)''')      
      
    # Add these lines in setup_database() function
    c.execute('''CREATE TABLE IF NOT EXISTS Tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                description TEXT NOT NULL,
                assigned_to INTEGER,
                FOREIGN KEY (assigned_to) REFERENCES Users(id)
            )''')

    c.execute('''CREATE TABLE IF NOT EXISTS CompletedTasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                user_id INTEGER,
                completion_date TEXT,
                FOREIGN KEY (task_id) REFERENCES Tasks(id),
                FOREIGN KEY (user_id) REFERENCES Users(id)
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
        referral_stats_button = InlineKeyboardButton("📊 View Referral Stats", web_app={"url": f"https://945a-197-251-193-137.ngrok-free.app/referral_stats/{user_id}"})
        view_task_button = InlineKeyboardButton("📋 View Task", web_app={"url": f"https://945a-197-251-193-137.ngrok-free.app/tasks"})

        # Construct the deep link for the Mini App
        deep_link = f"user_details/{user_id}"
        
        # Use the proper URL scheme for the Telegram Mini App
        dashboard_button = InlineKeyboardButton(
            "📊 View Dashboard",
            web_app={
                "url": f"https://945a-197-251-193-137.ngrok-free.app/{deep_link}"
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
#                 "url": f"https://945a-197-251-193-137.ngrok-free.app/{deep_link}"
#             }
#         )

#         keyboard = [
#             [signin_button],
#             [referral_button],
#             [view_task_button],
#             [dashboard_button]
#         ]
        
#         return InlineKeyboardMarkup(keyboard)



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
    application.add_handler(CallbackQueryHandler(select_country_callback, pattern="select_country_"))
    
    application.run_polling()

if __name__ == "__main__":
    main()
























# from requests import session
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
# import sqlite3
# from datetime import datetime

# # Database setup
# def setup_database():
#     conn = sqlite3.connect('attendance.db', check_same_thread=False)
#     c = conn.cursor()
    
#     # Create tables if they don't exist
#     c.execute('''CREATE TABLE IF NOT EXISTS Users (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 username TEXT NOT NULL,
#                 country TEXT NOT NULL,
#                 referral_id INTEGER,
#                 FOREIGN KEY (referral_id) REFERENCES Users(id)
#             )''')

#     c.execute('''CREATE TABLE IF NOT EXISTS Attendance (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 user_id INTEGER NOT NULL,
#                 date TEXT NOT NULL,
#                 time TEXT NOT NULL,
#                 FOREIGN KEY (user_id) REFERENCES Users(id)
#             )''')
    
#     c.execute('''CREATE TABLE Referrals (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 referrer_id INTEGER,
#                 referred_id INTEGER,
#                 FOREIGN KEY (referrer_id) REFERENCES Users(id),
#                 FOREIGN KEY (referred_id) REFERENCES Users(id)
#             )''')
    
#     c.execute('''CREATE TABLE Signins (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 user_id INTEGER,
#                 signins INTEGER DEFAULT 10,
#                 FOREIGN KEY (user_id) REFERENCES Users(id)
#             )''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS Ranks (
#                     user_id INTEGER PRIMARY KEY, 
#                     rank TEXT, 
#                     signins INTEGER,
#                     global_signins INTEGER DEFAULT 0,
#                     global_rank TEXT,
#                     bonus_claimed BOOLEAN DEFAULT 0,
#                     bonus_amount REAL DEFAULT 0)''')        

#     c.execute('''CREATE TABLE IF NOT EXISTS Tasks (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 task TEXT NOT NULL,
#                 country TEXT NOT NULL,
#                 url TEXT,
#                 completed BOOLEAN DEFAULT 0
#             )''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS GlobalTasks (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 task TEXT NOT NULL,
#                 url TEXT,
#                 completed BOOLEAN DEFAULT 0
#             )''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS UserGlobalTasks (
#                 user_id INTEGER NOT NULL,
#                 globalTask_id INTEGER NOT NULL,
#                 completed BOOLEAN DEFAULT 0,
#                 FOREIGN KEY (user_id) REFERENCES Users(id),
#                 FOREIGN KEY (globalTask_id) REFERENCES GlobalTasks(id),
#                 PRIMARY KEY (user_id, globalTask_id)
#             )''')  
    

#     c.execute('''CREATE TABLE IF NOT EXISTS UserTasks (
#                 user_id INTEGER NOT NULL,
#                 task_id INTEGER NOT NULL,
#                 globalTask_id INTEGER NOT NULL,
#                 completed BOOLEAN DEFAULT 0,
#                 FOREIGN KEY (user_id) REFERENCES Users(id),
#                 FOREIGN KEY (task_id) REFERENCES Tasks(id),
#                 FOREIGN KEY (globalTask_id) REFERENCES GlobalTasks(id),
#                 PRIMARY KEY (user_id, task_id, globalTask_id)
#             )''')   


#     conn.commit()
#     return conn, c

# conn, c = setup_database()

# # Menu Builder
# # Menu Builder
# class MenuBuilder:
#     @staticmethod
#     def main_menu(user_id):
#         signin_button = InlineKeyboardButton("🔑 Sign In", callback_data='signin')
#         # referral_button = InlineKeyboardButton("📨 Get Referral Link", callback_data='referral')
#         # view_task_button = InlineKeyboardButton("📋 View Task", callback_data='view_task')
        
#         # Construct the deep link for the Mini App
#         deep_link = f"user_details/{user_id}"
        
#         # Use the proper URL scheme for the Telegram Mini App
#         dashboard_button = {
#                     "text": "📊 View Dashboard",
#                     "web_app": {
#                         "url": f"https://945a-197-251-193-137.ngrok-free.app/{deep_link}"
#                     }
#                 }

#         keyboard = [
#             [signin_button],
#             # [referral_button],
#             [dashboard_button]
#         ]
        
#         return InlineKeyboardMarkup(keyboard)

# # Task Handler
# async def assign_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
    
#     conn = sqlite3.connect('attendance.db')
#     c = conn.cursor()

#     # Fetch the user's country
#     c.execute("SELECT country FROM Users WHERE id = ?", (user_id,))
#     user_country = c.fetchone()[0]

#     # Fetch available tasks for the user's country
#     try:
#         c.execute('''
#             SELECT task_id FROM UserTasks 
#             JOIN Tasks ON UserTasks.task_id = Tasks.id 
#             WHERE user_id = ? AND UserTasks.completed = 0
#         ''', (user_id,))
#         task = c.fetchone()
        
#         if not task:
#             c.execute('''
#                 SELECT id, task, url FROM Tasks 
#                 WHERE completed = 0 AND country = ? 
#                 LIMIT 1
#             ''', (user_country,))
#             new_task = c.fetchone()
            
#             if new_task:
#                 task_id, task_text, task_url = new_task
#                 c.execute('''
#                     INSERT INTO UserTasks (user_id, task_id, globalTask_id) 
#                     VALUES (?, ?, NULL)
#                 ''', (user_id, task_id))
#                 conn.commit()
#                 await update.message.reply_text(f"Task assigned: {task_text}")
#             else:
#                 await update.message.reply_text("No tasks are currently available.")
#         else:
#             await update.message.reply_text("You already have an active task.")
#     except sqlite3.OperationalError as e:
#         await update.message.reply_text(f"Database error: {e}")
#     finally:
#         conn.close()

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
#             conn.commit()
            
#             await query.edit_message_text("Task completed! Your progress has been recorded.")
#         except sqlite3.OperationalError as e:
#             await query.edit_message_text(f"Database error: {e}")

# # Registration form for country selection
# async def registration_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     countries = ["Country1", "Country2"]  # Replace with actual country list
#     buttons = [InlineKeyboardButton(country, callback_data=f"select_country_{country}") for country in countries]
#     keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]  # Arrange buttons in rows of 2
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await update.message.reply_text("Please select your country:", reply_markup=reply_markup)

# # Handle country selection
# async def select_country_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
#     selected_country = query.data.split('_')[-1]  # Extract the selected country from callback data
    
#     with sqlite3.connect('attendance.db') as conn:
#         c = conn.cursor()
#         try:
#             # Update the user's country
#             c.execute("UPDATE Users SET country = ? WHERE id = ?", (selected_country, user_id))
            
#             # Award the user with 5 additional sign-ins
#             c.execute("UPDATE Ranks SET signins = signins + 5 WHERE user_id = ?", (user_id,))
            
#             conn.commit()
#             await query.edit_message_text(f"Country updated to: {selected_country}. You have been awarded 5 sign-ins. You can now proceed to the main menu with /menu.")
#         except sqlite3.OperationalError as e:
#             await query.edit_message_text(f"Database error: {e}")



# # Update the start command to include registration form

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


# async def signin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
    
#     user = query.from_user
#     user_id = user.id
    
#     date = datetime.now().strftime('%Y-%m-%d')
#     time = datetime.now().strftime('%H:%M:%S')
    
#     conn = sqlite3.connect('attendance.db')
#     c = conn.cursor()
    
#     try:
#         # Check if the user has already signed in today
#         c.execute("SELECT id FROM Attendance WHERE user_id = ? AND date = ?", (user_id, date))
#         existing_entry = c.fetchone()
        
#         if existing_entry:
#             await query.edit_message_text("You have already signed in today.")
#         else:
#             # Insert sign-in record
#             c.execute("INSERT INTO Attendance (user_id, date, time) VALUES (?, ?, ?)", (user_id, date, time))
#             conn.commit()
            
#             # Update rank or other relevant data
#             c.execute("UPDATE Ranks SET signins = signins + 1 WHERE user_id = ?", (user_id,))
#             conn.commit()
            
#             await query.edit_message_text("Sign-in successful! Your progress has been recorded.")
#     except sqlite3.OperationalError as e:
#         await query.edit_message_text(f"Database error: {e}")
#     finally:
#         conn.close()



# # async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
# #     query = update.callback_query
# #     await query.answer()
    
# #     user = query.from_user
# #     user_id = user.id
    
# #     referral_link = f"https://t.me/m2e2bot/register/{user_id}"
    
# #     await query.edit_message_text(f"Your referral link: {referral_link}")


# # Main menu command
# async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id

#     # Build the main menu with the user's ID
#     reply_markup = MenuBuilder.main_menu(user_id)
    
#     # Send the menu to the user
#     await update.message.reply_text("Main Menu", reply_markup=reply_markup)




# async def send_dashboard_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.message.from_user
#     user_id = user.id
    
#     # Construct the deep link URL for your Mini App
#     deep_link = f"user_detail_{user_id}"
    
#     # Send a message with a button that opens the Mini App page
#     keyboard = [
#         [InlineKeyboardButton("📊 View Your Dashboard", url=f"https://t.me/m2e2bot?start={deep_link}")]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await update.message.reply_text("Click below to view your dashboard:", reply_markup=reply_markup)



# # Command handlers setup
# def main():
#     application = Application.builder().token("7308553019:AAHKVgixYmGnXPkq4mQpcK9bUmwkH604BP8").build()

#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CommandHandler("menu", menu))
#     application.add_handler(CallbackQueryHandler(signin_callback, pattern="signin"))
#     # application.add_handler(CallbackQueryHandler(referral_callback, pattern="referral"))
#     application.add_handler(CallbackQueryHandler(view_task_callback, pattern="view_task"))
#     application.add_handler(CallbackQueryHandler(complete_task_callback, pattern="complete_task_"))
#     application.add_handler(CallbackQueryHandler(select_country_callback, pattern="select_country_"))
#     # application.add_handler(CallbackQueryHandler(dashboard_callback, pattern="dashboard"))
    
#     application.run_polling()

# if __name__ == "__main__":
#     main()





















