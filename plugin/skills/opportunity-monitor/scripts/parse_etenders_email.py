#!/usr/bin/env python3
"""
Parses eTenders daily digest emails into structured JSON.
"""
import sys
import json
import re

def parse_email(text):
    opportunities = []
    
    # Simple regex to catch common eTenders digest patterns
    # e.g., "Title: Construction of New School\nAuthority: Dept of Ed\nDeadline: 12/08/2025"
    blocks = re.split(r'\n\s*\n', text)
    
    for block in blocks:
        if 'Title:' in block or 'Tender:' in block:
            opp = {
                "title": "",
                "authority": "",
                "deadline": "",
                "link": ""
            }
            
            for line in block.split('\n'):
                line = line.strip()
                if line.startswith('Title:') or line.startswith('Tender:'):
                    opp['title'] = line.split(':', 1)[1].strip()
                elif line.startswith('Authority:') or line.startswith('Client:'):
                    opp['authority'] = line.split(':', 1)[1].strip()
                elif line.startswith('Deadline:') or line.startswith('Closing:'):
                    opp['deadline'] = line.split(':', 1)[1].strip()
                elif 'http' in line:
                    opp['link'] = re.search(r'(https?://[^\s]+)', line).group(1) if re.search(r'(https?://[^\s]+)', line) else ""
            
            if opp['title']:
                opportunities.append(opp)
                
    return opportunities

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            text = f.read()
    else:
        text = sys.stdin.read()
        
    result = parse_email(text)
    print(json.dumps(result, indent=2))
