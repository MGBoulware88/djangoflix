from django import forms


TYPE = {
    "movie": "Movie",
    "series": "TV Series",
    "season": "TV Season",
}


class FetchForm(forms.Form):
    id = forms.CharField(min_length=1, max_length=7)
    type = forms.ChoiceField(choices=TYPE)
    season = forms.IntegerField(
        required=False,
        help_text="Only enter a value if type is \"TV Season\""
    )


class UploadForm(forms.Form):
    type = forms.ChoiceField(choices=TYPE)
    file = forms.FileField()