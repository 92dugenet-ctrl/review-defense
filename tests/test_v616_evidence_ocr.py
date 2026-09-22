import base64, io, json
from pathlib import Path
from src.evidence_ocr import extract_readable_text
from src.api_server import ReviewDefenseAPI


def call(app, method, path, body=None, token=None):
    raw=json.dumps(body or {}).encode(); env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
    if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
    out={}; data=b"".join(app(env,lambda status,headers: out.update(status=status,headers=headers))); return out["status"],json.loads(data)


def setup():
    app=ReviewDefenseAPI(); app.seed_user(organization_id='org-a',email='a@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'a@example.com','password':'StrongPass123!'})
    return app,login['access_token']


def test_pdf_text_extraction_is_bounded_and_unverified():
    from reportlab.pdfgen import canvas
    import io as _io
    buf=_io.BytesIO(); c=canvas.Canvas(buf); c.drawString(72,720,'Facture 60 euros'); c.save()
    out=extract_readable_text(content=buf.getvalue(),content_type='application/pdf',filename='x.pdf')
    assert out.method=='pdf-text' and '60 euros' in out.text


def test_png_ocr_extracts_text_without_network():
    import shutil
    import pytest
    if shutil.which("tesseract") is None:
        pytest.skip("tesseract is not installed in this runtime")
    from PIL import Image, ImageDraw, ImageFont
    img=Image.new('RGB',(600,120),'white'); d=ImageDraw.Draw(img); d.text((20,20),'60 euros',fill='black',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',42))
    buf=__import__('io').BytesIO(); img.save(buf,format='PNG')
    out=extract_readable_text(content=buf.getvalue(),content_type='image/png',filename='x.png')
    assert out.method=='ocr' and '60 euros' in out.text.lower()


def test_api_extracts_pdf_and_keeps_fact_unverified():
    app,t=setup()
    call(app,'POST','/v1/reviews',{'review_id':'r1','text':'On m\'a facture 50 euros.','rating':1,'published_at':'2026-09-20'},t)
    _,created=call(app,'POST','/v1/cases',{'review_id':'r1'},t); cid=created['case']['case_id']
    from reportlab.pdfgen import canvas
    b=__import__('io').BytesIO(); c=canvas.Canvas(b); c.drawString(72,720,'Facture 60 euros'); c.save()
    status,up=call(app,'POST','/v1/evidence',{'case_id':cid,'filename':'receipt.pdf','content_type':'application/pdf','content_base64':base64.b64encode(b.getvalue()).decode()},t)
    assert status=='201 Created'
    status,res=call(app,'POST',f'/v1/cases/{cid}/extract-facts',{},t)
    assert status=='200 OK' and res['count']==1 and res['verified'] is False
    assert res['suggestions'][0]['key']=='amount:eur' and res['suggestions'][0]['extraction_method']=='pdf-text'
    assert any(a['action']=='EVIDENCE_TEXT_EXTRACTED' for a in app.store.audit if a['organization_id']=='org-a')


def test_ocr_does_not_bypass_tenant_boundary():
    app,t=setup(); call(app,'POST','/v1/reviews',{'review_id':'r2','text':'x','rating':1,'published_at':'x'},t); _,c=call(app,'POST','/v1/cases',{'review_id':'r2'},t); cid=c['case']['case_id']
    app.seed_user(organization_id='org-b',email='b@example.com',password='StrongPass123!',role='ANALYST'); _,l=call(app,'POST','/v1/auth/login',{'email':'b@example.com','password':'StrongPass123!'})
    status,_=call(app,'POST',f'/v1/cases/{cid}/extract-facts',{},l['access_token']); assert status=='404 Not Found'


def test_ocr_rejects_unsupported_type():
    import pytest
    with pytest.raises(ValueError): extract_readable_text(content=b'x',content_type='application/zip',filename='x.zip')
