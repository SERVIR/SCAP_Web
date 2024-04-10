from django import forms
from django.core.exceptions import ValidationError

from scap.models import ForestCoverCollection, AOICollection, AGBCollection


class ForestCoverCollectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ForestCoverCollectionForm, self).__init__(*args, **kwargs)
    class Meta:
        model = ForestCoverCollection
        fields = ['name', 'description', 'doi_link', 'metadata_link', 'boundary_file', 'access_level', 'owner']

        ACCESS_CHOICES = ForestCoverCollection.ACCESS_CHOICES

        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter a name for the collection'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control',
                       'placeholder': 'Enter the collection information (source, projections, post-processing)'}),
            'boundary_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/zip'}),
            'access_level': forms.Select(choices=ACCESS_CHOICES, attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Collection Name'}),
            'last_accessed_on': forms.DateTimeInput(attrs={'class': 'form-control'}),
            'doi_link': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a DOI URL'}),
            'metadata_link': forms.URLInput(attrs={'class': 'form-control','placeholder':'Enter a Metadata URL'})
        }


class AOICollectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AOICollectionForm, self).__init__(*args, **kwargs)


    class Meta:
        model = AOICollection
        fields = ['name', 'description', 'doi_link', 'metadata_link', 'source_file','access_level', 'owner']
        ACCESS_CHOICES = AOICollection.ACCESS_CHOICES
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter a name for the AOI'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Enter the details about the AOI'}),
            'source_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/zip'}),
            'doi_link': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a DOI URL'}),
            'metadata_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter a Metadata URL'}),
            'access_level': forms.Select(choices=ACCESS_CHOICES, attrs={'class': 'form-control'})
        }


class AGBCollectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AGBCollectionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = AGBCollection
        fields = ['name', 'description', 'doi_link', 'metadata_link', 'boundary_file',
                  'source_file', 'access_level', 'owner', 'year']
        ACCESS_CHOICES =AGBCollection.ACCESS_CHOICES

        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter a name for the AGB'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Enter details about the AGB'}),
            'boundary_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/zip'}),
            'source_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/tiff'}),
            'doi_link': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a DOI URL'}),
            'metadata_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter a Metadata URL'}),
            'access_level': forms.Select(choices=ACCESS_CHOICES, attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2000'})
        }
