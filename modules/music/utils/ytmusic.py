import websockets
import json
import logging

from modules.core import SearchItem

logger = logging.getLogger("fzfx.music")


async def _send_cdp( ws, payload: dict):
    await ws.send(json.dumps(payload))
    while True:
        res = json.loads(await ws.recv())
        if res.get("id") == payload.get("id"):
            return res

async def write_to_search_dom(wsurl, query):
        async with websockets.connect(wsurl) as ws:
            await ws.send(json.dumps({
                "id": 2,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": f"(async()=>{{const findInput=(root)=>{{const selectors=['ytmusic-search-box input','tp-yt-paper-input input','input[placeholder*=\\\"Search\\\"]','input[aria-label*=\\\"Search\\\"]']; for (const sel of selectors) {{ const direct=root.querySelector(sel); if (direct) return direct; }} for (const el of root.querySelectorAll('*')) {{ if (el.shadowRoot) {{ const found=findInput(el.shadowRoot); if (found) return found; }} }} return null; }}; let el=findInput(document); if(!el) {{ const searchButton=[...document.querySelectorAll('*')].find((node)=>{{ const label=(node.getAttribute && (node.getAttribute('aria-label') || node.getAttribute('title'))) || ''; return label.toLowerCase().includes('search'); }}); if(searchButton) searchButton.click(); await new Promise((resolve)=>setTimeout(resolve, 150)); el=findInput(document); }} if(!el) return 'no input'; el.focus(); const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set; setter.call(el, {json.dumps(query)}); el.dispatchEvent(new InputEvent('input',{{bubbles:true, composed:true}})); el.dispatchEvent(new Event('change',{{bubbles:true, composed:true}})); return 'ok';}})()",
                    "returnByValue": True
                    ,"awaitPromise": True
                }
            }))
            await ws.recv()

async def get_suggestions_dom(wsurl):
        async with websockets.connect(wsurl) as ws:
            res = await _send_cdp(ws, {
                "id": 1,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "(()=>{const items=[]; const seen=new Set(); const clean=(s)=>String(s||'').replace(/\\s+/g,' ').trim(); for (const el of document.querySelectorAll('ytmusic-responsive-list-item-renderer')) { const text=clean(el.textContent); if (!text.includes('Song •')) continue; const a=el.querySelector(\"a[href*='watch?v=']\") || el.querySelector('a[href]'); if (!a) continue; const href=a.getAttribute('href') || ''; if (!href.includes('watch?v=')) continue; const url=new URL(href, location.origin).href; if (seen.has(url)) continue; const label=clean(el.getAttribute('aria-label') || a.getAttribute('aria-label') || a.getAttribute('title') || text.split('Song •', 1)[0]); if (!label) continue; seen.add(url); items.push({label, url}); if (items.length >= 20) break; } return JSON.stringify(items);})()",
                    "returnByValue": True,
                    "awaitPromise": True,
                }
            })

        value = res.get("result", {}).get("result", {}).get("value", "[]")
        if not isinstance(value, str) or not value.strip():
            return []

        try:
            items = json.loads(value)
            return items
        except json.JSONDecodeError:
            return []

async def get_suggestions_api(wsurl, query):

    jsexpr = f'''(async () => {{
      const ctx = ytcfg.get('INNERTUBE_CONTEXT');
      const resp = await fetch(
        'https://music.youtube.com/youtubei/v1/music/get_search_suggestions?prettyPrint=false',
        {{
          method: 'POST',
          headers: {{ 'content-type': 'application/json' }},
          credentials: 'include',
          body: JSON.stringify({{
            context: ctx,
            input: {json.dumps(query)},
          }}),
        }}
      );
      const data = await resp.json();
      const items = [];
      const seen = new Set();

      const pushSong = (item) => {{
        const r = item?.musicResponsiveListItemRenderer;
        if (!r) return;

        const secondLine = (r.flexColumns?.[1]?.musicResponsiveListItemFlexColumnRenderer?.text?.runs || [])
          .map((run) => run.text || '')
          .join('');
        if (!secondLine.includes('Song')) return;

        const label = (r.flexColumns?.[0]?.musicResponsiveListItemFlexColumnRenderer?.text?.runs || [])
          .map((run) => run.text || '')
          .join('')
          .trim();
        const videoId = r.navigationEndpoint?.watchEndpoint?.videoId
          || r.playlistItemData?.videoId
          || r.overlay?.musicItemThumbnailOverlayRenderer?.content?.musicPlayButtonRenderer?.playNavigationEndpoint?.watchEndpoint?.videoId;
        if (!label || !videoId) return;

        const url = `https://music.youtube.com/watch?v=${{videoId}}`;
        
        if (!label || !url) return;
        if (seen.has(url)) return;
        seen.add(url);
        items.push({{label, url}});

      }};

      for (const section of data.contents || []) {{
        const renderer = section.searchSuggestionsSectionRenderer;
        if (!renderer) continue;
        for (const item of renderer.contents || []) {{
          pushSong(item);
        }}
      }}
      return items;
    }})()'''

    async with websockets.connect(wsurl) as ws:
          res = await _send_cdp(ws, {
              "id": 1,
              "method": "Runtime.evaluate",
              "params": {
                  "expression": jsexpr,
                  "returnByValue": True,
                  "awaitPromise": True,
              },
          })
          value = res.get("result", {}).get("result", {}).get("value", [])
          if isinstance(value, list):
              return value
          if isinstance(value, str) and value.strip():
              try:
                  parsed = json.loads(value)
                  return parsed if isinstance(parsed, list) else []
              except json.JSONDecodeError:
                  return []
          return []

