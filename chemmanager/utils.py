import pubchempy as pcp
import os.path
from .models import Stock, Unit


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
        if initial_dict['cid'] is None:
            # self.load_img()
            initial_dict['cid'] = self.compound.cid

        return initial_dict


def unit_converter(input_val, unit_name, stock: Stock):
    """
    Check unit and compare with Stock Unit, if different, try to convert:
    """
    unit = Unit.objects.filter(name=unit_name).first()
    stock_unit = stock.unit
    if unit == stock_unit:
        print('1.')
        return input_val
    else:
        fact = 1
        if stock_unit != stock_unit.equals_standard_unit:
            fact /= stock_unit.equals_standard
            # Not ideal to set without saving, but works!
            stock_unit = stock_unit.equals_standard_unit

        if unit.equals_standard_unit == stock_unit:
            return input_val * unit.equals_standard * fact
        else:
            return False
