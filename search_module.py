import re
import warnings
warnings.filterwarnings("ignore")

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


def search(query, max_results=3):
    queries_to_try = [
        query,
        f"{query} summary",
        re.sub(r'\b(vs|versus)\b', '', query).strip()
    ]

    for q in queries_to_try:
        try:
            results = list(DDGS().text(q, max_results=max_results))
            if results:
                output = []
                for r in results:
                    title = r.get("title", "")
                    snippet = r.get("body", "")
                    output.append(f"Title: {title}\nSnippet: {snippet}")
                return "\n\n".join(output)
        except Exception:
            continue

    return "No search results found."