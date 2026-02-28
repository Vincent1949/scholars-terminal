"""
CLI Tool for Reviewing Staged Research Papers
Run from project root: python review_papers.py
"""

import sys
from pathlib import Path

# Add research_scanner to path
sys.path.insert(0, str(Path(__file__).parent / "research_scanner"))

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from reviewer import PaperReviewer

console = Console()
reviewer = PaperReviewer()


@click.group()
def cli():
    """Research Paper Review Tool"""
    pass


@cli.command()
@click.option('--sort', default='relevance', 
              type=click.Choice(['relevance', 'date', 'citations', 'topic']),
              help='Sort papers by criteria')
@click.option('--limit', default=20, help='Number of papers to show')
@click.option('--topic', default=None, help='Filter by topic')
def list(sort, limit, topic):
    """List papers in staging area"""
    papers = reviewer.get_staged_papers(sort_by=sort, limit=limit, topic_filter=topic)
    
    if not papers:
        console.print("[yellow]No papers in staging area[/yellow]")
        console.print("\n[dim]Papers will appear here after future scans (if indexer is configured to use staging)[/dim]")
        return
    
    table = Table(title=f"Staged Papers (sorted by {sort})")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Title", style="white", width=50)
    table.add_column("Relevance", justify="right", style="green")
    table.add_column("Citations", justify="right", style="yellow")
    table.add_column("Date", style="magenta")
    table.add_column("ID", style="dim", width=12)
    
    for i, paper in enumerate(papers, 1):
        table.add_row(
            str(i),
            paper['title'][:47] + "..." if len(paper['title']) > 50 else paper['title'],
            f"{paper['relevance_score']:.2f}",
            str(paper['citation_count']),
            paper['published_date'][:10],
            paper['id'][:12]
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(papers)} papers[/dim]")


@cli.command()
def stats():
    """Show review statistics"""
    stats = reviewer.get_stats()
    
    table = Table(title="Review Statistics")
    table.add_column("Status", style="cyan")
    table.add_column("Count", justify="right", style="yellow")
    
    table.add_row("Staged (awaiting review)", str(stats['staged']))
    table.add_row("Approved (in database)", str(stats['approved']))
    table.add_row("Rejected (declined)", str(stats['rejected']))
    table.add_row("Total processed", str(stats['total_processed']))
    
    console.print(table)
    
    if stats['staged'] == 0:
        console.print("\n[dim]Note: No papers in staging. Future scans will add papers here if indexer is configured.[/dim]")


@cli.command()
@click.argument('paper_id')
def preview(paper_id):
    """Preview full details of a paper"""
    paper = reviewer.preview_paper(paper_id)
    
    if not paper:
        console.print(f"[red]Paper {paper_id} not found in staging[/red]")
        return
    
    content = f"""
[bold cyan]{paper['title']}[/bold cyan]

[bold]Authors:[/bold] {paper['authors']}
[bold]Source:[/bold] {paper['source']} | [bold]Published:[/bold] {paper['published_date'][:10]}
[bold]Topics:[/bold] {paper['topics']}
[bold]Relevance:[/bold] {paper['relevance_score']:.2f} | [bold]Citations:[/bold] {paper['citation_count']}

[bold]Summary:[/bold]
{paper['summary']}

[bold]URL:[/bold] {paper['url']}
[bold]PDF:[/bold] {paper['pdf_url'] or 'N/A'}
    """.strip()
    
    panel = Panel(content, title="Paper Preview", border_style="blue")
    console.print(panel)


@cli.command()
@click.argument('paper_ids', nargs=-1, required=True)
def approve(paper_ids):
    """Approve one or more papers (space-separated IDs)"""
    paper_ids = list(paper_ids)
    
    console.print(f"[yellow]Approving {len(paper_ids)} paper(s)...[/yellow]")
    result = reviewer.approve_batch(paper_ids)
    
    console.print(f"[green]Approved: {result['approved']}[/green]")
    if result['failed'] > 0:
        console.print(f"[red]Failed: {result['failed']}[/red]")


@cli.command()
@click.argument('paper_ids', nargs=-1, required=True)
@click.option('--reason', default='', help='Reason for rejection')
def reject(paper_ids, reason):
    """Reject one or more papers (space-separated IDs)"""
    paper_ids = list(paper_ids)
    
    console.print(f"[yellow]Rejecting {len(paper_ids)} paper(s)...[/yellow]")
    result = reviewer.reject_batch(paper_ids, reason)
    
    console.print(f"[red]Rejected: {result['rejected']}[/red]")
    if result['failed'] > 0:
        console.print(f"[yellow]Failed: {result['failed']}[/yellow]")


@cli.command()
@click.option('--sort', default='relevance', 
              type=click.Choice(['relevance', 'date', 'citations']),
              help='Sort papers by criteria')
def interactive(sort):
    """Interactive review mode - approve/reject one by one"""
    papers = reviewer.get_staged_papers(sort_by=sort, limit=100)
    
    if not papers:
        console.print("[yellow]No papers in staging area[/yellow]")
        console.print("\n[dim]Papers will appear after future scans (if indexer is configured to use staging)[/dim]")
        return
    
    console.print(f"[bold cyan]Interactive Review Mode[/bold cyan]")
    console.print(f"Found {len(papers)} papers to review\n")
    
    for i, paper in enumerate(papers, 1):
        content = f"""
[bold]{i}/{len(papers)}: {paper['title']}[/bold]

[dim]Authors: {paper['authors'][:80]}...[/dim]
[dim]Published: {paper['published_date'][:10]} | Citations: {paper['citation_count']}[/dim]
[dim]Topics: {paper['topics']}[/dim]
[bold]Relevance: {paper['relevance_score']:.2f}[/bold]

{paper['summary'][:200]}...

[dim]{paper['url']}[/dim]
        """.strip()
        
        panel = Panel(content, border_style="blue")
        console.print(panel)
        
        action = Prompt.ask(
            "\n[a]pprove / [r]eject / [s]kip / [q]uit",
            choices=["a", "r", "s", "q"],
            default="s"
        )
        
        if action == 'a':
            reviewer.approve_paper(paper['id'])
            console.print("[green]Approved[/green]\n")
        elif action == 'r':
            reason = Prompt.ask("Reason (optional)", default="")
            reviewer.reject_paper(paper['id'], reason)
            console.print("[red]Rejected[/red]\n")
        elif action == 's':
            console.print("[yellow]Skipped[/yellow]\n")
        elif action == 'q':
            console.print("[cyan]Exiting review...[/cyan]")
            break
    
    stats = reviewer.get_stats()
    console.print(f"\n[bold]Review Complete![/bold]")
    console.print(f"Staged: {stats['staged']} | Approved: {stats['approved']} | Rejected: {stats['rejected']}")


@cli.command()
@click.option('--min-relevance', default=0.8, help='Minimum relevance score')
@click.option('--min-citations', default=100, help='Minimum citation count')
@click.option('--max-papers', default=10, help='Maximum papers to approve')
def auto_approve(min_relevance, min_citations, max_papers):
    """Automatically approve high-quality papers"""
    console.print("[yellow]Auto-approving papers...[/yellow]")
    
    approved = reviewer.auto_approve_by_criteria(
        min_relevance=min_relevance,
        min_citations=min_citations,
        max_papers=max_papers
    )
    
    console.print(f"[green]Auto-approved {len(approved)} papers[/green]")
    
    if approved:
        console.print("\n[bold]Approved papers:[/bold]")
        for paper_id in approved:
            console.print(f"  - {paper_id}")


if __name__ == "__main__":
    cli()
