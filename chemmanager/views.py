from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Count
from dal import autocomplete
from .models import Chemical, Stock, Extraction, Storage, Distributor, Workgroup, ChemicalList, ChemicalSynonym, Unit, Post
from .forms import ChemicalCreateForm, StockUpdateForm, ExtractionCreateForm, StorageCreateForm, SearchParameterForm, \
    ChemicalListUploadForm, ChemicalListVerifyForm
from .utils import PubChemLoader, unit_converter, update_chemical_synonyms
from braces import views
from django.shortcuts import redirect
import pandas as pd
from django.shortcuts import render

def about(request):
    return render(request, 'chemmanager/about.html', {'title': 'About'})

def blog(request):
    return render(request, 'chemmanager/blog_home.html')

class PostListView(ListView):
    model = Post
    template_name = 'chemmanager/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']


class ChemicalDetailView(LoginRequiredMixin, DetailView):
    # TODO user passes test!
    model = Chemical


class SearchParameterAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        parameter_list = ['only stocked']
        for my_storage in Storage.objects.filter(shared_workgroups=self.request.user.profile.workgroup).all():
            parameter_list.append(my_storage.workgroup.name)
        return list(set(parameter_list))


class DistributorAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Distributor.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class StockCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Stock
    form_class = StockUpdateForm

    def get_form_kwargs(self):
        """Pass Request for filtering storage drop-down"""
        kwargs = super(StockCreateView, self).get_form_kwargs()
        kwargs.update({
            'request': self.request,
        })
        return kwargs

    def form_valid(self, form):
        chemical_id = self.request.GET.get('chemical')
        form.instance.chemical = Chemical.objects.get(pk=chemical_id)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(StockCreateView, self).get_context_data(**kwargs)
        chemical_id = self.request.GET.get('chemical')
        context['chemical'] = Chemical.objects.get(pk=chemical_id).name

        return context

    def test_func(self):
        """Only Workgroup-Members are allowed to edit, Shared Groups are only permitted to create extractions!
        Otherwise Members of different Groups could change storage, which is not allowed"""
        if Chemical.objects.filter(id=self.request.GET.get('chemical'),
                                   workgroup=self.request.user.profile.workgroup).count() > 0:
            return True
        else:
            return False

    def handle_no_permission(self):
        messages.add_message(self.request, messages.WARNING, 'You are not permitted to apply changes! '
                                                             'Please contact your group admin.')
        return HttpResponseRedirect(reverse_lazy('chemmanager-home'))


