import re
import os

def count_commands(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    commands = []
    
    # Regex patterns
    # @app_commands.command(name="foo", ...)
    # @commands.hybrid_command(name='bar', ...)
    # group = app_commands.Group(name="baz", ...)
    
    # Pattern for decorators
    decorator_pattern = re.compile(r'@(?:app_commands\.command|commands\.hybrid_command|app_commands\.context_menu)\s*\((.*?)\)', re.DOTALL)
    
    # Pattern for groups
    group_pattern = re.compile(r'=\s*app_commands\.Group\s*\((.*?)\)', re.DOTALL)

    for match in decorator_pattern.finditer(content):
        args = match.group(1)
        name_match = re.search(r'name\s*=\s*[\'"]([^\'"]+)[\'"]', args)
        if name_match:
            commands.append(f"Command: {name_match.group(1)}")
        else:
            # Try to find positional arg if it's the first one (rare for these decorators but possible)
            # Actually, hybrid_command often uses function name if name not specified.
            # But let's just count it as "Unnamed/Inferred"
            commands.append("Command: (Inferred from function)")

    for match in group_pattern.finditer(content):
        args = match.group(1)
        # Check if parent is present
        if 'parent' not in args:
            name_match = re.search(r'name\s*=\s*[\'"]([^\'"]+)[\'"]', args)
            if name_match:
                commands.append(f"Group: {name_match.group(1)}")

    return len(commands), commands

print("Cog Analysis Results (Regex):")
print("-" * 50)
total_commands = 0
cogs_dir = 'cogs'
results = []

for filename in os.listdir(cogs_dir):
    if filename.endswith('.py'):
        count, cmds = count_commands(os.path.join(cogs_dir, filename))
        if count > 0:
            results.append((filename, count, cmds))
            total_commands += count

results.sort(key=lambda x: x[1], reverse=True)

for filename, count, cmds in results:
    print(f"{filename}: {count} commands")
    # Print first 5 commands only to save space
    for cmd in cmds[:5]:
        print(f"  - {cmd}")
    if len(cmds) > 5:
        print(f"  - ... and {len(cmds)-5} more")
    print("")

print("-" * 50)
print(f"Total Top-Level Commands (Approx): {total_commands}")
