#!/usr/bin/env python3
"""Track genuine receipts and expenses. Manual CSV input, no synthetic sales."""
import csv,sys
from pathlib import Path
from decimal import Decimal, InvalidOperation

def read(path):
    if not path.exists():return []
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def money(value):
    try:return Decimal(str(value)).quantize(Decimal('0.01'))
    except InvalidOperation:raise ValueError('Invalid amount')
def main():
    root=Path(__file__).resolve().parent
    receipts=read(root/'receipts.csv');costs=read(root/'expenses.csv')
    revenue=sum((money(r['amount_usd']) for r in receipts if r.get('status','').strip().lower()=='collected'),Decimal('0'))
    spend=sum((money(x['amount_usd']) for x in costs if x.get('status','').strip().lower()=='paid'),Decimal('0'))
    print(f'Collected revenue: ${revenue:.2f}')
    print(f'Paid expenses: ${spend:.2f}')
    print(f'Operating contribution: ${revenue-spend:.2f} (before taxes and unrecorded overhead)')
if __name__=='__main__':main()
