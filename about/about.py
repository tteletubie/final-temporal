# 1. Standard Libraries

# 2. Third-Party Libraries
from rich.align import Align
from rich.console import Console
from rich.panel import Panel

# 3. Local Modules
from ui import visuals

console = Console()


def show_staff():
    while True:
        console.clear()
        console.print(Align.center(Panel(Align.center("[bold green][/bold green]"), title="[bold #00FFB3]BookWorm Admins [/bold #00FFB3]", border_style="#00FFB3",width=50)))

        console.print(Align.center("[bold]Luis [green]Gael [/green]Gonzalez Torres\n"))
        console.print(Align.center("[bold][red]Carlos[/red] Silva Cortes\n"))
        console.print(Align.center("[bold][magenta]Lesly [/magenta] Adilene Terrazo Rodriguez\n"))
        console.print(Align.center("[bold]Maria [purple]Fernanda[/purple] Obregon Ramirez"))

        console.input()
        break


def show_rules():
    while True:
        console.clear()
        console.print(Align.center(Panel(Align.center("[bold green][/bold green]"), title="[bold #00FFB3]BookWorm Rules [/bold #00FFB3]", border_style="#00FFB3",width=50)))

        console.print(Align.center("\n[bold][green]1.[/green] Be respectful to others.\n"))
        console.print(Align.center("[bold][green]2.[/green] No spamming or advertising.\n"))
        console.print(Align.center("[bold][green]3.[/green] Use appropriate language.\n"))
        console.print(Align.center("[bold][green]4.[/green] Follow the community guidelines.\n"))
        console.print(Align.center("[bold][green]5.[/green] Report any suspicious activity.\n"))

        console.input()
        break


def show_made_by():
    while True:
        console.clear()
        console.print(Align.center(Panel(Align.center("[bold green][/bold green]"), title="[bold #00FFB3]Made By [/bold #00FFB3]", border_style="#00FFB3",width=50)))

        console.print(Align.center("[bold]Luis [green]Gael [/green]Gonzalez Torres\n"))
        console.print(Align.center("[bold][red]Carlos[/red] Silva Cortes\n"))
        console.print(Align.center("[bold][magenta]Lesly [/magenta] Adilene Terrazo Rodriguez\n"))
        console.print(Align.center("[bold]Maria [purple]Fernanda[/purple] Obregon Ramirez"))

        console.input()
        break
