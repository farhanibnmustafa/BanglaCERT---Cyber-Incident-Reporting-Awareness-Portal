from django import forms

from .models import Incident, IncidentComment


class IncidentReportForm(forms.ModelForm):
    def __init__(self, *args, require_reporter_email=False, anonymous_default=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reporter_email"].required = require_reporter_email
        self.fields["is_anonymous"].initial = anonymous_default

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


class IncidentCommentForm(forms.ModelForm):
    class Meta:
        model = IncidentComment
        fields = ("comment",)
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Write your comment"}),
        }
