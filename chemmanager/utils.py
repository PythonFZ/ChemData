import pubchempy as pcp
from .models import Chemical
import os.path


class PubChemLoader:
    def __init__(self, chemical_name):
        self.chemical_name = chemical_name
        try:
            self.compound = pcp.get_compounds(self.chemical_name, 'name')[0]
        except IndexError:
            print('Could not get any data')
            self.compound = None

    def load_img(self):
        img_path = f'/chemical_pics/{self.chemical.id}.png'
        if not os.path.isfile('./media' + img_path):
            pcp.download('PNG', './media' + img_path, self.compound.cid, 'cid')
        return img_path
