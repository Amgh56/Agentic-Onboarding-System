"""Try the whole flow with the real model, the mock inbox and the fake systems.

Run from backend/:

    python -m scripts.try_agent

It creates a new demo company (you can log in with the printed details) and then:
1. saves a job with a procedure and a contract the applicant must sign on every page;
2. adds two applicants at once, and onboarding starts on its own;
3. one applicant replies with only their ID, so the agent asks for what is still missing;
4. they send the signed contract as a PDF, and the agent finishes onboarding.
"""

import uuid

from fastapi.testclient import TestClient

from app.main import app

PROCEDURE = """Ask every new hire for their national ID (or Iqama for non-Saudis) and check it.
When the documents are valid, create their work email, then the accounts their role needs.
Developers get GitHub and the engineering Slack channel, and IT prepares a laptop.
Tell IT at it@demo.example when a developer joins, so they prepare the laptop.
Tell Payroll at payroll@demo.example about every new joiner, without any equipment details.
Tell Finance at finance@demo.example about every new joiner, so they can set up their cost centre.
Finish with a welcome email that lists the new work email and accounts."""

NATIONAL_ID = """KINGDOM OF SAUDI ARABIA - NATIONAL ID CARD
Name: Omar Abdullah
ID number: 1098765432
Date of birth: 1995-04-12
Expiry date: 2031-05-01"""


def pdf(pages: list[str]) -> bytes:
    """A small real PDF with one line of text per page."""
    objects = [b"<</Type/Catalog/Pages 2 0 R>>", b""]
    kids = []
    for text in pages:
        content = b"BT /F1 14 Tf 30 60 Td (" + text.encode() + b") Tj ET"
        page_number, content_number = len(objects) + 1, len(objects) + 2
        kids.append(b"%d 0 R" % page_number)
        objects.append(b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 500 120]/Contents %d 0 R/Resources<</Font<</F1 99 0 R>>>>>>" % content_number)
        objects.append(b"<</Length %d>>stream\n" % len(content) + content + b"\nendstream")
    objects[1] = b"<</Type/Pages/Kids[" + b" ".join(kids) + b"]/Count %d>>" % len(pages)
    objects += [b""] * (98 - len(objects)) + [b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>"]
    out, offsets = b"%PDF-1.4\n", []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + (body or b"null") + b"\nendobj\n"
    start = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offsets)
    return out + b"trailer<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, start)


def show(title, lines):
    print(f"\n=== {title} ===")
    for line in lines:
        print(f"  {line}")


def main():
    with TestClient(app) as client:
        email, password = f"hr-{uuid.uuid4().hex[:6]}@demo.example", "demo-password"
        token = client.post("/auth/signup", json={
            "company_name": "Demo Company", "full_name": "Demo HR", "email": email, "password": password,
        }).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # Test mode: emails are stored in the outbox, not really sent. Use the Email settings page for Gmail.
        client.put("/email-settings", json={"provider": "mock", "email_address": "onboarding@demo.example"}, headers=headers)

        job = client.post("/jobs", json={
            "title": "Backend Developer", "description": "Builds and runs our Python APIs.", "procedure": PROCEDURE,
        }, headers=headers).json()
        client.post(f"/jobs/{job['id']}/documents", data={"instructions": "Please sign at the end of each page"},
                    files={"file": ("contract.pdf", pdf(["Employment contract - page 1", "Employment contract - page 2"]), "application/pdf")},
                    headers=headers)

        plan = client.post(f"/jobs/{job['id']}/plan/draft", headers=headers).json()
        show("Plan drafted from the procedure", [f"{s['id']}: {s['title']}" for s in plan["steps"]])
        show("Departments found in the procedure", [f"{d['name']}: {d['email'] or 'no email given'}" for d in plan["departments"]])

        print("\nAdding two applicants at once. Onboarding starts on its own...")
        omar, sara = client.post(f"/jobs/{job['id']}/candidates/bulk", json=[
            {"full_name_en": "Omar Abdullah", "full_name_ar": "عمر عبدالله", "phone": "0500000000",
             "email": "omar.personal@example.com", "date_of_birth": "1995-04-12", "role": "Backend developer"},
            {"full_name_en": "Sara Ali", "full_name_ar": "سارة علي", "phone": "0511111111",
             "email": "sara.personal@example.com", "date_of_birth": "1998-01-02", "role": "Backend developer"},
        ], headers=headers).json()

        def reply(subject, files):
            client.post("/mock-inbox", data={"from_address": omar["email"], "subject": f"{subject} [ONB-{omar['id']}]", "body": "Hello"},
                        files=files, headers=headers)

        print("Omar replies with only his ID (he forgot the signed contract)...")
        reply("Re: documents", [("files", ("national_id.txt", NATIONAL_ID.encode(), "text/plain"))])
        print("Omar sends the contract, signed at the end of each page...")
        reply("Signed contract", [("files", ("contract_signed.pdf", pdf([
            "Employment contract - page 1 ... Signed: Omar Abdullah",
            "Employment contract - page 2 ... Signed: Omar Abdullah",
        ]), "application/pdf"))])

        for person in (omar, sara):
            events = client.get(f"/candidates/{person['id']}/events", headers=headers).json()
            status = client.get(f"/candidates/{person['id']}", headers=headers).json()["status"]
            show(f"{person['full_name_en']}: {status}", [f"[{e['actor']}] {e['title']}: {e['detail']}" for e in reversed(events)])

        outbox = client.get("/outbox", headers=headers).json()
        show("Outbox", [f"to {e['to_address']}: {e['subject']}" for e in reversed(outbox)])
        missing = [e for e in outbox if e["subject"].startswith("Still needed")]
        if missing:
            show("The 'still needed' email (English part)", missing[0]["body"].split("---")[-1].strip().splitlines())

        contents = client.get("/systems/contents", headers=headers).json()
        show("Fake systems", [
            f"{s['name']}: {a['display_name']} {a['address']} {a['status']} {a['groups']}" for s in contents for a in s["accounts"]
        ] + [f"{s['name']}: ticket '{t['item']}' for {t['requester']}" for s in contents for t in s["tickets"]])

        approvals = client.get("/approvals", headers=headers).json()
        show("HR queue", [f"{a['kind']}: {a['action'] or a['reason']}" for a in approvals] or ["empty"])
        show("Log in to see it", [f"{email} / {password}"])


if __name__ == "__main__":
    main()
