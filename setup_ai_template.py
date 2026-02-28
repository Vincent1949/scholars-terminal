"""
Switch to AI template for testing
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from research_scanner.template_manager import TemplateManager

# Load AI template
manager = TemplateManager()
template = manager.load_template('ai_ml')

# Save as user_config
manager.save_template('user_config', template)

print("[OK] AI & Machine Learning template saved as user_config")
print()
print(f"Domain: {template.domain}")
print(f"Topics: {len(template.topics)}")
for topic in template.topics[:5]:
    print(f"  - {topic.name}")
if len(template.topics) > 5:
    print(f"  ... and {len(template.topics) - 5} more")
print()
print("Sources:")
for source, config in template.sources.items():
    if config.enabled:
        print(f"  [X] {source}")
        if config.queries:
            print(f"    Queries: {len(config.queries)}")
        if config.categories:
            print(f"    Categories: {len(config.categories)}")
print()
print("Settings:")
print(f"  Relevance threshold: {template.relevance_threshold}")
print(f"  Days lookback: {template.days_lookback}")
print()
print("Ready to test AI template scan!")
