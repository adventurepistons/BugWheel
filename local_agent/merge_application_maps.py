import json
import os
from collections import defaultdict
import datetime

# Key properties to compare for deduplication
KEYS = [
    'url', 'tag', 'id', 'name', 'class', 'type', 'aria_label', 'role', 'text', 'text_content', 'placeholder', 'best_locator', 'css_selector', 'xpath'
]

MAP_DIR = os.path.join(os.path.dirname(__file__), 'application_maps')
PUBLIC_FILE = [f for f in os.listdir(MAP_DIR) if 'public' in f][0]
AUTH_FILE = [f for f in os.listdir(MAP_DIR) if 'authenticated' in f][0]

with open(os.path.join(MAP_DIR, PUBLIC_FILE), encoding='utf-8') as f:
    public_map = json.load(f)
with open(os.path.join(MAP_DIR, AUTH_FILE), encoding='utf-8') as f:
    auth_map = json.load(f)

# Helper to create a unique key for an element based on all key properties
def element_key(url, el):
    def safe(val):
        if isinstance(val, dict):
            return json.dumps(val, sort_keys=True)
        return str(val)
    return '|'.join([
        safe(url),
        safe(el.get('tag')),
        safe(el.get('id')),
        safe(el.get('name')),
        safe(el.get('class')),
        safe(el.get('type')),
        safe(el.get('aria_label')),
        safe(el.get('role')),
        safe(el.get('text')),
        safe(el.get('text_content')),
        safe(el.get('attributes', {}).get('placeholder')),
        safe(el.get('best_locator')),
        safe(el.get('css_selector')),
        safe(el.get('xpath')),
    ])

# Build merged map: url -> list of merged elements
def merge_maps(public_map, auth_map):
    merged = defaultdict(list)
    # url -> key -> {element, flows}
    index = defaultdict(dict)
    for flow, amap in [('public', public_map), ('authenticated', auth_map)]:
        for page in amap['application_map']:
            url = page['url']
            for el in page['elements']:
                k = element_key(url, el)
                if k in index[url]:
                    index[url][k]['flows'].append(flow)
                else:
                    el_copy = dict(el)
                    el_copy['flows'] = [flow]
                    index[url][k] = {'element': el_copy, 'flows': el_copy['flows']}
    # Flatten
    for url, elements in index.items():
        merged[url] = [v['element'] for v in elements.values()]
    # Build output structure
    merged_map = {
        'aut_id': public_map.get('aut_id', auth_map.get('aut_id', 'merged')),
        'scan_flows': ['public', 'authenticated'],
        'merged_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'application_map': []
    }
    for url, elements in merged.items():
        merged_map['application_map'].append({
            'url': url,
            'elements': elements
        })
    return merged_map

merged = merge_maps(public_map, auth_map)

with open(os.path.join(MAP_DIR, 'merged_app_map.json'), 'w', encoding='utf-8') as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)

print('Merged application map written to application_maps/merged_app_map.json') 