"""Entry point for the shopping-agent app.

Responsibilities:
- parse command-line arguments
- create the ShoppingAgent with the selected role
- run the user request and print the final answer
"""

import argparse

from agent import ShoppingAgent


def main():
    parser = argparse.ArgumentParser(description="Simple Safe Shopping Agent")
    parser.add_argument("request", nargs="*", help="The user request, e.g. 'find a laptop in stock'")
    parser.add_argument("--role", default="customer", choices=["customer", "admin"], help="Acting role")
    parser.add_argument("--confirm-delete", action="store_true", help="Skip the human approval prompt before delete actions.")
    parser.add_argument("--confirm-buy", action="store_true", help="Skip the human approval prompt before buy actions.")
    args = parser.parse_args()

    agent = ShoppingAgent(role=args.role, confirm_delete=args.confirm_delete, confirm_buy=args.confirm_buy)

    if args.request:
        user_request = " ".join(args.request)
        print("=" * 70)
        answer = agent.run(user_request)
        print("=" * 70)
        print(f"FINAL ANSWER: {answer}")
    else:
        print("Simple Shopping Agent -- interactive mode (Ctrl+C to quit)")
        print(f"Role: {args.role}")
        while True:
            try:
                user_request = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break
            if not user_request:
                continue
            print("-" * 70)
            answer = agent.run(user_request)
            print("-" * 70)
            print(f"FINAL ANSWER: {answer}")


if __name__ == "__main__":
    main()
