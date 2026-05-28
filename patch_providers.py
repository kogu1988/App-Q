import sys
import os

file_path = r'c:\Users\oguzk\.gemini\antigravity-ide\scratch\projeler\App-Q\packages\research_engine\providers.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

to_replace = '''        if "Defne" in system:
            system = f"{INTAKE_POLICY}\\n\\n{system}"
        else:
            system = f"{APP_Q_GENERATION_POLICY}\\n\\n{system}"'''

content = content.replace(to_replace, '')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Replaced occurrences.')
