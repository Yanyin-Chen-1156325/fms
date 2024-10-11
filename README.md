# FMS
 Farm Management Simulator for COMP636 Final Project.
  
## Design decisions
1.  SQL:  
   The data in the select parts are very similar. Therefore, I mainly use two sets of SQL queries with Group By clauses to present the data. Each function then retrieves the specific data it needs.
  
2.  Add and edit functions:   
   They require the same data. The only difference is that the edit function will pre-fill the data, while the add function will not. Therefore, we use the same template, paddock_form.html, but use different routes to pass different parameters. This helps identify with the add and edit functions.
   We use the same layout for both functions to reduce code duplication and improve efficiency.
  

## Image sources
1. farm2.jpg: [unsplash](https://unsplash.com/photos/herd-of-dairy-cattles-on-field-AxoNnnH1Y98)
     

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

