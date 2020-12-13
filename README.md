# Cybernetic ( Secure Version )

## NYP DSF1901 Year 2 Semester 1 Group Project

### Description

Cybernetic consists of secure APIs which encompasses vulnerabilities from the entire OWASP API Top 10 2019

### Group:

* [Dylan](https://github.com/Dylan-Liew)
* [Joel](https://github.com/j041)
* [William](https://github.com/willy00)
* [Kent](https://github.com/kentlow2002)

### Technologies:
* Python 3.7.3
* Flask
  * Flask Restx
  * Flask SQLAlchemy
  * Flask Marshmallow
  * Flask JWT 
  * Flask Mail
  * Flask Rest Paginate
  
### Configuration/Installation
* Please read this guide to create your project on **Pycharm** 
  * https://www.jetbrains.com/help/pycharm/creating-and-running-your-first-python-project.html#create-file
* Run `py -m pip install -r requirements.txt` on your pycharm terminal 
* Postman Setup
  * Import `Cybernetic.postman_collectin.json` 

### Features 
* Authentication API
* User Address API
* User Card API
* User Cart API
* User Order API
* User Profile API
* User Review API
* Products API
* Search API

### Command Guide
* `Flask db_drop` to drop all tables in SQL database
* `Flask db_create` to create all tables in SQL database
* `Flask db_seed` to create sample data for each table in SQL database
* `Flask db_reset` to reset SQL database with sample data

