#!/usr/bin/env python3
"""
LLM Call Log Analyzer

Analyzes JSONL log files from logs/llm_calls/ to provide insights into:
- API usage statistics
- Error rates
- Response characteristics
- Provider distribution
"""

import json
import os
from datetime import datetime
from collections import Counter
from pathlib import Path


def analyze_logs(log_dir='logs/llm_calls'):
    """Analyze all LLM call logs in the specified directory."""
    
    log_path = Path(log_dir)
    if not log_path.exists():
        print(f"❌ Log directory not found: {log_dir}")
        return
    
    log_files = list(log_path.glob('*.jsonl'))
    if not log_files:
        print(f"❌ No log files found in {log_dir}")
        return
    
    print(f"📊 Analyzing {len(log_files)} log file(s)...\n")
    
    # Collect all logs
    all_logs = []
    for log_file in sorted(log_files):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    all_logs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    if not all_logs:
        print("❌ No valid log entries found")
        return
    
    # Statistics
    total_calls = len(all_logs)
    providers = Counter(log['provider'] for log in all_logs)
    simulation_count = sum(1 for log in all_logs if log.get('simulation', False))
    error_count = sum(1 for log in all_logs if log.get('error'))
    
    # Response statistics
    response_lengths = [len(log['response'].get('text', '')) for log in all_logs if log['response'].get('success')]
    avg_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
    
    # Print results
    print("="*80)
    print("📈 LLM CALL STATISTICS")
    print("="*80)
    print(f"\n📞 Total Calls: {total_calls}")
    print(f"✅ Successful: {total_calls - error_count} ({(total_calls - error_count) / total_calls * 100:.1f}%)")
    print(f"❌ Errors: {error_count} ({error_count / total_calls * 100:.1f}%)")
    print(f"🎭 Simulation: {simulation_count} ({simulation_count / total_calls * 100:.1f}%)")
    print(f"🌐 Real API: {total_calls - simulation_count} ({(total_calls - simulation_count) / total_calls * 100:.1f}%)")
    
    print(f"\n🔧 Provider Distribution:")
    for provider, count in providers.most_common():
        print(f"  {provider}: {count} ({count / total_calls * 100:.1f}%)")
    
    print(f"\n📏 Response Statistics:")
    print(f"  Average Length: {avg_length:.0f} characters")
    if response_lengths:
        print(f"  Min Length: {min(response_lengths)} characters")
        print(f"  Max Length: {max(response_lengths)} characters")
    
    # Agent distribution (from system prompts)
    agents = Counter()
    for log in all_logs:
        system_prompt = log['request'].get('system_prompt', '').upper()
        if 'ARCHITECT' in system_prompt or 'ARCHITEKT' in system_prompt:
            agents['Architect'] += 1
        elif 'CURATOR' in system_prompt or 'KURATOR' in system_prompt:
            agents['Curator'] += 1
        elif 'TUTOR' in system_prompt:
            agents['Tutor'] += 1
        elif 'ASSESSOR' in system_prompt:
            agents['Assessor'] += 1
        else:
            agents['Unknown'] += 1
    
    print(f"\n🤖 Agent Distribution:")
    for agent, count in agents.most_common():
        print(f"  {agent}: {count} ({count / total_calls * 100:.1f}%)")
    
    # Errors
    if error_count > 0:
        print(f"\n❌ Error Details:")
        error_types = Counter(log.get('error', 'Unknown') for log in all_logs if log.get('error'))
        for error, count in error_types.most_common(5):
            print(f"  {error[:80]}: {count}")
    
    # Time distribution
    print(f"\n📅 Time Distribution:")
    dates = Counter(log['timestamp'][:10] for log in all_logs)
    for date, count in sorted(dates.items()):
        print(f"  {date}: {count} calls")
    
    print("\n" + "="*80)


def show_recent_errors(log_dir='logs/llm_calls', limit=5):
    """Show the most recent errors."""
    
    log_path = Path(log_dir)
    if not log_path.exists():
        return
    
    log_files = sorted(log_path.glob('*.jsonl'), reverse=True)
    
    errors = []
    for log_file in log_files:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log = json.loads(line)
                    if log.get('error'):
                        errors.append(log)
                        if len(errors) >= limit:
                            break
                except json.JSONDecodeError:
                    continue
        if len(errors) >= limit:
            break
    
    if errors:
        print("\n🔴 Recent Errors:")
        print("="*80)
        for i, error in enumerate(errors[:limit], 1):
            print(f"\n{i}. {error['timestamp']}")
            print(f"   Provider: {error['provider']}")
            print(f"   Error: {error['error']}")
            print(f"   Prompt: {error['request']['user_prompt'][:100]}...")
    else:
        print("\n✅ No recent errors found!")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--errors':
        show_recent_errors()
    else:
        analyze_logs()
        show_recent_errors()
