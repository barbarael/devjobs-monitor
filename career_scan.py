#!/usr/bin/env python3
"""
DevJobs Monitor - KARIÉRNÍ WEBY FIREM (nejspolehlivější)
=========================================================
Spusť: python career_scan.py

Prohledává přímo kariérní stránky developerských firem.
Nejspolehlivější způsob - žádné blokování.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

# ─── KONFIGURACE ──────────────────────────────────────────────────────────────

KEYWORDS = [
    "senior market", "head of market", "marketing manager", 
    "marketing director", "cmo", "chief marketing", 
    "vedoucí marketingu", "ředitel marketingu", "manažer marketingu",
    "brand manager", "communication manager"
]

# Kariérní stránky firem - ověřené URL
CAREER_SITES = {
    "CTP": [
        "https://www.ctp.eu/careers",
        "https://jobs.cz/rpd/ctp-czech-republic-s-r-o-1136154/",
    ],
    "Panattoni": [
        "https://www.panattoni.com/about/careers/",
        "https://jobs.cz/rpd/panattoni-czech-republic-s-r-o-1193669/",
    ],
    "Penta Real Estate": [
        "https://www.pentarealestate.com/cs/kariera",
        "https://jobs.cz/rpd/penta-real-estate-s-r-o-1100001/",
    ],
    "Crestyl": [
        "https://www.crestyl.com/cs/kariera",
        "https://jobs.cz/rpd/crestyl-a-s-1181/",
    ],
    "P3 Logistic Parks": [
        "https://www.p3parks.com/careers/",
        "https://jobs.cz/rpd/p3-logistic-parks-s-r-o-1103380/",
    ],
    "Daramis": [
        "https://www.daramis.cz/kariera/",
        "https://jobs.cz/rpd/daramis-a-s-1150965/",
    ],
    "Trigema": [
        "https://www.trigema.cz/cs/kariera",
        "https://jobs.cz/rpd/trigema-a-s-1101/",
    ],
    "Central Group": [
        "https://www.central-group.cz/kariera/",
        "https://jobs.cz/rpd/central-group-czech-republic-s-r-o-1102245/",
    ],
    "Skanska": [
        "https://www.skanska.cz/kariera/",
        "https://jobs.cz/rpd/skanska-a-s-1156/",
    ],
    "AFI Europe": [
        "https://www.afieurope.cz/kariera/",
        "https://jobs.cz/rpd/afi-europe-czech-republic-s-r-o-1101080/",
    ],
    "Metrostav Development": [
        "https://www.metrostav-development.cz/kariera",
        "https://jobs.cz/rpd/metrostav-development-a-s-1192746/",
    ],
}

# ─── HELPER FUNKCE ────────────────────────────────────────────────────────────

def clean_text(text):
    """Vyčistí text."""
    return " ".join(text.split())

def matches_keywords(text):
    """Vrátí True, pokud text obsahuje relevantní klíčové slovo."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in KEYWORDS)

def print_job(job, company):
    """Hezky vypíše inzerát."""
    print("\n" + "="*80)
    print(f"📋 {job['title']}")
    print(f"🏢 {company}")
    print(f"🔗 {job['url']}")
    if job.get('snippet'):
        snippet = job['snippet'][:200] + "..." if len(job['snippet']) > 200 else job['snippet']
        print(f"📝 {snippet}")
    print("="*80)

