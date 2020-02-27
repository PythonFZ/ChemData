from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Chemical, Stock
from .forms import ChemicalCreateForm


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
        return object_list
    paginate_by = 10
    ordering = ['name']


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


class ChemicalUpdateView(UserPassesTestMixin, UpdateView):
    model = Chemical
    form_class = ChemicalCreateForm
    success_url = reverse_lazy('chemmanager-home')
    extra_context = {
        'title': 'Update',
        'delete': True,
    }

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

    def test_func(self):
        chemical = self.get_object()
        if self.request.user == chemical.creator:
            return True
        else:
            return False


class ChemicalDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Chemical
    success_url = reverse_lazy('chemmanager-home')

    def test_func(self):
        chemical = self.get_object()
        if self.request.user == chemical.creator:
            return True
        else:
            return False


class StockDetailView(DetailView):
    model = Stock

