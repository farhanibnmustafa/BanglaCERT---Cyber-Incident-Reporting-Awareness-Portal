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
