"""Shared CSS for the sample pages (landowner note, data centre brief)."""
CSS = """
.note { padding-block: 8px 56px }
.paper { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: clamp(18px, 4vw, 40px); max-width: 920px }
.paper h2 { font-size: 22px; margin: 30px 0 10px }
.paper h2:first-of-type { margin-top: 14px }
.paper h3 { font-size: 16px; margin: 18px 0 8px; font-weight: 600 }
.paper p, .paper li { color: var(--fg-2); max-width: 72ch; margin-bottom: 10px }
.paper ul, .paper ol { padding-left: 20px }
.paper b { color: var(--fg) }
.meta { font: 12.5px var(--mono); color: var(--fg-3) !important }
.small { font-size: 13px; color: var(--fg-3) !important }
.tw { overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; margin: 10px 0 12px }
.tw table { border-collapse: collapse; width: 100%; font-size: 14px; min-width: 520px }
.tw th { text-align: left; font: 600 11px var(--mono); letter-spacing: .05em; text-transform: uppercase; color: var(--fg-3); padding: 9px 11px; border-bottom: 1px solid var(--line); vertical-align: bottom }
.tw td { padding: 9px 11px; border-bottom: 1px solid var(--line); vertical-align: top; color: var(--fg-2) }
.tw tr:last-child td, .tw tr:last-child th { border-bottom: 0 }
.tw td b { color: var(--fg); font-weight: 600; display: block }
.tw .dev { display: block; font-size: 12.5px; color: var(--fg-3) }
.tw .n { text-align: right; font-family: var(--mono); white-space: nowrap }
.kv { min-width: 0 !important }
.kv th { width: 34%; text-transform: none; letter-spacing: 0; font: 600 13px var(--sans, inherit); color: var(--fg-2) }
.rag { font: 600 11px var(--mono); padding: 2px 7px; border-radius: 4px }
.rag.G { background: var(--ok-bg); color: var(--ok) }
.rag.A { background: var(--warn-bg); color: var(--warn) }
.rag.R { background: var(--err-bg, var(--warn-bg)); color: var(--err, var(--warn)) }
.qwcta { margin-top: 28px; max-width: 920px; padding: 20px; border: 1px solid var(--line); border-radius: 10px; background: var(--card); display: flex; flex-wrap: wrap; gap: 12px 20px; align-items: center; justify-content: space-between }
.qwcta p { max-width: 60ch; color: var(--fg-2) }
"""
