#!/usr/bin/env python3
import json

with open(r'C:\Coding-projects\MCP-Server\all_clients_quick.json', 'r', encoding='utf-8') as f:
    clients = json.load(f)

print(f'Total Unique Clients: {len(clients)}')
print(f'\nClients with Policy Numbers: {sum(1 for c in clients if c.get("Policy Number"))}')
print(f'Clients with Phone Numbers: {sum(1 for c in clients if c.get("Phone"))}')
print(f'Clients with Email Addresses: {sum(1 for c in clients if c.get("Email"))}')
print(f'Clients with Premium Data: {sum(1 for c in clients if c.get("Premium"))}')
print(f'\nSample of first 15 client names:')
for i, client in enumerate(clients[:15], 1):
    policy = client.get("Policy Number", "N/A")
    premium = client.get("Premium", "N/A")
    phone = client.get("Phone", "N/A")
    print(f'{i:2}. {client["Name"]:30} | Policy: {policy:15} | Premium: ${premium:8} | Phone: {phone}')
