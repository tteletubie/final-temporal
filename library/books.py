# 1. Standard Libraries

# 2. Third-Party Libraries
from rich.align import Align
from rich.console import Console
from rich.panel import Panel

# 3. Local Modules
from ui import visuals
from database import database as db

console = Console()


def show_info():
        while True:
            console.clear()
            console.print(Align.center(Panel(Align.center("[bold green][/bold green]"), title="[bold #00FFB3]Search by Category[/bold #00FFB3]", border_style="#00FFB3",width=50)))
            category = visuals.input("Enter category: ")

            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM books WHERE category = ?", (category,))
                table = cursor.fetchall()

                if not table: 
                    console.print(f"[bold][yellow][[red]*[yellow]][red] No books found in the category [magenta]'{category}'[/magenta][red].[/red]")
                    input()
                    show_info()

                console.print("BUUKS:")
                for table in table:
                    console.print(f"[blue1]{table[0]} - [purple]{table[1]} - [light_steel_blue]{table[3]} - [magenta3]{table[4]}")
                input()
                break