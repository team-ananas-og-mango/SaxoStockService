import json
import os
import webbrowser
from secrets import token_urlsafe
from time import sleep
from typing import Dict, Optional, Union
from urllib.parse import parse_qs

from loguru import logger
from pydantic import AnyHttpUrl, ValidationError, parse_obj_as
from saxo_apy import SaxoOpenAPIClient
from saxo_apy.models import APIEnvironment, AuthorizationCode
from saxo_apy.redirect_server import RedirectServer
from saxo_apy.utils import construct_auth_url, validate_redirect_url
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

path = os.path.dirname(os.path.abspath(__file__))


class SaxoLoginClient(SaxoOpenAPIClient):
    def __init__(
        self,
        app_config: Union[Dict, str, None] = "app_config.json",
        log_sink: Optional[str] = None,
        log_level: str = "DEBUG",
    ):
        super().__init__(app_config, log_sink, log_level)

    def login(
        self,
        redirect_url: Optional[AnyHttpUrl] = None,
        redirect_port: Optional[int] = None,
        launch_browser: bool = True,
        catch_redirect: bool = True,
        start_async_refresh: bool = False,
    ) -> None:
        """Log in to Saxo OpenAPI using the provided config provided in __init__().

        Defaults to first `localhost` redirect url in config (if not provided).

        - Use `catch_redirect` to start a server that will listen for the post-login
        redirect from Saxo SSO.
        - Use `redirect_port` to override the redirect port provided in redirect_url if
        the redirect server is behind a reverse proxy.
        - Use `launch_browser` to automatically show login page.
        - Use `start_async_refresh` to ensure the session is automatically refreshed (to
        be used in Jupyter Notebooks).
        """
        logger.debug(
            f"initializing login sequence with {redirect_url=}, {launch_browser=} {catch_redirect=} "
            f"{start_async_refresh=} {redirect_port=}"
        )
        _redirect_url = validate_redirect_url(self._app_config, redirect_url)
        state = token_urlsafe(20)
        auth_url = construct_auth_url(self._app_config, _redirect_url, state)
        logger.debug(f"logging in with {str(_redirect_url)=} and {str(auth_url)=}")

        if catch_redirect:
            redirect_server = RedirectServer(_redirect_url, state=state, port=redirect_port)
            redirect_server.start()

        if launch_browser:
            logger.debug("launching browser with login page")
            print("🌐 opening login page in browser - waiting for user to " "authenticate... 🔑")
            webbrowser.open_new(auth_url)
        else:
            print(f"🌐 navigate to the following web page to log in: {auth_url}")
            app_config = self._app_config.dict()
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-dev-shm-usage")
            browser = webdriver.Chrome(options=chrome_options)
            browser.get(f"{auth_url}")
            user = browser.find_element(By.NAME, "field_userid")
            pword = browser.find_element(By.NAME, "field_password")
            button = browser.find_element(By.NAME, "button_login")
            user.clear()
            user.send_keys(os.getenv("USER_ID", ""))
            pword.clear()
            pword.send_keys(os.getenv("USER_PASS", ""))
            browser.execute_script("arguments[0].click();", button)
            sleep(5)
            browser.quit()
        if catch_redirect:
            try:
                while not redirect_server.auth_code:
                    sleep(0.1)
                print("📞 received callback from Saxo SSO")
                _auth_code = parse_obj_as(AuthorizationCode, redirect_server.auth_code)
            except KeyboardInterrupt:
                logger.warning("keyboard interrupt received - shutting down")
                print("🛑 operation interrupted by user - shutting down")
                return
            finally:
                redirect_server.shutdown()
        else:
            parsed_qs = None
            while not parsed_qs:
                try:
                    redirect_location_input = input("📎 paste redirect location (url): ")
                    redirect_location = parse_obj_as(AnyHttpUrl, redirect_location_input)
                    parsed_qs = parse_qs(redirect_location.query)
                    _auth_code = parse_obj_as(AuthorizationCode, parsed_qs["code"][0])
                except ValidationError as e:
                    print(f"❌ failed to parse provided url due to error(s): {e}")
                except KeyboardInterrupt:
                    logger.warning("keyboard interrupt received - shutting down")
                    print("🛑 operation interrupted by user - shutting down")
                    return

        self.get_tokens(auth_code=_auth_code)

        assert self._token_data

        env = self._app_config.env.value  # type: ignore[union-attr]
        perm = "WRITE / TRADE" if self._token_data.write_permission else "READ"

        print(
            f"✅ authorization succeeded - connected to {env} environment with {perm} permissions "
            f"(session ID: {self._token_data.session_id})"
        )

        if self._app_config.env is APIEnvironment.LIVE and self._token_data.write_permission:
            print(
                "❗ NOTE: you are now connected to a real-money client in the LIVE "
                "environment with WRITE & TRADE permissions - this means that this "
                "client can create and change orders on your Saxo account!"
            )
