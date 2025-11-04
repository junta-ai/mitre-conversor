import os
from playwright.sync_api import sync_playwright
import time
import json

from settings import RAW_DATA_DIR


def scrape_mitre():
    tactics = [
        ("Reconnaissance", "TA0043"),
        ("Resource Development", "TA0042"),
        ("Initial Access", "TA0001"),
        ("Execution", "TA0002"),
        ("Persistence", "TA0003"),
        ("Privilege Escalation", "TA0004"),
        ("Defense Evasion", "TA0005"),
        ("Credential Access", "TA0006"),
        ("Discovery", "TA0007"),
        ("Lateral Movement", "TA0008"),
        ("Collection", "TA0009"),
        ("Command and Control", "TA0011"),
        ("Exfiltration", "TA0010"),
        ("Impact", "TA0040"),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        try:
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

            training_data = []

            print("Coletando dados por tática...")

            for tactic_name, tactic_id in tactics:
                try:
                    print(f"\nProcessando tática: {tactic_name}")

                    tactic_url = f"https://attack.mitre.org/tactics/{tactic_id}/"
                    page.goto(tactic_url, wait_until="networkidle")
                    page.wait_for_selector("body", timeout=20000)
                    time.sleep(3)

                    page_title = page.title()
                    if "404" in page_title or "Not Found" in page_title:
                        print(
                            f"  Página não encontrada para {tactic_name}, tentando URL alternativa..."
                        )
                        alt_url = f"https://attack.mitre.org/techniques/?f%5B0%5D=x_mitre_tactic~{tactic_id}"
                        page.goto(alt_url, wait_until="networkidle")
                        time.sleep(2)

                    technique_links = []

                    selectors = ["tbody tr td:nth-child(2) a[href*='/techniques/']"]

                    for selector in selectors:
                        links = page.query_selector_all(selector)
                        technique_links.extend(links)

                    unique_links = []
                    seen_urls = set()
                    for link in technique_links:
                        url = link.get_attribute("href")
                        if url and url not in seen_urls and "/techniques/T" in url:
                            unique_links.append(link)
                            seen_urls.add(url)

                    technique_links = unique_links
                    print(
                        f"  Encontradas {len(technique_links)} técnicas para {tactic_name}"
                    )

                    processed_in_tactic = set()

                    for link in technique_links:
                        try:
                            technique_url = link.get_attribute("href")
                            if not technique_url or "/techniques/" not in technique_url:
                                continue

                            technique_id = technique_url.split("/techniques/")[1].split(
                                "/"
                            )[0]

                            if technique_id in processed_in_tactic:
                                continue
                            processed_in_tactic.add(technique_id)

                            if not technique_url.startswith("http"):
                                technique_url = (
                                    "https://attack.mitre.org" + technique_url
                                )

                            print(f"  Coletando técnica: {technique_id}")

                            tech_page = context.new_page()
                            try:
                                tech_page.goto(
                                    technique_url,
                                    wait_until="networkidle",
                                    timeout=30000,
                                )
                                tech_page.wait_for_selector("body", timeout=20000)
                                time.sleep(1)
                            except Exception as nav_error:
                                print(
                                    f"    Erro ao navegar para {technique_id}: {nav_error}"
                                )
                                tech_page.close()
                                continue

                            technique_name = ""
                            name_elem = tech_page.query_selector("h1")
                            if name_elem:
                                full_name = name_elem.inner_text().strip()
                                if technique_id in full_name:
                                    technique_name = full_name.replace(
                                        technique_id, ""
                                    ).strip(" -:")
                                else:
                                    technique_name = full_name

                            description = ""

                            desc_selectors = [
                                ".description-body",
                                ".card-body",
                                ".technique-description",
                            ]

                            for selector in desc_selectors:
                                desc_container = tech_page.query_selector(selector)
                                if desc_container:
                                    paragraphs = desc_container.query_selector_all("p")
                                    if paragraphs:
                                        desc_texts = []
                                        for p in paragraphs[:3]:
                                            text = p.inner_text().strip()
                                            if (
                                                len(text) > 30
                                                and not text.startswith("ID:")
                                                and not text.startswith(
                                                    "Sub-techniques:"
                                                )
                                                and not text.startswith("Version")
                                                and not text.startswith("Created")
                                            ):
                                                desc_texts.append(text)

                                        if desc_texts:
                                            description = " ".join(desc_texts)
                                            break

                            if not description:
                                all_paragraphs = tech_page.query_selector_all("p")
                                for p in all_paragraphs[:10]:
                                    text = p.inner_text().strip()
                                    if (
                                        len(text) > 100
                                        and not text.startswith("ID:")
                                        and not text.startswith("Sub-techniques:")
                                        and not text.startswith("Version")
                                        and not text.startswith("Created")
                                        and not text.startswith("Tactics:")
                                    ):
                                        description = text
                                        break

                            if (
                                description
                                and len(description) > 100
                                and technique_name
                            ):
                                training_entry = {
                                    "input": description,
                                    "output": {
                                        "tactic": tactic_name,
                                        "technique_id": technique_id,
                                        "technique_name": technique_name,
                                    },
                                }
                                training_data.append(training_entry)
                                print(f"    ✓ Coletado: {technique_name}")
                            else:
                                print(f"    ✗ Dados insuficientes para {technique_id}")

                            tech_page.close()
                            time.sleep(0.5)

                        except Exception as e:
                            print(f"    Erro ao processar técnica: {e}")
                            if "tech_page" in locals():
                                tech_page.close()
                            continue

                    techniques_collected = len(
                        [
                            x
                            for x in training_data
                            if x["output"]["tactic"] == tactic_name
                        ]
                    )
                    print(
                        f"  ✓ Coletadas {techniques_collected} técnicas de {tactic_name} (de {len(technique_links)} encontradas)"
                    )

                except Exception as e:
                    print(f"Erro ao processar tática {tactic_name}: {e}")
                    continue

                time.sleep(1)

            result = {
                "training_data": training_data,
                "metadata": {
                    "total_entries": len(training_data),
                    "collection_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "tactics_processed": len(tactics),
                    "tactics_names": [t[0] for t in tactics],
                },
            }

            return result

        except Exception as e:
            print(f"Erro geral: {e}")
            return None

        finally:
            browser.close()


def save_and_display(data):
    if not data or not data["training_data"]:
        print("Nenhum dado coletado")
        return

    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)

    with open(RAW_DATA_DIR + "/mitre_training_final.json", "w", encoding="utf-8") as f:
        json.dump(data["training_data"], f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    result = scrape_mitre()
    save_and_display(result)
