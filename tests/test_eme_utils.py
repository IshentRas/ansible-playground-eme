#!/usr/bin/python

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the library directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'library'))

from eme_utils import (
    parse_tag_objects,
    get_tag_objects,
    check_object_exists,
    check_tag_exists,
    export_object,
    import_object,
    export_tag,
    create_tag,
    run_air_command
)

class TestEMEUtils(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.module = MagicMock()
        self.module.fail_json = MagicMock(side_effect=Exception("Module failed"))
        self.module.params = {}

    def test_parse_tag_objects(self):
        """Test parsing tag objects from air command output."""
        # Test normal case
        sample_output = """
        /project/sit/graph_a.mp(/EMERepo/versions/graph_a/123)
        /project/sit/dml_b.dml(/EMERepo/versions/dml_b/45)
        /project/sit/xform_c.xfr(/EMERepo/versions/xform_c/67)
        """
        expected = [
            {'path': '/project/sit/graph_a.mp', 'version': '/EMERepo/versions/graph_a/123'},
            {'path': '/project/sit/dml_b.dml', 'version': '/EMERepo/versions/dml_b/45'},
            {'path': '/project/sit/xform_c.xfr', 'version': '/EMERepo/versions/xform_c/67'}
        ]
        result = parse_tag_objects(sample_output)
        self.assertEqual(result, expected)

        # Test empty input
        self.assertEqual(parse_tag_objects(""), [])

        # Test input with no valid objects
        self.assertEqual(parse_tag_objects("Some text\nMore text"), [])

        # Test input with malformed objects
        malformed = """
        /project/sit/graph_a.mp
        /project/sit/dml_b.dml(version)
        /project/sit/xform_c.xfr(/EMERepo/versions/xform_c/67)
        """
        result = parse_tag_objects(malformed)
        self.assertEqual(len(result), 2)  # Both dml_b.dml and xform_c.xfr should be parsed
        self.assertEqual(result[0]['path'], '/project/sit/dml_b.dml')
        self.assertEqual(result[0]['version'], 'version')
        self.assertEqual(result[1]['path'], '/project/sit/xform_c.xfr')
        self.assertEqual(result[1]['version'], '/EMERepo/versions/xform_c/67')

    @patch('eme_utils.run_air_command')
    def test_get_tag_objects_success(self, mock_run_command):
        """Test successful tag object retrieval."""
        mock_run_command.return_value = (0, """
        /project/sit/graph_a.mp(/EMERepo/versions/graph_a/123)
        /project/sit/dml_b.dml(/EMERepo/versions/dml_b/45)
        """, "")
        
        result = get_tag_objects(self.module, "test-tag")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['path'], '/project/sit/graph_a.mp')
        self.assertEqual(result[1]['path'], '/project/sit/dml_b.dml')

    @patch('eme_utils.run_air_command')
    def test_get_tag_objects_failure(self, mock_run_command):
        """Test tag object retrieval failure."""
        mock_run_command.return_value = (1, "", "Tag not found")
        
        with self.assertRaises(Exception):
            get_tag_objects(self.module, "non-existent-tag")

    @patch('eme_utils.run_air_command')
    def test_check_object_exists(self, mock_run_command):
        """Test object existence check."""
        # Test existing object
        mock_run_command.return_value = (0, "", "")
        self.assertTrue(check_object_exists(self.module, "/test/obj", "/test/ver"))

        # Test non-existing object
        mock_run_command.return_value = (1, "", "")
        self.assertFalse(check_object_exists(self.module, "/test/obj", "/test/ver"))

    @patch('eme_utils.run_air_command')
    def test_check_tag_exists(self, mock_run_command):
        """Test tag existence check."""
        # Test existing tag
        mock_run_command.return_value = (0, "", "")
        self.assertTrue(check_tag_exists(self.module, "test-tag"))

        # Test non-existing tag
        mock_run_command.return_value = (1, "", "")
        self.assertFalse(check_tag_exists(self.module, "non-existent-tag"))

    @patch('eme_utils.run_air_command')
    def test_export_object(self, mock_run_command):
        """Test object export."""
        # Test successful export
        mock_run_command.return_value = (0, "", "")
        self.assertTrue(export_object(self.module, "/test/obj", "/test/ver", "output.arl"))

        # Test export failure
        mock_run_command.return_value = (1, "", "Export failed")
        with self.assertRaises(Exception):
            export_object(self.module, "/test/obj", "/test/ver", "output.arl")

    @patch('eme_utils.run_air_command')
    def test_import_object(self, mock_run_command):
        """Test object import."""
        # Test successful import
        mock_run_command.return_value = (0, "", "")
        self.assertTrue(import_object(self.module, "input.arl"))

        # Test import failure
        mock_run_command.return_value = (1, "", "Import failed")
        with self.assertRaises(Exception):
            import_object(self.module, "input.arl")

    @patch('eme_utils.run_air_command')
    def test_export_tag(self, mock_run_command):
        """Test tag export."""
        # Test successful export
        mock_run_command.return_value = (0, "", "")
        self.assertTrue(export_tag(self.module, "test-tag", "output.arl"))

        # Test export failure
        mock_run_command.return_value = (1, "", "Export failed")
        with self.assertRaises(Exception):
            export_tag(self.module, "test-tag", "output.arl")

    @patch('eme_utils.run_air_command')
    def test_create_tag(self, mock_run_command):
        """Test tag creation."""
        # Test successful creation
        mock_run_command.return_value = (0, "", "")
        objects = [
            {'path': '/test/obj1', 'version': '/test/ver1'},
            {'path': '/test/obj2', 'version': '/test/ver2'}
        ]
        self.assertTrue(create_tag(self.module, "test-tag", objects, "Test comment"))

        # Test creation failure
        mock_run_command.return_value = (1, "", "Creation failed")
        with self.assertRaises(Exception):
            create_tag(self.module, "test-tag", objects, "Test comment")

        # Test missing tag name
        with self.assertRaises(Exception):
            create_tag(self.module, "", objects, "Test comment")

        # Test missing objects
        with self.assertRaises(Exception):
            create_tag(self.module, "test-tag", [], "Test comment")

    @patch('subprocess.Popen')
    def test_run_air_command(self, mock_popen):
        """Test running air commands."""
        # Test successful command
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        rc, stdout, stderr = run_air_command(self.module, "air tag show test-tag")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "output")
        self.assertEqual(stderr, "")

        # Test command failure
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("", "error")
        rc, stdout, stderr = run_air_command(self.module, "air tag show test-tag")
        self.assertEqual(rc, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "error")

        # Test command execution error
        mock_popen.side_effect = Exception("Command failed")
        with self.assertRaises(Exception):
            run_air_command(self.module, "air tag show test-tag")

if __name__ == '__main__':
    unittest.main() 