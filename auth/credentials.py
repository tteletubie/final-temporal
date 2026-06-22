# 2. Third-Party Libraries
from rich.align import Align
from rich.console import Console
from rich.panel import Panel

# 3. Local Modules
from ui import visuals
console = Console()

def login():
    console.clear()
    console.print(Align.center(Panel(Align.center("[bold green]Enter your credentials[/bold green]"), title="[bold #00FFB3]Login[/bold #00FFB3]", border_style="#00FFB3", width=50)))

    username = visuals.input("Username")
    password = visuals.input("Password", True)
    
    return username, password

def login_u():
    while True:
        visuals.show_login()

        name = visuals.input("Name")
        lastname = visuals.input("Lastname")
        username = visuals.input("Username")
        password = visuals.input("Password")
        birth = visuals.input_date("Date of Birth")
        job = visuals.input("Role")
        offences = visuals.input_int("Offences")

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