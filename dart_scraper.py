import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import csv, re

LEAGUE_URL = "https://tv.dartconnect.com/league/CarDL/matches/17812"
OUTPUT_CSV = "dart_highlights_combined.csv"



# -----------------------------------------------------
# PART 1 – FETCH GAME LINKS FROM LEAGUE PAGE
# -----------------------------------------------------
async def get_latest_week_links(page):
    print(f"Loading {LEAGUE_URL} ...")
    await page.goto(LEAGUE_URL, wait_until="networkidle")
    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")

    week_headers = soup.find_all("div", class_="bg-[#8aa2be]")
    if not week_headers:
        print("⚠️ No week headers found.")
        return []

    latest_header = week_headers[0]
    latest_week_text = latest_header.get_text(strip=True)
    print(f"✅ Latest week detected: {latest_week_text}")

    matches_div = latest_header.find_next_sibling("div")
    if not matches_div:
        print("⚠️ No sibling <div> found after week header.")
        return []

    links = []
    for a in matches_div.find_all("a", href=True):
        href = a["href"]
        if "https://recap.dartconnect.com/league-matches/" in href:
            links.append(href)

    print(f"✅ Found {len(links)} match links.")
    return links


async def follow_links_and_get_game_urls(links, page):
    game_urls = []
    for i, link in enumerate(links, start=1):
        print(f"→ Visiting link {i}/{len(links)}: {link}")
        await page.goto(link, wait_until="networkidle")
        final_url = page.url
        if "/matches/" in final_url:
            game_url = final_url.replace("/matches/", "/games/")
            print(f"   ✅ Converted to: {game_url}")
            game_urls.append(game_url)
        else:
            print(f"   ⚠️ Unexpected URL format: {final_url}")
    return game_urls


# -----------------------------------------------------
# PART 2 – FETCH AND PARSE EACH GAME PAGE
# -----------------------------------------------------
async def fetch_html_playwright(page, url):
    await page.goto(url, wait_until="networkidle")
    return await page.content()


def extract_teams(soup):
    spans = soup.find_all("span", class_="text-xl font-bold")
    if len(spans) >= 2:
        left_team = spans[0].get_text(strip=True)
        right_team = spans[1].get_text(strip=True)
        return [left_team, right_team]

    header = soup.find(["h2", "h3", "div"], string=re.compile(r"\d+\s*[-–]\s*\d+"))
    if header:
        text = header.get_text(" ", strip=True)
        m = re.match(r"^(.*?)\s*\d+\s*[-–]\s*\d+\s*(.*?)$", text)
        if m:
            return [m.group(1).strip(), m.group(2).strip()]

    return ["Home Team", "Away Team"]


def parse_game_data(html):
    soup = BeautifulSoup(html, "html.parser")
    teams = extract_teams(soup)

    rows = soup.find_all("tr")
    high_scores = []
    high_checkouts = []
    short_games = []

    current_format = None
    doubles_players = []

    for row in rows:
        cells = [td.get_text(" ", strip=True) for td in row.find_all("td")]
        if not cells:
            continue

        if len(cells) == 1 and "set" in cells[0].lower():
            text = cells[0].lower()
            if "doubles" in text:
                current_format = "doubles"
            elif "singles" in text:
                current_format = "singles"
            else:
                current_format = None
            doubles_players = []
            continue

        if len(cells) < 8:
            continue

        try:
            left_name = cells[1]
            left_score = int(cells[2]) if cells[2].isdigit() else None
            left_remaining = int(cells[3]) if cells[3].isdigit() else None
            round_no = int(cells[4]) if cells[4].isdigit() else None
            right_remaining = int(cells[5]) if cells[5].isdigit() else None
            right_score = int(cells[6]) if cells[6].isdigit() else None
            right_name = cells[7]
            checkout_info = cells[8] if len(cells) > 8 else ""

            if current_format == "doubles":
                if left_name and left_name not in doubles_players:
                    doubles_players.append(left_name)
                if right_name and right_name not in doubles_players:
                    doubles_players.append(right_name)
                doubles_players = doubles_players[:4]

            if left_score and left_score >= 170:
                high_scores.append((teams[0], left_name, left_score))
            if right_score and right_score >= 170:
                high_scores.append((teams[1], right_name, right_score))

            if left_remaining == 0 and left_score and left_score >= 101:
                high_checkouts.append((teams[0], left_name, left_score))
            if right_remaining == 0 and right_score and right_score >= 101:
                high_checkouts.append((teams[1], right_name, right_score))

            if left_remaining == 0 or right_remaining == 0:
                if left_remaining == 0:
                    winner = left_name
                    team = teams[0]
                else:
                    winner = right_name
                    team = teams[1]

                darts_used = 3
                m = re.search(r"\((\d)\)", checkout_info)
                if m:
                    darts_used = int(m.group(1))
                total_darts = (round_no - 1) * 3 + darts_used if round_no else None

                if current_format == "singles" and total_darts and total_darts <= 18:
                    short_games.append((team, "singles", winner, total_darts))
                elif current_format == "doubles" and total_darts and total_darts <= 31:
                    partners = ", ".join(doubles_players[:2]) if doubles_players else winner
                    short_games.append((team, "doubles", partners, total_darts))
        except Exception:
            continue

    return teams, high_scores, high_checkouts, short_games