class ChemicalListView(views.JSONResponseMixin, views.AjaxResponseMixin, LoginRequiredMixin, ListView):
    # TODO user passes test!
    # TODO Search-parameter should not be reset on page reload!
    model = Chemical

    template_name = 'chemmanager/chemdata_home.html'
    context_object_name = 'chemicals'
    paginate_by = 50
    extra_context = {
        'title': 'Chemical Manager',
        'chemical_detail': None,
    }

    def get_queryset(self):
        object_list = Chemical.objects.filter(workgroup=self.request.user.profile.workgroup)

        parameter = self.request.GET.getlist('p')
        # TODO add extra parameters
        # Check Workgroups:

        extra_parameter = {}

        if 'only stocked' in parameter:
            parameter.remove('only stocked')
            extra_parameter['only_stocked'] = True

        for param in parameter:
            curr_workgroup = Workgroup.objects.get(name=param)
            # Iterate through all search parameter, check if Storage is shared with current users workgroup!
            object_list = object_list | Chemical.objects.filter(
                stock__storage__shared_workgroups=self.request.user.profile.workgroup,
                workgroup=curr_workgroup).exclude(secret=True)

        if extra_parameter.get('only_stocked'):
            object_list = object_list.annotate(count_st=Count('stock')).filter(count_st__gt=0)

        query = self.request.GET.get('q')
        if query:
            object_list = object_list.filter(name__icontains=query) | object_list.filter(
                cas__startswith=query) | object_list.filter(chemicalsynonym__name__icontains=query)

        # Sort by most available / largest stock count and than by name!
        # object_list = object_list.annotate(count=Count('stock__id')).order_by('-count', 'name').distinct()
        object_list = object_list.order_by('name').distinct()
        return object_list

    def get_context_data(self, **kwargs):
        parameter_form = SearchParameterForm()
        kwargs.update({
            'parameter_form': parameter_form,
        })
        return super(ChemicalListView, self).get_context_data(**kwargs)

    def get_ajax(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        name_list = []
        for query_object in queryset.all():
            name_list.append(query_object.name)
        response = {'names': name_list}
        return self.render_json_response(response)

    # paginate_by = 6


class ChemicalTableView(ChemicalListView):
    model = Chemical

    template_name = 'chemmanager/chemicaltable_list.html'
    context_object_name = 'chemicals'
    paginate_by = 100000


class ChemicalCreateView(CreateView):
    model = Chemical
    form_class = ChemicalCreateForm
    extra_context = {
        'title': 'Add'
    }
    chemical_name = None

    # def get_form_kwargs(self):
    #     kwargs = super(ChemicalCreateView, self).get_form_kwargs()
    #     kwargs.update({
    #         'request': self.request,
    #     })
    #     return kwargs

    def form_valid(self, form, **kwargs):
        """Load Data from PubChem if button is pressed"""
        # TODO add Image download
        context = self.get_context_data(**kwargs)
        if 'check_pubchem' in self.request.POST:
            pubchemloader = PubChemLoader(chemical_name=form.cleaned_data.get('name'))
            if pubchemloader.compound is not None:
                initial_dict = pubchemloader.generate_initial(initial_dict=form.cleaned_data)
                context['form'] = ChemicalCreateForm(initial=initial_dict)
                return self.render_to_response(context)
            else:
                messages.add_message(self.request, messages.WARNING,
                                     f'Could not find Substance on PubChem!')
                return self.render_to_response(context)
        else:
            if Chemical.objects.filter(name=form.cleaned_data.get('name'),
                                       workgroup=self.request.user.profile.workgroup).count() > 0:
                messages.add_message(self.request, messages.WARNING,
                                     f'Chemical already created for Group {self.request.user.profile.workgroup}!')
                return self.render_to_response(context)
            # Check if CID has been generated, that means always, that an Image should be available!
            # if (form.data.get('image') == '') and (form.data.get('cid') is not None):
            #     form.instance.image = f'/chemical_pics/{form.data.get("cid")}.png'
            form.instance.creator = self.request.user
            form.instance.workgroup = self.request.user.profile.workgroup

            chemical = form.save()
            # Need to overwrite super to get instance of chemical for synonyms and later for stock!
            # TODO Write Stock creation after chemical creation here
            update_chemical_synonyms(chemical=chemical,
                                     synonyms=form.cleaned_data.get('synonyms').splitlines())

            return HttpResponseRedirect(
                reverse_lazy('chemical-list', kwargs={'pk': chemical.id}) + f'?q={chemical.name}')
            # return super().form_valid(form, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add Chemical Name from Search to create Chemical faster.
        form['name'].initial = self.kwargs.get('chemical_name')
        return form


class ChemicalUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Chemical
    form_class = ChemicalCreateForm
    extra_context = {
        'title': 'Update',
        'delete': True,
    }

    def form_valid(self, form, **kwargs):
        """
        Check if Chemical is renamed to a Chemical, that already exists.
        Call PubChemLoader for getting Data.
        """
        form.instance.creator = self.request.user
        chemical = self.get_object()

        context = self.get_context_data(**kwargs)
        if 'check_pubchem' in self.request.POST:
            pubchemloader = PubChemLoader(chemical_name=form.cleaned_data.get('name'))
            if pubchemloader.compound is not None:
                initial_dict = pubchemloader.generate_initial(initial_dict=form.cleaned_data)
                context['form'] = ChemicalCreateForm(initial=initial_dict)
                return self.render_to_response(context)
            else:
                messages.add_message(self.request, messages.WARNING,
                                     f'Could not find Substance on PubChem!')
                return self.render_to_response(context)
        else:
            if (form.cleaned_data.get('name') != chemical.name) and \
                    (Chemical.objects.filter(name=form.cleaned_data.get('name'),
                                             workgroup=self.request.user.profile.workgroup).count() > 0):
                messages.add_message(self.request, messages.WARNING,
                                     f'Chemical already created for Group {self.request.user.profile.workgroup}!')
                return self.render_to_response(context)

            update_chemical_synonyms(chemical=chemical,
                                     synonyms=form.cleaned_data.get('synonyms').splitlines())

            return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        chemical = self.get_object()
        # Show synonyms per line in TextArea
        synonyms = ''
        for synonym in chemical.chemicalsynonym_set.all():
            synonyms += synonym.name + '\n'
        form['synonyms'].initial = synonyms

        return form

    def test_func(self):
        chemical = self.get_object()
        if self.request.user == chemical.creator:
            return True
        else:
            return False

    def handle_no_permission(self):
        messages.add_message(self.request, messages.WARNING, 'You are not permitted to apply changes! '
                                                             'Please contact your group admin.')
        return HttpResponseRedirect(reverse_lazy('chemmanager-home'))


class ChemicalDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Chemical
    success_url = reverse_lazy('chemmanager-home')

    def delete(self, request, *args, **kwargs):
        chemical = self.get_object()
        if chemical.stock_set.count() > 0:
            messages.add_message(self.request, messages.WARNING, 'Can not delete Chemical with existing stock!')
            return HttpResponseRedirect(reverse_lazy('chemical-update', kwargs={'pk': chemical.pk}))
        if self.request.user == chemical.creator:
            messages.add_message(self.request, messages.INFO, f'{chemical.name} successfully removed!')
            return super().delete(request, *args, **kwargs)

    def test_func(self):
        chemical = self.get_object()
        if self.request.user == chemical.creator:
            return True
        else:
            return False

    def handle_no_permission(self):
        messages.add_message(self.request, messages.WARNING, 'You are not permitted to apply changes! '
                                                             'Please contact your group admin.')
        return HttpResponseRedirect(reverse_lazy('chemmanager-home'))


class StockDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Stock
    success_url = reverse_lazy('chemmanager-home')

    def delete(self, request, *args, **kwargs):
        stock = self.get_object()
        messages.add_message(self.request, messages.INFO, f'Stock for {stock.chemical.name} successfully removed!')
        return super().delete(request, *args, **kwargs)

    def test_func(self):
        """Check if User is in group and allowed to remove Stock"""
        stock = self.get_object()
        if self.request.user.profile.workgroup == stock.storage.workgroup:
            return True
        else:
            return False

    def handle_no_permission(self):
        messages.add_message(self.request, messages.WARNING, 'You are not permitted to apply changes! '
                                                             'Please contact your group admin.')
        return HttpResponseRedirect(reverse_lazy('chemmanager-home'))


class StockUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Stock
    form_class = StockUpdateForm

    def get_form_kwargs(self):
        kwargs = super(StockUpdateView, self).get_form_kwargs()
        kwargs.update({
            'request': self.request,
        })
        return kwargs

    def test_func(self):
        """Only Workgroup-Members are allowed to edit, Shared Groups are only permited to create extractions!
        Otherwise Members of different Groups could change storage, which is not allowed"""
        stock = self.get_object()
        if self.request.user.profile.workgroup == stock.chemical.workgroup:
            return True
        else:
            return False

    def handle_no_permission(self):
        messages.add_message(self.request, messages.WARNING, 'You are not permitted to apply changes! '
                                                             'Please contact your group admin.')
        return HttpResponseRedirect(reverse_lazy('chemmanager-home'))


class ExtractionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Extraction
    form_class = ExtractionCreateForm

    def get_form(self, form_class=None):
        """Get unit from the associated stock"""
        form = super().get_form(form_class)
        form['unit'].initial = Stock.objects.get(id=self.kwargs['pk']).unit
        return form

    def get_context_data(self, **kwargs):
        stock = Stock.objects.get(id=self.kwargs['pk'])
        extractions = stock.extraction_set.all()
        # TODO Use units!
        left_quantity = stock.quantity
        for extraction in extractions:
            left_quantity -= unit_converter(extraction.quantity, extraction.unit, stock)
        kwargs.update({
            'stock': stock,
            'left_quantity': left_quantity,
        })
        return super(ExtractionCreateView, self).get_context_data(**kwargs)

    def form_valid(self, form, **kwargs):
        if self.request.POST.get('anonymous'):
            form.instance.user = None
        else:
            form.instance.user = self.request.user
        stock = Stock.objects.get(id=self.kwargs['pk'])
        form.instance.stock = stock
        if unit_converter(form.cleaned_data.get('quantity'), form.cleaned_data.get('unit'), stock):
            if (stock.left_quantity - unit_converter(form.cleaned_data.get('quantity'), form.cleaned_data.get('unit'),
                                                     stock)) <= 0:
                path = reverse('stock-delete', args=[stock.id])
                messages.add_message(self.request, messages.WARNING,
                                     f'<div class="d-flex justify-content-between align-items-center"> <div>Stock for <b>{stock.chemical.name}</b> seems to be empty.</div> <a class="btn btn-outline-danger" href="{path}">Remove Stock!</a> </div>',
                                     extra_tags='safe')

            return super().form_valid(form)
        else:
            context = self.get_context_data(**kwargs)
            messages.add_message(self.request, messages.WARNING,
                                 f'Unit not supported!')
            return self.render_to_response(context)

    def test_func(self):
        """Check if User is in group and allowed to add Extraction
        Allow if stock_storage_workgroup is in workgroup of the user or if stock has no workgroup.
        Permit if Chemical is set to secret!
        """
        my_stock = Stock.objects.get(pk=self.kwargs['pk'])
        if my_stock.storage.shared_workgroups.filter(storage__shared_workgroups=self.request.user.profile.workgroup) or \
                my_stock.chemical.workgroup == self.request.user.profile.workgroup:
            if my_stock.chemical.secret and my_stock.chemical.workgroup != self.request.user.profile.workgroup:
                return False
            return True

        else:
            return False

    def handle_no_permission(self):
        messages.add_message(self.request, messages.WARNING, 'You are not permitted to apply changes! '
                                                             'Please contact your group admin.')
        return HttpResponseRedirect(reverse_lazy('chemmanager-home'))


class StorageListView(LoginRequiredMixin, ListView):
    # TODO child storage has to have the same workgroup as parent!
    model = Storage

    def get_queryset(self):
        # object_list = self.model.objects.filter(workgroup=self.request.user.profile.workgroup)
        object_list = self.model.objects.filter(workgroup=self.request.user.profile.workgroup)

        return object_list.order_by('name').distinct()


class StorageCreateView(LoginRequiredMixin, CreateView):
    # TODO UserPassesTest!
    model = Storage
    form_class = StorageCreateForm
    success_url = reverse_lazy('storage-list')

    def form_valid(self, form):
        # print(form.cleaned_data)
        if self.kwargs['pk'] == 0:  # If not child create root
            set_storage = Storage.add_root(name=form.instance.name, room=form.instance.room, creator=self.request.user,
                                           abbreviation=form.instance.abbreviation,
                                           workgroup=self.request.user.profile.workgroup)
            workgroups = form.cleaned_data.get('shared_workgroups')
        else:  # Create Child!
            root_storage = Storage.objects.get(id=self.kwargs['pk'])
            set_storage = root_storage.add_child(name=form.instance.name, room=form.instance.room,
                                                 creator=self.request.user, abbreviation=form.instance.abbreviation,
                                                 workgroup=self.request.user.profile.workgroup)
            workgroups = root_storage.shared_workgroups.all()
        for group in workgroups:
            set_storage.shared_workgroups.add(group)

        return HttpResponseRedirect(self.success_url)

    def get_form(self, form_class=None):
        """Make Workgroup selection only visible, if 1. Level Storage"""
        # TODO do not show Workgroup or make it disabled if substorage
        form = super().get_form(form_class)
        # Removing owner workgroup from list
        form.fields['shared_workgroups'].queryset = Workgroup.objects.exclude(pk=self.request.user.profile.workgroup_id)
        if self.kwargs['pk'] != 0:  # Look for root storage (editing child storage here!)
            root_storage = Storage.objects.get(id=self.kwargs['pk'])
            form.fields['shared_workgroups'].initial = root_storage.shared_workgroups.all()
            form.fields['room'].initial = root_storage.room

        return form

    def get_context_data(self, **kwargs):
        if self.kwargs['pk'] != 0:
            root_storage = Storage.objects.get(id=self.kwargs['pk'])
            kwargs.update({
                'root_storage': root_storage,
            })
        return super(StorageCreateView, self).get_context_data(**kwargs)


class StorageUpdateView(UpdateView):
    model = Storage
    form_class = StorageCreateForm
    success_url = reverse_lazy('storage-list')


class StorageDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Storage
    success_url = reverse_lazy('storage-list')

    def test_func(self):
        """Check if User is in group and allowed to remove Stock"""
        storage = self.get_object()
        if storage.creator == self.request.user:
            return True
        else:
            return False

    def handle_no_permission(self):
        messages.add_message(self.request, messages.WARNING, 'You are not permitted to apply changes! '
                                                             'Please contact your group admin.')
        return HttpResponseRedirect(reverse_lazy('storage-list'))


class ChemicalListUploadView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Uploads chemical-list and checks if it's csv"""
    model = ChemicalList
    success_url = reverse_lazy('chemmanager-home')
    form_class = ChemicalListUploadForm

    def test_func(self):
        return True

    def form_valid(self, form, **kwargs):
        if str(form.instance.file).endswith('.csv'):
            form.instance.workgroup = self.request.user.profile.workgroup
            object = form.save()
            return redirect('chemicallist-verify', object.id)
            # return super().form_valid(form)
        else:
            messages.add_message(self.request, messages.WARNING, 'This is not a csv file!')
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)


