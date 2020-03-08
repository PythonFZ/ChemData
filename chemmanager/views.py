from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Count
from .models import Chemical, Stock, Extraction, Storage
from .forms import ChemicalCreateForm, StockUpdateForm, ExtractionCreateForm, StorageCreateForm
from .utils import PubChemLoader, unit_converter


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


class ChemicalListView(ListView):
    model = Chemical
    template_name = 'chemmanager/home.html'
    context_object_name = 'chemicals'
    extra_context = {
        'title': 'Chemical Manager',
        'chemical_detail': None,
    }

    def get_queryset(self):

        if 'pk' in self.kwargs:
            self.extra_context['chemical_detail'] = Chemical.objects.filter(pk=self.kwargs['pk']).first()
        else:
            self.extra_context['chemical_detail'] = None

        object_list = Chemical.objects.filter(workgroup=self.request.user.profile.workgroup)
        object_list = object_list | Chemical.objects.filter(stock__storage__workgroup=self.request.user.profile.workgroup).exclude(secret=True)

        query = self.request.GET.get('q')
        if query:
            object_list = object_list.filter(name__icontains=query)

        # Sort by most available / largest stock count and than by name!
        return object_list.annotate(count=Count('stock__id')).order_by('-count', 'name').distinct()

    paginate_by = 8


class ChemicalCreateView(CreateView):
    model = Chemical
    form_class = ChemicalCreateForm
    extra_context = {
        'title': 'Add'
    }

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
            return super().form_valid(form, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        return form


class ChemicalUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Chemical
    form_class = ChemicalCreateForm
    extra_context = {
        'title': 'Update',
        'delete': True,
    }

    def form_valid(self, form, **kwargs):
        form.instance.creator = self.request.user
        chemical = self.get_object()

        if self.request.user == chemical.creator:
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
                return super().form_valid(form)
        else:
            messages.add_message(self.request, messages.WARNING, 'You are not permitted to apply changes! '
                                                                 'Please contact your group admin.')
            return HttpResponseRedirect(reverse_lazy('chemmanager-home'))

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
        messages.add_message(self.request, messages.INFO, f'{stock.name} successfully removed!')
        return super().delete(request, *args, **kwargs)

    def test_func(self):
        """Check if User is in group and allowed to remove Stock"""
        stock = self.get_object()
        if self.request.user.profile.workgroup in stock.storage.workgroup.all():
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
            if (stock.left_quantity - unit_converter(form.cleaned_data.get('quantity'), form.cleaned_data.get('unit'), stock)) <= 0:
                path = reverse('stock-delete', args=[stock.id])
                messages.add_message(self.request, messages.WARNING,
                                     f'<div class="d-flex justify-content-between align-items-center"> <div>Stock <b>{stock.name}</b> for <b>{stock.chemical.name}</b> seems to be empty.</div> <a class="btn btn-outline-danger" href="{path}">Remove Stock!</a> </div>',
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
        if my_stock.storage.workgroup.filter(storage__workgroup=self.request.user.profile.workgroup) or\
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
        object_list = self.model.objects.filter(workgroup=self.request.user.profile.workgroup)

        return object_list.order_by('name').distinct()
    # context_object_name = 'chemicals'
    # extra_context = {
    #     'title': 'Chemical Manager',
    #     'chemical_detail': None,
    # }
    #
    # def get_queryset(self):
    #
    #     if 'pk' in self.kwargs:
    #         self.extra_context['chemical_detail'] = Chemical.objects.filter(pk=self.kwargs['pk']).first()
    #     else:
    #         self.extra_context['chemical_detail'] = None
    #
    #     object_list = Chemical.objects.filter(workgroup=self.request.user.profile.workgroup)
    #     object_list = object_list | Chemical.objects.filter(stock__storage__workgroup=self.request.user.profile.workgroup).exclude(secret=True)
    #
    #     query = self.request.GET.get('q')
    #     if query:
    #         object_list = object_list.filter(name__icontains=query)
    #
    #     return object_list.order_by('name').distinct()
    #
    # paginate_by = 10


class StorageCreateView(LoginRequiredMixin, CreateView):
    model = Storage
    form_class = StorageCreateForm
    success_url = reverse_lazy('storage-list')

    def form_valid(self, form):
        print(form.cleaned_data)
        if self.kwargs['pk'] == 0:
            set_storage = Storage.add_root(name=form.instance.name, room=form.instance.room, creator=self.request.user)
            workgroups = form.cleaned_data.get('workgroup')
        else:
            root_storage = Storage.objects.get(id=self.kwargs['pk'])
            set_storage = root_storage.add_child(name=form.instance.name, room=form.instance.room, creator=self.request.user)
            workgroups = root_storage.workgroup.all()
        set_storage.workgroup.add(self.request.user.profile.workgroup)
        for group in workgroups:
            set_storage.workgroup.add(group)

        return HttpResponseRedirect(self.success_url)

    def get_form(self, form_class=None):
        """Make Workgroup selection only visible, if 1. Level Storage"""
        # TODO do not show Workgroup or make it disabled if substorage
        form = super().get_form(form_class)
        if self.kwargs['pk'] != 0:
            root_storage = Storage.objects.get(id=self.kwargs['pk'])
            form.fields['workgroup'].initial = root_storage.workgroup.all()
            # form.fields['workgroup'].widget = forms.HiddenInput()
            form.fields['room'].initial = root_storage.room
        else:
            form['workgroup'].initial = self.request.user.profile

        return form

    def get_context_data(self, **kwargs):
        if self.kwargs['pk'] != 0:
            root_storage = Storage.objects.get(id=self.kwargs['pk'])
            kwargs.update({
                'root_storage': root_storage,
            })
        return super(StorageCreateView, self).get_context_data(**kwargs)


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