def scan_website(url, company):
    """Skenuje jednotlivý web."""
    jobs = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'cs,en;q=0.9',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hledáme různé možné struktury
        # 1. Klasické job boardy
        job_elements = (
            soup.find_all('div', class_=re.compile(r'job|position|career|offer', re.I)) +
            soup.find_all('article', class_=re.compile(r'job|position|career', re.I)) +
            soup.find_all('li', class_=re.compile(r'job|position|career', re.I))
        )
        
        # 2. Linky s klíčovými slovy
        all_links = soup.find_all('a', href=True)
        
        found_any = False
        
        for link in all_links:
            try:
                text = clean_text(link.get_text())
                href = link['href']
                
                # Přeskoč prázdné nebo nerelevantní linky
                if not text or len(text) < 10:
                    continue
                
                if 'cookie' in href.lower() or 'privacy' in href.lower():
                    continue
                
                # Kontrola, jestli obsahuje klíčová slova
                if matches_keywords(text):
                    # Udělej absolutní URL
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        from urllib.parse import urlparse, urljoin
                        parsed = urlparse(url)
                        full_url = f"{parsed.scheme}://{parsed.netloc}{href}"
                    else:
                        from urllib.parse import urljoin
                        full_url = urljoin(url, href)
                    
                    job = {
                        'title': text,
                        'url': full_url,
                        'snippet': ''
                    }
                    
                    jobs.append(job)
                    found_any = True
            
            except Exception as e:
                continue
        
        # 3. Hledáme i v textu celé stránky
        if not found_any:
            page_text = soup.get_text()
            if matches_keywords(page_text):
                # Najdi všechny nadpisy, které mohou být pozice
                for tag in ['h1', 'h2', 'h3', 'h4']:
                    headings = soup.find_all(tag)
                    for h in headings:
                        text = clean_text(h.get_text())
                        if matches_keywords(text) and len(text) > 10:
                            jobs.append({
                                'title': text,
                                'url': url,
                                'snippet': f'Nalezeno na hlavní kariérní stránce'
                            })
                            break
        
    except requests.exceptions.Timeout:
        print(f"      ⏱️ Timeout: {url}")
    except requests.exceptions.RequestException as e:
        print(f"      ⚠️ Nedostupné: {url}")
    except Exception as e:
        print(f"      ⚠️ Chyba při zpracování: {url}")
    
    return jobs

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("="*80)
    print("🏗  DevJobs Monitor - KARIÉRNÍ WEBY FIREM")
    print("="*80)
    print(f"⏰ Čas: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"🎯 Hledám: senior marketing pozice")
    print(f"🏢 Firmy: {len(CAREER_SITES)} developerských společností")
    print("="*80)
    
    all_jobs = []
    
    for company, urls in CAREER_SITES.items():
        print(f"\n🔍 Skenuji {company}...")
        company_jobs = []
        
        for url in urls:
            print(f"   → {url}")
            jobs = scan_website(url, company)
            company_jobs.extend(jobs)
            time.sleep(1.5)  # Buď slušný
        
        # Deduplikace podle URL
        seen = set()
        unique_jobs = []
        for job in company_jobs:
            if job['url'] not in seen:
                seen.add(job['url'])
                unique_jobs.append(job)
        
        if unique_jobs:
            print(f"   ✅ Nalezeno {len(unique_jobs)} relevantních pozic")
            for job in unique_jobs:
                all_jobs.append({**job, 'company': company})
        else:
            print(f"   ℹ️  Žádné relevantní pozice")
    
    # Zobraz výsledky
    print("\n" + "="*80)
    print(f"🎯 CELKEM NALEZENO: {len(all_jobs)} RELEVANTNÍCH POZIC")
    print("="*80)
    
    if all_jobs:
        for i, job in enumerate(all_jobs, 1):
            print_job(job, f"{job['company']} (#{i})")
        
        # Ulož do souboru
        try:
            with open('found_jobs.txt', 'w', encoding='utf-8') as f:
                f.write(f"DevJobs Monitor - Výsledky skenování\n")
                f.write(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write(f"="*80 + "\n\n")
                
                for i, job in enumerate(all_jobs, 1):
                    f.write(f"{i}. {job['title']}\n")
                    f.write(f"   Firma: {job['company']}\n")
                    f.write(f"   URL: {job['url']}\n")
                    if job['snippet']:
                        f.write(f"   Poznámka: {job['snippet']}\n")
                    f.write("\n")
            
            print(f"\n💾 Výsledky uloženy do souboru: found_jobs.txt")
            print(f"   (Můžeš ho otevřít v Poznámkovém bloku)")
        except Exception as e:
            print(f"\n⚠️ Nepodařilo se uložit výsledky: {e}")
    
    else:
        print("\nℹ️  Momentálně žádné relevantní pozice.")
        print("💡 To je normální - senior marketing pozice se neobjevují každý den.")
        print("💡 Zkus to spustit znovu za týden.")
    
    print("\n" + "="*80)
    print("✅ Skenování dokončeno")
    print(f"📊 Prohledáno {len(CAREER_SITES)} firem ({sum(len(urls) for urls in CAREER_SITES.values())} URL)")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Skenování přerušeno")
    except Exception as e:
        print(f"\n\n❌ Neočekávaná chyba: {e}")
        import traceback
        traceback.print_exc()
