import visual
from visual import show_login

def login_u():
    while True:
        show_login()

        name = visual.enter("Name")
        lastname = visual.enter("Lastname")
        username = visual.enter("Username")
        password = visual.enter("Password")
        birth = visual.enter_date("Date of Birth")
        job = visual.enter("Role")
        offences = visual.enter_int("Offences")

        user = {
        "name": name,
        "lastname": lastname,
        "username": username,
        "password": password,
        "birth": birth,
        "job": job,
        "offences": offences
        }

        return job.lower(), user

def logout():
    pass


def authenticate(username, password):
    pass


def get_user_role(id_user):
    pass


def create_account():
    pass


def username_exists(username):
    pass