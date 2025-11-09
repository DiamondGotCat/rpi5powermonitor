#!/usr/bin/env python3
import subprocess
import time
import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from rich import box
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.table import Table
from rich.panel import Panel

console = Console()

CURRENT_RE = re.compile(
    r"^\s*(?P<name>[A-Z0-9_]+)\s+current\((?P<idx>\d+)\)=(?P<value>[\d\.]+)A"
)
VOLT_RE = re.compile(
    r"^\s*(?P<name>[A-Z0-9_]+)\s+volt\((?P<idx>\d+)\)=(?P<value>[\d\.]+)V"
)

@dataclass
class Rail:
    name: str
    voltage: Optional[float] = None
    current: Optional[float] = None
    idx_v: Optional[int] = None
    idx_i: Optional[int] = None

    @property
    def power(self) -> Optional[float]:
        if self.voltage is not None and self.current is not None:
            return self.voltage * self.current
        return None

def ensure_sudo() -> None:
    console.print(
        "[bold cyan]Raspberry Pi 5 Power Monitor[/bold cyan]\n"
        "[bold]This tool requires superuser privileges, enter your password if prompted.[/bold]"
    )
    try:
        subprocess.run(["sudo", "-v"], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Authentication failed. The program will now terminate.") from e

def run_pmic_read_adc() -> str:
    try:
        out = subprocess.check_output(
            ["sudo", "-n", "vcgencmd", "pmic_read_adc"],
            text=True,
            stderr=subprocess.STDOUT,
        )
        if not out.strip():
            raise RuntimeError("'vcgencmd pmic_read_adc' returned empty output.")
        return out
    except FileNotFoundError:
        raise RuntimeError("'vcgencmd' command not found.")
    except subprocess.CalledProcessError as e:
        msg = (e.output or "").strip()
        raise RuntimeError(
            "Failed to execute 'vcgencmd pmic_read_adc' via sudo.\nTip: Your sudo may have expired.\nThis monitor will be terminated, so please run it again and authenticate."
            + (f"\nDetails: {msg}" if msg else "")
        ) from e

def parse_pmic_output(text: str) -> Dict[str, Rail]:
    rails: Dict[str, Rail] = {}

    def get_or_create(base: str) -> Rail:
        if base not in rails:
            rails[base] = Rail(name=base)
        return rails[base]

    for line in text.splitlines():
        if not line.strip():
            continue

        m_i = CURRENT_RE.match(line)
        if m_i:
            name = m_i.group("name")
            idx = int(m_i.group("idx"))
            value = float(m_i.group("value"))
            base = _base_name(name)
            r = get_or_create(base)
            r.current = value
            r.idx_i = idx
            continue

        m_v = VOLT_RE.match(line)
        if m_v:
            name = m_v.group("name")
            idx = int(m_v.group("idx"))
            value = float(m_v.group("value"))
            base = _base_name(name)
            r = get_or_create(base)
            r.voltage = value
            r.idx_v = idx
            continue

    return rails

def _base_name(name: str) -> str:
    if "_" not in name:
        return name
    return name.rsplit("_", 1)[0]

def build_layout() -> Layout:
    layout = Layout(name="root")

    layout.split(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3),
    )

    layout["body"].split_row(
        Layout(name="rails", ratio=3),
        Layout(name="bars", ratio=2),
        Layout(name="summary", ratio=2),
    )

    return layout

def render_header(interval: float) -> Panel:
    return Panel(
        f"[bold cyan]Raspberry Pi 5 Power Monitor[/bold cyan]  "
        f"(vcgencmd pmic_read_adc via sudo, refresh: {interval:.1f}s)",
        box=box.ROUNDED,
    )

