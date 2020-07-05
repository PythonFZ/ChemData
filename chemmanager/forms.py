from django import forms
from dal import autocomplete
from .models import Chemical, Stock, Extraction, Storage, ChemicalList


class SearchParameterForm(forms.Form):
    p = forms.MultipleChoiceField(
        widget=autocomplete.Select2Multiple(url='search-parameter-autocomplete'),
        label='Search Parameter',
        required=False,
    )


class StorageCreateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(StorageCreateForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Storage
        fields = ('name', 'room', 'shared_workgroups', 'abbreviation')


class ChemicalCreateForm(forms.ModelForm):
    class Meta:
        model = Chemical
        fields = ('name', 'structure', 'molar_mass', 'density', 'melting_point', 'boiling_point',
                  'comment', 'cas', 'image', 'secret', 'cid')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Ethanol'}),
            'structure': forms.TextInput(attrs={'placeholder': 'e.g. CH3OH'}),
            'molar_mass': forms.TextInput(),
            'comment': forms.Textarea(attrs={'rows': 4}),
            'secret': forms.CheckboxInput(),
            'cid': forms.HiddenInput(),
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
            'cas': 'CAS',
        }


class StockUpdateForm(forms.ModelForm):
    # distributor = forms.ModelChoiceField(
    #     queryset=Distributor.objects.all(),
    #     widget=autocomplete.ModelSelect2(url='distributor-autocomplete')
    # )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super(StockUpdateForm, self).__init__(*args, **kwargs)
        self.fields['storage'].queryset = Storage.objects.filter(owner_workgroup__exact=request.user.profile.workgroup)

    class Meta:
        model = Stock
        fields = ('distributor', 'quantity', 'unit', 'purity', 'comment', 'storage', 'label')
        widgets = {
            # 'distributor': forms.TextInput(attrs={'placeholder': 'e.g. Sigma Aldrich'}),
            'distributor': autocomplete.ModelSelect2(
                url='distributor-autocomplete',
                attrs={'data-placeholder': 'e.g. Sigma Aldrich'}),
        }


class ExtractionCreateForm(forms.ModelForm):
    anonymous = forms.BooleanField(required=False, label='stay anonymous')

    class Meta:
        model = Extraction
        fields = ('quantity', 'unit', 'comment', 'date_created')
        # TODO Placeholder!
        widgets = {
            'anonymous': forms.CheckboxInput(),
            'comment': forms.Textarea(attrs={'rows': 4}),
            'label': forms.TextInput(attrs={'placeholder': 'Name'}),
        }


class ChemicalListUploadForm(forms.ModelForm):
    class Meta:
        model = ChemicalList
        fields = ('file',)


class ChemicalListVerifyForm(forms.Form):

    def __init__(self, *args, **kwargs):
        columns = kwargs.pop('columns')
        super(ChemicalListVerifyForm, self).__init__(*args, **kwargs)
        # choices = [(f.name, f.name) for f in Stock._meta.get_fields()]
        # choices.append(('--', 'empty'))
        required_fields = [f.name for f in Stock._meta.get_fields() if not getattr(f, 'blank', False) is True]

        choices = [('', '--')] + [(f.name, f.name) for f in Stock._meta.get_fields()]
        choices = [x for x in choices if x not in (('id', 'id'), ('softdeletemodel_ptr', 'softdeletemodel_ptr'))]

        choices = [f if f[1] not in required_fields else (f[0], f[1]+'*') for f in choices]
        #makes new list without id, softdelete_pzt etc.
        #TODO filter choices (no id), capitalize,default option
        #TODO Required choices marked with 'star'
        #creates list from Stock names, similiar to: for f in Stock.__... : choices.append((f.name, f.name))
        for i, label in enumerate(columns):

            self.fields[i] = forms.ChoiceField(label=label, choices=choices, required=False)


