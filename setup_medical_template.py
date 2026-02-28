"""
Automated setup for testing - selects Medical template
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from research_scanner.template_manager import TemplateManager
from research_scanner.config import TopicConfig

# Load medical template
manager = TemplateManager()
template = manager.load_template('medical_cardiac')

# Save as user_config
manager.save_template('user_config', template)

print("[OK] Medical - Cardiac Surgery template saved as user_config")
print()
print(f"Domain: {template.domain}")
print(f"Topics: {len(template.topics)}")
for topic in template.topics:
    print(f"  - {topic.name}")
print()
print("Sources:")
for source, config in template.sources.items():
    if config.enabled:
        print(f"  [X] {source}")
        if config.queries:
            print(f"    Queries: {len(config.queries)}")
print()
print("Settings:")
print(f"  Relevance threshold: {template.relevance_threshold}")
print(f"  Days lookback: {template.days_lookback}")
print()
print("="*70)
print("Medical template configured! Now test the scanner:")
print("  1. python test_template_integration.py  (verify user_config loads)")
print("  2. python Scholars_api.py               (start API)")
print("  3. curl -X POST http://localhost:8000/api/research/scan")
print("="*70)