def render_rails_table(rails: Dict[str, Rail]) -> Table:
    table = Table(
        title="Rails (sorted by power)",
        box=box.MINIMAL_DOUBLE_HEAD,
        expand=True,
        pad_edge=False,
        show_lines=False,
    )
    table.add_column("Rail", style="bold")
    table.add_column("Volt [V]", justify="right")
    table.add_column("Curr [A]", justify="right")
    table.add_column("Power [W]", justify="right")
    table.add_column("Idx(V/I)", justify="center")

    sorted_rails = sorted(
        rails.values(),
        key=lambda r: (r.power or 0.0),
        reverse=True,
    )

    for r in sorted_rails:
        v = f"{r.voltage:.6f}" if r.voltage is not None else "-"
        i = f"{r.current:.8f}" if r.current is not None else "-"
        p = f"{r.power:.6f}" if r.power is not None else "-"

        idx = ""
        if r.idx_v is not None or r.idx_i is not None:
            idx = f"{r.idx_v if r.idx_v is not None else '-'} / {r.idx_i if r.idx_i is not None else '-'}"

        style = None
        if (r.power or 0) > 1.0:
            style = "bold red"
        elif (r.power or 0) > 0.2:
            style = "yellow"

        table.add_row(r.name, v, i, p, idx, style=style)

    if not sorted_rails:
        table.add_row("No data", "-", "-", "-", "-")

    return table

def render_bars(rails: Dict[str, Rail]) -> Panel:
    powered = [r for r in rails.values() if r.power is not None]
    powered.sort(key=lambda r: r.power, reverse=True)
    top = powered[:8]

    if not top:
        return Panel("No power data", title="Top Rails", box=box.ROUNDED)

    max_power = max(r.power for r in top) or 1e-9
    lines = []
    bar_width = 24

    for r in top:
        ratio = (r.power or 0) / max_power
        blocks = int(ratio * bar_width)
        bar = "█" * blocks + " " * (bar_width - blocks)
        lines.append(
            f"[bold]{r.name:<14}[/bold] {bar} [cyan]{(r.power or 0):.3f} W[/cyan]"
        )

    text = "\n".join(lines)
    return Panel(text, title="Top Power Rails", box=box.ROUNDED)

def render_summary(rails: Dict[str, Rail]) -> Panel:
    total_power = sum((r.power or 0.0) for r in rails.values())

    core_names = [
        "VDD_CORE",
        "0V8_SW",
        "0V8_AON",
        "1V1_SYS",
        "1V8_SYS",
        "3V3_SYS",
    ]

    core_lines = []
    for name in core_names:
        r = _find_rail(rails, name)
        if r and r.power is not None:
            core_lines.append(
                f"[bold]{name:<8}[/bold] {r.voltage:.3f}V  {r.current:.4f}A  "
                f"[magenta]{r.power:.4f}W[/magenta]"
            )

    if not core_lines:
        core_lines.append("No core rails data")

    text = (
        f"[bold green]Total measured power:[/bold green] "
        f"[yellow]{total_power:.4f} W[/yellow]\n\n"
        "[bold]Core / key rails:[/bold]\n"
        + "\n".join(core_lines)
    )

    return Panel(text, title="Summary", box=box.ROUNDED)

def _find_rail(rails: Dict[str, Rail], key: str) -> Optional[Rail]:
    if key in rails:
        return rails[key]
    for name, r in rails.items():
        if name.startswith(key):
            return r
    return None

def render_footer(last_update: float) -> Panel:
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_update))
    return Panel(
        f"Last update: [bold]{ts}[/bold]    Quit: [bold]Ctrl+C[/bold]",
        box=box.SQUARE,
    )

def main(interval: float = 1.0) -> None:
    try:
        try:
            ensure_sudo()
        except RuntimeError as e:
            console.print(f"[bold red]{e}[/bold red]")
            return

        layout = build_layout()
        last_error: Optional[str] = None

        with Live(layout, console=console, screen=True, refresh_per_second=10):
            while True:
                try:
                    raw = run_pmic_read_adc()
                    rails = parse_pmic_output(raw)
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    last_error = str(e)
                    layout["footer"].update(
                        Panel(
                            f"[bold red]Error:[/bold red] {last_error}",
                            box=box.SQUARE,
                        )
                    )
                    break

                now = time.time()

                layout["header"].update(render_header(interval))
                layout["rails"].update(render_rails_table(rails))
                layout["bars"].update(render_bars(rails))
                layout["summary"].update(render_summary(rails))
                layout["footer"].update(render_footer(now))

                time.sleep(interval)

        if last_error:
            console.print(f"\n[bold red]Stopped:[/bold red] {last_error}")
    except KeyboardInterrupt:
        console.print("\n[bold red]Aborted.[/bold red]")

if __name__ == "__main__":
    main(interval=1.0)
