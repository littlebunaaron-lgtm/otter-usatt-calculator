import os
import time
import schedule
import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

# Import the refactored functions
from scraper import scrape_omnipong
from calc_ratings import run_calculation

def process_tournaments():
    print(f"[{datetime.datetime.now()}] Starting tournament check...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto('https://omnipong.com/T-tourney.asp?e=0', timeout=60000)
            
            # Use javascript to trigger the change just in case the locator is tricky
            # The select name might be "TimeFrame" or similar.
            page.wait_for_selector("select", timeout=10000)
            
            js_code = """
            () => {
                let f = document.querySelector('form');
                if (f) {
                    let s = f.querySelector('select[name="TimeFrame"]');
                    if (s) {
                        s.value = '2026';
                        f.submit();
                        return true;
                    }
                }
                return false;
            }
            """
            changed = page.evaluate(js_code)
            
            if changed:
                # Wait for reload
                page.wait_for_load_state("networkidle")
                time.sleep(3) # Give it a bit more time to render
            
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            tables = soup.find_all('table')
            ca_table = None
            
            for t in tables:
                prev = t.find_previous_sibling()
                while prev and prev.name != 'table':
                    if prev.name in ['h3', 'h4', 'h2', 'div'] and 'California' in prev.text:
                        ca_table = t
                        break
                    prev = prev.find_previous_sibling()
                if ca_table: break
                
            if not ca_table:
                print("Could not find California tournament section.")
                browser.close()
                return

            print("Found California tournaments table.")
            
            recent_tournaments = []
            
            rows = ca_table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3: continue
                
                title_text = cols[2].text.strip()
                safe_title = re.sub(r'[\\/*?:"<>|]', "", title_text).strip()
                
                has_results = False
                players_url = None
                results_page_url = None
                
                inputs = row.find_all('input')
                for inp in inputs:
                    val = inp.get('value', '')
                    onclick = inp.get('onclick', '')
                    if val == 'Results':
                        has_results = True
                        m2 = re.search(r"open_window\('([^']+)'", onclick)
                        if m2:
                            results_page_url = 'https://omnipong.com/' + m2.group(1).replace('&amp;', '&')
                    elif val == 'Players':
                        m = re.search(r"open_window\('([^']+)'", onclick)
                        if m:
                            players_url = 'https://omnipong.com/' + m.group(1).replace('&amp;', '&')
                            
                if not has_results:
                    # Reached the first tournament without results
                    break
                    
                if has_results and players_url and safe_title and results_page_url:
                    recent_tournaments.append({
                        'title': safe_title,
                        'url': players_url,
                        'results_page_url': results_page_url
                    })
                    
            print(f"Found {len(recent_tournaments)} completed California tournaments before the uncompleted boundary.")
            
            import requests
            target_tournaments = []
            
            # Only consider the top 3 most recent tournaments (the ones at the end of the 'has results' list)
            top_3_recent = list(reversed(recent_tournaments[-3:]))
            print(f"Analyzing the top 3 most recent tournaments: {[t['title'] for t in top_3_recent]}")

            for t in top_3_recent:
                title = t['title']
                
                # Check if already calculated
                if os.path.exists(title) and os.path.isdir(title):
                    print(f"Skipping '{title}' - already processed.")
                    continue
                    
                print(f"Validating cells for '{title}'...")
                res = requests.get(t['results_page_url'])
                if res.status_code != 200:
                    print(f"  Failed to fetch results page for {title}")
                    continue
                    
                t_soup = BeautifulSoup(res.content, 'html.parser')
                event_table = t_soup.find('table', class_='omnipong')
                
                if not event_table:
                    print(f"  No event table found for {title}")
                    continue
                    
                is_filled = True
                # Skip header row
                event_rows = event_table.find_all('tr')[1:]
                if not event_rows:
                    is_filled = False
                    
                for e_row in event_rows:
                    cells = e_row.find_all('td')
                    # 'First Place' is typically in the second column (index 1)
                    if len(cells) > 1:
                        if cells[1].text.strip() == '':
                            is_filled = False
                            break
                    if not is_filled:
                        break
                        
                if is_filled:
                    print(f"  Passed! '{title}' is fully complete.")
                    target_tournaments.append(t)
                else:
                    print(f"  Skipped! '{title}' contains empty cells.")
            
            for t in target_tournaments:
                title = t['title']
                url = t['url']
                
                print(f"Processing new tournament: '{title}'")
                os.makedirs(title, exist_ok=True)
                
                print(f"Scraping data for '{title}'...")
                try:
                    scrape_omnipong(url, title)
                    
                    print(f"Calculating ratings for '{title}'...")
                    run_calculation(title)
                    print(f"Successfully processed '{title}'.")
                except Exception as e:
                    print(f"Error processing '{title}': {e}")
            
            # Log the update if new tournaments were added
            if target_tournaments:
                log_file = 'updates_log.json'
                update_time = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
                log_data = []
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r') as f:
                            log_data = json.load(f)
                    except:
                        log_data = []
                
                log_data.append({
                    "timestamp": update_time,
                    "tournaments_added": [t['title'] for t in target_tournaments]
                })
                
                with open(log_file, 'w') as f:
                    json.dump(log_data, f, indent=4)
                print(f"Logged {len(target_tournaments)} new tournaments at {update_time}")
                    
        except Exception as e:
            print(f"An error occurred during navigation: {e}")
            
        browser.close()

    # Update data.js with all processed tournaments and their data
    print("Compiling universal database for offline web viewing...")
    import json
    import csv
    compiled_data = {}
    tournament_times = []
    
    for d in os.listdir('.'):
        csv_path = os.path.join(d, 'calculated_ratings.csv')
        matches_path = os.path.join(d, 'matches.csv')
        if os.path.isdir(d) and os.path.exists(csv_path):
            tournament_entry = {'players': [], 'matches': []}
            try:
                mtime = os.path.getmtime(csv_path)
                tournament_times.append((d, mtime))
                
                # Load players
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        tournament_entry['players'].append({
                            'Player Name': row['Player Name'],
                            'Initial Rating': row['Initial Rating'],
                            'Adjusted Rating': row['Adjusted Rating'],
                            'Final Rating': row['Final Rating'],
                            'Rating Change': row['Rating Change']
                        })
                
                # Load matches if they exist
                if os.path.exists(matches_path):
                    with open(matches_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            tournament_entry['matches'].append({
                                'Winner': row['Winner Name'],
                                'WinnerRating': row['Winner Rating'],
                                'Loser': row['Loser Name'],
                                'LoserRating': row['Loser Rating'],
                                'Event': row['Event']
                            })
                
                compiled_data[d] = tournament_entry
            except Exception as e:
                print(f"Error compiling data for {d}: {e}")
                
    # Sort tournaments by modification time descending (most recent first)
    tournament_times.sort(key=lambda x: x[1], reverse=True)
    sorted_tournament_names = [t[0] for t in tournament_times]
                
    current_time_str = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    # Get the last time new results were actually added
    last_addition_str = "Never"
    if os.path.exists('updates_log.json'):
        try:
            with open('updates_log.json', 'r') as f:
                logs = json.load(f)
                if logs:
                    last_addition_str = logs[-1]['timestamp']
        except:
            pass

    with open('data.js', 'w', encoding='utf-8') as f:
        f.write("window.USATT_LAST_CHECKED = " + json.dumps(current_time_str) + ";\n")
        f.write("window.USATT_LAST_UPDATED = " + json.dumps(last_addition_str) + ";\n")
        f.write("window.USATT_TOURNAMENTS = " + json.dumps(sorted_tournament_names) + ";\n")
        f.write("window.USATT_DATA = " + json.dumps(compiled_data, separators=(',', ':')) + ";\n")
    print(f"Database generated successfully with {len(compiled_data)} tournaments.")

def main():
    print("USATT Automator Started.")
    # Run once immediately
    process_tournaments()
    
    # Schedule to run every 6 hours
    schedule.every(6).hours.do(process_tournaments)
    
    print("Scheduler running. Waiting for next interval...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
