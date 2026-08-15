#!/usr/bin/env python3
import requests
import json

print("=" * 60)
print("BACKEND API TEST SUITE")
print("=" * 60)

# Test 1: Health
print("\n[TEST 1] Health Endpoint")
resp = requests.get('http://localhost:8000/api/health')
print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}")

# Test 2: Products List
print("\n[TEST 2] Products List")
resp = requests.get('http://localhost:8000/api/products')
data = resp.json()
print(f"Status: {resp.status_code}")
print(f"Total: {data['total']}")
print(f"Verified: {data['verified']}")
print(f"Needs Review: {data['needs_review']}")
print(f"Avg Confidence: {data['avg_confidence']}")
print(f"\nProducts:")
for p in data['products']:
    print(f"  - {p['id']}: {p['brand']} {p['part_number']} | Status: {p['status']} | Confidence: {p['overall_confidence']}")

# Test 3: Specific Product - P001 (Verified)
print("\n[TEST 3] Product P001 (Mean Well - Should be VERIFIED)")
resp = requests.get('http://localhost:8000/api/products/P001')
p = resp.json()
print(f"Status: {resp.status_code}")
print(f"Name: {p['product_name']}")
print(f"Status: {p['status']}")
print(f"Confidence: {p['overall_confidence']}")
print(f"Completeness: {p['completeness_pct']}%")
print(f"Review Needed: {p['review_needed']}")

# Test 4: Specific Product - P004 (Conflict)
print("\n[TEST 4] Product P004 (Siemens SITOP - Should have WEIGHT CONFLICT)")
resp = requests.get('http://localhost:8000/api/products/P004')
p = resp.json()
print(f"Status: {resp.status_code}")
print(f"Name: {p['product_name']}")
print(f"Status: {p['status']}")
print(f"Confidence: {p['overall_confidence']}")
print(f"Review Needed: {p['review_needed']}")

# Check weight attribute specifically
weight_attr = p['attributes'].get('weight', {})
print(f"\nWeight Attribute Details:")
print(f"  Value: {weight_attr.get('value')}")
print(f"  Unit: {weight_attr.get('unit')}")
print(f"  Confidence: {weight_attr.get('confidence')}")
print(f"  Conflict: {weight_attr.get('conflict')}")
print(f"  Status: {weight_attr.get('status')}")
if weight_attr.get('all_sources'):
    print(f"  Sources:")
    for src in weight_attr['all_sources']:
        print(f"    - {src.get('source_name')}: {src.get('value')} {src.get('unit')}")

# Test 5: Review Queue
print("\n[TEST 5] Review Queue")
resp = requests.get('http://localhost:8000/api/review-queue')
if resp.status_code == 200:
    queue = resp.json()
    print(f"Status: {resp.status_code}")
    print(f"Items in queue: {queue.get('total', len(queue.get('items', [])))}")
    items = queue.get('items', []) if isinstance(queue, dict) else queue
    for item in items:
        product_id = item.get('product_id', item.get('id', 'Unknown'))
        issues = item.get('issues', item.get('review_needed', []))
        print(f"  - {product_id}: {issues}")
else:
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")

print("\n" + "=" * 60)
print("API TESTS COMPLETE")
print("=" * 60)
