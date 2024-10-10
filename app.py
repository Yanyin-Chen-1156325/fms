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

def calculate_age(current_date, birth_date):
    """! Calculate the age of the animal based on the birth date.
    @param birth_date (datetime): birth date
    @return: (int) age
    """
    birth_date_t = birth_date.replace(year=current_date.year)
    age = 0
    if current_date >= birth_date_t:
        age = current_date.year - birth_date.year
    else:
        age = current_date.year - birth_date.year - 1
    return age

def pasture_levels(area, stock_num, total_dm, pasture_growth_rate, stock_consumption_rate):
    """
    Calculate total pasture (in kg DM) for a paddock based on area, growth rate and stock number.
    Arguments: area (ha), stock number, total DM (kg), pasture growth rate (kg DM/ha/day), stock_consumption rate (kg DM/animal/day) 
    """
    growth = area * pasture_growth_rate
    consumption = stock_num * stock_consumption_rate
    total_dm = total_dm + growth - consumption
    dm_per_ha = round(total_dm / area,2)
    return {'total_dm':total_dm, 'dm_per_ha':dm_per_ha}

def move_current_date():
    next_date = get_date() + timedelta(days=1)
    cursor = getCursor()
    qstr = "update curr_date set curr_date = %s;"
    qargs = (next_date, )
    cursor.execute(qstr, qargs)
    return

def mob_paddock_stock():
    cursor = getCursor()
    qstr = """select mobs.name as mob_name, paddocks.name as paddock_name, paddocks.id as paddock_id, paddocks.area as paddock_area, paddocks.total_dm as paddock_total_dm, count(stock.id) as mob_count, round(avg(stock.weight), 2) as avg_weight
                from mobs
                inner join stock on mobs.id = stock.mob_id
                inner join paddocks on mobs.paddock_id = paddocks.id
                group by mobs.name, paddocks.name, paddocks.id, paddocks.area, paddocks.total_dm
                order by mobs.name;
            """ 
    cursor.execute(qstr) 
    table = cursor.fetchall()
    return table

def mob_paddock():
    cursor = getCursor()  
    qstr = """SELECT paddocks.id as paddock_id, paddocks.name as paddock_name, paddocks.area as paddock_area, paddocks.dm_per_ha as paddock_dm, paddocks.total_dm as paddock_total_dm, 
                mobs.name as mob_name, COUNT(stock.id) as mob_count
                FROM paddocks
                LEFT JOIN mobs ON paddocks.id = mobs.paddock_id
                LEFT JOIN stock ON mobs.id = stock.mob_id
                GROUP BY paddocks.id, paddocks.name, paddocks.area, paddocks.dm_per_ha, paddocks.total_dm, mobs.name
                ORDER BY paddocks.name;
            """
    cursor.execute(qstr) 
    table = cursor.fetchall() 
    return table

def update_paddocks(paddocks):
    cursor = getCursor() 
    for paddock in paddocks:
        new_totaldm_dmha = pasture_levels(paddock["paddock_area"], paddock["mob_count"], paddock["paddock_total_dm"], pasture_growth_rate, stock_consumption_rate)
        qstr = "update paddocks set dm_per_ha = %s, total_dm = %s where id = %s;"
        qargs = (new_totaldm_dmha["dm_per_ha"], new_totaldm_dmha["total_dm"], paddock["paddock_id"])
        cursor.execute(qstr,qargs)
    return

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
    mobs = mob_paddock_stock()    
    curr_date = get_date()  
    return render_template("mobs.html", mobs=mobs, curr_date = get_date())  

@app.route("/stocks")
def stocks():
    curr_date = get_date()
    cursor = getCursor()        
    qstr = """select mobs.name as mob_name, stock.id as stock_id, stock.dob as stock_dob, stock.weight as stock_weight
                from mobs
                inner join stock on mobs.id = stock.mob_id
                order by 1,2;
            """ 
    cursor.execute(qstr)        
    stocks = cursor.fetchall()     
    for dict in stocks:
        dict['stock_age'] = calculate_age(curr_date, dict['stock_dob'])
     
    groups = mob_paddock_stock() 
    return render_template("stocks.html", stocks=stocks, groups=groups, curr_date = curr_date)

@app.route("/paddocks")
def paddocks():
    """List paddock details."""
    paddocks = mob_paddock() 
    curr_date = get_date()
    return render_template("paddocks.html", paddocks=paddocks, curr_date = curr_date)  

@app.route("/move_mobs")
def move_mobs():
    cursor = getCursor() 
    mobs = mob_paddock_stock()
    paddocks = mob_paddock()
    paddock_no_mob = [paddock for paddock in paddocks if paddock["mob_name"] is None]
    curr_date = get_date()
    return render_template("move_mobs.html", mobs= mobs, paddock_no_mob = paddock_no_mob, curr_date = curr_date)

@app.route("/moving", methods=['POST'])
def moving():
    cursor = getCursor() 
    formvals = request.form
    qstr = "update mobs set paddock_id = %s where id = %s;"
    qargs = (formvals['paddock_id'], formvals['mob_id'])
    cursor.execute(qstr,qargs)
    return redirect(url_for('paddocks'))

@app.route('/paddocks_edit', methods=['POST'])
def edit_paddock():
    paddock = request.form
    return render_template('paddocks_edit.html', paddock=paddock)

@app.route('/update_paddock', methods=['POST'])
def update_paddock():
    paddock_id = request.form['paddock_id']
    paddock_name = request.form['paddock_name']
    area = request.form['paddock_area']
    dm = request.form['paddock_dm']
    total_dm = round(float(area) * float(dm), 2)
    
    cursor = getCursor() 
    qstr = "update paddocks set name = %s, area = %s, dm_per_ha = %s, total_dm = %s where id = %s;"
    qargs = (paddock_name, area, dm, total_dm, paddock_id)
    cursor.execute(qstr,qargs)
    return redirect(url_for('paddocks'))

@app.route('/paddocks_add', methods=['POST'])
def paddocks_add():
    return render_template('paddocks_add.html')

@app.route('/add_paddock', methods=['POST'])
def add_paddock():
    cursor = getCursor() 
    formvals = request.form
    qstr = """Insert into paddocks(name, area, dm_per_ha, total_dm) 
                values(%s, %s, %s, %s);
            """
    qargs = (formvals['paddock_name'], float(formvals['paddock_area']), float(formvals['paddock_dm']), round(float(formvals['paddock_area']) * float(formvals['paddock_dm']), 2))
    cursor.execute(qstr,qargs)
    return redirect(url_for('paddocks'))

@app.route('/delete_paddock', methods=['POST'])
def delete_paddock():
    cursor = getCursor() 
    formvals = request.form
    qstr = """Delete from paddocks where id = %s;"""
    qargs = (formvals['paddock_id'], )
    cursor.execute(qstr, qargs)
    return redirect(url_for('paddocks'))

@app.route('/move_to_next_day', methods=['POST'])
def move_to_next_day():
    move_current_date()
    cursor = getCursor()
    paddocks = mob_paddock_stock()
    update_paddocks(paddocks)
    return redirect(url_for('paddocks'))

