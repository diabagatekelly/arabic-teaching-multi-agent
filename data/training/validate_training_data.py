"""
Validate and analyze training_data.jsonl
"""
import json
from pathlib import Path

def validate_and_analyze(filepath):
    """Load, validate, and analyze the training data"""
    conversations = []
    total_turns = 0
    total_tokens = 0
    errors = []

    print(f"Loading {filepath}...")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    conv = json.loads(line)
                    conversations.append(conv)

                    # Validate structure
                    if 'messages' not in conv:
                        errors.append(f"Line {line_num}: Missing 'messages' field")
                        continue

                    # Count turns
                    turns = len(conv['messages'])
                    total_turns += turns

                    # Estimate tokens (rough: 4 chars per token)
                    conv_text = json.dumps(conv)
                    tokens = len(conv_text) // 4
                    total_tokens += tokens

                    # Validate message structure
                    for msg_idx, msg in enumerate(conv['messages']):
                        if 'role' not in msg or 'content' not in msg:
                            errors.append(f"Line {line_num}, Message {msg_idx}: Invalid message structure")

                        if msg['role'] not in ['system', 'user', 'assistant']:
                            errors.append(f"Line {line_num}, Message {msg_idx}: Invalid role '{msg['role']}'")

                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: JSON decode error - {e}")

    except FileNotFoundError:
        print(f"ERROR: File not found: {filepath}")
        return

    # Print results
    print("\n" + "="*60)
    print("VALIDATION RESULTS")
    print("="*60)

    if errors:
        print(f"\n⚠️  Found {len(errors)} errors:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    else:
        print("\n✅ No errors found!")

    print("\n" + "="*60)
    print("STATISTICS")
    print("="*60)
    print(f"Total conversations: {len(conversations)}")
    print(f"Total turns: {total_turns}")
    print(f"Average turns per conversation: {total_turns / len(conversations):.1f}")
    print(f"Estimated tokens: {total_tokens:,}")
    print(f"Average tokens per conversation: {total_tokens / len(conversations):.0f}")

    # Analyze conversation types
    print("\n" + "="*60)
    print("CONVERSATION BREAKDOWN")
    print("="*60)

    if conversations:
        # Show sample conversation structure
        sample = conversations[0]
        print(f"\nSample conversation structure:")
        print(f"  Keys: {list(sample.keys())}")
        print(f"  Number of messages: {len(sample['messages'])}")
        print(f"  Message roles: {[m['role'] for m in sample['messages'][:5]]}")

        # Count role distribution
        role_counts = {'system': 0, 'user': 0, 'assistant': 0}
        for conv in conversations:
            for msg in conv['messages']:
                role = msg.get('role')
                if role in role_counts:
                    role_counts[role] += 1

        print(f"\nRole distribution across all conversations:")
        for role, count in role_counts.items():
            print(f"  {role}: {count}")

    print("\n" + "="*60)
    print("FILE READY FOR TRAINING" if not errors else "FIX ERRORS BEFORE TRAINING")
    print("="*60)

    return len(conversations), total_turns, total_tokens, len(errors)

if __name__ == "__main__":
    filepath = Path(__file__).parent / "training_data.jsonl"
    validate_and_analyze(filepath)
