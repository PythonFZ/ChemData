from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Chemical, Stock, Extraction
from .forms import ChemicalCreateForm, StockUpdateForm, ExtractionCreateForm


class StockCreateView(CreateView):
    model = Stock
    fields = ('name', 'quantity', 'unit')

    def form_valid(self, form):
        chemical_id = self.request.GET.get('chemical')
        form.instance.chemical = Chemical.objects.get(pk=chemical_id)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(StockCreateView, self).get_context_data(**kwargs)
        chemical_id = self.request.GET.get('chemical')
        context['chemical'] = Chemical.objects.get(pk=chemical_id).name

        return context


class ChemicalListView(ListView):
    model = Chemical
    template_name = 'chemmanager/home.html'
    context_object_name = 'chemicals'
    extra_context = {'title': 'Chemical Manager'}

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            object_list = self.model.objects.filter(name__icontains=query)
        else:
            object_list = self.model.objects.all()
        return object_list.order_by('name')

    paginate_by = 10


class ChemicalCreateView(CreateView):
    model = Chemical
    form_class = ChemicalCreateForm
    # success_url =
    extra_context = {
        'title': 'Add'
    }

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


class ChemicalUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Chemical
    form_class = ChemicalCreateForm
    extra_context = {
        'title': 'Update',
        'delete': True,
    }

    def form_valid(self, form):
        form.instance.creator = self.request.user
        chemical = self.get_object()
        if self.request.user == chemical.creator:
            return super().form_valid(form)
        else:
            # messages.ERROR(self.request, 'You are not permitted to apply changed! Please contact your admin!')
            messages.add_message(self.request, messages.WARNING, 'You are not permitted to apply changes! '
                                                                 'Please contact your group admin.')
            return HttpResponseRedirect(reverse_lazy('chemmanager-home'))

    def test_func(self):
        # TODO Implement Test-Function for Work-Group-Check
        chemical = self.get_object()
        if self.request.user == chemical.creator:
            return True
        else:
            return True


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
        return HttpResponseRedirect(self.success_url)


class StockUpdateView(UpdateView):
    model = Stock
    form_class = StockUpdateForm


class ExtractionCreateView(CreateView):
    model = Extraction
    form_class = ExtractionCreateForm

    def form_valid(self, form):
        if self.request.POST.get('anonymous'):
            form.instance.user = None
        else:
            form.instance.user = self.request.user
        form.instance.stock = Stock.objects.get(id=self.kwargs['pk'])

        return super().form_valid(form)
