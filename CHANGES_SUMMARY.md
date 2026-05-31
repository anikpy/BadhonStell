# Dynamic Product Search Implementation for Orders Create Page

## Overview
Added dynamic product search functionality to the orders create page (`/admin-panel/orders/create/`) similar to the invoices create page. Users can now search for products dynamically, select from inventory, or enter custom product names.

## Changes Made

### File Modified: `/shop/templates/admin_panel/order_form.html`

#### 1. **CSS Styles Added** (Lines 181-220)
Added new CSS classes for the product search dropdown:
- `.product-search-container` - Container for search input and dropdown
- `.product-search-input` - Search input field with focus styling
- `.product-dropdown` - Fixed position dropdown menu
- `.product-dropdown.show` - Show/hide dropdown
- `.product-option` - Individual product option styling

#### 2. **JavaScript Modifications**

**Data Initialization** (Line 360):
```javascript
const PRODUCTS = {{ products_json|safe }};
const productMap = {};
PRODUCTS.forEach(p => { productMap[p.id] = p; });
```

**Key Functions:**

1. **`buildProductOptions(selectedId)`** - Builds the product select dropdown options

2. **`addItem()`** - Enhanced to include:
   - Search input field for dynamic product search
   - Search container with dropdown
   - Product select (hidden but still functional)
   - Event listeners for real-time calculation

3. **`initProductSearch(idx)`** - NEW FUNCTION - Handles:
   - **Dynamic filtering**: Shows matching products as user types
   - **Custom names**: If product not found, shows "কাস্টম নাম" option
   - **Price handling**: Makes price editable for custom products, read-only for inventory products
   - **Stock display**: Shows available stock in dropdown
   - **Dropdown positioning**: Fixed position dropdown that follows search input
   - **Event handlers**: Input, focus, and click-outside events

4. **`selectProduct(itemId, productId)`** - Updated to:
   - Work with new search input structure
   - Set price from product data
   - Allow price editing for custom products

5. **`collectItemsData()`** - Updated to:
   - Extract product name from `.product-search-input` instead of `.product-name`
   - Supports both inventory and custom product names

6. **Edit Mode** - DOMContentLoaded handler updated to:
   - Load product names into search input field
   - Properly handle edit items on page load

## Key Features

✅ **Dynamic Search**
- Type to search for products from inventory
- Case-insensitive matching
- Real-time filtering as you type

✅ **Custom Product Names**
- If product name not found in inventory, it can be entered as custom name
- Price field becomes editable for custom products
- No requirement to select from inventory

✅ **Stock Information**
- Stock quantity displayed in dropdown options
- Stock warnings shown if insufficient stock
- Cross-row stock validation

✅ **User Experience**
- Search input with Bengali placeholder text
- Dropdown positions correctly below input
- Easy selection from filtered list
- Closed on click outside

## Usage

1. Navigate to **Orders Create Page**: `http://127.0.0.1:8000/admin-panel/orders/create/`
2. Click **"পণ্য যোগ করুন"** button to add items
3. In the product field:
   - **Type to search**: Start typing product name to see suggestions
   - **Select from dropdown**: Click product name to auto-fill price and description
   - **Custom product**: Type any name not in inventory and manually enter price
4. Quantity and price fields work as before
5. Form validates and saves orders with both inventory and custom products

## Data Flow

### Product Data Structure
Each product in PRODUCTS array contains:
```javascript
{
  id: number,           // Database ID
  name: string,         // Product name
  price: float,         // Unit price
  unit: string,         // Unit display (e.g., "কেজি", "লিটার")
  stock: float         // Available stock quantity
}
```

### Item Collection Format
When form is submitted, items are collected as:
```javascript
{
  product_name: string,          // From search input (inventory or custom)
  product_description: string,   // Optional description
  quantity: number,
  unit_price: number
}
```

## Backward Compatibility

✅ All existing order functionality remains intact:
- Customer selection still works
- Cash paid and due amount calculation
- Order date and delivery date fields
- Status and delivery status fields
- Form submission and validation

## Testing Checklist

- [ ] Type partial product name - see matching products
- [ ] Select product from dropdown - price auto-fills
- [ ] Enter custom product name not in inventory - price field becomes editable
- [ ] Stock information displays correctly
- [ ] Stock warnings appear when insufficient
- [ ] Form submits with inventory products
- [ ] Form submits with custom products
- [ ] Edit mode loads product names correctly
- [ ] Multiple rows work independently
- [ ] Dropdown closes on outside click

## Files Modified
- `/shop/templates/admin_panel/order_form.html` (839 lines total)
  - Added CSS for product search (40 lines)
  - Modified JavaScript functions (200+ lines of new/modified code)
  - Updated addItem(), initProductSearch(), selectProduct(), collectItemsData() functions
  - Enhanced DOMContentLoaded event handler

## Notes

- The implementation follows the same pattern as the invoice create page
- PRODUCTS data is already provided by the server in the correct format
- Supports both Bengali and English number input via conversion functions
- Dynamic search helps users quickly find products without scrolling long lists
- Custom product names allow flexibility for ad-hoc or non-inventory items