async def _search_songs_api(wsurl, query):
    logger.debug("search api start query=%r", query)
    jsexpr = f'''
        (async () => {{
          const ctx = ytcfg.get('INNERTUBE_CONTEXT');
          const resp = await fetch('https://music.youtube.com/youtubei/v1/search?prettyPrint=false', {{
            method: 'POST',
            headers: {{ 'content-type': 'application/json' }},
            credentials: 'include',
            body: JSON.stringify({{
              context: ctx,
              query: {json.dumps(query)},
            }}),
          }});
          const data = await resp.json();
          const items = [];
          const seen = new Set();
          const pushSong = (item) => {{
            const r = item?.musicResponsiveListItemRenderer;
            if (!r) return;
            const line2 = (r.flexColumns?.[1]?.musicResponsiveListItemFlexColumnRenderer?.text?.runs || [])
              .map(run => run.text || '')
              .join('');
            if (!line2.includes('Song')) return;
            const label = (r.flexColumns?.[0]?.musicResponsiveListItemFlexColumnRenderer?.text?.runs || [])
              .map(run => run.text || '')
              .join('')
              .trim();
            const videoId =
              r.navigationEndpoint?.watchEndpoint?.videoId ||
              r.playlistItemData?.videoId ||
              r.overlay?.musicItemThumbnailOverlayRenderer?.content?.musicPlayButtonRenderer?.playNavigationEndpoint?.watchEndpoint?.videoId;
            if (!label || !videoId) return;
            const url = `https://music.youtube.com/watch?v=${{videoId}}`;
            if (seen.has(url)) return;
            seen.add(url);
            items.push({{label, url }});
          }};
          const walk = (node) => {{
            if (!node || typeof node !== 'object') return;
            if (node.musicResponsiveListItemRenderer) pushSong(node);
            for (const value of Object.values(node)) {{
              if (Array.isArray(value)) {{
                for (const v of value) walk(v);
              }} else if (value && typeof value === 'object') {{
                walk(value);
              }}
            }}
          }};
          walk(data.contents);
          return items;
        }})()
    '''
    async with websockets.connect(wsurl) as ws:
          res = await _send_cdp(ws, {
              "id": 1,
              "method": "Runtime.evaluate",
              "params": {
                  "expression": jsexpr,
                  "returnByValue": True,
                  "awaitPromise": True,
              },
          })
          value = res.get("result", {}).get("result", {}).get("value", [])
          if isinstance(value, list):
              return value
          if isinstance(value, str) and value.strip():
              try:
                  parsed = json.loads(value)
                  logger.debug("search api returned parsed count=%s", len(parsed) if isinstance(parsed, list) else None)
                  return parsed if isinstance(parsed, list) else []
              except json.JSONDecodeError:
                  logger.exception("search api json decode failed")
                  return []
          return []

def toSearchItem(items):
    res_items: list[SearchItem] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        label = item.get("label", "")
        url = item.get("url", "")
        if isinstance(label, str) and isinstance(url, str) and label and url:
            res_items.append(SearchItem(
                key=f"ytmusic:{url}",
                type="music",
                label=label,
                meta={"url": url},
            ))
    return res_items
