import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.forms import FileField, ClearableFileInput, CheckboxInput, inlineformset_factory, modelformset_factory, \
    formset_factory
from scap.models import NewCollection, TiffFile


class NewCollectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewCollectionForm, self).__init__(*args, **kwargs)



    #
    # tiff_file = forms.FileField(widget = forms.TextInput(attrs={
    #         "name": "tiff_files",
    #         "type": "File",
    #         "class": "form-control",
    #         "multiple": "True",
    #     }), label = "")
    class Meta:
        model = NewCollection
        fields = ['collection_name', 'collection_description', 'boundary_file', 'access_level'
                  , 'resolution']
        ACCESS_CHOICES = (
            ('Public', 'Public'),  # First one is the value of select option and second is the displayed value in option
            ('Private', 'Private'),
        )
        widgets = {
            'collection_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a name for the collection'}),
            'collection_description': forms.Textarea(attrs={'class': 'form-control','placeholder': 'Enter the details about the collection'}),
            'boundary_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/zip'}),
            'access_level': forms.Select(choices=ACCESS_CHOICES, attrs={'class': 'form-control'}),
            'resolution': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Resolution in meters'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Collection Name'}),
            'last_accessed_on': forms.DateTimeInput(attrs={'class': 'form-control'})
        }


class TiffFileForm(forms.ModelForm):
    class Meta:
        model = TiffFile
        fields = ['file','year']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/tiff'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2000'}),
        }


TiffFileFormSet=inlineformset_factory(NewCollection, TiffFile,
                                            form=TiffFileForm, extra=3,can_delete = False)

