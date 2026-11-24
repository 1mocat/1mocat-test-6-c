#!/usr/bin/env python3
"""Python re-implementation of cobol/src/program.cbl (BOOKFORUM)."""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS = os.path.join(BASE, "data", "ACCOUNTS.DAT")
BOOKS = os.path.join(BASE, "data", "BOOKS.DAT")
TRANSACTIONS = os.path.join(BASE, "data", "TRANSACTIONS.DAT")
INPUT_FILE = os.path.join(BASE, "src", "INPUT.DAT")

ACC_REC = 34   # 4 + 20 + 10
BOOK_REC = 28  # 4 + 20 + 4
TRANS_REC = 22 # 4 + 10 + 4 + 4


def parse_amount(raw: bytes) -> int:
    s = raw.decode("latin-1")
    digits = "".join(c if c.isdigit() else "0" for c in s)
    return int(digits) if digits else 0


def read_input():
    with open(INPUT_FILE, "rb") as f:
        data = f.read()
    if not data:
        print("Error: Input file is empty")
        sys.exit(0)
    # Pad to full record length with spaces (COBOL behavior for short record)
    if len(data) < 22:
        data = data + b" " * (22 - len(data))
    buyer = data[0:4].decode("latin-1")
    seller = data[4:8].decode("latin-1")
    book = data[8:12].decode("latin-1")
    amount = parse_amount(data[12:22])
    return buyer, seller, book, amount


def read_fixed(path, size):
    with open(path, "rb") as f:
        data = f.read()
    return [data[i:i + size] for i in range(0, len(data), size) if len(data[i:i + size]) == size]


def main():
    buyer_id, seller_id, book_id, amount = read_input()

    accounts = read_fixed(ACCOUNTS, ACC_REC)
    books = read_fixed(BOOKS, BOOK_REC)

    buyer_found = any(r[0:4].decode("latin-1") == buyer_id for r in accounts)
    seller_found = any(r[0:4].decode("latin-1") == seller_id for r in accounts)
    book_found = False
    valid_owner = False
    for r in books:
        if r[0:4].decode("latin-1") == book_id:
            book_found = True
            if r[24:28].decode("latin-1") == seller_id:
                valid_owner = True

    print(" ")

    if not (buyer_found and seller_found and book_found and valid_owner):
        print("Transaction failed due to validation errors")
        return

    # Update ACCOUNTS
    new_accounts = []
    for r in accounts:
        aid = r[0:4].decode("latin-1")
        name = r[4:24]
        bal = int(r[24:34].decode("latin-1"))
        if aid == buyer_id:
            bal -= amount
        if aid == seller_id:
            bal += amount
        # COBOL PIC 9(10) with no SIGN — truncates to 10 digits after modular arithmetic
        bal_str = f"{bal % 10**10:010d}"
        new_accounts.append(aid.encode("latin-1") + name + bal_str.encode("latin-1"))
    with open(ACCOUNTS, "wb") as f:
        f.write(b"".join(new_accounts))

    # Update BOOKS
    new_books = []
    for r in books:
        bid = r[0:4].decode("latin-1")
        title = r[4:24]
        owner = r[24:28]
        if bid == book_id:
            owner = buyer_id.encode("latin-1")
        new_books.append(bid.encode("latin-1") + title + owner)
    with open(BOOKS, "wb") as f:
        f.write(b"".join(new_books))

    # Append transaction
    amount_str = f"{amount % 10**10:010d}"
    trans_rec = (book_id.encode("latin-1") + amount_str.encode("latin-1")
                 + seller_id.encode("latin-1") + buyer_id.encode("latin-1"))
    with open(TRANSACTIONS, "ab") as f:
        f.write(trans_rec)

    print("Transaction completed successfully")


if __name__ == "__main__":
    main()
