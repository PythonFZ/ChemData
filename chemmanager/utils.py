import pubchempy as pcp
from .models import Chemical
import os.path


class PubChemLoader:
    def __init__(self, chemical: Chemical):
        self.chemical = chemical
        try:
            self.compound = pcp.get_compounds(self.chemical.name, 'name')[0]
        except IndexError:
            print('Could not get any data')
            self.compound = None

    def load_img(self):
        img_path = f'/chemical_pics/{self.chemical.id}.png'
        if not os.path.isfile('./media' + img_path):
            pcp.download('PNG', './media' + img_path, self.compound.cid, 'cid')
        return img_path
