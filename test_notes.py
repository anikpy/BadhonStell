#!/usr/bin/env python3
"""
Test script to print customer notes from database
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from transactions.models import Customer, CustomerNote

def print_all_notes():
    """Print all customer notes"""
    print("=" * 80)
    print("CUSTOMER NOTES REPORT")
    print("=" * 80)
    
    # Get all customers
    customers = Customer.objects.all().order_by('name')
    
    if not customers:
        print("\nNo customers found in database.")
        return
    
    total_notes = 0
    
    for customer in customers:
        notes = customer.notes.all().order_by('-created_at')
        
        if notes.exists():
            print(f"\n{'='*80}")
            print(f"Customer: {customer.name} (ID: {customer.pk})")
            print(f"Mobile: {customer.mobile_number}")
            print(f"Total Notes: {notes.count()}")
            print(f"{'='*80}")
            
            for i, note in enumerate(notes, 1):
                print(f"\n  Note #{i}:")
                print(f"  Content: {note.note}")
                print(f"  Created: {note.created_at.strftime('%d/%m/%Y %H:%M')}")
                print(f"  Author: {note.created_by.username if note.created_by else 'System'}")
                print(f"  {'-'*76}")
            
            total_notes += notes.count()
    
    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"  Total Customers: {customers.count()}")
    print(f"  Total Notes: {total_notes}")
    print(f"{'='*80}\n")


def print_customer_notes(customer_id):
    """Print notes for a specific customer"""
    try:
        customer = Customer.objects.get(pk=customer_id)
        notes = customer.notes.all().order_by('-created_at')
        
        print(f"\n{'='*80}")
        print(f"Notes for: {customer.name} (ID: {customer.pk})")
        print(f"{'='*80}")
        
        if not notes.exists():
            print("\n  No notes found for this customer.\n")
            return
        
        for i, note in enumerate(notes, 1):
            print(f"\n  Note #{i}:")
            print(f"  Content: {note.note}")
            print(f"  Created: {note.created_at.strftime('%d/%m/%Y %H:%M')}")
            print(f"  Author: {note.created_by.username if note.created_by else 'System'}")
            print(f"  {'-'*76}")
        
        print(f"\n  Total: {notes.count()} notes\n")
        
    except Customer.DoesNotExist:
        print(f"\nError: Customer with ID {customer_id} not found.\n")


if __name__ == '__main__':
    print("\n📝 Customer Notes Test Script\n")
    
    if len(sys.argv) > 1:
        # Print notes for specific customer
        try:
            customer_id = int(sys.argv[1])
            print_customer_notes(customer_id)
        except ValueError:
            print("Usage: python test_notes.py [customer_id]")
            print("  customer_id: Optional. If provided, shows notes for that customer only.")
            print("  If not provided, shows all notes for all customers.\n")
    else:
        # Print all notes
        print_all_notes()