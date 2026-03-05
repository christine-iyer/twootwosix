#!/usr/bin/env python3
"""
Compare 2024 and 2026 Texas Senate primary results.
"""

import pandas as pd
import sys

def load_and_summarize(year, party):
    """Load and summarize election data."""
    party_abbr = party.lower()[:3]
    filename = f"texas_{party_abbr}_senate_{year}.csv"
    
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return None
    
    # Detect data format
    if 'candidate_name' in df.columns:
        # 2026 format: long format with candidate_name and votes columns
        totals = df.groupby('candidate_name')['votes'].sum().to_dict()
        num_units = df['county'].nunique()
    else:
        # 2024 format: wide format with candidate_votes columns
        vote_cols = [col for col in df.columns if col.endswith('_votes') and col != 'total_votes']
        candidates = [col.replace('_votes', '') for col in vote_cols]
        
        totals = {}
        for cand in candidates:
            total_votes = df[f'{cand}_votes'].sum()
            totals[cand] = total_votes
        
        num_units = len(df)
    
    # Sort by votes
    sorted_candidates = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    
    total_votes_cast = sum(totals.values())
    
    print(f"\n{year} Texas {party} Senate Primary")
    print("=" * 60)
    print(f"Total votes cast: {total_votes_cast:,}")
    print(f"Counties/Precincts: {len(df)}")
    print(f"\nCandidate Results:")
    print("-" * 60)
    
    for rank, (cand, votes) in enumerate(sorted_candidates, 1):
        pct = (votes / total_votes_cast * 100) if total_votes_cast > 0 else 0
        print(f"{rank}. {cand:30s} {votes:>10,} ({pct:>5.2f}%)")
    
    return {
        'year': year,
        'party': party,
        'total_votes': total_votes_cast,
        'num_units': len(df),
        'winner': sorted_candidates[0][0] if sorted_candidates else 'N/A',
        'winner_pct': (sorted_candidates[0][1] / total_votes_cast * 100) if sorted_candidates and total_votes_cast > 0 else 0,
        'candidates': sorted_candidates
    }

def main():
    print("\n" + "=" * 60)
    print("TEXAS SENATE PRIMARY COMPARISON: 2024 vs 2026")
    print("=" * 60)
    
    # Democratic comparisons
    dem_2024 = load_and_summarize(2024, 'Democratic')
    dem_2026 = load_and_summarize(2026, 'Democratic')
    
    # Republican comparisons
    rep_2024 = load_and_summarize(2024, 'Republican')
    rep_2026 = load_and_summarize(2026, 'Republican')
    
    # Summary comparison
    if dem_2024 and dem_2026:
        print(f"\n\n{'='*60}")
        print("DEMOCRATIC PRIMARY COMPARISON")
        print(f"{'='*60}")
        print(f"2024 Winner: {dem_2024['winner']} ({dem_2024['winner_pct']:.2f}%)")
        print(f"2026 Winner: {dem_2026['winner']} ({dem_2026['winner_pct']:.2f}%)")
        print(f"\nTurnout Change:")
        turnout_change = dem_2026['total_votes'] - dem_2024['total_votes']
        turnout_pct_change = (turnout_change / dem_2024['total_votes'] * 100) if dem_2024['total_votes'] > 0 else 0
        print(f"  2024: {dem_2024['total_votes']:,} votes")
        print(f"  2026: {dem_2026['total_votes']:,} votes")
        print(f"  Change: {turnout_change:+,} ({turnout_pct_change:+.2f}%)")
    
    if rep_2024 and rep_2026:
        print(f"\n\n{'='*60}")
        print("REPUBLICAN PRIMARY COMPARISON")
        print(f"{'='*60}")
        print(f"2024 Winner: {rep_2024['winner']} ({rep_2024['winner_pct']:.2f}%)")
        print(f"2026 Winner: {rep_2026['winner']} ({rep_2026['winner_pct']:.2f}%)")
        print(f"\nTurnout Change:")
        turnout_change = rep_2026['total_votes'] - rep_2024['total_votes']
        turnout_pct_change = (turnout_change / rep_2024['total_votes'] * 100) if rep_2024['total_votes'] > 0 else 0
        print(f"  2024: {rep_2024['total_votes']:,} votes")
        print(f"  2026: {rep_2026['total_votes']:,} votes")
        print(f"  Change: {turnout_change:+,} ({turnout_pct_change:+.2f}%)")

if __name__ == "__main__":
    main()
