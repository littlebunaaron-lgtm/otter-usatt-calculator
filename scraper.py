import sys
import csv
import re
import urllib.parse
import os

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Please install requests and beautifulsoup4: pip install requests beautifulsoup4")
    sys.exit(1)

def scrape_omnipong(url, output_dir="."):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }
    
    session = requests.Session()
    session.headers.update(headers)

    print(f"Fetching tournament page: {url}")
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the table containing the players
    tables = soup.find_all('table', class_='omnipong')
    target_table = None
    for table in tables:
        headers_row = table.find('tr')
        if headers_row:
            first_th = headers_row.find('th')
            if first_th and "Players" in first_th.text:
                target_table = table
                break
    
    if not target_table:
        print("Could not find the players table on the page.")
        return

    players = []
    
    # Iterate over all rows, skipping the header
    rows = target_table.find_all('tr')[1:]
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 4:
            first_col = cols[0]
            a_tag = first_col.find('a')
            if a_tag:
                raw_name = a_tag.text.strip()
                # Remove leading '-' if present
                name = re.sub(r'^-\s*', '', raw_name)
                
                href = a_tag.get('href')
                link = urllib.parse.urljoin('https://omnipong.com/', href)
            else:
                continue # Skip if no link, as we can't fetch their matches
                
            # Fourth column: Ratings Seed/Elig
            rating_col = cols[3]
            rating_text = rating_col.text.strip()
            # The rating is before the '/'
            seed_rating = rating_text.split('/')[0].strip()
            
            players.append((name, seed_rating, link))

    if not players:
        print("No player links found.")
        return

    output_csv = os.path.join(output_dir, "output.csv")
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Player Name', 'Rating', 'Profile Link'])
        for p in players:
            writer.writerow(p)

    print(f"Found {len(players)} players to process. Saved to {output_csv}. Fetching match results...")

    matches = set()
    player_ratings = {}
    
    for i, (p_name, p_rating, p_link) in enumerate(players):
        # Print progress
        if (i + 1) % 10 == 0 or (i + 1) == len(players):
            print(f"Processed {i + 1}/{len(players)} players...")
            
        p_resp = session.get(p_link)
        if p_resp.status_code != 200:
            continue
            
        p_soup = BeautifulSoup(p_resp.text, 'html.parser')
        
        page_name = p_name
        name_h4 = p_soup.find('h4')
        if name_h4 and name_h4.contents:
            page_name_text = str(name_h4.contents[0]).strip()
            if page_name_text:
                page_name = page_name_text
                
        # Store the true seeding rating for this player
        player_ratings[page_name] = p_rating
        
        for table in p_soup.find_all('table', class_='omnipong'):
            th = table.find('th')
            if th and "Opponent" in th.text:
                # Check text before table to see if these are Wins or Losses
                prev = table.previous_sibling
                is_win = False
                is_loss = False
                while prev:
                    text = prev.text if hasattr(prev, 'text') else str(prev)
                    if "Wins" in text:
                        is_win = True
                        break
                    if "Losses" in text:
                        is_loss = True
                        break
                    prev = prev.previous_sibling
                    
                match_rows = table.find_all('tr')[1:]
                for m_row in match_rows:
                    m_cols = m_row.find_all('td')
                    if len(m_cols) >= 5:
                        opp_raw = m_cols[0].text.strip()
                        opp_name = re.sub(r'^-\s*', '', opp_raw)
                        opp_rating = m_cols[2].text.strip().split('/')[0].strip()
                        event_name = m_cols[4].text.strip()
                        
                        # Store fallback rating if opponent hasn't been processed
                        if opp_name not in player_ratings:
                            player_ratings[opp_name] = opp_rating
                        
                        if is_win:
                            matches.add((page_name, opp_name, event_name))
                        elif is_loss:
                            matches.add((opp_name, page_name, event_name))

    print(f"Finished fetching matches. Total unique matches: {len(matches)}")

    # Write matches to CSV
    matches_csv = os.path.join(output_dir, "matches.csv")
    with open(matches_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Winner Name', 'Winner Rating', 'Loser Name', 'Loser Rating', 'Event'])
        for winner, loser, event in sorted(matches):
            w_rating = player_ratings.get(winner, "")
            l_rating = player_ratings.get(loser, "")
            writer.writerow([winner, w_rating, loser, l_rating, event])
            
    print(f"Successfully saved match results to {matches_csv}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <url> [output_dir]")
        sys.exit(1)
        
    url = sys.argv[1]
    output_dir = "."
    if len(sys.argv) >= 3:
        output_dir = sys.argv[2]
        
    scrape_omnipong(url, output_dir)
