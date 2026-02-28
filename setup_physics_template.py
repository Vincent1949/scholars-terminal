"""
Switch to Physics Quantum template for testing
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from research_scanner.template_manager import TemplateManager

# Load Physics template
manager = TemplateManager()
template = manager.load_template('physics_quantum')

# Save as user_config
manager.save_template('user_config', template)

print("[OK] Physics - Quantum & Condensed Matter template saved")
print()
print(f"Domain: {template.domain}")
print(f"Topics: {len(template.topics)}")
for i, topic in enumerate(template.topics, 1):
    print(f"  {i}. {topic.name}")
print()
print("Sources:")
for source, config in template.sources.items():
    if config.enabled:
        print(f"  [X] {source}")
        if config.categories:
            print(f"    Categories: {len(config.categories)}")
print()
print("Settings:")
print(f"  Relevance threshold: {template.relevance_threshold}")
print(f"  Days lookback: {template.days_lookback}")
print()
print("Ready to test Physics template!")
