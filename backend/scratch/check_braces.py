
def check_balance(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stack_braces = []
    stack_parens = []
    for i, char in enumerate(content):
        if char == '{':
            stack_braces.append(i)
        elif char == '}':
            if not stack_braces:
                print(f"Extra closing brace at char {i}: {content[max(0, i-20):i+20]}")
            else:
                stack_braces.pop()
        elif char == '(':
            stack_parens.append(i)
        elif char == ')':
            if not stack_parens:
                print(f"Extra closing paren at char {i}: {content[max(0, i-20):i+20]}")
            else:
                stack_parens.pop()
    
    if stack_braces:
        for i in stack_braces:
            print(f"Unclosed brace at char {i}: {content[max(0, i-20):i+20]}")
    if stack_parens:
        for i in stack_parens:
            print(f"Unclosed paren at char {i}: {content[max(0, i-20):i+20]}")
    
    if not stack_braces and not stack_parens:
        print("All balanced!")

check_balance('frontend/src/components/CommercePanel.tsx')