# -----------------------------------------------------
# PART 3 – SAVE TO CSV
# -----------------------------------------------------
def append_to_csv(all_rows):
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Type", "Team", "Players/Format", "Score/Checkout", "Darts"])
        writer.writerows(all_rows)
    print(f"\n✅ Combined CSV saved: {OUTPUT_CSV}")


# -----------------------------------------------------
# PART 4 – MAIN ENTRY
# -----------------------------------------------------
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()

        # Step 1 – Get /games/ links
        links = await get_latest_week_links(page)
        if not links:
            await browser.close()
            return
        game_urls = await follow_links_and_get_game_urls(links, page)

        all_high_scores = []
        all_high_checkouts = []
        all_short_games = []
        all_rows = []

        # Step 2 – Process each game page
        for i, url in enumerate(game_urls, start=1):
            print(f"\n==============================")
            print(f" Processing {i}/{len(game_urls)}: {url}")
            html = await fetch_html_playwright(page, url)
            teams, high_scores, high_checkouts, short_games = parse_game_data(html)

            # Accumulate results
            all_high_scores.extend(high_scores)
            all_high_checkouts.extend(high_checkouts)
            all_short_games.extend(short_games)

            for team, name, score in high_scores:
                all_rows.append(["High Score", team, name, score, ""])
            for team, name, score in high_checkouts:
                all_rows.append(["High Checkout", team, name, score, ""])
            for team, fmt, players, darts in short_games:
                all_rows.append(["Short Game", team, fmt.title(), players, darts])

        await browser.close()
        append_to_csv(all_rows)

    # Step 3 – Print consolidated results
    print("\n\n==============================")
    print("🏆 CONSOLIDATED MATCH SUMMARY")
    print("==============================")

    print("\n🎯 HIGH SCORES (≥170)")
    if all_high_scores:
        for t, p, s in all_high_scores:
            print(f"{t:15} | {p:25} | {s}")
    else:
        print("None found.")

    print("\n💥 HIGH CHECKOUTS (≥101)")
    if all_high_checkouts:
        for t, p, s in all_high_checkouts:
            print(f"{t:15} | {p:25} | {s}")
    else:
        print("None found.")

    print("\n⚡ SHORT GAMES")
    if all_short_games:
        for t, fmt, players, darts in all_short_games:
            print(f"{t:15} | {fmt.title():8} | {players:30} | {darts} darts")
    else:
        print("None found.")


async def run_scraper():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()

        links = await get_latest_week_links(page)
        if not links:
            await browser.close()
            return [["No links found"]]

        game_urls = await follow_links_and_get_game_urls(links, page)
        all_rows = []

        for url in game_urls:
            html = await fetch_html_playwright(page, url)
            teams, high_scores, high_checkouts, short_games = parse_game_data(html)

            for team, name, score in high_scores:
                all_rows.append(["High Score", team, name, score, ""])
            for team, name, score in high_checkouts:
                all_rows.append(["High Checkout", team, name, score, ""])
            for team, fmt, players, darts in short_games:
                all_rows.append(["Short Game", team, fmt.title(), players, darts])

        await browser.close()
        append_to_csv(all_rows)
        results = all_rows
    return results

if __name__ == "__main__":
    asyncio.run(main())

