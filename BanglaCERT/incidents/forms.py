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


class IncidentStaffFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Search title, description, reporter"}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All statuses"), *Incident.STATUS_CHOICES],
    )
    category = forms.ChoiceField(
        required=False,
        choices=[("", "All categories"), *Incident.CATEGORY_CHOICES],
    )


class IncidentStaffStatusForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ("status",)


class IncidentStaffCommentForm(forms.ModelForm):
    class Meta:
        model = IncidentComment
        fields = ("comment",)
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Add an internal staff note"}),
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
