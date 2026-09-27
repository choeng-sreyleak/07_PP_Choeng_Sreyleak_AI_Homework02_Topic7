"""Agent logic for the shopping assistant.

Responsibilities:
- interpret the user request
- decide which tool call to use next
- handle shopping tasks such as search, stock check, buy, and delete
- keep the app in local offline mode with simple rule-based behavior
"""

import re

from harness import MAX_ITERATIONS, execute_tool


class ShoppingAgent:
    def __init__(
        self,
        role: str = "customer",
        verbose: bool = True,
        confirm_delete: bool = False,
        confirm_buy: bool = False,
    ):
        self.role = role
        self.verbose = verbose
        self.confirm_delete = confirm_delete
        self.confirm_buy = confirm_buy

    def run(self, user_request: str) -> str:
        self._log(f"USER  ({self.role}): {user_request}")
        return self._run_loop(user_request)

    def _confirm_delete(self, product: dict) -> bool:
        if self.confirm_delete:
            return True

        product_id = product["id"]
        product_name = product["name"]
        product_price = product["price"]
        product_stock = product["stock"]

        print("\nProduct to delete:")
        print("{")
        print(f"  'id': {product_id},")
        print(f"  'name': '{product_name}',")
        print(f"  'price': ${product_price},")
        print(f"  'stock': {product_stock}")
        print("}")

        try:
            answer = input(
                f"Are you sure you want to delete product {product_id} ({product_name})? Type YES to approve: "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False

        return answer == "yes"

    def _confirm_buy(self, product: dict, quantity: int) -> bool:
        if self.confirm_buy:
            return True

        product_id = product["id"]
        product_name = product["name"]
        product_price = product["price"]
        total_price = round(product_price * quantity, 2)

        print("\nProduct to buy:")
        print("{")
        print(f"  'id': {product_id},")
        print(f"  'name': '{product_name}',")
        print(f"  'price': ${product_price},")
        print(f"  'quantity': {quantity},")
        print(f"  'total': ${total_price}")
        print("}")

        try:
            answer = input(
                f"Are you sure you want to buy {quantity}x '{product_name}' (id={product_id})? Type YES to approve: "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False

        return answer == "yes"

    def _run_loop(self, user_request: str) -> str:
        text = user_request.lower()
        step = 0

        if "delete" in text or "remove" in text:
            if self.role != "admin":
                final = "Delete failed: Role 'customer' is not permitted to call 'delete_product'."
                self._log(f"AGENT (final): {final}")
                return final

            step += 1
            product_id = self._extract_product_id(text)

            info_result = execute_tool("get_product", {"product_id": product_id}, self.role)
            self._log(f"STEP {step}: agent looks up product details before delete")
            self._log(f"        -> result: {info_result}")

            if not info_result.get("ok"):
                final = f"Delete failed: {info_result.get('message')}"
                self._log(f"AGENT (final): {final}")
                return final

            product = info_result["product"]
            if not self._confirm_delete(product):
                final = "Delete cancelled: human approval was not given."
                self._log(f"AGENT (final): {final}")
                return final

            step += 1
            self._log(f"STEP {step}: agent calls delete_product({{'product_id': {product_id}}})")
            result = execute_tool("delete_product", {"product_id": product_id}, self.role)
            self._log(f"        -> result: {result}")

            if result.get("ok"):
                final = result["message"]
            else:
                final = f"Delete failed: {result.get('message')}"

            self._log(f"AGENT (final): {final}")
            return final

        step += 1
        keyword = self._extract_keyword(text)
        self._log(f"STEP {step}: agent calls search_product({{'query': '{keyword}'}})")
        search_result = execute_tool("search_product", {"query": keyword}, self.role)
        self._log(f"        -> result: {search_result}")

        if step >= MAX_ITERATIONS:
            return "Reached the iteration limit."
        if not search_result.get("ok") or search_result.get("count", 0) == 0:
            return f"I couldn't find any products matching '{keyword}'."

        candidates = search_result["results"]
        chosen = candidates[0]
        wants_stock = any(word in text for word in ["stock", "available", "availability"])
        wants_buy = any(word in text for word in ["buy", "purchase", "order"])
        price_limit = self._extract_price_limit(text)
        if price_limit is not None:
            candidates = [p for p in candidates if p["price"] < price_limit]

        if wants_stock or wants_buy:
            checked = []
            in_stock = []

            for candidate in candidates:
                if step >= MAX_ITERATIONS:
                    break

                step += 1
                self._log(f"STEP {step}: agent calls check_stock({{'product_id': {candidate['id']}}})")
                stock_result = execute_tool("check_stock", {"product_id": candidate["id"]}, self.role)
                self._log(f"        -> result: {stock_result}")

                if not stock_result.get("ok"):
                    continue

                checked.append((candidate, stock_result))
                if stock_result["stock"] > 0:
                    in_stock.append((candidate, stock_result))

            if not checked:
                return f"Found '{chosen['name']}' but could not check stock for any match."

            requested_product = self._find_requested_product(candidates, text)
            requested_stock = None
            if requested_product is not None:
                requested_stock = next(
                    (result["stock"] for product, result in checked if product["id"] == requested_product["id"]),
                    0,
                )

            if wants_buy and requested_product is not None and requested_stock is not None and requested_stock <= 0:
                alternatives = [
                    (product, result)
                    for product, result in checked
                    if product["id"] != requested_product["id"] and result.get("stock", 0) > 0
                ]
                if alternatives:
                    recommended, recommended_result = max(alternatives, key=lambda item: item[1]["stock"])
                    final = (
                        f"The product you requested, '{requested_product['name']}', is out of stock. "
                        f"I recommend '{recommended['name']}' ({recommended_result['stock']} in stock)."
                    )
                    self._log(f"AGENT (final): {final}")
                    return final

                final = (
                    f"The product you requested, '{requested_product['name']}', is out of stock and no matching "
                    "alternatives are currently available."
                )
                self._log(f"AGENT (final): {final}")
                return final

            if in_stock:
                chosen, stock_result = max(in_stock, key=lambda item: item[1]["stock"])
            else:
                names = ", ".join(item["name"] for item, _ in checked)
                if not wants_buy:
                    return f"None of the matching products are currently in stock ({names})."
                chosen, stock_result = checked[0]

        if wants_buy:
            quantity = self._extract_quantity(text)
            if not self._confirm_buy(chosen, quantity):
                final = "Purchase cancelled: human approval was not given."
                self._log(f"AGENT (final): {final}")
                return final

            step += 1
            self._log(f"STEP {step}: agent calls buy_product({{'product_id': {chosen['id']}, 'quantity': {quantity}}})")
            buy_result = execute_tool("buy_product", {"product_id": chosen["id"], "quantity": quantity}, self.role)
            self._log(f"        -> result: {buy_result}")

            if not buy_result.get("ok"):
                final = f"Could not complete purchase: {buy_result.get('message')}"
                self._log(f"AGENT (final): {final}")
                return final

            final = (
                f"Purchased {buy_result['quantity']}x '{buy_result['name']}' "
                f"for ${buy_result['total_price']}. Remaining stock: {buy_result['remaining_stock']}."
            )
            self._log(f"AGENT (final): {final}")
            return final

        if wants_stock:
            in_stock_items = [
                (candidate, result)
                for candidate, result in checked
                if result.get("stock", 0) > 0
            ]
            if len(in_stock_items) == 1:
                product, result = in_stock_items[0]
                final = f"'{product['name']}' has {result['stock']} unit(s) in stock."
            else:
                items = ", ".join(
                    f"'{product['name']}' ({result['stock']} in stock)"
                    for product, result in in_stock_items
                )
                final = f"These matching products are in stock: {items}."
        else:
            names = ", ".join(f"{p['name']} (id={p['id']}, ${p['price']})" for p in candidates)
            final = f"Found {len(candidates)} match(es): {names}."

        self._log(f"AGENT (final): {final}")
        return final

    @staticmethod
    def _find_requested_product(candidates: list[dict], text: str):
        request_tokens = {
            token for token in re.findall(r"[a-z0-9]+", text.lower())
            if token not in {"buy", "product", "find", "search", "order", "purchase", "the", "a", "an", "in", "stock", "available", "availability", "currently", "laptop", "mouse", "hub", "accessory"}
            and len(token) > 1
        }

        if not request_tokens:
            return None

        for candidate in candidates:
            candidate_tokens = {
                token for token in re.findall(r"[a-z0-9]+", candidate["name"].lower())
                if len(token) > 1
            }
            if request_tokens & candidate_tokens:
                return candidate

        return None

    @staticmethod
    def _extract_keyword(text: str) -> str:
        for keyword in ["laptop", "mouse", "hub", "accessory"]:
            if keyword in text:
                return keyword

        words = re.findall(r"[a-zA-Z]+", text)
        return words[-1] if words else ""

    @staticmethod
    def _extract_quantity(text: str) -> int:
        match = re.search(r"\b(\d+)\b", text)
        return int(match.group(1)) if match else 1

    @staticmethod
    def _extract_product_id(text: str) -> int:
        match = re.search(r"\b(\d+)\b", text)
        return int(match.group(1)) if match else 1

    @staticmethod
    def _extract_price_limit(text: str):
        patterns = [
            r"under\s*(\d+(?:\.\d+)?)",
            r"below\s*(\d+(?:\.\d+)?)",
            r"less\s*than\s*(\d+(?:\.\d+)?)",
            r"lower\s*than\s*(\d+(?:\.\d+)?)",
            r"price\s*(?:is|<|<=)\s*(\d+(?:\.\d+)?)",
            r"\$(\d+(?:\.\d+)?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None

    def _log(self, line: str) -> None:
        if self.verbose:
            print(line)
