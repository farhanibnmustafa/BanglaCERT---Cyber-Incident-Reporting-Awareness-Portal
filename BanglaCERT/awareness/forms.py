from django import forms

from .models import AwarenessComment


class AwarenessCommentForm(forms.ModelForm):
    class Meta:
        model = AwarenessComment
        fields = ("comment",)
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Write your comment"}),
        }
