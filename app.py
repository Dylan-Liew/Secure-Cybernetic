from cybernetic import app, db
from cybernetic.blacklist_helper import prune_database
from add_test_data import add_test_data


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database Created!')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database Dropped!')


@app.cli.command('db_seed')
def db_seed():
    add_test_data()
    print("Sample Data Added!")


@app.cli.command('db_reset')
def db_reset():
    db.drop_all()
    db.create_all()
    add_test_data()
    print("Database Reset Successfully!")


@app.cli.command("remove_expired_tokens")
def db_purge():
    prune_database()
    print("Expired token removed")


if __name__ == '__main__':
    app.run(port=1000)
