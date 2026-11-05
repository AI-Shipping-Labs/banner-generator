import io

import pytest

from banner_generator import html_renderer_handler as handler
from banner_generator.html_renderer import RenderJob


def payload(**overrides):
    job = {
        "schema": "html-renderer.job.v1",
        "job_id": "card-job-123",
        "input": {"bucket": "private", "key": "input.html"},
        "output": {"bucket": "private", "key": "banner.png"},
        "format": "png",
        "viewport": {"width": 2400, "height": 1350},
    }
    return {**job, **overrides}


class ClientError(Exception):
    def __init__(self, code):
        self.response = {"Error": {"Code": code}}


class S3:
    class exceptions:
        ClientError = ClientError

    def __init__(self, existing=None, missing="404", race=None):
        self.existing, self.missing, self.race = existing, missing, race
        self.put = None

    def head_object(self, **kwargs):
        if self.existing is None:
            raise ClientError(self.missing)
        return self.existing

    def get_object(self, **kwargs):
        return {"Body": io.BytesIO(b"<h1>Card banner</h1>")}

    def put_object(self, **kwargs):
        if self.race:
            self.existing = self.race
            raise ClientError("PreconditionFailed")
        self.put = kwargs


def fake_render(html, job, output):
    output.write_bytes(b"png-fixture")
    return output


@pytest.mark.parametrize("missing", ["404", "403"])
def test_first_render_without_bucket_listing(monkeypatch, missing):
    s3 = S3(missing=missing)
    monkeypatch.setattr(handler, "render_document", fake_render)
    result = handler.process_job(payload(), s3=s3)
    assert result["schema"] == "html-renderer.completed.v1"
    assert result["size_bytes"] == len(b"png-fixture")
    assert s3.put["IfNoneMatch"] == "*"
    assert s3.put["Metadata"]["render-job-id"] == "card-job-123"
    assert s3.put["Metadata"]["sha256"] == result["checksum"]


def test_retry_reuses_matching_output_without_render(monkeypatch):
    s3 = S3(existing={"Metadata": {"render-job-id": "card-job-123", "sha256": "digest"}})
    monkeypatch.setattr(handler, "render_document", lambda *args: pytest.fail("rerendered"))
    assert handler.process_job(payload(), s3=s3)["reused"] is True


def test_existing_other_job_is_never_overwritten():
    s3 = S3(existing={"Metadata": {"render-job-id": "other"}})
    with pytest.raises(ValueError, match="already belongs"):
        handler.process_job(payload(), s3=s3)
    assert s3.put is None


@pytest.mark.parametrize("winner, reused", [("card-job-123", True), ("other", False)])
def test_concurrent_output_claim_is_conditional(monkeypatch, winner, reused):
    s3 = S3(race={"Metadata": {"render-job-id": winner, "sha256": "winner"}})
    monkeypatch.setattr(handler, "render_document", fake_render)
    if reused:
        result = handler.process_job(payload(), s3=s3)
        assert result["reused"] is True
        assert result["checksum"] == "winner"
    else:
        with pytest.raises(ValueError, match="different render job"):
            handler.process_job(payload(), s3=s3)


@pytest.mark.parametrize(
    "change",
    [
        {"job_id": "../../escape"},
        {"job_id": ""},
        {"viewport": {"width": 90000, "height": 1350}},
        {"format": "gif"},
        {"format": "jpeg", "image": {"quality": 101}},
    ],
)
def test_reject_unsafe_or_unbounded_jobs(change):
    with pytest.raises(ValueError):
        RenderJob.from_dict(payload(**change))


def test_invalid_direct_job_returns_structured_failure():
    result = handler.handler({"schema": "invalid", "job_id": "bad"})
    assert result["schema"] == "html-renderer.failed.v1"
    assert result["error"]["type"] == "ValueError"


def test_queue_reports_only_failed_record(monkeypatch):
    def process(job):
        if job["job_id"] == "bad":
            raise ValueError("bad")

    monkeypatch.setattr(handler, "process_job", process)
    monkeypatch.setattr(handler, "_publish_completion", lambda event: None)
    result = handler.handler(
        {
            "Records": [
                {"messageId": "a", "body": '{"job_id":"ok"}'},
                {"messageId": "b", "body": '{"job_id":"bad"}'},
            ]
        }
    )
    assert result == {"batchItemFailures": [{"itemIdentifier": "b"}]}
