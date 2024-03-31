"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import json
import os
  # accessible as a variable in homepage.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from flask import Flask, request, render_template, g, redirect, Response, url_for
from datetime import datetime

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


DATABASE_USERNAME = "sz3120"
DATABASE_PASSWRD = "zelendubrovina"
DATABASE_HOST = "35.212.75.104" # change to 34.28.53.86 if you used database 2 for part 2
DATABASEURI = f"postgresql://sz3120:zelendubrovina@35.212.75.104/proj1part2"
item_unique_id = 0
set_payment_id = 14
set_order_id = 14
set_customer_id = 16

#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
with engine.connect() as conn:
	create_table_command = """
	CREATE TABLE IF NOT EXISTS test (
		id serial,
		name text
	)
	"""
	res = conn.execute(text(create_table_command))
	insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
	res = conn.execute(text(insert_table_command))
	# you need to commit for create, insert, update queries to reflect
	conn.commit()


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


#
# @app.route is a decorator around homepage() that means:
#   run homepage() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def user_signup():
    return render_template('signup.html')

@app.route('/login')
def user_login():
    return render_template('login.html')

def homepage_info():
    select_query = "SELECT restaurant_id, restaurant_name FROM RESTAURANTS"
    cursor = g.conn.execute(text(select_query))
    restaurants = []
    for result in cursor:
        restaurant_id, restaurant_name = result
        restaurants.append({"id": restaurant_id, "name": restaurant_name})
    cursor.close()
    return restaurants

@app.route('/returning_user', methods=['POST'])
def returning_user():
    phone_number = request.form.get('phone_number')
    select_query = "SELECT customer_id FROM customers WHERE phone_number = :phone_number"
    cursor = g.conn.execute(text(select_query), {"phone_number": phone_number})

    try:
        customer_id = cursor.fetchone()[0]
        print("LOOP!")
        cursor.close()
        restaurants = []
        restaurants = homepage_info()
        return render_template('homepage.html', restaurants=restaurants, customer_id=customer_id)

    except TypeError:
        result = None
        error = "Hmmm, it seems like you don't have an account! Please double check your phone number"
        return render_template('login.html', error=error)





@app.route('/new_user_registration', methods=['POST'])
def user_registration():
    phone_number = request.form.get('phone_number')
    select_query = "SELECT customer_id FROM customers WHERE phone_number = :phone_number"
    cursor = g.conn.execute(text(select_query), {"phone_number": phone_number})


    try:
        customer_id = cursor.fetchone()[0]
        cursor.close()
        message = "It seems like you already have an account! Please click here to log in: "
        show_button = True
        return render_template("signup.html", show_button=show_button, message=message)

    except TypeError:
        show_button = False
        global set_customer_id
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email_address = request.form.get('email_address')
        customer_since = datetime.now().date()
        customer_id = "C" + str(set_customer_id)
        set_customer_id += 1

        insert_query = """
        INSERT INTO customers (customer_id, first_name, last_name, email_address, phone_number, customer_since)
        VALUES (:customer_id, :first_name, :last_name, :email_address, :phone_number, :customer_since)
        """
        g.conn.execute(text(insert_query), {"customer_id": customer_id, "first_name": first_name, "last_name": last_name, "email_address": email_address, "phone_number": phone_number, "customer_since": customer_since})
        g.conn.commit()

        restaurants = []
        restaurants = homepage_info()
        return render_template("homepage.html", restaurants=restaurants, customer_id=customer_id)


def clear_cart():
    delete_query = "DELETE FROM cart"
    g.conn.execute(text(delete_query))
    g.conn.commit()
    item_unique_id = 0
    return

@app.route('/restaurant/back/<string:customer_id>')
def back_to_homepage(customer_id):
    clear_cart()
    restaurants = []
    restaurants = homepage_info()
    return render_template("homepage.html", restaurants=restaurants, customer_id=customer_id)


