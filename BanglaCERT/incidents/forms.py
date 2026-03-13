from django import forms

from .models import Incident


class IncidentPublicReportForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ("title", "category", "description", "incident_date", "reporter_email", "is_anonymous")
        widgets = {
            "incident_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 6}),
        }
        labels = {
            "reporter_email": "Email for status updates",
            "is_anonymous": "Submit this report anonymously",
        }
        help_texts = {
            "reporter_email": "Used only for status update notifications.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_anonymous"].initial = True
        self.fields["reporter_email"].required = True
