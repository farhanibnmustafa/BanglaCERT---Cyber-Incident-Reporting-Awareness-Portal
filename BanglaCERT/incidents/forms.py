from django import forms
from .models import Incident

class IncidentReportForm(forms.ModelForm):

    report_anonymously = forms.BooleanField(
        required=False,
        label="Report Anonymously"
    )

    class Meta:
        model = Incident
        fields = [
            "title",
            "description",
            "category",
            "incident_date"
        ]