@app.route('/restaurant/<string:customer_id>/<string:restaurant_id>')
def restaurant_page(customer_id, restaurant_id):
    restaurant_data = get_restaurant_info(restaurant_id)
    categories_data = get_categories_data(restaurant_id)
    items_data = get_items_data(restaurant_id)
    cart_items = get_cart()
    return render_template('restaurant.html', customer_id=customer_id, restaurant=restaurant_data, categories=categories_data, items=items_data, cart_items=cart_items)

def get_restaurant_info(restaurant_id):
    select_query_restaurant = "SELECT * FROM RESTAURANTS WHERE restaurant_id = :restaurant_id"
    cursor = g.conn.execute(text(select_query_restaurant), {"restaurant_id": restaurant_id})
    result = cursor.fetchone()

    restaurant_id, restaurant_name, restaurant_address, city, restaurant_contact_num = result
    restaurant = {"id": restaurant_id, "name": restaurant_name, "address": restaurant_address, "city": city, "phone_number": restaurant_contact_num}
    cursor.close()
    return restaurant

def get_categories_data(restaurant_id):
    select_query_menu = "SELECT product_category FROM MENU WHERE restaurant_id = :restaurant_id"
    cursor = g.conn.execute(text(select_query_menu), {"restaurant_id": restaurant_id})
    categories = []
    for result in cursor:
        product_category = result
        categories.append({"category": product_category})
    cursor.close()
    return categories

def get_items_data(restaurant_id):
    select_query_items = "SELECT item_price, item_description, item_id FROM menu_items WHERE restaurant_id = :restaurant_id"
    cursor = g.conn.execute(text(select_query_items), {"restaurant_id": restaurant_id})
    items = []
    for result in cursor:
        item_price, item_description, item_id = result
        items.append({"price": item_price, "description": item_description, "id": item_id})
    cursor.close()
    return items


# Example of adding new data to the database
@app.route('/add_to_cart/<string:customer_id>/<string:restaurant_id>/<string:item_id>', methods=['POST'])
def add_to_cart(customer_id, restaurant_id, item_id):
    global item_unique_id
    #take item_description and price from the db using id
    select_query_item_info = "SELECT item_price, item_description FROM menu_items WHERE item_id = :item_id AND restaurant_id = :restaurant_id"
    cursor = g.conn.execute(text(select_query_item_info), {"item_id": item_id, "restaurant_id": restaurant_id})
    result = cursor.fetchone()
    item_price, item_description = result
    cursor.close()

    #put all of it back into the table 'cart'
    insert_query = """
    INSERT INTO cart (item_unique_id, item_id, item_price, item_description)
    VALUES (:item_unique_id, :item_id, :item_price, :item_description)
    """
    g.conn.execute(text(insert_query), {"item_unique_id": item_unique_id, "item_id": item_id, "item_price": item_price, "item_description": item_description})
    g.conn.commit()
    item_unique_id += 1
    return redirect(url_for('restaurant_page', customer_id=customer_id, restaurant_id=restaurant_id))

@app.route('/cart/<string:customer_id>/<string:restaurant_id>')
def cart(customer_id, restaurant_id):
    cart_items = get_cart()
    total_price = get_total_price(cart_items)
    print("Total price is " + str(total_price))
    return render_template('cart.html', customer_id=customer_id, cart_items = cart_items, restaurant_id=restaurant_id, total_price=total_price)

def get_total_price(cart_items):
    sum = 0
    for item in cart_items:
        sum += item['item_price']
    print("The sum is " + str(sum))
    return sum

def get_cart():
    select_query_cart = "SELECT item_description, item_price FROM cart"
    cursor = g.conn.execute(text(select_query_cart))
    cart_items = []
    for result in cursor:
        item_description, item_price = result
        cart_items.append({"item_description": item_description, "item_price": item_price})
    cursor.close()
    print("Cart items are " + str(cart_items))
    return cart_items

def get_cart_items(cart_items):
    select_query_cart_items = "SELECT item_id FROM cart"
    cursor = g.conn.execute(text(select_query_cart_items))
    items = []
    for result in cursor:
        item_id = result
        items.append({"item_id": item_id})
    cursor.close()
    return items



