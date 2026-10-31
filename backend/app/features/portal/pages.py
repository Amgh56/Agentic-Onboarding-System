from html import escape

STYLE = """<style>
body { margin: 0; font-family: system-ui, sans-serif; background: #f7f7f8; color: #16171a; }
main { max-width: 520px; margin: 40px auto; padding: 24px; background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; }
h1 { font-size: 22px; margin: 0 0 8px; }
p, li { line-height: 1.6; }
.ar { direction: rtl; text-align: right; }
hr { border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0; }
input[type=file] { display: block; margin: 16px 0; }
button { padding: 11px 18px; color: #fff; background: #0f9d58; border: 0; border-radius: 10px; font-size: 16px; cursor: pointer; }
</style>"""


def _page(title: str, content: str) -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>{STYLE}</head><body><main>{content}</main></body></html>"""


def upload_page(name_en: str, name_ar: str, documents: list[str]) -> str:
    items = "".join(f"<li>{escape(d)}</li>" for d in documents) or "<li>Your onboarding documents</li>"
    return _page("Upload your documents", f"""
<div class="ar"><h1>مرحبًا {escape(name_ar)}</h1><p>يرجى رفع المستندات التالية:</p></div>
<hr>
<h1>Hello {escape(name_en)}</h1>
<p>Please upload these documents:</p>
<ul>{items}</ul>
<form method="post" enctype="multipart/form-data">
  <input type="file" name="files" multiple required>
  <button type="submit">Upload / رفع</button>
</form>""")


def done_page() -> str:
    return _page("Thank you", """
<div class="ar"><h1>شكرًا لك</h1><p>استلمنا ملفاتك وسنتواصل معك عبر البريد الإلكتروني.</p></div>
<hr>
<h1>Thank you</h1>
<p>We received your files and will get back to you by email.</p>""")
