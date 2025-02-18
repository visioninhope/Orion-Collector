from abc import ABC
from datetime import datetime
from typing import List
from bs4 import BeautifulSoup
from playwright.sync_api import Page
from urllib.parse import urljoin
from crawler.crawler_instance.local_interface_model.leak_extractor_interface import leak_extractor_interface
from crawler.crawler_instance.local_shared_model.card_extraction_model import card_extraction_model
from crawler.crawler_instance.local_shared_model.rule_model import RuleModel, FetchProxy, FetchConfig
from crawler.crawler_services.redis_manager.redis_controller import redis_controller
from crawler.crawler_services.redis_manager.redis_enums import REDIS_COMMANDS, CUSTOM_SCRIPT_REDIS_KEYS
from crawler.crawler_services.shared.helper_method import helper_method


class _b1nd(leak_extractor_interface, ABC):
    _instance = None

    def __init__(self):
        self._card_data = []
        self._redis_instance = redis_controller()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(_b1nd, cls).__new__(cls)
        return cls._instance

    @property
    def seed_url(self) -> str:
        return "http://b1nd.net"

    @property
    def base_url(self) -> str:
        return "http://b1nd.net"

    @property
    def rule_config(self) -> RuleModel:
        return RuleModel(m_fetch_proxy=FetchProxy.NONE, m_fetch_config=FetchConfig.SELENIUM)

    @property
    def card_data(self) -> List[card_extraction_model]:
        return self._card_data

    def invoke_db(self, command: REDIS_COMMANDS, key: CUSTOM_SCRIPT_REDIS_KEYS, default_value) -> None:
        return self._redis_instance.invoke_trigger(command, [key.value + self.__class__.__name__, default_value])

    def contact_page(self) -> str:
        return self.seed_url

    def safe_find(self, page, selector, attr=None):
        """Safely find an element and return its text or attribute"""
        try:
            element = page.locator(selector).first
            if element.count() > 0:
                return element.get_attribute(attr) if attr else element.inner_text().strip()
        except Exception:
            return None

    def parse_leak_data(self, page: Page):
        try:
            print("Starting leak data extraction...")

            outer_list = []  # List to store outer links
            page.goto(self.seed_url)
            page.wait_for_load_state("load")
            print("Fetched seed URL:", self.seed_url)

            outer_elements = page.query_selector_all("h3.node-title a")
            for element in outer_elements:
                href = element.get_attribute("href")
                if href:
                    outer_list.append(urljoin(self.base_url, href))

            print("Total outer links found:", len(outer_list))

            for outer_link in outer_list:
                print("\nProcessing outer link:", outer_link)
                page.goto(outer_link)
                page.wait_for_load_state("load")

                while True:  # Loop for pagination in inner links
                    inner_list = []  # Reset inner list on each pagination cycle
                    inner_elements = page.query_selector_all("div.structItem-title a")

                    for element in inner_elements:
                        href = element.get_attribute("href")
                        if href:
                            inner_list.append(urljoin(self.base_url, href))

                    print(f"Found {len(inner_list)} inner links on page: {page.url}")

                    for inner_link in inner_list:
                        try:
                            print("Processing inner link:", inner_link)
                            page.goto(inner_link)
                            page.wait_for_load_state("load")

                            m_leak_date = self.safe_find(page, "time.u-dt")
                            m_content = self.safe_find(page, "div.bbWrapper")
                            title = self.safe_find(page, "h1.p-title-value")

                            # Check if content exists and process word count
                            if m_content:
                                words = m_content.split()
                                if len(words) > 500:
                                    m_important_content = " ".join(words[:500])
                                else:
                                    m_important_content = m_content
                            else:
                                m_important_content = ""

                            card_data = card_extraction_model(
                                m_title=title,
                                m_weblink=[inner_link],
                                m_url=inner_link,
                                m_addresses=[],
                                m_base_url=self.base_url,
                                m_content=m_content if m_content else "",
                                m_websites=[],
                                m_network=helper_method.get_network_type(self.base_url),
                                m_important_content=m_important_content,
                                m_content_type="leaks",
                                m_leak_date=m_leak_date if m_leak_date else ""
                            )
                            self._card_data.append(card_data)

                        except Exception as e:
                            print(f"Error processing inner link {inner_link}: {e}")
                            continue

                    # Check for pagination within inner pages
                    next_button = page.query_selector(".block-router-main .pageNav-jump--next")
                    if next_button:
                        next_url = next_button.get_attribute("href")
                        if next_url:
                            print("Moving to next inner pagination page:", next_url)
                            page.goto(urljoin(self.base_url, next_url))
                            page.wait_for_load_state("load")
                            continue  # Re-run the loop for the new page
                        else:
                            print("No next button URL found. Ending inner pagination.")
                            break
                    else:
                        print("No next button found. Moving to next outer link.")
                        break

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print("Data extraction completed. Invoking DB update.")
            self.invoke_db(REDIS_COMMANDS.S_SET_BOOL, CUSTOM_SCRIPT_REDIS_KEYS.URL_PARSED, True)
