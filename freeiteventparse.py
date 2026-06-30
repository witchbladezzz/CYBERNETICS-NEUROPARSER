import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import json
import re
import time

BASE = "https://freeitevent.ru"


# ----------------------------
# парсинг даты
# ----------------------------
def parse_date(text: str):
    if not text:
        return None

    months = {
        "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
        "мая": 5, "июня": 6, "июля": 7, "августа": 8,
        "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
    }

    text = text.lower()

    m = re.search(r"(\d{1,2})\s+([а-яА-Я]+)\s+(\d{4})", text)
    if m:
        day = int(m.group(1))
        month = months.get(m.group(2), 1)
        year = int(m.group(3))
        return datetime(year, month, day)

    return None


# ----------------------------
# главная страница -> ссылки
# ----------------------------
def get_links(html):
    soup = BeautifulSoup(html, "lxml")

    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/itevents/" in href and href.count("/") > 2:
            links.add(urljoin(BASE, href))

    return list(links)


# ----------------------------
# парсинг события
# ----------------------------
def parse_event(url):
    r = requests.get(url, timeout=30)
    soup = BeautifulSoup(r.text, "lxml")

    title = soup.find("h1")
    title = title.get_text(strip=True) if title else None

    text = soup.get_text(" ", strip=True)

    # дата
    date = None
    for t in soup.find_all(string=True):
        if t and any(x in t.lower() for x in ["г.", "января", "февраля", "марта"]):
            d = parse_date(t)
            if d:
                date = d
                break

    # формат (онлайн / офлайн)
    format_event = None
    badge = soup.find("span")
    if badge:
        format_event = badge.get_text(" ", strip=True)

    # теги
    tags = []
    for a in soup.find_all("a", href=True):
        if "/events/tags/" in a["href"]:
            tags.append(a.get_text(strip=True))

    tags = list(set(tags))

    # регистрация
    register_links = []
    for a in soup.find_all("a", href=True):
        t = a.get_text(" ", strip=True).lower()
        if any(x in t for x in ["регистрация", "зарегистр", "участвовать"]):
            register_links.append(urljoin(BASE, a["href"]))

    # внешние ссылки
    external_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http") and "freeitevent.ru" not in href:
            external_links.append(href)

    # --- НОВАЯ ЛОГИКА ДЛЯ АУДИТОРИИ И ПРИЗА ---
    audience = None
    prize = "Не предусмотрен"

    # Поиск аудитории
    # Ищем блок, содержащий "Для кого:"
    for strong_tag in soup.find_all("strong"):
        if strong_tag.get_text(strip=True).lower().startswith("для кого"):
            parent = strong_tag.find_parent()
            if parent:
                # Берем следующий за strong текст или весь текст родителя
                audience_text = parent.get_text(" ", strip=True)
                # Убираем "Для кого:" из начала строки
                audience = audience_text.replace("Для кого:", "", 1).strip()
            break
    # Если не нашли через strong, ищем по тексту
    if not audience:
        for elem in soup.find_all(string=True):
            if elem.strip().lower().startswith("для кого"):
                audience = elem.strip().replace("Для кого:", "", 1).strip()
                break

    # Поиск приза
    # Собираем весь текст страницы и ищем ключевые слова
    page_text = soup.get_text(" ", strip=True)
    prize_keywords = [
        "призовой фонд", "приз", "prize", "денежный приз",
        "руб.", "₽", "$", "€", "бонус", "вознаграждение"
    ]
    found_prizes = []
    for keyword in prize_keywords:
        if keyword.lower() in page_text.lower():
            # Пытаемся вырезать контекст
            for sentence in re.split(r'[.!?]', page_text):
                if keyword.lower() in sentence.lower():
                    # Очищаем предложение
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 10:  # Игнорируем короткие совпадения
                        found_prizes.append(clean_sentence)
                    break

    if found_prizes:
        # Берем первое подходящее предложение, но стараемся найти наиболее релевантное
        # Если есть упоминание "призовой фонд", берем его в первую очередь
        for p in found_prizes:
            if "призовой фонд" in p.lower() or "prize" in p.lower():
                prize = p
                break
        else:
            prize = found_prizes[0]

    # Фильтруем, чтобы не было слишком длинных строк
    if len(prize) > 20:
        prize = prize[:20] + "..."

    return {
        "url": url,
        "title": title,
        "date": date.strftime("%d.%m.%Y") if date else None,
        "format": format_event,
        "tags": tags,
        "register_links": list(set(register_links)),
        "external_links": list(set(external_links)),
        "audience": audience,
        "prize": prize,
        # "full_text": text[:5000]
    }


# ----------------------------
# основной парсер
# ----------------------------
def scrape():
    r = requests.get(BASE, timeout=30)
    links = get_links(r.text)

    results = []

    for i, link in enumerate(links):
        try:
            print(f"[{i+1}/{len(links)}] {link}")
            data = parse_event(link)
            results.append(data)
            time.sleep(0.3)

        except Exception as e:
            print("error:", link, e)

    return results


# ----------------------------
# save
# ----------------------------
def save(data):
    with open("freeitevent.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    data = scrape()
    save(data)
    print("DONE:", len(data))