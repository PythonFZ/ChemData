from django import forms
from .models import Chemical, Stock, Extraction


class ChemicalCreateForm(forms.ModelForm):

    class Meta:
        model = Chemical
        fields = ('name', 'structure', 'molar_mass', 'density', 'melting_point', 'boiling_point', 'comment')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Ethanol'}),
            'structure': forms.TextInput(attrs={'placeholder': 'e.g. CH3OH'}),
            'comment': forms.Textarea(attrs={'rows': 4})
        }

        html_script = '<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>' + \
                      '<script id="MathJax-script" async ' + \
                      'src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script> '

        labels = {
            'density': html_script + 'Density in \(\mathrm{g} \cdot \mathrm{cm}^{-3}\)',
            'melting_point': 'Melting Point in °C',
            'boiling_point': 'Boiling Point in °C',
            'molar_mass': html_script + 'Molar Mass in \(\mathrm{g}\cdot\mathrm{mol}^{-1}\)'
        }


class StockUpdateForm(forms.ModelForm):

    class Meta:
        model = Stock
        fields = ('name', 'quantity', 'unit', 'chemical')


class ExtractionCreateForm(forms.ModelForm):
    anonymous = forms.BooleanField(required=False, label='stay anonymous')

    class Meta:
        model = Extraction
        fields = ('quantity', 'comment', 'date_created', 'unit')

        widgets = {
            'anonymous': forms.CheckboxInput()
        }

# name = models.CharField(max_length=250)
#     structure = models.CharField(max_length=250, blank=True)
#     molar_mass = models.FloatField(blank=True, null=True)
#     density = models.FloatField(blank=True, null=True)
#     melting_point = models.FloatField(blank=True, null=True)
#     boiling_point = models.FloatField(blank=True, null=True)
#
#     comment = models.TextField(blank=True)
#     cid = models.CharField(max_length=100, blank=True, null=True)
#     cas = models.CharField(max_length=100, blank=True, null=True)