from pathlib import Path
import json, random


BAISE_DIR = Path(__file__).resolve().parent
FINGERPRINTS_DIR = BAISE_DIR / "fingerprints"

# list of fingerprint 
fingerprints = []
seen_user_agent = set() # base on uniqe useragent saved fingerprint

# load and append all fingerprint to list
for path in FINGERPRINTS_DIR.glob("*.json"):
    try:
        with open(path, 'r', encoding = 'utf-8') as f:
            content = f.read().strip()
            
            if not content:
                print(f"⚠ Skipped empty file: {path.name}")
                continue
        
            fingerprint = json.loads(content)
            user_agent = fingerprint.get("navigator", {}).get("userAgent", "").strip() 
            
            if not user_agent:
               print(f"UserAgent not found {path.name}")  

            if user_agent not in seen_user_agent: 
                seen_user_agent.add(user_agent)
                fingerprints.append(fingerprint)
                # print(f"✔ loaded: {path.name} | UA {user_agent}")
            else:
                pass
                # print(f"🔁 Duplicate skipped: {path.name}")
    
    except json.JSONDecodeError as e:
        print(f"❌ JSON error in {path.name}: {e}")
    except UnicodeDecodeError as e:
      print(f"❌ Encoding error in {path.name}: {e}")
    except Exception as e:
      print(f"❌ Unexpected error in {path.name}: {e}")
    


