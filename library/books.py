# 1. Standard Libraries

# 2. Third-Party Libraries
from rich.align import Align
from rich.console import Console
from rich.panel import Panel

# 3. Local Modules
from ui import visuals
from database import database as db

console = Console()


def show_category():
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
                    show_category()
                
                console.print(f"[bold] Books found in [magenta]'{category}'[/magenta]: \n")
                for table in table:
                    console.print(f"[blue1]{table[0]} - [purple]{table[1]} - [light_steel_blue]{table[3]} - [magenta3]{table[4]}")
                console.input()
                break

def show_title():
        while True:
            console.clear()
            console.print(Align.center(Panel(Align.center("[bold green][/bold green]"), title="[bold #00FFB3]Search by Title[/bold #00FFB3]", border_style="#00FFB3",width=50)))
            title = visuals.input("Enter title: ")

            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM books WHERE name = ?", (title,))
                table = cursor.fetchall()

                if not table: 
                    console.print(f"[bold][yellow][[red]*[yellow]][red] No books found with the title [magenta]'{title}'[/magenta][red].[/red]")
                    input()
                    show_title()
                
                console.print(f"[bold] Books found with [magenta]'{title}'[/magenta]: \n")
                for table in table:
                    console.print(f"[blue1]{table[0]} - [purple]{table[1]} - [dark_slate_gray2]{table[2]} - [light_steel_blue]{table[3]} - [magenta3]{table[4]}")
                console.input()
                break

def show_author():
        while True:
            console.clear()
            console.print(Align.center(Panel(Align.center("[bold green][/bold green]"), title="[bold #00FFB3]Search by Title[/bold #00FFB3]", border_style="#00FFB3",width=50)))
            author = visuals.input("Enter an author: ")

            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM books WHERE author = ?", (author,))
                table = cursor.fetchall()

                if not table: 
                    console.print(f"[bold][yellow][[red]*[yellow]][red] No books found with the author [magenta]'{author}'[/magenta][red].[/red]")
                    input()
                    show_author()
                
                console.print(f"[bold] Books found of [magenta]'{author}'[/magenta]: \n")
                for table in table:
                    console.print(f"[blue1]{table[0]} - [purple]{table[1]} - [light_steel_blue]{table[2]} - [magenta3]{table[4]}")
                console.input()
                break