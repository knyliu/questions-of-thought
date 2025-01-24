# tools/parse_utils.py

import re

def parse_multilevel_list(text: str):
    text = text.replace("\r\n", "\n")
    pattern_block = r"(?:^|\n)(\d+\.\s*.*?)(?=\n\d+\.\s|\Z)"
    blocks = re.findall(pattern_block, text, flags=re.DOTALL)

    results = []
    for block in blocks:
        block = block.strip()
        m = re.match(r"^(\d+)\.\s*(.*?)(?:\n|$)(.*)", block, flags=re.DOTALL)
        if m:
            top_title = m.group(2).strip()
            sub_text = m.group(3).rstrip("\n")

            if not sub_text.strip():
                cleaned_title = cleanup_markdown_title(top_title)
                results.append(cleaned_title)
            else:
                subs = re.findall(r"^[ \t]*[\*\-\+]\s*(.*)", sub_text, flags=re.MULTILINE)
                top_title_clean = cleanup_markdown_title(top_title)

                if subs:
                    for s in subs:
                        s_clean = s.strip()
                        if s_clean:
                            line = f"{top_title_clean} - {s_clean}"
                            results.append(line)
                else:
                    sub_lines = [sl.strip() for sl in sub_text.split('\n') if sl.strip()]
                    if sub_lines:
                        for s in sub_lines:
                            line = f"{top_title_clean} - {s}"
                            results.append(line)
                    else:
                        results.append(top_title_clean)
        else:
            block_clean = block.replace("\n", " ").strip()
            if block_clean:
                results.append(block_clean)
    return results

def cleanup_markdown_title(title: str) -> str:
    title = re.sub(r"(\*\*|__)", "", title)
    title = re.sub(r"(\*|_)", "", title)
    return title.strip()