async def load_fingerprint():
    print(f"✔ Total {len(fingerprints)} uniqe userAgent loaded")
    fingerprint = random.choice(fingerprints)
    nav = fingerprint.get("navigator", {})
    screen = fingerprint.get("screen", {})

    # Set defaults for screen dimensions if missing
    screen.setdefault("width", 1920)
    screen.setdefault("height", 1080)
    screen.setdefault("outerWidth", screen["width"])
    screen.setdefault("outerHeight", screen["height"])
    screen.setdefault("screenX", 0)
    screen.setdefault("devicePixelRatio", 1.0)

    plugins = fingerprint.get("PluginsData", {}).get("plugin", [])
    fonts = fingerprint.get("fonts", [])
    battery = fingerprint.get("battery", {})
    audio_codecs = fingerprint.get("audioCodecs", {})
    video_codecs = fingerprint.get("videoCodecs", {})
    video_card = fingerprint.get("videoCard", {})

    plugin_objects = []
    for p in plugins:
        plugin_objects.append({
            "name": p["name"],
            "description": p["description"],
            "filename": p["filename"],
            "mimeTypes": [{
                "type": m["type"],
                "suffixes": m["suffixes"],
                "description": m["description"]
            } for m in p.get("mimeTypes", [])]  
        })

    # JavaScript injection script
    script = f"""
    # ========== SCREEN PROPERTIES ==========
    Object.defineProperty(window, 'innerWidth', {{
      get: () => {screen['width']}
    }});
    Object.defineProperty(window, 'innerHeight', {{
      get: () => {screen['height']}
    }});
    Object.defineProperty(window, 'outerWidth', {{
      get: () => {screen['outerWidth']}
    }});
    Object.defineProperty(window, 'outerHeight', {{
      get: () => {screen['outerHeight']}
    }});
    Object.defineProperty(window, 'screenX', {{
      get: () => {screen['screenX']}
    }});
    Object.defineProperty(window, 'devicePixelRatio', {{
      get: () => {screen['devicePixelRatio']}
    }});


    // ========== NAVIGATOR PROPERTIES ==========
    const navigatorProps = {{
      userAgent: {json.dumps(nav['userAgent'])},
      language: {json.dumps(nav['language'])},
      languages: {json.dumps(nav['languages'])},
      platform: {json.dumps(nav['platform'])},
      deviceMemory: {nav['deviceMemory']},
      hardwareConcurrency: {nav['hardwareConcurrency']},
      maxTouchPoints: {nav['maxTouchPoints']},
      product: {json.dumps(nav.get('product', 'Gecko'))},
      productSub: {json.dumps(nav.get('productSub', '20030107'))},
      vendor: {json.dumps(nav.get('vendor', 'Google Inc.'))},
      vendorSub: {json.dumps(nav.get('vendorSub', ''))},
      doNotTrack: {json.dumps(nav.get("doNotTrack", "unspecified"))}
    }};
    for (const [prop, value] of Object.entries(navigatorProps)) {{
      Object.defineProperty(navigator, prop, {{
        value: value,
        writable: false,
        configurable: false,
        enumerable: true
      }});
    }}

    // ========== FONT ENUMERATION ==========
    const fontList = {json.dumps(fonts)};
    Object.defineProperty(document, 'fonts', {{
      value: {{
        status: 'loaded',
        ready: Promise.resolve(),
        check: (font, text) => true,
        load: (font, text) => Promise.resolve(),
        values: () => fontList.map(f => new FontFace(f, '')).values()
      }},
      configurable: false
    }});

    // ========== BATTERY API ==========
    Object.defineProperty(navigator, 'getBattery', {{
      value: () => Promise.resolve({{
        charging: {json.dumps(battery.get('charging', True))},
        chargingTime: {json.dumps(battery.get('chargingTime', 0))},
        dischargingTime: {json.dumps(battery.get('dischargingTime', 0))},
        level: {battery.get('level', 1.0)}
      }}),
      configurable: false
    }});

    // ========== MEDIA CAPABILITIES (Video) ==========
    HTMLVideoElement.prototype.canPlayType = function(type) {{
      const codecs = {json.dumps(video_codecs)};
      const match = type.match(/video\\/(\\w+)/);
      if (match) {{
        const format = match[1];
        return codecs[format] || 'maybe';
      }}
      return 'maybe';
    }};

    // ========== MEDIA CAPABILITIES (Audio) ==========
    HTMLAudioElement.prototype.canPlayType = function(type) {{
      const codecs = {json.dumps(audio_codecs)};
      const match = type.match(/audio\\/(\\w+)/);
      if (match) {{
        const format = match[1];
        return codecs[format] || 'maybe';
      }}
      return 'maybe';
    }};

    // ========== BROKEN IMAGE HANDLING ==========
    const OriginalImage = window.Image;
    window.Image = function() {{
      const img = new OriginalImage();
      img.addEventListener('error', () => {{
        Object.defineProperty(img, 'naturalWidth', {{ value: 16 }});
        Object.defineProperty(img, 'naturalHeight', {{ value: 16 }});
      }}, {{ once: true }});
      return img;
    }};

    // ========== PERMISSIONS API ==========
    const originalPermissionsQuery = navigator.permissions.query;
    navigator.permissions.query = async (descriptor) => {{
      if (descriptor.name === 'geolocation') {{
        return {{ state: 'denied' }};
      }}
      return await originalPermissionsQuery(descriptor);
    }};

    // ========== USER AGENT DATA ==========
    if (navigator.userAgentData) {{
      Object.defineProperty(navigator.userAgentData, 'brands', {{
        value: {json.dumps(nav.get('userAgentData', {}).get('brands', []))},
        writable: false
      }});
      Object.defineProperty(navigator.userAgentData, 'mobile', {{
        value: {json.dumps(nav.get('userAgentData', {}).get('mobile', False))},
        writable: false
      }});
      Object.defineProperty(navigator.userAgentData, 'platform', {{
        value: {json.dumps(nav.get('userAgentData', {}).get('platform', ""))},
        writable: false
      }});
    }}

    // ========== VIDEO CARD / GPU INFO SPOOF ==========
    const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {{
      if (param === 37445) return {json.dumps(video_card.get("vendor", "Google Inc."))}; // UNMASKED_VENDOR_WEBGL
      if (param === 37446) return {json.dumps(video_card.get("renderer", "ANGLE (Google Inc.)"))}; // UNMASKED_RENDERER_WEBGL
      return originalGetParameter.call(this, param);
    }};

    """

    return script
