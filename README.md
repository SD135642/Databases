# Databases

<h2>The PostgreSQL account where the database resides: </h2>
sz3120
<hr>

<h2>The URL of the web application. </h2>
http://127.0.0.1:8111
<hr>

<h2>A description of the general application. </h2>
  An application that allows the customer to enter their information, choose a restaurant they want to order food from, add items from the menu to the cart, enter payment information, place the order, and leave a rating of the restaurant. Includes two ways of logging in, via signing up and loging in as an existing customer, and deleting items from a cart.
<hr>
<h2>Two example database operations and why they are interesting. </h2>

<h3>payment.html </h3>
This page is used to collect all the information in one place and finally place the order. <br>
The information of the customer placing the order and the restaurant it is ordered from is passed when rendering the page. Payment type and card number are collected from the page via a form. Card number gets checked for validity (the right number of digits). The page calls a /place_order/… route on the server which receives customer and restaurant information as the passed parameters, and accesses payment information by requesting the form’s data. Then it creates new unique id’s for this payment and this order using two global variables for payment and order ids, and increments those variables. It gets all items in the cart using a select query, calculates the total price, and sets datetime_of order and payment. <br>
Finally, it uses 3 Postgre SQL insert queries to insert all the data for every column into orders, payment, and paid_using entities. At the end, it uses a delete query to clear out the cart and render the rating page. It is an important page because it is the final stage that collects all variables related to the order, actually places the order, and inserts all relevant information in the database all at once.

<br>
<h3>restaurant.html</h3>
This page displays the restaurant info and menu, and allows the customer to add items to cart. <br>
The route /restaurant/… uses select queries to get restaurant data, menu data, and cart data. Then it renders restaurant.html passing all those values. The page itself uses that information to show the restaurant’s details, food categories, menu items, and cart items. Each menu item has a button “add” next to it which leads to the server route that adds the item to the cart and renders the same page, restaurant.html, but with an updated cart. <br>
The cart displayed also has a remove button next to each item, which removes an item in a similar way. There is also a button “Go back” which takes the user back to the restaurant list, and uses a delete query to clear the cart data since the customer no longer wishes to order from this restaurant. In this case, it drops restaurant id and only retains customer id. Finally, there is a button “Continue to cart” which leads to the cart page. It passes customer id and restaurant id as parameters. It is an important page because it works with multiple sets of data coming from various sql queries, and it has multiple ways to leave that page which all imply different parameters. It is also responsible for dynamically updating and displaying the cart.
