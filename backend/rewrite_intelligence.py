import re

file_path = "backend/app/api/endpoints/intelligence.py"
with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

def replace_except(match):
    indent = match.group(1)
    e_var = match.group(2)
    return (
        f"{indent}except Exception as {e_var}:\n"
        f"{indent}    from fastapi import HTTPException\n"
        f"{indent}    logger.error(f\"Unhandled error: {{{e_var}}}\")\n"
        f"{indent}    raise HTTPException(status_code=500, detail=str({e_var}))\n\n"
    )

# Use a regex that matches `except Exception as x:` and all its indented block.
# A block continues as long as lines are strictly deeper indented than the except line, or are empty lines.
new_code = []
lines = code.split('\n')
i = 0
while i < len(lines):
    line = lines[i]
    m = re.match(r'^(\s+)except Exception as (\w+):', line)
    if m:
        indent = m.group(1)
        e_var = m.group(2)
        new_code.append(line)
        new_code.append(f"{indent}    from fastapi import HTTPException")
        new_code.append(f"{indent}    logger.error(f\"Unhandled error: {{{e_var}}}\")")
        new_code.append(f"{indent}    raise HTTPException(status_code=500, detail=str({e_var}))")
        
        # skip lines that are indented more than current indent
        i += 1
        while i < len(lines) and (lines[i].startswith(indent + ' ') or lines[i].strip() == ''):
            i += 1
        continue
        
    new_code.append(line)
    i += 1

with open(file_path, "w", encoding="utf-8") as f:
    f.write('\n'.join(new_code))

print("Rewrote intelligence.py")