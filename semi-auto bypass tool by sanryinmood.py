# ============================================
# LINK4M.COM BYPASS TOOL - SANRY
# FUNCTION: Automated redirection and captcha handling bypass
# TARGET: Standard link4m.com short links
# ============================================

import asyncio
import random
import time
from urllib.parse import urljoin, urlparse, parse_qs
import re

from camoufox import AsyncNewBrowser
from playwright.async_api import async_playwright

class UniversalKeyExtractor:
    @staticmethod
    async def get_all_sitekeys(page) -> dict:
        """
        A) Scan and return all sitekeys (ReCAPTCHA and hCAPTCHA) found on page.
        Returns dict: {'recaptcha': '...', 'hcaptcha': '...'}
        """
        results = {"recaptcha": None, "hcaptcha": None}
        
        recaptcha_el = await page.query_selector('.g-recaptcha, [data-sitekey]')
        if recaptcha_el:
            sitekey = await recaptcha_el.get_attribute('data-sitekey')
            if sitekey and len(sitekey) >= 8:
                results["recaptcha"] = sitekey

        hcaptcha_el = await page.query_selector('.h-captcha, [data-sitekey]')
        if hcaptcha_el:
            sitekey = await hcaptcha_el.get_attribute('data-sitekey')
            if sitekey and len(sitekey) >= 8:
                results["hcaptcha"] = sitekey

        if not results["recaptcha"] or not results["hcaptcha"]:
            iframes = await page.query_selector_all('iframe')
            for iframe in iframes:
                try:
                    src = await iframe.get_attribute('src')
                    if not src:
                        continue
                    
                    parsed_url = urlparse(src)
                    queries = parse_qs(parsed_url.query)
                    
                    if "google.com/recaptcha" in src and "k" in queries:
                        results["recaptcha"] = queries["k"][0]
                    elif "hcaptcha.com/embed" in src and "sitekey" in queries:
                        results["hcaptcha"] = queries["sitekey"][0]
                    elif "recaptcha.net" in src and "k" in queries:
                        results["recaptcha"] = queries["k"][0]
                except Exception:
                    continue

        if not results["recaptcha"] or not results["hcaptcha"]:
            html_content = await page.content()
            
            if not results["recaptcha"]:
                patterns = [
                    r'sitekey\s*:\s*["\']([a-zA-Z0-9_-]{8,})["\']',
                    r'data-sitekey=["\']([a-zA-Z0-9_-]{8,})["\']',
                    r'recaptcha_site_key["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'g-recaptcha.*?sitekey["\']?\s*:\s*["\']([^"\']+)["\']'
                ]
                for pattern in patterns:
                    re_match = re.search(pattern, html_content, re.I)
                    if re_match and len(re_match.group(1)) >= 8:
                        results["recaptcha"] = re_match.group(1)
                        break
            
            if not results["hcaptcha"]:
                h_patterns = [
                    r'sitekey\s*:\s*["\']([a-f0-9]{8,}[-]?[a-f0-9]*)["\']',
                    r'data-sitekey=["\']([a-f0-9]{8,}[-]?[a-f0-9]*)["\']',
                    r'hcaptcha_site_key["\']?\s*:\s*["\']([^"\']+)["\']'
                ]
                for pattern in h_patterns:
                    h_match = re.search(pattern, html_content, re.I)
                    if h_match and len(h_match.group(1)) >= 8:
                        results["hcaptcha"] = h_match.group(1)
                        break

        return results


class Link4mManualBypass:
    def __init__(self, url: str):
        self.url = url
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.get_time = 0
        self.post_time = 0
        self.popup_count = 0
        self.redirect_url = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.page:
                await self.page.close()
        except Exception as e:
            print(f"[CLEANUP] Page error: {e}")
        
        try:
            if self.context:
                await self.context.close()
        except Exception as e:
            print(f"[CLEANUP] Context error: {e}")
        
        try:
            if self.browser:
                await self.browser.close()
        except Exception as e:
            print(f"[CLEANUP] Browser error: {e}")
        
        finally:
            if self.playwright:
                await self.playwright.stop()

    async def stall_for_time(self, seconds: float):
        print(f"[STALL] Waiting {seconds:.2f} seconds...")
        start = time.time()
        await asyncio.sleep(seconds)
        elapsed = time.time() - start
        print(f"[STALL] Elapsed: {elapsed:.2f}s")

    async def random_scroll(self):
        for _ in range(random.randint(2, 5)):
            scroll_amount = random.randint(200, 600)
            await self.page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(random.uniform(0.5, 1.5))

    async def human_mouse_move(self, target_x: int = None, target_y: int = None):
        viewport = self.page.viewport_size
        if not viewport:
            viewport = {"width": 1920, "height": 1080}
        
        start_x = random.randint(0, viewport["width"])
        start_y = random.randint(0, viewport["height"])
        
        if target_x is None:
            target_x = random.randint(100, viewport["width"] - 100)
        if target_y is None:
            target_y = random.randint(100, viewport["height"] - 100)
        
        cp1_x = start_x + random.randint(-100, 100)
        cp1_y = start_y + random.randint(-50, 150)
        cp2_x = target_x + random.randint(-100, 100)
        cp2_y = target_y + random.randint(-50, 150)
        
        steps = random.randint(20, 40)
        for t in range(steps + 1):
            t_norm = t / steps
            mt = 1 - t_norm
            x = mt**3 * start_x + 3 * mt**2 * t_norm * cp1_x + 3 * mt * t_norm**2 * cp2_x + t_norm**3 * target_x
            y = mt**3 * start_y + 3 * mt**2 * t_norm * cp1_y + 3 * mt * t_norm**2 * cp2_y + t_norm**3 * target_y
            
            await self.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.008, 0.025))
        
        return target_x, target_y

    async def human_click_element(self, selector: str):
        element = await self.page.query_selector(selector)
        if not element:
            return False
        
        try:
            await element.scroll_into_view_if_needed()
            await asyncio.sleep(random.uniform(0.1, 0.3))
        except Exception as e:
            print(f"[SCROLL] Failed: {e}")
        
        box = await element.bounding_box()
        
        if box:
            target_x = box["x"] + random.uniform(box["width"] * 0.2, box["width"] * 0.8)
            target_y = box["y"] + random.uniform(box["height"] * 0.3, box["height"] * 0.7)
            
            await self.human_mouse_move(target_x, target_y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            jitter_x = random.uniform(-3, 3)
            jitter_y = random.uniform(-3, 3)
            await self.page.mouse.move(target_x + jitter_x, target_y + jitter_y)
            await asyncio.sleep(random.uniform(0.02, 0.08))
            
            await self.page.mouse.move(target_x, target_y)
            await asyncio.sleep(random.uniform(0.05, 0.12))
            
            await self.page.mouse.down()
            await asyncio.sleep(random.uniform(0.05, 0.15))
            await self.page.mouse.up()
            
            print(f"[CLICK] Physical click on '{selector}'")
            return True
        
        try:
            await element.click(force=True, timeout=3000)
            print(f"[CLICK] Force click on '{selector}'")
            return True
        except Exception as e:
            print(f"[FORCE CLICK] Failed: {e}")
        
        try:
            await self.page.evaluate("(el) => el.click()", element)
            print(f"[CLICK] JavaScript click on '{selector}'")
            return True
        except Exception as e:
            print(f"[JS CLICK] Failed: {e}")
        
        return False

    async def get_element_text(self, selector: str):
        element = await self.page.query_selector(selector)
        if not element:
            return None
        try:
            await element.scroll_into_view_if_needed()
            await asyncio.sleep(0.1)
        except:
            pass
        text = await element.inner_text()
        return text.strip() if text else None

    async def handle_popup(self, popup_page):
        self.popup_count += 1
        print(f"[POPUP] #{self.popup_count} - capturing...")
        
        try:
            await popup_page.wait_for_load_state("domcontentloaded", timeout=5000)
            popup_url = popup_page.url
            
            if popup_url and popup_url != "about:blank":
                print(f"[POPUP] #{self.popup_count} captured URL: {popup_url}")
                self.redirect_url = popup_url
                await popup_page.close()
                print(f"[POPUP] #{self.popup_count} closed after capture")
            else:
                await popup_page.close()
                print(f"[POPUP] #{self.popup_count} closed (blank)")
                
        except Exception as e:
            print(f"[POPUP] #{self.popup_count} error: {e}")
            try:
                await popup_page.close()
            except:
                pass

    async def init_browser(self):
        self.playwright = await async_playwright().start()
        
        self.browser = await AsyncNewBrowser(
            self.playwright,
            headless=False,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        self.context = await self.browser.new_context()
        self.context.on("page", lambda page: asyncio.create_task(self.handle_popup(page)))
        self.page = await self.context.new_page()
        
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = {runtime: {}};
        """)
        
        print("[INIT] Browser ready")

    async def smart_captcha_bypass(self):
        """
        B) Wait for manual CAPTCHA solving by user
        Tool pauses and checks every second until ReCAPTCHA is ticked (aria-checked="true")
        """
        print("\n" + "="*60)
        print("[DETECTOR] Waiting for you to solve CAPTCHA manually on screen...")
        print("[DETECTOR] Please complete the CAPTCHA challenge in the browser window.")
        print("[DETECTOR] The tool will automatically detect when CAPTCHA is solved.")
        print("="*60 + "\n")
        
        solved = False
        check_count = 0
        
        while not solved:
            await asyncio.sleep(1)
            check_count += 1
            if check_count % 10 == 0:
                print(f"[DETECTOR] Still waiting... ({check_count} seconds elapsed)")
            
            # Check for ReCAPTCHA iframe
            recaptcha_iframe = await self.page.query_selector('iframe[src*="recaptcha"]')
            if recaptcha_iframe:
                try:
                    frame = await recaptcha_iframe.content_frame()
                    if frame:
                        # Check if checkbox is checked (green checkmark)
                        checkbox = await frame.query_selector('#recaptcha-anchor[aria-checked="true"]')
                        if checkbox:
                            print(f"\n[CAPTCHA] Detected solved CAPTCHA after {check_count} seconds!")
                            solved = True
                            break
                except Exception as e:
                    pass
            
            # Check for hCaptcha
            hcaptcha_iframe = await self.page.query_selector('iframe[src*="hcaptcha.com"]')
            if hcaptcha_iframe and not solved:
                try:
                    frame = await hcaptcha_iframe.content_frame()
                    if frame:
                        # hCaptcha checked state indicator
                        checked = await frame.query_selector('.checkbox[aria-checked="true"], [role="checkbox"][aria-checked="true"]')
                        if checked:
                            print(f"\n[CAPTCHA] Detected solved hCaptcha after {check_count} seconds!")
                            solved = True
                            break
                except Exception as e:
                    pass
            
            # If no CAPTCHA iframe exists, assume no CAPTCHA needed
            if not recaptcha_iframe and not hcaptcha_iframe:
                print("[CAPTCHA] No CAPTCHA iframe detected - proceeding")
                solved = True
                break
        
        print("[CAPTCHA] CAPTCHA check complete, continuing...")
        return True

    async def detect_and_wait_timer(self):
        timer_selectors = [
            '#countdown', '.countdown', '.timer', '#timer',
            '[data-countdown]', '.seconds-remaining',
            'span:has-text("seconds")', 'div:has-text("remaining")'
        ]
        
        max_wait = 0
        for selector in timer_selectors:
            try:
                text = await self.get_element_text(selector)
                if text:
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        timer_value = int(numbers[0])
                        if 0 < timer_value < 600:
                            max_wait = max(max_wait, timer_value)
            except:
                pass
        
        js_timer = await self.page.evaluate("""
            () => {
                let timers = [];
                if (typeof window.timerSeconds !== 'undefined') timers.push(window.timerSeconds);
                if (typeof window.countdown !== 'undefined') timers.push(window.countdown);
                if (typeof window.remainingTime !== 'undefined') timers.push(window.remainingTime);
                if (timers.length) return Math.max(...timers);
                return null;
            }
        """)
        
        if js_timer and isinstance(js_timer, (int, float)) and 0 < js_timer < 600:
            max_wait = max(max_wait, int(js_timer))
        
        if max_wait > 0:
            wait_time = max_wait + random.uniform(0.5, 1.5)
            await self.stall_for_time(wait_time)
        else:
            await self.stall_for_time(random.uniform(4, 9))

    async def find_and_click_submit(self):
        """
        C) Dynamic submit button finder with extensive selector patterns.
        """
        submit_selectors = [
            '#submit', '#submit-btn', '#submit-button', '#continue', '#continue-btn',
            '#next', '#next-btn', '#verify', '#verify-btn', '#download', '#download-btn',
            '#get-link', '#generate',
            '.submit', '.submit-btn', '.submit-button', '.btn-submit',
            '.continue', '.continue-btn', '.continue-button', '.btn-continue',
            '.next', '.next-btn', '.btn-next', '.verify', '.verify-btn',
            '.download', '.download-btn', '.get-link', '.generate',
            'button[type="submit"]', 'input[type="submit"]',
            'button:has-text("Submit")', 'button:has-text("Continue")',
            'button:has-text("Next")', 'button:has-text("Verify")',
            'button:has-text("Download")', 'button:has-text("Get Link")',
            'button:has-text("Generate")', 'button:has-text("Proceed")',
            'button:has-text("Go")',
            'a:has-text("Continue")', 'a:has-text("Click here")',
            'a:has-text("Next")', 'a:has-text("Proceed")',
            'a:has-text("Verify")', 'a:has-text("Download")',
            'a:has-text("Get Link")',
            'button:has-text("continue")', 'button:has-text("submit")',
            'button:has-text("verify")', 'button:has-text("next")',
            'button:has-text("download")', 'button:has-text("proceed")',
            'button:has-text("go")',
            'input:has-text("Continue")', 'input:has-text("Submit")',
            'input:has-text("Next")',
            'button:visible', 'input[type="button"]:visible',
            '*:has-text("Continue"):visible', '*:has-text("Submit"):visible',
            '*:has-text("Next"):visible', '*:has-text("Verify"):visible',
            '*:has-text("Download"):visible', '*:has-text("Proceed"):visible',
            '*:has-text("Get Link"):visible', '*:has-text("Generate"):visible'
        ]
        
        for selector in submit_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    if await self.human_click_element(selector):
                        print(f"[SUBMIT] Successfully clicked with selector: {selector}")
                        return True
            except Exception as e:
                continue
        
        print("[SUBMIT] No submit button found with any selector")
        return False

    async def bypass(self):
        """
        D) Main orchestration with manual CAPTCHA waiting
        """
        self.get_time = time.time()
        
        await self.init_browser()
        
        print(f"[GET] {self.url}")
        await self.page.goto(self.url, wait_until="networkidle", timeout=45000)
        
        await self.random_scroll()
        await self.human_mouse_move()
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        await self.detect_and_wait_timer()
        
        # Wait for manual CAPTCHA solving
        await self.smart_captcha_bypass()
        
        middle_stall = random.uniform(4, 10)
        await self.stall_for_time(middle_stall)
        
        clicked = await self.find_and_click_submit()
        
        if not clicked:
            print("[SUBMIT] Could not find or click any submit button")
        
        self.post_time = time.time()
        total_time = self.post_time - self.get_time
        print(f"[TOTAL] {total_time:.2f}s | Popups captured: {self.popup_count}")
        
        await asyncio.sleep(random.uniform(3, 6))
        
        if self.redirect_url:
            print(f"[RESULT] Redirect captured from popup: {self.redirect_url}")
            return self.redirect_url
        
        final_url = self.page.url
        if final_url != self.url and not final_url.startswith("https://link4m.com"):
            print(f"[RESULT] Main page URL: {final_url}")
            return final_url
        
        meta_redirect = await self.page.query_selector('meta[http-equiv="refresh"]')
        if meta_redirect:
            content = await meta_redirect.get_attribute('content')
            if content:
                match = re.search(r'url=(.+)', content, re.I)
                if match:
                    final_url = urljoin(self.url, match.group(1))
                    print(f"[RESULT] Meta redirect: {final_url}")
                    return final_url
        
        print("[ERROR] No redirect found")
        return None


async def main():
    """
    E) Main entry point - Complete functional call for manual CAPTCHA solving
    """
    target = "https://link4m.com/zBU8SSO"
    
    print("\n" + "="*60)
    print("LINK4M BYPASS TOOL - MANUAL CAPTCHA MODE")
    print("="*60)
    print("\nInstructions:")
    print("1. A browser window will open automatically")
    print("2. Navigate to the target link")
    print("3. When CAPTCHA appears, solve it manually in the browser")
    print("4. The tool will auto-detect when CAPTCHA is solved")
    print("5. Then it will auto-click the continue button")
    print("="*60 + "\n")
    
    async with Link4mManualBypass(target) as bypasser:
        result = await bypasser.bypass()
        print(f"\n[FINAL] Final Destination: {result}")

if __name__ == "__main__":
    asyncio.run(main())