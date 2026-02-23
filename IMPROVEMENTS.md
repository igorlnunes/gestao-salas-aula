# Possible Improvements

The following is a list of potential improvements for the project:

## Code Quality & Structure
- **Use Mixins for Auth:** Replace manual authentication checks in Class-Based Views (like `SalaCreateView.dispatch`) with `LoginRequiredMixin`.
- **Refactor Templates:** specific templates currently duplicate HTML structure (head, body, scripts). Create a `base.html` template and have other templates extend it to reduce duplication and improve maintainability.
- **Environment Variables:** Move sensitive information (like `SECRET_KEY`, `DEBUG`, `allowed_hosts`) to environment variables (e.g., using `python-dotenv`).

## Functionality
- **Reservation Creation:** Currently, there is no UI for users to create reservations (only `Sala` creation). Add a `CreateView` for `Reserva` so users can book rooms.
- **Reservation Validation:** Implement validation in the `Reserva` model and forms to prevent overlapping reservations for the same room.
- **Room Availability Check:** Improve the dashboard to allow filtering rooms by specific dates/times, not just "now".

## Configuration
- **Localization:** Update `LANGUAGE_CODE` in `settings.py` to `pt-br` to match the application's language (Portuguese).

## Testing
- **Edge Case Testing:** Add tests for overlapping reservations and invalid time ranges.

## API
- **REST API:** Implement a REST API (using Django REST Framework) to expose rooms and reservations to other clients.
