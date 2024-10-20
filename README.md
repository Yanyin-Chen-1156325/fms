# FMS
 Farm Management Simulator for COMP636 Final Project.
  
## Design decisions
1.  SQL:  
   The data retrieved by SQL queries for each function are very similar, so I mainly use one SQL query to generate data for mobs, paddocks, and stock statistics. This allows different routes to use the data as needed. I believe this approach makes the code cleaner. Additionally, I use the same names for the columns created by different SQL queries. This way, the same names can be used across different pages, which helps avoid confusion.
   Currently, the amount of data is small, so I'm using join SQL. However, if the data grows to a point where it affects query performance, this method won't be suitable. In that case, we would need to change the approach to query each table separately and then process the related logic in the program.

  
2.  Add and edit functions:   
   They require the same data. The only difference is that the edit function will pre-fill the data, while the add function will not. Therefore, we use the same template, paddock_form.html, but use different routes to pass different parameters. This helps identify with the add and edit functions.
   We use the same layout for both functions to reduce code duplication and improve efficiency.

  
3. Methods used for add, modify, and delete buttons:  
    The POST method is used for both adding and deleting. Adding doesn't require any parameters, so either POST or GET could be used. Deleting needs to pass parameters, so POST is used to prevent users from potentially manipulating data. The GET method is used for Editing. It retrieves Paddock's id based on URL parameters and returns it to the page without changing the database, so GET can be used safely.
  
4. Input of area and dry matter per hectare:  
   Both fields are restricted to two decimal places. These values don’t need to be very precise, so limiting them to two decimal places is better for the layout.   
   The area must be greater than 0, as an area cannot be 0.   
   However, dry matter per hectare can be 0.

  
5. Moving mobs function:  
   Only paddocks without mobs are passed to the frontend. This approach helps prevent errors when updating the database.
  
  
6. Navbar function:  
   For user-friendly, highlight the item of the page which the user is clicking.
   
  
  
## Image sources
1. Ephraïm, L., _Herd of Dairy Cattles on Field_ [Picture]. Unsplash. https://unsplash.com/photos/herd-of-dairy-cattles-on-field-AxoNnnH1Y98
   
  
## Database questions
1. What SQL statement creates the mobs table and defines its fields/columns? (Copy and paste the relevant lines of SQL.)
    ```SQL
    CREATE TABLE mobs (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) DEFAULT NULL,
    paddock_id INT NOT NULL,
    PRIMARY KEY (id),
    UNIQUE INDEX paddock_idx (paddock_id),
    CONSTRAINT fk_paddock FOREIGN KEY (paddock_id)
        REFERENCES paddocks (id)
        ON DELETE NO ACTION ON UPDATE NO ACTION
    );
    ```
2. Which lines of SQL script sets up the relationship between the mobs and paddocks tables?
    ```SQL
    CONSTRAINT fk_paddock FOREIGN KEY (paddock_id)
            REFERENCES paddocks (id)
            ON DELETE NO ACTION ON UPDATE NO ACTION
    ```
3. The current FMS only works for one farm. Write SQL script to create a new table called farms, which includes a unique farm ID, the farm name, an optional short description and the owner’s name. The ID can be added automatically by the database. (Relationships to other tables not required.)
    ```SQL
    CREATE TABLE farms (
        id INT NOT NULL AUTO_INCREMENT,
        name VARCHAR(50) NOT NULL,
        description TEXT NULL,
        owner VARCHAR(50) NOT NULL,
        PRIMARY KEY (id)
    );
    ```
4. Write an SQL statement to add details for an example farm to your new farms table, which would be suitable to include in your web application for the users to add farms in a future version. (Type in actual values, don’t use %s markers.)
    ```SQL
    INSERT INTO farms(name, description, owner)
    VALUES('Farm 2', 'This is a farm with sheeps.', 'Ann');
    ```
5. What changes would you need to make to other tables to incorporate the new farms table? (Describe the changes. SQL script not required.)
    ```
    Add a Farm_id field to the Paddocks table and create a foreign key to the Farms.id. Use ON DELETE NO ACTION and ON UPDATE NO ACTION to protect data.
    ```

