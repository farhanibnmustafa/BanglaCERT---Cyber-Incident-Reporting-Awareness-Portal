from django import forms

from incidents.models import Incident


class PublicIncidentSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Keywords",
        widget=forms.TextInput(attrs={"placeholder": "Search by title or description"}),
    )
    category = forms.ChoiceField(
        required=False,
        choices=[("", "All categories"), *Incident.CATEGORY_CHOICES],
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Date from",
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Date to",
    )
