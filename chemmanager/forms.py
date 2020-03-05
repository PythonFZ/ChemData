from django import forms
from .models import Chemical, Stock, Extraction, Storage


class ChemicalCreateForm(forms.ModelForm):

    class Meta:
        model = Chemical
        fields = ('name', 'structure', 'molar_mass', 'density', 'melting_point', 'boiling_point', 'comment', 'image', 'cid', 'secret')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Ethanol'}),
            'structure': forms.TextInput(attrs={'placeholder': 'e.g. CH3OH'}),
            'comment': forms.Textarea(attrs={'rows': 4}),
            'secret': forms.CheckboxInput(),
            'cid': forms.HiddenInput()
        }

        html_script = '<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>' + \
                      '<script id="MathJax-script" async ' + \
                      'src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script> '

        labels = {
            'density': html_script + 'Density in \(\mathrm{g} \cdot \mathrm{cm}^{-3}\)',
            'melting_point': 'Melting Point in °C',
            'boiling_point': 'Boiling Point in °C',
            'molar_mass': html_script + 'Molar Mass in \(\mathrm{g}\cdot\mathrm{mol}^{-1}\)',
            'image': 'Image (leave empty for default pubchem img search)',
        }


class StockUpdateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super(StockUpdateForm, self).__init__(*args, **kwargs)
        self.fields['storage'].queryset = Storage.objects.filter(workgroup=request.user.profile.workgroup).distinct()

    class Meta:
        model = Stock
        fields = ('name', 'quantity', 'unit', 'comment', 'storage')


class ExtractionCreateForm(forms.ModelForm):
    anonymous = forms.BooleanField(required=False, label='stay anonymous')

    class Meta:

        model = Extraction
        fields = ('quantity', 'unit', 'comment', 'date_created')

        widgets = {
            'anonymous': forms.CheckboxInput(),
            'comment': forms.Textarea(attrs={'rows': 4})
        }
