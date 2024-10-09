from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from datetime import date, datetime, timedelta
import mysql.connector
import connect

####### Required for the reset function to work both locally and in PythonAnywhere
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'COMP636 S2'

start_date = datetime(2024,10,29)
pasture_growth_rate = 65    #kg DM/ha/day
stock_consumption_rate = 14 #kg DM/animal/day

db_connection = None
 
def getCursor():
    """Gets a new dictionary cursor for the database.
    If necessary, a new database connection is created here and used for all
    subsequent to getCursor()."""
    global db_connection
 
    if db_connection is None or not db_connection.is_connected():
        db_connection = mysql.connector.connect(user=connect.dbuser, \
            password=connect.dbpass, host=connect.dbhost,
            database=connect.dbname, autocommit=True)
       
    # cursor = db_connection.cursor(buffered=False)   # returns a list
    cursor = db_connection.cursor(dictionary=True, buffered=False)  # use a dictionary cursor if you prefer
    return cursor

####### New function - reads the date from the new database table
def get_date():
    cursor = getCursor()        
    qstr = "select curr_date from curr_date;"  
    cursor.execute(qstr)        
    curr_date = cursor.fetchone()['curr_date']        
    return curr_date

def calculate_age(birth_date):
    """! Calculate the age of the animal based on the birth date.
    @param birth_date (datetime): birth date
    @return: (int) age
    """
    current_date = get_date()
    birth_date_t = birth_date.replace(year=current_date.year)
    age = 0
    if current_date >= birth_date_t:
        age = current_date.year - birth_date.year
    else:
        age = current_date.year - birth_date.year - 1
    return age


####### Updated if statement with this line
@app.route("/")
def home():
    # This line:
    curr_date = get_date()
    # Replaces these lines:
    # if 'curr_date' not in session:
    #     session.update({'curr_date': start_date})
    return render_template("home.html", curr_date=curr_date)

####### New function to reset the simulation back to the beginning - replaces reset_date() and clear_date()
##  NOTE: This requires fms-reset.sql file to be in the same folder as app.py
@app.route("/reset")
def reset():
    """Reset data to original state."""
    THIS_FOLDER = Path(__file__).parent.resolve()
    with open(THIS_FOLDER / 'fms-reset.sql', 'r') as f:
        mqstr = f.read()
        for qstr in mqstr.split(";"):
            cursor = getCursor()
            cursor.execute(qstr)
    get_date()
    return redirect(url_for('paddocks'))  

@app.route("/mobs")
def mobs():
    """List the mob details (excludes the stock in each mob)."""
    cursor = getCursor()        
    qstr = """SELECT mobs.id as mob_name, paddocks.id as paddock_id, paddocks.name as paddock_name, paddocks.area as paddock_area 
            FROM mobs inner join paddocks on mobs.paddock_id = paddocks.id order by mobs.name;""" 
    cursor.execute(qstr)        
    mobs = cursor.fetchall()       
    return render_template("mobs.html", mobs=mobs)  

@app.route("/stocks")
def stocks():
    cursor = getCursor()        
    qstr = """select mobs.name as mob_name, stock.id as stock_id, stock.dob as stock_dob 
                from mobs
                inner join stock on mobs.id = stock.mob_id
                order by 1,2 ;
            """ 
    cursor.execute(qstr)        
    stocks = cursor.fetchall()     
    for dict in stocks:
        dict['stock_dob'] = calculate_age(dict['stock_dob'])

    qstr = """select mobs.name as mob_name, paddocks.name as paddock_name, count(stock.id) as mob_count, round(avg(stock.weight), 2) as avg_weight
                from mobs
                inner join stock on mobs.id = stock.mob_id
                inner join paddocks on mobs.paddock_id = paddocks.id
                group by mobs.name, paddocks.name
                order by 1
            """ 
    cursor.execute(qstr)
    groups = cursor.fetchall()  
    return render_template("stocks.html", stocks=stocks, groups=groups)

@app.route("/paddocks")
def paddocks():
    """List paddock details."""
    return render_template("paddocks.html")  