def insert_cart_items():
    select_query_cart_items = "SELECT item_id FROM cart"
    cursor = g.conn.execute(text(select_query_cart_items))
    for result in cursor:
        items_ordered = str(result)
        insert_query = """
        INSERT INTO orders (items_ordered)
        VALUES (:items_ordered)
        """
        g.conn.execute(text(insert_query), {"items_ordered": items_ordered})
        g.conn.commit()
    cursor.close()
    return True





@app.route('/payment/<string:customer_id>/<string:restaurant_id>')
def payment(customer_id, restaurant_id):
    return render_template('payment.html', restaurant_id=restaurant_id, customer_id=customer_id)


@app.route('/rate/<string:customer_id>/<string:restaurant_id>', methods=['POST'])
def rating(customer_id, restaurant_id):
    rating = request.form.get('rating')
    insert_query = """
    INSERT INTO rate (customer_id, restaurant_id, rating)
    VALUES (:customer_id, :restaurant_id, :rating)
    """
    g.conn.execute(text(insert_query), {"customer_id": customer_id, "restaurant_id": restaurant_id, "rating": rating})
    g.conn.commit()

    restaurants = []
    restaurants = homepage_info()

    return render_template('homepage.html', restaurants=restaurants, customer_id=customer_id)


@app.route('/place_order/<string:customer_id>/<string:restaurant_id>', methods=['POST'])
def place_order(customer_id, restaurant_id):
    #get payment type from the form
    payment_type = request.form.get('payment_type')
    card_number = request.form.get('card_number')
    if not (card_number.isdigit() and len(card_number) == 16):
        error = "Please enter a valid card number, without dashes"
        return render_template('payment.html', restaurant_id=restaurant_id, customer_id=customer_id, error=error)


    #create a new payment_id
    global set_payment_id
    payment_id = "PAY" + str(set_payment_id)
    set_payment_id += 1

    #create a new order_id
    global set_order_id
    order_id = "ORD" + str(set_order_id)
    set_order_id += 1

    #find total_price
    cart_items = get_cart()
    total_price = get_total_price(cart_items)
    payment_amount = total_price
    print("Total price is " + str(total_price))

    #set payment_amount to total_price
    #payment_amount = total_price
    #set datetime
    datetime_of_payment = datetime.now().date()
    #set datetime
    datetime_of_order = datetime.now().date()




    #insert into orders : total_price, order_id, datetime_of_order, customer_id, restaurant_id, items_ordered
    #insert_cart_items()

    insert_query = """
    INSERT INTO orders (order_id, datetime_of_order, customer_id, total_price, restaurant_id)
    VALUES (:order_id, :datetime_of_order, :customer_id, :total_price, :restaurant_id)
    """
    g.conn.execute(text(insert_query), {"order_id": order_id, "datetime_of_order": datetime_of_order, "customer_id": customer_id, "total_price": total_price, "restaurant_id": restaurant_id})
    g.conn.commit()


    #insert into payment : payment_id, payment_type, payment (total) amount, datetime_of_payment, order_id, datetime_of_order
    insert_query = """
    INSERT INTO payment (payment_id, payment_type, payment_amount, datetime_of_payment, order_id, datetime_of_order)
    VALUES (:payment_id, :payment_type, :payment_amount, :datetime_of_payment, :order_id, :datetime_of_order)
    """
    g.conn.execute(text(insert_query), {"payment_id": payment_id, "payment_type": payment_type, "payment_amount": total_price, "datetime_of_payment": datetime_of_payment, "order_id": order_id, "datetime_of_order": datetime_of_order})
    g.conn.commit()

    #insert into paid_using : payment_id, order_id
    insert_query = """
    INSERT INTO paid_using (payment_id, order_id)
    VALUES (:payment_id, :order_id)
    """
    g.conn.execute(text(insert_query), {"payment_id": payment_id, "order_id": order_id})
    g.conn.commit()

    #clearing out the cart
    clear_cart()

    return render_template('rating.html', restaurant_id=restaurant_id, customer_id=customer_id)



@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()




if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using:

            python server.py

        Show the help text using:

            python server.py --help

        """

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()