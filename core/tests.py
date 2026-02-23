from django.test import TestCase
from .models import Room
from .forms import RoomForm
import json

class RoomModelTest(TestCase):
    def test_room_creation(self):
        data = {"monday": [{"from": 9, "to": 17}]}
        room = Room.objects.create(name="Test Room", available_hours=data)
        self.assertEqual(room.name, "Test Room")
        self.assertEqual(room.available_hours, data)

class RoomFormTest(TestCase):
    def test_valid_form(self):
        valid_data = {
            'name': 'Valid Room',
            'available_hours': '{"monday": [{"from": 9, "to": 17}]}'
        }
        form = RoomForm(data=valid_data)
        self.assertTrue(form.is_valid())

    def test_invalid_json(self):
        invalid_json = {
            'name': 'Invalid JSON',
            'available_hours': '{invalid}'
        }
        form = RoomForm(data=invalid_json)
        self.assertFalse(form.is_valid())
        # Django's default error or mine
        self.assertTrue(any("JSON" in str(e) or "Enter a valid JSON" in str(e) for e in form.errors['available_hours']))

    def test_invalid_day(self):
        invalid_key = {
            'name': 'Invalid Key',
            'available_hours': '{"funday": [{"from": 9, "to": 17}]}'
        }
        form = RoomForm(data=invalid_key)
        self.assertFalse(form.is_valid())
        self.assertTrue(any("Invalid day" in str(e) for e in form.errors['available_hours']))

    def test_invalid_structure(self):
        invalid_struct = {
            'name': 'Invalid Struct',
            'available_hours': '{"monday": [{"from": 9}]}'
        }
        form = RoomForm(data=invalid_struct)
        self.assertFalse(form.is_valid())
        self.assertTrue(any("must contain" in str(e) for e in form.errors['available_hours']))
