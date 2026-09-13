from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from thlib.side.client.tactic_client_lib.common import upload_multipart

from thlib.side.client.tactic_client_lib.common.upload_multipart import (
    TacticUploadException,
    UploadMultipart,
)


class UploadMultipartTests(unittest.TestCase):
    def test_execute_keeps_the_successful_retry_response(self):
        upload = UploadMultipart()
        upload.set_upload_server("http://tactic/upload")
        upload.posturl = Mock(side_effect=[
            ConnectionResetError("connection reset"),
            (200, "OK", b"uploaded"),
        ])

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "attachment.txt"
            path.write_bytes(b"attachment")
            upload.execute(str(path))

        self.assertEqual(upload.posturl.call_count, 2)
        self.assertEqual(upload.offset, 1)
        self.assertEqual(upload.tries, 0)

    def test_exhausted_retries_raise_the_transport_cause(self):
        upload = UploadMultipart()
        upload.posturl = Mock(
            side_effect=ConnectionResetError("connection reset")
        )

        with self.assertRaises(TacticUploadException) as raised:
            upload.upload("http://tactic/upload", [], [])

        self.assertIn("failed after 5 attempts", str(raised.exception))
        self.assertIn("connection reset", str(raised.exception))
        self.assertIsInstance(
            raised.exception.__cause__, ConnectionResetError
        )
        self.assertEqual(upload.posturl.call_count, 5)
        self.assertEqual(upload.tries, 0)

    def test_http_failure_is_not_reported_as_a_missing_return_value(self):
        upload = UploadMultipart()
        upload.posturl = Mock(
            return_value=(503, "Service Unavailable", b"")
        )

        with self.assertRaises(TacticUploadException) as raised:
            upload.upload("http://tactic/upload", [], [])

        message = str(raised.exception)
        self.assertIn("HTTP 503 Service Unavailable", message)
        self.assertNotIn("NoneType", message)
        self.assertEqual(upload.posturl.call_count, 5)

    def test_unicode_filename_is_sent_as_utf8_bytes(self):
        upload = UploadMultipart()
        response = Mock(
            status=200,
            reason="OK",
            read=Mock(return_value=b"uploaded"),
        )
        connection = Mock()
        connection.getresponse.return_value = response

        with patch.object(
            upload_multipart.httplib,
            "HTTPConnection",
            return_value=connection,
        ):
            result = upload.post_multipart(
                "tactic.example",
                "/default/UploadServer/",
                [("action", "create")],
                [("file", r"D:\\temp\\статья.txt", b"content")],
                "http",
            )

        self.assertEqual(result, (200, "OK", b"uploaded"))
        request = connection.request.call_args.args
        self.assertEqual(request[:2], (
            "POST", "/default/UploadServer/",
        ))
        body = request[2]
        self.assertIsInstance(body, bytes)
        self.assertIn("статья.txt".encode("utf-8"), body)
        self.assertNotIn(r"D:\\temp".encode("utf-8"), body)
        self.assertIn(b"data:xyz/xyz;base64,", body)

    def test_local_encoding_error_is_not_retried(self):
        upload = UploadMultipart()
        upload.posturl = Mock(side_effect=UnicodeEncodeError(
            "latin-1", "статья", 0, 6, "not valid Latin-1"
        ))

        with self.assertRaises(TacticUploadException) as raised:
            upload.upload("http://tactic/upload", [], [])

        self.assertIn("could not prepare the request", str(raised.exception))
        self.assertEqual(upload.posturl.call_count, 1)


if __name__ == "__main__":
    unittest.main()
