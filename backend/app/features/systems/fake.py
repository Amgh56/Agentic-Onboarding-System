import re


def work_email_address(full_name: str, domain: str, taken: set[str]) -> str:
    """omar.abdullah@domain, or omar.abdullah2@domain if that one is taken."""
    words = re.sub(r"[^a-z0-9 ]", "", full_name.lower()).split() or ["user"]
    base = words[0] if len(words) == 1 else f"{words[0]}.{words[-1]}"
    address, number = f"{base}@{domain}", 1
    while address in taken:
        number += 1
        address = f"{base}{number}@{domain}"
    return address


def company_domain(company_name: str, company_id: int) -> str:
    slug = re.sub(r"[^a-z0-9]", "", company_name.lower())
    return f"{slug or f'company{company_id}'}.example"
