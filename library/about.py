from rich.align import Align
from rich.console import Console
from rich.console import Group
from rich.panel import Panel

from ui import visuals
from ui.key_input import read_key

console = Console()

STAFF_LINES = [
    "\n[bold]🌟 Luis [green]Galileo [/green]Gonzalez Torres\n",
    "[bold][red]Carlos[/red] Silva Cortes\n",
    "[bold][magenta]Lesly [/magenta] Adilene Terrazo Rodriguez\n",
    "[bold]Maria [purple]Fernanda[/purple] Obregon Ramirez\n",
]


def _staff_group() -> Group:
    return Group(*(Align.center(line) for line in STAFF_LINES))


def show_staff():
    while True:
        console.clear()
        visuals.big_title("BOOKWORMS")
        staff_panel = Panel(
            _staff_group(),
            title="[bold #00FFB3]BookWorm Admins [/bold #00FFB3]",
            border_style="#00FFB3",
            width=50,
        )
        console.print(Align.center(staff_panel))
        console.print(Align.center("[dim]q back | b back | Enter return[/dim]"))

        key = read_key(separate_quit_back=True)
        if key in ("QUIT", "BACK", "ENTER"):
            return


def show_rules():
    while True:
        console.clear()
        visuals.big_title("BOOKWORMS")
        rules_panel = Panel(
            Group(
                Align.center("\n[bold][green]1.[/green] Be respectful to others.\n"),
                Align.center("[bold][green]2.[/green] No spamming or advertising.\n"),
                Align.center("[bold][green]3.[/green] Use appropriate language.\n"),
                Align.center("[bold][green]4.[/green] Follow the community guidelines.\n"),
                Align.center("[bold][green]5.[/green] Report any suspicious activity.\n"),
            ),
            title="[bold #00FFB3]BookWorm Rules [/bold #00FFB3]",
            border_style="#00FFB3",
            width=60,
        )
        console.print(Align.center(rules_panel))
        console.print(Align.center("[dim]q back | b back | Enter return[/dim]"))

        key = read_key(separate_quit_back=True)
        if key in ("QUIT", "BACK", "ENTER"):
            return


def show_made_by():
    while True:
        console.clear()
        visuals.big_title("BOOKWORMS")
        credits_panel = Panel(
            _staff_group(),
            title="[bold #00FFB3]Made By [/bold #00FFB3]",
            border_style="#00FFB3",
            width=60,
        )
        console.print(Align.center(credits_panel))
        console.print(Align.center("[dim]q back | b back | Enter return[/dim]"))

        key = read_key(separate_quit_back=True)
        if key in ("QUIT", "BACK", "ENTER"):
            return
