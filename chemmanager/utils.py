import pubchempy as pcp
import os.path
from .models import Stock, Unit, ChemicalSynonym, Chemical


class PubChemLoader:
    def __init__(self, chemical_name):
        self.chemical_name = chemical_name
        try:
            self.compound = pcp.get_compounds(self.chemical_name, 'name')[0]
        except IndexError:
            print('Could not get any data')
            self.compound = None

    def load_img(self):
        img_path = f'/chemical_pics/{self.compound.cid}.png'
        if not os.path.isfile('./media' + img_path):
            pcp.download('PNG', './media' + img_path, self.compound.cid, 'cid')
        return img_path

    def generate_initial(self, initial_dict):
        # initial_dict['name'] = self.compound.iupac_name
        #if initial_dict['structure'] is None:
        if initial_dict['structure'] != self.compound.molecular_formula:
            initial_dict['structure'] = self.compound.molecular_formula
        #if initial_dict.get('molar_mass') is None:
        if initial_dict.get('molar_mass') != self.compound.molecular_weight:
            initial_dict['molar_mass'] = self.compound.molecular_weight
        # Has to be reset!
        initial_dict['cid'] = self.compound.cid

        return initial_dict


def update_chemical_synonyms(chemical: Chemical, synonyms: list):
    all_synonyms = ChemicalSynonym.objects.filter(chemical=chemical)
    # Create those, which do not exist
    for synonym in synonyms:
        _, _ = ChemicalSynonym.objects.get_or_create(name=synonym, chemical=chemical)
    # Remove those, which have been removed
    for synonym in all_synonyms:
        if synonym.name not in synonyms:
            synonym.delete()


def unit_converter(input_val, unit_name, stock: Stock):
    """
    Check unit and compare with Stock Unit, if different, try to convert:
    """
    unit = Unit.objects.filter(name=unit_name).first()
    stock_unit = stock.unit
    if unit == stock_unit:
        return input_val
    else:
        fact = 1
        if stock_unit != stock_unit.equals_standard_unit:
            fact /= stock_unit.equals_standard
            stock_unit = stock_unit.equals_standard_unit

        if unit.equals_standard_unit == stock_unit:
            return input_val * unit.equals_standard * fact
        else:
            return False
