from django import forms
from scap.models import ForestCoverCollection, AOICollection, AGBCollection


class ForestCoverCollectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ForestCoverCollectionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = ForestCoverCollection
        fields = ['collection_name', 'collection_description', 'doi_link', 'metadata_link', 'boundary_file',
                  'access_level'
                  ]
        ACCESS_CHOICES = (
            ('Select', 'Select'),
            ('Public', 'Public'),  # First one is the value of select option and second is the displayed value in option
            ('Private', 'Private'),
        )
        widgets = {
            'collection_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter a name for the collection'}),
            'collection_description': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Enter the details about the collection'}),
            'boundary_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/zip'}),
            'access_level': forms.Select(choices=ACCESS_CHOICES, attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Collection Name'}),
            'last_accessed_on': forms.DateTimeInput(attrs={'class': 'form-control'}),
            'doi_link': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
            'metadata_link': forms.URLInput(attrs={'class': 'form-control'})
        }


# class TiffFileForm(forms.ModelForm):
#     class Meta:
#         model = TiffFile
#         fields = ['file','year','doi_link','metadata_link']
#         widgets = {
#             'file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/tiff'}),
#             'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2000'}),
#             'doi_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': ''}),
#             'metadata_link': forms.URLInput(attrs={'class': 'form-control'})
#         }
#

# TiffFileFormSet=inlineformset_factory(NewCollection, TiffFile,
#                                             form=TiffFileForm, extra=1,can_delete = False)


class AOICollectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AOICollectionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = AOICollection
        fields = ['aoi_name', 'aoi_description', 'doi_link', 'metadata_link', 'aoi_shape_file','access_level']
        ACCESS_CHOICES = (
            ('Select', 'Select'),
            ('Public', 'Public'),  # First one is the value of select option and second is the displayed value in option
            ('Private', 'Private'),
        )
        widgets = {
            'aoi_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter a name for the AOI'}),
            'aoi_description': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Enter the details about the AOI'}),
            'aoi_shape_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/zip'}),
            'doi_link': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
            'metadata_link': forms.URLInput(attrs={'class': 'form-control'}),
            'access_level': forms.Select(choices=ACCESS_CHOICES, attrs={'class': 'form-control'}),

        }


class AGBCollectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AGBCollectionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = AGBCollection
        fields = ['agb_name', 'agb_description', 'doi_link', 'metadata_link','agb_boundary_file','agb_tiff_file','access_level']
        ACCESS_CHOICES = (
            ('Select', 'Select'),
            ('Public', 'Public'),  # First one is the value of select option and second is the displayed value in option
            ('Private', 'Private'),
        )
        widgets = {
            'agb_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter a name for the AGB'}),
            'agb_description': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Enter the details about the AGB'}),
            'agb_boundary_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/zip'}),
            'agb_tiff_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/tiff'}),
            'doi_link': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
            'metadata_link': forms.URLInput(attrs={'class': 'form-control'}),
            'access_level': forms.Select(choices=ACCESS_CHOICES, attrs={'class': 'form-control'}),

        }
