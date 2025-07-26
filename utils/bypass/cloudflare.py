import asyncio, json, os, re
from twocaptcha import TwoCaptcha
from dotenv import load_dotenv

# first load env value
load_dotenv()

class CloudflareBypasser:
    # constructor for get page obj and intialize vars
    def __init__(self,page):
        self.page = page
        self.api_key = os.getenv("2CAPTCHA_API_KEY")
        self.captured_params = None
     
    async def detect_and_bypass(self):
        if await self.page.locator("text='Additional Verification Required'").is_visible():
            print("Attempting Cloudflare Bypass")
            # frist we have to get parameter of captch like, sitkey, url etc.
            params = await self.get_captch_params(self)
            if params:
                token = await self.solve_captcha_async(params)
                if token:
                    await self.send_token(token)
                    await asyncio.sleep(5)
                    print("[+] Cloudflare Sucessfully Bypass")
                    return True
                else:
                    print("Failed to solve captcha")
                    return False
            else:
                print("Failed to get params, captcha")    
                return False
        
    async def get_captch_params(self):
        intercept_script = """
        console.clear = () => console.log("Console was cleared");
        let resolved = false;
        const intervalID = setInterval( () =>{
        if (window.turnstile && !resolved){
            clearInterval(intervalID);
            resolved = true;
            window.turnstile.render = (a,b) => {
            const params = {
            sitekey: b.sitekey,
            pageurl: b.window.location.href,
            data: b.cData,
            pagedata: b.action,
            useragent: b.userAgent
            };
            };
        };
        }; 50)
    """
        async def console_handler(msg):
            if "intercepted-params:" in msg.text:
                match = re.search(r"intercepted-params:(\{.*\})",msg.text)
                if match:
                    try:
                        self.captured_params = json.loads(match.group(1))
                    except json.JSONDecodeError:
                        pass
        self.page.on("console",console_handler)
        
        retries = 5
        while retries > 0 and not self.captured_params:
            print("[+] Attempting Cloudflare Baypass")
            await self.page.reload()
            await self.page.evaluate(intercept_script)
            await asyncio.sleep(5)
            retries -=1
        
        self.page.remove_listener("console", console_handler)

    async def solve_captcha_async(self, params):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.solve_captcha_sync(params))
    
    def solve_captcha_sync(self,params):
        solver = TwoCaptcha(self.api_key)
        try:
            result = solver.turnstile(
                sitekey = params["sitekey"],
                url = params["pageurl"],
                action = params["action"],
                data = params["data"],
                pagedata = params.get("pagedata"),
                useragent = params["useragent"],
            )
            print("Solved Successfully")
            print(f"result code: {result['code']}")
            return result["code"]
        except Exception as e:
            print(f"[-] Captcha Error:\n {e}")
            return None
    async def send_token(self,token):
        await self.page.evaluate(f"""
        () => {{
                if (typeof window.cfCallback === 'function'){{
                                window.cfCallback('{token}');
                }}
        }}
""")