class ChemicalListVerifyView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'chemmanager/chemicallist_list.html'
    model = ChemicalList

    def test_func(self):
        return True

    def get_context_data(self, **kwargs):
        '''gets data from uploaded csv-file and prints out its data'''
        context = super().get_context_data(**kwargs)
        my_chemicallist = ChemicalList.objects.get(id=self.kwargs['pk'])

        frame = pd.read_csv(my_chemicallist.file.path, engine='python', sep=None)
        context['frame'] = frame.to_dict('split')
        context['form'] = ChemicalListVerifyForm(columns=frame.columns)
        return context

    def post(self, request, *args, **kwargs):
        """Saves into database
        """
        # request.POST dictionary of chosen data (e.g. '0':'Storage')
        col_dict = {}
        for k, v in request.POST.items():
            try:
                col_dict[v] = int(k)
            except ValueError:
                pass

        missing_fields = []
        for element in Stock.get_required_fields():
            if element not in col_dict:
                missing_fields.append(element)

        if len(missing_fields) > 0:
            messages.add_message(self.request, messages.WARNING, f'Add all required data! * missing {missing_fields} ')
            # TODO keep forms filled
            return self.get(request, args, kwargs)

        my_chemicallist = ChemicalList.objects.get(id=self.kwargs['pk'])
        frame = pd.read_csv(my_chemicallist.file.path, engine='python', sep=None)
        # col_dict = {v: int(k) for k, v in request.POST.items()} #inverts e.g. 1: chemical -> chemical: 1

        for index, row in frame.iterrows():
            # print('---------------------')
            # print(row)
            # print(col_dict)
            # print('---------------------')
            chemical, created = Chemical.objects.get_or_create(name=row[col_dict.get('chemical')],
                                                               defaults={'creator': self.request.user,
                                                                         'workgroup': self.request.user.profile.workgroup})
            # if not created:
            # try:
            #     stock = Stock.objects.get(chemical=chemical, label=row[col_dict.get('label')])
            #     # TODO WHY?
            # except (Stock.DoesNotExist, KeyError):
            stock = Stock(chemical=chemical)
            if 'quantity' in col_dict:
                # try:
                #     stock.quantity = float(row[col_dict.get('quantity')].replace("[^0-9]", ""))
                # except ValueError:
                stock.quantity = -1
                # stock.quantity = 1  # TODO convert quantity to float

            if 'unit' in col_dict:
                try:
                    stock.unit = Unit.objects.get(name=row[col_dict.get('unit')])
                except Unit.DoesNotExist:
                    stock.unit = Unit.objects.get(name='None')
            else:
                stock.unit = Unit.objects.get(name='None')

            if 'label' in col_dict:
                stock.label = row[col_dict.get('label')]

            if 'storage' in col_dict:
                try:
                    stock.storage = Storage.objects.get(name=row[col_dict.get('storage')])
                except Storage.DoesNotExist:
                    stock.storage = Storage.add_root(name=row[col_dict.get('storage')], creator=self.request.user,
                                                     workgroup=self.request.user.profile.workgroup)
            else:
                # When no storage is selected, then everything will be stored in a (new) "default" storage
                try:
                    stock.storage = Storage.objects.get(name='default')
                except Storage.DoesNotExist:
                    stock.storage = Storage.add_root(name='default', creator=self.request.user,
                                                     workgroup=self.request.user.profile.workgroup)

            stock.save()

        return self.get(request, *args, **kwargs)
