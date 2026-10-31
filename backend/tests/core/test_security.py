from app.core.security import create_token, create_upload_token, read_token, read_upload_token


def test_login_and_upload_tokens_cannot_be_swapped():
    upload = create_upload_token(candidate_id=5, company_id=2)
    login = create_token(5)

    assert read_upload_token(upload) == (5, 2)
    assert read_token(login) == 5
    assert read_token(upload) is None
    assert read_upload_token(login) is None
    assert read_upload_token("garbage") is None
