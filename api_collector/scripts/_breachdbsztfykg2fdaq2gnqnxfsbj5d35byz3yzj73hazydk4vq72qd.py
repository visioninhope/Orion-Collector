import re
from abc import ABC
from typing import Dict
from playwright.async_api import BrowserContext
from crawler.crawler_instance.local_interface_model.api.api_collector_interface import api_collector_interface
from crawler.crawler_instance.local_shared_model.data_model.leak_model import leak_model
from crawler.crawler_instance.local_interface_model.api.api_data_model import api_data_model
from crawler.crawler_instance.local_shared_model.rule_model import RuleModel, FetchProxy, FetchConfig, ThreatType
from crawler.crawler_services.shared.helper_method import helper_method


class _breachdbsztfykg2fdaq2gnqnxfsbj5d35byz3yzj73hazydk4vq72qd(api_collector_interface, ABC):
  _instance = None

  def __init__(self):
    self._initialized = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super(_breachdbsztfykg2fdaq2gnqnxfsbj5d35byz3yzj73hazydk4vq72qd, cls).__new__(cls)
      cls._instance._initialized = False
    return cls._instance

  @property
  def base_url(self) -> str:
    return "http://breachdbsztfykg2fdaq2gnqnxfsbj5d35byz3yzj73hazydk4vq72qd.onion"

  @property
  def rule_config(self) -> RuleModel:
    return RuleModel(m_fetch_proxy=FetchProxy.TOR, m_fetch_config=FetchConfig.SELENIUM, threat_type=ThreatType.API)

  @staticmethod
  def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

  async def parse_leak_data(self, query: Dict[str, str], context: BrowserContext) -> api_data_model:
    p_data_url = self.base_url
    email = query.get("email", "")
    username = query.get("username", "")

    collector_model = api_data_model(base_url=p_data_url, content_type=["email", "username"])
    combined_records = set()
    email_list = set()
    username_list = set()

    try:
      page = await context.new_page()
      await page.goto(p_data_url)
      page_content = await page.content()
      if "This site can’t be reached" in page_content or "ERR_" in page_content:
        return collector_model

      try:
        await page.locator("#SearchType").wait_for(timeout=120000)

        for search_type, query_value in [("Username", username), ("Email", email)]:
          if not query_value:
            continue

          try:
            await page.locator("#SearchType").select_option(value=search_type)
            search_box = page.locator("#TxtSearch")
            await search_box.fill(query_value)
            search_button = page.locator("#BtnSearch")
            await search_button.click()

            result_panel_locator = page.locator(".ResultPanel")
            await result_panel_locator.wait_for(timeout=120000)

            spans = await result_panel_locator.locator("span").all()
            public_records = [
              (await span.text_content()).split("-->", 1)[0].strip()
              for span in spans if "-->" in (await span.text_content())
            ]
            combined_records.update(public_records)

            if search_type == "Email":
              email_list.add(query_value)
            else:
              username_list.add(query_value)
          except Exception as _:
            continue

        if combined_records:
          collector_model.cards_data = [leak_model(
            m_title=f"Records for provided queries",
            m_important_content=f"Records were found in a data breach.",
            m_weblink=[],
            m_content="",
            m_base_url=self.base_url,
            m_network=helper_method.get_network_type(self.base_url),
            m_url=p_data_url,
            m_content_type=["stolen"],
            m_dumplink=list(combined_records),
            m_email_addresses=list(email_list),
            m_name=", ".join(username_list)
          )]
      except Exception as _:
        return collector_model
    finally:
      pass

    return collector_model