from django.test import TestCase
from .models import Chemical


# Create your tests here.
# Look at https://docs.djangoproject.com/en/3.2/intro/tutorial05/ for more information

class ChemicalModelTest(TestCase):

    def test_if_str_is_str(self):
        """A Hello World Test case"""

        chemical = Chemical(name="Ethanol")

        self.assertIs(chemical.name, "Ethanol")
