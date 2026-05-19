import csv
import sys
import os

def calculate_points(r_high, r_low):
    higher_won = r_high >= r_low
    diff = abs(r_high - r_low)
    if diff <= 12: return 8 if higher_won else 8
    elif diff <= 37: return 7 if higher_won else 10
    elif diff <= 62: return 6 if higher_won else 13
    elif diff <= 87: return 5 if higher_won else 16
    elif diff <= 112: return 4 if higher_won else 20
    elif diff <= 137: return 3 if higher_won else 25
    elif diff <= 162: return 2 if higher_won else 30
    elif diff <= 187: return 2 if higher_won else 35
    elif diff <= 212: return 1 if higher_won else 40
    elif diff <= 237: return 1 if higher_won else 45
    else: return 0 if higher_won else 50

def calc_special_adjustment(wins_opp, losses_opp):
    wins_opp.sort(reverse=True)
    losses_opp.sort()
    
    if len(losses_opp) == 0:
        return sum(wins_opp[:2]) / min(len(wins_opp), 2)
        
    worst_loss = min(losses_opp)
    best_win = max(wins_opp)
    
    if worst_loss > best_win:
        return sum(wins_opp[:2]) / min(len(wins_opp), 2)
        
    cum_sum = 0
    count = 0
    
    for w, l in zip(wins_opp, losses_opp):
        if l > w:
            break
            
        test_sum = cum_sum + w + l
        test_count = count + 2
        test_mean = test_sum / test_count
        
        if count > 0:
            if w > test_mean and l > test_mean:
                cum_sum += w
                count += 1
                break
            elif w < test_mean and l < test_mean:
                cum_sum += l
                count += 1
                break
                
        cum_sum = test_sum
        count = test_count
        
    return cum_sum / count

def run_calculation(output_dir="."):
    players = {}
    matches = []
    
    matches_csv = os.path.join(output_dir, 'matches.csv')
    if not os.path.exists(matches_csv):
        print(f"File not found: {matches_csv}")
        return
        
    with open(matches_csv) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            w_name, w_rating, l_name, l_rating, event = row
            w_rating = int(w_rating) if w_rating else 0
            l_rating = int(l_rating) if l_rating else 0
            
            if w_name not in players:
                players[w_name] = {'initial': w_rating, 'matches_rated': [], 'adjusted': None}
            if l_name not in players:
                players[l_name] = {'initial': l_rating, 'matches_rated': [], 'adjusted': None}
                
            matches.append((w_name, l_name))
            
            if l_rating > 0:
                players[w_name]['matches_rated'].append((l_name, l_rating, True))
            if w_rating > 0:
                players[l_name]['matches_rated'].append((w_name, w_rating, False))

    # Pass 1: Rated Players
    for name, p in players.items():
        initial = p['initial']
        if initial > 0:
            net_points = 0
            wins_points = []
            for opp_name, opp_rating, is_win in p['matches_rated']:
                if is_win:
                    pts = calculate_points(initial, opp_rating)
                    net_points += pts
                    wins_points.append(pts)
                else:
                    pts = calculate_points(opp_rating, initial)
                    net_points -= pts
                    
            c1 = net_points >= 150
            c2 = sum(1 for pts in wins_points if pts == 50) >= 3
            c3 = False
            if sum(1 for pts in wins_points if pts == 50) >= 2:
                fifty_diffs = []
                for opp_name, opp_rating, is_win in p['matches_rated']:
                    if is_win and calculate_points(initial, opp_rating) == 50:
                        fifty_diffs.append(opp_rating - initial)
                fifty_diffs.sort(reverse=True)
                if len(fifty_diffs) >= 2 and (fifty_diffs[0] + fifty_diffs[1]) >= 700:
                    c3 = True
                    
            if c1 or c2 or c3:
                wins_opp = [r for n, r, w in p['matches_rated'] if w]
                losses_opp = [r for n, r, w in p['matches_rated'] if not w]
                p['adjusted'] = round(calc_special_adjustment(wins_opp, losses_opp))
            else:
                c4 = net_points >= 60
                c5 = (net_points >= 40) and (sum(1 for pts in wins_points if pts >= 20) >= 2)
                if c4 or c5:
                    p['adjusted'] = initial + net_points

    # Pass 2: Unrated Players
    for name, p in players.items():
        if p['initial'] == 0:
            wins_opp = [r for n, r, w in p['matches_rated'] if w]
            losses_opp = [r for n, r, w in p['matches_rated'] if not w]
            
            if not wins_opp and not losses_opp:
                p['adjusted'] = 200
                continue
                
            if len(wins_opp) == 0 and len(losses_opp) > 0:
                p['adjusted'] = 200
            elif len(losses_opp) == 0 and len(wins_opp) > 0:
                p['adjusted'] = max(wins_opp)
            else:
                worst_loss = min(losses_opp)
                best_win = max(wins_opp)
                if worst_loss >= best_win:
                    p['adjusted'] = best_win
                else:
                    p['adjusted'] = round(calc_special_adjustment(wins_opp, losses_opp))
                p['adjusted'] = max(p['adjusted'], 200)

    # Final Pass
    for name, p in players.items():
        p['baseline'] = p['adjusted'] if p['adjusted'] is not None else p['initial']
        p['final_net'] = 0

    for w_name, l_name in matches:
        w_base = players[w_name]['baseline']
        l_base = players[l_name]['baseline']
        
        pts = calculate_points(w_base, l_base)
        
        players[w_name]['final_net'] += pts
        loss_pts = min(pts, 3) if l_base < 100 else pts
        players[l_name]['final_net'] -= loss_pts

    # Generate Output
    output_rows = []
    for name, p in players.items():
        final_rating = p['baseline'] + p['final_net']
        initial_rating_str = str(p['initial'])
        if p['initial'] == 0:
            # Unrated player
            adj_str = str(p['adjusted'])
            change = final_rating - 0
        else:
            adj_str = str(p['adjusted']) if p['adjusted'] is not None else "n/a"
            change = final_rating - p['initial']
            
        output_rows.append([name, initial_rating_str, adj_str, final_rating, change])

    output_rows.sort(key=lambda x: x[0])
    
    output_csv = os.path.join(output_dir, 'calculated_ratings.csv')
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Player Name', 'Initial Rating', 'Adjusted Rating', 'Final Rating', 'Rating Change'])
        writer.writerows(output_rows)

    print(f"Calculated ratings successfully and saved to {output_csv}")

if __name__ == "__main__":
    output_dir = "."
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    run_calculation(output_dir)
