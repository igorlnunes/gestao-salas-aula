from django import forms
from .models import Room
import json

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'available_hours']
        widgets = {
            'available_hours': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'available_hours': 'Format: {"monday": [{"from": 9, "to": 17}]}. Use double quotes.',
        }

    def clean_available_hours(self):
        data = self.cleaned_data['available_hours']

        # If it's already a dict (Django might have parsed it), use it.
        # If it's a string, we might need to parse it, but JSONField usually handles basic parsing.
        # However, custom validation logic is needed.

        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format.")

        if not isinstance(data, dict):
            raise forms.ValidationError("Must be a JSON object (dictionary).")

        valid_days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}

        for day, times in data.items():
            if day.lower() not in valid_days:
                raise forms.ValidationError(f"Invalid day: {day}. Must be one of {valid_days}")

            if not isinstance(times, list):
                raise forms.ValidationError(f"Value for {day} must be a list of time ranges.")

            for time_range in times:
                if not isinstance(time_range, dict):
                     raise forms.ValidationError(f"Time range in {day} must be a dictionary.")

                if 'from' not in time_range or 'to' not in time_range:
                    raise forms.ValidationError(f"Time range in {day} must contain 'from' and 'to' keys.")

                if not isinstance(time_range['from'], int) or not isinstance(time_range['to'], int):
                    raise forms.ValidationError(f"Time values in {day} must be integers.")

                if time_range['from'] >= time_range['to']:
                    raise forms.ValidationError(f"'from' time must be less than 'to' time in {day}.")

        return data
