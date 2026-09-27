
# Simple Safe Shopping Agent

This project is a beginner-friendly example of an agent that can:
- receive a user request,
- decide which tool to call,
- check safety rules,
- run the tool,
- and give a final answer.

It is a small local demo, so it does not use an API key or a real LLM.

## What this project does

The agent acts like a shopping assistant for a small online store.

Examples of requests:
- "Find a laptop that is currently in stock"
- "Check all product in stock"
- "Buy 2 wireless mouse"
- "Delete product 1"

The agent decides what step to do next based on the request.

## How the flow works

```text
User request
    |
    v
Agent decides what to do
    |
    v
Call tool through harness
    |
    v
Permission check + input validation
    |
    v
Tool runs
    |
    v
Result comes back
    |
    v
Agent gives final answer
```

This is the same basic shape as a real agent system, but written in a simple way.

## Project files

- `main.py` - runs the program and accepts user input
- `agent.py` - decides which tool should be called
- `harness.py` - checks permission, validates input, and runs tools safely
- `tools.py` - the real store logic
- `schemas.py` - Pydantic validation rules for each tool

## Setup

First install the requirement:

```bash
pip install -r requirement.txt
```

Then run the project:

```bash
# Customer search example
py -3 main.py --role customer "Find a laptop that is currently in stock"

# Customer buy example
py -3 main.py --role customer "Buy 2 wireless mouse"

# Admin delete example
py -3 main.py --role admin "Delete product 1"
```

You can also run interactive mode:

```bash
py -3 main.py --role customer
```

## Tools in the project

| Tool | Description |
|---|---|
| `search_product(query)` | Search for products by keyword |
| `check_stock(product_id)` | Check how much stock a product has |
| `buy_product(product_id, quantity)` | Buy a product and reduce stock |
| `delete_product(product_id)` | Delete a product from the catalog |

## Safety rules

The program is designed to be safe.

### 1. Permission check

Not every role can do every action.

| Action | Customer | Admin |
|---|---|---|
| `search_product` | Yes | Yes |
| `check_stock` | Yes | Yes |
| `buy_product` | Yes | Yes |
| `delete_product` | No | Yes |

If a customer tries to delete, the program refuses it.

### 2. Input validation

Each tool has a schema in `schemas.py`.

Examples:
- `product_id` must be positive
- `quantity` must be positive
- `query` cannot be empty

If the input is invalid, the tool does not run.

### 3. Human approval before delete

Delete is a destructive action, so the program asks for confirmation first.

Example:

```text
Product to delete:
{
  'id': 1,
  'name': 'Aegis 14 Laptop',
  'price': $899.0,
  'stock': 0
}
Are you sure to delete product 1 ? Type YES to approve:
```

If the user does not type `YES`, the delete is cancelled.

### 4. Loop limit

The agent cannot loop forever.

The project has a max iteration limit so the loop stops safely if something goes wrong.

## Example behavior

### Search and stock example

```text
User: Find a laptop that is currently in stock
STEP 1: agent calls search_product({'query': 'laptop'})
STEP 2: agent calls check_stock({'product_id': 2})
FINAL ANSWER: 'Vertex Pro 15 Laptop' has 5 unit(s) in stock.
```

Stock queries can also list all currently available products:

```text
User: Check all product in stock
FINAL ANSWER: These matching products are in stock: 'Vertex Pro 15 Laptop' (5 in stock), 'Nimbus Air Laptop' (12 in stock), 'Wireless Mouse M1' (40 in stock), 'USB-C Hub 7-in-1' (8 in stock).
```

### Buy example

```text
User: Buy 2 wireless mouse
STEP 1: agent calls search_product({'query': 'mouse'})
STEP 2: agent calls check_stock({'product_id': 4})
STEP 3: agent calls buy_product({'product_id': 4, 'quantity': 2})
FINAL ANSWER: Purchased 2x 'Wireless Mouse M1' for $39.98. Remaining stock: 38.
```

### Delete example

```text
User: Delete product 1
Product to delete:
{
  'id': 1,
  'name': 'Aegis 14 Laptop',
  'price': $899.0,
  'stock': 0
}
Are you sure to delete product 1 ? Type YES to approve:
FINAL ANSWER: Product 'Aegis 14 Laptop' (id=1) deleted.
```

## Important idea

This project is not using a real AI model to decide what to do.
Instead, it uses simple rules and structured tool calls.

That is why it is a good beginner example of an agent:
- simple,
- clear,
- safe,
- easy to understand.

## Project structure

```text
shopping-agent/
├── README.md
├── requirements.txt
├── main.py
├── agent.py
├── tools.py
├── schemas.py
├── harness.py
```


