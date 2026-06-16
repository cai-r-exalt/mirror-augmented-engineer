"""Entry point — wires the domain and infrastructure packages together.

This module creates a minimal composition root that injects the
infrastructure repositories into the domain use case and exposes a
controller instance. It's intentionally simple and uses in-memory
adapters so tests and local runs don't require external services.
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List
from urllib.parse import parse_qs, urlparse

from app.application.controllers.commande_controller import CommandesController
from app.domain.entities.commande import Article, LigneCommande
from app.domain.exceptions import ArticleInconnuException, StockInsuffisantException
from app.domain.use_cases.place_order import PasserCommandeCommand, PasserCommandeUseCase
from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository
from app.infrastructure.adapters.sqlalchemy_order_repository import SQLAlchemyOrderRepository


def create_application():
    # Minimal infra wiring
    # Try to create a real DB session; fall back to in-memory repository if unavailable
    try:
        from app.infrastructure.db import create_session

        session = create_session()
    except Exception:
        session = None

    order_repo = SQLAlchemyOrderRepository(session=session)
    stock_repo = InMemoryStockRepository(initial_stock={"Mojito": 100, "Eau plate": 50})

    use_case = PasserCommandeUseCase(order_repository=order_repo, stock_repository=stock_repo)
    controller = CommandesController(use_case=use_case)
    return {
        "order_repository": order_repo,
        "stock_repository": stock_repo,
        "use_case": use_case,
        "controller": controller,
    }


def print_stock(stock_repo):
    if hasattr(stock_repo, "stock"):
        for k, v in getattr(stock_repo, "stock", {}).items():
            print(f"{k}: {v}")
    else:
        print("No stock information available")


def parse_items_args(item_args) -> List[Dict[str, int]]:
    """Parse items provided as either a single comma-separated string
    or a list of strings. Each item must be 'name:qty'. Names may include spaces.
    """
    if isinstance(item_args, list):
        raw = " ".join(item_args)
    else:
        raw = str(item_args)
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    items: List[Dict[str, int]] = []
    for it in parts:
        if ":" not in it:
            raise ValueError("Invalid item format, expected name:qty")
        name, qty = it.rsplit(":", 1)
        items.append({"name": name.strip(), "quantity": int(qty)})
    return items


def print_order(commande):
    if commande is None:
        print("Order not found")
        return
    print(f"id: {commande.id}")
    print(f"festivalier_id: {commande.festivalier_id}")
    print(f"status: {commande.status}")
    print("lines:")
    for ligne in commande.lignes:
        print(f"  - {ligne.article.name}: {ligne.quantite}")


def main() -> None:
    app = create_application()
    parser = argparse.ArgumentParser(prog="buvette", description="CLI to interact with the augmented-engineer project")
    subparsers = parser.add_subparsers(dest="cmd")

    # Stock commands
    stock_parser = subparsers.add_parser("stock", help="Manage stock")
    stock_sub = stock_parser.add_subparsers(dest="action")
    stock_sub.add_parser("list", help="List current stock")
    stock_set = stock_sub.add_parser("set", help="Set quantity for an item")
    stock_set.add_argument("name")
    stock_set.add_argument("quantity", type=int)

    # Order commands
    order_parser = subparsers.add_parser("order", help="Manage orders")
    order_sub = order_parser.add_subparsers(dest="action")
    order_create = order_sub.add_parser("create", help="Create a new order")
    order_create.add_argument("festivalier_id")
    order_create.add_argument(
        "items",
        help="Items as comma-separated name:qty pairs, e.g. 'Mojito:2, Eau plate:1'"
    )
    order_get = order_sub.add_parser("get", help="Get an order by id")
    order_get.add_argument("order_id")
    order_list = order_sub.add_parser("list", help="List orders (optionally filter by festivalier)")
    order_list.add_argument("--festivalier", dest="festivalier", required=False)
    order_list.add_argument("--status", dest="status", required=False)

    args = parser.parse_args()

    # If no args, behave like before
    if len(sys.argv) == 1:
        print("Application wired. Available components:", list(app.keys()))
        return

    stock_repo = app.get("stock_repository")
    order_repo = app.get("order_repository")
    use_case = app.get("use_case")

    # Dispatch
    if args.cmd == "stock":
        if args.action == "list":
            print_stock(stock_repo)
        elif args.action == "set":
            stock_repo.set_quantity(args.name, args.quantity)
            print(f"Set {args.name} -> {args.quantity}")
        else:
            parser.print_help()

    elif args.cmd == "order":
        if args.action == "create":
            try:
                items = parse_items_args(args.items)
                command = PasserCommandeCommand(festivalier_id=args.festivalier_id, items=items)
                result = use_case.execute(command)
                print(f"Created order: {getattr(result, 'id', repr(result))}")
            except (ArticleInconnuException, StockInsuffisantException) as e:
                print(f"Error: {e}")
        elif args.action == "get":
            commande = None
            if hasattr(order_repo, "get_by_id"):
                commande = order_repo.get_by_id(args.order_id)
            elif hasattr(order_repo, "_store"):
                commande = order_repo._store.get(args.order_id)
            print_order(commande)
        elif args.action == "list":
            results = []
            if args.festivalier and args.status and hasattr(order_repo, "find_by_festivalier_and_status"):
                results = order_repo.find_by_festivalier_and_status(args.festivalier, args.status)
            else:
                # Fallback: iterate in-memory store if available
                store = getattr(order_repo, "_store", {})
                results = list(store.values())
                if args.festivalier:
                    results = [r for r in results if r.festivalier_id == args.festivalier]
                if args.status:
                    results = [r for r in results if r.status == args.status]
            for c in results:
                print_order(c)
                print("---")
        else:
            parser.print_help()

    else:
        parser.print_help()


def run_interactive(app_components):
    stock_repo = app_components.get("stock_repository")
    order_repo = app_components.get("order_repository")
    use_case = app_components.get("use_case")

    print("Entering interactive mode. Type 'help' for commands, 'quit' to exit.")
    while True:
        try:
            line = input("buvette> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in ("quit", "exit"):
            break
        if line == "help":
            print(
                "Commands: stock list | stock set NAME QTY | order create FESTIVALIER",
                "NAME:QTY ... | order get ID | order list",
            )
            continue
        parts = line.split()
        try:
            if parts[0] == "stock":
                if parts[1] == "list":
                    for k, v in getattr(stock_repo, "stock", {}).items():
                        print(f"{k}: {v}")
                elif parts[1] == "set":
                    stock_repo.set_quantity(parts[2], int(parts[3]))
                    print("OK")
            elif parts[0] == "order":
                if parts[1] == "create":
                    festivalier = parts[2]
                    raw = ' '.join(parts[3:])
                    items = parse_items_args(raw)
                    command = PasserCommandeCommand(festivalier_id=festivalier, items=items)
                    result = use_case.execute(command)
                    print(f"Created: {getattr(result, 'id', repr(result))}")
                elif parts[1] == "get":
                    oid = parts[2]
                    commande = None
                    if hasattr(order_repo, "get_by_id"):
                        commande = order_repo.get_by_id(oid)
                    elif hasattr(order_repo, "_store"):
                        commande = order_repo._store.get(oid)
                    if commande:
                        print_order(commande)
                    else:
                        print("not found")
                elif parts[1] == "list":
                    store = getattr(order_repo, "_store", {})
                    for c in store.values():
                        print_order(c)
                        print("---")
        except Exception as e:
            print("Error:", e)


def run_server(app_components, host: str = "127.0.0.1", port: int = 8000):
    stock_repo = app_components.get("stock_repository")
    order_repo = app_components.get("order_repository")
    use_case = app_components.get("use_case")

    class Handler(BaseHTTPRequestHandler):
        def _set_json(self, code=200):
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)
            if path == "/":
                try:
                    with open("app/static/index.html", "rb") as f:
                        data = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(data)
                except Exception:
                    self.send_response(404)
                    self.end_headers()
                return
            # /api/stock -> list all stock
            if path == "/api/stock":
                self._set_json()
                body = {k: v for k, v in getattr(stock_repo, "stock", {}).items()}
                self.wfile.write(json.dumps(body).encode())
                return

            # /api/stock/{name} -> single item
            if path.startswith("/api/stock/"):
                name = path[len("/api/stock/"):]
                self._set_json()
                qty = getattr(stock_repo, "stock", {}).get(name)
                if qty is None:
                    self.wfile.write(json.dumps({"error": "not found"}).encode())
                else:
                    self.wfile.write(json.dumps({"name": name, "quantity": qty}).encode())
                return

            # /api/orders with optional query params
            if path == "/api/orders":
                festivalier = qs.get("festivalier", [None])[0]
                status = qs.get("status", [None])[0]
                self._set_json()
                store = getattr(order_repo, "_store", {})
                results = list(store.values())
                if festivalier:
                    results = [r for r in results if r.festivalier_id == festivalier]
                if status:
                    results = [r for r in results if r.status == status]
                out = []
                for c in results:
                    lines_list = [
                        {"name": ligne.article.name, "qty": ligne.quantite}
                        for ligne in c.lignes
                    ]
                    out.append(
                        {
                            "id": c.id,
                            "festivalier_id": c.festivalier_id,
                            "status": c.status,
                            "lines": lines_list,
                        }
                    )
                self.wfile.write(json.dumps(out).encode())
                return

            # /api/order/{id}
            if path.startswith("/api/order/"):
                oid = path[len("/api/order/"):]
                self._set_json()
                commande = None
                if hasattr(order_repo, "get_by_id"):
                    commande = order_repo.get_by_id(oid)
                else:
                    commande = getattr(order_repo, "_store", {}).get(oid)
                if not commande:
                    self.wfile.write(json.dumps({}).encode())
                else:
                    lines_list = [
                        {"name": ligne.article.name, "qty": ligne.quantite}
                        for ligne in commande.lignes
                    ]
                    out = {
                        "id": commande.id,
                        "festivalier_id": commande.festivalier_id,
                        "status": commande.status,
                        "lines": lines_list,
                    }
                    self.wfile.write(json.dumps(out).encode())
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            parsed = urlparse(self.path)
            path = parsed.path
            # POST /api/order -> create
            if path == "/api/order":
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                try:
                    payload = json.loads(raw)
                    festivalier = payload.get("festivalier_id")
                    items = payload.get("items", [])
                    command = PasserCommandeCommand(festivalier_id=festivalier, items=items)
                    result = use_case.execute(command)
                    self._set_json(201)
                    self.wfile.write(json.dumps({"id": getattr(result, "id", None)}).encode())
                except Exception as e:
                    self._set_json(400)
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                return

            # POST /api/order/{id}/modify -> modify order items
            if path.startswith("/api/order/") and path.endswith("/modify"):
                oid = path[len("/api/order/"):-len("/modify")]
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                try:
                    payload = json.loads(raw)
                    items = payload.get("items", [])
                    # fetch existing order
                    commande = None
                    if hasattr(order_repo, "get_by_id"):
                        commande = order_repo.get_by_id(oid)
                    else:
                        commande = getattr(order_repo, "_store", {}).get(oid)
                    if not commande:
                        self._set_json(404)
                        self.wfile.write(json.dumps({"error": "not found"}).encode())
                        return
                    # construct lignes
                    lignes = [LigneCommande(article=Article(name=i["name"]), quantite=i["quantity"]) for i in items]
                    commande.lignes = lignes
                    # persist
                    if hasattr(order_repo, "save"):
                        order_repo.save(commande)
                    else:
                        getattr(order_repo, "_store", {})[commande.id] = commande
                    self._set_json(200)
                    self.wfile.write(json.dumps({"id": commande.id}).encode())
                except Exception as e:
                    self._set_json(400)
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                return

            # POST /api/order/{id}/status -> update status
            if path.startswith("/api/order/") and path.endswith("/status"):
                # path like /api/order/{id}/status
                oid = path[len("/api/order/"):-len("/status")]
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                try:
                    payload = json.loads(raw)
                    status = payload.get("status")
                    if hasattr(order_repo, "update_status"):
                        order_repo.update_status(oid, status)
                        self._set_json(200)
                        self.wfile.write(json.dumps({"id": oid, "status": status}).encode())
                    else:
                        self._set_json(404)
                        self.wfile.write(json.dumps({"error": "not available"}).encode())
                except Exception as e:
                    self._set_json(400)
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                return

            # POST /api/stock/{name} -> set quantity via JSON {quantity: N}
            if path.startswith("/api/stock/"):
                name = path[len("/api/stock/"):]
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                try:
                    payload = json.loads(raw)
                    qty = int(payload.get("quantity"))
                    if hasattr(stock_repo, "set_quantity"):
                        stock_repo.set_quantity(name, qty)
                        self._set_json(200)
                        self.wfile.write(json.dumps({"name": name, "quantity": qty}).encode())
                    else:
                        self._set_json(404)
                        self.wfile.write(json.dumps({"error": "not available"}).encode())
                except Exception as e:
                    self._set_json(400)
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                return
            self.send_response(404)
            self.end_headers()

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Serving UI at http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server")
        server.server_close()


if __name__ == "__main__":
    # Allow invocation as a module: `python -m app.main [args]`
    app_components = create_application()
    # If user passed 'interactive' or 'serve' as top-level args, handle them.
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        run_interactive(app_components)
    elif len(sys.argv) > 1 and sys.argv[1] == "serve":
        # Remove the subcommand so argparse inside main() still works if needed
        # Accept optional host:port after 'serve'
        host = "127.0.0.1"
        port = 8000
        if len(sys.argv) >= 3:
            maybe = sys.argv[2]
            if ":" in maybe:
                host, port_s = maybe.split(":", 1)
                port = int(port_s)
        run_server(app_components, host, port)
    else:
        main()

