import re
import whois
import dns.resolver
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import datetime
import warnings

warnings.filterwarnings("ignore")


# -----------------------------
# SAFE REQUEST (NEVER BLOCKS)
# -----------------------------
def safe_request(url):
    try:
        return requests.get(
            url,
            timeout=4,
            allow_redirects=True,
            verify=False,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
    except Exception:
        return None


# -----------------------------
# MAIN FEATURE EXTRACTION
# -----------------------------
def extract_features(url: str) -> dict:
    features = {}
    parsed = urlparse(url)
    domain = parsed.hostname or ""

    # -----------------------------
    # 1. having_IP_Address
    # -----------------------------
    features["having_IP_Address"] = (
        -1 if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", domain) else 1
    )

    # -----------------------------
    # 2. URL_Length
    # -----------------------------
    features["URL_Length"] = 1 if len(url) < 54 else -1

    # -----------------------------
    # 3. Shortining_Service
    # -----------------------------
    features["Shortining_Service"] = (
        -1
        if re.search(r"(bit\.ly|tinyurl|goo\.gl|ow\.ly|t\.co)", url.lower())
        else 1
    )

    # -----------------------------
    # 4. having_At_Symbol
    # -----------------------------
    features["having_At_Symbol"] = -1 if "@" in url else 1

    # -----------------------------
    # 5. double_slash_redirecting
    # -----------------------------
    features["double_slash_redirecting"] = (
        -1 if url.find("//", 8) != -1 else 1
    )

    # -----------------------------
    # 6. Prefix_Suffix
    # -----------------------------
    features["Prefix_Suffix"] = -1 if "-" in domain else 1

    # -----------------------------
    # 7. having_Sub_Domain
    # -----------------------------
    features["having_Sub_Domain"] = (
        -1 if domain.count(".") > 1 else 1
    )

    # -----------------------------
    # 8. SSLfinal_State
    # -----------------------------
    features["SSLfinal_State"] = (
        1 if parsed.scheme == "https" else -1
    )

    # -----------------------------
    # 9 & 24. Domain age
    # -----------------------------
    try:
        w = whois.whois(domain)
        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        age_days = (datetime.datetime.now() - creation).days

        features["Domain_registeration_length"] = (
            1 if age_days > 365 else -1
        )
        features["age_of_domain"] = (
            1 if age_days > 365 else -1
        )
    except Exception:
        features["Domain_registeration_length"] = -1
        features["age_of_domain"] = -1

    # -----------------------------
    # 10. Favicon
    # -----------------------------
    features["Favicon"] = 1

    # -----------------------------
    # 11. port
    # -----------------------------
    features["port"] = -1 if parsed.port else 1

    # -----------------------------
    # 12. HTTPS_token
    # -----------------------------
    features["HTTPS_token"] = -1 if "https" in domain.lower() else 1

    # -----------------------------
    # FETCH PAGE (SAFE)
    # -----------------------------
    r = safe_request(url)

    if r is None:
        # 🚨 Page unreachable → suspicious
        features.update({
            "Request_URL": -1,
            "URL_of_Anchor": -1,
            "Links_in_tags": -1,
            "SFH": -1,
            "Submitting_to_email": -1,
            "Redirect": -1,
            "on_mouseover": -1,
            "RightClick": -1,
            "popUpWidnow": -1,
            "Iframe": -1,
        })
    else:
        soup = BeautifulSoup(r.text, "html.parser")

        # -----------------------------
        # 13. Request_URL
        # -----------------------------
        media = soup.find_all(["img", "audio", "embed", "iframe"])
        external = [
            m.get("src") for m in media
            if m.get("src") and domain not in m.get("src")
        ]
        features["Request_URL"] = (
            -1 if len(external) / max(len(media), 1) > 0.3 else 1
        )

        # -----------------------------
        # 14. URL_of_Anchor
        # -----------------------------
        anchors = soup.find_all("a", href=True)
        unsafe = [
            a for a in anchors
            if domain not in a["href"] and not a["href"].startswith("/")
        ]
        features["URL_of_Anchor"] = (
            -1 if len(unsafe) / max(len(anchors), 1) > 0.5 else 1
        )

        # -----------------------------
        # 15. Links_in_tags
        # -----------------------------
        tags = soup.find_all(["meta", "script", "link"])
        bad = [
            t for t in tags
            if t.get("src") and domain not in t.get("src")
        ]
        features["Links_in_tags"] = (
            -1 if len(bad) / max(len(tags), 1) > 0.5 else 1
        )

        # -----------------------------
        # 16. SFH
        # -----------------------------
        forms = soup.find_all("form")
        features["SFH"] = (
            -1
            if any(
                f.get("action") and domain not in f.get("action")
                for f in forms
            )
            else 1
        )

        # -----------------------------
        # 17. Submitting_to_email
        # -----------------------------
        features["Submitting_to_email"] = (
            -1
            if any(
                f.get("action", "").startswith("mailto:")
                for f in forms
            )
            else 1
        )

        # -----------------------------
        # 19. Redirect (FIXED)
        # -----------------------------
        features["Redirect"] = (
            -1 if len(r.history) > 0 else 1
        )

        # -----------------------------
        # 20–23. JS / Iframe
        # -----------------------------
        text = r.text.lower()
        features["on_mouseover"] = (
            -1 if "onmouseover" in text else 1
        )
        features["RightClick"] = (
            -1 if "event.button==2" in text else 1
        )
        features["popUpWidnow"] = (
            -1 if "window.open" in text else 1
        )
        features["Iframe"] = (
            -1 if soup.find("iframe") else 1
        )

    # -----------------------------
    # 18. Abnormal_URL
    # -----------------------------
    features["Abnormal_URL"] = (
        -1 if domain not in url else 1
    )

    # -----------------------------
    # 25. DNSRecord
    # -----------------------------
    try:
        dns.resolver.resolve(domain, "A")
        features["DNSRecord"] = 1
    except Exception:
        features["DNSRecord"] = -1

    # -----------------------------
    # 26–30. External metrics (safe defaults)
    # -----------------------------
    features["web_traffic"] = 0
    features["Page_Rank"] = 0
    features["Google_Index"] = 1
    features["Links_pointing_to_page"] = 0
    features["Statistical_report"] = 1

    return features
