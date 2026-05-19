from playwright.sync_api import sync_playwright

def test_extraction():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://omnipong.com/t-tourney.asp?e=0')
        
        # Select "2026"
        page.select_option('select[name="TimeFrame"]', '2026')
        
        # Wait for the page to load or refresh
        page.wait_for_timeout(2000)
        
        # Get the page content and parse with BS4
        html = page.content()
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        ca_table = None
        for t in tables:
            prev = t.find_previous_sibling()
            while prev and prev.name != 'table':
                if prev.name in ['h3', 'h4', 'h2', 'div'] and prev.text.strip() == 'California':
                    ca_table = t
                    break
                prev = prev.find_previous_sibling()
            if ca_table: break
            
        if ca_table:
            print("Found California Table")
            rows = ca_table.find_all('tr')
            for row in rows:
                links = row.find_all('a')
                for l in links:
                    href = l.get('href', '')
                    if 'r=' in href:
                        print(f"Tournament: {l.text.strip()} | Link: {href}")
        else:
            print("Did not find CA table")
            
        browser.close()

if __name__ == '__main__':
    test_extraction()
