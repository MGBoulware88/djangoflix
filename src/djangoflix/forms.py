from django import forms
from django.core.exceptions import ValidationError

from tmdb.models import Genre


GENRES = {genre.id: genre.name \
          for genre in Genre.objects.all().order_by("name")}


class SearchForm(forms.Form):
    title_search = forms.CharField(
        min_length=1, 
        max_length=255,
        # help_text="Search by Title",
        required=False
    )
    genre_filter = forms.MultipleChoiceField(
        choices=GENRES,
        # help_text="Filter by Genre",
        widget=forms.CheckboxSelectMultiple(choices=GENRES),
        required=False
    )

    # Overriding clean so that a 'valid' form 
    # of empty fields will raise ValidationError
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data["title_search"] \
        and not cleaned_data["genre_filter"]:
            raise ValidationError("No search terms entered", code="blank")
