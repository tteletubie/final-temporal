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

    username = visuals.enter("Username")
    password = visuals.enter("Password")
    
    return username, password

def login_u():
    while True:
        visuals.show_login()

        name = visuals.enter("Name")
        lastname = visuals.enter("Lastname")
        username = visuals.enter("Username")
        password = visuals.enter("Password")
        birth = visuals.enter_date("Date of Birth")
        job = visuals.enter("Role")
        offences = visuals.enter_int("Offences")

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