import sys
import re

def normalize_logic_expression(expression):
    """
    Takes a raw logic string like: "(B && A) || (D && C)"
    Returns a sorted canonical form: (('A', 'B'), ('C', 'D'))
    """
    # 1. Split by OR (||)
    # We use a list to collect the clauses
    clauses = expression.split('||')
    
    canonical_clauses = []
    
    for clause in clauses:
        # 2. Clean up: Remove parentheses and whitespace
        clean_clause = clause.replace('(', '').replace(')', '').strip()
        if not clean_clause:
            continue
            
        # 3. Split by AND (&&) to get the variables
        variables = [v.strip() for v in clean_clause.split('&&')]
        
        # 4. Sort variables alphabetically so (B && A) becomes (A, B)
        # Convert to tuple to make it hashable/immutable
        canonical_clauses.append(tuple(sorted(variables)))
    
    # 5. Sort the clauses themselves so ((C,D), (A,B)) becomes ((A,B), (C,D))
    return tuple(sorted(canonical_clauses))

def parse_logic_line(chunk):
    """
    Parses a full logic line like: "rb@F, (A && B) || (C)"
    Returns: ('LOGIC', 'rb@F', (('A', 'B'), ('C')))
    """
    header, expression = chunk.split(',', 1)
    canonical_expr = normalize_logic_expression(expression)
    return ('LOGIC', header.strip(), canonical_expr)

def parse_interaction_line(node, chunk):
    # Split by ; or : (regular expression)
    parts = re.split(r'[;:]', chunk)
    
    # Clean and sort the interaction strings
    # e.g. " cycb@E... " -> "cycb@E..."
    return [node + '@' + p.strip() for p in parts if p.strip()]

def parse_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read().strip()
    if 'network is consistent' in content:
        return content

    # Split by the main separator '/' between nodes
    raw_chunks = content.split('/')
    parsed_data = set()
    for chunk in raw_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        if ':' in chunk or ';' in chunk:
            fields = chunk.split('@')
            node, clean_chunk = fields[0], fields[1]
            for subchunk in parse_interaction_line(node, clean_chunk):
                parsed_data.add(parse_logic_line(subchunk))
        else:
            parsed_data.add(parse_logic_line(chunk))
            
    return parsed_data

def main():
    if len(sys.argv) != 3:
        print(f'Usage: python {sys.argv[0]} <modrev_file> <pymodrev_file>')
        sys.exit(1)
    file1 = sys.argv[-2]
    file2 = sys.argv[-1]

    try:
        # Parse both files into canonical sets
        data1 = parse_file(file1)
        data2 = parse_file(file2)

        if data1 != data2:
            # Calculate differences
            only_in_1 = data1 - data2
            only_in_2 = data2 - data1
            
            if only_in_1:
                print(f"  {file1}")
                for item in only_in_1:
                    print(f"    {item}")
                    
            if only_in_2:
                print(f"  {file2}")
                for item in only_in_2:
                    print(f"    {item}")

    except FileNotFoundError as e:
        print(f"Error: File not found - {e.filename}")
    except Exception as e:
        print(f"Error processing files: {e}")

if __name__ == "__main__":
    main()
