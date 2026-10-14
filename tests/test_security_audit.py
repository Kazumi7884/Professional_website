"""Regression cases for public asset confinement and authenticated outbound work."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


successor = load('audit_successor', 'successor/build.py')
legacy = load('audit_legacy', 'tools/site.py')
mal = load('audit_mal', 'tools/sync_myanimelist.py')


class AssetConfinement(unittest.TestCase):
    def test_symlinked_asset_ancestor_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'private/images').mkdir(parents=True)
            try:
                (root / 'static').symlink_to(root / 'private', target_is_directory=True)
            except OSError:
                self.skipTest('Symlinks unavailable on this account')
            with patch.object(successor, 'ROOT', root), self.assertRaises(ValueError):
                successor.validate_public_assets(root / 'static/images')

    def test_active_and_ambiguous_link_schemes_are_rejected(self):
        for url in ['javascript:alert(1)', 'data:text/html,test', '//example.org', '/\\example.org', '/about/\n']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                successor.link(url, 'Untrusted title')

    def test_both_builders_reject_symlinked_public_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / 'assets'
            assets.mkdir()
            private = root / 'private.txt'
            private.write_text('private sentinel')
            try:
                (assets / 'leak.txt').symlink_to(private)
            except OSError:
                self.skipTest('Symlinks unavailable on this account')
            for builder in (successor, legacy):
                with self.subTest(builder=builder.__name__), patch.object(builder, 'ROOT', root):
                    with self.assertRaises(ValueError):
                        builder.validate_public_assets(assets)

    def test_ordinary_public_files_remain_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'images').mkdir()
            (root / 'images/example.webp').write_bytes(b'public image')
            with patch.object(successor, 'ROOT', root):
                successor.validate_public_assets(root / 'images')


class OutboundMAL(unittest.TestCase):
    def test_private_and_external_destinations_are_rejected_before_network(self):
        for url in ['http://127.0.0.1/private', 'https://example.org/v2/users/kaz/animelist',
                    'https://api.myanimelist.net.example.org/v2/users/kaz/animelist',
                    'https://user:pass@api.myanimelist.net/v2/users/kaz/animelist',
                    'https://api.myanimelist.net:444/v2/users/kaz/animelist',
                    'https://api.myanimelist.net/v2/users/kaz/animelist#fragment']:
            with self.subTest(url=url), patch.object(mal.urllib.request, 'build_opener') as opener:
                with self.assertRaises(ValueError):
                    mal.request_json(url, 'public-test-client-id')
                opener.assert_not_called()

    def test_pagination_cannot_send_headers_to_another_host(self):
        with patch.object(mal, 'request_json', return_value={'data': [], 'paging': {'next': 'http://127.0.0.1/private'}}) as request:
            with self.assertRaises(ValueError):
                mal.fetch_list('kaz', 'public-test-client-id')
            self.assertEqual(request.call_count, 1)

    def test_pagination_cycles_stop(self):
        def repeated(url, _client):
            return {'data': [], 'paging': {'next': url}}
        with patch.object(mal, 'request_json', side_effect=repeated) as request:
            with self.assertRaises(ValueError):
                mal.fetch_list('kaz', 'public-test-client-id')
            self.assertEqual(request.call_count, 1)

    def test_pagination_cannot_switch_users(self):
        with patch.object(mal, 'request_json', return_value={'data': [], 'paging': {'next': 'https://api.myanimelist.net/v2/users/other/animelist'}}):
            with self.assertRaises(ValueError):
                mal.fetch_list('kaz', 'public-test-client-id')

    def test_valid_pagination_preserves_results(self):
        with patch.object(mal, 'request_json', side_effect=[{'data': [{'node': {'id': 1}}], 'paging': {'next': 'https://api.myanimelist.net/v2/users/kaz/animelist?offset=1'}}, {'data': [{'node': {'id': 2}}]}]):
            self.assertEqual(len(mal.fetch_list('kaz', 'public-test-client-id')), 2)

    def test_redirects_are_refused(self):
        with self.assertRaises(ValueError):
            mal.NoRedirect().redirect_request(None, None, 302, 'Found', {}, 'https://example.org/')
