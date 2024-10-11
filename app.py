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
    """! Gets a new dictionary cursor for the database.
    If necessary, a new database connection is created here and used for all
    subsequent to getCursor().
    @param: None
    @return: (cursor) a new dictionary cursor
    """
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
    """! Get the current date from the database.
    @param: None
    @return: (datetime) current date
    """
    cursor = getCursor()        
    qstr = "select curr_date from curr_date;"  
    cursor.execute(qstr)        
    curr_date = cursor.fetchone()['curr_date']        
    return curr_date

def calculate_age(current_date, birth_date):
    """! Calculate the age based on the birth date.
    @param current_date (datetime): current date which is from the database
    @param birth_date (datetime): birth date of the animal
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
    """! Calculate total pasture (in kg DM) for a paddock based on area, growth rate and stock number.
    @param area (float): paddock area in hectares
    @param stock_num (int): number of animals in the paddock
    @param total_dm (float): total dry matter (in kg) in the paddock
    @param pasture_growth_rate (float): growth rate of pasture in kg DM/ha/day
    @param stock_consumption_rate (float): consumption rate of pasture by an animal in kg DM/day
    @return: (dict) total_dm, dm_per_ha
    """
    growth = area * pasture_growth_rate
    consumption = stock_num * stock_consumption_rate
    total_dm = total_dm + growth - consumption
    dm_per_ha = round(total_dm / area,2)
    return {'total_dm':total_dm, 'dm_per_ha':dm_per_ha}

def move_current_date():
    """! Move the current date to the next day. Store the new date in the database.
    @param: None
    @return: None
    """
    next_date = get_date() + timedelta(days=1)
    cursor = getCursor()
    qstr = "update curr_date set curr_date = %s;"
    qargs = (next_date, )
    cursor.execute(qstr, qargs)
    return

def paddock_mob_stock():
    """! Get the mob details with the stock in each mob and paddock details.
    @param: None
    @return: (dict) mob details with the stock in each mob and paddock details
    """
    cursor = getCursor()  
    qstr = """SELECT paddocks.id as paddock_id, paddocks.name as paddock_name, paddocks.area as paddock_area, paddocks.dm_per_ha as paddock_dm, paddocks.total_dm as paddock_total_dm, 
                mobs.id as mob_id, mobs.name as mob_name, 
                COUNT(stock.id) as stock_count, round(avg(stock.weight), 2) as avg_weight
                FROM paddocks
                LEFT JOIN mobs ON paddocks.id = mobs.paddock_id
                LEFT JOIN stock ON mobs.id = stock.mob_id
                GROUP BY paddocks.id, paddocks.name, paddocks.area, paddocks.dm_per_ha, paddocks.total_dm, mobs.name
                ORDER BY mobs.name;
            """
    cursor.execute(qstr) 
    table = cursor.fetchall() 
    return table

def update_paddocks(paddocks):
    """! Update the paddock details based on the pasture levels into the database.
    @param paddocks (dict): paddock details and stock count in each mob
    @return: None
    """
    cursor = getCursor() 
    for paddock in paddocks:
        new_totaldm_dmha = pasture_levels(paddock["paddock_area"], paddock["stock_count"], paddock["paddock_total_dm"], pasture_growth_rate, stock_consumption_rate)
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
    """! Reset data to original state.
    @param: None
    @return: (redirect) to the paddocks page
    """
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
    """! List the mob details (excludes the stock in each mob).
    @param: None
    @return: (dict) mob details, (datetime) current date
    """       
    mobs = paddock_mob_stock() 
    mobs = [mob for mob in mobs if mob["mob_name"] is not None]   
    curr_date = get_date()  
    return render_template("mobs.html", mobs=mobs, curr_date = curr_date)  

@app.route("/stocks")
def stocks():
    """! List the mobs, and the stock details which includes the stock in each mob.
    @param: None
    @return: (dict) stock details, (dict) mob details with the stock in each mob, (datetime) current date
    """
    curr_date = get_date()
    cursor = getCursor()        
    qstr = """select stock.id as stock_id, stock.mob_id as mob_id, stock.dob as stock_dob, stock.weight as stock_weight
                from stock
                order by stock.id;
            """ 
    cursor.execute(qstr)        
    stocks = cursor.fetchall()     
    for item in stocks:
        item['stock_age'] = calculate_age(curr_date, item['stock_dob'])
     
    mobs = paddock_mob_stock() 
    mobs = [mob for mob in mobs if mob["mob_name"] is not None]
    return render_template("stocks.html", stocks=stocks, mobs=mobs, curr_date = curr_date)

@app.route("/paddocks")
def paddocks():
    """! List paddock details.
    @param: None
    @return: (dict) paddock details, (datetime) current date
    """
    paddocks = paddock_mob_stock() 
    paddocks = sorted(paddocks, key=lambda x: x['paddock_name'])
    curr_date = get_date()
    return render_template("paddocks.html", paddocks=paddocks, curr_date = curr_date)  

@app.route("/move_mobs")
def move_mobs():
    """! List the mobs and paddocks which do not have any mobs.
    @param: None
    @return: (dict) mobs, (dict) paddock_no_mob, (datetime) current date
    """
    all_data = paddock_mob_stock()
    mobs = [mob for mob in all_data if mob["mob_name"] is not None]
    paddock_no_mob = [paddock for paddock in all_data if paddock["mob_name"] is None]
    paddock_no_mob = sorted(paddock_no_mob, key=lambda x: x['paddock_name'])
    curr_date = get_date()
    return render_template("move_mobs.html", mobs= mobs, paddock_no_mob = paddock_no_mob, curr_date = curr_date)

@app.route("/moving", methods=['POST'])
def moving():
    """! Move the mob to a new paddock.
    @param: None
    @return: (redirect) to the paddocks page
    """
    cursor = getCursor() 
    formvals = request.form
    qstr = "update mobs set paddock_id = %s where id = %s;"
    qargs = (formvals['paddock_id'], formvals['mob_id'])
    cursor.execute(qstr,qargs)
    return redirect(url_for('paddocks'))

@app.route('/paddocks_edit/<int:paddock_id>', methods=['GET'])
def edit_paddock(paddock_id):
    """! Display the form for editing an existing paddock.
    @param: None
    @return: render the paddock form template for editing
    """
    cursor = getCursor()
    qstr = """SELECT paddocks.id as paddock_id, paddocks.name as paddock_name, paddocks.area as paddock_area, paddocks.dm_per_ha as paddock_dm
                FROM paddocks WHERE id = %s
            """
    cursor.execute(qstr, (paddock_id,))
    paddock = cursor.fetchone()
    return render_template('paddocks_form.html', is_add=False, paddock=paddock)

@app.route('/update_paddock', methods=['POST'])
def update_paddock():
    """! Update the paddock details.
    @param: None
    @return: (redirect) to the paddocks page
    """
    cursor = getCursor() 
    formvals = request.form
    qstr = "update paddocks set name = %s, area = %s, dm_per_ha = %s, total_dm = %s where id = %s;"
    qargs = (formvals['paddock_name'], formvals['paddock_area'], formvals['paddock_dm'], round(float(formvals['paddock_area']) * float(formvals['paddock_dm']), 2), formvals['paddock_id'])
    cursor.execute(qstr,qargs)
    return redirect(url_for('paddocks'))

@app.route('/paddocks_add', methods=['POST'])
def paddocks_add():
    """! Display the form for adding a new paddock.
    @param: None
    @return: (redirect) to the paddocks page
    """
    return render_template('paddocks_form.html', is_add=True)

@app.route('/add_paddock', methods=['POST'])
def add_paddock():
    """! Add a new paddock.
    @param: None
    @return: (redirect) to the paddocks page
    """
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
    """! Delete a paddock.
    @param: None
    @return: (redirect) to the paddocks page
    """
    cursor = getCursor() 
    formvals = request.form
    qstr = """Delete from paddocks where id = %s;"""
    qargs = (formvals['paddock_id'], )
    cursor.execute(qstr, qargs)
    return redirect(url_for('paddocks'))

@app.route('/move_to_next_day', methods=['POST'])
def move_to_next_day():
    """! Move to the next day. Calculate the pasture levels and update the paddock details. Calculate the age of the stock.
    @param: None
    @return: (redirect) to the paddocks page
    """
    move_current_date()
    paddocks = paddock_mob_stock()
    update_paddocks(paddocks)
    return redirect(url_for('paddocks'))

