from django import forms

from .models import Incident, IncidentComment


class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ("title", "category", "description", "incident_date")
        widgets = {
            "incident_date": forms.DateInput(attrs={"type": "date"}),
        }


class IncidentCommentForm(forms.ModelForm):
    class Meta:
        model = IncidentComment
        fields = ("comment",)
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Write your comment"}),
        }


class IncidentPublicReportForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ("title", "category", "description", "incident_date", "reporter_email")
        widgets = {
            "incident_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 6}),
        }
        labels = {
            "reporter_email": "Email for status updates",
        }
        help_texts = {
            "reporter_email": "Used only for status update notifications.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reporter_email"].required = True
